---
title: "Comparing PyArrow, Iceberg, DuckDB, LanceDB & Polars in queries of the 1000 Genomes Project"
date: 2026-06-25
author: Raaghav-Pillai, alexras, sunnyosun, Koncopd, falexwolf
affiliation:
  Raaghav-Pillai: Lamin Labs, NYC
  alexras: BitsOnDisk
  sunnyosun: Lamin Labs, Munich
  Koncopd: Lamin Labs, Munich
  falexwolf: Lamin Labs, Munich
db: https://lamin.ai/laminlabs/lakehouse-benchmarks
---

Over the past decade, the lakehouse has become the dominant data architecture in R&D.
In this post, we benchmark exemplary queries and review managing the life cycle of thousands of parquet files from the 1000 Genomes Project across PyArrow, Iceberg, DuckDB, LanceDB & Polars.

## The lakehouse landscape

The lakehouse architecture promises the flexibility of a data lake with the structure of a data warehouse enabling to work with multi-modal datasets with dedicated queries. Today's most popular lakehouse table format is Apache Iceberg[^iceberg], which provides transactions for manipulations of tabular datasets that are stored in of `.parquet` object storage systems like AWS S3.

### Iceberg and manifest-based snapshots

Under the hood, Iceberg organizes data into _snapshots_ — each a collection of data files plus manifest files that track which files belong to which snapshot. A single root metadata file describes the table's schema and points to the current snapshot. When a query engine writes to an Iceberg table, it creates a new snapshot and atomically updates the root metadata file to point to it.

This snapshot-based approach offers several advantages over raw files in S3. Iceberg writes are serializable ACID transactions, enabling time travel (reading previous snapshots), certain types of schema evolution without data rewrites, and write-audit-publish workflows where new snapshots can be staged for quality checks before becoming visible to consumers. Any query engine implementing the Iceberg spec supports these operations, providing flexibility in tooling.

But Iceberg's snapshot model has real costs. Creating a snapshot is expensive, so Iceberg assumes large, infrequent writes — small random writes are impractical. Optimistic concurrency control means concurrent writers will collide and all but one will fail. On S3 (which lacked atomic compare-and-swap until recently), an external catalog or lock is needed to coordinate metadata updates. Garbage collection of orphaned data files requires explicit action and doesn't happen automatically. Multi-table transactions are only available with certain catalogs.

### DuckLake and the relational metadata approach

One recent effort to address Iceberg's limitations is DuckLake,[^ducklake] developed by the DuckDB team. Rather than storing metadata in object storage files, DuckLake keeps all metadata in a relational database, leaving only the actual data files in S3. This gives it serializable transactions with true concurrent writer support, automatic maintenance via the database's native mechanisms, and native multi-table transactions — all things that are difficult or impossible with Iceberg's file-based metadata.

### Where LaminDB fits

LaminDB shares DuckLake's key architectural insight: use a relational database for metadata and object storage for data but it goes further in scope.
While Iceberg and DuckLake are exclusively concerned with tabular data in parquet files, LaminDB manages data in any format — Parquet, AnnData, HDF5, zarr, VCF, ... and provides features like data lineage.

LaminDB is largely complementary to Iceberg rather than a replacement. Iceberg, like the other engines here, is best seen as a downstream query engine that consumes collections of parquet files managed by LaminDB. LaminDB tracks which pipeline run produced a collection and links it to the AnnData files and VCFs that informed it, while the engine handles querying.

### Capability comparison

| Feature                                 | Raw Files | Iceberg | DuckLake | LaminDB |
| --------------------------------------- | --------- | ------- | -------- | ------- |
| ACID transactions                       | ❌        | ✅      | ✅       | ✅¹     |
| Time travel / snapshot isolation        | ❌        | ✅      | ✅       | ✅²     |
| Schema evolution without rewriting data | ❌        | ✅³     | ✅³      | ✅³     |
| Write-Audit-Publish workflow            | ❌        | ✅      | ❌       | ✅⁴     |
| Query engine independence               | ✅        | ✅      | ❌       | ✅      |
| Concurrent writers                      | ❌⁵       | ❌      | ✅       | ✅      |
| Automatic maintenance                   | ❌        | ❌      | ✅       | ✅⁶     |
| Native multi-table transactions         | ❌        | ❌      | ✅       | ❌      |
| Heterogeneous file support              | ✅        | ❌      | ❌       | ✅      |
| Data lineage                            | ❌        | ❌      | ❌       | ✅      |
| Ontologies                              | ❌        | ❌      | ❌       | ✅      |
| Registries with fine-grained control    | ❌        | ❌      | ❌       | ✅      |

¹ LaminDB guarantees storage↔metadata consistency, not row-level ACID inserts into parquet the way Iceberg and DuckLake do.

² Prior collection versions are addressable by UID — see the Time travel section.

³ Partial in all three: adding a nullable/optional column without rewriting existing files. LaminDB does this via an optional feature on the collection's schema.

⁴ Via LaminDB branches (stage, review, merge). [confirm mechanism in manage-changes.md]

⁵ Raw files have no commit protocol; concurrent writers risk partial writes / last-writer-wins.

⁶ Compaction of small files and garbage collection of orphaned data files without a manual step.

## Benchmarks

The second half of this post compares five tools — PyArrow, Iceberg, DuckDB, Polars, and LanceDB — for querying a collection of parquet files that store copy number variation data. We run against two layouts of the CNV data: a many-file layout (4M rows across 3,201 Parquet shards) and a few-file layout (88M rows across 26 shards). The contrast is deliberate — despite carrying 22× more data, the few-file run is dramatically faster for the read-bound engines, because wall-clock time on S3 is driven by per-file footer round-trips, not row count.

With each tool, we run the same four-step workflow: access, query, append rows, and evolve the schema. In the query step we run typical analytical computations, including computing per-sample statistics or recurrent region identification.
These operations are routine in genomics but span the full read-write operations of any tool. We'll try to make trade-offs evident: one tool might make querying concise but schema changes ephemeral; another tool that provides durable writes may require an upfront ingestion step; another tool that copies data into its own format removes it from the lineage graph.

All five approaches read from the same collection of parquet files on AWS S3:

```python
import lamindb as ln

db = ln.DB("laminlabs/lakehouse-benchmarks")
collection = db.Collection.get("Lh6IsCOGIl5TOjAj") #hVu9puwdRGskm1I6 for the 88M dataset
```

Three engines — PyArrow, Polars, and DuckDB — read the source Parquet files in place. Two — Iceberg and LanceDB — ingest the data into their own format before querying.

---

## Setup

::::::{tab-set}
:::::{tab-item} PyArrow
`collection.open()` returns a lazy PyArrow dataset backed by S3. No data is read until a query is issued.

```python
dataset = collection.open()   # lazy PyArrow dataset over the collection's shards
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
Iceberg requires a full materialisation of the LaminDB collection before ingestion into a catalog-managed table on S3. On the many-file layout this read dominates setup (~34 min); see the setup plot.

```python
from pyiceberg.catalog.sql import SqlCatalog

arrow = collection.open().to_table()

catalog = SqlCatalog("local", uri="sqlite:///iceberg_catalog.db", warehouse=WAREHOUSE)
catalog.create_namespace("genomics")
table = catalog.create_table("genomics.cnv_vcf", schema=arrow.schema)
table.overwrite(arrow)
```

Note: a SQLite catalog is used here for portability. Production deployments would use a Glue or REST catalog.
![Iceberg Warehouse S3 file layout](https://lamin-site-assets.s3.amazonaws.com/.lamindb/OgVhDACCMhzGKC4t0000.svg)

:::::

:::::{tab-item} LanceDB
LanceDB requires a full materialisation of the LaminDB collection and ingestion into Lance columnar format on S3. LanceDB is the only engine in this comparison that copies data out of the source Parquet files.

```python
import lancedb

arrow = collection.open().to_table()
db = lancedb.connect(WAREHOUSE)
table = db.create_table("cnv_vcf", data=arrow, mode="overwrite")
```

:::::
::::::

**Setup summary:**

<!-- PLOT: setup_cost.svg -->

Setup cost splits sharply by file count. On the many-file layout the one-time read into Iceberg/LanceDB runs ~34 minutes; on the few-file layout the same step is under three minutes.

![Setup cost — 4M rows, 3,201 files](https://lamin-site-assets.s3.amazonaws.com/.lamindb/Lf8f0LJY63quZ3n70001.svg)

Link to Plot: https://lamin.ai/laminlabs/lakehouse-benchmarks/artifact/kBOCwXvajOXJAniJ000L

![Setup cost — 88M rows, 26 files](https://lamin-site-assets.s3.amazonaws.com/.lamindb/Lf8f0LJY63quZ3n70002.svg)

Link to Plot: https://lamin.ai/laminlabs/lakehouse-benchmarks/artifact/kBOCwXvajOXJAniJ000N

---

## Queries

Three queries were run against all five engines. The computation logic is equivalent across engines; differences in timing reflect S3 read strategy and whether data has been pre-ingested.

All timings are single-run measurements on the two layouts above. On the many-file (3,201-shard) layout, the read-bound engines are dominated by per-file S3 footer round-trips rather than compute; on the few-file (26-shard) layout that cost largely disappears. Iceberg and LanceDB query times reflect reads from their own pre-ingested stores, so their setup cost should be amortised across queries when comparing total cost.

### Query 1 — filtered query

Variants on the most prevalent chromosome within the 10th–90th percentile position band. Each engine pushes the predicate into the storage layer. All five engines returned identical result sets.

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

### Query 2 — per-sample CNV statistics

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

### Query 3 — recurrent region detection

Genomic positions are binned into 1 kbp windows. Bins containing CNVs from two or more distinct samples are identified as recurrent regions. all five engines produced identical results.

::::::{tab-set}
:::::{tab-item} PyArrow

```python
df["region_key"] = df["CHROM"] + ":" + ((df["POS"] // 1000) * 1000).astype(str)
recurrent = df.groupby("region_key")["SAMPLE_NAME"].nunique()
recurrent = recurrent[recurrent >= 2]
```

:::::

:::::{tab-item} Polars

```python
df["region_key"] = df["CHROM"] + ":" + ((df["POS"] // 1000) * 1000).astype(str)
recurrent = df.groupby("region_key")["SAMPLE_NAME"].nunique()
recurrent = recurrent[recurrent >= 2]
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
""").df()
```

:::::

:::::{tab-item} Iceberg

```python
df["region_key"] = df["CHROM"] + ":" + ((df["POS"] // 1000) * 1000).astype(str)
recurrent = df.groupby("region_key")["SAMPLE_NAME"].nunique()
recurrent = recurrent[recurrent >= 2]
```

:::::

:::::{tab-item} LanceDB

```python
df["region_key"] = df["CHROM"] + ":" + ((df["POS"] // 1000) * 1000).astype(str)
recurrent = df.groupby("region_key")["SAMPLE_NAME"].nunique()
recurrent = recurrent[recurrent >= 2]
```

:::::
::::::

<!-- PLOT: query_times.svg -->

![Query Times — 4M rows, 3,201 files](https://lamin-site-assets.s3.amazonaws.com/.lamindb/d2r3p1yUGrcVTLtw0002.svg)

Link to Plot: https://lamin.ai/laminlabs/lakehouse-benchmarks/artifact/0Pzx1HBBsf5YsfvT000L

![Query Times — 88M rows, 26 files](https://lamin-site-assets.s3.amazonaws.com/.lamindb/d2r3p1yUGrcVTLtw0003.svg)

Link to Plot: https://lamin.ai/laminlabs/lakehouse-benchmarks/artifact/kBOCwXvajOXJAniJ000N

### Notes on query timing

**Read strategy dominates on the many-file layout.** PyArrow's dataset API fetches the 3,201 footers largely sequentially; Polars and DuckDB parallelise, which is why DuckDB runs the heavy aggregations in ~17s where PyArrow takes ~2,000s. On the few-file layout the gap narrows to single-digit factors. Ratios vary by query, so we report per-query times in the plots rather than a single speedup number.

**Iceberg and LanceDB post-ingest query times.** The low query times for Iceberg and LanceDB reflect reads from their own pre-ingested S3 stores. Their per-query times exclude the one-time setup cost of 2038s/51s and 2035s/152s respectively.

### Why file count dominates

The two layouts isolate a behaviour worth stating plainly: for the read-bound engines, wall-clock time tracks the number of Parquet files, not the number of rows. Opening a collection reads one footer per file; PyArrow fetches these largely serially, so 3,201 small shards cost far more than 26 large ones even when the large-file layout holds 22× the data.
The effect is order-of-magnitude. PyArrow's per-sample statistics run ~2,000s on the 3,201-file layout versus ~102s on the 26-file layout; Iceberg and LanceDB's one-time ingestion read drops from ~34 min to ~2 min. Engines that parallelise footer reads (DuckDB) or pre-compact into their own store (Iceberg, LanceDB) blunt this cost; engines that read in place and serially (PyArrow) are hit hardest.
The practical takeaway is a tuning knob independent of engine choice: compacting many small shards into fewer large ones is often a bigger win than switching engines. [If you have the same-data 3,201→26 repack numbers from the file-count test, cite them here — that's the controlled version of this claim.]

## Writes

Three write operations were tested: appending a new sample, adding a `QC_PASS` boolean column, and querying a historical state.

### Append

::::::{tab-set}
:::::{tab-item} PyArrow
PyArrow has no append operation for a sharded dataset — appending is a data-layer operation handled by LaminDB. A new artifact is saved with schema validation, then appended to the collection, creating a new version (S3 upload, metadata registration, lineage recording).

```python
new_art = ln.Artifact.from_dataframe(
    new_sample_df,
    key=f"lakehouse-benchmarks/append_batch_{ln.context.run.uid}.parquet",
    description="benchmark append batch (new sample)",
).save()

new_collection = collection.append(new_art)   # returns a new collection version
```

:::::

:::::{tab-item} Polars
Polars has no append API either — this is the same LaminDB collection.append() shown in the PyArrow tab. The engine that opened the data doesn't change how appends work.

:::::

:::::{tab-item} DuckDB
The view is redefined to union in the new rows from an in-memory Arrow table (new_sample_arrow — the same 1,536-row batch appended in the other tabs). No data is written to S3; the change lives only in this con session.

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
```

:::::
::::::

### Schema change

::::::{tab-set}
:::::{tab-item} PyArrow
This is a LaminDB operation, not a PyArrow one — PyArrow can write new files with a different schema but has no registry-level evolution over an existing dataset. Here a QC_PASS feature is registered in the LaminDB schema registry; all future artifacts saved against this schema — instance-wide — are validated to include it.

```python
schema = ln.Schema.get(name="1000 Genomes CNV VCF")
feat = ln.Feature(name="QC_PASS", dtype=bool).save()
schema.add_optional_features([feat])
```

:::::

:::::{tab-item} Polars
Same LaminDB operation as the PyArrow tab — Polars has no schema-evolution API of its own.

:::::

:::::{tab-item} DuckDB
The view is redefined to include a virtual NULL column. Because the view sits over read_parquet, DuckDB can't persist this to the source files — the change exists only in the current session. Persisting it would require writing new Parquet files (or using DuckLake).

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
Time travel is a LaminDB capability, not a PyArrow one. Collection versions share a stable UID differing only in the suffix — ...0000 (pre-append) vs ...0001 (post-append) — and every prior version stays addressable.

```python
original = ln.Collection.get("Lh6IsCOGIl5TOjAj0000")   # 0000 = v1, pre-append
rows_v1 = original.open().count_rows()

current = ln.Collection.get("Lh6IsCOGIl5TOjAj0001")    # 0001 = v2, post-append
rows_v2 = current.open().count_rows()
```

:::::

:::::{tab-item} Polars
Same as PyArrow — collection versioning via LaminDB.

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
historical.num_rows   # 4M
```

:::::

:::::{tab-item} LanceDB
A specific version is checked out by integer version number and restored with `checkout_latest()`.

```python
table.checkout(1)             # version 1 = pre-append state
table.count_rows()            # 4M
table.checkout_latest()       # restore current version
```

:::::
::::::

<!-- PLOT: write_path.svg -->

![Write Path — 4M rows, 3,201 files](https://lamin-site-assets.s3.amazonaws.com/.lamindb/VnVruqKX9KK0uhUw0002.svg)

Link to Plot: https://lamin.ai/laminlabs/lakehouse-benchmarks/artifact/ZtoBlPvxz9zWcZ0M000K

![Write Path — 88M rows, 26 files](https://lamin-site-assets.s3.amazonaws.com/.lamindb/VnVruqKX9KK0uhUw0003.svg)

Link to Plot: https://lamin.ai/laminlabs/lakehouse-benchmarks/artifact/ZtoBlPvxz9zWcZ0M000M

### Notes on write timing

**DuckDB append and schema change.** The 0.48s append and 0.54s schema change for DuckDB are not persisted operations. Both are in-session view redefinitions; no data is written to S3. These timings are not directly comparable to the persisted writes of the other four engines.

**LaminDB append and schema change scope.** The LaminDB append time (11.99s) includes an S3 upload, schema validation, stable UID assignment, lineage graph linking, and creation of a new collection version. The schema change time (3.59s) includes round-trips to a Postgres-backed schema registry that applies instance-wide. These operations have a wider scope than the equivalent operations in Iceberg (table-scoped) and LanceDB (table-scoped), which is reflected in the timing difference.

## Developer experience compared (4M / 3,201-file run — see plots for 88M)

|                              | PyArrow                                            | Polars                 | DuckDB            | Iceberg                      | LanceDB                      |
| ---------------------------- | -------------------------------------------------- | ---------------------- | ----------------- | ---------------------------- | ---------------------------- | --- |
| **Setup**                    | 1 line                                             | 1 line                 | 5 lines           | ~20 lines                    | 3 lines                      |
| **Data ingestion required**  | No                                                 | No                     | No                | No (wraps source Parquet)    | Yes (copies to Lance format) |
| **Query API**                | PyArrow / pandas                                   | Polars / pandas        | SQL               | Iceberg expressions / pandas | PyArrow / pandas / SQL       |
| **Append**                   | S3 upload + schema validation + collection version | same as PyArrow        | session-only view | atomic snapshot to S3        | versioned write to S3        |     |
| **Schema change scope**      | instance-wide registry                             | instance-wide registry | session only†     | this table                   | this table                   |
| **Time travel**              | collection versions                                | collection versions    | not supported     | snapshot ID                  | version number               |
| **ACID**                     | schema validation + collection versioning          | same as PyArrow        | none              | full snapshot isolation      | versioned appends            |
| **Vector search**            | no                                                 | no                     | no                | no                           | yes                          |
| **Stays in LaminDB lineage** | yes                                                | yes                    | yes               | yes                          | no                           |

† Not persisted; session-scoped only.

What LaminDB provides:

**Lineage.** Each pipeline notebook in this benchmark is a tracked transform. The timing results are saved as tracked artifacts. A final `plots.py` script reads those five artifacts as registered inputs and writes the comparison figures as registered outputs. The full provenance chain — from the original 1000 Genomes data transfer through to the figures in this report — is recorded in LaminHub:

![Lineage on Lamin Hub](https://lamin-site-assets.s3.amazonaws.com/.lamindb/v7yD8XvBy0eViHGG0001.png)
Link to view lineage: https://lamin.ai/laminlabs/lakehouse-benchmarks/artifact/0Pzx1HBBsf5YsfvT000L

Note: DuckDB is the one exception in this lineage graph. It reads the collection's Parquet files directly via S3 paths rather than through LaminDB's `collection.open()` API, so the collection node has no incoming arrow from `duckdb_pipeline.ipynb`. The benchmark result artifact (`benchmark_results/duckdb.parquet`) is still tracked as an output of that notebook run.

**Schema validation.** A schema registered against a collection validates new artifacts at write time. In the governance demo included in the PyArrow and Polars pipelines, saving a DataFrame with an unrecognised column against a closed schema raises a `ValidationError` before the data reaches storage.

**Collection versioning.** Each append creates a new collection version. Prior versions remain addressable by UID, providing a form of time travel equivalent to Iceberg's snapshot history and LanceDB's version checkout — but at the collection level rather than the table level.

**Metadata-queryable collections.** Artifacts in LaminDB carry biological metadata (organism, tissue, disease, experimental factor). Collections can be filtered by these metadata fields before any data is opened, allowing engine-agnostic subsetting at the collection level.

These capabilities are available regardless of which query engine is used.

## Conclusion

The five approaches in this comparison cover the main strategies for querying Parquet-based genomic data from a LaminDB collection: lazy reads without ingestion (PyArrow, Polars, DuckDB), metadata-layer ingestion (Iceberg), and format-conversion ingestion (LanceDB).

The primary tradeoffs observed:

- **Setup cost scales with file count.** On the 3,201-file layout, pre-ingesting into Iceberg or LanceDB takes ~34 min (a full footer-bound read); on the 26-file layout it's under 3 min. In-place engines skip this entirely but pay footer costs on every query.
- **File count, not data volume, drives read time.** The 4M-row / 3,201-file run is slower than the 88M-row / 26-file run for every read-bound engine — the clearest single result in this benchmark.
- **Query conciseness.** DuckDB's SQL interface produces the most concise aggregation queries. PyArrow and Polars require more verbose pandas expressions for equivalent operations.
- **Write durability.** DuckDB appends and schema changes are session-scoped and not persisted. All other engines write to S3.
- **Write scope.** LaminDB write operations (append, schema change) have instance-wide scope and include provenance recording; Iceberg and LanceDB operations are table-scoped.
- **Lineage.** Only LaminDB and the engines reading from LaminDB in place (PyArrow, Polars, DuckDB) maintain provenance. LanceDB copies data out of LaminDB's lineage graph.
- **Schema validation.** A schema registered on a collection rejects non-conforming artifacts at write time, before data reaches storage.
- **Versioning as time travel.** Each append creates a new collection version; prior versions stay addressable by UID.

Zooming out: as the capability table in the first section shows, Iceberg, DuckLake, and LaminDB each address different layers of the lakehouse problem. Iceberg provides snapshot-isolated ACID transactions for tabular data with query engine independence. DuckLake adds concurrent writers and automatic maintenance by moving metadata into a relational database. LaminDB adds heterogeneous file support, biological metadata, and lineage tracking — and is largely complementary to both.

## Author contributions

Raaghav Pillai performed data engineering and analysis.
Alex Rasmussen wrote the lakehouse ecosystem overview.
The original LaminDB ingestion pipeline was developed by Sunny Sun.
Alex Wolf and Sergei Rybakov supervised the project.

## Code & data availability

The five pipeline notebooks, the shared benchmarking utilities, and the plotting script are tracked in the `laminlabs/lakehouse-benchmarks` instance.

- [PyArrow pipeline](https://lamin.ai/laminlabs/lakehouse-benchmarks/transform/D10UPamv70IP)
- [Polars pipeline](https://lamin.ai/laminlabs/lakehouse-benchmarks/transform/2Wdo02w0MDgH)
- [DuckDB pipeline](https://lamin.ai/laminlabs/lakehouse-benchmarks/transform/tQaG9uhSD7BO)
- [Iceberg pipeline](https://lamin.ai/laminlabs/lakehouse-benchmarks/transform/wnVO8cu0qtOP)
- [LanceDB pipeline](https://lamin.ai/laminlabs/lakehouse-benchmarks/transform/WtZF9OX9v3uM)

The dataset is the 1000 Genomes Project CNV calls (DRAGEN, hg38), collection UID `Lh6IsCOGIl5TOjAj`.

## Methods

All timings are single-run measurements on SageMaker (`ml.m5.24xlarge`) in store mode unless otherwise stated.

## How to cite

```
Rasmussen A, Pillai R, Rybakov S & Wolf A (2026). Lakehouse engineering:
benchmarking metadata-driven query optimization.
Lamin Blog.
```

## References

[^iceberg]: Apache Software Foundation. Apache Iceberg: The open table format for analytic datasets. [Apache Iceberg](https://iceberg.apache.org/).

[^ducklake]: Raasveldt M & Holanda P (2026). DuckLake v1.0: The Lakehouse Format Built on SQL Reaches Production-Readiness. [DuckLake Blog](https://ducklake.select/2026/04/13/ducklake-10/).
