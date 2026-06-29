---
title: "Lakehouse Engineering: Benchmarking Metadata-Driven Query Optimization"
date: 2026-06-25
author: Koncopd, falexwolf, AlexR, raaghavpillai
affiliation:
  Koncopd: Lamin Labs, Munich
  falexwolf: Lamin Labs, Munich
  AlexR: Lamin Labs
  raaghavpillai: Lamin Labs
db: https://lamin.ai/laminlabs/lakehouse-benchmarks
---

Every genomics data scientist eventually hits the same wall. The biology is worked out. The pipeline is written. And then — before a single query can run — comes the decision of how to actually get at the data: which engine to use, whether to ingest or read in place, how to handle six Parquet files that need to behave like one table.

This post has two parts. The first explains where tools like Iceberg, DuckLake, and LaminDB sit in the data lakehouse ecosystem and what problems each solves. The second benchmarks five query approaches over a shared LaminDB collection of 1000 Genomes CNV calls, measuring the same six-step user journey in each.

---

## The lakehouse landscape

The lakehouse architecture promises to combine the flexibility of a data lake with the structure of a data warehouse, allowing teams with multi-modal datasets and different query engines to store their data in a single storage system and manipulate it transactionally. In recent years, lakehouse table formats like Apache Iceberg have emerged to provide transactional semantics on top of tabular data stored in object storage systems like S3.

### How Iceberg works

Under the hood, Iceberg organizes data into *snapshots* — each a collection of data files plus manifest files that track which files belong to which snapshot. A single root metadata file describes the table's schema and points to the current snapshot. When a query engine writes to an Iceberg table, it creates a new snapshot and atomically updates the root metadata file to point to it.

This snapshot-based approach offers several advantages over raw files in S3. Iceberg writes are serializable ACID transactions, enabling time travel (reading previous snapshots), schema evolution without data rewrites, and Write-Audit-Publish workflows where new snapshots can be staged for quality checks before becoming visible to consumers. Any query engine implementing the Iceberg spec supports these operations, providing flexibility in tooling.

But Iceberg's snapshot model has real costs. Creating a snapshot is expensive, so Iceberg assumes large, infrequent writes — small random writes are impractical. Optimistic concurrency control means concurrent writers will collide and all but one will fail. On S3 (which lacked atomic compare-and-swap until recently), an external catalog or lock is needed to coordinate metadata updates. Garbage collection of orphaned data files requires explicit action and doesn't happen automatically. Multi-table transactions are only available with certain catalogs.

### DuckLake and the relational metadata approach

One recent effort to address Iceberg's limitations is [DuckLake](https://ducklake.select), developed by the DuckDB team. Rather than storing metadata in object storage files, DuckLake keeps all metadata in a relational database (typically DuckDB itself), leaving only the actual data files in S3. This gives it serializable transactions with true concurrent writer support, automatic maintenance via the database's native mechanisms, and native multi-table transactions — all things that are difficult or impossible with Iceberg's file-based metadata.

### Where LaminDB fits

LaminDB shares DuckLake's key architectural insight: use a relational database (Postgres) for metadata, object storage for data. But it goes further in scope. Where Iceberg and DuckLake are concerned exclusively with tabular data and manage their own data files, LaminDB tracks metadata for heterogeneous files across multiple storage engines simultaneously — Parquet, AnnData, HDF5, zarr, VCF, or any other format — in a single lineage graph.

LaminDB is largely complementary to Iceberg rather than a replacement. It can treat an Iceberg table as a dataset like any other, track which pipeline run produced it, and link it to the AnnData files and VCFs that informed it.

### Capability comparison

| Feature | Raw Files | Iceberg | DuckLake | LaminDB |
|---|---|---|---|---|
| ACID transactions | ❌ | ✅ | ✅ | ✅ |
| Time travel / snapshot isolation | ❌ | ✅ | ✅ | ❌ |
| Schema evolution without rewriting data | ❌ | ✅ | ✅ | ❌ |
| Write-Audit-Publish workflow | ❌ | ✅ | ❌ | ❌ |
| Query engine independence | ✅ | ✅ | ❌ | ❌ |
| Concurrent writers | ❌ | ❌ | ✅ | ✅ |
| Automatic maintenance | ❌ | ❌ | ✅ | ✅ |
| Native multi-table transactions | ❌ | ❌ | ✅ | ✅ |
| Heterogeneous file support | ✅ | ❌ | ❌ | ✅ |
| Data lineage & provenance | ❌ | ❌ | ❌ | ✅ |
| Biological metadata & ontologies | ❌ | ❌ | ❌ | ✅ |

---

## Benchmark: five ways to query a LaminDB collection

The second half of this post measures five query approaches — PyArrow, Polars, DuckDB, Apache Iceberg, and LanceDB — over a shared LaminDB collection of 1000 Genomes CNV calls (8,929 rows across six DRAGEN Parquet shards). Each approach runs the same six-step user journey: access, per-sample statistics, recurrent region detection, filtered query, sample append, and schema change.

All timings are single-run measurements on SageMaker (ml.t3.medium) in store mode unless otherwise stated; they are provided as indicative comparisons on a small dataset, not rigorous benchmarks.

### Background

A copy-number variant analysis typically involves per-sample statistics, recurrent region identification across samples, filtered positional queries, incremental sample appends, and schema evolution. These operations are routine in genomics but span the full read-write surface of a query engine. Choosing an engine commits a team to a specific answer for all of them simultaneously: an engine that makes querying concise may make schema changes ephemeral; an engine that provides durable writes may require an upfront ingestion step; an engine that copies data into its own format removes it from the source lineage graph.

This benchmark measures all six operations end-to-end across five engines to make those tradeoffs explicit.

### One shared dataset

All five approaches read from the same LaminDB collection:

```python
import lamindb as ln
collection = ln.Collection.get("K6X8Ejk3fjgAZT6h0000")  # 1000 Genomes CNV calls
```

Three engines — PyArrow, Polars, and DuckDB — read the source Parquet files in place. Two — Iceberg and LanceDB — ingest the data into their own format before querying.

---

## Setup

::::::{tab-set}
:::::{tab-item} PyArrow
`collection.open()` returns a lazy PyArrow dataset backed by S3. No data is read until a query is issued.

```python
dataset = collection.open()   # lazy PyArrow dataset over the 6 shards
```
:::::

:::::{tab-item} Polars
`collection.open(engine="polars")` returns a context manager yielding a Polars LazyFrame backed by S3. No data is read until `.collect()` is called.

```python
with collection.open(engine="polars") as lazy_df:
    ...   # lazy_df is a Polars LazyFrame backed by S3
```
:::::

:::::{tab-item} DuckDB
DuckDB registers a view over the collection's S3 paths via `httpfs`. The view is lazy — nothing is read until a SQL query is issued.

```python
import duckdb
con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs;")
con.execute("CREATE OR REPLACE SECRET s3 (TYPE s3, PROVIDER credential_chain);")

s3_paths = [str(a.path) for a in collection.ordered_artifacts.all()]
con.execute(f"CREATE OR REPLACE VIEW cnv_vcf AS SELECT * FROM read_parquet({s3_paths})")
```
:::::

:::::{tab-item} Iceberg
Iceberg requires a full materialisation of the LaminDB collection before ingestion into a catalog-managed table on S3.

```python
from pyiceberg.catalog.sql import SqlCatalog

arrow = collection.open().to_table()   # 7.3s — full S3 read

catalog = SqlCatalog("local", uri="sqlite:///iceberg_catalog.db", warehouse=WAREHOUSE)
catalog.create_namespace("genomics")
table = catalog.create_table("genomics.cnv_vcf", schema=arrow.schema)
table.overwrite(arrow)   # 1.36s — writes Parquet + metadata to S3
```

Note: a SQLite catalog is used here for portability. Production deployments would use a Glue or REST catalog.
![Iceberg Warehouse S3 file layout](https://lamin-site-assets.s3.amazonaws.com/.lamindb/OgVhDACCMhzGKC4t0000.svg)

:::::

:::::{tab-item} LanceDB
LanceDB requires a full materialisation of the LaminDB collection and ingestion into Lance columnar format on S3. LanceDB is the only engine in this comparison that copies data out of the source Parquet files.

```python
import lancedb

arrow = collection.open().to_table()   # 7.4s — full S3 read
db = lancedb.connect(WAREHOUSE)
table = db.create_table("cnv_vcf", data=arrow, mode="overwrite")   # 0.15s
```
:::::
::::::

**Setup summary:**

| Engine | Lines | Time | Ingest required |
|---|---|---|---|
| PyArrow | 1 | ~0s | No |
| Polars | 1 | ~0s | No |
| DuckDB | 5 | ~1s | No |
| Iceberg | ~20 | ~8.7s | No (wraps source Parquet) |
| LanceDB | 3 | ~7.6s | Yes (copies to Lance format) |

<!-- PLOT: setup_cost.svg -->
![Setup cost](https://lamin-site-assets.s3.amazonaws.com/.lamindb/Lf8f0LJY63quZ3n70000.svg)

---

## Queries

Three queries were run against all five engines. The computation logic is equivalent across engines; differences in timing reflect S3 read strategy and whether data has been pre-ingested.

### Caveats on timing

All timings are single-run measurements on 8,929 rows. At this scale, results are dominated by fixed overheads (connection setup, S3 round-trips) rather than computational throughput. Iceberg and LanceDB query times reflect reads from their own pre-ingested S3 store, not from the source Parquet — their setup time should be amortised across queries when comparing total cost.

### Query 1 — per-sample CNV statistics

For each sample: total CNV count, deletion count, median deletion size, homozygous count, heterozygous count.

::::::{tab-set}
:::::{tab-item} PyArrow
```python
df = dataset.to_table().to_pandas()

stats = df.groupby("SAMPLE_NAME").agg(
    Total_CNVs=("INFO_SVLEN", "count"),
    Deletions=("INFO_SVLEN", lambda x: (x < 0).sum()),
    Median_Deletion_Size=("INFO_SVLEN", lambda x: abs(x[x < 0]).median()),
    Homozygous_CNVs=("SAMPLE_GT", lambda x: (x == "1/1").sum()),
    Heterozygous_CNVs=("SAMPLE_GT", lambda x: (x == "0/1").sum()),
).reset_index()
```
:::::

:::::{tab-item} Polars
```python
df = lazy_df.collect().to_pandas()

stats = df.groupby("SAMPLE_NAME").agg(
    Total_CNVs=("INFO_SVLEN", "count"),
    Deletions=("INFO_SVLEN", lambda x: (x < 0).sum()),
    Median_Deletion_Size=("INFO_SVLEN", lambda x: abs(x[x < 0]).median()),
    Homozygous_CNVs=("SAMPLE_GT", lambda x: (x == "1/1").sum()),
    Heterozygous_CNVs=("SAMPLE_GT", lambda x: (x == "0/1").sum()),
).reset_index()
```
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
:::::

:::::{tab-item} Iceberg
```python
df = table.scan().to_arrow().to_pandas()

stats = df.groupby("SAMPLE_NAME").agg(
    Total_CNVs=("INFO_SVLEN", "count"),
    Deletions=("INFO_SVLEN", lambda x: (x < 0).sum()),
    Median_Deletion_Size=("INFO_SVLEN", lambda x: abs(x[x < 0]).median()),
    Homozygous_CNVs=("SAMPLE_GT", lambda x: (x == "1/1").sum()),
    Heterozygous_CNVs=("SAMPLE_GT", lambda x: (x == "0/1").sum()),
).reset_index()
```
:::::

:::::{tab-item} LanceDB
```python
df = table.to_arrow().to_pandas()

stats = df.groupby("SAMPLE_NAME").agg(
    Total_CNVs=("INFO_SVLEN", "count"),
    Deletions=("INFO_SVLEN", lambda x: (x < 0).sum()),
    Median_Deletion_Size=("INFO_SVLEN", lambda x: abs(x[x < 0]).median()),
    Homozygous_CNVs=("SAMPLE_GT", lambda x: (x == "1/1").sum()),
    Heterozygous_CNVs=("SAMPLE_GT", lambda x: (x == "0/1").sum()),
).reset_index()
```
:::::
::::::

### Query 2 — recurrent region detection

Genomic positions are binned into 1 kbp windows. Bins containing CNVs from two or more distinct samples are identified as recurrent regions. All five engines produced 1,903 recurrent regions.

::::::{tab-set}
:::::{tab-item} PyArrow
```python
df["region_key"] = df["CHROM"] + ":" + ((df["POS"] // 1000) * 1000).astype(str)
recurrent = df.groupby("region_key")["SAMPLE_NAME"].nunique()
recurrent = recurrent[recurrent >= 2]   # 1,903 recurrent regions
```
:::::

:::::{tab-item} Polars
```python
df["region_key"] = df["CHROM"] + ":" + ((df["POS"] // 1000) * 1000).astype(str)
recurrent = df.groupby("region_key")["SAMPLE_NAME"].nunique()
recurrent = recurrent[recurrent >= 2]   # 1,903 recurrent regions
```
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
:::::

:::::{tab-item} Iceberg
```python
df["region_key"] = df["CHROM"] + ":" + ((df["POS"] // 1000) * 1000).astype(str)
recurrent = df.groupby("region_key")["SAMPLE_NAME"].nunique()
recurrent = recurrent[recurrent >= 2]   # 1,903 recurrent regions
```
:::::

:::::{tab-item} LanceDB
```python
df["region_key"] = df["CHROM"] + ":" + ((df["POS"] // 1000) * 1000).astype(str)
recurrent = df.groupby("region_key")["SAMPLE_NAME"].nunique()
recurrent = recurrent[recurrent >= 2]   # 1,903 recurrent regions
```
:::::
::::::

### Query 3 — filtered query

Variants on the most prevalent chromosome within the 10th–90th percentile position band. Each engine pushes the predicate into the storage layer. All five returned 589 variants.

::::::{tab-set}
:::::{tab-item} PyArrow
```python
import pyarrow.compute as pc
expr = ((pc.field("CHROM") == chrom)
        & (pc.field("POS") >= lo) & (pc.field("POS") <= hi))
filtered = dataset.to_table(filter=expr)   # predicate pushdown into Parquet row groups
```
:::::

:::::{tab-item} Polars
```python
filtered = lazy_df.filter(
    (pl.col("CHROM") == chrom) & (pl.col("POS") >= lo) & (pl.col("POS") <= hi)
).collect()
```
:::::

:::::{tab-item} DuckDB
```python
filtered = con.execute(
    "SELECT * FROM cnv_vcf WHERE CHROM = ? AND POS BETWEEN ? AND ?",
    [chrom, lo, hi],
).df()
```
:::::

:::::{tab-item} Iceberg
```python
from pyiceberg.expressions import And, EqualTo, GreaterThanOrEqual, LessThanOrEqual
row_filter = And(EqualTo("CHROM", chrom),
             And(GreaterThanOrEqual("POS", lo), LessThanOrEqual("POS", hi)))
filtered = table.scan(row_filter=row_filter).to_arrow()
```
:::::

:::::{tab-item} LanceDB
```python
filtered = table.to_lance().to_table(
    filter=f"CHROM = '{chrom}' AND POS BETWEEN {lo} AND {hi}"
).to_pandas()
```
:::::
::::::

<!-- PLOT: query_times.svg -->
![Query Times](https://lamin-site-assets.s3.amazonaws.com/.lamindb/d2r3p1yUGrcVTLtw0000.svg)

### Notes on query timing

**Polars vs. PyArrow.** Polars is ~4× faster than PyArrow across all three queries in store mode. Both engines run equivalent pandas aggregations after materialisation; the timing difference is attributable to the S3 read step. Polars reads the six shards concurrently; PyArrow's dataset API reads them more sequentially. In memory mode the difference is negligible. These are single-run measurements; the magnitude may vary with shard count and network conditions.

**Iceberg and LanceDB post-ingest query times.** The low query times for Iceberg (0.15–0.19s) and LanceDB (0.06–0.33s) reflect reads from their own pre-ingested S3 stores. Their per-query times exclude the one-time setup cost of 8.7s and 7.6s respectively. When amortised across ten queries, the total cost per query for each is approximately 1.1s — comparable to PyArrow and DuckDB.

---

## Writes

Three write operations were tested: appending a new sample (1,536 rows), adding a `QC_PASS` boolean column, and querying a historical state.

### Append

::::::{tab-set}
:::::{tab-item} PyArrow
The append saves a new artifact to LaminDB with schema validation and creates a new versioned collection. The operation includes an S3 upload, metadata registration, and lineage recording.

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
:::::

:::::{tab-item} Polars
Identical to PyArrow — the append uses LaminDB's artifact and collection APIs regardless of which query engine opened the data.

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
:::::

:::::{tab-item} DuckDB
The view is redefined to union in the new rows from an in-memory relation. No data is written to S3.

```python
con.register("append_batch", new_sample_arrow)
con.execute(
    f"CREATE OR REPLACE VIEW cnv_vcf AS "
    f"{base_select} UNION ALL SELECT * FROM append_batch"
)
```
:::::

:::::{tab-item} Iceberg
The append is atomic and snapshot-isolated. New Parquet files and a snapshot manifest are written to S3; concurrent readers see a consistent state throughout.

```python
table.append(new_sample_arrow)
```
:::::

:::::{tab-item} LanceDB
`add()` writes new rows to S3 and automatically increments the table version.

```python
table.add(new_sample_arrow)
# table.version == 2, table.count_rows() == 10,465
```
:::::
::::::

### Schema change

::::::{tab-set}
:::::{tab-item} PyArrow
A `QC_PASS` feature is registered in the LaminDB schema registry. All future artifacts saved against this schema — across the entire instance — are validated to include this feature.

```python
schema = ln.Schema.get(name="1000 Genomes CNV VCF")
feat = ln.Feature(name="QC_PASS", dtype=bool).save()
schema.add_optional_features([feat])
```
:::::

:::::{tab-item} Polars
Identical to PyArrow.

```python
schema = ln.Schema.get(name="1000 Genomes CNV VCF")
feat = ln.Feature(name="QC_PASS", dtype=bool).save()
schema.add_optional_features([feat])
```
:::::

:::::{tab-item} DuckDB
The view is redefined to include a virtual `NULL` column. No data is written to S3; the change exists only in the current session.

```python
con.execute(
    f"CREATE OR REPLACE VIEW cnv_vcf AS "
    f"SELECT *, CAST(NULL AS BOOLEAN) AS QC_PASS FROM ({base_select}) t"
)
```
:::::

:::::{tab-item} Iceberg
A new metadata file is written to S3 recording the updated schema. Existing Parquet files are not modified; reads of old files return `null` for the new column.

```python
from pyiceberg.types import BooleanType
with table.update_schema() as update:
    update.add_column("QC_PASS", BooleanType())
```
:::::

:::::{tab-item} LanceDB
A new column is added via SQL expression. All existing rows receive `null` for the new column.

```python
table.add_columns({"QC_PASS": "CAST(NULL AS BOOLEAN)"})
```
:::::
::::::

### Time travel

::::::{tab-set}
:::::{tab-item} PyArrow
The pre-append collection version is addressable by UID. LaminDB retains all prior collection versions.

```python
original = ln.Collection.get("K6X8Ejk3fjgAZT6h0000")
rows_v1 = original.open().count_rows()   # 8,929
```
:::::

:::::{tab-item} Polars
Same as PyArrow — collection versioning via LaminDB.

```python
original = ln.Collection.get("K6X8Ejk3fjgAZT6h0000")
with original.open(engine="polars") as lazy_v1:
    rows_v1 = lazy_v1.select(pl.len()).collect().item()   # 8,929
```
:::::

:::::{tab-item} DuckDB
Not supported. DuckDB maintains no snapshot history; the view redefinition used for append is also session-scoped.

```python
# not available
```
:::::

:::::{tab-item} Iceberg
Any historical snapshot is queryable by snapshot ID. Snapshots are retained until explicitly expired.

```python
first_snapshot = table.history()[0].snapshot_id
historical = table.scan(snapshot_id=first_snapshot).to_arrow()
historical.num_rows   # 8,929
```
:::::

:::::{tab-item} LanceDB
A specific version is checked out by integer version number and restored with `checkout_latest()`.

```python
table.checkout(1)             # version 1 = pre-append state
table.count_rows()            # 8,929
table.checkout_latest()       # restore current version
```
:::::
::::::

<!-- PLOT: write_path.svg -->
![Write Path](https://lamin-site-assets.s3.amazonaws.com/.lamindb/VnVruqKX9KK0uhUw0000.svg)

### Notes on write timing

**DuckDB append and schema change.** The 0.24s append and 0.25s schema change for DuckDB are not persisted operations. Both are in-session view redefinitions; no data is written to S3. These timings are not directly comparable to the persisted writes of the other four engines.

**LaminDB append and schema change scope.** The LaminDB append time (9.4s) includes an S3 upload, schema validation, stable UID assignment, lineage graph linking, and creation of a new collection version. The schema change time (3.5s) includes round-trips to a Postgres-backed schema registry that applies instance-wide. These operations have a wider scope than the equivalent operations in Iceberg (table-scoped) and LanceDB (table-scoped), which is reflected in the timing difference.

---

## Developer experience compared

| | PyArrow | Polars | DuckDB | Iceberg | LanceDB |
|---|---|---|---|---|---|
| **Setup** | 1 line, ~0s | 1 line, ~0s | 5 lines, ~1s | ~20 lines, ~8.7s | 3 lines, ~7.6s |
| **Data ingestion required** | No | No | No | No (wraps source Parquet) | Yes (copies to Lance format) |
| **Query API** | PyArrow / pandas | Polars / pandas | SQL | Iceberg expressions / pandas | PyArrow / pandas / SQL |
| **Store-mode query time** | ~1.1–1.4s | ~0.27–0.35s | ~0.77–0.87s | ~0.15–0.19s* | ~0.06–0.33s* |
| **Append** | S3 upload + schema validation + collection version | same as PyArrow | session-only view | atomic snapshot to S3 | versioned write to S3 |
| **Append time** | 9.4s | 9.5s | 0.24s† | 0.88s | 0.11s |
| **Schema change scope** | instance-wide registry | instance-wide registry | session only† | this table | this table |
| **Schema change time** | 3.5s | 3.6s | 0.25s† | 0.31s | 0.06s |
| **Time travel** | collection versions | collection versions | not supported | snapshot ID | version number |
| **ACID** | schema validation + collection versioning | same as PyArrow | none | full snapshot isolation | versioned appends |
| **Vector search** | no | no | no | no | yes |
| **Stays in LaminDB lineage** | yes | yes | yes | yes | no |

\* Post-ingest; excludes one-time setup cost of 8.7s (Iceberg) and 7.6s (LanceDB).
† Not persisted; session-scoped only.

---

## LaminDB as a data layer

The five engines above address the question of *how* to query data. LaminDB addresses a different question: *how to manage data across the lifecycle of a project.*

In this benchmark, LaminDB serves as the storage layer underneath all five query engines. The same collection is opened by each engine without any data movement or format conversion (with the exception of LanceDB, which copies the data out). LaminDB does not provide a query engine and does not compete with DuckDB, Iceberg, or LanceDB on query performance.

What LaminDB provides:

**Lineage.** Each pipeline notebook in this benchmark is a tracked transform. The timing results are saved as tracked artifacts. A final `plots.py` script reads those five artifacts as registered inputs and writes the comparison figures as registered outputs. The full provenance chain — from the original 1000 Genomes data transfer through to the figures in this report — is recorded in LaminHub:

![Lineage on Lamin Hub](https://lamin-site-assets.s3.amazonaws.com/.lamindb/v7yD8XvBy0eViHGG0000.png)

Note: DuckDB is the one exception in this lineage graph. It reads the collection's Parquet files directly via S3 paths rather than through LaminDB's `collection.open()` API, so the collection node has no incoming arrow from `duckdb_pipeline.ipynb`. The benchmark result artifact (`benchmark_results/duckdb.parquet`) is still tracked as an output of that notebook run.

**Schema validation.** A schema registered against a collection validates new artifacts at write time. In the governance demo included in the PyArrow and Polars pipelines, saving a DataFrame with an unrecognised column against a closed schema raises a `ValidationError` before the data reaches storage.

**Collection versioning.** Each append creates a new collection version. Prior versions remain addressable by UID, providing a form of time travel equivalent to Iceberg's snapshot history and LanceDB's version checkout — but at the collection level rather than the table level.

**Metadata-queryable collections.** Artifacts in LaminDB carry biological metadata (organism, tissue, disease, experimental factor). Collections can be filtered by these metadata fields before any data is opened, allowing engine-agnostic subsetting at the collection level.

These capabilities are available regardless of which query engine is used.

---

## Conclusion

The five approaches in this comparison cover the main strategies for querying Parquet-based genomic data from a LaminDB collection: lazy reads without ingestion (PyArrow, Polars, DuckDB), metadata-layer ingestion (Iceberg), and format-conversion ingestion (LanceDB).

The primary tradeoffs observed:

- **Setup cost vs. query cost.** Iceberg and LanceDB incur a one-time setup cost of 7–9s that is amortised across subsequent queries. PyArrow, Polars, and DuckDB have negligible setup cost but re-read S3 on each store-mode query.
- **Query conciseness.** DuckDB's SQL interface produces the most concise aggregation queries. PyArrow and Polars require more verbose pandas expressions for equivalent operations.
- **Write durability.** DuckDB appends and schema changes are session-scoped and not persisted. All other engines write to S3.
- **Write scope.** LaminDB write operations (append, schema change) have instance-wide scope and include provenance recording; Iceberg and LanceDB operations are table-scoped.
- **Lineage.** Only LaminDB and the engines reading from LaminDB in place (PyArrow, Polars, DuckDB) maintain provenance. LanceDB copies data out of LaminDB's lineage graph.
- **S3 parallelism.** Polars reads the six source shards concurrently; PyArrow reads them more sequentially. On this dataset, the observed difference is ~4× in store mode.

Zooming out: as the capability table in the first section shows, Iceberg, DuckLake, and LaminDB each address different layers of the lakehouse problem. Iceberg provides snapshot-isolated ACID transactions for tabular data with query engine independence. DuckLake adds concurrent writers and automatic maintenance by moving metadata into a relational database. LaminDB adds heterogeneous file support, biological metadata, and lineage tracking — and is largely complementary to both.

---

## Author contributions

Alex Rasmussen wrote the lakehouse ecosystem overview. Raaghav Pillai performed the benchmarking work and wrote the pipelines. The original LaminDB ingestion pipeline was developed by Sunny Sun. Alex Wolf and Sergei Rybakov supervised the project.

## Code & data availability

The five pipeline notebooks, the shared benchmarking utilities, and the plotting script are tracked in the `laminlabs/lakehouse-benchmarks` instance.

- [PyArrow pipeline](https://lamin.ai/laminlabs/lakehouse-benchmarks/transform/D10UPamv70IP0001)
- [Polars pipeline](https://lamin.ai/laminlabs/lakehouse-benchmarks/transform/2Wdo02w0MDgH0000)
- [DuckDB pipeline](https://lamin.ai/laminlabs/lakehouse-benchmarks/transform/tQaG9uhSD7BO0000)
- [Iceberg pipeline](https://lamin.ai/laminlabs/lakehouse-benchmarks/transform/wnVO8cu0qtOP0001)
- [LanceDB pipeline](https://lamin.ai/laminlabs/lakehouse-benchmarks/transform/WtZF9OX9v3uM0001)

The dataset is the 1000 Genomes Project CNV calls (DRAGEN, hg38), collection UID `K6X8Ejk3fjgAZT6h0000`.

## How to cite

```
Rasmussen A, Pillai R, Rybakov S & Wolf A (2026). Lakehouse engineering:
benchmarking metadata-driven query optimization.
Lamin Blog.
```