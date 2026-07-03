---
name: memory-check
description: Review code for memory-risk patterns, likely out-of-memory failure points, wasteful data movement, and stack-specific memory hazards. Use when a user asks about memory overflow, OOM risk, high RAM usage, peak-memory hot spots, pandas/DuckDB/NumPy/Polars issues, parquet or CSV pipeline memory behavior, model inference memory, garbage-collection concerns, chunking strategy, or when Codex should produce a structured memory-check report for a codebase.
---

# Memory Check

Review memory behavior before proposing fixes. Focus on peak memory, not just steady-state usage.

This skill is designed as a portable core that can move across repositories and host agents. Keep host-specific triggering or orchestration details outside the core audit rules.

## Core Workflow

1. Detect the active stack and runtime shape first.
   - Read imports, helper wrappers, data readers, and main entrypoints.
   - Identify whether the path is batch, streaming, per-file, per-key, or global.
   - Match the checklist depth to the detected stack instead of loading every rule section.

2. Locate the first real materialization point.
   - Flag the first place large data becomes a Python object or eager in-memory engine result.
   - Treat fake chunking as full-memory execution when materialization happens before slicing.

3. Estimate peak-memory multipliers.
   - Count likely simultaneous copies of the largest object.
   - Note DataFrame -> NumPy -> model, Arrow -> pandas, or SQL -> pandas boundaries.
   - Treat worker-level duplication as multiplicative peak risk.

4. Check whether safeguards apply at the real hotspot.
   - Look for chunking, column pruning, sampling, recent-window filtering, temp spill, cleanup, and direct keyed reads.
   - Verify whether checkpoint/resume or cached outputs hide the true hot path during testing.

5. Produce a structured report with a stable decision protocol.
   - Separate reusable severity rules from prose wording.
   - Quote file paths and line numbers for every actionable finding.
   - State what is proven from code inspection versus what still needs runtime validation.

## Rule Layout

Use this skill in four layers:

1. Core policy and workflow in this file.
2. Decision protocol in `references/decision-protocol.md`.
3. Stack and pattern catalog in `references/checklist.md`.
4. Formal output template and citations in `references/report-template.md` and `references/source-citations.md`.

## Output Contract

When using this skill, produce:

- `Executive Summary`: one-paragraph risk assessment.
- `Stack Profile`: detected libraries, storage formats, model stack, concurrency model, and why they matter.
- `Hot Path`: where the largest objects are created, copied, transformed, and persisted.
- `Findings`: actionable findings grouped by severity with file paths and lines.
- `Existing Safeguards`: chunking, temp spill, sampling, pruning, release logic, checkpoint behavior.
- `Recommended Fix Order`: the shortest path to reduce peak memory safely.
- `Validation Gaps`: what cannot be proven from static review alone.

For each finding, prefer these stable fields in the reasoning even when the final report is prose:

- `severity`
- `pattern_id`
- `hot_path_stage`
- `why_peak_occurs`
- `confidence`
- `runtime_validation_needed`

## Reference Use

- Read `references/decision-protocol.md` before assigning severity on a non-trivial review.
- Read `references/checklist.md` for stack-specific trigger patterns, remediation hints, and findings language.
- Read `references/report-template.md` when you need a consistent report layout.
- Read `references/source-citations.md` when you need primary-source support for memory-hotspot claims or want to attach citations.
- Read `../references/overlay-pattern.md` when deciding whether to apply a repo-specific overlay.
- If the target is `src/segment_causal_pipeline_v2/`, read `references/overlays/segment-causal-pipeline-v2.md`.
- If a library appears in imports but is not covered well enough by memory intuition, search primary sources before finalizing the review.
