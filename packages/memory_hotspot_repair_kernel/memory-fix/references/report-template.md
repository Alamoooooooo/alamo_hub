# Memory Fix Report Template

Use this template when the user wants a formal write-up of the remediation work.

## Fix Summary

- Overall result:
- Main bottleneck addressed:
- Peak-memory reduction mechanism:
- Runtime impact expectation:

## Report Intake

- Source report:
- Findings addressed:
- Findings deferred:
- Assumptions confirmed in code:

## Stack Profile

- Runtime shape:
- Libraries involved:
- Storage formats involved:
- Model / inference components:
- Concurrency pattern:

## Applied Changes

- `path:line`:
  - change:
  - mitigation pattern:
  - expected memory effect:
- `path:line`:
  - change:
  - mitigation pattern:
  - expected memory effect:

## Fix Fields

- `target_pattern_id`:
- `mitigation_pattern`:
- `contract_preserved`:
- `expected_peak_effect`:
- `fallback_risk`:
- `validation_needed`:

## Behavior Preserved

- Input contract preserved:
- Output schema preserved:
- Checkpoint / resume preserved:
- Missing-model / missing-file behavior preserved:
- Ranking / scoring semantics preserved:

## Residual Risk

- Remaining hotspot:
- Why it still exists:
- Trigger condition:
- Expected severity:

## Validation

- Static checks:
- Smoke / bounded run:
- Configs used for validation:
- What was not validated:

## Suggested Follow-up

1. 
2. 
3. 
