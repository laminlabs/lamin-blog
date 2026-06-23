# Four ways to query a LaminDB collection: a developer-experience comparison of PyArrow, DuckDB, Iceberg, and LanceDB

Working with genomic copy-number variant (CNV) calls means querying tabular data that's split across many Parquet files. We took a LaminDB collection of 1000 Genomes CNV calls — 8,929 rows across six DRAGEN Parquet shards — and worked through the same user journey with four different query engines: vanilla PyArrow, DuckDB, Apache Iceberg, and LanceDB. The journey covers accessing the data, computing per-sample statistics, running a filtered point query, appending a new sample, and evolving the schema. We compare the developer experience of each, and find that the query layer is largely interchangeable — while LaminDB's contribution sits underneath all four: lineage, schema validation, and versioning, available no matter which engine you choose.

## The problem

The starting point is deliberately modest: we want to query roughly 8,900 rows of CNV calls stored across six Parquet files, each file holding around 1,500 rows. This is a realistic shape for genomics — a dataset arrives as a handful of shards (here, one DRAGEN output per batch of samples), and you want to treat them as a single logical table without first stitching them together by hand.

On top of that table, a working biologist or data scientist runs a recurring set of operations. We picked five that together make up a typical user journey:

1. **Access** — connect to the data and get a queryable handle.
2. **Query** — compute per-sample CNV statistics, and identify recurrent regions where variants appear across multiple samples.
3. **Filtered query** — a point query on a chromosome and position range.
4. **Append** — add a new sample to the dataset.
5. **Evolve schema** — add a new column (here, a `QC_PASS` flag).

The question we set out to answer wasn't "which engine is fastest" — on 8,900 rows, nothing is slow. It was "what is it actually like to do this work, and what does the data infrastructure underneath give you?"

## One collection, four engines

All four engines read from the same LaminDB collection, and the data never leaves LaminDB. Getting a handle to it is a single line:

```python
import lamindb as ln
collection = ln.Collection.get("K6X8Ejk3fjgAZT6h0000")  # 1000 Genomes CNV calls
```

From here the four engines diverge. Two of them — PyArrow and DuckDB — read the Parquet files in place, with no copy step. The other two — Iceberg and LanceDB — wrap or rewrite the data into their own on-disk format first. That single distinction turns out to explain most of what differs between them.

## The four approaches

From the same collection handle, here is how each engine gets you to queryable data and handles the journey. Pick a tab to read that engine's full walkthrough.

<!-- Tabs use MyST / sphinx-design colon-fence syntax (::::{tab-set} / :::{tab-item}), matching the rest of the Lamin blog. -->

::::::{tab-set}
:::::{tab-item} Vanilla PyArrow
The most direct way to query the collection is to open it as a PyArrow dataset and compute in pandas. There is no setup, no catalog, and no ingestion:

```python
dataset = collection.open()          # a PyArrow dataset over the Parquet shards
df = dataset.to_table().to_pandas()  # materialize once
```

Per-sample statistics and recurrent-region detection are then ordinary pandas — a `groupby` over sample names, and a binning-and-counting pass over genomic position. A filtered query is either a PyArrow predicate pushed down to the Parquet row groups, or a pandas mask over the in-memory frame.

We want to be precise about what this path is, because it's the crux of the whole comparison. This is **not a LaminDB query engine** — LaminDB doesn't have one. It's PyArrow doing the reading and pandas doing the compute. LaminDB's role here is to hand you the collection and open it as a dataset; everything after that is the standard scientific-Python stack. Labeling this path "LaminDB" would suggest Lamin competes with DuckDB on query execution, which misrepresents what it does. So we call it **Vanilla PyArrow** — and we'll return to why that framing matters.
:::::

:::::{tab-item} DuckDB
DuckDB puts a SQL layer directly on the Parquet files in S3, read in place via `httpfs`. There's no ingestion step — it registers a view over the files and reads them on demand:

```python
import duckdb
con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs;")
s3_paths = [str(a.path) for a in collection.ordered_artifacts.all()]
con.execute(f"CREATE OR REPLACE VIEW cnv_vcf AS SELECT * FROM read_parquet({s3_paths})")
```

For anyone who thinks in SQL, this is the most comfortable of the four. The full per-sample statistics collapse into a single `GROUP BY` with `FILTER` clauses, and the filtered query uses predicate pushdown to read only the relevant row groups. Appending a sample and evolving the schema are both view redefinitions — instant, but ephemeral: they live only in the session and aren't persisted anywhere.

DuckDB's standout is cross-file SQL. Because each Parquet shard can be exposed as its own view and unioned in a single query, comparing or joining across the shards is concise, and it scales from one file to a thousand without changing shape.
:::::

:::::{tab-item} Iceberg
Iceberg wraps the Parquet files in a metadata layer managed by a catalog. Rather than reading files directly, it records them in a table whose schema, snapshots, and file manifests live in metadata files alongside the data:

```python
from pyiceberg.catalog.sql import SqlCatalog
catalog = SqlCatalog("local", uri="sqlite:///iceberg_catalog.db", warehouse=WAREHOUSE)
catalog.create_namespace("genomics")
table = catalog.create_table("genomics.cnv_vcf", schema=arrow.schema)
table.overwrite(arrow)
```

This is the heaviest setup of the four — a catalog, a namespace, table registration, and an ingest step — but it buys the strongest write guarantees. Appends are atomic and snapshot-isolated, so concurrent readers always see a consistent state. Time travel lets you query any historical snapshot by ID. And schema evolution adds, renames, or reorders columns by writing a new metadata file, without rewriting any of the underlying Parquet.

The cost shows up in what Iceberg writes to storage. A single logical table is a tree of metadata, manifest, and data files:

<!-- SCREENSHOT: Iceberg file layout on S3 — the metadata/, manifest, and data/ structure under genomics/cnv_vcf/. Drop the screenshot here. -->
![Iceberg file layout on S3: a single table is a tree of metadata files, manifest lists, and Parquet data files](images/iceberg-file-layout.png)

That structure is exactly what powers atomic appends and time travel — each write produces a new metadata file and snapshot, leaving prior ones intact — but it's also why Iceberg has the most moving parts of the four.
:::::

:::::{tab-item} LanceDB
LanceDB is the only engine that copies the data out of Parquet and into its own columnar format. Unlike the other three, this is a genuine write step:

```python
import lancedb
db = lancedb.connect(WAREHOUSE)
table = db.create_table("cnv_vcf", data=arrow, mode="overwrite")
```

Once ingested, querying is the PyArrow/pandas API or SQL through Lance's built-in DuckDB integration. Every `add()` automatically creates a new version, and time travel checks out a previous version by number. Its distinguishing capability is native vector search with approximate-nearest-neighbor indexing — relevant if your CNV regions carry sequence or phenotype embeddings, though not exercised by this particular journey.

The tradeoff is the ingest tax. Because the data is copied into Lance format, it lives outside LaminDB's lineage graph once written — you've forked a second copy whose provenance LaminDB no longer tracks.
:::::
::::::

## Side by side: one query, four engines

The walkthroughs above read engine-first. It's worth flipping the axis and putting a *single* operation in front of all four at once — the clearest way to see that the query layer is interchangeable. Here is the filtered query — find every variant on `chr1` within a position range — written for each. All four return the same 589 variants from the same underlying Parquet; only the syntax changes.

::::::{tab-set}
:::::{tab-item} Vanilla PyArrow
```python
import pyarrow.compute as pc

expr = ((pc.field("CHROM") == chrom)
        & (pc.field("POS") >= lo) & (pc.field("POS") <= hi))
filtered = dataset.to_table(filter=expr)   # predicate pushed into the Parquet scan
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

row_filter = And(
    EqualTo("CHROM", chrom),
    And(GreaterThanOrEqual("POS", lo), LessThanOrEqual("POS", hi)),
)
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

Four engines, four syntaxes, one result. DuckDB and LanceDB express the predicate in SQL, PyArrow and Iceberg in their respective expression APIs, but each pushes the filter down to skip the rows it doesn't need — and each is reading the same data, reached through the same LaminDB collection. The choice between them is ergonomic, not architectural.

## Developer experience compared

Across the five operations, the engines sort into a clear pattern. The table below summarizes the qualities that actually differed in practice:

| | Vanilla PyArrow | DuckDB | Iceberg | LanceDB |
|---|---|---|---|---|
| **Setup before first query** | open the collection | register a view | catalog + namespace + table | connect + ingest |
| **Data ingestion required** | No | No | No (wraps files) | Yes (copies to Lance) |
| **Query style** | PyArrow / pandas | SQL | Iceberg expressions | PyArrow / pandas / SQL |
| **Append** | save a new artifact | redefine view (ephemeral) | atomic, snapshot-isolated | versioned `add()` |
| **Schema change** | update registry | redefine view (ephemeral) | metadata file, no rewrite | recreate / `add_columns` |
| **Time travel** | collection versions | none | snapshot id | version number |
| **ACID** | validation + versioning | none | full snapshot isolation | versioned appends |
| **Vector search** | no | no | no | yes |
| **Stays in LaminDB lineage** | yes | yes | yes | no (copied out) |

The timings tell a consistent story, but they need a caveat first: on 8,929 rows, nothing here is measuring raw engine throughput — the numbers are dominated by fixed overheads like connection setup and the cost of a single S3 round-trip. That caveat is itself instructive. The per-sample statistics and recurrent-region detection are the *same pandas code* in the PyArrow, Iceberg, and LanceDB paths, so once the data is in memory they take roughly the same few tens of milliseconds regardless of engine. The differences you see in the charts come from two places: whether an engine re-reads storage on every query or caches it, and whether it pays an upfront ingest. Neither is about one query engine being cleverer than another.

<!-- PLOT: setup_cost.svg — read-from-LaminDB + ingest, stacked per engine -->
![Setup cost per engine: PyArrow and DuckDB read in place; Iceberg and LanceDB pay an ingest step](images/setup_cost.svg)

<!-- PLOT: query_times.svg — per-sample stats, recurrent regions, filtered query -->
![Query times per engine. Once data is materialized, the compute is identical pandas across engines](images/query_times.svg)

<!-- PLOT: write_path.svg — append, schema change, time travel -->
![Write-path times. Iceberg and LanceDB write small metadata files; LaminDB does a validated, versioned registry update](images/write_path.svg)

DuckDB had the lowest friction for a SQL user, reaching a queryable view in two lines. Iceberg asked for the most ceremony but returned the strongest write semantics. LanceDB was straightforward once its API was found, with the ingest step as the one real cost. And the Vanilla PyArrow path needed no setup at all — which raises the obvious question.

## The reframe: a query engine is not a data layer

If querying a LaminDB collection through plain PyArrow is this direct, what is LaminDB actually doing?

The honest answer is: not the querying. The Vanilla PyArrow column makes that explicit — the reads are PyArrow, the compute is pandas, and you could swap in DuckDB, Iceberg, or LanceDB on top of the same collection without LaminDB minding. There is no proprietary query engine to be locked into and no query tax to pay. Whichever of the four engines fits the task, the query path is yours to choose.

What LaminDB provides sits *underneath* that choice:

**Lineage.** Every artifact records where it came from and what produced it. The benchmark itself is the demonstration — each engine's results are written back as a tracked artifact, and a final script reads those four results to produce the comparison plots. The whole graph, from the original data transfer through to the figures in this post, is browsable:

<!-- SCREENSHOT: LaminHub lineage graph — transfer → collection → 4 pipeline notebooks → 4 result parquets → plots script → 3 figures -->
![The lineage graph: the source collection feeds four pipeline notebooks, each producing a result artifact, which a plotting script consumes to produce these figures](images/lineage-graph.png)

**Schema validation.** A schema registered against the collection validates new data at write time, rejecting artifacts that don't conform — before they ever reach a query. This catches the bad column on save rather than as a confusing result three steps later.

**Versioning.** Appending a sample creates a new version of the collection, so the state before and after the append are both addressable, with the relationship between them recorded.

**Metadata-queryable collections.** Because artifacts carry biological metadata, you can filter the collection down by that metadata before opening any data at all — selecting the relevant subset of artifacts first, then handing only those to whichever engine does the compute.

The key property is that none of this depends on the query engine. Lineage, validation, and versioning are available whether you go on to query with PyArrow, DuckDB, Iceberg, or LanceDB. The data layer and the query layer are separate concerns, and conflating them — treating "LaminDB" as a competitor to DuckDB — misses the point of both.

## The cost, and the benefit

This separation also explains the one place where LaminDB looks slower. On the write path — appending a sample, evolving the schema — a registered, validated, versioned update to LaminDB takes longer than Iceberg or LanceDB writing a small metadata file. That gap is real, but it isn't a slower version of the same operation; it's a different operation. Iceberg's schema change writes one file scoped to one table. LaminDB's schema change updates a registry that validates every future artifact and is queryable across the entire dataset. You're paying for governance across a data estate, not for a column addition.

The query path, by contrast, carries no such tax — because it's just PyArrow. The thing that makes the Vanilla PyArrow path powerful isn't its speed, which is simply pandas. It's that the data it's reading was tracked, validated, and versioned on the way in, and that you reached it through a collection you can query by biology rather than by file path.

## Conclusion

For genomics R&D, the lakehouse engine is a choice you can make per task. Need SQL and cross-file joins? DuckDB. Need concurrent atomic writes and time travel? Iceberg. Need vector search over embeddings? LanceDB. Just need to read a table and compute? PyArrow is right there. None of these choices is permanent, and none requires giving up the others.

What stays constant underneath is the data layer. LaminDB doesn't ask you to adopt its query engine — it doesn't have one — it asks to hold your data with lineage, validation, and versioning, and then gets out of the way so you can query it however suits the task. Pick the engine that fits the work; keep the governance constant.

## Author contributions

Raaghav Pillai performed the benchmarking work and wrote the pipelines. The original LaminDB ingestion pipeline this work builds on was developed by Sunny Sun. Alex Wolf supervised the project.

## Code & data availability

The four pipeline notebooks, the shared benchmarking utilities, and the plotting script are tracked in the `laminlabs/lakehouse-benchmarks` instance. The dataset is the 1000 Genomes Project CNV calls (DRAGEN, hg38), collection UID `K6X8Ejk3fjgAZT6h0000`.

## How to cite

```
Pillai R, Sun S & Wolf A (2026). Four ways to query a LaminDB collection:
a developer-experience comparison of PyArrow, DuckDB, Iceberg, and LanceDB.
Lamin Blog.
```