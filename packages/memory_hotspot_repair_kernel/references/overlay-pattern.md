# Repo Overlay Pattern

Use this pattern when you want a portable core skill plus repository-specific guidance.

## Goal

Keep project-specific knowledge out of the portable core while still making it easy to apply high-value local context.

## Structure

Use a small overlay file per active code line or project family. Good overlays usually contain:

- the target path or module family
- the runtime shape
- repeated hotspot patterns in that codebase
- behavior contracts that must not regress
- validation paths or smoke configs

## Rules

- Overlays are optional and additive.
- The core skill must still work without the overlay.
- Do not repeat generic pandas/DuckDB/Polars rules in the overlay.
- Only include project-local patterns, contracts, and pitfalls.
- Link overlays from the relevant core skills instead of embedding them in orchestration prompts alone.

## When To Read An Overlay

Read the overlay when:

- the target path clearly matches the overlay scope
- the repository has repeated hotspot shapes that general rules do not capture well
- validation depends on project-local configs or smoke paths

## Current Example

- `examples/<package-name>/<repo-name>/overlays/memory-check/...`
- `examples/<package-name>/<repo-name>/overlays/memory-fix/...`
- `examples/<package-name>/<repo-name>/overlays/memory-review/...`

## Generic Template

- `references/generic-overlay-template.md`

Copy that template when starting a new repository-specific overlay. In a multi-skill hub, keep example overlays outside the package body when they are repo-specific and optional.
