# Memory Optimizer Dry Run

- Workspace: `E:\alamowork\causalmlforguangfen\CausalModel_1w-main\CausalModel_1w-main`
- Targets: `src\segment_causal_pipeline_v2`
- Profile: `default`
- Max rounds: `2`
- Preflight required: `True`
- Allow degraded without Codex: `True`
- Codex timeout: `900s`
- Preflight timeout: `120s`
- Validation timeout default: `300s`

## Planned Loop

1. preflight Codex CLI/auth when enabled
2. memory-check
3. memory-fix
4. validation
5. memory-review
6. optional next round when signals justify it

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