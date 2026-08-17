---
title: "Lamin: An open data platform for traceable, multimodal AI"
date: 2026-08-17
author: sunnyosun, Koncopd, Ebad371, sheetalgiri, chaichontat, fredericenard, falexwolf
affiliation:
  sunnyosun: Lamin Labs, Munich
  Koncopd: Lamin Labs, Munich
  Ebad371: Lamin Labs, Munich
  sheetalgiri: Lamin Labs, Munich
  fredericenard: Lamin Labs, NYC
  chaichontat: Lamin Labs, NYC
  falexwolf: Lamin Labs, Munich
---

Today we launch Lamin to the general public! With a single click, anyone can create a database on [lamin.ai](https://lamin.ai/) to build more trustworthy & efficient multimodal AI, no matter where and how you run it.

We started working on Lamin in early 2022 with the idea that computational biology should become more traceable & efficent, in particular in large projects spanning many collaborators and datasets, and ever since serving teams in academia, BioTech, and Big Pharma.
Today, anyone can delegate work to a team of agents, and even a project with a single human might need to keep track of many datasets, analyses, models, and entities.
To our knowledge there is no open-source data management tool that lets you do that.
For example, Jeremie started using LaminDB during his PhD on single-cell foundation models.

> When I start a computational biology project these days, I set up a git repo and a LaminDB instance. It lets me do a lot more, in a reasonable time, in a reproducible way. That's a rare combination in this field. -- [Jeremie Kalfon, ENS Paris & Institut Pasteur](https://www.linkedin.com/feed/update/urn:li:activity:7452778533657014273/)

Here is an example illustrating how traceability matters across a drug discovery project that spans multiple entities and data generation steps -- from a genome-wide screen that reads out IFNG expression in T cells, a marker for their inflammatory response -- to scRNA-seq.[^schmidt22]

```{raw} html
<iframe width="560" height="315" src="https://www.youtube.com/embed/yK3ODFZLL1A?si=Eqn4dBZyFDrbcxvm" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
```

With the exception of closed biological systems – e.g. for modeling structure-based predictions – it has remained notoriously difficult to create large-scale training datasets for biology. This holds in particular for collections of multi-modal omics datasets. Lamin built an open-source data lakehouse that makes it easy to create, manage, and leverage growing biological dataset collections.

To illustrate this, we provide free programmatic access to the world’s largest public collection of single-cell data at lamin.ai/explore. We did not re-curate data for 100s of millions of cells, but instead interface public biological data collections such as CellXGene, HubMAP, or the Arc Virtual Cell Atlas and make their datasets and entities queryable through easy-to-use open-source Python & R libraries. Instead of navigating fragmented dataset conventions, you can now query for genes, cell types, or perturbations from a single interface. If Lamin was a closed web platform rather than an open-source harmonizing access layer for the modern data stack, we could never have built on the work of others simply by interfacing their assets.

So, what is a LaminDB instance? Imagine a “queryable git repository” designed to query, version, and share datasets instead of code. Both are open-source distributed platforms that can run on your laptop or in the cloud, and both track changes. But unlike git, LaminDB lets you query for biological data structures & entities – datasets, genes, proteins, cell types, perturbations, projects, samples – all from your programming language of choice and based on popular open standards like Postgres, SQLite, parquet, zarr, or h5ad.

The more complex dataset collections become, the harder it is to perform reliable reproducible research. Even navigating a single project can become a challenge, leave alone training an AI on all datasets of a large organization, or all of humanities biological datasets. Hence, LaminDB provides data and code traceability, linking your models and analyses to their input datasets.

What makes reproducibility even more challenging is the fact that much of computational biology happens in interactive analyses - notebooks, scripts, ad-hoc queries & model usage - but these analyses often exist in a vacuum, invisible to the organization's broader data flow. While insights emerge from these analyses, the steps that generated them remain inaccessible. Data and code traceability captures these interactive analyses and creates an unprecedented training dataset that helps both humans and AI models learn from every analysis. It closes the training feedback loop across different teams and models, in particular between the wetlab and the drylab.

Screenshot of data lineage graph illustrating how transforms like notebooks, scripts, pipelines, and functions produce artifacts like datasets or models: https://lamin.ai/laminlabs/lamindata/artifact/W1AiST5wLrbNEyVq

Organizations across pharma, biotech, and academia are already using Lamin to create these training feedback loops, including:

Pfizer – A global BigPharma company with headquarters in the US
Ensocell Therapeutics – A BioTech with offices in Cambridge, UK, and California
DZNE – The National Research Center for Neuro-Degenerative Diseases in Germany
Helmholtz Munich – The National Research Center for Environmental Health in Germany
scverse – An international non-profit consortium for open-source omics data tools
The Global Immunological Swarm Learning Network – Research hospitals at U Bonn, Harvard, MIT, Stanford, ETH Zürich, Charite, Mount Sinai, and others

Get started.

Explore datasets at https://lamin.ai/explore, play with the quickstart of the open-source package at https://docs.lamin.ai or request a hosted LaminDB instance to play with LaminHub.

## Thanks to

Zavain Dar, Adam Goulburn & Nan Li from Dimension led our seed investment round in September 2022 and have actively supported us ever since. They previously backed companies like Recursion & HuggingFace. Surbhi Sarna & Jared Friedman from YC believed in us even before a meaningful line of code was written. Pillar VC, Pioneer Fund, and our angel investors Aaron Kimball, Alec Nielsen, Jeff Hammerbacher, and Oskari Saarenmaa completed the seed investment.

We’re grateful to those people & organizations maintaining the open infrastructure on which Lamin is built. First and foremost, that’s Postgres, Django, and fsspec. We should also mention big data storage formats including parquet, HDF5, zarr, tiledbsoma, and of course AnnData & SpatialData. And web technologies like FastAPI, Svelte, and Supabase, which we use to provide access to Postgres connection strings at scale.

We're deeply grateful to our early customers for their patience and feedback, our team for relentlessly building the platform, and everyone who supported us along the way. We hope to feature their many names and contributions in upcoming posts.

## References

[schmidt22]: https://pubmed.ncbi.nlm.nih.gov/35113687/ "Schmidt R, Steinhart Z, Layeghi M, Freimer JW, Bueno R, Nguyen VQ, Blaeschke F, Ye CJ, Marson A. CRISPR activation and interference screens decode stimulation responses in primary human T cells. Science. 2022."
