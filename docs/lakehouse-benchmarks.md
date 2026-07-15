---
title: "Polars, DuckDB, Iceberg & LanceDB for the datasets of the 1000 Genomes Project"
date: 2026-07-15
author: Raaghav-Pillai, alexras, ishitajain9717, sunnyosun, Koncopd, falexwolf
affiliation:
  Raaghav-Pillai: Lamin Labs, NYC
  alexras: BitsOnDisk
  ishitajain9717: Lamin Labs, Munich
  sunnyosun: Lamin Labs, Munich
  Koncopd: Lamin Labs, Munich
  falexwolf: Lamin Labs, Munich
db: https://lamin.ai/laminlabs/lakehouse-benchmarks
---

Over the past decade, the lakehouse has become the dominant data management architecture in R&D.
In this post we review how Polars, DuckDB, Iceberg, and LanceDB help to query and manage 100M observations from the 1000 Genomes Project.

## The lakehouse landscape

The lakehouse architecture promises the flexibility of a data lake with the structure of a data warehouse, so you can use different query engines for multi-modal datasets.
So, before reviewing query engines, we review three recent lakehouse frameworks.

### Frameworks

<figure style="float: right; width: 400px; margin-left: 0.5rem">
  <img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/OgVhDACCMhzGKC4t0000.svg" />
  <strong>Figure 1.</strong> File layout of an Iceberg table.
</figure>

**Iceberg.** Today's most popular lakehouse specification is Apache Iceberg,[^apache-iceberg] which provides transactions for manipulating tabular datasets in storage locations like AWS S3, alongside Delta Lake[^delta] and Apache Hudi[^hudi].
Iceberg is a table format that organizes datasets into _snapshots_ — each a collection of parquet files plus manifest files that track which files belong to which snapshot. A single root metadata file describes the table's schema and points to the current snapshot. When a query engine writes to an Iceberg table, it creates a new snapshot and atomically updates the root metadata file to point to it.

Unlike when working with raw parquet files Iceberg writes are [ACID transactions](https://en.wikipedia.org/wiki/ACID) and enable reading previous snapshots ("time travel"), certain types of schema evolution without data rewrites, and write-audit-publish workflows where new snapshots can be staged for quality checks before becoming visible to consumers. Any query engine implementing the Iceberg spec supports these operations, providing flexibility in tooling.

<div style="float: right; width: 65%; margin: 0.5rem 0 1rem 1.5rem; font-size: 0.85em;">

| Feature                                  | Raw S3 | Iceberg | DuckLake | LaminDB |
| ---------------------------------------- | ------ | ------- | -------- | ------- |
| Data lake (file management & annotation) | ✅     | ❌      | ❌       | ✅      |
| ACID transactions                        | ❌     | ✅      | ✅       | ✅ ¹    |
| Time travel / snapshot version isolation | ❌     | ✅      | ✅       | ✅ ²    |
| Schema evolution without rewriting data  | ❌     | ✅ ³    | ✅ ³     | ✅ ³    |
| Write-Audit-Publish workflow             | ❌     | ✅      | ❌       | ✅ ⁴    |
| Query engine independence                | ✅     | ✅      | ❌       | ✅      |
| Concurrent writers                       | ❌ ⁵   | ❌      | ✅       | ✅      |
| Automatic maintenance                    | ❌     | ❌      | ✅ ⁶     | ✅ ⁶    |
| Native multi-table transactions          | ❌     | ❌      | ✅       | ❌      |
| Dataset formats beyond tables            | ✅     | ❌      | ❌       | ✅      |
| Data lineage                             | ❌     | ❌      | ❌       | ✅      |
| Ontologies                               | ❌     | ❌      | ❌       | ✅      |
| Registries with fine-grained control     | ❌     | ❌      | ❌       | ✅      |

:::{dropdown} **Table 1.** A high-level overview of lakehouse technologies.

¹ LaminDB [guarantees data ↔ metadata consistency through ACID operations](https://docs.lamin.ai/faq/acid.md), but does not guarantee row-level ACID operations the way Iceberg and DuckLake do. Because you can map an insert into a collection of parquet files via `lamindb.Collection.append()` in an ACID way, the practical robustness guarantee to the user is similar.

² See the [Time travel](#time-travel) section.

³ Adding a nullable/optional column without rewriting existing files.

⁴ In LaminDB, via branches (stage, review, merge).

⁵ Raw files have no commit protocol; concurrent writers risk partial writes / last-writer-wins.

⁶ No need for cleaning orphaned files like in Iceberg.

:::

</div>

Iceberg's snapshot model has costs. Creating a snapshot is expensive, so Iceberg assumes large, infrequent writes. Optimistic concurrency control means concurrent writers will collide and all but one will fail. On S3, an external catalog (like Project Nessie,[^nessie] AWS Glue, or Databricks Unity Catalog) or lock is needed to coordinate metadata updates. Garbage collection of orphaned data files requires explicit action and doesn't happen automatically. And multi-table transactions are only available with certain catalogs.

**DuckLake.** One approach that gains popularity in addressing Iceberg's limitations is DuckLake,[^ducklake-format][^ducklake-v1] developed by the DuckDB team. Rather than storing metadata in files, DuckLake keeps all metadata in a relational database, leaving only parquet files in storage. This gives it much cheaper writes that can be more frequent, transactions with true concurrent writer support, automatic maintenance via the database's native mechanisms, and native multi-table transactions — all things that are difficult or impossible with Iceberg's file-based metadata.

One limitation remains, however: like Iceberg, DuckLake can only manage tabular data.

**LaminDB.** Unlike Iceberg and DuckLake, LaminDB goes beyond tables allowing to work with any storage format - parquet, AnnData, HDF5, zarr, VCF, …. The user can manage anything from blobs in a data lake to structured datasets with multiple array components with a single schema abstraction. LaminDB shares DuckLake's architectural design — a relational database for metadata and storage for data — and natively provides data lineage, among other features (**Table 1**).

**LanceDB, `arraylake`, `tensorstore`, `tiledb`.** While Iceberg & DuckLake are based on the parquet format, and LaminDB is format-agnostic, LanceDB manages datasets in the Lance format, a columnar format inspired by parquet that's optimized for arrays. To use LanceDB, you need to convert your data into the Lance format.
While LanceDB fits the lakehouse architecture, non-lakehouse architectures for managing array-like data exist, too, in particulary, `arraylake` & `tensorstore` for `.zarr` arrays, and `tiledb` for `.tiledb` arrays. While we consider `LanceDB` in some of our comparisons, these non-lakehouse technologies are out of scope for this post given the established query engines don't apply to them.

### Query engines

While lakehouse frameworks help managing large numbers of datasets, query engines enable querying those datasets. We'll review popular query engines in combination with different storage formats, most importantly, PyArrow,[^pyarrow] Polars,[^polars] & DuckDB.[^duckdb]

We will not consider distributed query engines like Apache Spark,[^spark] Trino,[^trino] and Dremio.[^dremio]

## Benchmarks

We run the same user journey — read, filter, aggregate, append, evolve schema, time-travel — over two layouts that isolate the effect of file count:

- **Dataset 1 (many files):** a CNV dataset where each file maps to one human individual — **4.86M rows across 3,201 Parquet files**, with per-sample columns (`SAMPLE_NAME`, `SAMPLE_GT`, `INFO_SVLEN`, …). Collection UID `Lh6IsCOGIl5TOjAj`.
- **Dataset 2 (few files):** an SNV/Indel/CNV dataset — **88M rows across 26 Parquet files**, with per-chromosome columns (`chrom`, `variant_type`, `af`, `eur_af`). Collection UID `hVu9puwdRGskm1I6`.

The two datasets have different schemas, so the _aggregation_ queries (Query 2 and Query 3) run analogous but not identical analyses — per-sample on Dataset 1, per-chromosome on Dataset 2. The read and filter operations are identical in logic, which is where the clean cross-layout comparison lives.

```python
# pip install lamindb
import lamindb as ln

db = ln.DB("laminlabs/lakehouse-benchmarks")
# base version of the collection, addressable by UID (append runs create newer versions)
collection = db.Collection.get("Lh6IsCOGIl5TOjAj0000") # hVu9puwdRGskm1I6 for the 88M dataset
```

Three tools — PyArrow, Polars, and DuckDB — read the source Parquet files in place. Two — Iceberg and LanceDB — ingest the data into their own format before querying.

### Setup

::::::{tab-set}
:::::{tab-item} PyArrow
A lazy PyArrow dataset backed by S3. No data is read until a query is issued.

```python
with collection.open(engine="pyarrow") as lazy_ds:  # lazy PyArrow dataset backed by S3
```

:::::

:::::{tab-item} Polars
A Polars LazyFrame backed by S3. No data is read until `.collect()` is called.

```python
with collection.open(engine="polars") as lazy_df:
    ...   # lazy_df is a Polars LazyFrame backed by S3
```

:::::

:::::{tab-item} DuckDB
DuckDB registers a lazy view over the collection's S3 paths via `httpfs`. The source bucket is cross-account (EU), so credentials are extracted from the artifact's own storage session — `PROVIDER credential_chain` does **not** authenticate here.

```python
import duckdb
con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs;")

# extract frozen session-token credentials from the artifact's storage session
# (see duckdb_pipeline.ipynb for the full async extraction)
con.execute(f"""
    CREATE OR REPLACE SECRET s3 (
        TYPE s3, KEY_ID '{access_key}', SECRET '{secret_key}',
        SESSION_TOKEN '{token}', REGION 'eu-central-1'
    )
""")

s3_paths = [a.path.as_posix() for a in collection.artifacts.all()]
con.execute(f"CREATE OR REPLACE VIEW cnv_vcf AS SELECT * FROM read_parquet({s3_paths})")
```

:::::

:::::{tab-item} Iceberg
Iceberg requires a full materialisation of the LaminDB collection before ingestion. On the many-file layout, that **read** dominates setup (~34 min); the Iceberg write itself is trivial (~6s).

```python
from pyiceberg.catalog.sql import SqlCatalog

arrow = collection.open().to_table()   # full materialise — the ~34 min cost on 3,201 files

catalog = SqlCatalog("local", uri="sqlite:///iceberg_catalog.db", warehouse=WAREHOUSE)
catalog.create_namespace("genomics")
table = catalog.create_table("genomics.cnv_vcf", schema=arrow.schema)
table.append(arrow)
```

:::::

:::::{tab-item} LanceDB
LanceDB also requires a full materialisation, then ingests into Lance columnar format on S3.

```python
import lancedb

arrow = collection.open().to_table()
db = lancedb.connect(WAREHOUSE)
table = db.create_table("cnv_vcf", data=arrow, mode="overwrite")
```

:::::
::::::

Setup cost, both layouts:

| Setup step (seconds)                                | PyArrow | Polars | DuckDB | Iceberg  | LanceDB  |
| --------------------------------------------------- | ------- | ------ | ------ | -------- | -------- |
| Read from LaminDB — Dataset 1 (4.86M / 3,201 files) | lazy    | lazy   | 23.9 ⁷ | **2043** | **2045** |
| Read from LaminDB — Dataset 2 (88M / 26 files)      | lazy    | lazy   | 2.7 ⁷  | 43.0     | 45.2     |
| Ingest — Dataset 1                                  | —       | —      | 0      | 6.0      | 7.0      |
| Ingest — Dataset 2                                  | —       | —      | 0      | 5.7      | 109.0 ⁸  |

⁷ DuckDB's setup number is a `CREATE VIEW` plus a `COUNT(*)`, which reads Parquet metadata only, not data.
⁸ LanceDB's ingest tracks row count: writing 88M rows into Lance format takes 109s vs 7s for 4.86M — the one place the few-file dataset is _slower_, because there is simply more data to rewrite.

The read cost is the story: ~34 minutes on 3,201 files versus under a minute on 26 files, despite Dataset 2 holding 18× the rows (**Figure 2**).

<div style="display: flex; gap: 16px; align-items: flex-start;">
  <div style="flex: 1; min-width: 0;">
    <img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/Lf8f0LJY63quZ3n70003.svg" />
    <p><strong>Figure 2a (<a href="https://lamin.ai/laminlabs/lakehouse-benchmarks/artifact/kBOCwXvajOXJAniJ000U">source</a>)</strong>: Dataset 1: 4.86M rows, 3,201 files.</p>
  </div>
  <div style="flex: 1; min-width: 0;">
    <img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/Lf8f0LJY63quZ3n70004.svg" />
    <p><strong>Figure 2b (<a href="https://lamin.ai/laminlabs/lakehouse-benchmarks/artifact/kBOCwXvajOXJAniJ000W">source</a>)</strong>: Dataset 2: 88M rows, 26 files.</p>
  </div>
</div>

### Queries

Query 1 filters variants on the most prevalent chromosome within the 10th–90th percentile position band — identical logic on both datasets (Dataset 1: chr1, 321,894 variants; Dataset 2: chr2, 5,665,280 variants). Queries 2 and 3 aggregate, and because the schemas differ they run analogous but not identical analyses (per-sample on Dataset 1, per-chromosome on Dataset 2). Within each dataset, all five engines returned identical results.

A note on how compute is measured. Query engines (PyArrow, Polars, DuckDB) compute natively. Table formats (Iceberg, LanceDB) are _not_ compute engines — they scan and hand data off — so their aggregations are a native scan plus a standard DuckDB aggregation, timed separately. That is why the format tabs read `scan → compute`.

The code tabs below show Dataset 1's per-sample analysis; Dataset 2 runs the analogous per-chromosome version (grouping by `chrom`, over `variant_type` / `af`).

**Query 1: filter by chromosome and position.**

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
# .to_lance() exposes the underlying Lance dataset so the predicate pushes down
# at the storage layer; the LanceDB table wrapper doesn't expose that filter directly.
filtered = table.to_lance().to_table(
    filter=f"CHROM = '{chrom}' AND POS BETWEEN {lo} AND {hi}"
)
```

:::::
::::::

**Query 2: summary statistics.** Dataset 1 (per sample): total CNV count, deletions, median deletion size, homozygous/heterozygous counts. Query engines compute natively; the two formats scan then aggregate in DuckDB via a shared `STATS_SQL`.

::::::{tab-set}
:::::{tab-item} PyArrow

```python
# Native PyArrow aggregation. Note: PyArrow only offers an *approximate* (t-digest)
# grouped median, so Median_Deletion_Size is approximate for PyArrow; SQL/Polars are exact.
t = dataset.to_table(columns=["SAMPLE_NAME", "INFO_SVLEN", "SAMPLE_GT"])
t = t.append_column("is_del", pc.cast(pc.less(t["INFO_SVLEN"], 0), pa.int64()))
t = t.append_column("is_hom", pc.cast(pc.equal(t["SAMPLE_GT"], "1/1"), pa.int64()))
t = t.append_column("is_het", pc.cast(pc.equal(t["SAMPLE_GT"], "0/1"), pa.int64()))
base = t.group_by("SAMPLE_NAME").aggregate([
    ("SAMPLE_NAME", "count"), ("is_del", "sum"), ("is_hom", "sum"), ("is_het", "sum"),
])
dels = t.filter(pc.less(t["INFO_SVLEN"], 0))
dels = dels.append_column("abs_svlen", pc.abs(dels["INFO_SVLEN"]))
med = dels.group_by("SAMPLE_NAME").aggregate([("abs_svlen", "approximate_median")])
stats = base.join(med, keys="SAMPLE_NAME", join_type="left outer")
```

:::::

:::::{tab-item} Polars

```python
stats = (
    lazy_df.group_by("SAMPLE_NAME").agg(
        pl.len().alias("Total_CNVs"),
        (pl.col("INFO_SVLEN") < 0).sum().alias("Deletions"),
        pl.col("INFO_SVLEN").filter(pl.col("INFO_SVLEN") < 0).abs().median().alias("Median_Deletion_Size"),
        (pl.col("SAMPLE_GT") == "1/1").sum().alias("Homozygous_CNVs"),
        (pl.col("SAMPLE_GT") == "0/1").sum().alias("Heterozygous_CNVs"),
    ).sort("SAMPLE_NAME").collect()
)
```

:::::

:::::{tab-item} DuckDB

```python
stats = con.execute("""
    SELECT SAMPLE_NAME,
           COUNT(*)                                              AS Total_CNVs,
           COUNT(*) FILTER (WHERE INFO_SVLEN < 0)                AS Deletions,
           MEDIAN(ABS(INFO_SVLEN)) FILTER (WHERE INFO_SVLEN < 0) AS Median_Deletion_Size,
           COUNT(*) FILTER (WHERE SAMPLE_GT = '1/1')             AS Homozygous_CNVs,
           COUNT(*) FILTER (WHERE SAMPLE_GT = '0/1')             AS Heterozygous_CNVs
    FROM cnv_vcf
    GROUP BY SAMPLE_NAME
""").df()
```

:::::

:::::{tab-item} Iceberg

```python
# Iceberg is a table format, not a compute engine: native scan, then aggregate in DuckDB.
arrow = table.scan().to_arrow()
stats = compute_duckdb(arrow, STATS_SQL)
```

:::::

:::::{tab-item} LanceDB

```python
arrow = table.to_arrow()
stats = compute_duckdb(arrow, STATS_SQL)
```

:::::
::::::

**Query 3: recurrent region detection.** Dataset 1 bins positions into 1 kbp windows and flags bins with CNVs from ≥2 distinct samples (67,763 regions). Dataset 2 bins into 1 Mbp windows and flags bins with ≥2 variants (2,911 regions) — a different definition, dictated by the schema. Code shown is Dataset 1.

::::::{tab-set}
:::::{tab-item} PyArrow

```python
t = dataset.to_table(columns=["CHROM", "POS", "SAMPLE_NAME"])
bin_start = pc.multiply(pc.cast(pc.divide(t["POS"], 1000), pa.int64()), 1000)
region_key = pc.binary_join_element_wise(
    pc.cast(t["CHROM"], pa.string()), pc.cast(bin_start, pa.string()), ":")
t = t.append_column("region_key", region_key)
pairs = t.select(["region_key", "SAMPLE_NAME"]).group_by(["region_key", "SAMPLE_NAME"]).aggregate([])
counts = pairs.group_by("region_key").aggregate([("SAMPLE_NAME", "count")])
recurrent = counts.filter(pc.greater_equal(counts["SAMPLE_NAME_count"], 2))
```

:::::

:::::{tab-item} Polars

```python
recurrent = (
    lazy_df.with_columns(
        (pl.col("CHROM").cast(pl.Utf8) + ":" +
         ((pl.col("POS") // 1000) * 1000).cast(pl.Utf8)).alias("region_key")
    )
    .group_by("region_key").agg(pl.col("SAMPLE_NAME").n_unique().alias("sample_count"))
    .filter(pl.col("sample_count") >= 2)
    .sort("sample_count", descending=True).collect()
)
```

:::::

:::::{tab-item} DuckDB

```python
recurrent = con.execute("""
    SELECT CHROM || ':' || CAST((POS // 1000) * 1000 AS VARCHAR) AS region_key,
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
arrow = table.scan().to_arrow()
recurrent = compute_duckdb(arrow, RECURRENT_SQL)
```

:::::

:::::{tab-item} LanceDB

```python
arrow = table.to_arrow()
recurrent = compute_duckdb(arrow, RECURRENT_SQL)
```

:::::
::::::

### Timing results

For the table formats, `scan + compute` is shown; the compute segment is a DuckDB aggregation over the native scan.

**Query 1 — filtered query (identical logic on both datasets):**

| Seconds                 | PyArrow | Polars | DuckDB   | Iceberg | LanceDB |
| ----------------------- | ------- | ------ | -------- | ------- | ------- |
| Dataset 1 (3,201 files) | 1012    | 12.1   | **2181** | 0.78    | 1.44    |
| Dataset 2 (26 files)    | 7.4     | 2.1    | 4.8      | 1.92    | 8.87    |

**Query 2 — statistics** (per-sample on D1, per-chromosome on D2):

| Seconds   | PyArrow | Polars | DuckDB | Iceberg     | LanceDB      |
| --------- | ------- | ------ | ------ | ----------- | ------------ |
| Dataset 1 | 1022    | 11.6   | 17.2   | 0.82 + 0.07 | 1.79 + 0.53  |
| Dataset 2 | 64.4    | 2.34   | 2.84   | 2.55 + 0.15 | 22.75 + 6.29 |

**Query 3 — recurrent regions** (1 kbp / distinct samples on D1 → 67,763; 1 Mbp / variants on D2 → 2,911):

| Seconds   | PyArrow | Polars | DuckDB | Iceberg     | LanceDB      |
| --------- | ------- | ------ | ------ | ----------- | ------------ |
| Dataset 1 | 1012    | 11.6   | 19.0   | 0.71 + 0.19 | 1.78 + 0.56  |
| Dataset 2 | 35.2    | 10.6   | 2.67   | 1.70 + 0.22 | 30.68 + 6.21 |

<div style="display: flex; gap: 16px; align-items: flex-start;">
  <div style="flex: 1; min-width: 0;">
    <img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/ot7DqOb8NMiOyzTA0001.svg" />
    <p><strong>Figure 3a(<a href="https://lamin.ai/laminlabs/lakehouse-benchmarks/artifact/0Pzx1HBBsf5YsfvT000U">source</a>)</strong>: Dataset 1 query times.</p>
  </div>
  <div style="flex: 1; min-width: 0;">
    <img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/ot7DqOb8NMiOyzTA0002.svg" />
    <p><strong>Figure 3b (<a href="https://lamin.ai/laminlabs/lakehouse-benchmarks/artifact/kBOCwXvajOXJAniJ000W">source</a>)</strong>: Dataset 2 query times.</p>
  </div>
</div>

**Two opposite scaling laws.** For the **in-place** engines, query time tracks the number of files. PyArrow's filtered query runs 1012s on 3,201 files but 7.4s on 26 files (137×), and DuckDB's `SELECT *` over `httpfs` goes from 4.8s to 2,181s (454×) — despite Dataset 1 holding 18× _fewer_ rows. The cost is per-file, full-width fetches, not compute. For the **pre-ingested** formats, the opposite holds: Iceberg and LanceDB pay the file-count penalty once at ingest, and their subsequent queries scale with row count — LanceDB's `query_stats` is 1.8s on 4.86M rows (Dataset 1) but 22.8s on 88M rows (Dataset 2). Polars sits apart: its async S3 reader is remarkably resilient to file count (12s vs 2s), the only in-place engine that stays fast on the many-file layout.

:::{dropdown} Why the number of Parquet files matters

Opening a collection reads one footer per file, and materialising it fetches each file's data. On 3,201 small shards this per-file overhead dominates. The controlled comparison is the filtered query — identical logic on both datasets — where the in-place engines are 100–450× slower on 3,201 files than on 26, even though the many-file dataset has fewer rows. The mechanism differs by engine: PyArrow fetches files largely serially; DuckDB's `httpfs` pays a full-width network round-trip per file for a `SELECT *`; Polars parallelises aggressively and mostly escapes the penalty.

The pre-ingested formats (Iceberg, LanceDB) show the flip side: their query cost tracks rows, not files, because they read from a compacted store — but they pay the full file-count read once, up front, at ingest (~34 min on 3,201 files).

The practical takeaway is a tuning knob independent of engine choice: **compacting many small shards into fewer large ones is often a bigger win than switching engines.**

:::

## Data management

Three write operations were tested: appending a new batch, adding a `QC_PASS` boolean column, and querying a historical state. Code blocks are excerpts; each links to its full, runnable notebook under [Code & data availability](#code--data-availability).

### Appending data

Neither PyArrow nor Polars has an append operation for a sharded dataset — appending is a data-layer operation handled by LaminDB. A new artifact is saved (with a run-scoped key so its content hash is unique per run), then a new collection version is created that revises the original.

::::::{tab-set}
:::::{tab-item} LaminDB

```python
new_art = ln.Artifact.from_dataframe(
    new_sample_df,
    key="lakehouse-benchmarks/new_batch.parquet",
).save()
new_collection = collection.append(new_art)   # returns a new collection version
```

:::::

:::::{tab-item} Iceberg
Atomic and snapshot-isolated. New Parquet files and a snapshot manifest are written to S3; concurrent readers see a consistent state throughout.

```python
table.append(batch)
```

:::::

:::::{tab-item} LanceDB
`add()` writes new rows to S3 and automatically increments the table version.

```python
table.add(batch)
```

:::::
::::::

### Schema evolution

Neither PyArrow nor Polars can write new files with a different schema. For DuckDB the change is session-only — DuckDB is a query engine and cannot persist schema evolution to the source Parquet; making it durable is exactly what DuckLake (or a table format) adds. LaminDB registers the feature in its schema registry, validating all future artifacts instance-wide.

::::::{tab-set}
:::::{tab-item} LaminDB

```python
schema = ln.Schema.get(name="1000 Genomes CNV VCF")
feat = ln.Feature(name="QC_PASS", dtype=bool).save()
schema.add_optional_features([feat])
```

:::::

:::::{tab-item} Iceberg
A new metadata file records the updated schema. Existing Parquet files are not modified; reads of old files return `null` for the new column.

```python
from pyiceberg.types import BooleanType
with table.update_schema() as update:
    update.add_column("QC_PASS", BooleanType())
```

:::::

:::::{tab-item} LanceDB
`add_columns` takes a per-column SQL value expression — hence the `CAST(NULL AS BOOLEAN)` string, which supplies both the value and its type for existing rows.

```python
table.add_columns({"QC_PASS": "CAST(NULL AS BOOLEAN)"})
```

:::::
::::::

(time-travel)=

### Time travel

Neither PyArrow, Polars, nor DuckDB has this capability on its own; DuckLake adds it to the DuckDB ecosystem (see the capability table). LaminDB provides it at the collection level via versions.

::::::{tab-set}
:::::{tab-item} LaminDB

```python
original = db.Collection.get("Lh6IsCOGIl5TOjAj", version="1")   # v1, pre-append
rows_v1 = original.open().count_rows()

current = db.Collection.get("Lh6IsCOGIl5TOjAj0001", version="2")    # v2, post-append
rows_v2 = current.open().count_rows()
```

:::::

:::::{tab-item} Iceberg

```python
first_snapshot = table.history()[0].snapshot_id
historical = table.scan(snapshot_id=first_snapshot).to_arrow()
```

:::::

:::::{tab-item} LanceDB

```python
table.checkout(1)             # version 1 = pre-append state
table.count_rows()
table.checkout_latest()       # restore current version
```

:::::
::::::

### Timing results

Write-path times, both datasets:

| Seconds                   | LaminDb | DuckDB | Iceberg | LanceDB |
| ------------------------- | ------- | ------ | ------- | ------- |
| Append — Dataset 1        | 11.0    | n/a    | 0.85    | 0.11    |
| Append — Dataset 2        | 4.14    | n/a    | 1.10    | 0.32    |
| Schema change — Dataset 1 | 3.6     | n/a    | 0.33    | 0.07    |
| Schema change — Dataset 2 | 3.53    | n/a    | 0.36    | 0.08    |
| Time travel — Dataset 1   | n/a     | n/a    | 0.69    | 0.11    |
| Time travel — Dataset 2   | n/a     | n/a    | 1.64    | 0.11    |

Two observations. The LaminDB-path append is slower on Dataset 1 (~11s) than Dataset 2 (~4s) because creating a new collection version rebuilds the member list — 3,201 artifacts versus 26 — so append cost tracks the number of files in the collection.

<div style="display: flex; gap: 16px; align-items: flex-start;">
  <div style="flex: 1; min-width: 0;">
    <img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/VnVruqKX9KK0uhUw0006.svg" />
    <p><strong>Figure 4a (<a href="https://lamin.ai/laminlabs/lakehouse-benchmarks/artifact/ZtoBlPvxz9zWcZ0M000T">source</a>)</strong>: Dataset 1 write path.</p>
  </div>
  <div style="flex: 1; min-width: 0;">
    <img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/VnVruqKX9KK0uhUw0007.svg" />
    <p><strong>Figure 4b (<a href="https://lamin.ai/laminlabs/lakehouse-benchmarks/artifact/ZtoBlPvxz9zWcZ0M000V">source</a>)</strong>: Dataset 2 write path.</p>
  </div>
</div>

## Developer experience

|                              | PyArrow                                            | Polars                 | DuckDB            | Iceberg                   | LanceDB                      |
| ---------------------------- | -------------------------------------------------- | ---------------------- | ----------------- | ------------------------- | ---------------------------- |
| **Setup**                    | 1 line                                             | 1 line                 | ~15 lines ⁹       | ~20 lines                 | 3 lines                      |
| **Data ingestion required**  | No                                                 | No                     | No                | Yes (copies into Iceberg) | Yes (copies to Lance format) |
| **Native compute**           | Yes (approx. median)                               | Yes                    | Yes               | No (format)               | No (format)                  |
| **Query cost scales with**   | file count                                         | file count (resilient) | file count        | row count (post-ingest)   | row count (post-ingest)      |
| **Append**                   | S3 upload + schema validation + collection version | same as PyArrow        | session-only view | atomic snapshot to S3     | versioned write to S3        |
| **Schema change scope**      | instance-wide registry                             | instance-wide registry | session only †    | this table                | this table                   |
| **Time travel**              | collection versions                                | collection versions    | not supported     | snapshot ID               | version number               |
| **Vector search**            | no                                                 | no                     | no                | no                        | yes                          |
| **Stays in LaminDB lineage** | yes                                                | yes                    | yes               | no (copies out)           | no (copies out)              |

† Not persisted; session-scoped only.
⁹ DuckDB's extra lines are cross-account credential extraction, not query logic.

What LaminDB provides:

**Lineage.** Each pipeline notebook is a tracked transform; the timing results are saved as tracked artifacts; a final `plots.py` reads those five artifacts as registered inputs and writes the comparison figures as registered outputs. The full provenance chain — from the original 1000 Genomes data through to the figures — is recorded in LaminHub.

![Lineage on Lamin Hub](https://lamin-site-assets.s3.amazonaws.com/.lamindb/v7yD8XvBy0eViHGG0001.png)
Link to view lineage: https://lamin.ai/laminlabs/lakehouse-benchmarks/artifact/0Pzx1HBBsf5YsfvT000Q

Note: DuckDB is one exception in the lineage graph — it reads the collection's Parquet files directly via S3 paths rather than through `collection.open()`, so the collection node has no incoming edge from `duckdb_pipeline.ipynb`. Its result artifact is still tracked as an output.

**Schema validation.** A schema registered against a collection validates new artifacts at write time. In the governance demo (PyArrow and Polars pipelines), saving a DataFrame with an unrecognised column against a closed schema raises a `ValidationError` before the data reaches storage.

**Collection versioning.** Each append creates a new collection version; prior versions remain addressable by UID — time travel at the collection level.

**Metadata-queryable collections.** Artifacts carry biological metadata (organism, tissue, disease, experimental factor); collections can be filtered by these fields before any data is opened.

These capabilities are available regardless of which query engine is used.

## Conclusion

The five approaches cover the main strategies for querying Parquet-based genomic data from a LaminDB collection: lazy reads without ingestion (PyArrow, Polars, DuckDB), metadata-layer ingestion (Iceberg), and format-conversion ingestion (LanceDB).

Primary tradeoffs observed across the two layouts:

- **File count, not row count, drives read time — and reader design decides how much.** On the identical filtered query, the in-place engines are 100–450× slower on 3,201 files than on 26, despite the many-file dataset having 18× fewer rows. DuckDB's `httpfs` `SELECT *` is the extreme (4.8s → 2,181s); Polars' async reader is the exception that stays fast.
- **Two scaling laws.** In-place engines pay the file-count cost on every query; pre-ingested formats (Iceberg, LanceDB) pay it once at ingest and then scale with row count. LaminDB's collection-version append also scales with file count (member-list rebuild).
- **Formats aren't compute engines.** Iceberg and LanceDB have no native aggregation; their fast query numbers are a scan of a pre-compacted store plus a DuckDB aggregation.
- **Query conciseness.** DuckDB's SQL is the most concise; PyArrow requires the most machinery (and only an approximate grouped median).
- **Write durability.** DuckDB appends and schema changes are session-scoped; DuckLake is what makes them durable. All other engines write to S3.
- **Lineage.** Only the in-place engines keep the data in LaminDB's lineage graph. Iceberg and LanceDB copy the data into their own store, out of that graph.

Recommendation, conditional: use **Polars** for in-place querying of many-file collections; **DuckDB** for concise SQL on few-file layouts (avoid `httpfs` `SELECT *` on thousands of shards); **Iceberg/LanceDB** when you query the same data repeatedly enough to amortise a one-time ingest; and **compact your shards** before reaching for any of them.

Zooming out: Iceberg, DuckLake, and LaminDB address different layers. Iceberg provides snapshot-isolated ACID transactions with query-engine independence. DuckLake adds concurrent writers and automatic maintenance. LaminDB adds heterogeneous file support, biological metadata, and lineage — and is largely complementary to both.

## Author contributions

Raaghav performed data engineering and analysis. Alex R. wrote the lakehouse ecosystem overview. Ishita curated the 88M-row SNV & Indel dataset. Sunny curated the original CNV datasets. Alex W. and Sergei supervised the project.

## Code & data availability

The five pipeline notebooks, the shared benchmarking utilities, and the plotting script are tracked in the `laminlabs/lakehouse-benchmarks` instance.

- [PyArrow pipeline](https://lamin.ai/laminlabs/lakehouse-benchmarks/transform/D10UPamv70IP)
- [Polars pipeline](https://lamin.ai/laminlabs/lakehouse-benchmarks/transform/2Wdo02w0MDgH)
- [DuckDB pipeline](https://lamin.ai/laminlabs/lakehouse-benchmarks/transform/tQaG9uhSD7BO)
- [Iceberg pipeline](https://lamin.ai/laminlabs/lakehouse-benchmarks/transform/wnVO8cu0qtOP)
- [LanceDB pipeline](https://lamin.ai/laminlabs/lakehouse-benchmarks/transform/WtZF9OX9v3uM)

Dataset 1: 1000 Genomes CNV calls (DRAGEN, hg38), UID `Lh6IsCOGIl5TOjAj`. Dataset 2: 1000 Genomes SNV/Indel/CNV, UID `hVu9puwdRGskm1I6`.

## Methods

All timings are single-run measurements on SageMaker (`ml.m5.24xlarge`) in `store` mode. Versions: `lamindb-core==2.7.0`, `duckdb==1.5.3`, `polars==1.42.0`, `pyiceberg==0.11.1`, `lancedb==0.33.0`, `pandas==2.3.3`, Python 3.12. Query engines (PyArrow, Polars, DuckDB) compute natively; table formats (Iceberg, LanceDB) scan natively and aggregate in DuckDB. PyArrow's grouped median is approximate (t-digest); the others are exact. Because the two datasets differ in schema, Queries 2 and 3 run analogous but not identical analyses (per-sample on Dataset 1, per-chromosome on Dataset 2); the read and filter operations are identical in logic across datasets and carry the file-count comparison. Single-run numbers are point measurements, not distributions.

## How to cite

```
Pillai R, Rasmussen A, Jain I, Sun S, Rybakov S & Wolf A (2026).Polars, DuckDB, Iceberg, LanceDB & LaminDB in queries of the 1000 Genomes Project. Lamin Blog. https://blog.lamin.ai/lakehouse-benchmarks
```

## References

[^apache-iceberg]: Apache Software Foundation. Apache Iceberg: The open table format for analytic datasets. [Apache Iceberg](https://iceberg.apache.org/).

[^ducklake-format]: Raasveldt M & Mühleisen H (2025). DuckLake: SQL as a Lakehouse Format. [DuckLake Blog](https://ducklake.select/2025/05/27/ducklake-01/).

[^ducklake-v1]: Raasveldt M & Holanda P (2026). DuckLake v1.0: The Lakehouse Format Built on SQL Reaches Production-Readiness. [DuckLake Blog](https://ducklake.select/2026/04/13/ducklake-10/).

[^delta]: Linux Foundation. Delta Lake: An open-source storage framework that enables building a Lakehouse architecture. [Delta Lake](https://delta.io/).

[^hudi]: Apache Software Foundation. Apache Hudi: Streaming data on data lakes. [Apache Hudi](https://hudi.apache.org/).

[^nessie]: Project Nessie. Nessie: Transactional Catalog for Data Lakes. [Project Nessie](https://projectnessie.org/).

[^spark]: Apache Software Foundation. Apache Spark: Unified engine for large-scale data analytics. [Apache Spark](https://spark.apache.org/).

[^trino]: Trino Software Foundation. Trino: Fast distributed SQL query engine for big data analytics. [Trino](https://trino.io/).

[^dremio]: Dremio Corporation. Dremio: The Unified Lakehouse Platform. [Dremio](https://www.dremio.com/).

[^pyarrow]: Apache Software Foundation. Apache Arrow: A cross-language development platform for in-memory analytics. [Apache Arrow](https://arrow.apache.org/).

[^polars]: Polars. Polars: Fast multi-threaded, hybrid-streaming DataFrame library. [Polars](https://pola.rs/).

[^duckdb]: DuckDB Foundation. DuckDB: An in-process SQL OLAP database management system. [DuckDB](https://duckdb.org/).
