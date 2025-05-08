---
title: "Interactive visualization of Lamin Artifacts using Vitessce"
date: 2025-05-06
author: keller-mark, sunnyosun, falexwolf
affiliation:
  keller-mark: Harvard Medical School, Boston
  sunnyosun: Lamin Labs, Munich
  falexwolf: Lamin Labs, Munich
---

---

The Lamin Hub interface displays key information about the contents of Artifacts, enabling filtering and querying for data of interest within a Lamin Instance.
Integrations with interactive visualization tools can further enable exploration and communication of data within Artifacts and Collections managed by Lamin.
In this post, we discuss the usage of the [Vitessce](https://vitessce.io) framework for visualization of multimodal and spatial single-cell data, including that which is accessible via Lamin Hub.


## Background

Single-cell experiments result in heterogeneous datasets due to several factors: differing profiling techniques (e.g., sequencing-based versus imaging-based), platforms, modalities (e.g., transcriptomics, epigenomics, proteomics, and combinations thereof), and scales (e.g., spot to single-cell to subcellular).
Through data processing, different types of derived information may be produced, such as cell type annotations, unsupervised clusterings, cell segmentations, or dimensionality reductions.
The heterogeneous nature of single-cell datasets presents challenges for data analysis, including visualization.


While there are standalone tools for different purposes, such as scatterplot viewers, image viewers, and genome browsers, disconnected tools can fragment the analysis workflow and can hinder identification of relationships or patterns which span data modalities.
Other challenges that can arise in the process of single-cell data visualization include the need to deploy and maintain specialized server-side software, the need to convert data to non-standard formats (requiring time, compute, and storage), and the increasing size of single-cell datasets.
Finally, upon creation of an interactive visualization, it can be useful to be able to access this from multiple environments (Python, R, or the web) and to save and share with collaborators.


## Vitessce

[Vitessce](https://vitessce.io) is a web-based framework for interactive visualization of multimodal and spatial single-cell data.
Vitessce can be configured within Python environments (including Jupyter notebooks), and supports viewing data hosted locally or remotely, including Artifacts and Collections that are accessible via Lamin Hub.
This framework has been designed around the following goals:

1. __Tailor visualizations to problem-specific data and biological questions.__ The interactive plots and control components (together referred to as "views") included within a grid of multiple interactive elements can be configured to reflect the data types available and biological questions of interest.
2. __Integrate and explore multimodal data with coordinated multiple views.__ Coordinated multiple views refers to the linking of properties across views. For example, selection of a gene, cell type, or a visual property such as a colormap.
3. __Explore visualizations in different computational environments.__ As the core functionality of Vitessce is implemented using web technologies such as JavaScript and WebGL, the framework can be used not only in websites (as a [React component](https://vitessce.io/docs/js-react-vitessce/)), but also in Python as a [Jupyter widget](https://python-docs.vitessce.io/widget_examples.html) or in R (in the RStudio Viewer pane, in [pkgdown websites](https://r-docs.vitessce.io/articles/pkgdown.html), or as a [Shiny widget](https://r-docs.vitessce.io/articles/shiny.html)).
4. __Deploy and share interactive visualizations.__ Vitessce visualizations can be shared by [hosting data](https://vitessce.io/docs/data-hosting/) in cloud object storage and either deploying a [standalone website](https://vitessce.io/docs/tutorial-gh-pages/) or including the JSON configuration in a [URL](https://vitessce.io/#?edit=true).
5. __Access data from multiple file formats.__ Data can be loaded from [multiple file formats](https://vitessce.io/docs/data-types-file-types/), including the Scverse AnnData, MuData, and SpatialData formats and the Open Microscopy Environment OME-TIFF and OME-Zarr formats.


## Visualizing data stored in different locations

The Vitessce Python package contains features to view data stored both locally and remotely.
As Vitessce is a web-based framework, this often entails pointing to data via URL (localhost URLs and absolute URLs to object storage systems, respectively).
Challenges can arise when using high-performance computing clusters and cloud notebook platforms, necessitating [consideration of where each software process is running with respect to the location of the data](https://python-docs.vitessce.io/data_options.html).
For examply, if data is stored in a cluster system, the Python kernel process powering Jupyter might be running on a cluster node, while the Jupyter notebook frontend is running on your laptop web browser.
When using Lamin, a Python kernel process may be running on your laptop, while the data is stored in a cloud object storage system, and you aim to view a visualization in your laptop web browser.
Vitessce contains features that enable interactive visualizations to be accessed even in these more challenging scenarios.

### Zarr-based data access

When data is stored in a Zarr-based format, the Vitessce Jupyter widget can use the Zarr Store interface to perform partial reads (as opposed to relying on HTTP requests).
This is made possible thanks to the experimental remote procedural call feature of [Anywidget](https://github.com/manzt/anywidget), which Vitessce uses internally when data is specified using `_store`-suffixed parameters (e.g., `adata_store` for [AnnDataWrapper](https://python-docs.vitessce.io/api_data.html#vitessce.wrappers.AnnDataWrapper)).

### Lamin Artifacts

When Lamin is used to manage and analyze data, this data can be visualized by passing Artifacts directly to Vitessce during configuration.
Specifically, Vitessce can be configured using `_artifact`-suffixed data parameters (e.g., `adata_artifact` for [AnnDataWrapper](https://python-docs.vitessce.io/api_data.html#vitessce.wrappers.AnnDataWrapper)).
Unlike the aforementioned Zarr-based case, Artifact-based configuration is not restricted to particular formats, for instance, enabling visualization of H5AD- and OME-TIFF-based artifacts (e.g., `img_artifact` for [ImageOmeTiffWrapper](https://python-docs.vitessce.io/api_data.html#vitessce.wrappers.ImageOmeTiffWrapper)).
Examples of Artifact-based configuration of Vitessce can be found in the [Lamin documentation](https://docs.lamin.ai/vitessce) as well as in a new [example notebook](https://lamin.ai/vitessce/examples/transform/3ixi4FetqaJk) accessible as a Transform.

## Visualizing data stored using multiple formats

Vitessce supports multiple Scverse data formats, including AnnData, MuData, and SpatialData, as well as the bioimaging formats OME-TIFF and OME-Zarr.
SpatialData is the most recent of these formats, and acts as a container object for multiple Spatial Elements: Tables, Points, Shapes, Labels, and Images.
While individual elements within a SpatialData object can be stored using multiple separate formats (e.g., AnnData for Tables; OME-TIFF for Images), usage of SpatialData enables storing metadata such as coordinate systems and transformations in a single place and facilitates operations such as spatial queries which involve table columns or rapid conversion between vector- and raster-based representations.

In an [example notebook](https://lamin.ai/vitessce/examples/transform/3ixi4FetqaJk), we demonstrate visualization of a SpatialData object, followed by visualization of individual Spatial Elements using alternative formats.
This notebook first shows how to visualize data stored locally using the Vitessce widget, and then saves the data using Lamin Artifacts and explains how to launch the resulting visualizations from Lamin Hub.


## Customizing a Vitessce visualization

There are three main ways that a Vitessce visualization can be customized: [data](https://vitessce.io/docs/data-types-file-types/), [views](https://vitessce.io/docs/components/), and [coordinations](https://vitessce.io/docs/coordination/).
Coordinations refers to the linkages among subsets of views (e.g., two views can be coordinated by linking them to the same colormap selection or gene selection property).
Useful starting points for customization are the following examples:
- [vitessce/examples Lamin instance](https://lamin.ai/vitessce/examples)
- [Example Jupyter notebooks in the vitessce-python GitHub Repository](https://github.com/vitessce/vitessce-python/tree/main/docs/notebooks)
- [The vitessce-python-tutorial GitHub Repository](https://github.com/vitessce/vitessce-python-tutorial/)
- [The paper-figures GitHub Repository](https://github.com/vitessce/paper-figures)

---

Vitessce is developed by the [Humans in Data Integration, Visualization, and Exploration (HIDIVE) Lab](https://hidivelab.org) at Harvard Medical School.
The HIDIVE Lab aims to address challenges in visualization and exploration of biomedical data.

