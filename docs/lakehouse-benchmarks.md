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

The 1000 Genomes Project sequenced ~3200 individuals worldwide to build a comprehensive atlas of human genetic variation.
We will show how Polars and DuckDB help to efficiently query the atlas across 93M genomic variants, and how lakehouse frameworks, including Iceberg, LanceDB, and LaminDB, can be used to manage the underlying datasets.

We want to analyze the tabular datasets of the 1000 Genomes Project,[^1000g] which record human genetic variants observed in the raw genome sequences. These variants include Copy Number Variants (CNVs), Single Nucleotide Variants (SNVs), and small insertions/deletions (Indels). In one dataset, we look at CNVs called for each individual. Because CNVs are relatively rare per person, this dataset totals only 4.86M rows across 3201 files (one file per person). In a second dataset, we look at a population-level catalog of all unique variants — CNVs, SNVs, and Indels. Grouping this data by chromosome yields 26 files with 88M total rows. We transformed raw VCF files to parquet files to make use of popular query engines like PyArrow,[^pyarrow] Polars,[^polars], and DuckDB.[^duckdb]

| #     | Observations       | File grouping  | Rows  | Files | Example columns                          | Explore                                                                                           |
| ----- | ------------------ | -------------- | ----- | ----- | ---------------------------------------- | ------------------------------------------------------------------------------------------------- |
| **1** | CNVs               | Per-individual | 4.86M | 3201  | `SAMPLE_NAME`, `SAMPLE_GT`, `INFO_SVLEN` | [`Lh6IsCOGIl5TOjAj`](https://lamin.ai/laminlabs/lakehouse-benchmarks/collection/Lh6IsCOGIl5TOjAj) |
| **2** | CNVs, SNVs, Indels | Per-chromosome | 88M   | 26    | `chrom`, `variant_type`, `af`, `eur_af`  | [`hVu9puwdRGskm1I6`](https://lamin.ai/laminlabs/lakehouse-benchmarks/collection/hVu9puwdRGskm1I6) |

## Queries

We'll be looking at queries that are part of a typical CNV analysis. You can access the two datasets programmatically as a collection of parquet files:

```python
import lamindb as ln

db = ln.DB("laminlabs/lakehouse-benchmarks")
collection = db.Collection.get("Lh6IsCOGIl5TOjAj")  # hVu9puwdRGskm1I6 for dataset 2
```

**Query 1: Filter by chromosome and position.** Query 1 filters variants on the most prevalent chromosome within the 10th–90th percentile position band, returning 321,894 variants for dataset 1 and 5,665,280 variants for dataset 2.

::::::{tab-set}
:::::{tab-item} PyArrow

```python
import pyarrow.compute as pc

with colletion.open(engine="pyarrow") as dataset:
    expr = ((pc.field("CHROM") == chrom)
            & (pc.field("POS") >= lo) & (pc.field("POS") <= hi))
    filtered = dataset.to_table(filter=expr)
```

:::::

:::::{tab-item} Polars

```python
with colletion.open(engine="polars") as df:
    filtered = df.filter(
        (pl.col("CHROM") == chrom) & (pl.col("POS") >= lo) & (pl.col("POS") <= hi)
    ).collect()
```

:::::

:::::{tab-item} DuckDB

To query via DuckDB, we need to register a lazy view over the collection's S3 paths. The source bucket is cross-account (EU), so credentials are extracted from the artifact's own storage session — `PROVIDER credential_chain` does **not** authenticate here. Creating this view takes around 40 sec for dataset 1 and 3 sec for dataset 2.

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

The actual query is then:

```python
filtered = con.execute(
    "SELECT * FROM cnv_vcf WHERE CHROM = ? AND POS BETWEEN ? AND ?",
    [chrom, lo, hi],
).df()
```

:::::
::::::

**Query 2: Calculate summary statistics.** Calculate the total CNV count, deletions, median deletion size, and homozygous/heterozygous counts.

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
    df.group_by("SAMPLE_NAME").agg(
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
::::::

**Query 3: recurrent region detection.** Dataset 1 bins positions into 1 kbp windows and flags bins with CNVs from ≥2 distinct samples (67,763 regions). Dataset 2 bins into 1 Mbp windows and flags bins with ≥2 variants (2,911 regions).

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
    df.with_columns(
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
::::::

<div style="display: flex; gap: 16px; align-items: flex-start;">
  <div style="flex: 1; min-width: 0;">
    <img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/P7AElQmpeMjSMtvG0001.svg" />
    <p><strong>Figure 2a (<a href="https://lamin.ai/laminlabs/lakehouse-benchmarks/artifact/OT9cCtNhFmUFiyBm0002">source</a>)</strong>: Dataset 1 query times.</p>
  </div>
  <div style="flex: 1; min-width: 0;">
    <img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/P7AElQmpeMjSMtvG0000.svg" />
    <p><strong>Figure 2b (<a href="https://lamin.ai/laminlabs/lakehouse-benchmarks/artifact/OT9cCtNhFmUFiyBm0001">source</a>)</strong>: Dataset 2 query times.</p>
  </div>
</div>

Running these queries reveals two main results (**Figure 2**): Polars is the only query engine that's able to efficiently query a large number of parquet files in dataset 1, albeit still at slower times than for the 20x more rows in dataset 2. Polars yields the fastest queries overall, except for the complicated recurrent region detection in dataset 2, where DuckDB wins.

## Data management

Today's most popular lakehouse framework is **Iceberg**.[^apache-iceberg]
Like the comparable Delta Lake[^delta] and Apache Hudi,[^hudi] Iceberg is a table format that organizes datasets into snapshots — each a collection of parquet files plus manifest files that track which files belong to which snapshot. A metadata file describes the table's schema and points to the current snapshot. When writing to an Iceberg table, a new snapshot is created and the metadata updated to point to that new snapshot.

Iceberg provides [ACID transactions](https://en.wikipedia.org/wiki/ACID), "time travel" to previous versions, schema evolution, write-audit-publish workflows, and query engine flexibility. However, its snapshot model introduces costs: expensive creation dictates large, infrequent writes, optimistic concurrency causes simultaneous writers to collide, and orphaned files require manual garbage collection. Additionally, S3 requires an external catalog (like Nessie,[^nessie] AWS Glue, or Unity Catalog) or an external lock to coordinate metadata updates.

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
| Registries/ontologies                    | ❌     | ❌      | ❌       | ✅      |

:::{dropdown} **Table 1.** A high-level overview of lakehouse technologies.

¹ LaminDB [guarantees data ↔ metadata consistency through ACID operations](https://docs.lamin.ai/faq/acid.md), but does not guarantee row-level ACID operations the way Iceberg and DuckLake do. Because you can map an insert into a collection of parquet files via `lamindb.Collection.append()` in an ACID way, the practical robustness guarantee to the user is similar.

² See the [Time travel](#time-travel) section.

³ Adding a nullable/optional column without rewriting existing files.

⁴ In LaminDB, via branches (stage, review, merge).

⁵ Raw files have no commit protocol; concurrent writers risk partial writes / last-writer-wins.

⁶ No need for cleaning orphaned files like in Iceberg.

:::

</div>

An approach that gains popularity in addressing Iceberg's limitations is **DuckLake**,[^ducklake-format][^ducklake-v1] developed by the DuckDB team. Rather than storing metadata in files, DuckLake keeps all metadata in a relational database, leaving only parquet files in storage. This gives it cheap writes that can be more frequent, transactions with true concurrent writer support, automatic maintenance via the database's native mechanisms, and native multi-table transactions — all things that are difficult or impossible with Iceberg's file-based metadata.

Unlike Iceberg and DuckLake, **LaminDB** goes beyond tables and supports datasets across any storage format - parquet, AnnData, HDF5, zarr, VCF, …. The user can manage anything from blobs in a data lake to structured datasets with multiple array components using a single composite schema concept. LaminDB shares DuckLake's architectural design — a relational database for metadata and storage for data — and natively provides data lineage (**Table 1**).

While Iceberg & DuckLake are based on the parquet format, and LaminDB is format-agnostic, **LanceDB** manages datasets in the Lance format, a columnar format inspired by parquet that's optimized for arrays. To use LanceDB, you need to convert your data into the Lance format.
While LanceDB fits the lakehouse architecture, non-lakehouse architectures for managing array-like data exist, too, in particulary, `arraylake` & `tensorstore` for `.zarr` arrays, and `tiledb` for `.tiledb` arrays. These non-lakehouse technologies are out of scope for this post given the established query engines don't apply to them.

### Appending data

::::::{tab-set}
:::::{tab-item} Iceberg
Atomic and snapshot-isolated. New Parquet files and a snapshot manifest are written to S3; concurrent readers see a consistent state throughout.

```python
table.append(batch)  # batch is a pyarrow dataset
```

:::::

:::::{tab-item} LanceDB
`add()` writes new rows to S3 and automatically increments the table version.

```python
table.add(batch)  # batch is a pyarrow dataset
```

:::::

:::::{tab-item} LaminDB
Atomic and snapshot-isolated. A new parquet file creates a new collection version.

```python
collection.append(batch)  # batch is an artifact
```

:::::
::::::

### Add a column

::::::{tab-set}

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

:::::{tab-item} LaminDB
LaminDB registers the feature in its schema registry, validating all future artifacts instance-wide.

```python
feature = ln.Feature(name="QC_PASS", dtype=bool).save()
collection.schema.add(feature)
```

:::::
::::::

(time-travel)=

### Time travel

::::::{tab-set}

:::::{tab-item} Iceberg

```python
first_snapshot = table.history()[0].snapshot_id  # access version 0
table.scan(snapshot_id=first_snapshot)
```

:::::

:::::{tab-item} LanceDB

```python
table.checkout(1)             # checkout a previous version
```

:::::

:::::{tab-item} LaminDB

```python
collection.versions.get(version="1")  # get a previous version
```

:::::
::::::

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

## Appendix

### Querying the Iceberg & LanceDB formats

This section demonstrates that there isn't a noteworthy difference in querying parquet files, the Iceberg, or the LanceDB format. To study the latter, we have to convert parquet files into the Iceberg and LanceDB table formats.

::::::{tab-set}

:::::{tab-item} Iceberg

```python
from pyiceberg.catalog.sql import SqlCatalog

arrow = collection.open().to_table()
catalog = SqlCatalog("local", uri="sqlite:///iceberg_catalog.db", warehouse=WAREHOUSE)
catalog.create_namespace("genomics")
table = catalog.create_table("genomics.cnv_vcf", schema=arrow.schema)
table.append(arrow)
```

:::::

:::::{tab-item} LanceDB

```python
import lancedb

arrow = collection.open().to_table()
db = lancedb.connect(WAREHOUSE)
table = db.create_table("cnv_vcf", data=arrow, mode="overwrite")
```

:::::
::::::

The timing results for format conversion are dominated by the conversion to a PyArrow dataset, and take substantially longer for LanceDB than for Iceberg for the larger dataset 2.

| Operation | Dataset | Iceberg (sec) | LanceDB (sec) |
| --------- | ------- | ------------- | ------------- |
| Read      | 1       | 2043          | 2045          |
| Read      | 2       | 43            | 45.2          |
| Ingest    | 1       | 6             | 7             |
| Ingest    | 2       | 5.7           | 109           |

**Query 1.** Because the format conversion implies a much lower number of files for Iceberg and LanceDB, we're also converting the original parquet files to a single parquet file, so that we're not biasing performance of Query 1 due to the high number of files.

::::::{tab-set}

:::::{tab-item} DuckDB

```python
path = db.Artifact.get(key="benchmark/dragen_cnv.parquet").path.as_posix()
duckdb.sql(f"""
    SELECT "Chromosome", count(*) AS n_calls
    FROM read_parquet('{path}')
    WHERE "QUAL" >= 30
    GROUP BY "Chromosome"
    ORDER BY n_calls DESC
""").show()
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

**Query 2 & 3.** Both of these queries cannot be natively run via `pyiceberg` or `lancedb`. Hence, we're timing results for a DuckDB-based query after converting back from `pyarrow`.

::::::{tab-set}
:::::{tab-item} DuckDB + Iceberg

```python
# Iceberg is a table format, not a compute engine: native scan, then aggregate in DuckDB.
arrow = table.scan().to_arrow()
stats = compute_duckdb(arrow, SQL_EXPRESSION)
```

:::::

:::::{tab-item} DuckDB + LanceDB

```python
arrow = table.to_arrow()
stats = compute_duckdb(arrow, SQL_EXPRESSION)
```

:::::
::::::

:::{dropdown} How is compute_duckdb processing information

```python
def compute_duckdb(arrow_table, sql):
    """Format already scanned natively; run the standard aggregation in DuckDB."""
    con = duckdb.connect()
    con.register("t", arrow_table)
    return con.execute(sql.format(src="t")).df()
```

:::

<div style="display: flex; gap: 16px; align-items: flex-start;">
  <div style="flex: 1; min-width: 0;">
    <img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/l0Fq8SDUjudi7SCz0003.svg" />
    <p><strong>Figure 4a (<a href="https://lamin.ai/laminlabs/lakehouse-benchmarks/artifact/T2hvcgmzjlMPFNCQ0003">source</a>)</strong>: Dataset 1 query times.</p>
  </div>
  <div style="flex: 1; min-width: 0;">
    <img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/l0Fq8SDUjudi7SCz0002.svg" />
    <p><strong>Figure 4b (<a href="https://lamin.ai/laminlabs/lakehouse-benchmarks/artifact/T2hvcgmzjlMPFNCQ0004">source</a>)</strong>: Dataset 2 query times.</p>
  </div>
</div>

## Methods

### Dataset curation

**Dataset 1.** The 1000 Genomes Project datasets were sourced from the Registry of Open Data on AWS, specifically the DRAGEN v3.7.6 reanalysis (`s3://1000genomes-dragen`). For Dataset 1, we read the `.cnv.vcf.gz` files directly from the S3 bucket into memory using `pysam`, flattened the VCF records (including nested `INFO` and `FORMAT` fields) into a tabular structure, and saved them to LaminDB as partitioned Parquet files (`.cnv.parquet`). You can trace the run [here](https://lamin.ai/laminlabs/lakehouse-benchmarks/run/e1XtEb7mHnh8MoVj).

Note that while the full high-coverage expanded cohort of the 1000 Genomes Project contains 3,202 individuals, the DRAGEN `hg38` reanalysis we pulled from contains exactly 3,201 files. This is because one sample (NA18498) from the original Phase 3 release was excluded during the re-alignment to the GRCh38 reference genome, a common occurrence in genomics due to relatedness discoveries or quality control thresholds.

### Benchmarks

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

[^1000g]: 1000 Genomes Project Consortium (2015). A global reference for human genetic variation. Nature, 526(7571), 68-74. [doi:10.1038/nature15393](https://doi.org/10.1038/nature15393).
