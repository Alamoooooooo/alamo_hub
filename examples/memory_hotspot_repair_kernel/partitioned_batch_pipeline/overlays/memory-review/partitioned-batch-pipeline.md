# Overlay: partitioned_batch_pipeline

Use this overlay when reviewing memory-related changes under `src/pipelines/partitioned_batch_pipeline/`.

## High-Value Local Review Targets

- stale temp view or stale relation reuse across partition/batch loops
- fallback path drifting from the main processing path
- checkpoint or overwrite logic causing the changed code not to run
- aggregation/reporting becoming the new dominant peak
- output schema drift in batch-level artifacts

## Local Review Questions

- Did the fix really reduce broad scans of batch inputs?
- Did the change preserve partition-aware processing behavior?
- Did a narrowed projection drop fields still needed in later reporting or manifests?
- Does `smoke_configs` still exercise the changed branch, or is it masked by checkpoints or existing outputs?
