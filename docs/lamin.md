---
title: "Lamin: An open data platform for traceable, multimodal AI"
date: 2026-08-17
author: sunnyosun, Koncopd, Ebad371, sheetalgiri, chaichontat, fredericenard, falexwolf
affiliation:
  sunnyosun: Lamin Labs, Munich
  Koncopd: Lamin Labs, Munich
  Ebad371: Lamin Labs, Munich
  sheetalgiri: Lamin Labs, Munich
  chaichontat: Lamin Labs, NYC
  fredericenard: Lamin Labs, NYC
  falexwolf: Lamin Labs, Munich
---

Today we're happy to launch Lamin to the general public. With a single click, anyone can create a database on [lamin.ai](https://lamin.ai/) to build more trustworthy and efficient AI, no matter where and how you run it, and in particular in the life sciences.

## Why?

AI had its breakthrough, intelligence has become abundant, but no fundamental innovation has taken place on the memory layer despite a strong need for it given the staggering speed in which AI produces and transforms data in sometimes unreliable and dangerous ways.
It is still git that manages code, it's still markdown that holds notes, it's still the same file systems, databases, warehouses, and lakehouses that hold data, it's still the same ontologies that provide agents with a framework.
People are using these systems in similar ways to how humans have been using them, just at a much higher frequency and scales in a number of ways.
There are also still the same note taking, inventory management, and workspace applications that serve as systems of record -- just that they now allow you to run AI inside these applications.
None of these systems were built for models and humans to manage the complexity of data in a complex domain like biology at these new scale.

We started working on Lamin in early 2022 with the idea that computational biology should become more traceable & efficent.
Some of the underlying problems are fundamental and had already been true for decades.

> There are three kinds of lies: lies, damned lies, and statistics. -- [Mark Twain (1907)](https://en.wikipedia.org/wiki/Lies,_damned_lies,_and_statistics) <br>
> A huge amount of effort is spent cleaning data to get it ready for analysis. -- [Hadley Wickham (2014)](https://www.jstatsoft.org/article/view/v059i10)

But only since everybody started to delegate work to agents they have become painful for a large number of people: Untraceable agentic results cannot be trusted. Agents burn tokens, make mistakes, or fail entirely if unable to efficiently access data. Changes made by agents have a strong need for review.

> The bottleneck for biological agents is the absence of a layer for querying biological data. -- [Laura Luebbert (2026)](https://www.anthropic.com/research/agents-in-biology)

These fundamental problems are particularly severe in the life sciences due to its many different data formats, complex data geenration processes, the high number of concepts needed to define measurements and parametrize datasets across modalities -- it's not just tokens or pixels or a few simple metrics as in other domains -- and the related need for interactive human or agentic analyses, producing non-deterministic data flow.

<div style="text-align: center">
<img width="800px" src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/VFFgFdAlJnssyOdk0001.svg" style="padding: 0;">
</div>

The last decade has brought much innovation in the sophistication and scale of data generation techniques -- in particular scRNA-seq, next-generation sequencing, and high-throughput techqniues.
And it has brought the promise of AI helping to get real value out of it while the world kept building UI-first platforms and ELN systems for biologists wrangling anecdotal data.
So it was clear that a new API-first data management tool for the age of AI was needed, and we built it open-source into the pydata stack, so that you don't have to worry about an ideosyncratic rate-limited REST.

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

Especially drug discovery teams need end-to-end traceability for GxP compliance (21 CFR Part 11 and EU Annex 11). LaminDB allows tracing how information flows through many data transformation steps and across many entities -- from a genome-wide screen that reads out IFNG expression in T cells, a marker for their inflammatory response -- to scRNA-seq and agentic insights about targets and perturbations.[^schmidt22]

```{raw} html
<iframe width="560" height="315" src="https://www.youtube.com/embed/yK3ODFZLL1A?si=Eqn4dBZyFDrbcxvm" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
```

Beyond audibility for trust ("Was this analysis done correctly?"), tracebility also creates context for interpretation ("Has this confounder been corrected for?"), reproducibility ("What were the parameters, the source code, input dataset versions, and the run environment?"), and creates a long-term memory of data operations ("How did we analyze datasets for frozen lung tissue before?"). It's been notoriously difficult to create big training datasets for biology outside of simple systems. Just by using LaminDB, one creates FAIR training data automatically, a bit like when using git to manage the source code of a project.

## Accessing data - lakehouse beyond tables

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

## Unifying records - LIMS & ELN

> A feature is an individual measurable property or characteristic of a data set. [Bishop (2006)](<https://en.wikipedia.org/wiki/Feature_(machine_learning)>)

While models are trained on datasets in storage - be it a local file system or S3 - many workflows require managing data in transactional systems of record.
Most prominently, the electronic lab notebook (ELN) and laboratory inventory management systems (LIMS) used by life scientists to manage experiments and all the entities and notes that surround them.
Mapping data in such an ELN or LIMS system on data that a machine learning scientist would use for model training has historically been a painful process.
We are not aware of any system that would provide that mapping and so all organizations we know use syncing processes that export data from these systems into machine-learning ready formats in storage.
These processes are almost always brittle and almost never provide the detailed context that the original system provided.

So, we built a records framework into a transactional database that's based on the same features that index datasets in the storage of a lakehouse.
Hence, if you export or import between database and storage, there is no mapping and no ambiguity; the columns of an interactive sheet with experimental records map onto the columns of a csv or parquet file.
And similar for other metadata dimensions of other data formats.

The records management experience is similar to popular systems of record:

```{raw} html
<iframe width="560" height="315" src="https://www.youtube.com/embed/NRzVQXJaRH8?si=Eqn4dBZyFDrbcxvm" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
```

## Unifying biological atlases

We provide free programmatic access to the world’s largest public collection of single-cell data at [lamin.ai/explore](https://lamin.ai/explore). We did not re-curate data for 100s of millions of cells, but instead interface public biological data collections such as CellXGene, HubMAP, or the Arc Virtual Cell Atlas and make their datasets and entities queryable through easy-to-use open-source Python & R libraries. Instead of navigating fragmented dataset conventions, you can now query for genes, cell types, or perturbations from a single interface. If Lamin was a closed web platform rather than an open-source harmonizing access layer for the modern data stack, we could never have built on the work of others simply by interfacing their assets.

The more complex dataset collections become, the harder it is to perform reliable reproducible research. Even navigating a single project can become a challenge, leave alone training an AI on all datasets of a large organization, or all of humanities biological datasets. Hence, LaminDB provides data and code traceability, linking your models and analyses to their input datasets.

What makes reproducibility even more challenging is the fact that much of computational biology happens in interactive analyses - notebooks, scripts, ad-hoc queries & model usage - but these analyses often exist in a vacuum, invisible to the organization's broader data flow. While insights emerge from these analyses, the steps that generated them remain inaccessible. Data and code traceability captures these interactive analyses and creates an unprecedented training dataset that helps both humans and AI models learn from every analysis. It closes the training feedback loop across different teams and models, in particular between the wetlab and the drylab.

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

## References

[^anthropic-agents]: Luebbert L et al. (2026). Paving the way for agents in biology. [Anthropic Research](https://www.anthropic.com/research/agents-in-biology).

[^schmidt22]: https://pubmed.ncbi.nlm.nih.gov/35113687/ "Schmidt R, Steinhart Z, Layeghi M, Freimer JW, Bueno R, Nguyen VQ, Blaeschke F, Ye CJ, Marson A. CRISPR activation and interference screens decode stimulation responses in primary human T cells. Science. 2022."

[^pillai26]: Pillai R, Rasmussen A, Jain I, Sun S, Rybakov S & Wolf A (2026). Agentic variant analysis of the 1000 Genomes Project using Polars, DuckDB, and lakehouses. Lamin Blog. https://blog.lamin.ai/1000genomes
