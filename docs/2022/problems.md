---
title: Key problems of data-heavy R&D
date: 2022-07-31
number: 2
author: sunnyosun, falexwolf
orcid:
  sunnyosun: 0000-0002-2365-0888
  falexwolf: 0000-0002-8760-7838
---

We think that the complexity of modern R&D data often blocks fully realizing the scientific progress it promised.

Here, we list key problems we see and how we think about solving them.

## Data cannot be accessed at all

<!-- prettier-ignore -->
Problem | Description | Solution
--- | --- | ---
_Object storage._ | Data in object storage can't be queried. | Index {term}`observations <observation>` and {term}`variables <variable>` and link them in a query database.
_Pile of data._ | Data can't be accessed as it's not structured and siloed in fragmented infrastructure. | Structure data both by biological entities and by provenance with one interface across storage and database backends.

## Data cannot be accessed at scale

<!-- prettier-ignore -->
Problem | Description | Solution
--- | --- | ---
_Anecdotal data._ | Data can't be accessed at scale as no viable programmatic interfaces exist. | API-first platform.
_Cross-storage integration._ | Molecular (high-dimensional) data can't be efficiently integrated with phenotypic (low-dimensional) data. | Index molecular data with the same biological entities as phenotypic data. Provide connectors for low-dimensional data management systems (ELN & LIMS systems).

## Scientific results are not solid

<!-- prettier-ignore -->
Problem | Description | Solution
--- | --- | ---
_Stand on solid ground._ | Key analytics results cannot be linked to supporting data as too many processing steps are involved. | Provide full data provenance.

## Collaborative science across organizations is hard

<!-- prettier-ignore -->
Problem | Description | Solution
--- | --- | ---
_Siloed infrastructure._ | Data can't be easily shared across organizations. | Federated collaboration hub on distributed infrastructure.
_Siloed semantics._ | External data can't be mapped on in-house data and vice versa. | Provide curation and ingestion API, operate on open-source data models that can be adopted by any organization.

## R&D misses opportunities for higher effectiveness

<!-- prettier-ignore -->
Problem | Description | Solution
--- | --- | ---
_Optimal decision making._ | There is no framework for tracking decision making in complex R&D teams. | Graph of data flow in R&D team, including scientists, computation, decisions, predictions. Unlike workflow frameworks, LaminDB creates an emergent graphs.
_Dry lab is not integrated._ | Data platforms offer no adequate interface for the drylab. | API-first with data scientist needs in mind.
_Support learning._ | There is no support for the learning-from-data cycle. | Support data models across the full lab cycle, including measured → relevant → derived features. Manage knowledge through rich semantic models that map high-dimensional data.

## Data platforms lack support for basic R&D operations

<!-- prettier-ignore -->
Problem | Description | Solution
--- | --- | ---
_Development data._ | Data associated with assay development can't be ingested as data models are too rigid. | Allow partial integrity in LaminDB's implementation of a data lakehouse: ingest data of any curation level and label them with corresponding QC flags.
_Corrupted data._ | Data is often corrupted. | Full provenance allows to trace back corruption to its origin and write a simple fix, typically, in form of an ingestion constraint.

## Building a data platform is hard

<!-- prettier-ignore -->
Problem | Description | Solution
--- | --- | ---
_Aligning data models._ | Data models are hard to align across interdisciplinary stakeholders. | Lamin's data model templates cover 90% of cases, the remaining 10% can be get configured.
_Lock-in._ | Existing platforms lock organizations into specific cloud infrastructure. | Open-source and multi-cloud stack with zero lock-in danger.
_Migrations are a pain._ | Migrating data models in a fast-paced R&D environment can be prohibitive. | LaminDB's schema modules migrate automatically.

_Note: This problem statement was [originally published](https://github.com/laminlabs/lamindb/pull/112) as part of the `lamindb` docs. It remained prominently linked from the about page of lamin.ai while traveling through various repositories with small edits: [within lamindb](https://github.com/laminlabs/lamindb/commits/531202bcbd3e044fd15211cf0abaa3ac65e10a28/docs/notes/problems.md), [within lamin-about](https://github.com/laminlabs/lamin-about/commits/4b530db5e33082ebb612719a5ed57bca67646fd5/profile/problems.md), [within lamin-docs](https://github.com/laminlabs/lamin-docs/commits/main/docs/problems.md)_. It got moved to the blog page on 2023-08-11 and will remain there unmodified.
