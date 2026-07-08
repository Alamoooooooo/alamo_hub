# Partitioned Batch Pipeline Example

This directory is a sanitized example for the `memory_hotspot_repair_kernel` package.

It is intended to demonstrate:

- how a repo-specific example can provide run configs
- how `memory-check`, `memory-fix`, and `memory-review` overlays can be organized
- how a large-data batch pipeline can be represented in a portable, shareable form

This example does **not** represent:

- a real production repository
- real business naming
- real source file layout from a private codebase
- a one-to-one snapshot of any internal pipeline

Interpret this directory as a reference template, not as a literal source-code export.

## What Is Included

- `partitioned_batch_pipeline.prompt_bundle.yaml`
- `partitioned_batch_pipeline.run.yaml`
- `partitioned_batch_pipeline.run.linux.yaml`
- `overlays/memory-check/`
- `overlays/memory-fix/`
- `overlays/memory-review/`

## How To Use It

Use this example when you want to understand:

- how to adapt the package to one concrete pipeline shape
- how to structure a bounded validation flow
- how to keep project-local rules outside the portable core package

When migrating to a new repository, replace the placeholder paths, commands, and local assumptions with the real ones from the target environment.

## Sanitization Note

Names such as `partitioned_batch_pipeline`, `batch_score.py`, and `smoke_configs/` are generic placeholders chosen for explanation and portability.

They should be read as representative example labels rather than leaked identifiers from an original codebase.
