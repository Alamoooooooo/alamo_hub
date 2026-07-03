# Overlay: segment_causal_pipeline_v2

Use this overlay when the target path is under `src/segment_causal_pipeline_v2/`.

## Runtime Shape

- Python pipeline with per-product and per-segment processing
- parquet-backed intermediate datasets
- model-scoring steps that cross pandas -> NumPy -> model boundaries
- smoke validation through `tmp_smoke` configs

## Repeated Hotspot Patterns

- broad parquet scans followed by filtering per segment or product
- `list(glob(...))` style path enumeration before keyed filtering
- fake chunking where data is fully materialized before batch slicing
- source frame, working frame, encoded frame, NumPy matrix, and predictions alive together
- final ranking, aggregation, or bundle reporting becoming the new peak after main-loop fixes
- checkpoint or existing outputs hiding the real expensive path during smoke validation

## Behavior Contracts To Preserve

- segment-aware ranking and scoring semantics
- missing-model skip behavior where already established
- checkpoint, overwrite, and resume behavior
- existing tmp_smoke config shape and output contract unless explicitly broadened

## Validation Hints

- Verify whether the smoke config actually exercises the hot path.
- Re-check `tmp_smoke/out/.checkpoints` when a resume path could skip the expensive branch.
- Treat final bundle/report outputs as possible secondary peaks even if the main scoring loop improves.
