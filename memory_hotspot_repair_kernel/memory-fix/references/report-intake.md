# Report Intake

Use this when the input is a `memory-check` report.

## Intake Steps

1. Read `High Risk` first.
2. Confirm each cited hotspot in code before editing.
3. Compare `Existing Safeguards` against the actual hot path.
4. Treat `Recommended Fix Order` as a starting point, not a constraint.
5. Re-check `Validation Gaps` before claiming the issue is solved.

## How To Prioritize

- Fix the earliest peak in the pipeline first.
- Prefer changes that reduce both runtime and memory.
- Prefer config-backed narrowing when it preserves semantics.
- Prefer local fixes over cross-module redesign unless local fixes cannot work.

## How To Write Back

When handing results to the user:

- tie each fix to a report finding
- state what contract was preserved
- call out any unresolved hotspots that were intentionally left for a later pass
