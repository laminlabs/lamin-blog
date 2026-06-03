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

The Arc Virtual Cell Atlas is the globally largest collection of homogeneously processed scRNA-seq datasets, available as a set of parquet and h5ad files on Google Cloud Storage.
To offer queries by entities, a graphical user interface, and the lineage-aware sharing of datasets, we mirror the 2.5B transcriptional profiles in a LaminDB instance.
The latency for queries across the 460k datasets is subsecond and data and metadata can easily be cached locally for efficient model training.

The file-based access of the original Virtual Cell Atlas[^youngblut25] works well when you already know a file path, for example, an organism or plate folder. Accessing datasets that match a more complicated query like "Give me all count matrices created for human brain tissue and processed with pipeline X”, however, requires scanning directories and parquet files, as described on [github.com/ArcInstitute/arc-virtual-cell-atlas](https://github.com/ArcInstitute/arc-virtual-cell-atlas). This requires using an API that's not applicable in other settings, has rather high latency, and is not possible through a graphical user interface. LaminDB offers a query layer that can be used across many public and inhouse collections, is anchored in general registries for biological ontologies and operational metadata, and comes with a UI.

For example, the following [UI query](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/artifacts?filter[and][0][or][0][branch.name][eq]=main&filter[and][1][or][0][is_latest][eq]=true&filter[and][2][or][0][projects.name][eq]=scBaseCount&filter[and][3][or][0][ulabels.name][eq]=GeneFull_Ex50pAS&filter[and][4][or][0][diseases.name][eq]=glioblastoma%20multiforme&filter[and][5][or][0][experimental_factors.name][eq]=10x_Genomics&filter[and][5][or][1][experimental_factors.name][eq]=3_prime_gex&filter[and][6][or][0][tissues.name][eq]=brain&filter[and][7][or][0][organisms.name][eq]=human) selects count matrices from human brain samples annotated with glioblastoma multiforme and processed to `GeneFull_Ex50pAS` STARsolo count features:

<div style="text-align: center">
<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/zLm6239ndakZStoi0001.png" width="700" alt="LaminHub artifacts page filtered by organism and tissue metadata" style="padding: 0;">
</div>

The same query can be expressed through the Python/R APIs or via an agent prompted with "Give me all count matrices created for human brain tissue, glioblastome multiforme, and processed for feature types GeneFull_Ex50pAS":

::::::{tab-set}
:::::{tab-item} Python

```python
import lamindb as ln

db = ln.DB("laminlabs/arc-virtual-cell-atlas")

scbasecount = db.Project.get(name="scBaseCount")
genefull_ex50pas = db.ULabel.get(name="GeneFull_Ex50pAS")
gbm = db.bionty.Disease.get(name="glioblastoma multiforme")
factors = db.bionty.ExperimentalFactor.filter(name__in=["10x_Genomics", "3_prime_gex"]).all()
brain = db.bionty.Tissue.get(name="brain")
human = db.bionty.Organism.get(name="human")

datasets = db.Artifact.filter(
    projects=scbasecount,
    ulabels=genefull_ex50pas,
    diseases=gbm,
    experimental_factors__in=factors,
    tissues=brain,
    organisms=human,
)
```

:::::
:::::{tab-item} R

```r
library(laminr)
ln <- laminr::import_module("lamindb")

db <- ln$DB("laminlabs/arc-virtual-cell-atlas")

scbasecount <- db$Project$get(name = "scBaseCount")
genefull_ex50pas <- db$ULabel$get(name = "GeneFull_Ex50pAS")
gbm <- db$bionty$Disease$get(name = "glioblastoma multiforme")
factors <- db$bionty$ExperimentalFactor$filter(name__in = c("10x_Genomics", "3_prime_gex"))$all()
brain <- db$bionty$Tissue$get(name = "brain")
human <- db$bionty$Organism$get(name = "human")

datasets <- db$Artifact$filter(
  projects = scbasecount,
  ulabels = genefull_ex50pas,
  diseases = gbm,
  experimental_factors__in = factors,
  tissues = brain,
  organisms = human
)
```

:::::
::::::

Each part of the filter is anchored to a registry entry. This makes the query easier to inspect and debug: `human` is an organism,`brain` is a tissue, `glioblastoma multiforme` is a disease annotation, and `GeneFull_Ex50pAS` is a `STARsolo count feature`. Selected datasets can then be loaded, cached, or streamed:

```python
first_dataset = datasets[0]  # get the first dataset
adata = first_dataset.load()  # cache and load into memory
local_filepath = first_dataset.cache()  # cache and return file path
with first_dataset.open() as adata:  # streaming access
    ...
```

These commands retrieve the selected object while preserving a run record that points back to the original dataset in the Arc database.
This means that downstream processing can be traced back to the source data.

In this [example](https://lamin.ai/laminlabs/arrayloader-benchmarks/artifact/BDttiuV3Te8VB0dU), the same mechanism was used to sync `Tahoe-100M` datasets into a benchmarking database for machine-learning data loaders, including workflows that convert selected inputs to `.zarr` stores for some methods.

<div style="text-align: center">
<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/D5nJXInD6i3qMItB0000.png" width="700" alt="LaminHub example of lineage-aware syncing of Tahoe-100M datasets" style="padding: 0;">
</div>

If you're just looking to filter by project: datasets are annotated by the two projects underlying the original atlas: [Tahoe-100M](https://biorxiv.org/10.1101/2025.02.20.639398)[^zhang25] and [scBaseCount](https://arcinstitute.org/manuscripts/scBaseCount).[^youngblut25] Here is a query for just the Tahoe-100M datasets on the UI:

<div style="text-align: center">
<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/F2BcIAi5eggMVXx40000.png" width="700" alt="LaminHub artifacts page filtered by Tahoe-100M project" style="padding: 0;">
</div>

The same query using the Python API:

```python
import lamindb as ln

db = ln.DB("laminlabs/arc-virtual-cell-atlas")
tahoe100M = db.Project.get(name="Tahoe-100M")
db.Artifact.filter(projects=tahoe100M)
```

In total, the Arc Virtual Cell Atlas hosts around 600M cells, which lead to 2.5B transcriptional profiles through the five different ways of processing for all datasets except the 100M cells of the Tahoe-100M dataset.

The LaminDB instance for the Arc Virtual Cell Atlas is organized around biological and experimental annotations that are familiar from single-cell analysis workflows:

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

Each dataset in LaminDB comes with a schema that maps the entities of above table on the features measured in the dataset, for example, `srx_accession`, `tissue`, `gene_count`, `plate`, `drug`, `cell_line` in addition to the numerical counts. This means you can query datasets by whether they measured a given feature.

The database also offers 135 collections that are stratified by 27 organisms and 5 feature types. For example `scBaseCount/GeneFull_Ex50pAS/Homo_sapiens`, browsable here: [arc-virtual-cell-atlas/collections](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/collections).

[`laminlabs/arc-virtual-cell-atlas`](https://lamin.ai/laminlabs/arc-virtual-cell-atlas) exists alongside CELLxGENE, HuBMAP, and other public atlases mirrored as LaminDB instances, allowing the same query patterns to be reused across multiple resources.

Here is a step-by-step tutorial: [docs.lamin.ai/arc-virtual-cell-atlas](https://docs.lamin.ai/arc-virtual-cell-atlas).

## Code & data availability

- Repo: https://github.com/ArcInstitute/arc-virtual-cell-atlas
- DB: https://lamin.ai/laminlabs/arc-virtual-cell-atlas
- Tutorial: https://docs.lamin.ai/arc-virtual-cell-atlas

## Methods

The [Arc Virtual Cell Atlas](https://arcinstitute.org/tools/virtualcellatlas) combines [scBaseCount](https://github.com/ArcInstitute/arc-virtual-cell-atlas/tree/main/scBaseCount) and [Tahoe-100M](https://github.com/ArcInstitute/arc-virtual-cell-atlas/tree/main/tahoe-100M) — roughly 460k files and on the order of 600 million cells.[^youngblut25] Arc hosts the data on Google Cloud ([`gs://arc-institute-virtual-cell-atlas`](https://github.com/ArcInstitute/arc-virtual-cell-atlas)) and documents access in [GitHub tutorials](https://github.com/ArcInstitute/arc-virtual-cell-atlas) under each dataset folder.

In the LaminDB instance [`laminlabs/arc-virtual-cell-atlas`](https://lamin.ai/laminlabs/arc-virtual-cell-atlas), we register the same objects Arc hosts on GCS: we **do not copy or rewrite** upstream `.h5ad` or parquet files. Each file becomes an **artifact** (a pointer to the original path) with **annotations** for search and filter. [LaminHub](https://lamin.ai/laminlabs/arc-virtual-cell-atlas) is the web UI for that instance—you browse artifacts, collections, and schemas there, or query via the `lamindb` Python API.

The LaminDB mirror was created in 2 steps:

1. **Register** each file as an artifact keyed to its Google Cloud Storage path.
2. **Annotate** each artifact with standardized metadata — and, for h5ads, register **schemas** for `obs` and `var` slots.

Tahoe registers `obs_metadata.parquet` for bulk cell-level fields (`plate`, `BARCODE_SUB_LIB_ID`, `drug`, …); see the [Tahoe README](https://github.com/ArcInstitute/arc-virtual-cell-atlas/blob/main/tahoe-100M/README.md).

**scBaseCount:** `scBaseCount_obs_schema` for [sample-level fields](https://github.com/ArcInstitute/arc-virtual-cell-atlas/blob/main/scBaseCount/README.md#metadata); per-organism AnnData schemas such as `scBaseCount_Homo_sapiens_anndata_schema` for each release’s h5ads.

**Tahoe-100M:** `tahoe100_obs_schema` and `tahoe100_var_schema` for columns in the [Tahoe README](https://github.com/ArcInstitute/arc-virtual-cell-atlas/blob/main/tahoe-100M/README.md).

Preview a registered h5ad without loading it:

```python
artifact = db.Artifact.get("...")  # uid from a query
artifact.describe()
```

`describe()` prints linked annotations, the schema (`obs` and `var` features), and storage details. On LaminHub, open [Schemas](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/schemas) to browse them in the UI.

In this context, an artifact is usually a single registered file such as an `.h5ad` or `.parquet` file. In some cases, an artifact can also be a folder, for example a STAR reference under `star_references/<organism>/` for the `2026-01-12` release. LaminDB stores the path, size, and hash for each artifact, and links annotated files to the metadata entities listed above.

**scBaseCount releases.** Both Arc snapshots are registered:

<!-- prettier-ignore -->
`version_tag` | Arc release | Scale
--- | --- | ---
**`2026-01-12`** | [Publication release](https://github.com/ArcInstitute/arc-virtual-cell-atlas/blob/main/scBaseCount/README.md#2026-01-12-publication-release) (current) | >502M cells, 27 organisms, 5 STARsolo count features
**`2025-02-25`** | [Initial release](https://github.com/ArcInstitute/arc-virtual-cell-atlas/blob/main/scBaseCount/README.md#2025-02-01-initial-release) | >230M cells, 21 organisms

You can use the `version_tag` to select a release or keep the default of `is_latest=True` to select the latest release. Paths follow `scbasecount/<version>/h5ad/...` on `gs://arc-institute-virtual-cell-atlas`. For Tahoe-100M, the latest release is `2025-02-25`.

## References

[^youngblut25]: Youngblut ND et al. (2025). scBaseCount: an AI agent-curated, uniformly processed, and continually expanding single cell data repository. [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.02.27.640494).

[^zhang25]: Zhang JQ et al. (2025). Tahoe-100M: A Giga-Scale Single-Cell Perturbation Atlas for Context-Dependent Gene Function and Cellular Modeling. [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.02.20.639398).
