---
name: memory-optimizer-agent
description: Orchestrate a bounded memory-optimization loop over a codebase by chaining memory-check, memory-fix, smoke validation, and memory-review until the main memory risks are reduced or the stop conditions are met. Use when a user wants one dedicated mini-agent to drive check-fix-smoke-review cycles, converge on practical memory improvements, and stop safely without infinite optimization loops.
---

# Memory Optimizer Agent

Act like a dedicated mini-agent that coordinates `memory-check`, `memory-fix`, and `memory-review`. Optimize for safe convergence, not for endless looping.

This skill is the host-adapter and orchestration layer. Keep reusable memory-hotspot policy in the underlying skills and their `references/` files, not in the orchestration prompts.

## Core Policy

- Run a bounded loop, not an infinite one.
- Preserve behavior and contracts unless the user explicitly asks for broader change.
- Treat correctness and validation failures as higher priority than further optimization.
- Prefer one meaningful fix over many speculative edits.

## Default Loop

1. Run `memory-check`.
2. Select the highest-value fix target.
3. Run `memory-fix`.
4. Run focused validation:
   - `py_compile` or equivalent syntax checks
   - targeted smoke or bounded config when available
5. Run `memory-review`.
6. Decide whether another round is justified.
7. If yes, do one more `fix -> validate -> review` round.
8. Stop and summarize.

In the executable orchestrator, every round re-runs `check` so the next fix is based on the current code state rather than the original hotspot report.

## Stop Conditions

Stop immediately when any of these is true:

- no new `High` / `P1` / `P2` issue remains in the reviewed hot path
- smoke passes and remaining issues are low priority
- the last round produced no meaningful reduction in risk
- the next fix would require changing business semantics or I/O contract
- the remaining risk cannot be resolved without new user input, new data, or broader refactor

## Round Limits

- Default: at most **2 rounds**
  - round 1: `check -> fix -> validate -> review`
  - round 2: `fix -> validate -> review` only if high-signal issues remain
- Only go to **3 rounds** if the user explicitly asks for a more aggressive optimization pass.

## Prioritization Rules

Fix in this order:

1. correctness bug introduced by an optimization
2. fake chunking or full materialization still on the hot path
3. stale view / stale relation / broken fallback
4. repeated broad scan that should be direct keyed read
5. unnecessary copy churn or optional readback peak
6. secondary cleanup and maintainability issues

## Validation Policy

- Validate after every applied fix round.
- Prefer the smallest validation that proves the changed path still works.
- If a smoke config exists, use it before broader runs.
- If validation is impossible, say exactly what remains unproven.
- Feed validation results into the next fix/review decision instead of treating them as logging only.

## Runtime Features

The executable orchestrator supports:

- Codex CLI preflight
- degraded validation-only fallback when Codex auth is unavailable
- per-run ledgers and summaries under `runs/`
- run listing / summary rebuild
- resume from a prior failed run
- config profiles via `profiles` + `--profile-name`
- partial rerun from a chosen round on resumed runs
- dashboard generation for run inventory and status

## Output Per Run

Produce:

- `Loop Summary`: rounds executed and why the loop stopped
- `Round Results`: check, fix, validation, and review outcomes by round
- `Applied Fixes`: files changed and why
- `Validated Paths`: what smoke or bounded checks were run
- `Residual Risks`: what still remains and why
- `Next Best Move`: whether to stop, continue manually, or broaden scope

## Reference Use

- Read `references/loop-policy.md` for the precise round controller and stop rules.
- Read `references/host-adapter.md` when changing prompt wiring, CLI invocation, or other Codex-specific behavior.
- Read `references/report-template.md` when the user wants a formal optimization-run report.
- Read `references/usage-notes.md` for prompt patterns and fit guidance.
- Prefer `scripts/orchestrate.py` for deterministic multi-round execution.
- Read `references/config-example.yaml` before preparing a real run config.
- Use `../memory-check/SKILL.md` for the audit phase.
- Use `../memory-fix/SKILL.md` for the remediation phase.
- Use `../memory-review/SKILL.md` for the post-fix review phase.

## Execution Notes

- The real orchestrator entrypoint is `scripts/orchestrate.py`.
- It drives Codex CLI non-interactively, stores per-round artifacts under `runs/`, and writes a final `summary.md`.
- It maintains per-round state for `check`, `fix`, `validation`, `review`, diff summaries, changed files, and continue/stop decisions.
- It can run in `full`, `degraded`, or `preflight` mode depending on environment readiness.
- Do not loop just because a low-value cleanup remains.
- Do not apply a second fix round until the first round has been validated and reviewed.
- If the review finds a correctness regression, fix that before pursuing more memory gains.
- Keep a short per-round ledger of:
  - target hotspot
  - fix applied
  - validation result
  - review result
  - continue / stop decision
