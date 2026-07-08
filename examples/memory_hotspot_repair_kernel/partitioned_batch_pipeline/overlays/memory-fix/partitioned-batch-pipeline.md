# Overlay: partitioned_batch_pipeline

Use this overlay when fixing memory hotspots under `src/pipelines/partitioned_batch_pipeline/`.

## Preferred Local Fix Shapes

- direct per-partition or per-batch reads instead of broad global unions
- earlier column pruning before pandas or NumPy conversion
- one narrow working frame instead of parallel copies of source, work, transformed, and scored data
- engine-side writeout or persistence before optional readback

## Local Red Lines

- do not change batch ordering or output semantics to save memory
- do not silently change missing-input skip behavior
- do not break `smoke_configs` validation paths or checkpoint location assumptions without an explicit contract update

## Local Validation Hints

- use the existing `smoke_configs` YAMLs for bounded checks
- confirm that a fix did not just move the peak into final aggregation or bundle reporting
- verify that checkpointed runs do not bypass the changed path
