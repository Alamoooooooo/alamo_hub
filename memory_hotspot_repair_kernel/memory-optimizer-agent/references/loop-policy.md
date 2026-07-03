# Memory Optimizer Loop Policy

Use this as the controller for each run.

## Round 1

1. Run `memory-check`
2. Pick the top hotspot
3. Run `memory-fix`
4. Validate the changed path
5. Run `memory-review`
6. Decide stop or continue

## Round 2

Run only if Round 1 review leaves a high-signal issue:

1. re-run `memory-check` on the updated code state
2. fix the current top hotspot or blocking review finding
3. validate again
4. review again
5. stop unless the user explicitly asked for more rounds

## Round State

Each round should carry:

- check payload
- fix payload
- validation payload
- review payload
- diff summary before fix
- diff summary after fix
- changed files
- continue / stop decision

This is not just logging; it is the decision state for the next round.

## Decision Signals

Primary continue signals:

- blocking findings remain
- validation failed and follow-up is enabled
- review explicitly recommends continuing

Primary stop signals:

- validation passed and there are no blocking findings
- review explicitly recommends stopping
- no meaningful diff impact remains
- max rounds reached

Validation must feed the next round; it is not a side log.

## Preflight and Degraded Mode

Before running full rounds:

- check whether Codex CLI is callable
- check whether non-interactive auth is usable

If preflight fails:

- either stop immediately when degraded mode is disabled
- or run degraded mode:
  - skip check/fix/review
  - run validation only
  - emit a summary that the agent framework is healthy but Codex auth is unavailable

## Resume and Replay

- A run may be resumed from a prior failed run ledger.
- Resume should continue from the next round when possible.
- Partial rerun may discard round state from a chosen round onward and replay from there.
- Summary rebuild and run listing should work even when a run failed midway.

## Continue Decision

Continue only when all are true:

- there is a concrete remaining issue worth fixing now
- the next fix is local and behavior-preserving
- validation for the previous round passed or failed in a way the next fix addresses
- the improvement is expected to be meaningful

## Stop Decision

Stop when any is true:

- only low-priority findings remain
- the review says the main risk is already reduced enough
- the next change would be speculative
- the next step needs broader redesign
- validation uncertainty is better handled by the user in a fuller environment

## Escalation Cases

Pause and surface tradeoffs instead of auto-continuing when:

- the next fix changes output meaning
- the next fix changes ranking / scoring semantics
- the next fix changes checkpoint or resume behavior
- the next fix requires broad config or data-layout changes

## Minimal Ledger

Record for each round:

- hotspot addressed
- files changed
- validation command(s)
- validation outcome
- review outcome
- stop / continue decision
