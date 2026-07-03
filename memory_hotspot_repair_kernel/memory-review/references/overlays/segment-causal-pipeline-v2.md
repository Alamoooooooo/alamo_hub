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
