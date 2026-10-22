---
title: "Introducing Lamin: An open data platform for traceable, multimodal AI"
date: 2026-10-22
author: sunnyosun, Koncopd, ebadukhan, sheetalgiri, AllaVinner, chaichontat*, fredericenard*, falexwolf
affiliation:
  sunnyosun: Lamin Labs, Munich
  Koncopd: Lamin Labs, Munich
  ebadukhan: Lamin Labs, Munich
  sheetalgiri: Lamin Labs, Munich
  AllaVinner: Lamin Labs, Munich
  chaichontat: Lamin Labs, NYC
  fredericenard: Lamin Labs, NYC
  falexwolf: Lamin Labs, Munich
---

We’re thrilled to share that Lamin is generally available! With just a few clicks, anyone can now create a database on [lamin.ai](https://lamin.ai/).

In 2022, we set out to build an open-source data management tool that’d make it easier to scale AI workflows in the life sciences.
Over the past few years, we’ve served research labs and enterprises of all sizes.
Now, anyone can use Lamin to manage knowledge, workflows, and datasets, whatever the format and size.

```{raw} html
<div style="text-align: center">
<iframe width="560" height="315" src="https://www.youtube.com/embed/CFW80-O1YAE?si=Eqn4dBZyFDrbcxvm" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>
```

## Why?

There's a strong need for innovation in data systems: agents produce and manipulate data at a staggering pace, sometimes in unreliable and dangerous ways.[^crane26][^treybig26]
Yet git still holds code, markdown holds notes, OWL/RDF hold ontologies, and the same file systems, databases, and warehouses hold data.
One layer up, the same high-level systems of record dominate: note-taking apps, inventory managers, and productivity suites built around a UI-first, human-centric design.
None of these systems were built for agents managing complex life sciences data at scale.

We started working on Lamin in early 2022, concerned that comp bio operations weren't traceable and efficient enough. Today, agents have amplified those problems:

1. Untraceable results cannot be trusted, especially when non-verifiable tasks are delegated to agents.
2. Without effective access to multimodal data, LLMs burn tokens or fail entirely.
3. Without git-like governance for data, it's hard to evaluate agents, debug their mistakes, and safely merge their contributions.

Especially in life sciences, hard-to-verify tasks are abundant, data formats are heterogeneous, and teams need end-to-end traceability for GxP compliance (21 CFR Part 11 and EU Annex 11).

> The bottleneck for biological agents is not only reasoning but the absence of widespread deterministic execution layers for querying biological data. -- [Laura Luebbert (2026)](https://www.anthropic.com/research/agents-in-biology)

In the past decade, biological data generation has exploded in both resolution and scale, for example, in spatially resolved transcriptomics.[^marx21]
AI promises to extract much more value out of this data, but most vendors have kept building UI-first platforms that could only handle isolated, small-scale datasets.
We felt an open-source, API-first data management tool was missing from the landscape, so we built one directly into the PyData stack—letting scientists keep the tools they already love.

## What?

LaminDB is an open-source data management tool that makes it easy to query, trace, and govern datasets across diverse storage formats and locations. Like git, LaminDB runs anywhere and captures relevant context about your work. This includes the data flow through models and analyses, the entities and notes defining the work, and the features and schemas of datasets. It takes about a minute to `uv pip install lamindb` and create a database on a laptop or in the cloud.

<div style="display: flex; gap: 16px; align-items: flex-start; width: 85%; margin: 0 auto;">
  <div style="flex: 0.80; min-width: 0;">
    <img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/jMlG8OWw2yFbuhZJ0002.png" style="display: block; width: 100%; height: auto; border-radius: 12px; padding-bottom: 0;" />
    <p style="text-align: right; margin-top: 0.2rem;"><em>Init a local database like you init a git repo.</em></p>
  </div>
  <div style="flex: 1.2; min-width: 0;">
    <img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/KWOioD0id2csEv2S0005.png" style="display: block; width: 100%; height: auto; border-radius: 12px; padding-bottom: 0;" />
    <p style="text-align: right; margin-top: 0.2rem;"><em>The SQLite file indexing your files.</em></p>
  </div>
  <div style="flex: 1.2; min-width: 0;">
    <img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/EqsNFkUSWz0XdGFG0001.png" style="display: block; width: 100%; height: auto; border-radius: 12px; padding-bottom: 0;" />
    <p style="text-align: right; margin-top: 0.2rem;"><em>Create a database on the hub UI.</em></p>
  </div>
</div>

LaminHub is a collaboration hub built on LaminDB, similar to how GitHub is built on git. Instead of repos, you're looking at databases:

<div style="text-align: center">
<img width="400px" src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/4uXxd6wZ4A4VQaKx0000.png" style="padding: 0;">
</div>

Together, Lamin covers what usually takes a dozen tools or an enterprise data platform:

- Data lineage
- Format-agnostic lakehouse
- Notes, ELN, LIMS, ontologies, projects
- Versioning, branching
- Data lake, catalog
- Agents, workflows, notebooks
- Feature store, MLOps

Let's walk through several of these in more detail.

## Data lineage

Over the past few years, we have been helping teams in life science organizations to trace data, code, and agents.
Drug discovery teams, in particular, need end-to-end traceability for compliance — not just for deterministic data pipelines, but also for upstream metadata entry in the wetlab and downstream interactive and agentic analyses.
The following video demonstrates tracing information flow from an scRNA-seq study and a genome-wide screen that reads out IFNG expression in T cells, based on Schmidt _et al._, Science (2022).[^schmidt22]

```{raw} html
<div style="text-align: center">
<iframe width="560" height="315" src="https://www.youtube.com/embed/yK3ODFZLL1A?si=Eqn4dBZyFDrbcxvm" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>
```

Tracking data flow is easy. For example, in a Python script or notebook you'd just call:

```python
import lamindb as ln

ln.track()  # initiate a tracked notebook/script run

# your code automatically tracks inputs & outputs

ln.finish()  # mark run as finished, save execution report, source code & environment
```

You can also decorate Python functions, use similar syntax in R, or use `nf-lamin` to track Nextflow pipelines.

Traceability is valuable beyond compliance. It gives you:

- auditability for trust ("Was this analysis done correctly?")
- context for interpretation ("Has this confounder been corrected for?")
- reproducibility ("What were the parameters, the source code, input dataset versions, and the run environment?")
- long-term memory ("How did we analyze datasets for frozen lung tissue before?")

Here is an example of how Lamin is deployed in an enterprise R&D data platform:

```{raw} html
<div style="text-align: center">
<iframe width="560" height="315" src="https://www.youtube.com/embed/rpydrLFXLwE?si=VfTXVGrEr38FZ_qL&start=477" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>
```

> The Lamin data lakehouse really underlies a lot of the work we're doing. [...] The way we think about it is that Lamin is to data what GitHub is to code. It's a way to track and trace the full lineage of your data as you're working on it. [...]

Today, even a project with a single human might need to keep track of many datasets, analyses, models, and entities.
For example, a researcher who started using LaminDB during his PhD on single-cell foundation models [says](https://x.com/jkobject/status/2047043597820666039):

> When I start a computational biology project these days, I set up a git repo and a LaminDB instance. It lets me do a lot more, in a reasonable time, in a reproducible way. That's a rare combination in this field.

## Format-agnostic lakehouse

Unlike in traditional SQL-based data warehousing, data in AI and R&D is often kept in storage systems or data lakes.
While AI agents can navigate these storage systems, doing so forces them to waste tokens simply finding files and verifying their schemas.
A recent study on the NCBI Virus Database demonstrated that agents can fail when accessing data across heterogeneous sources, but succeed when provided with a unified schema or API layer.[^anthropic-agents]
This is also true when performing even a simple genetic variant analysis: by treating a number of parquet files as a single dataset with a joint schema, an agent can readily query a collection of 26 such files storing 88M variants, for example, with `polars`:[^polars]

```python
import lamindb as ln
import polars as pl

db = ln.DB("laminlabs/1000genomes")
collection = db.Collection.get("hVu9puwdRGskm1I6")
with collection.open(engine="polars") as df:
    chrom = "1"
    lo, hi = 150_000_000, 200_000_000
    filtered = df.filter(
        (pl.col("chrom") == chrom) & (pl.col("pos") >= lo) & (pl.col("pos") <= hi)
    ).collect()
```

And if you manipulate such a `Collection` object, you get ACID transactions and time travel, similar to established lakehouse frameworks like Iceberg.

This doesn't just work for tabular data or specific array formats. For years we've worked with communities who use data structures of higher complexity, such as `AnnData`[^anndata] or `SpatialData`[^spatialdata], and different formats such as `hdf5`, `zarr`, and `tiledb`.[^spatialdata-blog][^mapped-collection] Here is how you'd train a model on a collection of `AnnData` artifacts in `zarr` format using `annbatch`:[^annbatch]

```python
import anndata as ad
import zarr
from annbatch import Loader

db = ln.DB("laminlabs/arrayloader-benchmarks")
collection = db.Collection.get(key="Tahoe100M_zarr")

paths = [artifact.cache() for artifact in collection.artifacts.all()]
loader = Loader(shuffle=True, batch_size=4096, chunk_size=256, preload_nchunks=64)
loader.add_datasets(
    datasets=[ad.io.sparse_dataset(zarr.open(p)["X"]) for p in paths],
    obs=[ad.io.read_elem(zarr.open(p)["obs"]) for p in paths],
)
for batch in loader:
    pass
```

The central idea is to index features independent of how they're materialized, create schemas, and validate incoming datasets based on those. Whether you actually validate and use lakehouse-style dataset sharding via collections or just keep working with artifacts in a data lake is your choice and depends on the data engineering goal at hand.

<div style="text-align: center">
<img width="800px" src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/VFFgFdAlJnssyOdk0001.svg" style="padding: 0;">
</div>

Efficient data access spares humans from wrangling data and helps agents reduce token usage.[^pillai26] Here is a video that illustrates this.

```{raw} html
<div style="text-align: center">
<iframe width="560" height="315" src="https://www.youtube.com/embed/vZIoTjYvEgw?si=Eqn4dBZyFDrbcxvm" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>
```

## Notes, ELN, LIMS, ontologies

While models are trained on datasets in storage — be it a local file system or S3 — many workflows require managing data in transactional systems of record.
Most prominently, life scientists use electronic lab notebooks (ELN) and laboratory information management systems (LIMS) to manage experiments along with the entities surrounding them.
Mapping records from an ELN or LIMS onto the datasets that a machine learning scientist uses for model training has long been a painful process.
We are not aware of any system that provides that mapping and so all organizations we know use syncing processes that export data from these systems into machine-learning-ready formats in storage.
These processes are almost always brittle and almost never provide the detailed context that the original system captured.

> A feature is an individual measurable property or characteristic of a data set. -- [Bishop (2006)](<https://en.wikipedia.org/wiki/Feature_(machine_learning)>)

So, we built a records framework into a transactional database that's based on the same features that index datasets in lakehouse storage.
Hence, if you export or import between database and storage, there is no ambiguity; the columns of an interactive sheet with experimental records map onto the columns of a csv or parquet file.
The same holds for other metadata dimensions and data formats.

```{raw} html
<div style="text-align: center">
<iframe width="560" height="315" src="https://www.youtube.com/embed/NRzVQXJaRH8?si=Eqn4dBZyFDrbcxvm" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>
```

You can also build your own ontologies or integrate established public ones. Here is how you'd get a public ontology record from a `lamindb` plugin to use for validation:

```python
import bionty as bt

hek293 = bt.CellLine.from_source(name="HEK293").save()
```

You can easily get started with notes management by syncing markdown notes into your database. In your development directory, run:

```shell
lamin save my-note.md
```

To load a markdown record back, run:

```shell
lamin load https://lamin.ai/laminlabs/lamindata/record/mNDJgWFrkWQVW3ox
```

This way you can use your favorite local editors and agent harnesses:

<div align="center">
  <img width=300 src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/kebpWrpEOZSUhtKK0000.png" style="padding: 0;"/>
</div>

## Branching & versioning

There is an established tool for managing changes: `git`. It just doesn't work for large datasets and it doesn't understand entities.
While `dvc` fixes the former, it still doesn't fix the latter. While `dolt` fixes the latter, it doesn't fix the former.
LaminDB fixes both so that dimensional modeling of entities with schemas becomes possible, while users can continue to use their most popular formats: `parquet`, `csv`, `hdf5`, `zarr`, and others.

In LaminDB, you can create and switch to a new branch like you do on git:

```bash
lamin switch -c my_branch
```

You can then save new dataset versions, add new records, write new code all on that branch as you'd do in `git`. Once you're done, you can create a "Change Request" and ask a collaborator for review, like you'd do on GitHub.

```{raw} html
<div style="text-align: center">
<iframe width="560" height="315" src="https://www.youtube.com/embed/rzRwcMj6-fc?si=Eqn4dBZyFDrbcxvm" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>
```

## Biological atlases

We provide free programmatic access to the world’s largest public collections of single-cell data at [lamin.ai/explore](https://lamin.ai/explore). We did not re-curate data for 100s of millions of cells, but mirror collections such as CELLxGENE, the Arc Virtual Cell Atlas, and HuBMAP.

## What's next?

We will keep helping a rapidly growing number of life science researchers and organizations stay in control while AI accelerates their research.

> All is data. -- [Barney Glaser (1978)](https://en.wikipedia.org/wiki/Grounded_theory)

And we'll continue to address some of the fundamental issues of data-driven research.

> There are three kinds of lies: lies, damned lies, and statistics. -- [Twain/Disraeli (1907)](https://en.wikipedia.org/wiki/Lies,_damned_lies,_and_statistics) <br>
> A huge amount of effort is spent in cleaning data to get it ready for analysis. -- [Hadley Wickham (2014)](https://www.jstatsoft.org/article/view/v059i10)

## Thanks to

Our early customers for their patience and kindness.

Zavain Dar, Adam Goulburn & Nan Li from Dimension, who led our seed investment in 2022 and have supported us ever since. YC (Surbhi Sarna & Jared Friedman), Pillar VC (Tony Kulesa), Pioneer Fund, and our angel investors Aaron Kimball, Alec Nielsen, Jeff Hammerbacher, and Oskari Saarenmaa.

The previous and part-time team members and consultants who helped build Lamin, some of whom have been working with us for years. Among them, most notable are Robrecht Cannoodt, Luke Zappia, Lukas Heumos, Bernardo Penteado, Altana Namsaraeva, and Ishita Jain.

The people & organizations maintaining the open infrastructure on which Lamin is built. First and foremost, that’s Postgres, Django, and fsspec. We'd also like to mention data storage formats including parquet, zarr, tiledbsoma, and of course AnnData & SpatialData. And web technologies like FastAPI, Svelte, and Supabase.

The many people who supported us along the way, in particular, families and friends.

## Author contributions

`*` These authors contributed equally.

Sunny is a co-founder of Lamin and led building biology-focused use cases and the related open-source libraries, e.g., `bionty`. She has also led customer interactions and product management for the UI.

Sergei is a founding engineer who started working with us in the first month. Over the years, he has led the deep data infrastructure work across both the open-source libraries and the web platform. He has also made numerous other contributions to the open-source libraries.

Ebad is an AI Backend Engineer who has implemented features like the bot accounts, the Pro subscription plan on LaminHub, and agent harness integrations.

Sheetal is a full-stack and Research Software Engineer who has developed the UI with features such as Change Requests. She has also contributed to the open-source libraries.

Joel is a full-stack and Research Software Engineer who is driving agentic use cases and contributing across the stack.

Chaichontat is a founding full-stack engineer. He architected, implemented, and leads the frontend of LaminHub. He has also contributed to many other aspects of Lamin.

Frederic is a founding full-stack engineer. He architected, implemented, and leads the backend of LaminHub along with infrastructure systems.

Alex is a co-founder of Lamin and implemented much of LaminDB.

## References

[^anthropic-agents]: Luebbert L et al. (2026). Paving the way for agents in biology. [Anthropic Research](https://www.anthropic.com/research/agents-in-biology).

[^schmidt22]: Schmidt R, Steinhart Z, Layeghi M, Freimer JW, Bueno R, Nguyen VQ, Blaeschke F, Ye CJ, Marson A. CRISPR activation and interference screens decode stimulation responses in primary human T cells. Science. 2022. https://pubmed.ncbi.nlm.nih.gov/35113687/

[^pillai26]: Pillai R, Rasmussen A, Jain I, Sun S, Rybakov S & Wolf A (2026). Agentic variant analysis of the 1000 Genomes Project using Polars, DuckDB, and lakehouses. Lamin Blog. https://blog.lamin.ai/1000genomes

[^polars]: Polars. Polars: Fast multi-threaded, hybrid-streaming DataFrame library. [Polars](https://pola.rs/).

[^anndata]: Virshup I, Rybakov S, Theis FJ, Angerer P & Wolf FA (2021). anndata: Annotated data. bioRxiv. https://doi.org/10.1101/2021.12.16.473007

[^spatialdata]: Marconato, L., Palla, G., Yamauchi, K.A. et al. SpatialData: an open and universal data framework for spatial omics. Nat Methods 22, 58–62 (2025).

[^spatialdata-blog]: Heumos L, Namsaraeva A, Treis T, Keller M, Vierdag WM, Marconato L, Zimmermann L, Sunny S & Wolf A (2026). Managing spatial omics datasets with SpatialData & LaminDB. Lamin Blog. https://blog.lamin.ai/spatialdata

[^mapped-collection]: Rybakov S, Fischer F, Wiatrak M, Gold I, Rosen Y, Sun S, Sriworarat C, Theis F, Kalfon J & Wolf A (2024). MappedCollection: Weighted random sampling from large collections of scRNA-seq datasets. Lamin Blog. https://blog.lamin.ai/mapped-collection

[^annbatch]: Fischer F, Gold I, Theis F & Wolf A (2026). Scaling anndata training to the terabyte scale with annbatch. Lamin Blog. https://blog.lamin.ai/annbatch

[^crane26]: Crane J (2026). An AI Agent Just Destroyed Our Production Data. It Confessed in Writing. X. https://x.com/lifeofjer/article/2048103471019434248

[^treybig26]: Treybig D (2026). How Agents Use Systems Differently. Substack. https://davistreybig.substack.com/p/how-agents-use-systems-differently

[^marx21]: Marx V (2021). Method of the Year: spatially resolved transcriptomics. Nat Methods 18, 9. https://doi.org/10.1038/s41592-020-01033-y
