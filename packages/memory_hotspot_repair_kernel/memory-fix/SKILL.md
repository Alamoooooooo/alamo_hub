---
name: memory-fix
description: Apply safe, targeted fixes for memory bottlenecks based on a memory review report or direct code inspection. Use when a user wants Codex to remediate OOM risks, reduce peak memory, convert fake chunking to real chunking, shrink pandas/DuckDB/NumPy/Polars memory pressure, tune parquet or CSV ingestion, reduce model-scoring memory peaks, or implement low-risk memory improvements without changing the pipeline contract unnecessarily.
---

# Memory Fix

Use this skill after `memory-check` or when the memory hot path is already known. Prefer the smallest fix that meaningfully reduces peak memory.

This skill is the portable remediation core. Keep host-specific orchestration prompts and runtime wiring outside the remediation policy.

## Core Workflow

1. Reconfirm the hotspot before editing.
   - Read the report first when one exists.
   - Re-open cited files and confirm the real materialization boundary in code.
   - Treat prior findings as a prioritization guide, not as ground truth.

2. Protect behavior before changing internals.
   - Preserve input/output contracts, output schema, checkpoint behavior, skip behavior, and logging semantics unless the user explicitly broadens scope.
   - Prefer localized edits over framework rewrites.

3. Apply the least invasive fix with real peak-memory impact.
   - Eliminate full materialization before tuning downstream code.
   - Convert fake chunking to true chunking before reducing chunk size.
   - Remove unnecessary copies before redesigning feature engineering.

4. Re-check for moved peaks and secondary regressions.
   - A safer main loop can move the peak to final ranking, merge, grouped aggregation, writeback, or optional readback.
   - Re-check checkpoint/resume and fallback behavior after the fix.

5. Hand off to validation and post-fix review.
   - Prefer targeted smoke or bounded validation first.
   - Recommend an independent `memory-review` pass after substantial changes.

## Rule Layout

Use this skill in four layers:

1. Core remediation workflow in this file.
2. Remediation protocol in `references/remediation-protocol.md`.
3. Stack and fix pattern catalog in `references/fix-patterns.md`.
4. Intake and formal reporting in `references/report-intake.md` and `references/report-template.md`.

## Output Contract

When using this skill, produce:

- `Fix Summary`: what was changed and why it reduces peak memory.
- `Applied Changes`: file paths and the specific mitigation pattern used.
- `Behavior Preserved`: contracts intentionally kept stable.
- `Residual Risk`: remaining likely hot spots after the fix.
- `Suggested Follow-up`: next validation, next hotspot to address, and whether to run `memory-review`.

For each major fix, prefer these stable fields in the reasoning even when the final output is prose:

- `target_pattern_id`
- `mitigation_pattern`
- `contract_preserved`
- `expected_peak_effect`
- `fallback_risk`
- `validation_needed`

## Reference Use

- Read `references/remediation-protocol.md` before editing a non-trivial hotspot.
- Read `references/fix-patterns.md` for stack-specific remediation patterns.
- Read `references/report-intake.md` when the input is a `memory-check` report.
- Read `references/report-template.md` when the user wants a formal remediation report.
- Read `../references/overlay-pattern.md` when deciding whether to apply a repo-specific overlay.
- Recommend `../memory-review/SKILL.md` as the preferred independent post-fix review step when the main remediation is done.
- If the fix depends on version-sensitive library behavior, verify it from primary sources before editing.
