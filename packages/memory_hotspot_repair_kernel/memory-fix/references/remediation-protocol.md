# Memory Fix Remediation Protocol

Use this file as the portable decision protocol for behavior-preserving memory fixes.

## Goal

Apply the smallest change that materially reduces peak memory without silently changing business semantics, output contracts, or recovery behavior.

## Required Fix Fields

For each major applied fix, reason about these fields:

- `target_pattern_id`: the hotspot pattern being addressed
- `mitigation_pattern`: short stable label such as `stream-read`, `narrow-projection`, `direct-keyed-read`, `engine-side-writeout`, `copy-elimination`
- `contract_preserved`: short sentence describing the preserved external behavior
- `expected_peak_effect`: `large`, `medium`, or `small`
- `fallback_risk`: `high`, `medium`, or `low`
- `validation_needed`: `yes` or `no`

## Fix Priority

1. Eliminate full-result materialization.
2. Move chunking or streaming to the read boundary.
3. Replace repeated broad scans with direct keyed reads.
4. Remove unnecessary copies and conversion churn.
5. Keep ranking, aggregation, and writeout inside the engine longer.
6. Add spill and memory-safe config.
7. Reduce worker duplication.

## Red Lines

Do not do these unless the user explicitly asks for broader change:

- rewrite the full pipeline into a different framework
- change ranking, scoring, or business semantics to save memory
- remove checkpointing, skip behavior, overwrite behavior, or persistence contracts silently
- drop required columns or rows without an explicit config contract

## Validation Rules

Set `validation_needed` to `yes` when:

- the fix changes read boundaries, batching, fallback logic, or resume behavior
- the fix depends on version-sensitive APIs or spill behavior
- the fix is likely to move the peak into a downstream ranking or aggregation stage
- the smoke path can bypass the expensive branch

## Reporting Guidance

Use prose in the final report, but keep the above fields stable in the underlying reasoning so the fix can be reviewed or replayed consistently across projects.
