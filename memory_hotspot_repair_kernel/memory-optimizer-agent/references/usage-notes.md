# Usage Notes

In Codex-hosted environments, use prompts like:

- "Use $memory-optimizer-agent to optimize memory hotspots in `src/segment_causal_pipeline_v2`."
- "Use $memory-optimizer-agent on the current uncommitted changes and stop after 2 rounds."
- "Use $memory-optimizer-agent to check, fix, smoke, review, and summarize the remaining risks."

Use script entrypoints like:

- `python .codex/skills-review/memory-optimizer-agent/scripts/orchestrate.py --config <run.yaml>`
- `python .codex/skills-review/memory-optimizer-agent/scripts/orchestrate.py --config <run.yaml> --profile-name <profile>`
- `python .codex/skills-review/memory-optimizer-agent/scripts/orchestrate.py --config <run.yaml> --preflight-only`
- `python .codex/skills-review/memory-optimizer-agent/scripts/orchestrate.py --list-runs`
- `python .codex/skills-review/memory-optimizer-agent/scripts/orchestrate.py --dashboard`
- `python .codex/skills-review/memory-optimizer-agent/scripts/orchestrate.py --resume-latest-failed`
- `python .codex/skills-review/memory-optimizer-agent/scripts/orchestrate.py --resume-run <run-name> --partial-rerun-from-round 1`
- `python .codex/skills-review/scripts/sync_to_codex_home.py --dry-run`
- `python .codex/skills-review/scripts/sync_to_codex_home.py`

To reduce Codex dependence, set `execution_backend: prompt-bundle` in the YAML. That mode generates `check.prompt.md`, `fix.prompt.md`, and `review.prompt.md` plus validation artifacts, without requiring Codex CLI execution.
Validation commands in that mode will also try to resolve a usable Python interpreter automatically, preferring `python3` when `python` is unavailable.

Generic starting points:

- `references/generic.run.yaml`: host-integrated starter template for a new repo
- `references/generic.prompt_bundle.yaml`: host-neutral starter template for prompt-bundle mode
- `../generic-overlay-template.md`: repo-specific overlay starter template

## P3 Additions

- `profiles` let one YAML carry multiple run presets, selected by `--profile-name`.
- `dashboard` rebuilds `runs/dashboard.md` and `runs/dashboard.json`.
- partial rerun keeps earlier round artifacts and replays the loop from a chosen round.
- run creation now auto-deduplicates same-second timestamps instead of colliding.

## Recommended Profiles

- `fast`: 1 round for quick hotspot triage or first-pass checks
- `default`: 2 rounds for the normal bounded optimization loop
- `aggressive`: 3 rounds only when the user explicitly wants a deeper pass

## Best Fit

This agent is best when:

- the code already has obvious memory pressure or OOM symptoms
- there is a smoke config or bounded validation path
- the user wants one orchestrated pass instead of manually calling multiple skills
- the user wants per-round artifacts and a resumable audit trail under `runs/`
- the environment may occasionally lose Codex auth and needs preflight or degraded fallback

## Generic Backend

- `execution_backend: codex` keeps the current Codex-executed behavior.
- `execution_backend: prompt-bundle` avoids Codex runtime dependence and emits portable prompt bundles for any compatible agent or CLI.

## Generic Migration Flow

1. Copy `generic.run.yaml` or `generic.prompt_bundle.yaml`.
2. Change `workspace_root` and `target_paths` to the new repo.
3. Replace the placeholder validation command with repo-specific compile, test, or smoke commands.
4. Add a repo overlay only if the codebase has repeated local hotspot patterns that the core rules do not capture well.
5. If needed, start that overlay from `../generic-overlay-template.md` instead of copying an old repo's overlay blindly.

## Global Sync

- Use `python .codex/skills-review/scripts/sync_to_codex_home.py` to copy the repo-local skills into `$CODEX_HOME/skills` or `~/.codex/skills`.
- The sync script copies `memory-check`, `memory-fix`, `memory-review`, and `memory-optimizer-agent`.
- It intentionally skips `runs/`, `__pycache__/`, and `.pyc` artifacts.

## Overlay Fit

- If the target path is under `src/segment_causal_pipeline_v2/`, pair the portable core skills with the repo-specific overlays under each skill's `references/overlays/`.
- Keep project-specific guidance in overlays rather than stuffing it into `check_prompt_extra`, `fix_prompt_extra`, or `review_prompt_extra` unless the runtime needs a temporary adapter hint.

## Avoid Overuse

Do not use this agent when:

- the task is a tiny one-line fix
- the user only wants a code review
- the problem is primarily business-logic correctness rather than memory/runtime behavior

## Portability Note

- The workflow is portable.
- The `$memory-optimizer-agent` phrasing is not the portable part; it is only one host adapter.
- Keep reusable policy in the underlying skills and their references.
