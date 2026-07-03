# Memory Review Protocol

Use this file as the portable decision protocol for post-fix review findings.

## Goal

Judge whether a memory-oriented fix is both correct and materially helpful, without silently changing contracts or moving the peak into a new unreviewed stage.

## Required Review Fields

For each major finding, reason about these fields:

- `finding_kind`: `general`, `memory-regression`, `fallback-bug`, `stale-state`, `residual-hotspot`, or `validation-gap`
- `blocking_level`: `block-now`, `should-fix`, or `can-defer`
- `claimed_improvement_verified`: `yes`, `partly`, or `no`
- `new_peak_risk`: `high`, `medium`, or `low`
- `behavior_regression_risk`: `high`, `medium`, or `low`
- `followup_needed`: `yes` or `no`

## Blocking Rules

Use `block-now` when at least one is true:

- the fix introduces a correctness bug
- the fallback path is broken, unreachable, or semantically inconsistent
- stale state, stale view, or stale relation reuse can produce wrong outputs
- output contracts, checkpoint/resume, or overwrite behavior are broken
- the claimed hotspot reduction is not real on the stated hot path

Use `should-fix` when:

- the main improvement is real, but a substantial residual hotspot or regression risk remains
- the fix moved the peak into a new stage that should be called out before merge
- the code remains safe enough to understand, but the next issue is still high-signal

Use `can-defer` when:

- the issue is secondary churn or maintainability cost after the main hotspot is already addressed
- the risk is bounded and clearly documented

## Review Priorities

1. correctness regression introduced by the optimization
2. fake improvement that did not actually reduce the real peak
3. stale-state or fallback bug
4. moved peak or residual hotspot
5. secondary cleanup and maintainability issues

## Reporting Guidance

Use prose in the final review, but keep the above fields stable in the underlying reasoning so reviews remain comparable across repos and hosts.
