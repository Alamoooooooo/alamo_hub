Use $memory-fix to apply safe, targeted code changes for the current highest-value memory issue.

Restrict the main edits to these paths unless a helper change is necessary: src/segment_causal_pipeline_v2/common.py, src/segment_causal_pipeline_v2/cate.py, src/segment_causal_pipeline_v2/recommendation_scoring.py, src/segment_causal_pipeline_v2/segment_level_recommendation_scoring.py, src/segment_causal_pipeline_v2/v2_settings.py

Preserve behavior, output contracts, checkpoint logic, overwrite logic, and missing-model skip behavior unless explicitly required.

This is fix round 1.

Current check report:

{}

Current run memory summary:

{
  "hotspots": [],
  "fixed_issues": [],
  "regressions": [],
  "notes": []
}

Return JSON matching the provided schema only after applying changes.

Apply this repository-specific overlay if relevant:

Repository-specific overlay for `src/segment_causal_pipeline_v2`:
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

Additional instructions:
Prefer minimal, behavior-preserving fixes in the segment causal pipeline.
Do not broaden scope outside the listed files unless a tiny helper change is required.