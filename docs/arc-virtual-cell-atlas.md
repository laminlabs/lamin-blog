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
To offer queries by entities, a graphical user interace, and the lineage-aware sharing of datasets, we mirror the 2.5B transcriptional profiles in a LaminDB instance.
The latency for queries of the 460k datasets is subsecond and data and metadata can easily be cached locally for efficient model training.

The file-based access of the original Virtual Cell Atlas[^youngblut25] works well when you already know a file path, for example, an organism or plate folder. Accessing datasets that match a more complicated query like "Give me all count matrices created for human brain tissue and processed with pipeline X”, however, requires scanning directories and parquet files, as described on [github.com/ArcInstitute/arc-virtual-cell-atlas](https://github.com/ArcInstitute/arc-virtual-cell-atlas). This requires using an API that's not applicable in other settings, has rather high latency, and is not possible through a graphical user interface. LaminDB offers a query layer that can be used across many public and inhouse collections, is anchored in general registries for biological ontologies and operational metadata, and comes with a UI.

<!-- prettier-ignore -->
Entity (click to explore) | Examples | Source
--- | --- | ---
[`Organism`](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/bionty/organism) | `Homo sapiens`, `Mus musculus`, … | Sample / study metadata
`Tissue` | `brain`, `liver`, … | Sample metadata
[`Disease`](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/bionty/disease) | study-level disease annotations | Sample metadata (see Arc note on study-level disease)
[`CellLine`](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/bionty/cellline) | Cellosaurus IDs, common names | scBaseCount sample fields; Tahoe `cell_line` / `cell_name`
[`ExperimentalFactor`](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/bionty/experimentalfactor) | single-cell vs nucleus, 10x chemistry, … | `lib_prep`, `tech_10x`, `cell_prep`, etc.
[`Compound`](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/pertdb/compound) | compounds, concentrations | `drug`, `drugname_drugconc`
[`Project`](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/projects) | `scBaseCount`, `Tahoe-100M` | Dataset program
[STARsolo count feature](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/ulabel/f2O4a8gq) | `Gene`, `GeneFull_Ex50pAS`, `Velocyto`, … | [scBaseCount feature types](https://github.com/ArcInstitute/arc-virtual-cell-atlas/blob/main/scBaseCount/README.md#starsolo-count-features)
[Release](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/artifacts?filter[and][0][or][0][branch.name][eq]=main&filter[and][1][or][0][is_latest][eq]=true&filter[and][2][or][0][version_tag][eq]=2026-01-12) | `version_tag` e.g. `2026-01-12` | scBaseCount release folder

You can use these entities to query datasets, for example, with this [filter](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/artifacts?filter[and][0][or][0][branch.name][eq]=main&filter[and][1][or][0][is_latest][eq]=true&filter[and][2][or][0][projects.name][eq]=scBaseCount&filter[and][3][or][0][ulabels.name][eq]=GeneFull_Ex50pAS&filter[and][4][or][0][diseases.name][eq]=glioblastoma%20multiforme&filter[and][5][or][0][experimental_factors.name][eq]=10x_Genomics&filter[and][5][or][1][experimental_factors.name][eq]=3_prime_gex&filter[and][6][or][0][tissues.name][eq]=brain&filter[and][7][or][0][organisms.name][eq]=human).

<div style="text-align: center">
<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/zLm6239ndakZStoi0001.png" width="700" alt="LaminHub artifacts page filtered by organism and tissue metadata" style="padding: 0;">
</div>

And here is the same query using the API:

```python
db = ln.DB("laminlabs/arc-virtual-cell-atlas")

human = db.bionty.Organism.get(name="human")
brain = db.bionty.Tissue.get(name="brain")

datasets = db.Artifact.filter(
    organisms=human,
    tissues=brain
)
```

Each dataset in LaminDB comes with a schema that maps the entities on the features measured in the dataset, for example, `srx_accession`, `tissue`, `gene_count`, `plate`, `drug`, `cell_line` in addition to the numerical counts. This means you can query datasets by whether they measured a given feature.

The database groups datasets by the two projects underlying the original atlas: [Tahoe-100M](https://biorxiv.org/10.1101/2025.02.20.639398)[^zhang25] and [scBaseCount](https://arcinstitute.org/manuscripts/scBaseCount).[^youngblut25] Here is a query for just the Tahoe-100M datasets on the UI:

<div style="text-align: center">
<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/F2BcIAi5eggMVXx40000.png" width="700" style="padding: 0;">
</div>

And here is the same query using the API:

```python
import lamindb as ln

db = ln.DB("laminlabs/arc-virtual-cell-atlas")
tahoe100M = db.Project.get(name="Tahoe-100M")
db.Artifact.filter(projects=tahoe100M)
```

The database also offers 135 collections that are stratified by 27 organisms and 5 feature types. For example `scBaseCount/GeneFull_Ex50pAS/Homo_sapiens`, browesable here: [arc-virtual-cell-atlas/collections](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/collections).

## Other biological atlases

[`laminlabs/arc-virtual-cell-atlas`](https://lamin.ai/laminlabs/arc-virtual-cell-atlas) sits alongside CELLxGENE, HuBMAP, and other hosted atlases on Lamin. The same `ln.DB("account/instance")` connection pattern and annotation conventions apply across instances.

## Getting Started

```python
import lamindb as ln

# Connect to the instance
db = ln.DB("laminlabs/arc-virtual-cell-atlas")

# Example query for human brain datasets
organisms = db.bionty.Organism.lookup()
tissues = db.bionty.Tissue.lookup()

h5ads_brain = db.Artifact.filter(
    organisms=organisms.human,
    tissues=tissues.brain
).distinct()

print(h5ads_brain.to_dataframe())
```

After you pick artifacts, load them with `.cache()`, `.load()`, or `.open()`—the same AnnData objects as in Arc’s [Python tutorials](https://github.com/ArcInstitute/arc-virtual-cell-atlas). For Tahoe workflows starting from `obs_metadata.parquet`, see the [Lamin docs tutorial](https://docs.lamin.ai/arc-virtual-cell-atlas).

## Background

The [Arc Virtual Cell Atlas](https://arcinstitute.org/tools/virtualcellatlas) combines [scBaseCount](https://github.com/ArcInstitute/arc-virtual-cell-atlas/tree/main/scBaseCount) and [Tahoe-100M](https://github.com/ArcInstitute/arc-virtual-cell-atlas/tree/main/tahoe-100M)—roughly 300,000 files and on the order of 600 million cells.[^youngblut25] Arc hosts the data on Google Cloud ([`gs://arc-institute-virtual-cell-atlas`](https://github.com/ArcInstitute/arc-virtual-cell-atlas)) and documents access in [GitHub tutorials](https://github.com/ArcInstitute/arc-virtual-cell-atlas) under each dataset folder.

In the LaminDB instance [`laminlabs/arc-virtual-cell-atlas`](https://lamin.ai/laminlabs/arc-virtual-cell-atlas), we register the same objects Arc hosts on GCS: we **do not copy or rewrite** upstream `.h5ad` or parquet files. Each file becomes an **artifact** (a pointer to the original path) with **annotations** for search and filter. [LaminHub](https://lamin.ai/laminlabs/arc-virtual-cell-atlas) is the web UI for that instance—you browse artifacts, collections, and schemas there, or query via the `lamindb` Python API.

The step-by-step tutorial lives in the [Lamin docs](https://docs.lamin.ai/arc-virtual-cell-atlas).

The LaminDB mirror was created like this:

1. **Register** each file as an artifact keyed to its GCS path in that instance.
2. **Annotate** each artifact with standardized metadata—and, for h5ads, registered **schemas** for `obs` and `var` columns.
3. **Query** with `db.Artifact.filter(...)` or [LaminHub](https://lamin.ai/laminlabs/arc-virtual-cell-atlas) (for example filter `organisms=human`, `tissues=brain`), then `.cache()` or `.open()` the same objects Arc ships.

Tahoe registers `obs_metadata.parquet` for bulk cell-level fields (`plate`, `BARCODE_SUB_LIB_ID`, `drug`, …); see the [Tahoe README](https://github.com/ArcInstitute/arc-virtual-cell-atlas/blob/main/tahoe-100M/README.md).

**scBaseCount:** `scBaseCount_obs_schema` for [sample-level fields](https://github.com/ArcInstitute/arc-virtual-cell-atlas/blob/main/scBaseCount/README.md#metadata); per-organism AnnData schemas such as `scBaseCount_Homo_sapiens_anndata_schema` for each release’s h5ads.

**Tahoe-100M:** `tahoe100_obs_schema` and `tahoe100_var_schema` for columns in the [Tahoe README](https://github.com/ArcInstitute/arc-virtual-cell-atlas/blob/main/tahoe-100M/README.md).

Preview a registered h5ad without loading it:

```python
artifact = db.Artifact.get("...")  # uid from a query
artifact.describe()
```

`describe()` prints linked annotations, the schema (`obs` and `var` features), and storage details. On LaminHub, open [Schemas](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/schemas) to browse them in the UI.

An **artifact** is a registered object on Arc’s bucket—usually a single file (`.h5ad`, `.parquet`), sometimes a **folder** (for example a STAR reference under `star_references/<organism>/` on the `2026-01-12` release). LaminDB stores path, size, and hash; annotated files link to the metadata in the table above.

**scBaseCount releases.** Both Arc snapshots are registered:

<!-- prettier-ignore -->
`version_tag` | Arc release | Scale
--- | --- | ---
**`2026-01-12`** | [Publication release](https://github.com/ArcInstitute/arc-virtual-cell-atlas/blob/main/scBaseCount/README.md#2026-01-12-publication-release) (current) | >502M cells, 27 organisms, 5 STARsolo count features
**`2025-02-25`** | [Initial release](https://github.com/ArcInstitute/arc-virtual-cell-atlas/blob/main/scBaseCount/README.md#2025-02-01-initial-release) | >230M cells, 21 organisms

Use `version_tag` in queries to pick a release, or `is_latest=True` for the current one. Paths follow `scbasecount/<version>/h5ad/...` on `gs://arc-institute-virtual-cell-atlas`. Tahoe-100M is a single snapshot (`2025-02-25` on GCS) without this versioning.

## Next steps

- Arc upstream: [overview](https://github.com/ArcInstitute/arc-virtual-cell-atlas), [scBaseCount](https://github.com/ArcInstitute/arc-virtual-cell-atlas/tree/main/scBaseCount), [Tahoe-100M](https://github.com/ArcInstitute/arc-virtual-cell-atlas/tree/main/tahoe-100M).
- [`laminlabs/arc-virtual-cell-atlas`](https://lamin.ai/laminlabs/arc-virtual-cell-atlas) on LaminHub: [Artifacts](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/artifacts), [Collections](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/collections), [Schemas](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/schemas).
- Run the example above, then the [Lamin tutorial](https://docs.lamin.ai/arc-virtual-cell-atlas).

## References

[^youngblut25]: Youngblut ND et al. (2025). scBaseCount: an AI agent-curated, uniformly processed, and continually expanding single cell data repository. [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.02.27.640494).

[^zhang25]: Zhang JQ et al. (2025). Tahoe-100M: A Giga-Scale Single-Cell Perturbation Atlas for Context-Dependent Gene Function and Cellular Modeling. [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.02.20.639398).
