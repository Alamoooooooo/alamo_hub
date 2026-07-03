# Memory Hotspot Reference Citations

Use these entries when you want primary-source support for generic memory-hotspot guidance.

## Python tracing and hotspot inspection

- Python Software Foundation, `tracemalloc` documentation.
  - URL: https://docs.python.org/3/library/tracemalloc.html
  - Why it matters: snapshot-based allocation tracking, line-level statistics, and peak/current traced memory inspection.
  - Best use: support claims about runtime hotspot localization and before/after snapshot comparison.

## pandas large-data memory behavior

- pandas documentation, `Scaling to large datasets`.
  - URL: https://pandas.pydata.org/docs/user_guide/scale.html
  - Why it matters: pandas is an in-memory tool and intermediate operations can multiply memory pressure even when raw data barely fits in RAM.
  - Best use: support claims about full materialization, column pruning, chunking, and avoiding unnecessary copies.

## DuckDB memory and OOM behavior

- DuckDB documentation, `Out of Memory Errors`.
  - URL: https://duckdb.org/docs/stable/guides/troubleshooting/oom_errors.html
  - Why it matters: identifies blocking operators, thread count, and memory-limit tradeoffs that often dominate peak memory.
  - Best use: support claims about spill-sensitive operators, memory limit tuning, and diagnosing large-query peaks.

- DuckDB engineering article, `Memory Management in DuckDB` published July 9, 2024.
  - URL: https://duckdb.org/2024/07/09/memory-management.html
  - Why it matters: explains streaming execution, buffer manager spill, `temp_directory`, `max_temp_directory_size`, and default memory-limit behavior.
  - Best use: support claims about spill configuration, temporary storage, and why in-engine execution can still peak on blocking operators.

## Polars streaming and fallback

- Polars user guide, `Streaming`.
  - URL: https://docs.pola.rs/user-guide/concepts/streaming/
  - Why it matters: explains that lazy execution can stream in batches, but not every operator remains streamable.
  - Best use: support claims about lazy-vs-eager execution, engine fallback risk, and large-collection hotspots.

## Citation Guidance

- Cite the most specific source for the claim.
- Prefer one citation per major rule family instead of repeating the same URL on every finding.
- When a claim is version-sensitive, verify the current page before finalizing the report.
