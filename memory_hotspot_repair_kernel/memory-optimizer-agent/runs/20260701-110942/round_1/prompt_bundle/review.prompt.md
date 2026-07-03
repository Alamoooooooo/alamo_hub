Use $memory-review to review the current uncommitted changes.

Start from normal code review, then add memory-specific regression checks.

Focus on these paths: src/segment_causal_pipeline_v2/common.py, src/segment_causal_pipeline_v2/cate.py, src/segment_causal_pipeline_v2/recommendation_scoring.py, src/segment_causal_pipeline_v2/segment_level_recommendation_scoring.py, src/segment_causal_pipeline_v2/v2_settings.py

This is review round 1.

Round check report:

{}

Round fix report:

{}

Validation results:

{}

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

Use this overlay when reviewing memory-related changes under `src/segment_causal_pipeline_v2/`.

## High-Value Local Review Targets

- stale temp view or stale relation reuse across segment/product loops
- fallback path drifting from the main scoring path
- checkpoint or overwrite logic causing the changed code not to run
- bundle/report aggregation becoming the new dominant peak
- output schema drift in recommendation or segment-level artifacts

## Local Review Questions

- Did the fix really reduce broad scans of eval or scoring inputs?
- Did the change preserve segment-aware ranking behavior?
- Did a narrowed projection drop fields still needed in later reporting or manifests?
- Does tmp_smoke still exercise the changed branch, or is it masked by checkpoints or existing outputs?

Additional instructions:
Review specifically for correctness regressions introduced by memory optimizations in:
- fallback behavior
- stale temp views / stale relations
- output contracts
- resume / overwrite behavior