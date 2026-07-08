# Overlay: partitioned_batch_pipeline

Use this overlay when the target path is under `src/pipelines/partitioned_batch_pipeline/`.

## Runtime Shape

- Python pipeline with per-partition and per-batch processing
- parquet-backed intermediate datasets
- batch scoring steps that cross pandas -> NumPy -> compute boundaries
- smoke validation through `smoke_configs` configs

## Repeated Hotspot Patterns

- broad parquet scans followed by filtering per partition or batch key
- `list(glob(...))` style path enumeration before keyed filtering
- fake chunking where data is fully materialized before batch slicing
- source frame, working frame, transformed frame, NumPy matrix, and outputs alive together
- final aggregation or reporting becoming the new peak after main-loop fixes
- checkpoint or existing outputs hiding the real expensive path during smoke validation

## Behavior Contracts To Preserve

- partition-aware processing order and output semantics
- missing-input skip behavior where already established
- checkpoint, overwrite, and resume behavior
- existing `smoke_configs` shape and output contract unless explicitly broadened

## Validation Hints

- Verify whether the smoke config actually exercises the hot path.
- Re-check `smoke_configs/out/.checkpoints` when a resume path could skip the expensive branch.
- Treat final aggregation/report outputs as possible secondary peaks even if the main processing loop improves.
