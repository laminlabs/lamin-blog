---
title: "Simpler queries for the 2.5B transcriptional profiles of the Arc Virtual Cell Atlas"
date: 2026-06-02
author: sunnyosun, Koncopd, fredericenard, chaichontat, falexwolf
affiliation:
  sunnyosun: Lamin Labs, Munich
  fredericenard: Lamin Labs, NYC
  chaichontat: Lamin Labs, NYC
  Koncopd: Lamin Labs, Munich
  falexwolf: Lamin Labs, Munich
db: https://lamin.ai/laminlabs/arc-virtual-cell-atlas
---

With 2.5B expression profiles that map to about 600M cells, the Arc Virtual Cell Atlas offers the world's largest collection of uniformly processed scRNA-seq datasets.
Arc Institute distributes the atlas as 460k parquet and h5ad files totaling 41TB on Google Cloud Storage.
We present a database mirror that offers queries by entities, a graphical user interface, and zero-copy, lineage-aware sharing of datasets.

For example, you might want to find datasets for human brain samples linked to glioblastoma that were processed with a certain pipeline.
In the original atlas,[^youngblut25] this requires scanning directories and parquet files.
In a database, you can express queries through the entities you care about: the organism, tissue, disease, and the processing pipeline.
The screenshot shows how this works on [lamin.ai/laminlabs/arc-virtual-cell-atlas](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/artifacts):

<div style="text-align: center">
<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/zLm6239ndakZStoi0001.png" width="700" alt="LaminHub artifacts page filtered by organism and tissue metadata" style="padding: 0;">
</div>

The same query can also be expressed in Python or R:

::::::{tab-set}
:::::{tab-item} Python

```python
import lamindb as ln

db = ln.DB("laminlabs/arc-virtual-cell-atlas")

scbase = db.Project.get(name="scBaseCount")
gbm = db.bionty.Disease.get(name="glioblastoma multiforme")
brain = db.bionty.Tissue.get(name="brain")
human = db.bionty.Organism.get(name="human")
factors = db.bionty.ExperimentalFactor.filter(name__in=["10x_Genomics", "3_prime_gex"])
genefull = db.ULabel.get(name="GeneFull_Ex50pAS")

datasets = db.Artifact.filter(
    projects=scbase,
    diseases=gbm,
    tissues=brain,
    organisms=human,
    experimental_factors__in=factors,
    ulabels=genefull,
    is_latest=True,
)
```

:::::
:::::{tab-item} R

```r
library(laminr)
ln <- laminr::import_module("lamindb")

db <- ln$DB("laminlabs/arc-virtual-cell-atlas")

scbase <- db$Project$get(name = "scBaseCount")
gbm <- db$bionty$Disease$get(name = "glioblastoma multiforme")
brain <- db$bionty$Tissue$get(name = "brain")
human <- db$bionty$Organism$get(name = "human")
factors <- db$bionty$ExperimentalFactor$filter(name__in = c("10x_Genomics", "3_prime_gex"))
genefull <- db$ULabel$get(name = "GeneFull_Ex50pAS")

datasets <- db$Artifact$filter(
  projects = scbase,
  diseases = gbm,
  tissues = brain,
  organisms = human,
  experimental_factors__in = factors,
  ulabels = genefull,
  is_latest = TRUE
)
```

:::::
::::::

Queried datasets can then be transfered, loaded, cached, or streamed for cell-level slicing:

::::::{tab-set}
:::::{tab-item} Python

```python
first_dataset = datasets[0]
first_dataset.save()  # zero-copy transfer into your own database
adata = first_dataset.load()  # cache and load into memory
local_filepath = first_dataset.cache()  # cache and return file path
with first_dataset.open() as adata:  # stream slices from cloud storage
    ...
```

:::::
:::::{tab-item} R

```r
first_dataset <- datasets[[1]]
first_dataset$save()  # zero-copy transfer into your own database
adata <- first_dataset$load()  # cache and load into memory
local_filepath <- first_dataset$cache()  # cache and return file path
with(first_dataset$open(), {  # stream slices from cloud storage
  ...
})
```

:::::
::::::

Under the hood, these methods preserve a run object that points back to the original dataset in the Arc database so that downstream processing can be traced back to the source.
For example, [here](https://lamin.ai/laminlabs/arrayloader-benchmarks/artifact/BDttiuV3Te8VB0dU) we used the `.save()` method to sync the `Tahoe-100M` datasets into a benchmarking database for ML data loaders.
The data lineage graph shows the link to the data source:

<div style="text-align: center">
<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/D5nJXInD6i3qMItB0001.png" width="700" alt="LaminHub example of lineage-aware syncing of Tahoe-100M datasets" style="padding: 0;">
</div>

For a detailed walk-through, read the tutorial: [docs.lamin.ai/arc-virtual-cell-atlas](https://docs.lamin.ai/arc-virtual-cell-atlas).

## Entities

The database is organized around entity types that are familiar from single-cell analysis workflows. In LaminDB, these entity types map to biological ontologies and experimental registries through an adaptation of the Django ORM. You can explore them on the UI and in the API reference:

<!-- prettier-ignore -->
Entity (click to explore) | Examples | Source
--- | --- | ---
[`Organism`](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/bionty/organism) | `Homo sapiens`, `Mus musculus`, … | Sample / study metadata
[`Tissue`](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/bionty/tissue) | `brain`, `liver`, … | Sample metadata
[`Disease`](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/bionty/disease) | study-level disease annotations | Sample metadata (see Arc note on study-level disease)
[`CellLine`](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/bionty/cellline) | Cellosaurus IDs, common names | scBaseCount sample fields; Tahoe `cell_line` / `cell_name`
[`ExperimentalFactor`](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/bionty/experimentalfactor) | single-cell vs nucleus, 10x chemistry, … | `lib_prep`, `tech_10x`, `cell_prep`, etc.
[`Compound`](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/pertdb/compound) | compounds, concentrations | `drug`, `drugname_drugconc`
[`Project`](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/projects) | `scBaseCount`, `Tahoe-100M` | Dataset program
[STARsolo count feature](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/ulabel/f2O4a8gq) | `Gene`, `GeneFull_Ex50pAS`, `Velocyto`, … | [scBaseCount feature types](https://github.com/ArcInstitute/arc-virtual-cell-atlas/blob/main/scBaseCount/README.md#starsolo-count-features)
[Release](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/artifacts?filter[and][0][or][0][branch.name][eq]=main&filter[and][1][or][0][is_latest][eq]=true&filter[and][2][or][0][version_tag][eq]=2026-01-12) | `version_tag` e.g. `2026-01-12` | scBaseCount release folder

## Releases

The Arc Virtual Cell Atlas combines two major data resources: `Tahoe-100M`[^zhang25] and `scBaseCount`.[^youngblut25] `scBaseCount` comes with two releases, which we mirror. You can use the `version_tag` to select a release or keep the default of `is_latest=True` to select the latest release. Paths follow `scbasecount/<version>/h5ad/...` on `gs://arc-institute-virtual-cell-atlas`. For Tahoe-100M, the latest release is `2025-02-25`.

<!-- prettier-ignore -->
`version_tag` | Arc release | Scale
--- | --- | ---
**`2026-01-12`** | [Publication release](https://github.com/ArcInstitute/arc-virtual-cell-atlas/blob/main/scBaseCount/README.md#2026-01-12-publication-release) (current) | >502M cells, 27 organisms, 5 STARsolo count features
**`2025-02-25`** | [Initial release](https://github.com/ArcInstitute/arc-virtual-cell-atlas/blob/main/scBaseCount/README.md#2025-02-01-initial-release) | >230M cells, 21 organisms

## Other atlases

[`laminlabs/arc-virtual-cell-atlas`](https://lamin.ai/laminlabs/arc-virtual-cell-atlas) exists alongside [`laminlabs/cellxgene`](https://lamin.ai/laminlabs/cellxgene), [`laminlabs/hubmap`](https://lamin.ai/laminlabs/hubmap), and other public atlases mirrored as LaminDB instances at [lamin.ai/explore](https://lamin.ai/explore), allowing the same query patterns to be reused across multiple resources.

## Code & data availability

- Tutorial: [docs.lamin.ai/arc-virtual-cell-atlas](https://docs.lamin.ai/arc-virtual-cell-atlas)
- DB: [lamin.ai/laminlabs/arc-virtual-cell-atlas](https://lamin.ai/laminlabs/arc-virtual-cell-atlas)
- Repo: https://github.com/ArcInstitute/arc-virtual-cell-atlas

## Acknowledgements

We're grateful to the creators of the original resource[^youngblut25][^zhang25] for sharing it publicly on a scalable storage backend. We're particularly grateful to Nicholas Youngblut for helping with questions regarding the structure of the atlas and reviewing the tutorial.

## Author contributions

Sunny created the database as a mirror of the Arc Virtual Cell Atlas. Sergei developed the data layer, Fred the backend, and Chaichontat the frontend. Alex supervised the project.

## How to cite

Please cite the original references! If the mirror is useful to you, consider citing:

```
Sun S, Rybakov S, Enard F, Sriworarat C & Wolf A (2026). Simpler queries for the 2.5B transcriptional profiles of the Arc Virtual Cell Atlas. Lamin Blog. https://blog.lamin.ai/arc-virtual-cell-atlas
```

## References

[^youngblut25]: Youngblut ND et al. (2025). scBaseCount: an AI agent-curated, uniformly processed, and continually expanding single cell data repository. [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.02.27.640494).

[^zhang25]: Zhang JQ et al. (2025). Tahoe-100M: A Giga-Scale Single-Cell Perturbation Atlas for Context-Dependent Gene Function and Cellular Modeling. [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.02.20.639398).
