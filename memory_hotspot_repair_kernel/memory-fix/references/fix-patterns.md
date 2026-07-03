# Memory Fix Patterns

Use these patterns after confirming the hot path in code.

## pandas

### Prefer

- read fewer columns up front
- process per chunk and write immediately
- keep one narrow working frame
- avoid repeated `copy()`, `astype()`, `fillna()`, `to_numeric()` passes over many columns
- use `map`, masked assignment, or lookup dicts instead of row-wise `apply(...)`

### Avoid

- full `read_parquet()` / `read_csv()` when only a subset is needed
- building a list of many frames then `pd.concat(...)`
- keeping source, work, encoded, and scored frames alive together longer than necessary

## DuckDB

### Prefer

- direct per-key reads instead of broad `**/*.parquet` scans when possible
- direct per-segment reads when downstream processing already loops by `segment_name`
- streaming readers or bounded batch fetches
- `temp_directory` and related memory-safe config
- engine-side ranking, filtering, and parquet writeout
- narrow `SELECT` projection before `.df()` or pandas conversion

### Avoid

- `.df()` / `.fetchdf()` for large intermediate results
- `:memory:` for spill-heavy workloads
- broad grouped list/json aggregations if a simpler persisted representation works

## Parquet / CSV

### Prefer

- projection before materialization
- row-window pruning before pandas
- one-pass keyed reads

### Avoid

- reading all files first and filtering later in Python
- repeated scans of the same files for each key

## Polars

### Prefer

- keep scans lazy as long as possible
- push projection and filtering before `collect()`
- use streaming or sink-style output when the operation supports it

### Avoid

- early `collect()` on data that can stay lazy
- converting large Polars frames to pandas before the final boundary
- full-data sorts or joins before column and row pruning

## NumPy / Model Inference

### Prefer

- narrow dtypes where numerically safe
- short-lived arrays
- per-product or per-batch scoring with immediate persistence

### Avoid

- full-frame `.to_numpy()` while several same-size pandas copies still exist
- loading the same large model and mappings in too many workers

## GC / Cleanup

### Prefer

- explicit release of large locals after each chunk/product
- cleanup after persistence, not only at process end

### Avoid

- relying on `gc.collect()` while references are still retained

## Typical Fix Mapping

- `High Risk: full materialization` -> move to streaming/batching or engine-side writeout
- `High Risk: fake chunking` -> chunk at the data source
- `High Risk: global ranking` -> keep ranking in engine and persist directly
- `Medium Risk: repeated scans` -> direct keyed reads or cached narrow relation
- `Medium Risk: copy churn` -> single working frame and fewer conversion passes
- `Medium Risk: SELECT * but only few columns used` -> project required columns before materialization
- `Medium Risk: row-wise apply in reporting` -> replace with `map` or masked vectorized assignment
