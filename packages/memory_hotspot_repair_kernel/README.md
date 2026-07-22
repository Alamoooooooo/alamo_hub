# Memory Hotspot Repair Kernel

`memory_hotspot_repair_kernel` is an installable and portable AI coding-agent skill package for diagnosing and fixing memory hotspots in real codebases.

It is designed for workflows such as:

- Python memory usage keeps growing
- pandas, DuckDB, NumPy, or Polars pipelines materialize too much data
- model scoring or feature engineering creates avoidable copy churn
- a repository needs a repeatable check -> fix -> validate -> review loop

## Primary Entry Point

The main entry point is `memory-optimizer-agent`.

It orchestrates:

1. `memory-check`
2. `memory-fix`
3. validation
4. `memory-review`
5. a bounded stop-or-continue decision

## Included Skills

- `memory-check`: inspect memory-risk patterns and hot paths
- `memory-fix`: apply safe, targeted memory fixes
- `memory-review`: review changes for correctness and memory regression risk
- `memory-optimizer-agent`: coordinate the bounded optimization loop

## Best Fit

Use this package when you want:

- a Codex skill for memory hotspot optimization
- a portable agent workflow that can be adapted outside Codex
- repeatable memory engineering guidance rather than a single prompt
- structured reports and bounded iteration instead of open-ended tuning

## Start Here

- For Codex: read `../README.md`, then run `python3 scripts/sync_to_codex_home.py`
- For other hosts: read `PORTABLE_USAGE.md`
- For the orchestration contract: read `memory-optimizer-agent/SKILL.md`
- For the long-form background and sharing article: read [Memory Skill Suite Wiki](wiki/memory-skill-suite-wiki.md)

## Metadata

This package also includes machine-readable metadata in `metadata.json`.
