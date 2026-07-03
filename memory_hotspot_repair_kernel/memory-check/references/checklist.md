# Memory Risk Checklist

Use this checklist while auditing code. Quote file paths and line numbers in findings.

## How To Use

1. Detect the stack from imports and key APIs first.
2. Read only the sections that match the detected stack in depth.
3. Always apply the `Universal` section.
4. If a library or API is version-sensitive, verify behavior from primary sources before finalizing conclusions.

## Universal

### Red Flags

- Full materialization:
  - `.df()`
  - `.fetchdf()`
  - `pd.read_parquet(...)`
  - `pd.read_csv(...)`
  - `.to_pandas()`
  - `.collect()`
  - `fetchall()` on non-trivial result sets
  - `SELECT * FROM read_parquet(...)` when only a few columns are consumed downstream
- Fake chunking:
  - read everything first, then `iloc`, `head`, `split`, or `groupby` later
  - `df = query.df()` followed by per-chunk slicing in Python
- Large copies:
  - `df.copy()`
  - helper functions that internally do `copy()`
  - `work = product_df.copy()` followed by more copies
  - repeated `astype()/fillna()/to_numeric()` over many columns
- Matrix duplication:
  - `X = df[feature_cols].to_numpy()`
  - score arrays or prediction arrays created from full frames
- Register-without-relief:
  - `con.register("name", df)` when `df` is already the peak object
- Large in-memory accumulation:
  - `all_rows.append(df)` then `pd.concat(all_rows)`
  - collecting many `part_paths` and then unioning them all
- Global SQL memory pressure:
  - `ROW_NUMBER() OVER (...)`
  - `ORDER BY` on full relations
  - `GROUP BY` on large wide inputs
  - `GROUP BY` plus `list(...)`
  - `GROUP BY` plus `to_json(...)`
  - dedup windows over large partitions
- Parallel amplification:
  - `ProcessPoolExecutor`
  - many workers each reading the same large source
  - many workers each loading the same large model or encoding mapping
- In-memory execution:
  - `connect_duckdb(":memory:")` for large jobs
  - no `temp_directory`
  - no memory limit
- File enumeration:
  - `list(path.glob(...))`
  - recursive path discovery creating large Python lists
- Hidden hot path:
  - checkpoint/resume skips the expensive path during testing
  - smoke data is too small to surface true peak memory

### Yellow Flags

- Recursive glob reads:
  - `/**/*.parquet`
  - `/**/*.csv`
- Repeated filtering over a broad base relation instead of direct keyed reads
- building one global view over all segment files when the task later loops by `segment_name`
- Returning full outputs to memory after already writing them to disk
- TopK/combo outputs materialized as pandas at the end of a large pipeline
- Final merge/union/report stage can become the new peak after earlier loops are optimized
- Large mapping dicts, encoders, or feature metadata held for the whole run
- row-wise `DataFrame.apply(...)` used to fill a column that could come from `map`, `merge`, or masked assignment

### Green Flags

- Chunked or streaming readers
- Direct per-product or per-part reads
- Column pruning before materialization
- Sample limits or fraction limits
- Recent-window pruning for eval or scoring inputs
- Temp spill directory configured for DuckDB
- Explicit release / cleanup after each chunk or product
- Config knobs that reduce input scope before expensive transforms

### Review Questions

1. Where is the first full materialization into Python?
2. How many copies of the largest object exist simultaneously?
3. Does parallelism multiply the same peak?
4. Is the most expensive sort or window global?
5. Is chunking applied before or after the dangerous step?
6. Can the code read a smaller keyed subset directly?
7. Can the output stay in DuckDB/parquet instead of becoming pandas?
8. Can the final merge/ranking/report stage exceed the peak of the main loop?
9. Are config defaults safe for production-scale data?

## pandas

### Red Flags

- `pd.read_parquet(...)` or `pd.read_csv(...)` on broad operational data
- `df.copy()` before feature engineering
- repeated per-column conversion loops over a wide feature set
- `df[feature_cols].to_numpy()` on wide/tall frames
- `pd.concat(frames)` after long accumulation
- eager `merge()` on wide frames before pruning columns

### Yellow Flags

- `astype(str)` across many large columns
- object dtype columns kept longer than necessary
- reading full data only to keep a small subset of columns

### Green Flags

- `usecols=...`
- dtype narrowing where safe
- per-chunk processing with immediate writeout
- minimal pandas lifetime before DuckDB or parquet persistence

## DuckDB

### Red Flags

- `.df()` / `.fetchdf()` on large relations
- `.fetchall()` on large result sets
- `:memory:` database for large sorts/joins
- no `temp_directory` for spill-heavy operations
- broad `read_parquet('**/*.parquet')` with later filtering
- window functions or `ORDER BY` over full scored outputs
- grouped list/json aggregation over large relations

### Yellow Flags

- `UNION ALL` over many files built from a large Python list
- `con.register(df)` after already materializing a large pandas frame
- version-specific streaming APIs used without fallback

### Green Flags

- Arrow reader / record batch streaming
- direct per-key file reads
- direct per-segment file reads for segment-partitioned assets
- writing final outputs directly from DuckDB
- cleanup of temp views and relations

## Parquet / Arrow

### Red Flags

- reading many parquet files fully into pandas
- materializing Arrow tables fully before batch iteration
- converting Arrow -> pandas -> NumPy in one hot path

### Yellow Flags

- unioning many part files in Python before pushing work down
- reading the same parquet outputs back for optional return values

### Green Flags

- reader/batch APIs
- column projection before conversion
- direct engine-to-parquet persistence
- narrow `SELECT col1, col2, ...` instead of `SELECT *`

## CSV

### Red Flags

- full CSV read with default object dtypes
- no column pruning or dtype hints on very wide CSV
- repeated CSV rescans instead of one keyed pass

### Yellow Flags

- schema inference repeated across many files
- mixed-type columns forcing object expansion

### Green Flags

- bounded read size
- selected columns only
- conversion to efficient typed storage early

## NumPy

### Red Flags

- full-frame `.to_numpy()` after multiple pandas copies
- large temporary score arrays kept alongside source frame
- float64 used when float32 is sufficient and acceptable

### Yellow Flags

- implicit copying during dtype conversion
- duplicated masks / boolean arrays on huge matrices

### Green Flags

- dtype narrowing where numerically safe
- short-lived arrays with immediate release

## Polars

### Red Flags

- eager `read_parquet()` / `collect()` on data that should stay lazy
- converting large Polars frames to pandas too early
- sorting full lazy pipelines without pushdown or pruning

### Yellow Flags

- lazy plan looks efficient but ends in one huge `collect()`
- repeated `with_columns()` chains that widen temporary state

### Green Flags

- lazy scans
- projection and predicate pushdown
- streaming or sink-based output where supported

## Model / Inference

### Red Flags

- one model object per worker with high worker count
- large encoding mappings loaded once per product or worker
- input frame, encoded frame, NumPy matrix, and prediction output all alive together

### Yellow Flags

- missing model cache lifecycle control
- per-product scoring loops that reload large artifacts repeatedly

### Green Flags

- per-product isolation with prompt writeout and release
- skipping missing models without crashing the full task

## GC / Cleanup

### Red Flags

- long loops with no release of large temporary objects
- retaining references in lists, closures, or result dicts
- relying on `gc.collect()` while references still exist

### Yellow Flags

- cleanup exists but happens only at the very end
- cleanup helper does not cover all large objects

### Green Flags

- explicit del / scope exit before `gc.collect()`
- cleanup after each chunk, product, or batch

## Vectorization

### Red Flags

- `DataFrame.apply(..., axis=1)` on large frames in final reporting or enrichment steps
- repeated whole-frame filtering inside a per-group loop

### Green Flags

- `Series.map(...)`
- masked assignment
- precomputed lookup dicts
- grouped views reused without copying

## Version Compatibility

### Red Flags

- streaming/memory fix depends on an API missing in target runtime
- optimization uses a library feature without fallback

### Yellow Flags

- comments assume a newer library version than deployment

### Green Flags

- fallback path for older versions
- version-sensitive behavior documented in config or logs

## Findings Language

- **High Risk**
  - "This line fully materializes all rows for one product into pandas; peak memory scales with the largest product."
  - "This path creates multiple same-size copies (`source`, `work`, encoded copy, NumPy array), so peak memory is several times the raw frame size."
  - "This global ranking step is likely to spill or OOM because it sorts the entire scored dataset at once."
  - "This is fake chunking: the data is fully loaded before being sliced into batches, so peak memory does not improve."
  - "Registering this frame in DuckDB does not reduce peak memory because pandas already owns the large object."
- **Medium Risk**
  - "This recursive glob is not an immediate OOM, but it increases scan cost and keeps large intermediate state alive longer than necessary."
  - "This result is written to disk and then optionally read back into pandas, which is avoidable memory churn."
  - "This wide per-column conversion loop is unlikely to be the first OOM point, but it creates heavy allocation churn and slows GC."
- **Low Risk**
  - "This metadata query uses `fetchall()`, but the result cardinality is naturally small."

## Common Remediations

- Replace full `.df()` with chunked readers or bounded queries.
- Read direct per-key files instead of scanning a whole directory repeatedly.
- Read the current segment/key partition directly when the downstream loop is already segmented.
- Remove unnecessary `.copy()` calls.
- Push chunking before pandas materialization, not after.
- Keep ranking and aggregation inside DuckDB as long as possible.
- Write outputs directly from DuckDB instead of materializing intermediate pandas frames.
- Add `temp_directory` and memory limit for large DuckDB jobs.
- Add version-compatible fallback paths for streaming APIs.
- Lower worker count when each worker holds a large model or frame.
- Project only the columns required by the next stage before materialization.
- Replace row-wise `apply` with vectorized `map`/masked assignment in final reporting stages.
