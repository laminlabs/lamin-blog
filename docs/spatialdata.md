---
title: "Managing spatial omics data with SpatialData & LaminDB"
date: 2026-04-13
author: Zethson, namsaraeva, timtreis, keller-mark, melonora, LucaMarconato, zimea, falexwolf
affiliation:
  Zethson: Lamin Labs, Munich
  namsaraeva: Lamin Labs, Munich
  timtreis: Helmholtz Munich, Munich
  keller-mark: Harvard University, Boston
  melonora: EMBL Heidelberg, Heidelberg
  LucaMarconato: EMBL Heidelberg, Heidelberg
  zimea: Helmholtz Munich, Munich
  falexwolf: Lamin Labs, Munich
tweet: TBD
linkedin: TBD
---

Spatial omics technologies — Xenium, Visium, MERFISH, seqFISH, and others — are generating datasets that combine molecular profiling with spatial coordinates.
The [SpatialData](https://github.com/scverse/spatialdata) framework[^marconato25] provides a unified data format for these heterogeneous datasets: images, segmentation masks, point clouds, shapes, and count tables, all stored in a single `.zarr` store.
But as spatial datasets accumulate across experiments, technologies, and labs, querying, finding them, and training models on them become a challenge. LaminDB's cross-dataset queries & validation can now fill this gap with the new support for `SpatialData`.

## Querying spatial datasets by biological metadata

Every SpatialData `.zarr` stored in LaminDB is a queryable `Artifact` annotated with biological & operational metadata.
This means you can query datasets by tissue, assay, disease, cell type, projects, source code, etc. — without knowing file paths or folder structures:

:::::{tab-set}

::::{tab-item} By strings

```python
import lamindb as ln

db = ln.DB("laminlabs/lamindata")

# pass strings to keyword arguments that map on features
xenium_lung = db.Artifact.filter(
    assay="Xenium Spatial Gene Expression",
    tissue="lung",
)
xenium_lung.to_dataframe()
```

::::

::::{tab-item} Via expressions

```python
import lamindb as ln

db = ln.DB("laminlabs/lamindata")

# query feature objects and construct expressions
xenium_lung = db.Artifact.filter(
    ln.Feature.get(name="assay") == "Xenium Spatial Gene Expression",
    ln.Feature.get(name="tissue") == "lung",
)
xenium_lung.to_dataframe()
```

::::

::::{tab-item} Via ontology lookups

```python
import lamindb as ln
import bionty as bt

db = ln.DB("laminlabs/lamindata")

# query ontological records to create an expression
xenium_lung = db.Artifact.filter(
    ln.Feature.get(name="assay") == bt.ExperimentalFactor.get(name="Xenium Spatial Gene Expression"),
    ln.Feature.get(name="tissue") == bt.Tissue.get(name="lung"),
)
xenium_lung.to_dataframe()
```

::::

:::::

This returns all Xenium datasets in the connected database that characterize lung tissue.

## Loading and analyzing spatial data

Once you've found a dataset, loading it into a `SpatialData` object is one line:

```python
sdata = xenium_lung[0].load()
```

which looks like:

```
SpatialData object, with associated Zarr store: /home/user/.cache/lamindb/lamindata/xenium/2.0.0/Xenium_V1_humanLung_Cancer_FFPE_outs.sdata.zarr
├── Images
│     ├── 'he_image': DataTree[cyx] (3, 45087, 11580), (3, 22543, 5790), (3, 11271, 2895), (3, 5635, 1447), (3, 2817, 723)
│     └── 'morphology_focus': DataTree[cyx] (5, 17098, 51187), (5, 8549, 25593), (5, 4274, 12796), (5, 2137, 6398), (5, 1068, 3199)
├── Labels
│     ├── 'cell_labels': DataTree[yx] (17098, 51187), (8549, 25593), (4274, 12796), (2137, 6398), (1068, 3199)
│     └── 'nucleus_labels': DataTree[yx] (17098, 51187), (8549, 25593), (4274, 12796), (2137, 6398), (1068, 3199)
├── Points
│     └── 'transcripts': DataFrame with shape: (<dask_expr.expr.Scalar: expr=ReadParquetFSSpec(f1038c4).size() // 11, dtype=int64>, 11) (3D points)
├── Shapes
│     ├── 'cell_boundaries': GeoDataFrame shape: (162254, 1) (2D shapes)
│     ├── 'cell_circles': GeoDataFrame shape: (162254, 2) (2D shapes)
│     └── 'nucleus_boundaries': GeoDataFrame shape: (156628, 1) (2D shapes)
└── Tables
      └── 'table': AnnData (154472, 377)
with coordinate systems:
    ▸ 'global', with elements:
        he_image (Images), morphology_focus (Images), cell_labels (Labels), nucleus_labels (Labels), transcripts (Points), cell_boundaries (Shapes), cell_circles (Shapes), nucleus_boundaries (Shapes)
```

The resulting object integrates seamlessly with the scverse ecosystem.
You can visualize H&E images and segmentation masks with [spatialdata-plot](https://github.com/scverse/spatialdata-plot), run spatial analyses with [squidpy](https://github.com/scverse/squidpy), apply standard [scanpy](https://github.com/scverse/scanpy) workflows to the count matrix in `sdata.tables["table"]`, and use any other scverse ecosystem package.

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
<img width="800" src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/PMPKWayCU7fa8o9R0000.svg">
</div>

The `AnnData` table embedded in SpatialData stores the expression matrix alongside cell-level annotations:

```python
sdata.tables["table"]
```

gives us:

```
AnnData object with n_obs × n_vars = 154472 × 377
    ...
    obs: 'cell_id', 'transcript_counts', 'control_probe_counts', 'control_codeword_counts', ...
    var: 'gene_ids', 'feature_types', 'genome', 'n_cells_by_counts', ...
    uns: 'umap', 'pca', 'spatialdata_attrs', 'leiden', 'neighbors', 'log1p'
    obsm: 'X_umap', 'spatial', 'X_pca'
    varm: 'PCs'
    layers: 'counts'
    obsp: 'connectivities', 'distances'
```

## Curating and ingesting spatial data

LaminDB provides `Artifact.from_spatialdata()` and a `SpatialDataCurator` for validated ingestion.
The curator validates table metadata against ontology-backed registries — ensuring gene IDs, cell types, diseases, and assays are standardized before data enters your instance.

```python
import lamindb as ln

sdata_schema = ln.Schema.get(name="my_spatial_schema")
curator = ln.curators.SpatialDataCurator(sdata, sdata_schema)
curator.validate()

artifact = ln.Artifact.from_spatialdata(
    sdata,
    key="xenium/my_experiment.zarr",
    schema=sdata_schema,
).save()

artifact.describe()
```

The resulting artifact stores the full SpatialData `.zarr` — images, labels, shapes, points, and tables — as a single tracked unit.
Its `.describe()` output shows dataset features from the table's `obs` and `var`, external features like assay and disease, and all linked ontology labels.

<div style="text-align: center">
<img width="800" src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/0gtAqs1IBzHZ0m8t0000.png">
</div>

## Interactive visualization with Vitessce

LaminDB integrates with [Vitessce](https://vitessce.io/) for interactive spatial visualization directly on LaminHub in your browser.
After saving a SpatialData artifact, you can configure a Vitessce dashboard and attach it:

```python
from vitessce import VitessceConfig, AnnDataWrapper

vc = VitessceConfig(schema_version="1.0.18", name="Xenium Lung")
dataset = vc.add_dataset(name="lung").add_object(
    AnnDataWrapper(adata_artifact=artifact, ...)
)
# ... configure views ...

artifact.save_vitessce_config(vc)
```

Once saved, a **Vitessce** button appears next to the artifact on LaminHub, enabling collaborators to explore the spatial data interactively — no downloads required.
When viewed, it looks like:

<div style="text-align: center">
<img width="800" src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/0AMvLfVX9VXVbhUf0000.png">
</div>

For a full walkthrough, see the [Vitessce: SpatialData guide](https://docs.lamin.ai/vitessce2).

## Training ML models on spatial data

SpatialData's `ImageTilesDataset` creates a PyTorch-compatible dataset by tiling images around spatial coordinates.
Combined with LaminDB's artifact tracking, you get a complete lineage from raw spatial data through tiled training sets to model checkpoints.

```python
from spatialdata.dataloader.datasets import ImageTilesDataset

import torchvision.transforms as v2

tile_transform = v2.Compose([
    v2.ToTensor(),
])

tiles_dataset = ImageTilesDataset(
    sdata=sdata,
    regions_to_images={"cell_circles": "he_image"},
    regions_to_coordinate_systems={"cell_circles": "global"},
    tile_dim_in_units=128,
    tile_scale=1.0,
    transform=tile_transform,
)
```

This dataset plugs directly into PyTorch Lightning for training spatial models — for example, cell type classifiers using DenseNet on image tiles.
See the [spatial ML guide](https://docs.lamin.ai/spatial4) for a full example.

## The `scverse/spatialdata-db` instance

A curated collection of public SpatialData datasets is available at [`scverse/spatialdata-db`](https://lamin.ai/scverse/spatialdata-db).
This instance provides ready-to-query spatial datasets in standardized format — useful for benchmarking, method development, or as reference atlases.

## Code & data availability

- The code snippets of this post: https://lamin.ai/laminlabs/lamindata/transform/PqAYAQzVm8ml0000
- Spatial guide: [docs.lamin.ai/spatial](https://docs.lamin.ai/spatial)
- Vitessce integration: [docs.lamin.ai/vitessce2](https://docs.lamin.ai/vitessce2) & [blog.lamin.ai/vitessce](https://blog.lamin.ai/vitessce)
- Curate & ingest guide: [docs.lamin.ai/spatial3](https://docs.lamin.ai/spatial3)
- Spatial ML training: [docs.lamin.ai/spatial4](https://docs.lamin.ai/spatial4)
- Public spatial datasets: [lamin.ai/scverse/spatialdata-db](https://lamin.ai/scverse/spatialdata-db)
- SpatialData framework: [github.com/scverse/spatialdata](https://github.com/scverse/spatialdata)

## Author contributions

Lukas designed the integration, developed the `SpatialDataCurator`, the initial spatial guides, and helped implement scverse/spatialdata-db.
Altana Namsaraeva improved the spatial guides.
Tim Treis [implemented the necessary `get_attrs`](https://github.com/scverse/spatialdata/pull/806) helper function to access shared metadata, is the lead author of spatialdata-plot, and registered datasets in [spatialdata-db](https://lamin.ai/scverse/spatialdata-db).
Mark Keller develops the Vitessce framework and helped bring the visualizations to life.
Wouter-Michiel Vierdag improved cloud support of the SpatialData framework.
Luca Marconato develops the SpatialData framework and provided implementation guidance.
Lea Zimmermann implemented the scverse/spatialdata curation schema and registered datasets in [spatialdata-db](https://lamin.ai/scverse/spatialdata-db).
Alex supervised the work.

## Citation

```
Heumos L, Namsaraeva A, Treis T, Keller M, Vierdag WM, Marconato L, Zimmermann L & Wolf A (2026). Managing spatial omics data with SpatialData & LaminDB. Lamin Blog.
https://blog.lamin.ai/spatialdata
```

[^marconato25]: Marconato, L., Palla, G., Yamauchi, K.A. et al. SpatialData: an open and universal data framework for spatial omics. Nat Methods 22, 58–62 (2025).
