---
title: "Interactive visualization of multimodal and spatial data with Vitessce"
date: 2025-05-06
author: keller-mark, namsaraeva, falexwolf, chaichontat, sunnyosun
affiliation:
  keller-mark: Harvard Medical School, Boston
  namsaraeva: Lamin Labs, Munich
  falexwolf: Lamin Labs, Munich
  chaichontat: Lamin Labs, NYC
  sunnyosun: Lamin Labs, Munich
db: vitessce/examples
repo: laminlabs/spatial
---

---

In this post, we discuss how to use [Vitessce](https://vitessce.io) to visualize multimodal and spatial single-cell data that is managed with LaminDB.

---

## Background

Single-cell experiments result in heterogeneous datasets due to several factors: differing profiling techniques (e.g., sequencing-based versus imaging-based), platforms, modalities (e.g., transcriptomics, epigenomics, proteomics, and combinations thereof), and scales (e.g., spot to single-cell to subcellular).
Through data processing, different types of derived information may be produced, such as cell type annotations, unsupervised clusterings, cell segmentations, or dimensionality reductions.
The heterogeneous nature of single-cell datasets presents challenges for data analysis, including visualization.

While there are standalone tools for different purposes, such as scatterplot viewers, image viewers, and genome browsers, disconnected tools can fragment the analysis workflow and hinder identification of relationships or patterns that span data modalities.
Additional challenges that can arise in the process of single-cell data visualization include deploying and maintaining specialized server-side software, converting data to non-standard formats (requiring time, compute, and storage), and the increasing size of single-cell datasets.
Finally, once an interactive visualization is created, it is useful to access it from multiple environments (Python, R, or the web) and to save and share it with collaborators.

## Vitessce

[Vitessce](https://vitessce.io) is a web-based framework for interactive visualization of multimodal and spatial single-cell data.
Vitessce can be configured within Python environments (including Jupyter notebooks), and supports viewing data hosted locally or remotely, including LaminDB's artifacts and collections.
Vitessce has been designed around the following goals:

1. **Tailor visualizations to problem-specific data and biological questions.** The interactive plots and control components (together referred to as "views") included within a grid of multiple interactive elements can be configured to reflect the data types available and biological questions of interest.
2. **Integrate and explore multimodal data with coordinated multiple views.** Coordinated multiple views refers to the linking of properties across views. For example, selection of a gene, cell type, or a visual property such as a colormap.
3. **Explore visualizations in different computational environments.** As the core functionality of Vitessce is implemented using web technologies such as JavaScript and WebGL, the framework can be used not only in websites (as a [React component](https://vitessce.io/docs/js-react-vitessce/)), but also in Python as a [Jupyter widget](https://python-docs.vitessce.io/widget_examples.html) or in R (in the RStudio Viewer pane, in [pkgdown websites](https://r-docs.vitessce.io/articles/pkgdown.html), or as a [Shiny widget](https://r-docs.vitessce.io/articles/shiny.html)).
4. **Deploy and share interactive visualizations.** Vitessce visualizations can be shared by [hosting data](https://vitessce.io/docs/data-hosting/) in cloud object storage and either deploying a [standalone website](https://vitessce.io/docs/tutorial-gh-pages/) or including the JSON configuration in a [URL](https://vitessce.io/#?edit=true).
5. **Access data from multiple file formats.** Data can be loaded from [multiple file formats](https://vitessce.io/docs/data-types-file-types/), including the scverse `AnnData`, `MuData`, and `SpatialData` formats and the Open Microscopy Environment OME-TIFF and OME-Zarr formats.

## Visualizing data across locations

The Vitessce Python package contains features to view data stored both locally and remotely.
As Vitessce is a web-based framework, this often entails pointing to data via URL (localhost URLs and absolute URLs to object storage systems, respectively).
Challenges can arise when using high-performance computing clusters and cloud notebook platforms, necessitating consideration of where each software process is running with respect to the [location of the data](https://python-docs.vitessce.io/data_options.html).
For example, if data is stored in a cluster system, the Python kernel process powering Jupyter might be running on a cluster node, while the Jupyter notebook frontend is running on your laptop web browser.
When using Lamin, a Python kernel process may be running on your laptop, while the data is stored in a cloud object storage system, and you aim to view a visualization in your laptop web browser.
Vitessce contains features that enable interactive visualizations to be accessed even in these more challenging scenarios.

### Zarr-based data access

When data is stored in a Zarr-based format, the Vitessce Jupyter widget can use the Zarr Store interface to perform partial reads (as opposed to relying on HTTP requests).
This is made possible thanks to the experimental remote procedure call feature of [anywidget](https://github.com/manzt/anywidget), which Vitessce uses internally when data is specified using `_store`-suffixed parameters (e.g., `adata_store` for [AnnDataWrapper](https://python-docs.vitessce.io/api_data.html#vitessce.wrappers.AnnDataWrapper)).

### LaminDB artifacts

When LaminDB is used to manage datasets, these datasets can be visualized by passing artifacts directly to Vitessce during configuration.
Specifically, Vitessce can be configured using `_artifact`-suffixed dataset parameters (e.g., `adata_artifact` for [AnnDataWrapper](https://python-docs.vitessce.io/api_data.html#vitessce.wrappers.AnnDataWrapper)).
Unlike the aforementioned Zarr-based case, artifact-based configuration is not restricted to particular formats, for instance, enabling visualization of H5AD- and OME-TIFF-based artifacts (e.g., `img_artifact` for [ImageOmeTiffWrapper](https://python-docs.vitessce.io/api_data.html#vitessce.wrappers.ImageOmeTiffWrapper)).
Examples of artifact-based configuration of Vitessce can be found at [docs.lamin.ai/vitessce](https://docs.lamin.ai/vitessce) as well as this [example notebook](https://lamin.ai/vitessce/examples/transform/3ixi4FetqaJk).

## Visualizing data across formats

Vitessce supports multiple scverse data formats, including `AnnData`, `MuData`, and `SpatialData`, as well as the bioimaging formats OME-TIFF and OME-Zarr.
SpatialData is the most recent of these formats, and acts as a container object for multiple Spatial Elements: Tables, Points, Shapes, Labels, and Images.
While individual elements within a `SpatialData` object can be stored using multiple separate formats (e.g., AnnData for Tables; OME-TIFF for Images), usage of `SpatialData` enables storing metadata such as coordinate systems and transformations in a single place and facilitates operations such as spatial queries that involve table columns or rapid conversion between vector- and raster-based representations.

In the aforementioned [example notebook](https://lamin.ai/vitessce/examples/transform/3ixi4FetqaJk0000), we demonstrate visualization of a `SpatialData` object, followed by visualization of individual Spatial Elements using alternative formats.
This notebook first demonstrates how to visualize locally stored data using the Vitessce widget, then saves the data as Lamin artifacts and shows how to launch the resulting visualizations from LaminHub.

<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/YjFyCUEICxunisKs0000.png" title="SpatialData object" width="500" />

## Author contributions

Mark added support for `lamindb.artifact` within the Vitessce Python package, created the example database http://lamin.ai/vitessce/examples, overhauled the LaminDB integration (https://github.com/laminlabs/lamindb/pull/1953), and wrote the first comprehensive version of the Vitessce ingestion guide: http://docs.lamin.ai/vitessce.

Altana resolved many issues running the integration in production, overhauled the ingestion guide: https://github.com/laminlabs/lamin-spatial/pull/48, and reviewed this post.

Alex created the Vitessce integration for LaminDB (https://github.com/laminlabs/lamindb/pull/1532) and maintained it over two years.

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
