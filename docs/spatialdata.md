---
title: "Managing spatial omics datasets with SpatialData & LaminDB"
date: 2026-04-13
author: Zethson, namsaraeva, timtreis, keller-mark, melonora, LucaMarconato, zimea, sunnyosun, falexwolf
affiliation:
  Zethson: Lamin Labs, Munich
  namsaraeva: Lamin Labs, Munich
  timtreis: Helmholtz Munich, Munich
  keller-mark: Harvard University, Boston
  melonora: EMBL Heidelberg, Heidelberg
  LucaMarconato: EMBL Heidelberg, Heidelberg
  zimea: Helmholtz Munich, Munich
  sunnyosun: Lamin Labs, Munich
  falexwolf: Lamin Labs, Munich
tweet: TBD
linkedin: TBD
---

Spatial omics technologies — Xenium, Visium, MERFISH, seqFISH, and others — are generating datasets that combine molecular profiling with spatial coordinates.
The [SpatialData](https://github.com/scverse/spatialdata) framework[^marconato25] provides a unified format for these heterogeneous datasets: images, segmentation masks, point clouds, shapes, and count tables, all stored in a single `.zarr` store.
But as spatial datasets accumulate across experiments, technologies, and labs, managing, querying, and training models on them become challenges.
To address these challenges, we have built native SpatialData support into LaminDB, enabling robust cross-dataset queries, validation, and lineage tracking.

## Querying spatial datasets by biological metadata

Every SpatialData `.zarr` stored in LaminDB is a queryable `Artifact` annotated with biological & operational metadata.
This means you can query datasets by tissue, assay, disease, cell type, project, source code, etc. — without knowing file paths or folder structures, but based on registries for the features and entities you care about.

:::::{tab-set}

::::{tab-item} By strings

```python
import lamindb as ln

db = ln.DB("laminlabs/lamindata")

# easiest: pass strings to keyword arguments that map on features
xenium_datasets = db.Artifact.filter(
    assay="Xenium Spatial Gene Expression",
    disease="ductal breast carcinoma in situ",
)
xenium_datasets.to_dataframe()
```

::::

::::{tab-item} Via expressions

```python
import lamindb as ln

db = ln.DB("laminlabs/lamindata")

# more explicit: query the feature registry and construct expressions
xenium_datasets = db.Artifact.filter(
    ln.Feature.get(name="assay") == "Xenium Spatial Gene Expression",
    ln.Feature.get(name="disease") == "ductal breast carcinoma in situ",
)
xenium_datasets.to_dataframe()
```

::::

::::{tab-item} Via ontology lookups

```python
import lamindb as ln
import bionty as bt

db = ln.DB("laminlabs/lamindata")

# very explicit: query ontological registries and construct expressions
xenium_datasets = db.Artifact.filter(
    ln.Feature.get(name="assay") == bt.ExperimentalFactor.get(name="Xenium Spatial Gene Expression"),
    ln.Feature.get(name="disease") == bt.Disease.get(name="ductal breast carcinoma in situ"),
)
xenium_datasets.to_dataframe()
```

::::

:::::

This returns all Xenium datasets in the `laminlabs/lamindata` database that characterize breast carcinoma.

## Understanding the context of a dataset

Let us pick the first dataset in the results and call `.describe()`:

```python
artifact = xenium_datasets[0]
artifact.describe()
```

We can see all metadata, including the notebook that created the dataset [`blog/spatialdata/curate.ipynb`](https://lamin.ai/laminlabs/lamindata/transform/PDKnhPHpxeMU0001):

<div style="text-align: center">
<img width="600" src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/0gtAqs1IBzHZ0m8t0001.png">
</div>

## Loading and analyzing spatial data

Loading the artifact into a `SpatialData` object is one line:

```python
sdata = artifact.load()
```

It looks like:

```
SpatialData object, with associated Zarr store: /Users/falexwolf/Library/Caches/lamindb/lamindata/sample_datasets/xenium1_curated_breast_carcinoma_in_situ.zarr
├── Images
│     ├── 'morphology_focus': DataTree[cyx] (1, 2310, 3027), (1, 1155, 1514), (1, 578, 757), (1, 288, 379), (1, 145, 189)
│     └── 'morphology_mip': DataTree[cyx] (1, 2310, 3027), (1, 1155, 1514), (1, 578, 757), (1, 288, 379), (1, 145, 189)
├── Points
│     └── 'transcripts': DataFrame with shape: (<Delayed>, 8) (3D points)
├── Shapes
│     ├── 'cell_boundaries': GeoDataFrame shape: (1899, 1) (2D shapes)
│     └── 'cell_circles': GeoDataFrame shape: (1812, 2) (2D shapes)
└── Tables
      └── 'table': AnnData (1812, 313)
with coordinate systems:
    ▸ 'aligned', with elements:
        morphology_focus (Images), morphology_mip (Images), transcripts (Points), cell_boundaries (Shapes), cell_circles (Shapes)
    ▸ 'global', with elements:
        morphology_focus (Images), morphology_mip (Images), transcripts (Points), cell_boundaries (Shapes), cell_circles (Shapes)
```

The resulting object integrates with the scverse ecosystem.
For instance, one can visualize H&E images and segmentation masks with [spatialdata-plot](https://github.com/scverse/spatialdata-plot),[^examplebelow] run spatial analyses with [squidpy](https://github.com/scverse/squidpy), apply standard [scanpy](https://github.com/scverse/scanpy) workflows to the count matrix in `sdata.tables["table"]`, and use any other scverse ecosystem package.

```python
import spatialdata_plot

axes = plt.subplots(1, 2, figsize=(10, 10))[1].flatten()
sdata.pl.render_images("he_image", scale="scale4").pl.show(
    ax=axes[0], title="H&E image"
)
sdata.pl.render_images("morphology_focus", scale="scale4").pl.show(
    ax=axes[1], title="Morphology image"
)
```

<div style="text-align: center">
<img width="800" src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/PMPKWayCU7fa8o9R0000.png">
</div>

The `AnnData` table embedded in `SpatialData` stores the expression matrix alongside cell-level annotations:

```python
sdata.tables["table"]
```

gives us:

```
AnnData object with n_obs × n_vars = 1812 × 313
    obs: 'cell_id', 'transcript_counts', 'control_probe_counts', 'control_codeword_counts', 'total_counts', 'cell_area', 'nucleus_area', 'region', 'dataset', 'celltype_major', 'celltype_minor'
    var: 'symbols', 'feature_types', 'genome'
    uns: 'spatialdata_attrs'
    obsm: 'spatial'
```

## Validating `SpatialData` objects

While you can store any `.zarr` folder in LaminDB using the standard {class}`~lamindb.Artifact` constructor, some workflows require stricter data integrity.
To enforce this, LaminDB provides {meth}`~lamindb.Artifact.from_spatialdata` — a specialized constructor that validates the object against a {class}`~lamindb.Schema`.
Because `SpatialData` objects are highly compositional, the `Schema` object allows you to define precise validation rules for specific components:

```python
schema = db.Schema.get(name="spatialdata_blog_schema")
schema.describe()
```

<div style="text-align: center">
<img width="600" src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/KUNmrvM5R1kEOqv60000.png">
</div>

The schema validates metadata against ontology-backed registries — ensuring gene IDs, cell types, diseases, and assays are standardized before a dataset gets ingested. The ingestion then looks like this:

```python
artifact = ln.Artifact.from_spatialdata(
    sdata,
    key="xenium/my_experiment.zarr",
    schema=schema,
).save()
```

Under the hood, this leverages the {class}`~lamindb.curators.SpatialDataCurator` class, which offers helpers for standardization in addition to validation.
For a deeper dive into the richer curation API, see the [curation guide](https://docs.lamin.ai/spatial3).

## Interactive visualization with Vitessce

LaminDB integrates with [Vitessce](https://vitessce.io/) for interactive spatial visualization directly on LaminHub in your browser.
After saving a SpatialData artifact, you can configure a Vitessce dashboard and attach it:

```python
from vitessce import VitessceConfig, SpatialDataWrapper

vc = VitessceConfig(schema_version="1.0.18")
dataset = vc.add_dataset(name="lung").add_object(
    SpatialDataWrapper(sdata_artifact=artifact, ...)
)
# ... configure views ...

ln.integrations.save_vitessce_config(vc)
```

Once saved, a **Vitessce** button appears next to the artifact on LaminHub, enabling collaborators to explore the dataset interactively:

<div style="text-align: center">
<img width="800" src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/0AMvLfVX9VXVbhUf0000.png">
</div>

You can explore such a dashboard [here](https://lamin.ai/laminlabs/lamindata/artifact/8sPWscz3SICG1D8t0000). For a full walkthrough, see the [Vitessce: SpatialData guide](https://docs.lamin.ai/vitessce2).

## Training ML models on spatial data

SpatialData's `ImageTilesDataset` creates a PyTorch-compatible dataset by tiling images around spatial coordinates.
Combined with LaminDB's artifact tracking, you get a complete lineage from raw spatial data through tiled training sets to model checkpoints.

```python
from spatialdata.dataloader.datasets import ImageTilesDataset

tiles_dataset = ImageTilesDataset(
    sdata=sdata,
    regions_to_images={"cell_circles": "he_image"},
    regions_to_coordinate_systems={"cell_circles": "global"},
    tile_dim_in_units=128,
    tile_scale=1.0,
)
```

This dataset plugs directly into PyTorch Lightning for training spatial models — for example, cell type classifiers using DenseNet on image tiles.
See the [spatial ML guide](https://docs.lamin.ai/spatial4) for a full example.

## Acknowledgements: `scverse`

We are grateful for collaborating with `scverse` not only on interoperability but also by supporting a curated collection of public SpatialData datasets at [`scverse/spatialdata-db`](https://lamin.ai/scverse/spatialdata-db).
This database is a work in progress but already today provides validated ready-to-query spatial datasets — useful for benchmarking, method development, model training, and as a reference atlas.

## Code & data availability

- The code snippets & figures of this post: [lamin.ai/laminlabs/lamindata/transform/PqAYAQzVm8ml](https://lamin.ai/laminlabs/lamindata/transform/PqAYAQzVm8ml)
- Spatial guide: [docs.lamin.ai/spatial](https://docs.lamin.ai/spatial)
- Vitessce integration: [docs.lamin.ai/vitessce2](https://docs.lamin.ai/vitessce2) & [blog.lamin.ai/vitessce](https://blog.lamin.ai/vitessce)
- Curate & ingest guide: [docs.lamin.ai/spatial3](https://docs.lamin.ai/spatial3)
- Spatial ML training: [docs.lamin.ai/spatial4](https://docs.lamin.ai/spatial4)
- Public spatial datasets: [lamin.ai/scverse/spatialdata-db](https://lamin.ai/scverse/spatialdata-db)
- SpatialData framework: [github.com/scverse/spatialdata](https://github.com/scverse/spatialdata)

## Author contributions

Lukas created the `SpatialDataCurator` class and usage guides.

Altana overhauled the usage guides.

Tim [implemented a helper function](https://github.com/scverse/spatialdata/pull/806) to access shared metadata, is the lead author of `spatialdata-plot` and provided feedback in the context of his work on [spatialdata-db](https://lamin.ai/scverse/spatialdata-db).

Mark develops the Vitessce framework and advised on topics related to it.

Wouter-Michiel improved cloud support of the SpatialData framework, relevant for a seamless experience with LaminDB, which is typically hosted in the cloud.

Luca develops the SpatialData framework and provided implementation guidance.

Lea provided valuable feedback on designing schemas for SpatialData in the context of her work on [spatialdata-db](https://lamin.ai/scverse/spatialdata-db).

Sunny built use cases and co-supervised the work.

Alex created composable schemas — suitable for validating data formats such as `SpatialData` — and co-supervised the work.

## Citation

```
Heumos L, Namsaraeva A, Treis T, Keller M, Vierdag WM, Marconato L, Zimmermann L, Sunny S & Wolf A (2026). Managing spatial omics datasets with SpatialData & LaminDB. Lamin Blog.
https://blog.lamin.ai/spatialdata
```

[^marconato25]: Marconato, L., Palla, G., Yamauchi, K.A. et al. SpatialData: an open and universal data framework for spatial omics. Nat Methods 22, 58–62 (2025).

[^examplebelow]: The `spatialdata_plot` example displayed is for better effect for a larger object: `sdata = ln.DB("laminlabs/lamindata").get("8sPWscz3SICG1D8t").load()`. See here: https://lamin.ai/laminlabs/lamindata/transform/ZVBwKNxmg0mN. An equivalent plot for the smaller example dataset showcased can be found here: https://lamin.ai/laminlabs/lamindata/transform/PqAYAQzVm8ml.
