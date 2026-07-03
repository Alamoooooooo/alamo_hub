---
name: memory-review
description: Review code changes after a memory-oriented fix using Codex-style general code review as the baseline, then add memory-specific checks for peak RAM, scan amplification, fallback safety, chunking correctness, spill behavior, and regression risk. Use when a user wants an independent post-fix review, wants to validate memory-related changes before merge, or wants follow-up findings and optionally additional fixes after memory optimization work.
---

# Memory Review

Review the current code changes the same way a strong general code review would, then add memory-specific scrutiny. Treat correctness first, then memory, then maintainability.

This skill is the portable post-fix review core. Keep host-specific review prompt wiring outside the review policy.

## Core Workflow

1. Start from normal code review.
   - Inspect the current diff, not just the final files.
   - Look for correctness, compatibility, maintainability, and regression risk introduced by the change.
   - Prefer discrete findings the author would actually fix.

2. Then run the memory-specialized pass.
   - Re-open the hot-path files touched by the change.
   - Check whether the intended memory fix actually moved the materialization boundary, reduced copies, reduced scans, or reduced worker duplication.
   - Check whether the fix merely moved the peak into a later ranking, merge, aggregation, manifest, or optional readback step.

3. Review the change as a behavior-preserving optimization.
   - Verify checkpoint/resume, overwrite behavior, skip behavior, output contracts, and logging semantics.
   - Be suspicious of changes that reduce memory by silently changing what is read, scored, ranked, filtered, or written.

4. Report actionable findings only.
   - Prioritize correctness and regression findings over style commentary.
   - If the user asks for issue-only review, keep the output concise and report only actionable findings.

## Rule Layout

Use this skill in four layers:

1. Core post-fix review workflow in this file.
2. Review protocol in `references/review-protocol.md`.
3. Combined review checklist in `references/review-checklist.md`.
4. Formal output template in `references/review-template.md`.

## Output Contract

When using this skill, produce:

- `Review Summary`: overall assessment of the change quality and residual risk.
- `General Findings`: correctness / compatibility / maintainability issues from normal code review.
- `Memory Findings`: issues specific to peak memory, scan amplification, fallback behavior, or hidden new peaks.
- `What Improved`: which memory risks were actually reduced by the change.
- `Residual Hotspots`: remaining likely hot paths after the fix.
- `Fix Recommendation`: which findings to fix now vs. defer.

For each major finding, prefer these stable fields in the reasoning even when the final output is prose:

- `finding_kind`
- `blocking_level`
- `claimed_improvement_verified`
- `new_peak_risk`
- `behavior_regression_risk`
- `followup_needed`

## Reference Use

- Read `references/review-protocol.md` before writing a non-trivial post-fix review.
- Read `references/review-checklist.md` for the combined general-review + memory-review checklist.
- Read `references/review-template.md` when the user wants a formal post-fix review document.
- Read `../references/overlay-pattern.md` when deciding whether to apply a repo-specific overlay.
- Read `../memory-check/references/checklist.md` when you need deeper memory-risk heuristics.
- Read `../memory-fix/references/fix-patterns.md` when judging whether a remediation pattern was applied correctly.
- If the change depends on library-version behavior, verify it from primary sources before making a claim.
