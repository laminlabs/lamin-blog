---
title: "How I used LaminDB to build the scPRINT family of models"
date: 2026-04-15
author: jkobject
affiliation:
  jkobject: ENS Ulm
---

At the start of my PhD, I was faced with what seemed like a mountain to climb: build, largely alone, a foundation model for single-cell RNA-seq data. As anyone in the field knows, building the model is not the hard part. Getting the data is.

To train a cell foundation model that actually generalizes, you need thousands of datasets. You need to find them, download them, harmonize gene names across species, align cell type labels to controlled ontologies, preprocess everything consistently, store it in a way that doesn't collapse under its own weight, and feed it to a model at scale. Managing a dozen datasets is already painful for most computational biologists. I needed to handle thousands.

Thirty months ago, three things came at exactly the right moment. The Chan Zuckerberg Initiative had made around 700 datasets easily accessible through CellxGene. Alex Wolf's Lamin.ai project gave me a way to manage large, heterogeneous collections of biological data with metadata that actually meant something. And Sergei Rybakov (now at Lamin) was building a loader for streaming single-cell data at scale.

## Managing scale with LaminDB

The core problem with large-scale single-cell data is not raw file size. It's the metadata. A dataset from a 2019 mouse lung study uses different gene IDs, different tissue labels, and different cell type annotations than a 2023 human heart study. Reconciling these across hundreds of datasets by hand is a losing battle that compounds as the corpus grows.

LaminDB treats biological ontologies as first-class citizens. Every dataset I ingested was linked to standardized terms: Cell Ontology for cell types, Uberon for tissues, NCBI Taxonomy for species. That ontological consistency is what made it possible to build scPRINT-2's hierarchical classification loss, which penalizes predictions based on their distance in the ontology graph rather than just correct/wrong. The loss knows that "T cell" and "CD8-positive T cell" are related in a way that "T cell" and "hepatocyte" are not. That knowledge came from having the data structured correctly from the start.

Without LaminDB I would have spent months on this. With it, it took weeks.

## Streaming 350 million cells

Loading 350 million cells into memory is not an option. You need streaming, shuffling across datasets, and batching that mixes cell types, species, and sequencing technologies, without the dataloader becoming the bottleneck.

scDataloader handles this. It's built on top of LaminDB's MappedCollection interface, which lets you treat hundreds of separate datasets as a single object you can sample, filter, and iterate over. It streams directly from the artifact store and integrates cleanly with PyTorch's DataLoader. I was able to train scPRINT-2 on 350 million cells and 25 TB of data on a single cluster without writing custom data infrastructure. That felt like a minor miracle at the time.

## Beyond training

Once scPRINT was published and colleagues and interns started using the infrastructure, having a LaminDB instance meant they could reproduce my work exactly: same artifacts, same lineage, same ontology mappings. Data lineage made it easy to answer "which datasets went into this version of the model?" or "was this processed before or after the normalization change?" without digging through scripts.

It also meant I could serve processed data to the team with enough context attached that they didn't need me to explain what they were looking at.

## The reflex it created

These days, when I start a computational biology project, I set up a git repo and a LaminDB instance. In that order, roughly. The alternative — an ad hoc folder of CSVs and undocumented preprocessing scripts — is a debt that compounds faster than most people expect.

I used LaminDB throughout my PhD. It let me do a lot alone, in a reasonable time, in a reproducible way. That's a rare combination in this field.
