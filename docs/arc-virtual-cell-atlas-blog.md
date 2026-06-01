---
title: "Simple queries for 2.5B transcriptional profiles in the Arc Virtual Cell Atlas"
date: 2026-05-20
author: sunnyosun, Koncopd, fredericenard, chaichontat, falexwolf
affiliation:
  sunnyosun: Lamin Labs, Munich
  fredericenard: Lamin Labs, NYC
  chaichontat: Lamin Labs, NYC
  Koncopd: Lamin Labs, Munich
  falexwolf: Lamin Labs, Munich
db: https://lamin.ai/laminlabs/arc-virtual-cell-atlas
---

The [Arc Virtual Cell Atlas](https://arcinstitute.org/tools/virtualcellatlas) combines [scBaseCount](https://github.com/ArcInstitute/arc-virtual-cell-atlas/tree/main/scBaseCount) and [Tahoe-100M](https://github.com/ArcInstitute/arc-virtual-cell-atlas/tree/main/tahoe-100M)—roughly 300,000 files and on the order of 1.4 billion cells[^youngblut25][^zhang25]. Arc hosts the data on Google Cloud ([`gs://arc-institute-virtual-cell-atlas`](https://github.com/ArcInstitute/arc-virtual-cell-atlas)) and documents access in [GitHub tutorials](https://github.com/ArcInstitute/arc-virtual-cell-atlas) under each dataset folder.

In the LaminDB instance [`laminlabs/arc-virtual-cell-atlas`](https://lamin.ai/laminlabs/arc-virtual-cell-atlas), we register the same objects Arc hosts on GCS: we **do not copy or rewrite** upstream `.h5ad` or parquet files. Each file becomes an **artifact** (a pointer to the original path) with **annotations** for search and filter. [LaminHub](https://lamin.ai/laminlabs/arc-virtual-cell-atlas) is the web UI for that instance—you browse artifacts, collections, and schemas there, or query via the `lamindb` Python API.

```{note}

This is a post in a series of posts on biological data atlases.

```

The step-by-step tutorial lives in the [Lamin docs](https://docs.lamin.ai/arc-virtual-cell-atlas).

## What LaminDB adds

Arc’s tutorials work well when you already know a GCS path—for example an organism folder or a Tahoe plate. Cross-cutting questions (“all human brain scBaseCount files with `GeneFull_Ex50pAS` counts”) are harder without scanning directories or loading metadata yourself.

The [`laminlabs/arc-virtual-cell-atlas`](https://lamin.ai/laminlabs/arc-virtual-cell-atlas) instance adds a query layer on top of the unchanged GCS layout:

1. **Register** each file as an artifact keyed to its GCS path in that instance.
2. **Annotate** each artifact with standardized metadata—and, for h5ads, registered **schemas** for `obs` and `var` columns (see [Annotations we attach](annotations-we-attach)).
3. **Query** with `db.Artifact.filter(...)` or [LaminHub](https://lamin.ai/laminlabs/arc-virtual-cell-atlas) (for example filter `organisms=human`, `tissues=brain`), then `.cache()` or `.open()` the same objects Arc ships.

(annotations-we-attach)=

### Annotations we attach

These annotations follow what Arc publishes in sample sheets, parquet metadata, and cell-level tables. Typical filter dimensions:

| Dimension                           | Examples                                  | Source                                                                                                                                      |
| ----------------------------------- | ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| **Project**                         | `scBaseCount`, `Tahoe-100M`               | Dataset program                                                                                                                             |
| **ULabel** (STARsolo count feature) | `Gene`, `GeneFull_Ex50pAS`, `Velocyto`, … | [scBaseCount feature types](https://github.com/ArcInstitute/arc-virtual-cell-atlas/blob/main/scBaseCount/README.md#starsolo-count-features) |
| **Organism**                        | `Homo sapiens`, `Mus musculus`, …         | Sample / study metadata                                                                                                                     |
| **Tissue**                          | brain, liver, …                           | Sample metadata                                                                                                                             |
| **Disease**                         | study-level disease annotations           | Sample metadata (see Arc note on study-level disease)                                                                                       |
| **Cell line**                       | Cellosaurus IDs, common names             | scBaseCount sample fields; Tahoe `cell_line` / `cell_name`                                                                                  |
| **Experimental factor**             | single-cell vs nucleus, 10x chemistry, …  | `lib_prep`, `tech_10x`, `cell_prep`, etc.                                                                                                   |
| **Perturbation / compound** (Tahoe) | drugs, concentrations                     | `drug`, `drugname_drugconc`; curated via `pertdb`                                                                                           |
| **Release**                         | `version_tag` e.g. `2026-01-12`           | scBaseCount release folder on GCS                                                                                                           |

Tahoe also registers `obs_metadata.parquet` for bulk cell-level fields (`plate`, `BARCODE_SUB_LIB_ID`, `drug`, …); see the [Tahoe README](https://github.com/ArcInstitute/arc-virtual-cell-atlas/blob/main/tahoe-100M/README.md).

#### Schemas

Each `.h5ad` can also reference a **schema**: a registered list of **features** (column names) and **data types**, matching `adata.obs` and `adata.var` but stored in LaminDB for inspection without opening the file.

AnnData schemas use two slots:

- **`obs`** — per-cell metadata (for example `srx_accession`, `tissue`, `gene_count` in scBaseCount, or `plate`, `drug`, `cell_line` in Tahoe).
- **`var`** — per-gene metadata (gene identifiers, feature types, …).

**scBaseCount:** `scBaseCount_obs_schema` for [sample-level fields](https://github.com/ArcInstitute/arc-virtual-cell-atlas/blob/main/scBaseCount/README.md#metadata); per-organism AnnData schemas such as `scBaseCount_Homo_sapiens_anndata_schema` for each release’s h5ads.

**Tahoe-100M:** `tahoe100_obs_schema` and `tahoe100_var_schema` for columns in the [Tahoe README](https://github.com/ArcInstitute/arc-virtual-cell-atlas/blob/main/tahoe-100M/README.md).

Preview a registered h5ad without loading it:

```python
artifact = db.Artifact.get("...")  # uid from a query
artifact.describe()
```

`describe()` prints linked annotations, the schema (`obs` and `var` features), and storage details. On LaminHub, open [Schemas](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/schemas) to browse them in the UI.

## How `laminlabs/arc-virtual-cell-atlas` is organized

The [instance](https://lamin.ai/laminlabs/arc-virtual-cell-atlas) is organized in LaminDB as **artifacts** and **collections**, grouped under two **projects**: [Tahoe-100M](https://biorxiv.org/10.1101/2025.02.20.639398) and [scBaseCount](https://arcinstitute.org/manuscripts/scBaseCount).

### Artifacts

An **artifact** is a registered object on Arc’s bucket—usually a single file (`.h5ad`, `.parquet`), sometimes a **folder** (for example a STAR reference under `star_references/<organism>/` on the `2026-01-12` release). LaminDB stores path, size, and hash; annotated files link to the metadata in the table above.

**scBaseCount releases.** Both Arc snapshots are registered:

| `version_tag`    | Arc release                                                                                                                                            | Scale (approx.)                                      |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------- |
| **`2026-01-12`** | [Publication release](https://github.com/ArcInstitute/arc-virtual-cell-atlas/blob/main/scBaseCount/README.md#2026-01-12-publication-release) (current) | >502M cells, 27 organisms, 5 STARsolo count features |
| **`2025-02-25`** | [Initial release](https://github.com/ArcInstitute/arc-virtual-cell-atlas/blob/main/scBaseCount/README.md#2025-02-01-initial-release)                   | >230M cells, 21 organisms                            |

Use `version_tag` in queries to pick a release, or `is_latest=True` for the current one. Paths follow `scbasecount/<version>/h5ad/...` on `gs://arc-institute-virtual-cell-atlas`. Tahoe-100M is a single snapshot (`2025-02-25` on GCS) without this versioning.

[Browse artifacts](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/artifacts) in `laminlabs/arc-virtual-cell-atlas`.

### Collections

**Collections** group artifacts like folders on GCS—useful when you already know organism and count feature.

- **Tahoe-100M:** [`tahoe100`](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/collection/BpavRL4ntRTzWEE5) — 14 plate-level `.h5ad` files plus parquet sidecars such as `obs_metadata.parquet`.
- **scBaseCount (`2026-01-12`):** **135 collections** (27 organisms × 5 STARsolo features), keyed `scBaseCount/<count_feature>/<Organism>` — for example [`scBaseCount/GeneFull_Ex50pAS/Homo_sapiens`](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/collections). Features: `Gene`, `GeneFull`, `GeneFull_Ex50pAS`, `GeneFull_ExonOverIntron`, `Velocyto`. The `2025-02-25` release is still available as artifacts (`version_tag`); collections for that release follow the same key pattern on GCS.

[Browse collections](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/collections) in `laminlabs/arc-virtual-cell-atlas`.

## Querying and browsing

Filters run against the `laminlabs/arc-virtual-cell-atlas` instance in LaminDB, so you can list matching artifacts without downloading matrices. On [LaminHub](https://lamin.ai/laminlabs/arc-virtual-cell-atlas) (the UI for that instance), open **Artifacts** and combine metadata filters—organism, tissue, project, count feature, and the rest. The screenshot shows human brain tissue as an example.

<div style="text-align: center">
<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/zLm6239ndakZStoi0000.png" width="700" alt="LaminHub artifacts page filtered by organism and tissue metadata" style="padding: 0;">
</div>

In Python, use the same filters with `db.Artifact.filter(...)`, or `artifact.describe()` on one result before `.cache()` / `.open()`.

## Other atlases on Lamin

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

## Next steps

- Arc upstream: [overview](https://github.com/ArcInstitute/arc-virtual-cell-atlas), [scBaseCount](https://github.com/ArcInstitute/arc-virtual-cell-atlas/tree/main/scBaseCount), [Tahoe-100M](https://github.com/ArcInstitute/arc-virtual-cell-atlas/tree/main/tahoe-100M).
- [`laminlabs/arc-virtual-cell-atlas`](https://lamin.ai/laminlabs/arc-virtual-cell-atlas) on LaminHub: [Artifacts](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/artifacts), [Collections](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/collections), [Schemas](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/schemas).
- Run the example above, then the [Lamin tutorial](https://docs.lamin.ai/arc-virtual-cell-atlas).

## References

[^youngblut25]: Youngblut ND et al. (2025). scBaseCount: an AI agent-curated, uniformly processed, and continually expanding single cell data repository. [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.02.27.640494).

[^zhang25]: Zhang JQ et al. (2025). Tahoe-100M: A Giga-Scale Single-Cell Perturbation Atlas for Context-Dependent Gene Function and Cellular Modeling. [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.02.20.639398).
