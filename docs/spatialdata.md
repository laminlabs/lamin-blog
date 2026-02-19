---
title: "Managing spatial omics data with LaminDB & SpatialData"
date: 2026-02-21
author: Zethson, namsaraeva-altana, treis-tim, keller-mark, vierdag-michiel, marconato-luca, zimmermann-lea, falexwolf
orcid:
  Zethson: 0000-0002-8937-3457
  falexwolf: 0000-0002-8760-7838
affiliation:
  Zethson: Lamin Labs, Munich
  namsaraeva-altana: Lamin Labs, Munich
  treis-tim: Helmholtz Munich, Munich
  keller-mark: Harvard University, Boston
  vierdag-michiel: EMBL Heidelberg, Heidelberg
  marconato-luca: EMBL Heidelberg, Heidelberg
  zimmermann-lea: Helmholtz Munich, Munich
  falexwolf: Lamin Labs, Munich
db: https://lamin.ai/laminlabs/lamindata
repo: https://github.com/laminlabs/lamindb
tweet: TBD
linkedin: TBD
---

---

Spatial omics technologies — Xenium, Visium, MERFISH, seqFISH, and others — are generating datasets that combine molecular profiling with spatial coordinates.
The [SpatialData](https://github.com/scverse/spatialdata) framework (Marconato et al., Nat Methods, 2025) provides a unified in-memory and on-disk representation for these heterogeneous data types: images, segmentation masks, point clouds, shapes, and count tables, all stored in a single `.zarr` container.

But as spatial datasets accumulate across experiments, technologies, and labs, querying, curating, and sharing them becomes a challenge.
LaminDB now provides first-class support for SpatialData — from ingestion and validation to cross-dataset queries, interactive visualization, and ML training.

This post walks through the full integration.

---

## Querying spatial datasets by biological metadata

Every SpatialData `.zarr` stored in LaminDB is a queryable `Artifact`, annotated with biological metadata from ontology-backed registries.
This means you can find datasets by tissue, assay, disease, or cell type — without knowing file paths or folder structures.

```python
import lamindb as ln

db = ln.DB("laminlabs/lamindata")

xenium_lung = db.Artifact.filter(
    assay="Xenium Spatial Gene Expression",
    tissue="lung",
)
xenium_lung.to_dataframe()
```

This returns all Xenium lung datasets in the instance, each with its full metadata context accessible via `.describe()`.

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

![](https://lamin-site-assets.s3.amazonaws.com/.lamindb/PMPKWayCU7fa8o9R0000.svg)

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
curator = ln.curators.SpatialDataCurator(spatialdata, sdata_schema)
curator.validate()

artifact = ln.Artifact.from_spatialdata(
    spatialdata,
    key="xenium/my_experiment.zarr",
    schema=sdata_schema,
).save()

artifact.describe()
```

The resulting artifact stores the full SpatialData `.zarr` — images, labels, shapes, points, and tables — as a single tracked unit.
Its `.describe()` output shows dataset features from the table's `obs` and `var`, external features like assay and disease, and all linked ontology labels.

```
Artifact .zarr/SpatialData
├── General
│   ├── .key = 'xenium/my_experiment.zarr'
│   ├── .size = 7.0 GB
│   ├── .n_files = 1457
│   └── .created_by = namsaraeva
├── Dataset features
│   ├── attrs:bio • 2 [Feature]
│   │   developmental_stage  cat[bionty.DevelopmentalStage]  adult stage
│   │   disease              cat[bionty.Disease]            normal
│   ├── attrs:tech • 1 [Feature]
│   │   assay                cat[bionty.ExperimentalFactor]  Xenium Spatial Gene Expression
│   └── tables:table:obs • ...
└── Labels
    └── .tissues             bionty.Tissue                   lung
```

## Interactive visualization with Vitessce

LaminDB integrates with [Vitessce](https://vitessce.io/) for interactive spatial visualization directly on LaminHub in your browser.
After saving a SpatialData artifact, you can configure a Vitessce dashboard and attach it:

```python
from vitessce import VitessceConfig, AnnDataWrapper

vc = VitessceConfig(schema_version="1.0.16", name="Xenium Lung")
dataset = vc.add_dataset(name="lung").add_object(
    AnnDataWrapper(adata_artifact=artifact, ...)
)
# ... configure views ...

artifact.save_vitessce_config(vc)
```

Once saved, a **Vitessce** button appears next to the artifact on LaminHub, enabling collaborators to explore the spatial data interactively — no downloads required.

For a full walkthrough, see the [Vitessce: SpatialData guide](https://docs.lamin.ai/vitessce2).

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
    transform=tile_transform,
)
```

This dataset plugs directly into PyTorch Lightning for training spatial models — for example, cell type classifiers using DenseNet on image tiles.
See the [spatial ML guide](https://docs.lamin.ai/spatial4) for a full example.

## The `scverse/spatialdata-db` instance

A curated collection of public SpatialData datasets is available at [`scverse/spatialdata-db`](https://lamin.ai/scverse/spatialdata-db).
This instance provides ready-to-query spatial datasets in standardized format — useful for benchmarking, method development, or as reference atlases.

## Code & data availability

- Spatial guide: [docs.lamin.ai/spatial](https://docs.lamin.ai/spatial)
- Vitessce integration: [docs.lamin.ai/vitessce2](https://docs.lamin.ai/vitessce2)
- Curate & ingest guide: [docs.lamin.ai/spatial3](https://docs.lamin.ai/spatial3)
- Spatial ML training: [docs.lamin.ai/spatial4](https://docs.lamin.ai/spatial4)
- Public spatial datasets: [lamin.ai/scverse/spatialdata-db](https://lamin.ai/scverse/spatialdata-db)
- SpatialData framework: [github.com/scverse/spatialdata](https://github.com/scverse/spatialdata)

## Author contributions

Lukas designed the integration, developed the `SpatialDataCurator`, the initial spatial guides, and helped implement scverse/spatialdata-db.
Altana Namsaraeva improved the spatial guides.
Tim Treis [implemented the necessary `get_attrs`](https://github.com/scverse/spatialdata/pull/806) helper function to access shared metadata, is the lead author of spatialdata-plot, and registered datasets in [spatialdata-db](https://lamin.ai/scverse/spatialdata-db).
Mark Keller develops the Vitessce framework and helped bringing the visualizations to life.
Wouter-Michiel Vierdag improved cloud support of the SpatialData framework.
Luca Marconato develops the SpatialData framework and provided implementation guidance.
Lea Zimmermann implemented the scverse/spatialdata curation schema and registered datasets in [spatialdata-db](https://lamin.ai/scverse/spatialdata-db).
Alex supervised the work.

## Citation

```
Heumos L, Namsaraeva A, Treis T, Marconato L & Wolf A (2026). Managing spatial omics data with LaminDB & SpatialData. Lamin Blog.
https://blog.lamin.ai/spatialdata
```
