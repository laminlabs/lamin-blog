# Five ways to query a LaminDB collection: a developer-experience comparison

Working with genomic copy-number variant (CNV) calls means querying tabular data split across many Parquet files. We took a LaminDB collection of 1000 Genomes CNV calls — 8,929 rows across six DRAGEN Parquet shards, roughly 1,500 rows per file — and ran the same user journey through five different query systems: Vanilla PyArrow, Polars, DuckDB, Apache Iceberg, and LanceDB. We compare the developer experience at every step — setup, querying, and writing — and find that the query layer is largely interchangeable, while LaminDB's contribution sits underneath all five: lineage, schema validation, and versioning, regardless of which engine you pick.

## The problem

The starting point is deliberately modest. Six Parquet files, 8,929 CNV calls, and a set of operations that any genomics data scientist would run routinely: compute per-sample statistics, find recurrent regions, filter to a position range, append a new sample, and add a QC column. On 8,929 rows, none of these is slow. The question throughout is not which engine is fastest — it is what it is actually like to do this work.

All five approaches read from the same LaminDB collection. Getting a handle to it is one line:

```python
import lamindb as ln
collection = ln.Collection.get("K6X8Ejk3fjgAZT6h0000")  # 1000 Genomes CNV calls
```

From here the five paths diverge.

---

## Setup

How each engine gets from the collection handle to something queryable is where the developer experience first differs.

::::::{tab-set}
:::::{tab-item} Vanilla PyArrow
One line. The collection opens as a lazy PyArrow dataset backed by S3 — nothing is downloaded until a query fires.

```python
dataset = collection.open()   # lazy PyArrow dataset over the 6 shards
```

No catalog, no ingestion, no extra configuration. The dataset is ready to query immediately.
:::::

:::::{tab-item} Polars
One line, same as PyArrow. The `engine="polars"` flag returns a lazy Polars LazyFrame instead of a PyArrow dataset. The context manager holds the S3 connection open.

```python
with collection.open(engine="polars") as lazy_df:
    ...   # lazy_df is a Polars LazyFrame backed by S3
```

Nothing is read until `.collect()` is called.
:::::

:::::{tab-item} DuckDB
Three setup steps: connect, load the S3 extension, create a view over the collection's S3 paths.

```python
import duckdb
con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs;")
con.execute("CREATE OR REPLACE SECRET s3 (TYPE s3, PROVIDER credential_chain);")

s3_paths = [str(a.path) for a in collection.ordered_artifacts.all()]
con.execute(f"CREATE OR REPLACE VIEW cnv_vcf AS SELECT * FROM read_parquet({s3_paths})")
```

The view is lazy — DuckDB reads nothing until a SQL query fires. From here, everything is SQL against `cnv_vcf`.
:::::

:::::{tab-item} Iceberg
The heaviest setup of the five. After reading the data from LaminDB, it must be ingested into a catalog-managed Iceberg table on S3.

```python
from pyiceberg.catalog.sql import SqlCatalog

# read from LaminDB first — required before ingestion
arrow = collection.open().to_table()   # 7.3s — full S3 read

# set up the catalog and ingest
catalog = SqlCatalog("local", uri="sqlite:///iceberg_catalog.db", warehouse=WAREHOUSE)
catalog.create_namespace("genomics")
table = catalog.create_table("genomics.cnv_vcf", schema=arrow.schema)
table.overwrite(arrow)   # 1.36s — writes data + metadata to S3
```

Total setup: ~8.7s and roughly 20 lines including imports. The payoff is the strongest write semantics of the five.
:::::

:::::{tab-item} LanceDB
Two steps: read from LaminDB, ingest into Lance format on S3. LanceDB is the only engine that physically copies the data out of Parquet.

```python
import lancedb

arrow = collection.open().to_table()   # 7.4s — full S3 read
db = lancedb.connect(WAREHOUSE)
table = db.create_table("cnv_vcf", data=arrow, mode="overwrite")   # 0.15s
```

The ingest is fast but it's real — data now lives in Lance columnar format outside LaminDB's lineage graph. Total setup: ~7.6s.
:::::
::::::

The setup story in one line: PyArrow and Polars need one line; DuckDB needs five; Iceberg needs ~20 and 8.7 seconds; LanceDB needs three lines and 7.6 seconds (mostly the S3 read).

---

## Queries

We ran three queries against all five engines. The logic is identical across all five — what changes is the syntax and the speed.

### Query 1 — per-sample CNV statistics

For each sample, compute: total CNV count, number of deletions, median deletion size, and homo/heterozygous counts.

::::::{tab-set}
:::::{tab-item} Vanilla PyArrow
```python
df = dataset.to_table().to_pandas()   # materialise — 1.37s S3 read

stats = df.groupby("SAMPLE_NAME").agg(
    Total_CNVs=("INFO_SVLEN", "count"),
    Deletions=("INFO_SVLEN", lambda x: (x < 0).sum()),
    Median_Deletion_Size=("INFO_SVLEN", lambda x: abs(x[x < 0]).median()),
    Homozygous_CNVs=("SAMPLE_GT", lambda x: (x == "1/1").sum()),
    Heterozygous_CNVs=("SAMPLE_GT", lambda x: (x == "0/1").sum()),
).reset_index()
```
**Time (store mode):** 1.37s
:::::

:::::{tab-item} Polars
```python
df = lazy_df.collect().to_pandas()   # materialise — 0.35s S3 read (parallel)

stats = df.groupby("SAMPLE_NAME").agg(
    Total_CNVs=("INFO_SVLEN", "count"),
    Deletions=("INFO_SVLEN", lambda x: (x < 0).sum()),
    Median_Deletion_Size=("INFO_SVLEN", lambda x: abs(x[x < 0]).median()),
    Homozygous_CNVs=("SAMPLE_GT", lambda x: (x == "1/1").sum()),
    Heterozygous_CNVs=("SAMPLE_GT", lambda x: (x == "0/1").sum()),
).reset_index()
```
**Time (store mode):** 0.35s — ~4× faster than PyArrow due to parallel S3 reads.
:::::

:::::{tab-item} DuckDB
```python
stats = con.execute("""
    SELECT
        SAMPLE_NAME,
        COUNT(*)                                               AS Total_CNVs,
        COUNT(*) FILTER (WHERE INFO_SVLEN < 0)                 AS Deletions,
        MEDIAN(ABS(INFO_SVLEN)) FILTER (WHERE INFO_SVLEN < 0)  AS Median_Deletion_Size,
        COUNT(*) FILTER (WHERE SAMPLE_GT = '1/1')              AS Homozygous_CNVs,
        COUNT(*) FILTER (WHERE SAMPLE_GT = '0/1')              AS Heterozygous_CNVs
    FROM cnv_vcf
    GROUP BY SAMPLE_NAME
""").df()
```
**Time (store mode):** 0.77s — most concise expression; single SQL statement.
:::::

:::::{tab-item} Iceberg
```python
df = table.scan().to_arrow().to_pandas()   # reads from Iceberg store — 0.19s

stats = df.groupby("SAMPLE_NAME").agg(
    Total_CNVs=("INFO_SVLEN", "count"),
    Deletions=("INFO_SVLEN", lambda x: (x < 0).sum()),
    Median_Deletion_Size=("INFO_SVLEN", lambda x: abs(x[x < 0]).median()),
    Homozygous_CNVs=("SAMPLE_GT", lambda x: (x == "1/1").sum()),
    Heterozygous_CNVs=("SAMPLE_GT", lambda x: (x == "0/1").sum()),
).reset_index()
```
**Time (store mode):** 0.19s — fast because data is already in Iceberg's own S3 store.
:::::

:::::{tab-item} LanceDB
```python
df = table.to_arrow().to_pandas()   # reads from Lance store — 0.17s

stats = df.groupby("SAMPLE_NAME").agg(
    Total_CNVs=("INFO_SVLEN", "count"),
    Deletions=("INFO_SVLEN", lambda x: (x < 0).sum()),
    Median_Deletion_Size=("INFO_SVLEN", lambda x: abs(x[x < 0]).median()),
    Homozygous_CNVs=("SAMPLE_GT", lambda x: (x == "1/1").sum()),
    Heterozygous_CNVs=("SAMPLE_GT", lambda x: (x == "0/1").sum()),
).reset_index()
```
**Time (store mode):** 0.17s — fast for the same reason as Iceberg.
:::::
::::::

### Query 2 — recurrent region detection

Bin genomic positions into 1 kbp windows. Find bins where CNVs appear in two or more distinct samples — these are the recurrent regions. All five engines found 1,903.

::::::{tab-set}
:::::{tab-item} Vanilla PyArrow
```python
df["region_key"] = df["CHROM"] + ":" + ((df["POS"] // 1000) * 1000).astype(str)
recurrent = df.groupby("region_key")["SAMPLE_NAME"].nunique()
recurrent = recurrent[recurrent >= 2]   # 1,903 recurrent regions
```
**Time (store mode):** 1.11s
:::::

:::::{tab-item} Polars
```python
df["region_key"] = df["CHROM"] + ":" + ((df["POS"] // 1000) * 1000).astype(str)
recurrent = df.groupby("region_key")["SAMPLE_NAME"].nunique()
recurrent = recurrent[recurrent >= 2]   # 1,903 recurrent regions
```
**Time (store mode):** 0.28s
:::::

:::::{tab-item} DuckDB
```python
recurrent = con.execute("""
    SELECT
        CHROM || ':' || CAST((POS // 1000) * 1000 AS VARCHAR) AS region_key,
        COUNT(DISTINCT SAMPLE_NAME) AS sample_count
    FROM cnv_vcf
    GROUP BY region_key
    HAVING COUNT(DISTINCT SAMPLE_NAME) >= 2
    ORDER BY sample_count DESC
""").df()   # 1,903 recurrent regions
```
**Time (store mode):** 0.80s
:::::

:::::{tab-item} Iceberg
```python
df["region_key"] = df["CHROM"] + ":" + ((df["POS"] // 1000) * 1000).astype(str)
recurrent = df.groupby("region_key")["SAMPLE_NAME"].nunique()
recurrent = recurrent[recurrent >= 2]   # 1,903 recurrent regions
```
**Time (store mode):** 0.17s
:::::

:::::{tab-item} LanceDB
```python
df["region_key"] = df["CHROM"] + ":" + ((df["POS"] // 1000) * 1000).astype(str)
recurrent = df.groupby("region_key")["SAMPLE_NAME"].nunique()
recurrent = recurrent[recurrent >= 2]   # 1,903 recurrent regions
```
**Time (store mode):** 0.06s
:::::
::::::

### Query 3 — filtered query

Point query: all variants on the most common chromosome within the 10th–90th percentile position band. All five engines returned 589 variants. Each engine pushes the predicate down into the storage layer — only matching row groups or files are read.

::::::{tab-set}
:::::{tab-item} Vanilla PyArrow
```python
import pyarrow.compute as pc
expr = ((pc.field("CHROM") == chrom)
        & (pc.field("POS") >= lo) & (pc.field("POS") <= hi))
filtered = dataset.to_table(filter=expr)   # pushdown into Parquet row groups
```
**Time:** 1.05s &nbsp;·&nbsp; **Result:** 589 variants
:::::

:::::{tab-item} Polars
```python
filtered = lazy_df.filter(
    (pl.col("CHROM") == chrom) & (pl.col("POS") >= lo) & (pl.col("POS") <= hi)
).collect()   # lazy filter — pushdown into Parquet scan
```
**Time:** 0.27s &nbsp;·&nbsp; **Result:** 589 variants
:::::

:::::{tab-item} DuckDB
```python
filtered = con.execute(
    "SELECT * FROM cnv_vcf WHERE CHROM = ? AND POS BETWEEN ? AND ?",
    [chrom, lo, hi],
).df()
```
**Time:** 0.79s &nbsp;·&nbsp; **Result:** 589 variants
:::::

:::::{tab-item} Iceberg
```python
from pyiceberg.expressions import And, EqualTo, GreaterThanOrEqual, LessThanOrEqual
row_filter = And(EqualTo("CHROM", chrom),
             And(GreaterThanOrEqual("POS", lo), LessThanOrEqual("POS", hi)))
filtered = table.scan(row_filter=row_filter).to_arrow()
```
**Time:** 0.15s &nbsp;·&nbsp; **Result:** 589 variants
:::::

:::::{tab-item} LanceDB
```python
filtered = table.to_lance().to_table(
    filter=f"CHROM = '{chrom}' AND POS BETWEEN {lo} AND {hi}"
).to_pandas()
```
**Time:** 0.33s &nbsp;·&nbsp; **Result:** 589 variants
:::::
::::::

<!-- PLOT: query_times.svg -->
![Query times across all five engines and three query types](images/query_times.svg)

**On the Polars vs PyArrow gap:** Polars is consistently ~4× faster than Vanilla PyArrow in store mode across all three queries. This is not a compute difference — both engines run the same pandas groupby on the same data. The difference is in the S3 reader: Polars fetches all six shards in parallel, while PyArrow's dataset reads them more sequentially. In memory mode (materialise once, query the cached frame), the gap collapses to near-zero.

**On Iceberg and LanceDB being fast after ingest:** they read their own copy of the data on S3, already reformatted and indexed. They paid the read cost upfront at ingest time, not per query.

---

## Writes

Three write operations: append a new sample, add a schema column, and (where available) travel back in time to a previous state.

### Append

Add a new sample — 1,536 rows, one sample's worth of CNV calls — bringing the total from 8,929 to 10,465 rows.

::::::{tab-set}
:::::{tab-item} Vanilla PyArrow
In LaminDB, appending means saving a validated artifact and creating a new collection version. The append is tracked, versioned, and queryable by biology — but it's the heaviest write of the five.

```python
new_art = ln.Artifact.from_dataframe(
    new_sample_df,
    key=f"lakehouse-benchmarks/append_batch_{ln.context.run.uid}.parquet",
    description="benchmark append batch (new sample)",
).save()   # S3 upload + schema validation

new_collection = ln.Collection(
    [*original_arts, new_art],
    key=collection.key, revises=collection,
).save()   # new collection version registered in LaminDB
```
**Time:** 9.4s &nbsp;·&nbsp; **Persisted:** Yes &nbsp;·&nbsp; **Tracked in lineage:** Yes
:::::

:::::{tab-item} Polars
Identical to Vanilla PyArrow — the append goes through LaminDB's artifact and collection APIs regardless of which query engine opened the data.

```python
new_art = ln.Artifact.from_dataframe(
    new_sample_df,
    key=f"lakehouse-benchmarks/append_batch_{ln.context.run.uid}.parquet",
    description="benchmark append batch (new sample)",
).save()

new_collection = ln.Collection(
    [*original_arts, new_art],
    key=collection.key, revises=collection,
).save()
```
**Time:** 9.5s &nbsp;·&nbsp; **Persisted:** Yes &nbsp;·&nbsp; **Tracked in lineage:** Yes
:::::

:::::{tab-item} DuckDB
Redefine the view to union in the new rows. Instant — but exists only in the current session.

```python
con.register("append_batch", new_sample_arrow)
con.execute(
    f"CREATE OR REPLACE VIEW cnv_vcf AS "
    f"{base_select} UNION ALL SELECT * FROM append_batch"
)
rows_after = con.execute("SELECT COUNT(*) FROM cnv_vcf").fetchone()[0]   # 10,465
```
**Time:** 0.24s &nbsp;·&nbsp; **Persisted:** No (session only) &nbsp;·&nbsp; **Tracked in lineage:** No
:::::

:::::{tab-item} Iceberg
Atomic, snapshot-isolated append — concurrent readers always see a consistent state. Writes new Parquet files and a new snapshot manifest to S3.

```python
table.append(new_sample_arrow)   # atomic write
rows_after = table.scan().to_arrow().num_rows   # 10,465
```
**Time:** 0.88s &nbsp;·&nbsp; **Persisted:** Yes &nbsp;·&nbsp; **Tracked in lineage:** No (outside LaminDB)
:::::

:::::{tab-item} LanceDB
Every `add()` automatically creates a new version. Fast, versioned, and persisted to S3.

```python
table.add(new_sample_arrow)
print(f"Version {table.version} | rows: {table.count_rows():,}")   # Version 2 | 10,465
```
**Time:** 0.11s &nbsp;·&nbsp; **Persisted:** Yes &nbsp;·&nbsp; **Tracked in lineage:** No (outside LaminDB)
:::::
::::::

### Schema change

Add a `QC_PASS` boolean column.

::::::{tab-set}
:::::{tab-item} Vanilla PyArrow
Updates the registered LaminDB schema — all future artifacts saved against it are validated against the new definition. This is a registry update, not a file operation.

```python
schema = ln.Schema.get(name="1000 Genomes CNV VCF")
feat = ln.Feature(name="QC_PASS", dtype=bool).save()
schema.add_optional_features([feat])
```
**Time:** 3.5s &nbsp;·&nbsp; **Scope:** entire LaminDB instance (all future artifacts)
:::::

:::::{tab-item} Polars
Identical to Vanilla PyArrow.

```python
schema = ln.Schema.get(name="1000 Genomes CNV VCF")
feat = ln.Feature(name="QC_PASS", dtype=bool).save()
schema.add_optional_features([feat])
```
**Time:** 3.6s &nbsp;·&nbsp; **Scope:** entire LaminDB instance (all future artifacts)
:::::

:::::{tab-item} DuckDB
View redefinition — adds a virtual `NULL` column. Instant, but session-scoped only.

```python
con.execute(
    f"CREATE OR REPLACE VIEW cnv_vcf AS "
    f"SELECT *, CAST(NULL AS BOOLEAN) AS QC_PASS FROM ({base_select}) t"
)
```
**Time:** 0.25s &nbsp;·&nbsp; **Scope:** this session only
:::::

:::::{tab-item} Iceberg
Writes a new metadata file. No existing Parquet files are touched — old files return `null` for the new column.

```python
from pyiceberg.types import BooleanType
with table.update_schema() as update:
    update.add_column("QC_PASS", BooleanType())
```
**Time:** 0.31s &nbsp;·&nbsp; **Scope:** this Iceberg table on S3
:::::

:::::{tab-item} LanceDB
Adds a column via a SQL expression. Every existing row gets `NULL` for the new column.

```python
table.add_columns({"QC_PASS": "CAST(NULL AS BOOLEAN)"})
```
**Time:** 0.06s &nbsp;·&nbsp; **Scope:** this Lance table on S3
:::::
::::::

### Time travel

Query the state of the data before the append — 8,929 rows, not 10,465.

::::::{tab-set}
:::::{tab-item} Vanilla PyArrow
Time travel is collection versioning. The original collection version is still addressable by UID.

```python
original = ln.Collection.get("K6X8Ejk3fjgAZT6h0000")   # the pre-append version
dataset_v1 = original.open()
rows_v1 = dataset_v1.count_rows()   # 8,929
```
:::::

:::::{tab-item} Polars
Same as Vanilla PyArrow — collection versioning via LaminDB.

```python
original = ln.Collection.get("K6X8Ejk3fjgAZT6h0000")
with original.open(engine="polars") as lazy_v1:
    rows_v1 = lazy_v1.select(pl.len()).collect().item()   # 8,929
```
:::::

:::::{tab-item} DuckDB
DuckDB has no time travel. The view only reflects the current state. Once the session ends, even the append is gone.

```python
# not available in DuckDB
```
:::::

:::::{tab-item} Iceberg
Query any historical snapshot by ID. Iceberg preserves every snapshot until explicitly expired.

```python
first_snapshot = table.history()[0].snapshot_id
historical = table.scan(snapshot_id=first_snapshot).to_arrow()
print(historical.num_rows)   # 8,929 — pre-append state
```
**Time:** 0.14s
:::::

:::::{tab-item} LanceDB
Check out a specific version by number. `checkout_latest()` restores the current version.

```python
table.checkout(1)   # version 1 = initial create
print(table.count_rows())   # 8,929
table.checkout_latest()     # restore
```
**Time:** 0.10s
:::::
::::::

<!-- PLOT: write_path.svg -->
![Write-path times: append, schema change, and time travel per engine](images/write_path.svg)

---

## Developer experience compared

| | Vanilla PyArrow | Polars | DuckDB | Iceberg | LanceDB |
|---|---|---|---|---|---|
| **Setup** | 1 line | 1 line | 5 lines | ~20 lines + 8.7s | 3 lines + 7.6s |
| **Data ingestion required** | No | No | No | No (wraps) | Yes (copies) |
| **Query style** | PyArrow / pandas | Polars / pandas | SQL | Iceberg expressions | PyArrow / pandas / SQL |
| **Store-mode query speed** | ~1.1–1.4s | ~0.27–0.35s | ~0.77–0.87s | ~0.15–0.19s | ~0.06–0.33s |
| **Append** | tracked + versioned | tracked + versioned | ephemeral view | atomic snapshot | versioned `add()` |
| **Schema change** | registry (instance-wide) | registry (instance-wide) | ephemeral view | metadata file (table) | column expression (table) |
| **Time travel** | collection versions | collection versions | none | snapshot id | version number |
| **ACID** | validation + versioning | validation + versioning | none | full snapshot isolation | versioned appends |
| **Vector search** | no | no | no | no | yes |
| **Stays in LaminDB lineage** | yes | yes | yes | yes | no |

<!-- PLOT: setup_cost.svg -->
![Setup cost per engine](images/setup_cost.svg)

A few observations that cut across the table:

**DuckDB's write numbers are misleading.** The 0.24s append and 0.25s schema change look fast, but they're not comparable to the others — they're view redefinitions that exist only in the session. Close the connection and both are gone. Every other engine writes something durable.

**LaminDB's write times are high because the operation is larger in scope.** The 9.4s append includes an S3 upload, schema validation, and a new collection version registered in a Postgres-backed metadata database. The 3.5s schema change updates a registry that governs every future artifact in the instance. Iceberg's 0.88s append and 0.31s schema change write to one table. These are different operations with different scopes — not a fast vs. slow version of the same thing.

**Polars' 4× query advantage over Vanilla PyArrow is an I/O effect, not a compute difference.** Both run the same pandas groupby. The difference is Polars' parallel S3 reader vs. PyArrow's more sequential one. In memory mode the gap disappears.

**Iceberg and LanceDB look fast on queries because they already paid the read cost.** They ingested the data into their own S3 store at setup. The per-query times reflect reading from a warm, already-formatted local copy — not from the source Parquet across S3.

---

## The reframe: a query engine is not a data layer

If querying a LaminDB collection is this direct across five different engines, what is LaminDB actually doing?

Not the querying. The reads and compute happen entirely in each engine's own runtime. You could swap any of the five approaches on top of the same collection without LaminDB minding. There is no proprietary query layer and no query tax.

What LaminDB provides sits underneath that choice:

**Lineage.** Every artifact records where it came from and what produced it. The benchmark itself demonstrates this — each engine's results are written back as a tracked artifact, and a final `plots.py` reads those five artifacts to produce the comparison charts. The full graph, from the original data transfer through to the figures in this post, is browsable in LaminHub:

<!-- SCREENSHOT: LaminHub lineage graph -->
![The lineage graph: source collection → five pipeline notebooks → five result parquets → plots.py → three figures](images/lineage-graph.png)

**Schema validation.** A registered schema validates new data at write time. In our governance demo, a DataFrame with only a `wrong_column` raises a `ValidationError` on save — caught at the boundary, not discovered three queries later.

**Versioning.** Appending a sample creates a new collection version. The state before and after the append are both addressable, with the relationship recorded.

**Metadata-queryable collections.** Artifacts carry biological metadata. You can filter by tissue, organism, disease, or any registered feature before opening any data — selecting the right subset first, then handing it to whichever engine does the compute.

None of this depends on the query engine.

---

## Conclusion

For genomics R&D, the query engine is a choice you make per task. Want the fastest store-mode reads without any setup? Polars. Want SQL and cross-file joins? DuckDB. Need concurrent atomic writes and time travel? Iceberg. Building pipelines with vector embeddings? LanceDB. Just need to open a table and compute? PyArrow is right there. None of these choices is permanent.

What stays constant underneath is the data layer. LaminDB doesn't ask you to adopt its query engine — it doesn't have one — it asks to hold your data with lineage, validation, and versioning, and then gets out of the way. Pick the engine that fits the work; keep the governance constant.

---

## Author contributions

Raaghav Pillai performed the benchmarking work and wrote the pipelines. The original LaminDB ingestion pipeline this work builds on was developed by Sunny Sun. Alex Wolf and Sergei R supervised the project.

## Code & data availability

The five pipeline notebooks, the shared benchmarking utilities, and the plotting script are tracked in the `laminlabs/lakehouse-benchmarks` instance.

- [Vanilla PyArrow pipeline](https://lamin.ai/laminlabs/lakehouse-benchmarks/transform/D10UPamv70IP)
- [Polars pipeline](https://lamin.ai/laminlabs/lakehouse-benchmarks/transform/2Wdo02w0MDgH)
- [DuckDB pipeline](https://lamin.ai/laminlabs/lakehouse-benchmarks/transform/tQaG9uhSD7BO)
- [Iceberg pipeline](https://lamin.ai/laminlabs/lakehouse-benchmarks/transform/wnVO8cu0qtOP)
- [LanceDB pipeline](https://lamin.ai/laminlabs/lakehouse-benchmarks/transform/WtZF9OX9v3uM)

The dataset is the 1000 Genomes Project CNV calls (DRAGEN, hg38), collection UID `K6X8Ejk3fjgAZT6h0000`.

## How to cite

```
Pillai R, Sun S & Wolf A (2026). Five ways to query a LaminDB collection:
a developer-experience comparison of PyArrow, Polars, DuckDB, Iceberg, and LanceDB.
Lamin Blog.
```