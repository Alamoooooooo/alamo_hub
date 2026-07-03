#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


SCRIPT_PATH = Path(__file__).resolve()
SKILL_DIR = SCRIPT_PATH.parents[1]
RUNS_DIR = SKILL_DIR / "runs"
SCHEMAS_DIR = SKILL_DIR / "assets" / "schemas"
SKILLS_REVIEW_DIR = SKILL_DIR.parent

OVERLAY_REGISTRY: tuple[dict[str, Any], ...] = ()


@dataclass
class ValidationCommand:
    name: str
    command: str
    shell: str = "auto"
    workdir: str | None = None
    required: bool = True
    timeout_seconds: int | None = None


@dataclass
class OrchestratorConfig:
    workspace_root: str = "."
    target_paths: list[str] = field(default_factory=list)
    max_rounds: int = 2
    execution_backend: str = "codex"
    codex_command: str = "codex.cmd"
    sandbox_mode: str = "workspace-write"
    approval_policy: str = "never"
    model: str | None = None
    profile: str | None = None
    profile_name: str = "default"
    additional_writable_dirs: list[str] = field(default_factory=list)
    validation_commands: list[ValidationCommand] = field(default_factory=list)
    continue_on_validation_failure: bool = True
    check_prompt_extra: str = ""
    fix_prompt_extra: str = ""
    review_prompt_extra: str = ""
    codex_timeout_seconds: int = 900
    codex_preflight_timeout_seconds: int = 120
    validation_timeout_seconds: int = 300
    default_shell: str = "auto"
    preflight_required: bool = True
    allow_degraded_without_codex: bool = True


@dataclass
class ProcessResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False
    timeout_seconds: int | None = None


@dataclass
class RoundState:
    round_index: int
    started_at: str
    mode: str = "full"
    diff_summary_before: str = ""
    diff_summary_after: str = ""
    diff_files_before: list[str] = field(default_factory=list)
    diff_files_after: list[str] = field(default_factory=list)
    changed_files: list[str] = field(default_factory=list)
    check: dict[str, Any] = field(default_factory=dict)
    fix: dict[str, Any] = field(default_factory=dict)
    validation: dict[str, Any] = field(default_factory=dict)
    review: dict[str, Any] = field(default_factory=dict)
    decision: dict[str, Any] = field(default_factory=dict)
    finished_at: str | None = None


@dataclass
class RunState:
    workspace_root: str
    target_paths: list[str]
    started_at: str
    mode: str = "full"
    status: str = "running"
    profile_name: str = "default"
    preflight: dict[str, Any] = field(default_factory=dict)
    resumed_from: str | None = None
    partial_rerun_from_round: int | None = None
    rounds: list[RoundState] = field(default_factory=list)
    memory_summary: dict[str, Any] = field(
        default_factory=lambda: {"hotspots": [], "fixed_issues": [], "regressions": [], "notes": []}
    )
    stop_reason: str = ""
    final_fix_summary: str = ""
    final_review_summary: str = ""
    finished_at: str | None = None


class OrchestrationError(RuntimeError):
    pass


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"config must be a mapping: {path}")
    return data


def _load_profiles(raw: dict[str, Any], profile_override: str | None) -> tuple[dict[str, Any], str]:
    profiles = raw.get("profiles", {}) or {}
    if not profiles:
        return raw, str(raw.get("profile_name", "default") or "default")
    if not isinstance(profiles, dict):
        raise ValueError("profiles must be a mapping")
    profile_name = profile_override or str(raw.get("default_profile", "") or "")
    if not profile_name:
        if len(profiles) == 1:
            profile_name = next(iter(profiles))
        else:
            raise ValueError("multiple profiles exist; specify one with --profile-name or default_profile")
    if profile_name not in profiles:
        raise ValueError(f"profile not found: {profile_name}")
    merged = dict(raw)
    merged.update(dict(profiles[profile_name] or {}))
    merged.pop("profiles", None)
    merged["profile_name"] = profile_name
    return merged, profile_name


def _raw_config_to_object(raw: dict[str, Any], *, source_path: Path, profile_override: str | None = None) -> OrchestratorConfig:
    merged_raw, resolved_profile_name = _load_profiles(raw, profile_override)
    default_shell = str(merged_raw.get("default_shell", "auto") or "auto")
    default_validation_timeout = (
        None
        if merged_raw.get("validation_timeout_seconds") in (None, "", "null")
        else int(merged_raw.get("validation_timeout_seconds"))
    )
    validation_commands = [
        ValidationCommand(
            name=str(item["name"]),
            command=str(item["command"]),
            shell=str(item.get("shell", default_shell) or default_shell),
            workdir=str(item["workdir"]) if item.get("workdir") else None,
            required=bool(item.get("required", True)),
            timeout_seconds=(
                None
                if item.get("timeout_seconds", default_validation_timeout) in (None, "", "null")
                else int(item.get("timeout_seconds", default_validation_timeout))
            ),
        )
        for item in merged_raw.get("validation_commands", []) or []
    ]
    cfg = OrchestratorConfig(
        workspace_root=str(merged_raw.get("workspace_root", ".") or "."),
        target_paths=[str(x) for x in (merged_raw.get("target_paths", []) or [])],
        max_rounds=int(merged_raw.get("max_rounds", 2) or 2),
        execution_backend=str(merged_raw.get("execution_backend", "codex") or "codex"),
        codex_command=str(merged_raw.get("codex_command", "codex.cmd") or "codex.cmd"),
        sandbox_mode=str(merged_raw.get("sandbox_mode", "workspace-write") or "workspace-write"),
        approval_policy=str(merged_raw.get("approval_policy", "never") or "never"),
        model=str(merged_raw["model"]) if merged_raw.get("model") else None,
        profile=str(merged_raw["profile"]) if merged_raw.get("profile") else None,
        profile_name=resolved_profile_name,
        additional_writable_dirs=[str(x) for x in (merged_raw.get("additional_writable_dirs", []) or [])],
        validation_commands=validation_commands,
        continue_on_validation_failure=bool(merged_raw.get("continue_on_validation_failure", True)),
        check_prompt_extra=str(merged_raw.get("check_prompt_extra", "") or ""),
        fix_prompt_extra=str(merged_raw.get("fix_prompt_extra", "") or ""),
        review_prompt_extra=str(merged_raw.get("review_prompt_extra", "") or ""),
        codex_timeout_seconds=int(merged_raw.get("codex_timeout_seconds", 900) or 900),
        codex_preflight_timeout_seconds=int(merged_raw.get("codex_preflight_timeout_seconds", 120) or 120),
        validation_timeout_seconds=int(merged_raw.get("validation_timeout_seconds", 300) or 300),
        default_shell=default_shell,
        preflight_required=bool(merged_raw.get("preflight_required", True)),
        allow_degraded_without_codex=bool(merged_raw.get("allow_degraded_without_codex", True)),
    )
    _validate_config(cfg, source_path)
    return cfg


def _load_config(path: Path, profile_override: str | None = None) -> OrchestratorConfig:
    return _raw_config_to_object(_load_yaml(path), source_path=path, profile_override=profile_override)


def _validate_config(cfg: OrchestratorConfig, path: Path) -> None:
    if not cfg.target_paths:
        raise ValueError(f"target_paths is required: {path}")
    if cfg.max_rounds < 1 or cfg.max_rounds > 3:
        raise ValueError(f"max_rounds must be between 1 and 3: {cfg.max_rounds}")
    if cfg.execution_backend not in {"codex", "prompt-bundle"}:
        raise ValueError(f"unsupported execution_backend: {cfg.execution_backend}")
    if cfg.sandbox_mode not in {"read-only", "workspace-write", "danger-full-access"}:
        raise ValueError(f"unsupported sandbox_mode: {cfg.sandbox_mode}")
    if cfg.approval_policy not in {"untrusted", "on-failure", "on-request", "never"}:
        raise ValueError(f"unsupported approval_policy: {cfg.approval_policy}")
    if cfg.codex_timeout_seconds <= 0:
        raise ValueError(f"codex_timeout_seconds must be positive: {cfg.codex_timeout_seconds}")
    if cfg.codex_preflight_timeout_seconds <= 0:
        raise ValueError(f"codex_preflight_timeout_seconds must be positive: {cfg.codex_preflight_timeout_seconds}")
    if cfg.validation_timeout_seconds <= 0:
        raise ValueError(f"validation_timeout_seconds must be positive: {cfg.validation_timeout_seconds}")


def _resolve_workspace(path_str: str, config_path: Path) -> Path:
    workspace = Path(path_str)
    if not workspace.is_absolute():
        workspace = (config_path.parent / workspace).resolve()
    return workspace


def _resolve_path(base: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = (base / path).resolve()
    return path


def _safe_relative_path(path: Path, workspace: Path) -> str:
    try:
        return str(path.relative_to(workspace))
    except ValueError:
        return str(path)


def _resolve_target_paths(workspace: Path, target_paths: list[str]) -> list[str]:
    return [_safe_relative_path(_resolve_path(workspace, item), workspace) for item in target_paths]


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_text(path: Path, content: str) -> None:
    _ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, payload: Any) -> None:
    _ensure_dir(path.parent)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_text_if_exists(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def _collect_overlay_context(target_paths: list[str], step: str) -> str:
    sections: list[str] = []
    normalized_targets = [item.replace("\\", "/") for item in target_paths]
    for overlay in OVERLAY_REGISTRY:
        prefixes = tuple(str(item).replace("\\", "/").rstrip("/") for item in overlay.get("match_prefixes", ()))
        if not any(target == prefix or target.startswith(f"{prefix}/") for target in normalized_targets for prefix in prefixes):
            continue
        overlay_path = overlay.get(f"{step}_overlay")
        if not isinstance(overlay_path, Path):
            continue
        content = _read_text_if_exists(overlay_path)
        if not content:
            continue
        sections.append(f"Repository-specific overlay for `{', '.join(prefixes)}`:\n{content}")
    return "\n\n".join(sections)


def _parse_json_payload(text: str) -> Any:
    candidate = text.strip()
    if not candidate:
        return {}
    if candidate.startswith("```"):
        lines = candidate.splitlines()
        if len(lines) >= 3:
            candidate = "\n".join(lines[1:-1]).strip()
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        for index, char in enumerate(candidate):
            if char not in "{[":
                continue
            try:
                obj, end_index = decoder.raw_decode(candidate[index:])
            except json.JSONDecodeError:
                continue
            trailing = candidate[index + end_index :].strip()
            if trailing:
                continue
            return obj
        raise


def _build_codex_base_command(cfg: OrchestratorConfig, workspace: Path) -> list[str]:
    codex_bin = cfg.codex_command
    if os.name == "nt" and codex_bin.lower().endswith(".cmd"):
        base = ["cmd", "/c", codex_bin]
    else:
        base = [codex_bin]
    base.extend(["-a", cfg.approval_policy])
    base.extend(
        [
            "exec",
            "-",
            "-C",
            str(workspace),
            "-s",
            cfg.sandbox_mode,
            "--output-schema",
        ]
    )
    if cfg.model:
        base.extend(["-m", cfg.model])
    if cfg.profile:
        base.extend(["-p", cfg.profile])
    for item in cfg.additional_writable_dirs:
        base.extend(["--add-dir", str(item)])
    return base


def _run_subprocess(
    command: list[str],
    *,
    input_text: str | None = None,
    cwd: Path | None = None,
    timeout_seconds: int | None = None,
) -> ProcessResult:
    try:
        result = subprocess.run(
            command,
            input=input_text,
            text=True,
            capture_output=True,
            cwd=str(cwd) if cwd else None,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=timeout_seconds,
        )
        return ProcessResult(
            command=command,
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            timed_out=False,
            timeout_seconds=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout.decode("utf-8", "replace") if exc.stdout else "")
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr.decode("utf-8", "replace") if exc.stderr else "")
        return ProcessResult(
            command=command,
            returncode=124,
            stdout=stdout,
            stderr=stderr,
            timed_out=True,
            timeout_seconds=timeout_seconds,
        )


def _run_codex_step(
    *,
    cfg: OrchestratorConfig,
    workspace: Path,
    schema_path: Path,
    prompt: str,
    output_file: Path,
    log_prefix: Path,
    timeout_seconds: int | None = None,
) -> dict[str, Any]:
    command = _build_codex_base_command(cfg, workspace)
    command.extend([str(schema_path), "-o", str(output_file)])
    result = _run_subprocess(
        command,
        input_text=prompt,
        cwd=workspace,
        timeout_seconds=timeout_seconds if timeout_seconds is not None else cfg.codex_timeout_seconds,
    )
    _write_text(log_prefix.with_suffix(".stdout.log"), result.stdout)
    _write_text(log_prefix.with_suffix(".stderr.log"), result.stderr)
    _write_json(
        log_prefix.with_suffix(".process.json"),
        {
            "returncode": result.returncode,
            "command": command,
            "timed_out": result.timed_out,
            "timeout_seconds": result.timeout_seconds,
        },
    )
    if result.timed_out:
        raise OrchestrationError(
            f"Codex step timed out after {(timeout_seconds if timeout_seconds is not None else cfg.codex_timeout_seconds)}s. See {log_prefix.with_suffix('.stderr.log')}"
        )
    if result.returncode != 0:
        raise OrchestrationError(
            f"Codex step failed with exit code {result.returncode}. See {log_prefix.with_suffix('.stderr.log')}"
        )
    if not output_file.exists():
        raise OrchestrationError(f"Codex step completed but did not write output file: {output_file}")
    payload = _parse_json_payload(output_file.read_text(encoding="utf-8"))
    _write_json(log_prefix.with_suffix(".parsed.json"), payload)
    return payload


def _build_check_prompt(
    cfg: OrchestratorConfig,
    target_paths: list[str],
    *,
    round_index: int,
    memory_summary: dict[str, Any],
    prior_round: RoundState | None,
) -> str:
    target_text = ", ".join(target_paths)
    extra = f"\nAdditional instructions:\n{cfg.check_prompt_extra.strip()}\n" if cfg.check_prompt_extra.strip() else ""
    overlay = _collect_overlay_context(target_paths, "check")
    prompt = [
        "Use $memory-check to inspect this codebase and produce a structured memory risk report.",
        f"Focus on these paths: {target_text}",
        f"This is check round {round_index}.",
        "Select the single highest-value hotspot to fix next.",
        "Preserve current pipeline semantics when reasoning about fixes.",
    ]
    if prior_round is not None:
        prompt.extend(
            [
                "Previous round review summary:",
                json.dumps(prior_round.review, ensure_ascii=False, indent=2),
                "Previous round validation summary:",
                json.dumps(prior_round.validation, ensure_ascii=False, indent=2),
            ]
        )
    prompt.extend(
        [
            "Current run memory summary:",
            json.dumps(memory_summary, ensure_ascii=False, indent=2),
            "Return JSON matching the provided schema only.",
        ]
    )
    if overlay:
        prompt.extend(["Apply this repository-specific overlay if relevant:", overlay])
    if extra:
        prompt.append(extra.strip())
    return "\n\n".join(prompt)


def _build_fix_prompt(
    cfg: OrchestratorConfig,
    target_paths: list[str],
    *,
    round_index: int,
    check_payload: dict[str, Any],
    prior_round: RoundState | None,
    memory_summary: dict[str, Any],
) -> str:
    target_text = ", ".join(target_paths)
    extra = f"\nAdditional instructions:\n{cfg.fix_prompt_extra.strip()}\n" if cfg.fix_prompt_extra.strip() else ""
    overlay = _collect_overlay_context(target_paths, "fix")
    prompt = [
        "Use $memory-fix to apply safe, targeted code changes for the current highest-value memory issue.",
        f"Restrict the main edits to these paths unless a helper change is necessary: {target_text}",
        "Preserve behavior, output contracts, checkpoint logic, overwrite logic, and missing-model skip behavior unless explicitly required.",
        f"This is fix round {round_index}.",
        "Current check report:",
        json.dumps(check_payload, ensure_ascii=False, indent=2),
        "Current run memory summary:",
        json.dumps(memory_summary, ensure_ascii=False, indent=2),
    ]
    if prior_round is not None:
        prompt.extend(
            [
                "Previous round validation results to address if still relevant:",
                json.dumps(prior_round.validation, ensure_ascii=False, indent=2),
                "Previous round review findings to address if still relevant:",
                json.dumps(prior_round.review, ensure_ascii=False, indent=2),
                "Previous round diff summary:",
                json.dumps(
                    {
                        "diff_summary_before": prior_round.diff_summary_before,
                        "diff_summary_after": prior_round.diff_summary_after,
                        "changed_files": prior_round.changed_files,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            ]
        )
    prompt.append("Return JSON matching the provided schema only after applying changes.")
    if overlay:
        prompt.extend(["Apply this repository-specific overlay if relevant:", overlay])
    if extra:
        prompt.append(extra.strip())
    return "\n\n".join(prompt)


def _build_review_prompt(
    cfg: OrchestratorConfig,
    target_paths: list[str],
    *,
    round_state: RoundState,
    memory_summary: dict[str, Any],
) -> str:
    target_text = ", ".join(target_paths)
    extra = f"\nAdditional instructions:\n{cfg.review_prompt_extra.strip()}\n" if cfg.review_prompt_extra.strip() else ""
    overlay = _collect_overlay_context(target_paths, "review")
    prompt = [
        "Use $memory-review to review the current uncommitted changes.",
        "Start from normal code review, then add memory-specific regression checks.",
        f"Focus on these paths: {target_text}",
        f"This is review round {round_state.round_index}.",
        "Round check report:",
        json.dumps(round_state.check, ensure_ascii=False, indent=2),
        "Round fix report:",
        json.dumps(round_state.fix, ensure_ascii=False, indent=2),
        "Validation results:",
        json.dumps(round_state.validation, ensure_ascii=False, indent=2),
        "Current run memory summary:",
        json.dumps(memory_summary, ensure_ascii=False, indent=2),
        "Return JSON matching the provided schema only.",
    ]
    if overlay:
        prompt.extend(["Apply this repository-specific overlay if relevant:", overlay])
    if extra:
        prompt.append(extra.strip())
    return "\n\n".join(prompt)


def _shell_command(command: str, shell_name: str, default_shell: str) -> list[str]:
    normalized = (shell_name or default_shell or "auto").strip().lower()
    if normalized == "auto":
        normalized = "powershell" if os.name == "nt" else "bash"
    if normalized in {"powershell", "pwsh"}:
        executable = "pwsh" if normalized == "pwsh" else "powershell"
        return [executable, "-NoProfile", "-Command", command]
    if normalized == "cmd":
        return ["cmd", "/c", command]
    if normalized in {"bash", "sh"}:
        return [normalized, "-lc", command]
    raise ValueError(f"unsupported shell for validation command: {shell_name}")


def _preferred_python_command() -> str:
    for candidate in ("python3", "python"):
        resolved = shutil.which(candidate)
        if resolved:
            return candidate
    return "python"


def _rewrite_validation_command(command: str) -> str:
    stripped = command.lstrip()
    python_cmd = _preferred_python_command()
    if stripped.startswith("python "):
        prefix_len = len(command) - len(stripped)
        return command[:prefix_len] + python_cmd + stripped[len("python") :]
    if "@' | python -" in command:
        return command.replace("@' | python -", f"@' | {python_cmd} -")
    if "| python -" in command:
        return command.replace("| python -", f"| {python_cmd} -")
    return command


def _extract_dependency_diagnostics(stderr_text: str) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    for line in stderr_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("ModuleNotFoundError: No module named "):
            module_name = stripped.split("ModuleNotFoundError: No module named ", 1)[1].strip().strip("'\"")
            diagnostics.append(
                {
                    "kind": "missing_python_module",
                    "module": module_name,
                    "message": stripped,
                }
            )
        elif stripped.startswith("ImportError:"):
            diagnostics.append(
                {
                    "kind": "import_error",
                    "module": "",
                    "message": stripped,
                }
            )
    return diagnostics


def _run_validation(
    cfg: OrchestratorConfig,
    commands: list[ValidationCommand],
    *,
    workspace: Path,
    output_dir: Path,
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    overall_ok = True
    dependency_diagnostics: list[dict[str, str]] = []
    for item in commands:
        workdir = _resolve_path(workspace, item.workdir) if item.workdir else workspace
        rewritten_command = _rewrite_validation_command(item.command)
        command = _shell_command(rewritten_command, item.shell, cfg.default_shell)
        timeout_seconds = item.timeout_seconds if item.timeout_seconds is not None else cfg.validation_timeout_seconds
        result = _run_subprocess(command, cwd=workdir, timeout_seconds=timeout_seconds)
        stdout_path = output_dir / f"{item.name}.stdout.log"
        stderr_path = output_dir / f"{item.name}.stderr.log"
        _write_text(stdout_path, result.stdout)
        _write_text(stderr_path, result.stderr)
        item_diagnostics = _extract_dependency_diagnostics(result.stderr)
        dependency_diagnostics.extend(item_diagnostics)
        passed = (result.returncode == 0) and not result.timed_out
        if item.required and not passed:
            overall_ok = False
        results.append(
            {
                "name": item.name,
                "command": item.command,
                "resolved_command": rewritten_command,
                "shell": item.shell,
                "workdir": str(workdir),
                "required": item.required,
                "timeout_seconds": timeout_seconds,
                "returncode": result.returncode,
                "timed_out": result.timed_out,
                "passed": passed,
                "dependency_diagnostics": item_diagnostics,
                "stdout_log": str(stdout_path),
                "stderr_log": str(stderr_path),
            }
        )
    deduped: list[dict[str, str]] = []
    seen = set()
    for item in dependency_diagnostics:
        key = (item.get("kind", ""), item.get("module", ""), item.get("message", ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    payload = {"passed": overall_ok, "results": results, "dependency_diagnostics": deduped}
    _write_json(output_dir / "validation.json", payload)
    return payload


def _git_diff_stat(workspace: Path, target_paths: list[str]) -> str:
    command = ["git", "diff", "--stat", "--", *target_paths]
    result = _run_subprocess(command, cwd=workspace, timeout_seconds=30)
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _git_diff_names(workspace: Path, target_paths: list[str]) -> list[str]:
    command = ["git", "diff", "--name-only", "--", *target_paths]
    result = _run_subprocess(command, cwd=workspace, timeout_seconds=30)
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _git_status(workspace: Path) -> str:
    result = _run_subprocess(["git", "status", "--short"], cwd=workspace, timeout_seconds=30)
    if result.returncode != 0:
        return ""
    return result.stdout


def _git_diff_patch_summary(workspace: Path, target_paths: list[str]) -> dict[str, Any]:
    command = ["git", "diff", "--numstat", "--", *target_paths]
    result = _run_subprocess(command, cwd=workspace, timeout_seconds=30)
    if result.returncode != 0:
        return {"files": [], "total_added": 0, "total_deleted": 0}
    files: list[dict[str, Any]] = []
    total_added = 0
    total_deleted = 0
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        added_raw, deleted_raw, file_path = parts
        added = 0 if added_raw == "-" else int(added_raw)
        deleted = 0 if deleted_raw == "-" else int(deleted_raw)
        files.append({"file": file_path, "added": added, "deleted": deleted})
        total_added += added
        total_deleted += deleted
    return {
        "files": files,
        "total_added": total_added,
        "total_deleted": total_deleted,
    }


def _should_continue(
    *,
    cfg: OrchestratorConfig,
    round_state: RoundState,
) -> tuple[bool, str]:
    round_index = round_state.round_index
    review_payload = round_state.review or {}
    validation_payload = round_state.validation or {}
    blocking = review_payload.get("blocking_findings", []) or []
    stop_recommended = bool(review_payload.get("stop_recommended", False))
    validation_passed = bool(validation_payload.get("passed", False))
    diff_changed = round_state.diff_summary_before != round_state.diff_summary_after

    if round_index >= cfg.max_rounds:
        return False, "max_rounds_reached"
    if stop_recommended and validation_passed and not blocking:
        return False, str(review_payload.get("stop_reason", "") or "review_recommended_stop")
    if validation_passed and not blocking:
        if not diff_changed:
            return False, "validated_without_new_diff_impact"
        return False, str(review_payload.get("stop_reason", "") or "validated_without_blocking_findings")
    if not validation_passed:
        if not cfg.continue_on_validation_failure:
            return False, "validation_failed_and_followup_disabled"
        return True, "validation_failed_requires_followup"
    if blocking:
        return True, "blocking_findings_remain"
    if bool(review_payload.get("continue_recommended", False)):
        return True, "review_recommended_continue"
    return False, str(review_payload.get("stop_reason", "") or "no_high_value_followup")


def _update_memory_summary(run_state: RunState, round_state: RoundState) -> None:
    check_hotspot = str(round_state.check.get("top_hotspot", "") or "").strip()
    if check_hotspot and check_hotspot not in run_state.memory_summary["hotspots"]:
        run_state.memory_summary["hotspots"].append(check_hotspot)

    for item in round_state.review.get("what_improved", []) or []:
        text = str(item).strip()
        if text and text not in run_state.memory_summary["fixed_issues"]:
            run_state.memory_summary["fixed_issues"].append(text)

    if not bool(round_state.validation.get("passed", False)):
        note = f"round {round_state.round_index}: validation failed"
        if note not in run_state.memory_summary["regressions"]:
            run_state.memory_summary["regressions"].append(note)
    for item in round_state.validation.get("dependency_diagnostics", []) or []:
        module = str(item.get("module", "") or "").strip()
        message = str(item.get("message", "") or "").strip()
        note = f"missing dependency: {module}" if module else message
        if note and note not in run_state.memory_summary["notes"]:
            run_state.memory_summary["notes"].append(note)

    for item in round_state.review.get("blocking_findings", []) or []:
        reason = str(item.get("reason", "") or "").strip()
        if reason and reason not in run_state.memory_summary["regressions"]:
            run_state.memory_summary["regressions"].append(reason)

    for item in round_state.review.get("residual_hotspots", []) or []:
        text = str(item).strip()
        if text and text not in run_state.memory_summary["notes"]:
            run_state.memory_summary["notes"].append(text)


def _write_summary(run_dir: Path, run_state: RunState) -> None:
    lines = [
        "# Memory Optimizer Run Summary",
        "",
        f"- Workspace: `{run_state.workspace_root}`",
        f"- Targets: `{', '.join(run_state.target_paths)}`",
        f"- Mode: `{run_state.mode}`",
        f"- Status: `{run_state.status}`",
        f"- Profile: `{run_state.profile_name}`",
        f"- Rounds executed: `{len(run_state.rounds)}`",
        f"- Stop reason: `{run_state.stop_reason}`",
    ]
    if run_state.resumed_from:
        lines.append(f"- Resumed from: `{run_state.resumed_from}`")
    if run_state.partial_rerun_from_round is not None:
        lines.append(f"- Partial rerun from round: `{run_state.partial_rerun_from_round}`")
    if run_state.preflight:
        lines.extend(
            [
                f"- Preflight CLI available: `{run_state.preflight.get('cli_available', False)}`",
                f"- Preflight auth ready: `{run_state.preflight.get('auth_ready', False)}`",
            ]
        )
    lines.extend(["", "## Rounds", ""])
    for item in run_state.rounds:
        lines.extend(
            [
                f"### Round {item.round_index}",
                "",
                f"- Mode: `{item.mode}`",
                f"- Check hotspot: `{item.check.get('top_hotspot', '')}`",
                f"- Fix summary: `{item.fix.get('summary', '')}`",
                f"- Validation passed: `{item.validation.get('passed', False)}`",
                f"- Dependency diagnostics: `{'; '.join((diag.get('module') or diag.get('message') or '') for diag in (item.validation.get('dependency_diagnostics', []) or []))}`",
                f"- Blocking findings: `{len(item.review.get('blocking_findings', []) or [])}`",
                f"- Decision: `{item.decision.get('reason', '')}`",
                f"- Changed files: `{', '.join(item.changed_files)}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Memory Summary",
            "",
            f"- Hotspots: `{'; '.join(run_state.memory_summary.get('hotspots', []))}`",
            f"- Fixed issues: `{'; '.join(run_state.memory_summary.get('fixed_issues', []))}`",
            f"- Regressions: `{'; '.join(run_state.memory_summary.get('regressions', []))}`",
            f"- Notes: `{'; '.join(run_state.memory_summary.get('notes', []))}`",
            "",
            "## Final",
            "",
            f"- Final review summary: `{run_state.final_review_summary}`",
            f"- Final fix summary: `{run_state.final_fix_summary}`",
            "",
        ]
    )
    _write_text(run_dir / "summary.md", "\n".join(lines))


def _create_run_dir(label: str | None = None) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_label = f"-{label}" if label else ""
    base_name = f"{stamp}{safe_label}"
    run_dir = RUNS_DIR / base_name
    if not run_dir.exists():
        _ensure_dir(run_dir)
        return run_dir
    suffix = 1
    while True:
        candidate = RUNS_DIR / f"{base_name}-{suffix:02d}"
        if not candidate.exists():
            _ensure_dir(candidate)
            return candidate
        suffix += 1


def _resolved_config_payload(cfg: OrchestratorConfig, workspace: Path, target_paths: list[str]) -> dict[str, Any]:
    payload = asdict(cfg)
    payload["workspace_root"] = str(workspace)
    payload["target_paths"] = target_paths
    return payload


def _run_dry_run(run_dir: Path, cfg: OrchestratorConfig, workspace: Path, target_paths: list[str]) -> None:
    lines = [
        "# Memory Optimizer Dry Run",
        "",
        f"- Workspace: `{workspace}`",
        f"- Targets: `{', '.join(target_paths)}`",
        f"- Profile: `{cfg.profile_name}`",
        f"- Max rounds: `{cfg.max_rounds}`",
        f"- Preflight required: `{cfg.preflight_required}`",
        f"- Allow degraded without Codex: `{cfg.allow_degraded_without_codex}`",
        f"- Codex timeout: `{cfg.codex_timeout_seconds}s`",
        f"- Preflight timeout: `{cfg.codex_preflight_timeout_seconds}s`",
        f"- Validation timeout default: `{cfg.validation_timeout_seconds}s`",
        "",
        "## Planned Loop",
        "",
        "1. preflight Codex CLI/auth when enabled",
        "2. memory-check",
        "3. memory-fix",
        "4. validation",
        "5. memory-review",
        "6. optional next round when signals justify it",
        "",
        "## Validation Commands",
        "",
    ]
    for item in cfg.validation_commands:
        timeout_seconds = item.timeout_seconds if item.timeout_seconds is not None else cfg.validation_timeout_seconds
        lines.append(f"- `{item.name}` ({item.shell}, timeout={timeout_seconds}s): `{item.command}`")
    _write_text(run_dir / "dry-run.md", "\n".join(lines))


def _round_state_from_dict(raw: dict[str, Any]) -> RoundState:
    return RoundState(
        round_index=int(raw.get("round_index", 0) or 0),
        started_at=str(raw.get("started_at", "") or ""),
        mode=str(raw.get("mode", "full") or "full"),
        diff_summary_before=str(raw.get("diff_summary_before", "") or ""),
        diff_summary_after=str(raw.get("diff_summary_after", "") or ""),
        diff_files_before=[str(x) for x in (raw.get("diff_files_before", []) or [])],
        diff_files_after=[str(x) for x in (raw.get("diff_files_after", []) or [])],
        changed_files=[str(x) for x in (raw.get("changed_files", []) or [])],
        check=dict(raw.get("check", {}) or {}),
        fix=dict(raw.get("fix", {}) or {}),
        validation=dict(raw.get("validation", {}) or {}),
        review=dict(raw.get("review", {}) or {}),
        decision=dict(raw.get("decision", {}) or {}),
        finished_at=str(raw["finished_at"]) if raw.get("finished_at") else None,
    )


def _run_state_from_dict(raw: dict[str, Any]) -> RunState:
    return RunState(
        workspace_root=str(raw.get("workspace_root", "") or ""),
        target_paths=[str(x) for x in (raw.get("target_paths", []) or [])],
        started_at=str(raw.get("started_at", "") or ""),
        mode=str(raw.get("mode", "full") or "full"),
        status=str(raw.get("status", "running") or "running"),
        profile_name=str(raw.get("profile_name", "default") or "default"),
        preflight=dict(raw.get("preflight", {}) or {}),
        resumed_from=str(raw["resumed_from"]) if raw.get("resumed_from") else None,
        partial_rerun_from_round=(
            None if raw.get("partial_rerun_from_round") in (None, "", "null") else int(raw.get("partial_rerun_from_round"))
        ),
        rounds=[_round_state_from_dict(item) for item in (raw.get("rounds", []) or [])],
        memory_summary=dict(
            raw.get("memory_summary", {"hotspots": [], "fixed_issues": [], "regressions": [], "notes": []}) or {}
        ),
        stop_reason=str(raw.get("stop_reason", "") or ""),
        final_fix_summary=str(raw.get("final_fix_summary", "") or ""),
        final_review_summary=str(raw.get("final_review_summary", "") or ""),
        finished_at=str(raw["finished_at"]) if raw.get("finished_at") else None,
    )


def _load_run_state(run_dir: Path) -> RunState:
    ledger_path = run_dir / "ledger.json"
    if not ledger_path.exists():
        raise FileNotFoundError(f"ledger.json not found under run dir: {run_dir}")
    raw = json.loads(ledger_path.read_text(encoding="utf-8"))
    return _run_state_from_dict(raw)


def _load_resolved_config(run_dir: Path, profile_override: str | None = None) -> OrchestratorConfig:
    resolved_path = run_dir / "resolved-config.json"
    if not resolved_path.exists():
        raise FileNotFoundError(f"resolved-config.json not found under run dir: {run_dir}")
    raw = json.loads(resolved_path.read_text(encoding="utf-8"))
    return _raw_config_to_object(raw, source_path=resolved_path, profile_override=profile_override)


def _resolve_run_dir(identifier: str) -> Path:
    candidate = Path(identifier)
    if candidate.exists():
        return candidate.resolve()
    candidate = (RUNS_DIR / identifier).resolve()
    if candidate.exists():
        return candidate
    raise FileNotFoundError(f"run directory not found: {identifier}")


def _run_metadata(run_dir: Path) -> dict[str, Any]:
    ledger_path = run_dir / "ledger.json"
    if not ledger_path.exists():
        return {
            "name": run_dir.name,
            "path": str(run_dir),
            "status": "unknown",
            "stop_reason": "",
            "rounds": 0,
            "mode": "",
            "profile_name": "",
            "started_at": "",
            "partial_rerun_from_round": None,
            "resumed_from": None,
        }
    raw = json.loads(ledger_path.read_text(encoding="utf-8"))
    return {
        "name": run_dir.name,
        "path": str(run_dir),
        "status": str(raw.get("status", "unknown") or "unknown"),
        "stop_reason": str(raw.get("stop_reason", "") or ""),
        "rounds": len(raw.get("rounds", []) or []),
        "mode": str(raw.get("mode", "") or ""),
        "profile_name": str(raw.get("profile_name", "") or ""),
        "started_at": str(raw.get("started_at", "") or ""),
        "partial_rerun_from_round": raw.get("partial_rerun_from_round"),
        "resumed_from": raw.get("resumed_from"),
    }


def _dashboard_payload() -> dict[str, Any]:
    _ensure_dir(RUNS_DIR)
    runs = []
    total_runs = 0
    full_runs = 0
    degraded_runs = 0
    failed_runs = 0
    completed_runs = 0
    for run_dir in sorted([p for p in RUNS_DIR.iterdir() if p.is_dir()], key=lambda p: p.name, reverse=True):
        meta = _run_metadata(run_dir)
        runs.append(meta)
        total_runs += 1
        mode = str(meta.get("mode", "") or "")
        status = str(meta.get("status", "") or "")
        if mode == "full":
            full_runs += 1
        if mode == "degraded":
            degraded_runs += 1
        if status == "failed":
            failed_runs += 1
        if status == "completed":
            completed_runs += 1
    payload = {
        "generated_at": _now_iso(),
        "summary": {
            "total_runs": total_runs,
            "full_runs": full_runs,
            "degraded_runs": degraded_runs,
            "failed_runs": failed_runs,
            "completed_runs": completed_runs,
        },
        "runs": runs,
    }
    return payload


def _write_dashboard() -> dict[str, Any]:
    payload = _dashboard_payload()
    _write_json(RUNS_DIR / "index.json", payload["runs"])
    _write_json(RUNS_DIR / "dashboard.json", payload)
    lines = [
        "# Memory Optimizer Dashboard",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Total runs: `{payload['summary']['total_runs']}`",
        f"- Full runs: `{payload['summary']['full_runs']}`",
        f"- Degraded runs: `{payload['summary']['degraded_runs']}`",
        f"- Failed runs: `{payload['summary']['failed_runs']}`",
        f"- Completed runs: `{payload['summary']['completed_runs']}`",
        "",
        "## Runs",
        "",
    ]
    for item in payload["runs"]:
        lines.append(
            f"- `{item['name']}` | status=`{item['status']}` | mode=`{item['mode']}` | profile=`{item['profile_name']}` | rounds=`{item['rounds']}` | stop=`{item['stop_reason']}`"
        )
    _write_text(RUNS_DIR / "dashboard.md", "\n".join(lines))
    return payload


def _list_runs() -> int:
    payload = _write_dashboard()
    runs = payload["runs"]
    if not runs:
        print("No runs found.")
        return 0
    for item in runs:
        print(
            f"{item['name']} | status={item['status']} | mode={item['mode']} | profile={item['profile_name']} | rounds={item['rounds']} | stop={item['stop_reason']}"
        )
    return 0


def _select_latest_failed_run() -> Path:
    payload = _write_dashboard()
    for item in payload["runs"]:
        stop_reason = str(item.get("stop_reason", "") or "")
        if item.get("status") == "failed" or stop_reason.startswith("error:"):
            return Path(item["path"])
    raise FileNotFoundError("no failed run found under runs/")


def _write_run_artifacts(run_dir: Path, run_state: RunState, workspace: Path) -> None:
    _write_json(run_dir / "ledger.json", asdict(run_state))
    _write_text(run_dir / "git-status-after.txt", _git_status(workspace))
    _write_summary(run_dir, run_state)
    _write_dashboard()


def _build_preflight_prompt() -> str:
    return "Return JSON matching the schema with ok=true and message='preflight-ok'."


def _detect_auth_diagnostic(stderr_text: str) -> str:
    lowered = stderr_text.lower()
    if "401" in lowered or "unauthorized" in lowered:
        return "auth_unauthorized"
    if "missing bearer" in lowered:
        return "missing_bearer_token"
    if "error sending request" in lowered or "stream disconnected" in lowered:
        return "transport_or_network_error"
    return "unknown_error"


def _run_preflight(cfg: OrchestratorConfig, workspace: Path, run_dir: Path) -> dict[str, Any]:
    preflight_dir = run_dir / "preflight"
    _ensure_dir(preflight_dir)

    if cfg.execution_backend == "prompt-bundle":
        payload = {
            "checked_at": _now_iso(),
            "cli_available": False,
            "auth_ready": False,
            "auth_error": "",
            "auth_diagnostic": "prompt_bundle_backend",
            "auth_transport_hint": "",
            "allow_degraded_without_codex": True,
        }
        _write_json(preflight_dir / "preflight.json", payload)
        return payload

    if os.name == "nt" and cfg.codex_command.lower().endswith(".cmd"):
        command = ["cmd", "/c", cfg.codex_command, "exec", "--help"]
    else:
        command = [cfg.codex_command, "exec", "--help"]
    help_result = _run_subprocess(
        command,
        cwd=workspace,
        timeout_seconds=min(cfg.codex_preflight_timeout_seconds, 30),
    )
    _write_text(preflight_dir / "cli-help.stdout.log", help_result.stdout)
    _write_text(preflight_dir / "cli-help.stderr.log", help_result.stderr)

    cli_available = help_result.returncode == 0 and not help_result.timed_out
    auth_ready = False
    auth_error = ""
    auth_diagnostic = ""
    auth_transport = ""

    if cli_available:
        schema_path = SCHEMAS_DIR / "preflight.schema.json"
        output_file = preflight_dir / "auth.json"
        log_prefix = preflight_dir / "auth"
        try:
            payload = _run_codex_step(
                cfg=cfg,
                workspace=workspace,
                schema_path=schema_path,
                prompt=_build_preflight_prompt(),
                output_file=output_file,
                log_prefix=log_prefix,
                timeout_seconds=cfg.codex_preflight_timeout_seconds,
            )
            auth_ready = bool(payload.get("ok", False))
        except Exception as exc:
            auth_error = str(exc)
            stderr_log = log_prefix.with_suffix(".stderr.log")
            stderr_text = stderr_log.read_text(encoding="utf-8") if stderr_log.exists() else ""
            auth_diagnostic = _detect_auth_diagnostic(stderr_text)
            if "responses_websocket" in stderr_text or "wss://" in stderr_text:
                auth_transport = "websocket_or_http_fallback"
    else:
        auth_error = "codex exec --help failed"
        auth_diagnostic = "cli_unavailable"

    payload = {
        "checked_at": _now_iso(),
        "cli_available": cli_available,
        "auth_ready": auth_ready,
        "auth_error": auth_error,
        "auth_diagnostic": auth_diagnostic,
        "auth_transport_hint": auth_transport,
        "allow_degraded_without_codex": cfg.allow_degraded_without_codex,
    }
    _write_json(preflight_dir / "preflight.json", payload)
    return payload


def _run_degraded_round(
    cfg: OrchestratorConfig,
    *,
    workspace: Path,
    run_state: RunState,
    run_dir: Path,
    start_round: int,
) -> None:
    round_dir = run_dir / f"round_{start_round}"
    _ensure_dir(round_dir)
    round_state = RoundState(
        round_index=start_round,
        started_at=_now_iso(),
        mode="degraded",
        diff_summary_before=_git_diff_stat(workspace, run_state.target_paths),
        diff_files_before=_git_diff_names(workspace, run_state.target_paths),
    )
    round_state.validation = _run_validation(
        cfg,
        cfg.validation_commands,
        workspace=workspace,
        output_dir=round_dir / "validation",
    )
    round_state.diff_summary_after = _git_diff_stat(workspace, run_state.target_paths)
    round_state.diff_files_after = _git_diff_names(workspace, run_state.target_paths)
    round_state.changed_files = _git_diff_names(workspace, run_state.target_paths)
    round_state.decision = {
        "continue": False,
        "reason": "degraded_preflight_mode",
    }
    round_state.finished_at = _now_iso()
    run_state.rounds.append(round_state)
    run_state.mode = "degraded"
    run_state.status = "degraded"
    run_state.stop_reason = "preflight_failed_degraded_mode"
    if not bool(round_state.validation.get("passed", False)):
        run_state.memory_summary["regressions"].append("degraded mode validation failed")


def _run_prompt_bundle_round(
    cfg: OrchestratorConfig,
    *,
    workspace: Path,
    run_state: RunState,
    run_dir: Path,
    start_round: int,
) -> None:
    round_dir = run_dir / f"round_{start_round}"
    _ensure_dir(round_dir)
    round_state = RoundState(
        round_index=start_round,
        started_at=_now_iso(),
        mode="prompt-bundle",
        diff_summary_before=_git_diff_stat(workspace, run_state.target_paths),
        diff_files_before=_git_diff_names(workspace, run_state.target_paths),
    )
    prompts_dir = round_dir / "prompt_bundle"
    _ensure_dir(prompts_dir)

    check_prompt = _build_check_prompt(
        cfg,
        run_state.target_paths,
        round_index=start_round,
        memory_summary=run_state.memory_summary,
        prior_round=None,
    )
    fix_prompt = _build_fix_prompt(
        cfg,
        run_state.target_paths,
        round_index=start_round,
        check_payload={},
        prior_round=None,
        memory_summary=run_state.memory_summary,
    )
    review_prompt = _build_review_prompt(
        cfg,
        run_state.target_paths,
        round_state=round_state,
        memory_summary=run_state.memory_summary,
    )

    _write_text(prompts_dir / "check.prompt.md", check_prompt)
    _write_text(prompts_dir / "fix.prompt.md", fix_prompt)
    _write_text(prompts_dir / "review.prompt.md", review_prompt)
    instructions = [
        "# External Run Instructions",
        "",
        "This prompt bundle is host-neutral. It does not require Codex runtime integration.",
        "",
        "## Suggested sequence",
        "",
        "1. Run `check.prompt.md` in your preferred coding agent or CLI.",
        "2. Save the structured output from that run as `check.result.json` beside the prompt bundle if your host supports JSON output.",
        "3. Run `fix.prompt.md`, pasting or attaching the check output when the host cannot automatically chain context.",
        "4. Apply and validate code changes in the workspace.",
        "5. Run `review.prompt.md`, pasting or attaching the check result, fix summary, and validation result if needed.",
        "",
        "## Files",
        "",
        "- `check.prompt.md`: hotspot audit prompt",
        "- `fix.prompt.md`: behavior-preserving remediation prompt",
        "- `review.prompt.md`: post-fix review prompt",
        "- `bundle.json`: machine-readable prompt bundle manifest",
        "",
        "## Validation",
        "",
        "Validation commands were executed locally by the orchestrator when possible. See the sibling `validation/` directory for command logs and pass/fail status.",
        "If local dependency diagnostics were found, use them to fix the environment before treating smoke failures as code regressions.",
        "",
        "## Notes",
        "",
        "- Repository-specific overlays are already injected into the generated prompts when target paths matched an overlay rule.",
        "- If your host does not support skill names like `$memory-check`, keep the prompt text but remove the `$...` token and retain the instructions.",
        "- If your host cannot emit structured JSON, save its prose output separately and carry the relevant sections into the next prompt.",
        "",
    ]
    diagnostics = round_state.validation.get("dependency_diagnostics", []) or []
    if diagnostics:
        instructions.extend(["## Dependency Diagnostics", ""])
        for item in diagnostics:
            module = str(item.get("module", "") or "").strip()
            message = str(item.get("message", "") or "").strip()
            if module:
                instructions.append(f"- Missing Python module `{module}`: {message}")
            else:
                instructions.append(f"- {message}")
        instructions.append("")
    _write_text(prompts_dir / "README.md", "\n".join(instructions))
    _write_json(
        prompts_dir / "bundle.json",
        {
            "mode": "prompt-bundle",
            "round": start_round,
            "workspace": str(workspace),
            "targets": run_state.target_paths,
            "profile": cfg.profile_name,
            "files": {
                "check_prompt": str(prompts_dir / "check.prompt.md"),
                "fix_prompt": str(prompts_dir / "fix.prompt.md"),
                "review_prompt": str(prompts_dir / "review.prompt.md"),
                "instructions": str(prompts_dir / "README.md"),
            },
        },
    )

    round_state.validation = _run_validation(
        cfg,
        cfg.validation_commands,
        workspace=workspace,
        output_dir=round_dir / "validation",
    )
    round_state.decision = {"continue": False, "reason": "prompt_bundle_only"}
    round_state.finished_at = _now_iso()
    run_state.rounds.append(round_state)
    run_state.mode = "prompt-bundle"
    run_state.status = "completed"
    run_state.stop_reason = "prompt_bundle_generated"
    if not bool(round_state.validation.get("passed", False)):
        run_state.memory_summary["regressions"].append("prompt bundle validation failed")
    else:
        run_state.memory_summary["notes"].append("prompt bundle generated for external execution")


def _next_round_after_partial_rerun(run_state: RunState, partial_rerun_from_round: int) -> int:
    return partial_rerun_from_round


def _truncate_rounds_for_partial_rerun(run_state: RunState, partial_rerun_from_round: int) -> None:
    kept_rounds = [item for item in run_state.rounds if item.round_index < partial_rerun_from_round]
    run_state.rounds = kept_rounds
    run_state.partial_rerun_from_round = partial_rerun_from_round
    run_state.memory_summary = {"hotspots": [], "fixed_issues": [], "regressions": [], "notes": []}
    for item in run_state.rounds:
        _update_memory_summary(run_state, item)


def _copy_prior_round_artifacts(previous_run_dir: Path, new_run_dir: Path, upto_round_exclusive: int) -> None:
    for previous_round_dir in sorted(previous_run_dir.glob("round_*")):
        try:
            round_index = int(previous_round_dir.name.split("_", 1)[1])
        except Exception:
            continue
        if round_index >= upto_round_exclusive:
            continue
        target = new_run_dir / previous_round_dir.name
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
        shutil.copytree(previous_round_dir, target)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a bounded memory optimization orchestrator.")
    parser.add_argument("--config", help="YAML config path")
    parser.add_argument("--profile-name", help="Config profile name when config defines profiles")
    parser.add_argument("--label", default="", help="Optional run label suffix")
    parser.add_argument("--dry-run", action="store_true", help="Write the planned loop but do not call Codex")
    parser.add_argument("--list-runs", action="store_true", help="List recorded runs and exit")
    parser.add_argument("--dashboard", action="store_true", help="Rebuild dashboard and print its path")
    parser.add_argument("--resume-run", help="Resume a prior run directory or run name")
    parser.add_argument("--resume-latest-failed", action="store_true", help="Resume the latest failed run")
    parser.add_argument("--partial-rerun-from-round", type=int, help="Re-run from the specified round index on a resumed run")
    parser.add_argument("--rebuild-summary", help="Rebuild summary/index for a prior run and exit")
    parser.add_argument("--preflight-only", action="store_true", help="Run Codex preflight only and exit")
    args = parser.parse_args()

    if args.list_runs:
        return _list_runs()
    if args.dashboard:
        _write_dashboard()
        print(f"Dashboard written to {RUNS_DIR / 'dashboard.md'}")
        return 0

    if args.rebuild_summary:
        run_dir = _resolve_run_dir(args.rebuild_summary)
        run_state = _load_run_state(run_dir)
        _write_summary(run_dir, run_state)
        _write_dashboard()
        print(f"Rebuilt summary for {run_dir}")
        return 0

    resume_run_dir: Path | None = None
    if args.resume_latest_failed:
        resume_run_dir = _select_latest_failed_run()
    elif args.resume_run:
        resume_run_dir = _resolve_run_dir(args.resume_run)

    if resume_run_dir is None and not args.config:
        parser.error("--config is required unless using --list-runs, --dashboard, --rebuild-summary, or --resume-*")

    if args.partial_rerun_from_round is not None and args.partial_rerun_from_round < 1:
        parser.error("--partial-rerun-from-round must be >= 1")

    if resume_run_dir is not None:
        cfg = (
            _load_resolved_config(resume_run_dir, profile_override=args.profile_name)
            if not args.config
            else _load_config(Path(args.config).resolve(), profile_override=args.profile_name)
        )
        run_state = _load_run_state(resume_run_dir)
        run_state.resumed_from = str(resume_run_dir)
        run_state.status = "running"
        if not run_state.started_at:
            run_state.started_at = _now_iso()
        run_dir = _create_run_dir(args.label or f"resumed-{resume_run_dir.name}")
        _write_json(run_dir / "previous-run.json", _run_metadata(resume_run_dir))
        if args.partial_rerun_from_round is not None:
            _copy_prior_round_artifacts(resume_run_dir, run_dir, args.partial_rerun_from_round)
            _truncate_rounds_for_partial_rerun(run_state, args.partial_rerun_from_round)
    else:
        cfg = _load_config(Path(args.config).resolve(), profile_override=args.profile_name)
        run_state = None
        run_dir = _create_run_dir(args.label or None)

    config_path = Path(args.config).resolve() if args.config else (resume_run_dir / "resolved-config.json")
    workspace = _resolve_workspace(cfg.workspace_root, config_path)
    target_paths = _resolve_target_paths(workspace, cfg.target_paths)

    if run_state is None:
        run_state = RunState(
            workspace_root=str(workspace),
            target_paths=target_paths,
            started_at=_now_iso(),
            profile_name=cfg.profile_name,
        )
    else:
        run_state.workspace_root = str(workspace)
        run_state.target_paths = target_paths
        run_state.profile_name = cfg.profile_name

    _write_json(run_dir / "resolved-config.json", _resolved_config_payload(cfg, workspace, target_paths))
    _write_text(run_dir / "git-status-before.txt", _git_status(workspace))

    if args.dry_run:
        run_state.mode = "dry-run"
        run_state.status = "completed"
        run_state.stop_reason = "dry_run_only"
        run_state.finished_at = _now_iso()
        _run_dry_run(run_dir, cfg, workspace, target_paths)
        _write_run_artifacts(run_dir, run_state, workspace)
        print(f"Dry run written to {run_dir}")
        return 0

    try:
        if cfg.execution_backend == "prompt-bundle":
            if args.preflight_only:
                run_state.mode = "prompt-bundle"
                run_state.status = "completed"
                run_state.stop_reason = "prompt_bundle_preflight_skipped"
                run_state.finished_at = _now_iso()
                _write_run_artifacts(run_dir, run_state, workspace)
                print(f"Prompt-bundle mode does not require preflight. Artifacts: {run_dir}")
                return 0
            _run_prompt_bundle_round(cfg, workspace=workspace, run_state=run_state, run_dir=run_dir, start_round=1)
            run_state.final_fix_summary = "External fix execution required from generated prompt bundle."
            run_state.final_review_summary = "External review execution required from generated prompt bundle."
            run_state.finished_at = _now_iso()
            _write_run_artifacts(run_dir, run_state, workspace)
            print(f"Prompt bundle generated. Summary: {run_dir / 'summary.md'}")
            return 0

        if cfg.preflight_required:
            run_state.preflight = _run_preflight(cfg, workspace, run_dir)
            if args.preflight_only:
                run_state.mode = "preflight"
                run_state.status = "completed"
                run_state.stop_reason = "preflight_only"
                run_state.finished_at = _now_iso()
                _write_run_artifacts(run_dir, run_state, workspace)
                print(f"Preflight completed. Artifacts: {run_dir}")
                return 0
            if not bool(run_state.preflight.get("auth_ready", False)):
                if not cfg.allow_degraded_without_codex:
                    raise OrchestrationError(
                        f"Codex preflight failed and degraded mode is disabled. See {run_dir / 'preflight' / 'preflight.json'}"
                    )
                start_round = len(run_state.rounds) + 1
                _run_degraded_round(cfg, workspace=workspace, run_state=run_state, run_dir=run_dir, start_round=start_round)
                run_state.finished_at = _now_iso()
                run_state.final_fix_summary = ""
                run_state.final_review_summary = ""
                _write_run_artifacts(run_dir, run_state, workspace)
                print(f"Run completed in degraded mode. Summary: {run_dir / 'summary.md'}")
                return 0
        elif args.preflight_only:
            run_state.mode = "preflight"
            run_state.status = "completed"
            run_state.stop_reason = "preflight_skipped_by_config"
            run_state.finished_at = _now_iso()
            _write_run_artifacts(run_dir, run_state, workspace)
            print(f"Preflight skipped by config. Artifacts: {run_dir}")
            return 0

        if args.partial_rerun_from_round is not None:
            start_round = _next_round_after_partial_rerun(run_state, args.partial_rerun_from_round)
        else:
            start_round = len(run_state.rounds) + 1
        if start_round > cfg.max_rounds:
            run_state.status = "completed"
            run_state.stop_reason = "resume_exhausted_max_rounds"
            run_state.finished_at = _now_iso()
            _write_run_artifacts(run_dir, run_state, workspace)
            print(f"Run already exhausted max rounds. Summary: {run_dir / 'summary.md'}")
            return 0

        check_schema = SCHEMAS_DIR / "check.schema.json"
        fix_schema = SCHEMAS_DIR / "fix.schema.json"
        review_schema = SCHEMAS_DIR / "review.schema.json"

        for round_index in range(start_round, cfg.max_rounds + 1):
            round_dir = run_dir / f"round_{round_index}"
            _ensure_dir(round_dir)

            prior_round = run_state.rounds[-1] if run_state.rounds else None
            round_state = RoundState(
                round_index=round_index,
                started_at=_now_iso(),
                mode="full",
                diff_summary_before=_git_diff_stat(workspace, target_paths),
                diff_files_before=_git_diff_names(workspace, target_paths),
            )

            round_state.check = _run_codex_step(
                cfg=cfg,
                workspace=workspace,
                schema_path=check_schema,
                prompt=_build_check_prompt(
                    cfg,
                    target_paths,
                    round_index=round_index,
                    memory_summary=run_state.memory_summary,
                    prior_round=prior_round,
                ),
                output_file=round_dir / "check.json",
                log_prefix=round_dir / "check",
            )

            round_state.fix = _run_codex_step(
                cfg=cfg,
                workspace=workspace,
                schema_path=fix_schema,
                prompt=_build_fix_prompt(
                    cfg,
                    target_paths,
                    round_index=round_index,
                    check_payload=round_state.check,
                    prior_round=prior_round,
                    memory_summary=run_state.memory_summary,
                ),
                output_file=round_dir / "fix.json",
                log_prefix=round_dir / "fix",
            )

            round_state.diff_summary_after = _git_diff_stat(workspace, target_paths)
            round_state.diff_files_after = _git_diff_names(workspace, target_paths)
            round_state.changed_files = _git_diff_names(workspace, target_paths)
            _write_json(round_dir / "diff-summary.json", _git_diff_patch_summary(workspace, target_paths))

            round_state.validation = _run_validation(
                cfg,
                cfg.validation_commands,
                workspace=workspace,
                output_dir=round_dir / "validation",
            )

            round_state.review = _run_codex_step(
                cfg=cfg,
                workspace=workspace,
                schema_path=review_schema,
                prompt=_build_review_prompt(
                    cfg,
                    target_paths,
                    round_state=round_state,
                    memory_summary=run_state.memory_summary,
                ),
                output_file=round_dir / "review.json",
                log_prefix=round_dir / "review",
            )

            should_continue, decision_reason = _should_continue(cfg=cfg, round_state=round_state)
            round_state.decision = {
                "continue": should_continue,
                "reason": decision_reason,
            }
            round_state.finished_at = _now_iso()

            run_state.rounds.append(round_state)
            _update_memory_summary(run_state, round_state)

            if not should_continue:
                run_state.stop_reason = decision_reason
                break
        else:
            run_state.stop_reason = "loop_completed_without_break"

        last_round = run_state.rounds[-1] if run_state.rounds else None
        run_state.finished_at = _now_iso()
        run_state.final_fix_summary = (last_round.fix.get("summary", "") if last_round else "")
        run_state.final_review_summary = (last_round.review.get("summary", "") if last_round else "")
        run_state.status = "completed" if run_state.mode == "full" else run_state.status
        _write_run_artifacts(run_dir, run_state, workspace)
        print(f"Run completed. Summary: {run_dir / 'summary.md'}")
        return 0
    except Exception as exc:
        run_state.finished_at = _now_iso()
        run_state.status = "failed"
        run_state.stop_reason = f"error: {type(exc).__name__}: {exc}"
        _write_run_artifacts(run_dir, run_state, workspace)
        print(f"Run failed. See {run_dir}", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
