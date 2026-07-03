# Memory Optimizer Dry Run

- Workspace: `E:\alamowork\causalmlforguangfen\CausalModel_1w-main\CausalModel_1w-main`
- Targets: `src\segment_causal_pipeline_v2`
- Max rounds: `2`
- Codex timeout: `900s`
- Validation timeout default: `300s`

## Planned Loop

1. memory-check
2. memory-fix
3. validation
4. memory-review
5. optional second/third check-fix-validation-review round if signals justify it

## Validation Commands

- `py_compile_segment_pipeline` (auto, timeout=60s): `@'
import py_compile
files = [
    "src/segment_causal_pipeline_v2/common.py",
    "src/segment_causal_pipeline_v2/cate.py",
    "src/segment_causal_pipeline_v2/recommendation_scoring.py",
    "src/segment_causal_pipeline_v2/segment_level_recommendation_scoring.py",
]
for f in files:
    py_compile.compile(f, doraise=True)
    print("OK", f)
'@ | python -
`
- `segment_level_smoke` (auto, timeout=180s): `python src/segment_causal_pipeline_v2/segment_level_recommendation_scoring.py --config src/segment_causal_pipeline_v2/tmp_smoke/segment_level_recommendation_scoring_smoke.yaml
`