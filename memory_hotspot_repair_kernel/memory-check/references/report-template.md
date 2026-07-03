# Memory Check Report Template

Use this template when the user wants a formal output document instead of an informal review.

## Executive Summary

- Overall memory-risk level:
- Main reason:
- Most urgent mitigation:

## Stack Profile

- Runtime shape:
- Libraries detected:
- Storage formats detected:
- Model / inference stack:
- Concurrency pattern:

## Hot Path

- Main input path:
- Largest materialization point:
- Largest copy / conversion point:
- Largest aggregation / ranking point:
- Final output / merge peak:

## Findings

### High Risk

- `path:line`:
- `path:line`:

### Medium Risk

- `path:line`:
- `path:line`:

### Low Risk / Notes

- `path:line`:
- `path:line`:

## Finding Fields

- `severity`:
- `pattern_id`:
- `hot_path_stage`:
- `evidence_kind`:
- `confidence`:
- `runtime_validation_needed`:

## Existing Safeguards

- Chunking / streaming:
- Column pruning:
- Sampling / recent-window filtering:
- Spill / temp storage:
- Cleanup / release:
- Checkpoint / resume:

## Recommended Fix Order

1. 
2. 
3. 

## Validation Gaps

- Missing runtime metric:
- Version-dependent uncertainty:
- Scale assumption:

## Citations

- Primary-source references used:
- Version-sensitive claims re-checked:
