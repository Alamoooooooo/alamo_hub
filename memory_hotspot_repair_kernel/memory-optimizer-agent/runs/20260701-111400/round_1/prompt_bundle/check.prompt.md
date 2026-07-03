Use $memory-check to inspect this codebase and produce a structured memory risk report.

Focus on these paths: src/segment_causal_pipeline_v2/common.py, src/segment_causal_pipeline_v2/cate.py, src/segment_causal_pipeline_v2/recommendation_scoring.py, src/segment_causal_pipeline_v2/segment_level_recommendation_scoring.py, src/segment_causal_pipeline_v2/v2_settings.py

This is check round 1.

Select the single highest-value hotspot to fix next.

Preserve current pipeline semantics when reasoning about fixes.

Current run memory summary:

{
  "hotspots": [],
  "fixed_issues": [],
  "regressions": [],
  "notes": []
}

Return JSON matching the provided schema only.

Apply this repository-specific overlay if relevant:

Repository-specific overlay for `src/segment_causal_pipeline_v2`:
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

Additional instructions:
Focus on the remaining memory hotspots in the segment causal pipeline, especially:
- residual broad scans
- list(glob(...)) style path enumeration
- fake chunking
- final aggregation peaks
Prefer practical, codebase-specific findings over generic advice.