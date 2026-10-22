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

We’re thrilled to share that Lamin is generally available! With just a few clicks, anyone can now create a database on [lamin.ai](http://lamin.ai/).

In 2022, we set out to build an open-source data management tool that’d make it easier to scale AI workflows in the life sciences.
Over the past few years, we’ve served research labs and enterprises of all sizes.
Today, Lamin helps even individuals manage knowledge, workflows, and datasets, no matter which format and size.
This post provides some of the background story.

```{raw} html
<div style="text-align: center">
<iframe width="560" height="315" src="https://www.youtube.com/embed/CFW80-O1YAE?si=Eqn4dBZyFDrbcxvm" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>
```

## Why?

Agents had their breakthrough but innovation on data systems lags behind.
There's a strong need for it: the speed at which agents produce and manipulate data in sometimes unreliable and dangerous ways[^crane26] is staggering.[^treybig26]
Still git holds code, markdown holds notes, OWL holds ontologies, and the same file systems, databases, and warehouses hold data.
One layer up, the same high-level systems dominate: note-taking, inventory management, productivity suites with a UI-first, human-centric design are used as the primary systems of record.
None of these systems were built for agents to manage data in a complex domain such as the life sciences at this new scale.

We started working on Lamin in early 2022 concerned that comp bio operations weren't traceable and efficient enough. Today it turns out that those problems have become exacerbated:

1. Untraceable results cannot be trusted, especially when non-verifiable tasks are delegated to agents.
2. Without effective access to multimodal data, LLMs burn tokens or fail entirely.
3. Without governing changes to data akin to governing changes to software with git, it's hard to evaluate agents, debug their mistakes, and safely merge their contributions.

Existing data lakehouses aren't a comprehensive solution. They only address the 2nd and 3rd of these problems for a single table or array format, such as `parquet` or `zarr`.

Especially in life sciences, hard-to-verify tasks are abundant, data formats are heterogeneous, and teams need end-to-end traceability for GxP compliance (21 CFR Part 11 and EU Annex 11).

> The bottleneck for biological agents is the absence of a layer for querying biological data. -- [Laura Luebbert (2026)](https://www.anthropic.com/research/agents-in-biology)

While perhaps more pressing than ever, these problems are decades old.

> There are three kinds of lies: lies, damned lies, and statistics. -- [Mark Twain (1907)](https://en.wikipedia.org/wiki/Lies,_damned_lies,_and_statistics) <br>
> A huge amount of effort is spent cleaning data to get it ready for analysis. -- [Hadley Wickham (2014)](https://www.jstatsoft.org/article/view/v059i10)

The last decade has brought much innovation in the resolution and scale of biological data generation techniques, for example, spatial RNA sequencing.[^marx21]
It also brought the promise of AI helping to extract real value out of this data.
Because most companies kept building UI-first platforms that would only be able to deal with anecdotal data, we felt that an open-source API-first data management tool was missing from the landscape.
We built it directly into the pydata stack based on established tools so that users wouldn't have to worry about dealing with an idiosyncratic, rate-limited REST API.

> I don't want to learn your garbage query language. -- [Erik Bernhardsson (2018)](https://erikbern.com/2018/08/30/i-dont-want-to-learn-your-garbage-query-language.html)

## What?

LaminDB is an open-source data management tool that makes it easy to query, trace and govern datasets across diverse storage formats and locations. Like git, LaminDB runs anywhere and captures relevant context about your work. This includes the data flow through models and analyses, the entities and notes defining the work, and the features & schemas of datasets. It takes about a minute to install LaminDB and create a database on a laptop or in the cloud.

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

LaminHub is a collaboration hub built on LaminDB similar to how GitHub is built on git. Instead of repos, you're looking at databases:

<div style="text-align: center">
<img width="400px" src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/4uXxd6wZ4A4VQaKx0000.png" style="padding: 0;">
</div>

Together, Lamin makes up for what usually takes a dozen tools or an enterprise data platform:

- Data lineage
- Format-agnostic lakehouse
- Notes, ELN, LIMS, Ontologies, Projects
- Versioning + branching
- Data lake + catalog
- Agents + workflows + notebooks
- Feature store, MLOps

Let's walk through it in more detail.

## Data lineage

Over the past years, we have been helping teams in life science organizations to trace data, code & agents. Especially drug discovery teams need end-to-end traceability for compliance; that is not just for a deterministic data pipeline but also upstream metadata entry in the wetlab and downstream interactive and agentic analyses.
The following video exemplifies tracing information flow from an scRNA-seq study and a genome-wide screen that reads out IFNG expression in T cells, based on Schmidt _et al._, Science (2022).[^schmidt22]

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

- audibility for trust ("Was this analysis done correctly?")
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
For example, Jeremie started using LaminDB during his PhD on single-cell foundation models and [says](https://x.com/jkobject/status/2047043597820666039):

> When I start a computational biology project these days, I set up a git repo and a LaminDB instance. It lets me do a lot more, in a reasonable time, in a reproducible way. That's a rare combination in this field.

## Format-agnostic lakehouse

Unlike in traditional SQL-based data warehousing, in AI and R&D data is often kept in storage systems or data lakes.
While AI agents can navigate these storage systems, doing so forces them to waste tokens simply finding files and verifying their schemas.
A recent study on the NCBI Virus Database demonstrated that agents can fail entirely when accessing data across heterogeneous sources, but succeed when provided with a unified schema or API layer.[^anthropic-agents]
This is also true when performing even a simple genetic variant analysis: by treating a number of parquet files as a single dataset with a joint schema, an agent can readily query a collection of 26 such files storing together 88M variants e.g. with polars:

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

And it doesn't just work for tabular data. For years we've helped communities manage data structures with higher complexity, such as `AnnData`[^anndata] or `SpatialData`[^spatialdata] manage datasets at scale.[^spatialdata-blog][^mapped-collection][^annbatch] The central idea for this is to index features independent of how they're materialized.

<div style="text-align: center">
<img width="800px" src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/VFFgFdAlJnssyOdk0001.svg" style="padding: 0;">
</div>

Efficient data access spares humans wrangling data and helps agents reduce token usage.[^pillai26] Here is a video that illustrates this.

```{raw} html
<div style="text-align: center">
<iframe width="560" height="315" src="https://www.youtube.com/embed/vZIoTjYvEgw?si=Eqn4dBZyFDrbcxvm" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>
```

## Notes, LIMS, ELN, Ontologies

While models are trained on datasets in storage - be it a local file system or S3 - many workflows require managing data in transactional systems of record.
Most prominently, the electronic lab notebook (ELN) and laboratory inventory management systems (LIMS) are used by life scientists to manage experiments along with the entities surrounding them.
Mapping data in such an ELN or LIMS system on data that a machine learning scientist would use for model training has been a painful process.
We are not aware of any system that would provide that mapping and so all organizations we know use syncing processes that export data from these systems into machine-learning ready formats in storage.
These processes are almost always brittle and almost never provide the detailed context that the original system provided.

> A feature is an individual measurable property or characteristic of a data set. [Bishop (2006)](<https://en.wikipedia.org/wiki/Feature_(machine_learning)>)

So, we built a records framework into a transactional database that's based on the same features that index datasets in the storage of a lakehouse.
Hence, if you export or import between database and storage, there is no mapping and no ambiguity; the columns of an interactive sheet with experimental records map onto the columns of a csv or parquet file.
And similar for other metadata dimensions of other data formats.

```{raw} html
<div style="text-align: center">
<iframe width="560" height="315" src="https://www.youtube.com/embed/NRzVQXJaRH8?si=Eqn4dBZyFDrbcxvm" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>
```

## Managing changes

There is an established tool for managing changes: `git`. It just doesn't work for large datasets and it doesn't understand entities.
While `dvc` fixes the former, it still doesn't fix the latter. While `dolt` fixes the latter, it doesn't fix the former.
LaminDB fixes both so that dimenionsal modeling of entities with schemas becomes possible, while users can continue to use their most popular formats: `parquet`, `csv`, `hdf5`, `zarr`, and others.

In LaminDB, you can create and switch to a new branch like you do on git:

```bash
lamin switch -c my_branch
```

You can then save new datasets versions, add new records, write new code all on that branch as you'd do in `git`. Once you're done, you can create a "Change Request" and ask a collaborator for review, like you'd do on GitHub.

```{raw} html
<div style="text-align: center">
<iframe width="560" height="315" src="https://www.youtube.com/embed/rzRwcMj6-fc?si=Eqn4dBZyFDrbcxvm" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>
```

## Exploring biological atlases

We provide free programmatic access to the world’s largest public collection of single-cell data at [lamin.ai/explore](https://lamin.ai/explore). We did not re-curate data for 100s of millions of cells, but instead interface public biological data collections such as CellXGene, the Arc Virtual Cell Atlas, and HubMAP, and make their datasets and entities queryable through easy-to-use open-source Python & R libraries.
Instead of navigating fragmented dataset conventions, you can now query for genes, cell types, or perturbations from a single interface.

## What's next?

> All is data. -- [Barney Glaser (1978)](https://en.wikipedia.org/wiki/Grounded_theory)

We're looking forward to helping a strongly growing number of life science researchers and organizations stay in control while AI accelerates their research.

## Thanks to

Our early customers for their patience and kindness.

Zavain Dar, Adam Goulburn & Nan Li from Dimension, who led our seed investment round in September 2022 and have actively supported us ever since. They previously backed companies like Recursion & Hugging Face. Surbhi Sarna & Jared Friedman from YC. Pillar VC, Pioneer Fund, and our angel investors Aaron Kimball, Alec Nielsen, Jeff Hammerbacher, and Oskari Saarenmaa.

> Current myopic obsessions: 1) technoscientific collisions driven by scaling laws of ML applied to the life sciences (@envedabio, @newlimit, @laminlabs, @automata_tech) 2) data first compute stacks 3) obsessing over technological disruption of company form & investor underwriting -- [Zavain Dar, Dimension](https://x.com/zavaindar/status/1717659487312531638)

The previous and part-time team members and consultants who helped build Lamin, some of which have been working with us for years and building key products. Among them, most notable are Robrecht Cannoodt, Luke Zappia, Lukas Heumos, Bernardo Penteado, Altana Namsareava, and Ishita Jain.

Those people & organizations maintaining the open infrastructure on which Lamin is built. First and foremost, that’s Postgres, Django, and fsspec. We should also mention big data storage formats including parquet, HDF5, zarr, tiledbsoma, and of course AnnData & SpatialData. And web technologies like FastAPI, Svelte, and Supabase.

The many people who supported us along the way. Most notably, families and friends.

## Author contributions

`*` These authors contributed equally.

Sunny is a co-founder of Lamin and led building biology-focsed use cases and the related open-source libraries, e.g., `bionty`. She has also led customer interactions and product management for the UI.

Sergei is a founding engineer who started working with us in our first month. Over the years, he has led the deep data infrastructure work across both the open-source libraries and the web platform He has also made numerous other contributions to the open-source libraries.

Ebad is a AI Backend Engineer who has implemented features like the bot accounts, the Pro subscription plan on LaminHub, and agent harness integrations.

Ishita is a Research Software Engineer who has maintained the open-source libraries, the `cellxgene` mirror, and data curation projects.

Sheetal is a full-stack and Research Software Engineer who has developed the UI with features such as Change Requests. She has also contributed to the open-source libraries.

Joel is a full-stack and Research Software Engineer who is driving agentic use cases and contributing across the stack.

Chaichontat is a founding full-stack engineer. He architected, implemented, and leads the frontend of LaminHub. He has also contributed to many other aspects of Lamin.

Frederic is a founding full-stack engineer who started working with us after just a few months. He architected, implemented, and leads the backend of LaminHub along with all infrastructure systems. He also contributed to many other aspects of Lamin.

Alex is a co-founder of Lamin. He implemented wide parts of LaminDB and contributed his opinion to most other parts of Lamin.

## References

[^anthropic-agents]: Luebbert L et al. (2026). Paving the way for agents in biology. [Anthropic Research](https://www.anthropic.com/research/agents-in-biology).

[^schmidt22]: https://pubmed.ncbi.nlm.nih.gov/35113687/ "Schmidt R, Steinhart Z, Layeghi M, Freimer JW, Bueno R, Nguyen VQ, Blaeschke F, Ye CJ, Marson A. CRISPR activation and interference screens decode stimulation responses in primary human T cells. Science. 2022."

[^pillai26]: Pillai R, Rasmussen A, Jain I, Sun S, Rybakov S & Wolf A (2026). Agentic variant analysis of the 1000 Genomes Project using Polars, DuckDB, and lakehouses. Lamin Blog. https://blog.lamin.ai/1000genomes

[^anndata]: Virshup I, Rybakov S, Theis FJ, Angerer P & Wolf FA (2021). anndata: Annotated data. bioRxiv. https://doi.org/10.1101/2021.12.16.473007

[^spatialdata]: Marconato, L., Palla, G., Yamauchi, K.A. et al. SpatialData: an open and universal data framework for spatial omics. Nat Methods 22, 58–62 (2025).

[^spatialdata-blog]: Heumos L, Namsaraeva A, Treis T, Keller M, Vierdag WM, Marconato L, Zimmermann L, Sunny S & Wolf A (2026). Managing spatial omics datasets with SpatialData & LaminDB. Lamin Blog. https://blog.lamin.ai/spatialdata

[^mapped-collection]: Rybakov S, Fischer F, Wiatrak M, Gold I, Rosen Y, Sun S, Sriworarat C, Theis F, Kalfon J & Wolf A (2024). MappedCollection: Weighted random sampling from large collections of scRNA-seq datasets. Lamin Blog. https://blog.lamin.ai/mapped-collection

[^annbatch]: Fischer F, Gold I, Theis F & Wolf A (2026). Scaling anndata training to the terabyte scale with annbatch. Lamin Blog. https://blog.lamin.ai/annbatch

[^crane26]: Crane J (2026). An AI Agent Just Destroyed Our Production Data. It Confessed in Writing. X. https://x.com/lifeofjer/article/2048103471019434248

[^treybig26]: Treybig D (2026). How Agents Use Systems Differently. Substack. https://davistreybig.substack.com/p/how-agents-use-systems-differently

[^marx21]: Marx V (2021). Method of the Year: spatially resolved transcriptomics. Nat Methods 18, 9. https://doi.org/10.1038/s41592-020-01033-y
