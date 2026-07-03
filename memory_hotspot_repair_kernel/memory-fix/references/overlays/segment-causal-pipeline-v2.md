# Overlay: segment_causal_pipeline_v2

Use this overlay when fixing memory hotspots under `src/segment_causal_pipeline_v2/`.

## Preferred Local Fix Shapes

- direct per-segment or per-product reads instead of broad global unions
- earlier column pruning before pandas or NumPy conversion
- one narrow working frame instead of parallel copies of source, work, encoded, and scored data
- engine-side writeout or persistence before optional readback

## Local Red Lines

- do not change ranking or scoring semantics to save memory
- do not silently change missing-model skip behavior
- do not break tmp_smoke validation paths or checkpoint location assumptions without an explicit contract update

## Local Validation Hints

- use the existing tmp_smoke YAMLs for bounded checks
- confirm that a fix did not just move the peak into final recommendation aggregation or bundle reporting
- verify that checkpointed runs do not bypass the changed path
