---
title: "Lamin: An open data platform for traceable, multimodal AI"
date: 2026-09-07
author: sunnyosun, Koncopd, Ebad371, ishitajain9717, sheetalgiri, fredericenard*, chaichontat*, falexwolf
affiliation:
  sunnyosun: Lamin Labs, Munich
  Koncopd: Lamin Labs, Munich
  Ebad371: Lamin Labs, Munich
  ishitajain9717: Lamin Labs, Munich
  sheetalgiri: Lamin Labs, Munich
  fredericenard: Lamin Labs, NYC
  chaichontat: Lamin Labs, NYC
  falexwolf: Lamin Labs, Munich
---

We're super happy to announce that Lamin is now generally available!
With a few clicks, anyone can create a database on [lamin.ai](https://lamin.ai/), which makes hosting the open-source LaminDB as easy as it gets.
For years we've been helping life science organizations get multimodal data AI-ready and processes traceable at a new scale.
Today agents let even individuals work with high numbers of datasets, workflows, analyses, and models.
Lamin provides the open-source data layer that keeps that work sane.

## Why?

While agents had their breakthrough and intelligence has become abundant, innovation on the system layers that are operated by agents is still lagging behind.
There's a strong need for it: the speed in which agents produce and manipulate data in sometimes unreliable and even dangerous ways[^crane26] is staggering.
But it is still git that manages code, it's still markdown that holds notes, and it's largely still the same file systems, databases, warehouses, and lakehouses that hold data, it's still the same ontologies that provide agents with a framework.
Agents are using these low-level systems in somewhat similar ways to how developers have been using them for years, although at a different scale and with different characteristics.[^treybig26]
One layer up in the technology stack, the world is still using the same high-level systems: note taking, inventory management, productivity workspaces with a UI-first, human-centric design are used as the primary systems of record.
None of these systems were built for agents to manage data in a complex domain like biology at this new scale.

We started working on Lamin in early 2022 with the idea that computational biology should become more traceable & efficent.
Some of the underlying problems are fundamental and had already been true for decades.

> There are three kinds of lies: lies, damned lies, and statistics. -- [Mark Twain (1907)](https://en.wikipedia.org/wiki/Lies,_damned_lies,_and_statistics) <br>
> A huge amount of effort is spent cleaning data to get it ready for analysis. -- [Hadley Wickham (2014)](https://www.jstatsoft.org/article/view/v059i10)

But only since everybody started to delegate work to agents they have become painful for a large number of people and organizations: Agents need API-first access to operate. Untraceable agentic results cannot be trusted but tracing interactive data workloads doesn't fit the established workflow managers. Agents burn tokens, make mistakes, or fail entirely if unable to efficiently access data.

> The bottleneck for biological agents is the absence of a layer for querying biological data. -- [Laura Luebbert (2026)](https://www.anthropic.com/research/agents-in-biology)

Changes made by agents have a strong need for review and need to frequently corrected.
These fundamental problems are particularly severe in the life sciences due to its many different data formats, complex data generation processes, the high number of concepts needed even to just define measurements -- it's not just tokens or pixels or a few simple metrics as in other domains.

<div style="text-align: center">
<img width="800px" src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/VFFgFdAlJnssyOdk0001.svg" style="padding: 0;">
</div>

The last decade has brought much innovation in the resolution and scale of biological data generation techniques, for example, spatial RNA sequencing.[^marx21]
The last decade also brought the promise of AI helping to get real value out of these data.
But the world has kept building UI-first platforms and ELN systems for biologists wrangling anecdotal data.
So we thought an API-first data management tool for the age of AI was needed, and we built it open-source into the pydata stack, so that it's just a `pip install` to set it up and users wouldn't have to worry about dealing with the ideosyncratic rate-limited REST API of a startup.

> I don't want to learn your garbage query language. -- [Erik Bernarhardsson](https://erikbern.com/2018/08/30/i-dont-want-to-learn-your-garbage-query-language.html)

## What?

LaminDB is an open-source data management tool that makes it easy to query, trace & govern datasets across diverse storage formats and locations.
Like git, LaminDB is a distributed system that runs anywhere and captures all relevant context about your work.
That includes the data flow through models and analyses, the entities and notes defining experiments, and the features & schemas of datasets.
It takes a few seconds to install LaminDB and create a database.

<div style="display: flex; gap: 16px; align-items: flex-start; width: 85%; margin: 0 auto;">
  <div style="flex: 0.80; min-width: 0;">
    <img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/jMlG8OWw2yFbuhZJ0002.png" style="display: block; width: 100%; height: auto; border-radius: 12px; padding-bottom: 0;" />
    <p style="text-align: right; margin-top: 0.2rem;"><em>Init a database like you init a git repo.</em></p>
  </div>
  <div style="flex: 1.2; min-width: 0;">
    <img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/KWOioD0id2csEv2S0005.png" style="display: block; width: 100%; height: auto; border-radius: 12px; padding-bottom: 0;" />
    <p style="text-align: right; margin-top: 0.2rem;"><em>An SQLite database tracks all context you need.</em></p>
  </div>
</div>

## Tracing data, code & agents

For years, we have been serving teams of humans in academia, BioTech, and Big Pharma, but today, anyone can delegate work to a team of agents, and even a project with a single human might need to keep track of many datasets, analyses, models, and entities.
For example, Jeremie started using LaminDB during his PhD on single-cell foundation models and says:

> When I start a computational biology project these days, I set up a git repo and a LaminDB instance. It lets me do a lot more, in a reasonable time, in a reproducible way. That's a rare combination in this field. -- [Jeremie Kalfon, ENS Paris & Institut Pasteur](https://x.com/jkobject/status/2047043597820666039)

Especially drug discovery teams need end-to-end traceability for GxP compliance (21 CFR Part 11 and EU Annex 11). LaminDB allows tracing how information flows through data transformation steps and across entities -- from a genome-wide screen that reads out IFNG expression in T cells, a marker for their inflammatory response -- to scRNA-seq and agentic insights about drug targets and perturbations.[^schmidt22]

```{raw} html
<iframe width="560" height="315" src="https://www.youtube.com/embed/yK3ODFZLL1A?si=Eqn4dBZyFDrbcxvm" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
```

Beyond audibility for trust ("Was this analysis done correctly?"), tracebility also creates context for interpretation ("Has this confounder been corrected for?"), reproducibility ("What were the parameters, the source code, input dataset versions, and the run environment?"), and creates a long-term memory of data operations ("How did we analyze datasets for frozen lung tissue before?"). It's been notoriously difficult to create big training datasets for biology outside of simple systems.
Just by using LaminDB, one creates FAIR training data automatically, a bit like when using git to manage the source code of a project produces a rich queryable dataset about the evolution of the project.
This creates an unprecedented training dataset that helps both humans and AI models learn from every analysis.
It closes the training feedback loop across different teams and models, in particular between the wetlab and the drylab.

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

Such efficient data access then helps agents reduce token usage or spares humans wrangling data.[^pillai26]

```{raw} html
<iframe width="560" height="315" src="https://www.youtube.com/embed/vZIoTjYvEgw?si=Eqn4dBZyFDrbcxvm" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
```

And it doesn't just work for tabular data. For years we've helped communities manage data structures with higher complexity, such as `AnnData`[^anndata] or `SpatialData`[^spatialdata] manage datasets at scale.[^spatialdata-blog][^mapped-collection][^annbatch]

## Notes, LIMS, ELN, Ontologies

> A feature is an individual measurable property or characteristic of a data set. [Bishop (2006)](<https://en.wikipedia.org/wiki/Feature_(machine_learning)>)

While models are trained on datasets in storage - be it a local file system or S3 - many workflows require managing data in transactional systems of record.
Most prominently, the electronic lab notebook (ELN) and laboratory inventory management systems (LIMS) used by life scientists to manage experiments and all the entities and notes that surround them.
Mapping data in such an ELN or LIMS system on data that a machine learning scientist would use for model training has historically been a painful process.
We are not aware of any system that would provide that mapping and so all organizations we know use syncing processes that export data from these systems into machine-learning ready formats in storage.
These processes are almost always brittle and almost never provide the detailed context that the original system provided.

So, we built a records framework into a transactional database that's based on the same features that index datasets in the storage of a lakehouse.
Hence, if you export or import between database and storage, there is no mapping and no ambiguity; the columns of an interactive sheet with experimental records map onto the columns of a csv or parquet file.
And similar for other metadata dimensions of other data formats.

```{raw} html
<iframe width="560" height="315" src="https://www.youtube.com/embed/NRzVQXJaRH8?si=Eqn4dBZyFDrbcxvm" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
```

## Managing changes

There is an established tool for managing changes: `git`. It just doesn't work for large datasets and it doesn't understand entities. While `dvc` fixes the former, it still doesn't fix the latter. While `dolt` fixes the latter, it doesn't fix the former.

Much of data architecture across fields relies on dimenionsal modeling of entities with schemas.
And the worlds most popular formats for datasets are storage based, e.g., parquet, csv, `hdf5`, or `.zarr`.

In LaminDB, you can create and switch to new branch like you do on git:

```bash
lamin switch -c my_branch
```

You can then save new datasets versions, add new records, write new code all on that branch as you'd do in `git`. Once you're done, you can create a "Change Request" and ask a collaborator for review, like you'd do on GitHub.

```{raw} html
<iframe width="560" height="315" src="https://www.youtube.com/embed/rzRwcMj6-fc?si=Eqn4dBZyFDrbcxvm" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
```

## Explore biological atlases

We provide free programmatic access to the world’s largest public collection of single-cell data at [lamin.ai/explore](https://lamin.ai/explore). We did not re-curate data for 100s of millions of cells, but instead interface public biological data collections such as CellXGene, the Arc Virtual Cell Atlas, and HubMAP, and make their datasets and entities queryable through easy-to-use open-source Python & R libraries.
Instead of navigating fragmented dataset conventions, you can now query for genes, cell types, or perturbations from a single interface.

## Validate & annotate datasets

...

## Who uses it?

Organizations across pharma, biotech, and academia are already using Lamin to create these training feedback loops, including:

- Pfizer – A global BigPharma company with headquarters in the US
- Ensocell Therapeutics – A BioTech with offices in Cambridge, UK, and California
- DZNE – The National Research Center for Neuro-Degenerative Diseases in Germany
- Helmholtz Munich – The National Research Center for Environmental Health in Germany
- The Global Immunological Swarm Learning Network – Research hospitals at U Bonn, Harvard, MIT, Stanford, ETH Zürich, Charite, Mount Sinai, and others

> All is data. -- [Barney Glaser (1978)](https://en.wikipedia.org/wiki/Grounded_theory) <br>

## Thanks to

Zavain Dar, Adam Goulburn & Nan Li from Dimension led our seed investment round in September 2022 and have actively supported us ever since. They previously backed companies like Recursion & HuggingFace. Surbhi Sarna & Jared Friedman from YC believed in us even before a meaningful line of code was written. Pillar VC, Pioneer Fund, and our angel investors Aaron Kimball, Alec Nielsen, Jeff Hammerbacher, and Oskari Saarenmaa completed the seed investment.

We’re grateful to those people & organizations maintaining the open infrastructure on which Lamin is built. First and foremost, that’s Postgres, Django, and fsspec. We should also mention big data storage formats including parquet, HDF5, zarr, tiledbsoma, and of course AnnData & SpatialData. And web technologies like FastAPI, Svelte, and Supabase.

We're deeply grateful to our early customers for their patience and feedback, our team for relentlessly building the platform, and everyone who supported us along the way. We hope to feature their many names and contributions in upcoming posts.

## Author contributions

`*` These authors contributed equally.

## References

[^anthropic-agents]: Luebbert L et al. (2026). Paving the way for agents in biology. [Anthropic Research](https://www.anthropic.com/research/agents-in-biology).

[^schmidt22]: https://pubmed.ncbi.nlm.nih.gov/35113687/ "Schmidt R, Steinhart Z, Layeghi M, Freimer JW, Bueno R, Nguyen VQ, Blaeschke F, Ye CJ, Marson A. CRISPR activation and interference screens decode stimulation responses in primary human T cells. Science. 2022."

[^pillai26]: Pillai R, Rasmussen A, Jain I, Sun S, Rybakov S & Wolf A (2026). Agentic variant analysis of the 1000 Genomes Project using Polars, DuckDB, and lakehouses. Lamin Blog. https://blog.lamin.ai/1000genomes

[^symbolic-memory]: Wolf A (2026). Symbolic memory for biological R&D. Lamin Blog. https://blog.lamin.ai/symbolic-memory

[^anndata]: Virshup I, Rybakov S, Theis FJ, Angerer P & Wolf FA (2021). anndata: Annotated data. bioRxiv. https://doi.org/10.1101/2021.12.16.473007

[^spatialdata]: Marconato, L., Palla, G., Yamauchi, K.A. et al. SpatialData: an open and universal data framework for spatial omics. Nat Methods 22, 58–62 (2025).

[^spatialdata-blog]: Heumos L, Namsaraeva A, Treis T, Keller M, Vierdag WM, Marconato L, Zimmermann L, Sunny S & Wolf A (2026). Managing spatial omics datasets with SpatialData & LaminDB. Lamin Blog. https://blog.lamin.ai/spatialdata

[^mapped-collection]: Rybakov S, Fischer F, Wiatrak M, Gold I, Rosen Y, Sun S, Sriworarat C, Theis F, Kalfon J & Wolf A (2024). MappedCollection: Weighted random sampling from large collections of scRNA-seq datasets. Lamin Blog. https://blog.lamin.ai/mapped-collection

[^annbatch]: Fischer F, Gold I, Theis F & Wolf A (2026). Scaling anndata training to the terabyte scale with annbatch. Lamin Blog. https://blog.lamin.ai/annbatch

[^crane26]: Crane J (2026). An AI Agent Just Destroyed Our Production Data. It Confessed in Writing. X. https://x.com/lifeofjer/article/2048103471019434248

[^treybig26]: Treybig D (2026). How Agents Use Systems Differently. Substack. https://davistreybig.substack.com/p/how-agents-use-systems-differently

[^marx21]: Marx V (2021). Method of the Year: spatially resolved transcriptomics. Nat Methods 18, 9. https://doi.org/10.1038/s41592-020-01033-y
