---
title: "The sparse biological feature store as data lakehouse"
date: 2026-03-01
author: jejomath, falexwolf
affiliation:
  jejomath: MergeLogic, Cambridge, MA
  falexwolf: Lamin Labs, Munich
---

One avenue into the future of biotech is scaled learning from multi-modal data.
Given these data easily measure millions of features, they can't be queried through any established data infrastructure.
This note proposes to model the sparse biological feature store as a data lakehouse.

## Multi-modal datasets

Early discovery biotech often feels like stumbling around a dark room with a flashlight: Each assay and experiment provides a narrow slice of insight into a highly complex system with more exceptions than rules.
Multi-modal data such as transcriptomics, proteomics and high-content imaging give researchers additional spotlights, expanding their field of view. But to understand what they’re seeing, they need to stitch these data modalities together into a single coherent whole.
Most biological data consists of large numbers of relatively small datasets from different experiments, assays, labs and protocols. Some are large matrices, such as single-cell gene expression data, with additional annotations on both rows and columns.
Others, such as sequences or image features are more conventional tables with a small number of columns.
Most are annotated with complex, external ontologies or vocabularies linked to additional structured and unstructured metadata. And even datasets that are purportedly the same “type” often have slightly different schemas/structures.
Because of the partially overlapping features between these datasets, they conceptually fit together into a giant, sparse "feature matrix" where each row is an observation and each column could be a numerical measurement, a reference to a shared vocabulary/ontology, or something else.

<div style="text-align: center">
<img width="800" src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/VFFgFdAlJnssyOdk0000.svg">
</div>

To build multi-modal machine learning models, computational biologists need to extract data from this (conceptual) matrix. But because datasets are stored as flat files scattered across different directories and file stores, doing this in practice is complex and time consuming under the best of circumstances. In most circumstances, it makes training ML models across multiple datasets effectively impossible.

## Data lakes and warehouses

General-purpose data storage tools and infrastructure weren’t built for this reality of biological data.
Until recently, the gold standard for managing data at scale was the data warehouse, which extends the paradigm of the classical relational database. But while data warehouses have no problem managing the scale of multi-modal biological data, the problem is the relational paradigm.
Data warehouses expect data to fit into a fixed number of tables with consistent schemas and with new data appended below existing rows, as on the left in the figure below. This works well for data that is collected incrementally through a consistent process. But for batches of biological data from a constantly changing collection of experimental protocols and objectives, it doesn’t work at all.

<div style="text-align: center">
<img width="800" src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/gQW0EWG9iR7ArkJ40000.svg">
</div>

The data lake architecture was introduced for contexts like this that don’t provide enough consistency to use a data warehouse. Data lakes give users complete flexibility to store data of any type in any format. This flexibility has made data lakes the standard solution for multi-modal biological data.
However, the only way data lakes are able to provide this level of flexibility is to completely eliminate structure and consistency. Each dataset becomes its own isolated universe of information, as in the center of the above figure. If you want to connect it to an external ontology or even another dataset in the same format, it’s a completely manual process.
This is part of why computational biologists spend half their time on manual cleaning and integration work.

## The Lakehouse

Data warehouses impose too much structure for multi-modal biological data. Data lakes don’t provide enough. So an intermediate framework, the data lakehouse, was introduced to find a better balance for exactly this kind of situation.
As shown on the right of the previous figure, a data lakehouse functions as a layer on top of a data lake that records structural information about each isolated dataset that can be used to dynamically extract consistently formatted information and integrate it with other datasets, external ontologies and other resources.

This option provides the best of both worlds: enough flexibility to store data from any assay/experiment/protocol that might come up, with enough structure to enable intuitive querying and model training while eliminating manual cleaning and bookkeeping.
But the layer of structure still needs to be designed around the specific characteristics of multi-modal biology data.

LaminDB integrates biological entities via registries holding ontologies & experimental metadata, while hiding engineering details so users can think in terms of the biology. No more looking up ids or manually joining external vocabularies. Lamin takes care of it automatically.

<div style="text-align: center">
<img width="800" src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/Duc60Ut5oykXThEL0001.svg">
</div>

In addition to tabular, `DataFrame`-like data, this works for non-tabular, biological data structures such as `AnnData`, `MuData`, `tiledbsoma` and spatial data.
