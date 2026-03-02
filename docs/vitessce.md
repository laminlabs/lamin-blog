---
title: "Interactive visualization of multimodal and spatial data with Vitessce"
date: 2026-03-02
author: keller-mark, namsaraeva, falexwolf, chaichontat, sunnyosun
affiliation:
  keller-mark: Harvard Medical School, Boston
  namsaraeva: Lamin Labs, Munich
  falexwolf: Lamin Labs, Munich
  chaichontat: Lamin Labs, NYC
  sunnyosun: Lamin Labs, Munich
db: http://lamin.ai/vitessce/examples
repo: http://github.com/laminlabs/lamin-spatial
---

In this post, we discuss how he open-source tool [Vitessce](https://vitessce.io) and Lamin work together to visualize multimodal and spatial single-cell data.

The key idea is simple: define a Vitessce config in code, save it as an artifact, and share the interactive visualization along with your datasets on LaminHub.

<div style="text-align: center">
<img width="800" src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/rcJQthuZfseneY0m0004.png">
</div>

## Vitessce

Single-cell experiments result in heterogeneous datasets due to several factors: differing profiling techniques (e.g., sequencing-based versus imaging-based), platforms, modalities (e.g., transcriptomics, epigenomics, proteomics, and combinations thereof), and scales (e.g., spot to single-cell to subcellular).
In addition, data pipelines pipelines often add cell type annotations or cell segmentations together with embeddings and other types of information.
Allow interactive visualizing of the rich information evidently helps interpreting key features of datasets be it biologists looking for answers to biological questions, or by machine learning engineers, trying to understand behaviors of outlier datasets.

Vitessce is an open-source JavaScript-based framework for interactive visualization of multimodal and spatial single-cell data. Its dashboard-like views can easily be defined programmatically and then serialized as a JSON artifact. Vitessce then runs serverless anywhere against common storage backends like AWS S3. Specifically, it was designed around the following goals:

1. Tailor visualizations to problem-specific data and biological questions.
2. Integrate and explore multimodal data with multiple coordinated views triggered, e.g. by the selecting a gene, a cell type, or a visual property such as a colormap.
3. Platform-independence: Being implemented in JavaScript and WebGL, the framework can be used not only in websites as a [React component](https://vitessce.io/docs/js-react-vitessce/), but also in Python as a [Jupyter widget](https://python-docs.vitessce.io/widget_examples.html) or in R in the RStudio Viewer pane, in [pkgdown websites](https://r-docs.vitessce.io/articles/pkgdown.html), or as a [Shiny widget](https://r-docs.vitessce.io/articles/shiny.html).
4. Deploy and share interactive visualizations.
5. Access data from different storage formats. Data can be loaded from [multiple storage formats](https://vitessce.io/docs/data-types-file-types/), including the scverse `AnnData`, `MuData`, and `SpatialData` formats and the Open Microscopy Environment OME-TIFF and OME-Zarr formats.

## How Vitessce and LaminDB connect

The Vitessce Python package contains features to view data stored both locally and remotely.
As Vitessce is a web-based framework, this often entails pointing to data via URL (localhost URLs and absolute URLs to object storage systems, respectively).
Challenges can also arise on high-performance computing clusters and cloud notebook platforms, where the location of each software process relative to the [data](https://python-docs.vitessce.io/data_options.html) must be carefully considered.
For example, if data is stored in a cluster system, the Python kernel process powering Jupyter might be running on a cluster node, while the Jupyter notebook frontend is running on your laptop web browser.
When using Lamin, the Python kernel may run on your laptop while the data is stored in a cloud object storage, and you want to view the visualization in your local web browser.
Vitessce provides features that enable interactive visualizations even in these more challenging scenarios.

The Vitessce Python package can consume LaminDB artifacts directly.
In practice, this means you can configure visualizations against tracked artifacts instead of manually wiring URLs and file paths.

### Zarr-based data access

When data is stored in Zarr-based formats, the Vitessce Jupyter widget can use Zarr Store interfaces for efficient partial reads (as opposed to relying on HTTP requests).
Internally, this uses the experimental remote procedure call capabilities of [anywidget](https://github.com/manzt/anywidget) via `_store`-suffixed parameters (for example, `adata_store` in [AnnDataWrapper](https://python-docs.vitessce.io/api_data.html#vitessce.wrappers.AnnDataWrapper)).

### LaminDB artifacts

When datasets are managed in LaminDB, you can pass artifacts directly into Vitessce wrappers using `_artifact`-suffixed parameters (for example, `adata_artifact` in [AnnDataWrapper](https://python-docs.vitessce.io/api_data.html#vitessce.wrappers.AnnDataWrapper)).
Unlike the Zarr-store path, this approach works across multiple formats, including H5AD and OME-TIFF (for example, `img_artifact` in [ImageOmeTiffWrapper](https://python-docs.vitessce.io/api_data.html#vitessce.wrappers.ImageOmeTiffWrapper)).
Examples are available in the [Lamin Vitessce guide](https://docs.lamin.ai/vitessce) and this [example notebook](https://lamin.ai/vitessce/examples/transform/3ixi4FetqaJk).

## LaminHub UI

In this integration, data and visualization-relevant objects are managed as LaminDB artifacts, then viewed in LaminHub. From LaminHub, users can filter and discover artifacts, apply access controls, and launch the corresponding Vitessce views in the browser.

## Visualizing data across formats

Vitessce supports multiple scverse data formats, including `AnnData`, `MuData`, and `SpatialData`, as well as the bioimaging formats OME-TIFF and OME-Zarr.
SpatialData is the most recent of these formats, and acts as a container object for multiple Spatial Elements: Tables, Points, Shapes, Labels, and Images.
While individual elements within a `SpatialData` object can be stored using multiple separate formats (e.g., AnnData for Tables; OME-TIFF for Images), usage of `SpatialData` enables storing metadata such as coordinate systems and transformations in a single place and facilitates operations such as spatial queries that involve table columns or rapid conversion between vector- and raster-based representations.

![SpatialData object](https://lamin-site-assets.s3.amazonaws.com/.lamindb/YjFyCUEICxunisKs0000.png)

In the aforementioned [example notebook](https://lamin.ai/vitessce/examples/transform/3ixi4FetqaJk0000), we demonstrate visualization of a `SpatialData` object, followed by visualization of individual Spatial Elements using alternative formats.
This notebook first demonstrates how to visualize locally stored data using the Vitessce widget, then saves the data as Lamin artifacts and shows how to launch the resulting visualizations from LaminHub.

## Author contributions

Mark added support for `lamindb.artifact` within the Vitessce Python package, created the example database [lamin.ai/vitessce/examples](http://lamin.ai/vitessce/examples), overhauled the LaminDB integration ([laminlabs/lamindb#1953](https://github.com/laminlabs/lamindb/pull/1953)), and wrote the first comprehensive version of the Vitessce ingestion guide: [docs.lamin.ai/vitessce](http://docs.lamin.ai/vitessce).

Altana resolved many issues running the integration in production, overhauled the ingestion guide ([laminlabs/lamin-spatial#48](https://github.com/laminlabs/lamin-spatial/pull/48)), and reviewed this post.

Alex created the Vitessce integration for LaminDB ([laminlabs/lamindb#1532](https://github.com/laminlabs/lamindb/pull/1532)) and maintained it over two years.

Richard created a storage proxy that would allow secure streaming of private data into an externally hosted (static) Vitessce application, keeping data in the client and data-hosting cloud (AWS, GCP, etc.) account.

Sunny coordinated the project and created the visual LaminHub integration.

## Acknowledgements

Vitessce is developed by the [Humans in Data Integration, Visualization, and Exploration (HIDIVE) Lab](https://hidivelab.org) at Harvard Medical School.
The HIDIVE Lab aims to address challenges in visualization and exploration of biomedical data.

## Appendix: Customizing a Vitessce visualization

There are three main ways that a Vitessce visualization can be customized: [data](https://vitessce.io/docs/data-types-file-types/), [views](https://vitessce.io/docs/components/), and [coordinations](https://vitessce.io/docs/coordination/).
Coordination refers to the linkages among subsets of views. For example, two views can be coordinated by sharing the same colormap or gene selection.
Useful starting points for customization include the following example database and related resources:

- Database: [vitessce/examples](https://lamin.ai/vitessce/examples)
- Vitessce docs:
  - [The vitessce-python-tutorial GitHub Repository](https://github.com/vitessce/vitessce-python-tutorial/)
  - [The paper-figures GitHub Repository](https://github.com/vitessce/paper-figures)
