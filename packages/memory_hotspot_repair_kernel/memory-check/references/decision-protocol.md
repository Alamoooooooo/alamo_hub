# Memory Check Decision Protocol

Use this file as the portable rule protocol for classifying memory-hotspot findings.

## Goal

Produce findings that are comparable across repositories and host agents. Separate:

- what pattern was detected
- where it occurs
- why it creates peak memory
- how severe it is
- what still needs runtime proof

## Required Finding Fields

Every actionable finding should be reasoned about with these fields:

- `severity`: `high`, `medium`, or `low`
- `pattern_id`: short stable identifier such as `full-materialization`, `fake-chunking`, `global-sort-peak`, `worker-duplication`
- `hot_path_stage`: `read`, `transform`, `model`, `aggregate`, `writeback`, or `validation`
- `evidence_kind`: `code-inspection`, `config-default`, `runtime-metric`, or `primary-source`
- `why_peak_occurs`: one short sentence explaining the memory multiplier or blocking operator
- `confidence`: `high`, `medium`, or `low`
- `runtime_validation_needed`: `yes` or `no`

## Severity Rules

### High

Use `high` when at least one is true:

- the path fully materializes operational-scale data into Python or an eager engine result
- the code keeps multiple same-size copies alive on the hot path
- a global sort, window, grouped list/json aggregation, or similar blocking step runs over the full scored dataset
- each worker loads a large independent copy of data, models, or feature maps
- a spill-sensitive DuckDB path runs in `:memory:` mode or without usable temp spill configuration

### Medium

Use `medium` when the path is likely to scale poorly but is not yet an obvious first OOM point:

- recursive broad scans are filtered later instead of reading a keyed subset
- path enumeration or `UNION ALL` construction keeps large intermediate Python state
- already-persisted outputs are read back into pandas only for convenience
- conversion churn or wide per-column transforms create substantial temporary allocation pressure

### Low

Use `low` when the pattern is real but not likely to dominate peak memory:

- the data volume is naturally bounded
- the object is metadata-sized
- the copy or allocation is small and localized

## Confidence Rules

- `high`: directly visible hotspot in the current code path and no major ambiguity about scale behavior
- `medium`: likely hotspot, but exact scale or fallback behavior depends on data shape or runtime config
- `low`: pattern exists, but impact depends heavily on missing runtime context

## Validation Rules

Set `runtime_validation_needed` to `yes` when:

- checkpoint or resume logic can skip the expensive path
- smoke data is likely too small to expose the peak
- the fix depends on version-sensitive APIs or engine fallback behavior
- the likely new peak is in final ranking, aggregation, or writeback rather than the main loop

## Preferred Fix Priority

1. Eliminate full materialization.
2. Move chunking or streaming to the read boundary.
3. Replace broad scans with direct per-key or per-part reads.
4. Reduce duplicate copies and conversion churn.
5. Add spill and memory controls.
6. Reduce worker duplication.

## Reporting Guidance

Use prose in the final report, but keep the above fields stable in the underlying reasoning. This lets host-specific orchestrators make better continue/stop decisions without coupling the core skill to one prompt style.
