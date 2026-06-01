---
title: "Querying the 300k artifacts and 1.4B cells of the Arc Virtual Cell Atlas with a simple API & UI"
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

The [Arc Virtual Cell Atlas](https://arcinstitute.org/tools/virtualcellatlas) brings together two large scRNA-seq resources—[scBaseCount](https://github.com/ArcInstitute/arc-virtual-cell-atlas/tree/main/scBaseCount) and [Tahoe-100M](https://github.com/ArcInstitute/arc-virtual-cell-atlas/tree/main/tahoe-100M)—hosted on Google Cloud ([`gs://arc-institute-virtual-cell-atlas`](https://github.com/ArcInstitute/arc-virtual-cell-atlas))[^youngblut25][^zhang25]. Arc documents how to access the files in their [GitHub tutorials](https://github.com/ArcInstitute/arc-virtual-cell-atlas) (Python notebooks under each dataset folder).

On [LaminHub](https://lamin.ai/laminlabs/arc-virtual-cell-atlas) we catalog the same files: we **do not copy or rewrite** the upstream `.h5ad` or parquet objects on GCS. We **register** them as LaminDB **artifacts** (pointers to the original paths) and **annotate** them with metadata from the source so you can search and filter before download.

```{note}

This is a post in a series of posts on biological data atlases.

```

The step-by-step tutorial lives in the [Lamin docs](https://docs.lamin.ai/arc-virtual-cell-atlas).

## What the Lamin catalog adds

Arc’s tutorials focus on listing and opening files from GCS—for example by organism folder or plate. That works well when you already know the path. It is harder to ask cross-cutting questions (“all human brain scBaseCount files with `GeneFull_Ex50pAS` counts”) without scanning directories or loading metadata yourself.

Lamin adds a query layer on top of the unchanged GCS layout:

1. **Register** each file as an artifact keyed to its GCS path (see all registered artifacts on the [artifacts page](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/artifacts)).
2. **Annotate** each artifact by linking it to standardized metadata records and, for h5ads, registered **schemas** that document `obs` and `var` features (see [Annotations we attach](#annotations-we-attach)). You can filter in the UI or API (for example `organisms=human`, `tissues=brain`) without parsing filenames or loading matrices.
3. **Query** via SQL-backed `db.Artifact.filter(...)` or the LaminHub UI, then `.cache()` / `.open()` the same GCS objects Arc ships.

### Annotations we attach

Annotations follow what Arc publishes in sample sheets, parquet metadata, and `obs` schemas. Typical filter dimensions include:

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

Tahoe also registers an `obs_metadata.parquet` artifact for bulk cell-level fields (`plate`, `BARCODE_SUB_LIB_ID`, `drug`, …) as in the [Tahoe README](https://github.com/ArcInstitute/arc-virtual-cell-atlas/blob/main/tahoe-100M/README.md).

#### Schemas

Beyond the catalog annotations in the table, each `.h5ad` can carry a registered **schema** that documents its internal structure. A schema lists **features** (column names) and their **data types**—the same information you would see in `adata.obs` and `adata.var`, but stored in LaminDB so you can inspect it without opening the file.

For **AnnData** artifacts, an AnnData schema has two slots:

- **`obs`** — per-cell metadata (for example `srx_accession`, `tissue`, `gene_count` in scBaseCount, or `plate`, `drug`, `cell_line` in Tahoe).
- **`var`** — per-gene metadata (for example gene identifiers and feature types).

**scBaseCount** uses `scBaseCount_obs_schema` for sample-level fields from Arc’s [metadata documentation](https://github.com/ArcInstitute/arc-virtual-cell-atlas/blob/main/scBaseCount/README.md#metadata), plus per-organism AnnData schemas such as `scBaseCount_Homo_sapiens_anndata_schema` for the `obs` and `var` slots inside each release’s h5ads.

**Tahoe-100M** uses `tahoe100_obs_schema` and `tahoe100_var_schema` for cell- and gene-level columns described in the [Tahoe README](https://github.com/ArcInstitute/arc-virtual-cell-atlas/blob/main/tahoe-100M/README.md).

To preview what is on a registered h5ad without loading it into memory:

```python
artifact = db.Artifact.get("...")  # uid from a query
artifact.describe()
```

`describe()` prints linked annotations, the schema (including `obs` and `var` features), and storage details. Browse all registered schemas on LaminHub: [Schemas](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/schemas).

## How the instance is organized

On LaminHub, the catalog is organized around **artifacts** and **collections**. Two **projects** separate the source programs: [Tahoe-100M](https://biorxiv.org/10.1101/2025.02.20.639398) and [scBaseCount](https://arcinstitute.org/manuscripts/scBaseCount).

### Artifacts

An **artifact** is a registered object on Arc’s GCS bucket, left in place—most often a single file (`.h5ad` count matrix, `.parquet` metadata), but sometimes a **folder** (for example a STAR reference genome under `star_references/<organism>/`, registered for the `2026-01-12` release). The catalog stores the GCS path, size, and hash. Annotated h5ads and parquet files also link to standardized metadata (organism, tissue, and the fields in the table above).

**scBaseCount releases.** Arc publishes two scBaseCount snapshots on GCS, both registered as artifacts:

| `version_tag`    | Arc release                                                                                                                                            | Scale (approx.)                                       |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------- |
| **`2026-01-12`** | [Publication release](https://github.com/ArcInstitute/arc-virtual-cell-atlas/blob/main/scBaseCount/README.md#2026-01-12-publication-release) (current) | \>502M cells, 27 organisms, 5 STARsolo count features |
| **`2025-02-25`** | [Initial release](https://github.com/ArcInstitute/arc-virtual-cell-atlas/blob/main/scBaseCount/README.md#2025-02-01-initial-release)                   | \>230M cells, 21 organisms                            |

Each scBaseCount artifact carries a **`version_tag`** for one of these releases. Filter on `version_tag` in queries to pick a release, or use `is_latest=True` for the current one. Paths look like `scbasecount/<version>/h5ad/...` on `gs://arc-institute-virtual-cell-atlas`. Tahoe-100M is a single GCS snapshot (`2025-02-25`); its artifacts are not versioned this way.

Browse all artifacts on the [artifacts page](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/artifacts).

### Collections

**Collections** group artifacts the same way Arc groups folders on GCS. They are the main entry point when you already know the slice you want.

**Tahoe-100M:** one collection, [`tahoe100`](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/collection/BpavRL4ntRTzWEE5), with the 14 plate-level `.h5ad` files (plus related parquet artifacts such as `obs_metadata.parquet`).

**scBaseCount (`2026-01-12`, current):** **135 collections**—one per organism × STARsolo count feature (27 × 5). Keys mirror the upstream layout:

```text
scBaseCount/<count_feature>/<Organism>
```

For example [`scBaseCount/GeneFull_Ex50pAS/Homo_sapiens`](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/collections). Count features are `Gene`, `GeneFull`, `GeneFull_Ex50pAS`, `GeneFull_ExonOverIntron`, and `Velocyto`. The older **`2025-02-25`** release remains available as artifacts (filter by `version_tag`); collection keys for that release follow the same pattern under the earlier folder on GCS.

See all collections on LaminHub: [Collections](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/collections).

## Querying and browsing

Metadata filters run against the LaminDB catalog, so you can list matching artifacts without downloading matrices. On [LaminHub](https://lamin.ai/laminlabs/arc-virtual-cell-atlas), open the **Artifacts** page and combine filters on the annotations from the table above—organism, tissue, project, count feature, and others—to narrow the catalog before download. The screenshot below shows an example query in the UI (human artifacts in brain tissue).

<div style="text-align: center">
<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/zLm6239ndakZStoi0000.png" width="700" alt="LaminHub artifacts page filtered by organism and tissue metadata" style="padding: 0;">
</div>

In Python, the same filters apply via `db.Artifact.filter(...)`. Use `artifact.describe()` to inspect annotations and schemas on a single h5ad before you load it into memory.

## Other atlases on Lamin

This mirror sits alongside other hosted atlases (CELLxGENE, HuBMAP, and others). The same `lamindb` connection pattern and similar annotation conventions apply across instances, which helps when you combine datasets from more than one source.

## Getting Started

Connecting to the atlas and querying for datasets with `lamindb`:

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

After you pick artifacts, load them with `.cache()`, `.load()`, or `.open()`—the same AnnData objects you would get from Arc’s [Python tutorials](https://github.com/ArcInstitute/arc-virtual-cell-atlas), without an extra copy step on our side. For Tahoe workflows that start from `obs_metadata.parquet`, see the [Lamin docs tutorial](https://docs.lamin.ai/arc-virtual-cell-atlas).

## Next steps

- Read Arc’s upstream docs: [repository overview](https://github.com/ArcInstitute/arc-virtual-cell-atlas), [scBaseCount](https://github.com/ArcInstitute/arc-virtual-cell-atlas/tree/main/scBaseCount), [Tahoe-100M](https://github.com/ArcInstitute/arc-virtual-cell-atlas/tree/main/tahoe-100M).
- Browse [Collections](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/collections) and [Artifacts](https://lamin.ai/laminlabs/arc-virtual-cell-atlas/artifacts) on LaminHub.
- Run the API example above, then the [Lamin tutorial](https://docs.lamin.ai/arc-virtual-cell-atlas).

## References

[^youngblut25]: Youngblut ND et al. (2025). scBaseCount: an AI agent-curated, uniformly processed, and continually expanding single cell data repository. [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.02.27.640494).

[^zhang25]: Zhang JQ et al. (2025). Tahoe-100M: A Giga-Scale Single-Cell Perturbation Atlas for Context-Dependent Gene Function and Cellular Modeling. [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.02.20.639398).
