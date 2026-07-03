# Memory Review Checklist

Use this after a memory-oriented code change. Start with normal code review, then add the memory-specific checks.

## 1. General Code Review Baseline

Check for:

- correctness regressions
- broken control flow or stale state reuse
- unreachable fallback paths
- compatibility risks
- output-contract drift
- checkpoint / resume / overwrite regressions
- missing cleanup on failure paths
- duplicated logic that is now inconsistent across files

Only raise issues that are actionable and likely to be fixed.

## 2. Memory Review Pass

### Real improvement or fake improvement?

- Did the change remove a true `.df()` / pandas full read, or just move it elsewhere?
- Did the change replace `SELECT *` with narrow projection where possible?
- Did the change replace a global scan with direct per-key or per-segment reads?
- Did the change reduce the number of simultaneously live copies?

### New correctness risks introduced by memory fixes

- view or relation reused with stale data
- fallback path no longer matches primary path semantics
- temporary part merge changes output ordering or dedup semantics
- chunk loop skips required columns or rows
- narrow projection accidentally drops fields still needed later
- resume / overwrite returns early before required outputs are refreshed

### New memory risks introduced by the fix

- many temporary parquet parts plus a large union step
- repeated rescans of the same source inside loops
- `list(glob(...))` or `list(part_paths)` growth becoming the new hotspot
- final grouped list/json aggregation now the dominant peak
- optional readback into pandas after engine-side writeout
- fallback path materializes more than the primary path

### Stack-specific checks

- **DuckDB**
  - does direct keyed read really avoid the broad `**/*.parquet` scan?
  - does fallback work on the deployed DuckDB version?
  - does `temp_directory` or spill config still apply on the actual hot path?
- **pandas**
  - are `copy()`, `to_numeric()`, `fillna()`, `astype()` loops still duplicating large frames?
  - was row-wise `apply(...)` removed from large result frames?
- **Arrow**
  - can the reader be constructed in environments without full Arrow support?
  - does failure happen before fallback is reached?
- **Model scoring**
  - does the fix keep source frame, work frame, encoded frame, NumPy matrix, and predictions alive together longer than necessary?

## 3. Review Outcome Guidance

- **Block now**
  - correctness bug
  - fallback bug
  - stale-view / stale-state bug
  - output-contract regression
  - likely OOM still present in the claimed fixed path
- **Call out but can defer**
  - residual hotspot with bounded scope
  - maintainability issue that does not threaten correctness
  - secondary memory churn after the main OOM source is already fixed

## 4. Findings Language

- "This fix reduces the main pandas materialization, but it leaves the final grouped aggregation as the new likely peak."
- "The fallback path appears unreachable because reader initialization can fail before the fallback branch runs."
- "This segment loop can reuse the prior segment's temp view, so metrics may be computed from stale data."
- "The change improves scan locality by reading the current segment directly instead of scanning the global eval view."
- "This still enumerates all matching files into Python before filtering, so memory and scan cost remain higher than necessary."
