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
---

The open-source tool [Vitessce](https://vitessce.io) and Lamin now work together to manage & visualize multimodal and spatial single-cell data.
It's simple: define a Vitessce config in code, save it as an artifact, and share the interactive visualization along with your datasets on LaminHub.

<div style="text-align: center">
<img width="800" src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/rcJQthuZfseneY0m0005.png">
</div>

## Vitessce

Single-cell experiments result in heterogeneous datasets due to several factors: differing profiling techniques (e.g., sequencing-based versus imaging-based), platforms, modalities (e.g., transcriptomics, epigenomics, proteomics, and combinations thereof), and scales (e.g., spot to single-cell to subcellular).
Data pipelines often add cell type annotations or cell segmentations together with embeddings and other types of information.
Visualizing the rich information in these complex datasets helps scientists interpret key features, whether they are biologists looking to answer biological questions or machine learning engineers trying to understand behaviors of outlier datasets.

Vitessce[^keller25] is an open-source JavaScript-based framework for interactive visualization of multimodal and spatial single-cell data. Its dashboard-like views can easily be defined programmatically and then serialized as a JSON artifact. Vitessce then runs serverless anywhere against common storage backends like AWS S3. Specifically, it was designed around the following goals:

1. Tailor visualizations to problem-specific data and biological questions.
2. Integrate and explore multimodal data with multiple coordinated views triggered, e.g. by selecting a gene, a cell type, or a visual property such as a colormap.
3. Deploy and share interactive visualizations.
4. Access data from different storage formats. Data can be loaded from [multiple storage formats](https://vitessce.io/docs/data-types-file-types/), including the scverse `AnnData`, `MuData`, and `SpatialData` formats and the Open Microscopy Environment OME-TIFF and OME-Zarr formats.
5. Platform-independence: Being implemented in JavaScript and WebGL, the framework can be used not only in websites as a [React component](https://vitessce.io/docs/js-react-vitessce/), but also in Python as a [Jupyter widget](https://python-docs.vitessce.io/widget_examples.html) or in R in the RStudio Viewer pane, in [pkgdown websites](https://r-docs.vitessce.io/articles/pkgdown.html), or as a [Shiny widget](https://r-docs.vitessce.io/articles/shiny.html).

## Integration with LaminDB

Managing the URL paths to local and cloud object storage systems manually becomes cumbersome in particular when managing a high number of datasets.
Through the integration with LaminDB, the `vitessce` Python module now supports building configurations directly based on LaminDB artifacts, which are tracked, validated, and queryable and let the user focus on the entities they care about -- genes, experiments, cell types, samples, etc. -- rather than storage paths.

The way this works is by passing `Artifact` objects to `_artifact`-suffixed arguments, for example, for `AnnData`, via the `adata_artifact` argument in Vitessce's `AnnDataWrapper`, or for OME-TIFF via the `img_artifact` argument in `ImageOmeTiffWrapper`.

## Supported formats

Vitessce supports multiple scverse data formats, including `AnnData`, `MuData`, and `SpatialData`, as well as the bioimaging formats OME-TIFF and OME-Zarr.
`SpatialData`[^marconato25] is the most recent of these formats, and acts as a container object for multiple spatial elements: Tables, Points, Shapes, Labels, and Images.
While individual elements within a `SpatialData` object can be stored using multiple separate formats (e.g., `AnnData` for Tables; OME-TIFF for Images), usage of `SpatialData` enables storing metadata such as coordinate systems and transformations in a single place. It hence facilitates operations such as spatial queries that involve table columns or rapid conversion between vector- and raster-based representations.

## Example & guides

You'll find simple guides for visualizing `AnnData`, `SpatialData`, `OME-ZARR` and `OME-TIFF` at [docs.lamin.ai/vitessce](https://docs.lamin.ai/vitessce).

In this [rich example notebook](https://lamin.ai/vitessce/examples/transform/3ixi4FetqaJk0000), you'll find a complex example for a `SpatialData` object that includes visualizing individual Spatial Elements using alternative formats, all tracked & managed with LaminDB.

## Author contributions

Mark added support for `lamindb.artifact` within the Vitessce Python package, created the example database [lamin.ai/vitessce/examples](http://lamin.ai/vitessce/examples), overhauled the LaminDB integration ([laminlabs/lamindb#1953](https://github.com/laminlabs/lamindb/pull/1953)), and wrote the first comprehensive version of the Vitessce ingestion guide: [docs.lamin.ai/vitessce](http://docs.lamin.ai/vitessce).

Altana resolved many issues running the integration in production, overhauled the ingestion guide ([laminlabs/lamin-spatial#48](https://github.com/laminlabs/lamin-spatial/pull/48)), and reviewed this post.

Alex created & maintained the Vitessce integration for LaminDB ([laminlabs/lamindb#1532](https://github.com/laminlabs/lamindb/pull/1532)).

Richard created a storage proxy that would allow secure streaming of private data into an externally hosted (static) Vitessce application, keeping data within the client and data-hosting cloud.

Sunny coordinated the project and created the visual LaminHub integration.

Mark, Sunny & Alex wrote the blog post.

## Acknowledgements

Vitessce is developed by the [Humans in Data Integration, Visualization, and Exploration (HIDIVE) Lab](https://hidivelab.org) at Harvard Medical School.
The HIDIVE Lab aims to address challenges in visualization and exploration of biomedical data.

Lamin started first working on the integration because the need was surfaced by Tim Treis & Lukas Heumos. We're grateful for that!

## Appendix

There are three main ways that a Vitessce visualization can be customized: [data](https://vitessce.io/docs/data-types-file-types/), [views](https://vitessce.io/docs/components/), and [coordinations](https://vitessce.io/docs/coordination/).
Useful starting points for customization include the following example database and related resources:

- The [vitessce/examples](https://lamin.ai/vitessce/examples) database
- The [vitessce-python-tutorial](https://github.com/vitessce/vitessce-python-tutorial/) repository
- The [paper-figures](https://github.com/vitessce/paper-figures) repository

[^keller25]: Keller, M.S., Gold, I., McCallum, C. et al. Vitessce: integrative visualization of multimodal and spatially resolved single-cell data. Nat Methods 22, 63–67 (2025).

[^marconato25]: Marconato, L., Palla, G., Yamauchi, K.A. et al. SpatialData: an open and universal data framework for spatial omics. Nat Methods 22, 58–62 (2025).
