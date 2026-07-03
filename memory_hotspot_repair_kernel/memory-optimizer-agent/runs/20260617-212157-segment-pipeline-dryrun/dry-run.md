# Memory Optimizer Dry Run

- Workspace: `E:\alamowork\causalmlforguangfen\CausalModel_1w-main\CausalModel_1w-main\.codex\skills-review\memory-optimizer-agent\references`
- Targets: `src\segment_causal_pipeline_v2\common.py, src\segment_causal_pipeline_v2\cate.py, src\segment_causal_pipeline_v2\recommendation_scoring.py, src\segment_causal_pipeline_v2\segment_level_recommendation_scoring.py, src\segment_causal_pipeline_v2\v2_settings.py`
- Max rounds: `2`

## Planned Loop

1. memory-check
2. memory-fix
3. validation
4. memory-review
5. optional second fix/validation/review round if blocking findings remain

## Validation Commands

- `py_compile_segment_pipeline` (powershell): `@'
import py_compile
files = [
    "src/segment_causal_pipeline_v2/common.py",
    "src/segment_causal_pipeline_v2/cate.py",
    "src/segment_causal_pipeline_v2/recommendation_scoring.py",
    "src/segment_causal_pipeline_v2/segment_level_recommendation_scoring.py",
    "src/segment_causal_pipeline_v2/v2_settings.py",
]
for f in files:
    py_compile.compile(f, doraise=True)
    print("OK", f)
'@ | python -
`
- `smoke_segment_level_scoring` (powershell): `python src/segment_causal_pipeline_v2/segment_level_recommendation_scoring.py --config src/segment_causal_pipeline_v2/tmp_smoke/segment_level_recommendation_scoring_smoke.yaml
`
- `smoke_recommendation_scoring` (powershell): `python src/segment_causal_pipeline_v2/recommendation_scoring.py --config src/segment_causal_pipeline_v2/tmp_smoke/recommendation_scoring_smoke.yaml
`