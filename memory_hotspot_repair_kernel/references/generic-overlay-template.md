# Generic Overlay Template

Use this as the starting point when a new repository needs repo-specific guidance on top of the portable memory skills.

Keep this file short. Only include patterns and contracts that are truly local to the repository.

## Overlay Scope

- Repository or module family:
- Matching target paths:
- Main runtime shape:

## Repeated Local Hotspot Patterns

- broad scan or broad enumeration pattern:
- fake chunking pattern:
- repeated copy or conversion pattern:
- final aggregation or reporting peak:
- worker duplication or model-loading pattern:

## Local Behavior Contracts To Preserve

- ranking / scoring semantics:
- checkpoint / resume behavior:
- overwrite behavior:
- skip / fallback behavior:
- output schema or persisted artifact contract:

## Local Validation Hints

- bounded smoke path:
- compile or syntax checks:
- known expensive branch to make sure validation really exercises:
- dependency prerequisites:

## Local Review Targets

- stale temp view or stale cached relation risk:
- fallback path drift risk:
- moved peak risk:
- output contract drift risk:

## Notes

- Do not repeat general pandas, DuckDB, Arrow, NumPy, or Polars rules here.
- If the repository does not have repeated local patterns, do not create an overlay.
