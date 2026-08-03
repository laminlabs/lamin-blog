---
title: "Agentic variant analysis of the 1000 Genomes Project using Polars, DuckDB, and lakehouses"
date: 2026-08-03
author: Raaghav-Pillai, alexras, ishitajain9717, sunnyosun, Koncopd, falexwolf
affiliation:
  Raaghav-Pillai: Lamin Labs, NYC
  alexras: BitsOnDisk
  ishitajain9717: Lamin Labs, Munich
  sunnyosun: Lamin Labs, Munich
  Koncopd: Lamin Labs, Munich
  falexwolf: Lamin Labs, Munich
db: https://lamin.ai/laminlabs/1000genomes
---

The 1000 Genomes Project sequenced 3201 individuals worldwide to build a comprehensive atlas of human genetic variation.
Here, we discuss how to efficiently analyze 100M+ genomic variants in the age of agents.
We evaluate modern query engines like Polars and DuckDB for streaming these large, distributed datasets, and show how lakehouse frameworks (Iceberg, LanceDB, LaminDB) address the efficiency and integrity problems of letting agents interact directly with raw files.

An atlas like 1000 Genomes[^1000g] serves as a foundational reference for researchers to understand disease-associated mutations and evolutionary history.
Such studies often require querying large amounts of data and are increasingly performed by AI agents leveraging formats such as Parquet.
Several benchmarks show that queries of Parquet files can be up to 1000x faster than querying VCF files, not to mention the advantages of cloud-native access.[^23andme][^azure-genomics][^aws-emr][^boufea2017]
Hence, we transform two collections of VCF files to Parquet files:

<!-- prettier-ignore -->
| # | Pipeline | Variant types | Grouping | Variants | Files | Source | Explore |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **1** | DRAGEN[^dragen] | CNVs | Per-individual | 4.86M | 3201 | [link](https://registry.opendata.aws/ilmn-dragen-1kgp/) | [link](https://lamin.ai/laminlabs/1000genomes/collection/Lh6IsCOGIl5TOjAj) |
| **2** | EMBL SHAPEIT2[^shapeit] | CNVs, SNVs, Indels | Per-chromosome | 88M | 26 | [link](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/release/20130502/) | [link](https://lamin.ai/laminlabs/1000genomes/collection/hVu9puwdRGskm1I6) |

The first collection stores individual-level information—such as the individual's identifier, their specific genotype call, and the length of the structural variant. The second dataset is a population-level catalog of all unique variants, recording the location, type, and both global and population-specific allele frequencies.

## Data access

Modern query engines like Polars[^polars] and DuckDB[^duckdb] vastly outperform classical data access methods, yet these formidable tools are often pointed at raw file storage systems or data lakes.
In these environments, the relevant `.vcf` and `.parquet` files are often buried within massive collections of mixed file types. While AI agents can navigate these storage systems, doing so forces them to waste significant compute and token limits simply finding files and verifying their schemas.
A recent study[^anthropic-agents] demonstrated that agents can fail entirely when accessing data across heterogeneous sources, but succeed when provided with a unified schema or API layer.

### A simple agentic analysis

To illustrate this, we tasked an agent with a simple analysis: determine the number and types of variants in a specific genomic band. This mimics a typical workflow where researchers zoom into a specific genomic region or locus to study local variants, for instance, to identify mutations linked to a specific disease gene or to prepare data for a genome-wide association study (GWAS) focused on a candidate region. If the data was in a single DataFrame `df`, the analysis would look like this using the `polars` Python package:

```python
import polars as pl

# filter variants
chrom = "1"
lo, hi = 150_000_000, 200_000_000
filtered = df.filter(
    (pl.col("chrom") == chrom) & (pl.col("pos") >= lo) & (pl.col("pos") <= hi)
).collect()

# breakdown by variant type, for context
by_type = (
    filtered.group_by("variant_type")
    .agg(pl.len().alias("n"))
    .sort("n", descending=True)
    .collect()
)
```

But it's not. Hence, an agent first needs to find the files, and once it finds them, it needs to investigate whether they have the same schema so that they can be efficiently queried. So, it runs something like this:

```python
# find files with a consistent schema
schemas, valid_filepaths = [], []
for filepath in filepaths:
    schema = pl.scan_parquet(filepath).collect_schema()
    if not schemas or schema == schemas[0]:
        schemas.append(schema)
        valid_filepaths.append(filepath)

# create a dataframe from files with a consistent schema
df = pl.scan_parquet(valid_filepaths)
```

To make it easy for the agent, let's take dataset 2, which is distributed across only 26 files, and not 3200.
Even then, we find that the agent spends many tokens and much time navigating the files.
And this happens despite [the prompt](https://lamin.ai/laminlabs/1000genomes/run/8esUbPUzXhRExQ72) pointing the agent directly to the 26 files to avoid spending tokens on finding those files in the first place (**Figure 1**).

<div style="text-align: center">
<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/TiR6uHs6qULMwaYs0000.svg" width="700" style="padding: 0;"/>
</div>

**Figure 1 ([source](https://lamin.ai/laminlabs/1000genomes/artifact/yExW5sWBJur4riJA))**: Tokens and time required for an agent to analyze variants across a genomic region using Polars on Dataset 2 (26 files). Here is an exemplary [agent run](https://lamin.ai/laminlabs/1000genomes/run/8esUbPUzXhRExQ72) for raw files, and here [is one](https://lamin.ai/laminlabs/1000genomes/run/j2xJseimmBQU4BtC) that leverages the schema contract of the collection.

### A schema contract

How can a lakehouse help? In the context of this problem, a lakehouse does nothing more than ensuring that the 26 files fulfill a schema contract and form one dataset together. In many lakehouse frameworks, this is called a "table", backed by parquet files. In LaminDB, we call it a "Collection". If parquet files are part of a schema-validated collection, an agent can trust that they all have a consistent schema, and it doesn't even need to navigate filepaths. The access pattern looks like this:

```python
import lamindb as ln

# Connect to the database
db = ln.DB("laminlabs/1000genomes")

# Retrieve the collection
collection = db.Collection.get("hVu9puwdRGskm1I6")

# Confirm the schema contract for these files
collection.schema.describe()

# Open the collection as a lazy Polars dataframe
df = collection.open(engine="polars")
```

The schema contract for the 26 parquet files can also be visualized, showing the 12 features computed in the EMBL SHAPEIT2 pipeline[^shapeit] (**Figure 2**).

<div style="text-align: center">
<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/5wVVtCfTQ80ObXEL0000.png" width="1000" style="padding: 0;">
</div>

**Figure 2**: Screenshot of [dataset 2](https://lamin.ai/laminlabs/1000genomes/collection/hVu9puwdRGskm1I6).

The result is an agentic analysis that costs 3x fewer tokens and is 4x faster (**Figure 1**), with [a comparable prompt](https://lamin.ai/laminlabs/1000genomes/run/j2xJseimmBQU4BtC) and the same context. While ensuring efficient data access has a big impact on agentic efficiency and is often equated to "AI-ready data", it's little help if the actual data queries are inefficient. Let's study them!

## Queries

We will be using the popular query engines Polars[^polars], DuckDB[^duckdb], and PyArrow[^pyarrow], all of which handle datasets that don't fit into memory by streaming them directly from storage.

### Simple filter

Let us first look at the simple filter from the analysis above across all three query engines:

::::::{tab-set}
:::::{tab-item} Polars

```python
with collection.open(engine="polars") as df:
    filtered = df.filter(
        (pl.col("CHROM") == chrom) & (pl.col("POS") >= lo) & (pl.col("POS") <= hi)
    ).collect()
```

:::::

:::::{tab-item} DuckDB

To query via DuckDB, we need to register a lazy view over the collection's S3 paths. The source bucket is cross-account (EU), so credentials are extracted from the artifact's own storage session — `PROVIDER credential_chain` does **not** authenticate here. Creating this view takes around 40 sec for dataset 1 and 3 sec for dataset 2. As DuckDB cold reads all 3,201 Parquet files over `httpfs` the query is bottlenecked on 3,201 sequential S3 footer round-trips to locate row groups because of which the filter query is so high.

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

:::::{tab-item} PyArrow

```python
import pyarrow.compute as pc

with colletion.open(engine="pyarrow") as dataset:
    expr = ((pc.field("CHROM") == chrom)
            & (pc.field("POS") >= lo) & (pc.field("POS") <= hi))
    filtered = dataset.to_table(filter=expr)
```

:::::
::::::

### Summary statistics

Profiling summary statistics is a standard exploratory step to assess genetic diversity, establish baselines for rare disease studies, and identify severe structural variations before downstream association studies. Here, we calculate the total CNV count, deletions, median deletion size, and homozygous/heterozygous counts:

::::::{tab-set}
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
::::::

### Recurrent regions

Finding recurrent mutation hotspots helps pinpoint highly mutable regions, functional genomic elements under evolutionary pressure, and common structural variations across populations. To identify these, we bin positions into genomic windows (1 kbp for dataset 1, 1 Mbp for dataset 2) and flag bins containing variants from multiple samples.

::::::{tab-set}
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
::::::

### Timing results

Benchmarking the runtime of these queries reveals two main results (**Figure 3**): Polars is the only query engine that's able to efficiently query the high number of parquet files in dataset 1, albeit still at slower times than for the 20x more rows in dataset 2. Polars yields the fastest queries overall, except for the complicated recurrent region detection in dataset 2, where DuckDB wins.

<div style="display: flex; gap: 16px; align-items: flex-start;">
  <div style="flex: 1; min-width: 0;">
    <img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/P7AElQmpeMjSMtvG0002.svg" />
    <p><strong>Figure 3a (<a href="https://lamin.ai/laminlabs/1000genomes/artifact/OT9cCtNhFmUFiyBm0002">source</a>)</strong>: Dataset 1 query times.</p>
  </div>
  <div style="flex: 1; min-width: 0;">
    <img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/P7AElQmpeMjSMtvG0000.svg" />
    <p><strong>Figure 3b (<a href="https://lamin.ai/laminlabs/1000genomes/artifact/OT9cCtNhFmUFiyBm0001">source</a>)</strong>: Dataset 2 query times.</p>
  </div>
</div>

## Data management

Working with a high number of VCF and parquet files from different sources can easily lead to non-robust and obscure data organization, in particular given agents who almost always just focus on solving the task at hand, rather than optimizing for long-term maintainability. Concurrent and frequent access and write patterns make a purely file-based architecture brittle, too.

The lakehouse, which has been the leading data architecture for tabular data in R&D, solves these problems. Today's most popular lakehouse framework is **Iceberg**.[^apache-iceberg] Like the comparable Delta Lake[^delta][^databricks] and Apache Hudi,[^hudi] Iceberg is a table format that organizes datasets into snapshots — each a collection of parquet files plus manifest files that track which files belong to which snapshot. A metadata file describes the table's schema and points to the current snapshot. When writing to an Iceberg table, a new snapshot is created and the metadata updated to point to that new snapshot.

### Frameworks

<figure style="float: right; width: 400px; margin-left: 0.5rem">
  <img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/OgVhDACCMhzGKC4t0001.svg" />
  <strong>Figure 4.</strong> File layout of an Iceberg table.
</figure>

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

¹ LaminDB [guarantees data ↔ metadata consistency through ACID operations](https://docs.lamin.ai/acid), but does not guarantee row-level ACID operations the way Iceberg and DuckLake do. Because you can map an insert into a collection of parquet files via `lamindb.Collection.append()` in an ACID way, the practical robustness guarantee to the user is similar.

² See the [Time travel](#time-travel) section.

³ Adding a nullable/optional column without rewriting existing files.

⁴ In LaminDB, via branches (stage, review, merge).

⁵ Raw files have no commit protocol; concurrent writers risk partial writes / last-writer-wins.

⁶ No need for cleaning orphaned files like in Iceberg.

:::

</div>

An approach that gains popularity in addressing Iceberg's limitations is **DuckLake**,[^ducklake-format][^ducklake-v1] developed by the DuckDB team. Rather than storing metadata in files, DuckLake keeps all metadata in a relational database, leaving only parquet files in storage. This gives it cheap writes that can be more frequent, transactions with true concurrent writer support, automatic maintenance via the database's native mechanisms, and native multi-table transactions — all things that are difficult or impossible with Iceberg's file-based metadata.

Unlike Iceberg and DuckLake, **LaminDB** goes beyond tables and supports datasets across any storage format - parquet, AnnData, HDF5, zarr, VCF, …. The user can manage anything from blobs in a data lake to structured datasets with multiple components based on a single schema concept. LaminDB shares DuckLake's architectural design — a relational database for metadata and storage for data — and natively provides data lineage (**Table 1**).

While Iceberg & DuckLake are based on the parquet format, and LaminDB is format-agnostic, **LanceDB** manages datasets in the Lance format, a columnar format inspired by parquet that's optimized for arrays.[^lancedb-format] To use LanceDB, you need to convert your data into the Lance format.
While LanceDB fits the lakehouse architecture, non-lakehouse architectures for managing array-like data exist, too, in particular, `arraylake` & `tensorstore` for `.zarr` arrays, and `tiledb` for `.tiledb` arrays.[^tiledb] These non-lakehouse technologies are out of scope for this post given the established query engines don't apply to them.

Today a new generation of readers can even efficiently query raw `.vcf` files directly,[^biodatageeks] albeit without the advantages of cloud nativeness and a much broader big data ecosystem.

Let us now review the code for different operations.

### Append rows

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

### Add columns

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

## Code & data availability

The five central notebooks, the shared benchmarking utilities, and the plotting script are available in the `laminlabs/1000genomes` database.

- [PyArrow](https://lamin.ai/laminlabs/1000genomes/transform/D10UPamv70IP)
- [Polars](https://lamin.ai/laminlabs/1000genomes/transform/2Wdo02w0MDgH)
- [DuckDB](https://lamin.ai/laminlabs/1000genomes/transform/tQaG9uhSD7BO)
- [Iceberg](https://lamin.ai/laminlabs/1000genomes/transform/wnVO8cu0qtOP)
- [LanceDB](https://lamin.ai/laminlabs/1000genomes/transform/WtZF9OX9v3uM)

Dataset 1: 1000 Genomes CNV calls (DRAGEN, hg38), UID `Lh6IsCOGIl5TOjAj`. Dataset 2: 1000 Genomes SNV/Indel/CNV, UID `hVu9puwdRGskm1I6`.

## Methods

### Dataset curation

**Dataset 1 ([lineage](https://lamin.ai/laminlabs/1000genomes/collection/Lh6IsCOGIl5TOjAj)):** The 1000 Genomes Project datasets were sourced from the Registry of Open Data on AWS, specifically the DRAGEN v3.7.6 reanalysis (`s3://1000genomes-dragen`). For Dataset 1, we read the `.cnv.vcf.gz` files directly from the S3 bucket into memory using `pysam`, flattened the VCF records (including nested `INFO` and `FORMAT` fields) into a tabular structure, and saved them to LaminDB as partitioned Parquet files (`.cnv.parquet`). You can trace the run [here](https://lamin.ai/laminlabs/1000genomes/run/e1XtEb7mHnh8MoVj).

Note that while the full high-coverage expanded cohort of the 1000 Genomes Project contains 3,202 individuals, the DRAGEN `hg38` reanalysis we pulled from contains exactly 3,201 files. This is because one sample (NA18498) from the original Phase 3 release was excluded during the re-alignment to the GRCh38 reference genome, a common occurrence in genomics due to relatedness discoveries or quality control thresholds.

**Dataset 2 ([lineage](https://lamin.ai/laminlabs/1000genomes/collection/hVu9puwdRGskm1I6)):** The Phase 3 release of the 1000 Genomes Project is one of the most comprehensive dataset from the original project, comprising whole-genome and exome sequencing data from 2,504 individuals across 26 populations spanning 5 continental populations (AFR, AMR, EAS, EUR, SAS). Variant calls are provided as VCF files, split per chromosome, with the standard naming convention. Each field in the filename encodes one step of the pipeline, in order — `ALL` (cohort) → `chr<N>` (which chromosome the file covers) → `phase3` (release/call-set version) → `shapeit2_mvncall_integrated` (methods used, in the order applied: `MVNCall` integrates calls, then `SHAPEIT2` phases them) → `20130502` (release date, YYYYMMDD).

### Query timings

All timings are single-run measurements on SageMaker (`ml.m5.24xlarge`) in `store` mode. Versions: `lamindb-core==2.7.0`, `duckdb==1.5.3`, `polars==1.42.0`, `pyiceberg==0.11.1`, `lancedb==0.33.0`, `pandas==2.3.3`, Python 3.12. Query engines (PyArrow, Polars, DuckDB) compute natively; table formats (Iceberg, LanceDB) scan natively and aggregate in DuckDB. PyArrow's grouped median is approximate (t-digest); the others are exact. Because the two datasets differ in schema, Queries 2 and 3 run analogous but not identical analyses (per-sample on Dataset 1, per-chromosome on Dataset 2); the read and filter operations are identical in logic across datasets and carry the file-count comparison. Single-run numbers are point measurements, not distributions.

### Querying Iceberg & LanceDB

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
    <img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/l0Fq8SDUjudi7SCz0004.svg" />
    <p><strong>Figure 5a (<a href="https://lamin.ai/laminlabs/1000genomes/artifact/T2hvcgmzjlMPFNCQ0003">source</a>)</strong>: Dataset 1 query times.</p>
  </div>
  <div style="flex: 1; min-width: 0;">
    <img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/l0Fq8SDUjudi7SCz0002.svg" />
    <p><strong>Figure 5b (<a href="https://lamin.ai/laminlabs/1000genomes/artifact/T2hvcgmzjlMPFNCQ0004">source</a>)</strong>: Dataset 2 query times.</p>
  </div>
</div>

## How to cite

```
Pillai R, Rasmussen A, Jain I, Sun S, Rybakov S & Wolf A (2026). Agentic variant analysis of the 1000 Genomes Project using Polars, DuckDB, and lakehouses. Lamin Blog. https://blog.lamin.ai/1000genomes
```

## Author contributions

Raaghav performed data engineering and analysis. Alex Rasmussen wrote the lakehouse ecosystem overview. Ishita curated the 88M-row SNV & Indel dataset. Sunny created the original CNV dataset based on `DRAGEN` and the basic CNV analysis flow. Sergei helped supervise the project and created the `polars` and `pyarrow` integrations in `lamindb`. Alex Wolf supervised the project.

## References

[^apache-iceberg]: Apache Software Foundation. Apache Iceberg: The open table format for analytic datasets. [Apache Iceberg](https://iceberg.apache.org/).

[^ducklake-format]: Raasveldt M & Mühleisen H (2025). DuckLake: SQL as a Lakehouse Format. [DuckLake Blog](https://ducklake.select/2025/05/27/ducklake-01/).

[^ducklake-v1]: Raasveldt M & Holanda P (2026). DuckLake v1.0: The Lakehouse Format Built on SQL Reaches Production-Readiness. [DuckLake Blog](https://ducklake.select/2026/04/13/ducklake-10/).

[^delta]: Linux Foundation. Delta Lake: An open-source storage framework that enables building a Lakehouse architecture. [Delta Lake](https://delta.io/).

[^hudi]: Apache Software Foundation. Apache Hudi: Streaming data on data lakes. [Apache Hudi](https://hudi.apache.org/).

[^nessie]: Project Nessie. Nessie: Transactional Catalog for Data Lakes. [Project Nessie](https://projectnessie.org/).

[^pyarrow]: Apache Software Foundation. Apache Arrow: A cross-language development platform for in-memory analytics. [Apache Arrow](https://arrow.apache.org/).

[^polars]: Polars. Polars: Fast multi-threaded, hybrid-streaming DataFrame library. [Polars](https://pola.rs/).

[^duckdb]: DuckDB Foundation. DuckDB: An in-process SQL OLAP database management system. [DuckDB](https://duckdb.org/).

[^1000g]: 1000 Genomes Project Consortium (2015). A global reference for human genetic variation. Nature, 526(7571), 68-74. [doi:10.1038/nature15393](https://doi.org/10.1038/nature15393).

[^shapeit]: Delaneau O et al. (2014). Integrating sequence and array data to create an improved 1000 Genomes Project haplotype reference panel. Nature Communications, 5(1), 3934. [doi:10.1038/ncomms4934](https://doi.org/10.1038/ncomms4934).

[^anthropic-agents]: Luebbert L et al. (2026). Paving the way for agents in biology. [Anthropic Research](https://www.anthropic.com/research/agents-in-biology).

[^databricks]: Databricks (2020). Accurately Building Genomic Cohorts at Scale with Delta Lake and Spark. [Databricks Blog](https://www.databricks.com/blog/2020/09/22/accurately-building-genomic-cohorts-at-scale-with-delta-lake-and-spark.html).

[^biodatageeks]: BioDataGeeks (2025). Benchmarking genomic format readers in Python with Polars. [BioDataGeeks Blog](https://biodatageeks.org/polars-bio/blog/2026/02/14/benchmarking-genomic-format-readers-in-python-with-polars/).

[^lancedb-format]: LanceDB (2024). Lance Format v2.2 Benchmarks: Half the storage, none of the slowdown. [LanceDB Blog](https://lancedb.com/blog/lance-format-v2-2-benchmarks-half-the-storage-none-of-the-slowdown).

[^tiledb]: TileDB (2020). Population Genomics Data with TileDB. [TileDB Blog](https://tiledb.com/blog/population-genomics-data-with-tiledb).

[^23andme]: 23andMe Engineering (2018). Genetic datastore using AWS S3, Parquet, Arrow. [Medium](https://medium.com/23andme-engineering/genetic-datastore-4b213256db31).

[^azure-genomics]: Microsoft (2021). Genomic data in Parquet format on Azure. [Azure Blog](https://techcommunity.microsoft.com/blog/healthcareandlifesciencesblog/genomic-data-in-parquet-format-on-azure/3150554).

[^aws-emr]: AWS (2020). Build a genomics data lake on AWS using Amazon EMR. [AWS Blog](https://aws.amazon.com/blogs/industries/build-a-genomics-data-lake-on-aws-using-amazon-emr-part-1/).

[^boufea2017]: Boufea K & Athanasiadis IN (2017). Managing Variant Calling Files the Big Data Way. [doi:10.1145/3148055.3148060](https://doi.org/10.1145/3148055.3148060).

[^dragen]: Illumina (2021). 1000 Genomes Phase 3 Reanalysis with DRAGEN. [Registry of Open Data on AWS](https://registry.opendata.aws/ilmn-dragen-1kgp/).
