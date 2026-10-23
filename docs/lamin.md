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
linkedin: https://www.linkedin.com/feed/update/urn:li:activity:7519061025565024256/
tweet: https://x.com/falexwolf/status/2113296693441573326
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
2. Without effective access to multimodal data, agents burn tokens or fail entirely.
3. Without git-like governance for data, it's hard to evaluate agents, debug their mistakes, and safely merge their contributions.

Especially in life sciences, hard-to-verify tasks are abundant, data formats are heterogeneous, and teams need end-to-end traceability for GxP compliance (21 CFR Part 11 and EU Annex 11).

> The bottleneck for biological agents is not only reasoning but the absence of widespread deterministic execution layers for querying biological data. -- [Laura Luebbert (2026)](https://www.anthropic.com/research/agents-in-biology)

In the past decade, biological data generation has exploded in both resolution and scale, for example, in spatially resolved transcriptomics.[^marx21]
AI promises to extract much more value out of this data, but most vendors have kept building UI-first platforms that could only handle isolated, small-scale datasets.
We felt an open-source, API-first data management tool was missing from the landscape, so we built one into the PyData and R stack — letting scientists keep the tools they already love.

## What?

LaminDB is an open-source data management tool that makes it easy to query, trace, and govern datasets across diverse storage formats and locations. Like git, LaminDB runs anywhere and captures relevant context about your work. This includes the data flow through models and analyses, the entities and notes defining the work, and the features and schemas of datasets. It takes a few seconds to `uv pip install lamindb` and create a database on a laptop or in the cloud.

<div style="display: flex; gap: 16px; align-items: flex-start; width: 85%; margin: 0 auto;">
  <div style="flex: 0.80; min-width: 0;">
    <img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/jMlG8OWw2yFbuhZJ0004.png" style="display: block; width: 100%; height: auto; border-radius: 12px; padding-bottom: 0;" />
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
Drug discovery teams, in particular, need end-to-end traceability for compliance: for deterministic data pipelines, for upstream metadata entry in the wet lab, and for downstream interactive and agentic analyses.
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

Today, even a single researcher might need to keep track of many datasets, analyses, models, and entities.
For example, a researcher who started using LaminDB during his PhD on single-cell foundation models [says](https://x.com/jkobject/status/2047043597820666039):

> When I start a computational biology project these days, I set up a git repo and a LaminDB instance. It lets me do a lot more, in a reasonable time, in a reproducible way. That's a rare combination in this field.

## Format-agnostic lakehouse

In AI and R&D, most data is stored as files in object storage or data lakes. Before an agent can query such data, it has to find the relevant files and work out their schemas, and it spends tokens and makes errors doing so.
In a recent study on the NCBI Virus database, agents retrieving viral sequences on their own were often inaccurate and gave different answers from run to run, whereas every agent exceeded 90% accuracy when given a deterministic retrieval tool.[^anthropic-agents]
LaminDB provides such a layer for files. It indexes features independently of how datasets store them, in whatever format or location, groups features into schemas, and validates incoming datasets against those schemas.
You group files into a collection with one schema, and you or an agent[^pillai26] can then query the collection as one dataset, for example, filtering 88M variants stored in 26 parquet files with a single `polars` query:[^polars]

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

Each `collection.append()` creates a new version of the collection in an ACID transaction, and earlier versions remain queryable, similar to time travel in Iceberg. When agents append data later, the version used in an earlier analysis stays unchanged.

This doesn't just work for tabular data or specific array formats. For years we've worked with communities who use data structures of higher complexity, such as `AnnData`[^anndata] or `SpatialData`,[^spatialdata] and different formats such as `hdf5`, `zarr`, and `tiledb`.[^spatialdata-blog][^mapped-collection] Here is how you'd stream training batches from on a collection of `AnnData` artifacts in `zarr` format using `annbatch`:[^annbatch]

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

The central idea is to index features independent of how they're materialized, create schemas, and validate incoming datasets based on those.
Whether you validate datasets and shard them lakehouse-style via collections, or keep working with individual artifacts in a data lake, depends on your data engineering goal.

<div style="text-align: center">
<img width="800px" src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/VFFgFdAlJnssyOdk0001.svg" style="padding: 0;">
</div>

Here is a video that illustrates the lakehouse idea for the genetic variant analysis.

```{raw} html
<div style="text-align: center">
<iframe width="560" height="315" src="https://www.youtube.com/embed/vZIoTjYvEgw?si=Eqn4dBZyFDrbcxvm" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>
```

## Notes, ELN, LIMS, ontologies

While models are trained on datasets in storage — be it a local file system or S3 — many workflows require managing data in transactional systems of record.
Most prominently, life scientists use electronic lab notebooks (ELN) and laboratory information management systems (LIMS) to manage experiments and the samples, reagents, and cell lines they use.
Mapping records from an ELN or LIMS onto the datasets that a machine learning scientist uses for model training has long been a painful process.
We are not aware of any system that provides that mapping. All organizations we know use syncing processes that export data from these systems into machine-learning-ready formats in storage.
These processes are almost always brittle and rarely keep the detailed context that the original system captured, such as which sample a measurement came from.

> A feature is an individual measurable property or characteristic of a data set. -- [Bishop (2006)](<https://en.wikipedia.org/wiki/Feature_(machine_learning)>)

So, we built a records framework into a transactional database that's based on the same features that index datasets in lakehouse storage.
Hence, if you export or import between database and storage, there is no ambiguity; the columns of an interactive registry of experimental records map onto the columns of a csv or parquet file.
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

And, you can easily get started with notes management by syncing markdown notes into your database:

```shell
lamin save my-note.md
```

This way you can use your favorite local editors and agent harnesses:

<div align="center">
  <img width=300 src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/kebpWrpEOZSUhtKK0000.png" style="padding: 0;"/>
</div>

## Branching & versioning

`git` is the established tool for managing changes. It just doesn't work for large datasets and it doesn't understand entities.
While `dvc` fixes the former, it still doesn't fix the latter. While `dolt` fixes the latter, it doesn't fix the former.
LaminDB fixes both — enabling dimensional modeling of entities with schemas and while letting you use your favorite formats: `parquet`, `csv`, `hdf5`, `zarr`, and others.

In LaminDB, you can create and switch to a new branch like you do in `git`:

```bash
lamin switch -c my_branch
```

You can then save new dataset versions, add new records, make a change to a notebook, and trace agents — all on that branch. Once you're done, you can create a "Change Request" and ask a collaborator for review, like you'd do on GitHub.
LaminDB works alongside `git`: You keep using `git` for code and can leverage LaminDB's integration to sync changes.

```{raw} html
<div style="text-align: center">
<iframe width="560" height="315" src="https://www.youtube.com/embed/rzRwcMj6-fc?si=Eqn4dBZyFDrbcxvm" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>
```

## Biological atlases

You can access some of the world’s largest public collections of single-cell, spatial, and other biological data at [lamin.ai/explore](https://lamin.ai/explore). Rather than re-curating data for hundreds of millions of cells, we mirror resources such as CELLxGENE and the Arc Virtual Cell Atlas.

## What's next?

We look forward to helping a rapidly growing number of life science researchers and organizations stay in control while AI accelerates their work.
And we're happy to keep addressing fundamental challenges of data-driven science that have been around for much longer than AI.

> There are three kinds of lies: lies, damned lies, and statistics. -- [Twain/Disraeli (1907)](https://en.wikipedia.org/wiki/Lies,_damned_lies,_and_statistics) <br>
> A huge amount of effort is spent in cleaning data to get it ready for analysis. -- [Hadley Wickham (2014)](https://www.jstatsoft.org/article/view/v059i10) <br>
> All is data. -- [Barney Glaser (1978)](https://en.wikipedia.org/wiki/Grounded_theory)

## Thanks to

Our early customers for their patience and kindness.

Zavain Dar, Adam Goulburn & Nan Li from Dimension, who led our seed investment in 2022 and have supported us ever since. YC (Surbhi Sarna & Jared Friedman), Pillar VC (Tony Kulesa), Pioneer Fund, and our angel investors Aaron Kimball, Alec Nielsen, Jeff Hammerbacher, and Oskari Saarenmaa.

Past and part-time team members and consultants who helped build Lamin, some of whom have been working with us for years — in particular, Robrecht Cannoodt, Luke Zappia, Lukas Heumos, Bernardo Penteado, Lawrence Lee, Altana Namsaraeva, Alex Rasmusen, Alex Kramer, Cydney Nielsen, Wahed Mangal, Ishita Jain, Malte Kuehl, and Paul Schwind.

The people and organizations maintaining the open infrastructure on which Lamin is built — first and foremost Postgres, Django, and fsspec, alongside data formats and frameworks like parquet, zarr, tiledbsoma, AnnData, and SpatialData, and web technologies like FastAPI, Svelte, and Supabase.

The many people who supported us along the way, in particular, our families and friends.

## Author contributions

`*` These authors contributed equally.

Sunny is a co-founder of Lamin and led building biology-focused use cases and products.

Sergei is a founding engineer who started working with us in the first month. Over the years, he has led the deep data infrastructure work across both the open-source libraries and the web platform.

Ebad is an AI backend engineer who has implemented features like bot accounts, the Pro subscription plan on LaminHub, and agent harness integrations.

Sheetal is a full-stack and research software engineer who has developed UI features such as Change Requests. She has also contributed to the open-source libraries.

Joel is a full-stack and research software engineer who is driving agentic use cases and contributing across the stack.

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

[^spatialdata-blog]: Heumos L, Namsaraeva A, Treis T, Keller M, Vierdag WM, Marconato L, Zimmermann L, Sun S & Wolf A (2026). Managing spatial omics datasets with SpatialData & LaminDB. Lamin Blog. https://blog.lamin.ai/spatialdata

[^mapped-collection]: Rybakov S, Fischer F, Wiatrak M, Gold I, Rosen Y, Sun S, Sriworarat C, Theis F, Kalfon J & Wolf A (2024). MappedCollection: Weighted random sampling from large collections of scRNA-seq datasets. Lamin Blog. https://blog.lamin.ai/mapped-collection

[^annbatch]: Fischer F, Gold I, Theis F & Wolf A (2026). Scaling anndata training to the terabyte scale with annbatch. Lamin Blog. https://blog.lamin.ai/annbatch

[^crane26]: Crane J (2026). An AI Agent Just Destroyed Our Production Data. It Confessed in Writing. X. https://x.com/lifeofjer/article/2048103471019434248

[^treybig26]: Treybig D (2026). How Agents Use Systems Differently. Substack. https://davistreybig.substack.com/p/how-agents-use-systems-differently

[^marx21]: Marx V (2021). Method of the Year: spatially resolved transcriptomics. Nat Methods 18, 9. https://doi.org/10.1038/s41592-020-01033-y
