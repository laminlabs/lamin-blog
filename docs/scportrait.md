---
title: "Analyzing single-cell images from 10x Genomics Xenium data with scPortrait"
date: 2026-08-11
author: sophiamaedler, nik-as
affiliation:
  sophiamaedler: Matthias Mann Lab
  nik-as: Fabian Theis Lab
db: https://lamin.ai/scportrait/examples
---

Profiling cells in tissues, their native environment, promises to deliver deep insights into diverse aspects of cellular function. When applied to patient tissue, such techniques improve our understanding of disease. One technology that provides this type of data is spatial transcriptomics, which measures the abundance and spatial location of RNA transcripts in cells, while preserving tissue context. Named “Method of the year 2020” by [Nature Methods](https://www.nature.com/articles/s41592-020-01033-y), spatial transcriptomics is now routinely applied in diverse biological contexts. Along with information on transcripts, fluorescence microscopy images of cells are also routinely collected now. These images contain information about cell morphology and the intracellular distribution of proteins, complementing the information provided by the transcriptome. Here, we show how this image information can be made available on the single cell level by segmenting tissue slides and extracting single cell images with the Python-based toolkit [scPortrait](https://github.com/MannLabs/scPortrait). We then build a representation of the cells in our tissue using deep learning to embed their image-derived profiles into a continuous space.

The technology that was used to generate the data we work with is 10x Genomics’s Xenium. Xenium enables the acquisition of two data modalities on the single cell level:

1. Spatial Transcriptomics. A set of probes is used to read out the expression of genes _in situ_.
2. Images. Multiple fluorescence imaging channels can record the distribution of stained proteins and cellular structures with subcellular accuracy.

To profile the transcriptome, Xenium implements a probe-based transcriptomics assay where a panel of 5,000 probes is used to measure the expression of a predefined set of genes in all cells. The main advantage of probe-based methods is their high resolution, up to the subcellular level.

We work with a publicly available [Xenium dataset](https://www.10xgenomics.com/welcome?closeUrl=%2Fdatasets&lastTouchOfferName=FFPE%20Human%20Ovarian%20Cancer%20with%205K%20Human%20Pan%20Tissue%20and%20Pathways%20Panel%20plus%20100%20Custom%20Genes&lastTouchOfferType=Dataset&product=chromium&redirectUrl=%2Fdatasets%2Fxenium-prime-ffpe-human-ovarian-cancer) from an Ovarian cancer patient. This dataset includes more than 120 million transcripts from more than 400,000 cells. It also includes fluorescence images of staining for multiple cellular structures and proteins including the cell membrane and the nucleus.

Our workflow consists of:

1. Loading Xenium data as a [SpatialData](https://spatialdata.scverse.org) object
2. Loading the immunohistochemistry images into scPortrait
3. Using the cytosol segmentation provided as part of the dataset to extract single cell images with scPortrait
4. Deriving single cell image features with the convolutional neural network [ConvNeXt](https://arxiv.org/abs/2201.03545) pretrained on natural images

## Loading Xenium Data

After loading the Xenium dataset into a SpatialData object we can inspect the tissue sample that was profiled (**Figure 1**).

<div style="text-align: center">
<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/j9yhX6gjAMF0QstE0000.png" width="700" style="padding: 0;"/>
</div>

**Figure 1 ([source](https://lamin.ai/scportrait/examples/transform/OofR70fo7iEt0007))**: H&E staining of the 10x Genomics Xenium ovarian cancer tissue sample.

Zooming in further, we can see that the different fluorescence microscopy imaging channels capture different aspects of cellular composition that allow us to differentiate between cells in the tissue (**Figure 2**). The stained structures are summarized in Table 1.

<div style="text-align: center">
<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/eQxraEWXKSeB7kMe0000.png" width="700" style="padding: 0;"/>
</div>

**Figure 2 ([source](https://lamin.ai/scportrait/examples/transform/OofR70fo7iEt0007))**: Fluorescence microscopy images of different proteins and subcellular structures in a small region of the ovarian cancer Xenium dataset.

| Channel # | Stain                    | Description                                                                                                                                          |
| --------- | ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1         | DAPI                     | DNA                                                                                                                                                  |
| 2         | ATP1A1, E-Cadherin, CD45 | **ATP1A1, E-Cadherin:** Epithelial markers<br>**CD45:** Pan-lymphocyte marker                                                                        |
| 3         | 18S                      | Ribosomal RNA, used for [segmentation](https://www.10xgenomics.com/support/software/xenium-onboard-analysis/latest/algorithms-overview/segmentation) |
| 4         | AlphaSMA/Vimentin        | **AlphaSMA:** Smooth Muscle Actin, a cytoskeletal protein<br>**Vimentin:** A cytoskeletal protein used as a soft-tissue tumor marker                 |
| 5         | None                     | Dummy Channel                                                                                                                                        |

**Table 1**: Summary of the fluorescent stains used in the ovarian cancer Xenium dataset.
|

## Generating Single Cell Images with scPortrait

To generate a single cell image dataset we apply a segmentation mask to the image, and then extract images of individual cells. The Xenium dataset provides a segmentation mask already (**Figure 3**).

<div style="text-align: center">
<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/vfTvQso0dF5vXLl30000.png" width="700" style="padding: 0;"/>
</div>

**Figure 3 ([source](https://lamin.ai/scportrait/examples/transform/OofR70fo7iEt0007))**: Segmentation masks from the ovarian cancer Xenium dataset loaded into scPortrait.

After loading the sdata object into an `scPortrait` project, we can run `scPortrait.extract()` to extract a single cell image dataset (**Figure 4**).

<div style="text-align: center">
<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/VDLiYGGEcoHQMaR60000.png" width="700" style="padding: 0;"/>
</div>

**Figure 4 ([source](https://lamin.ai/scportrait/examples/transform/OofR70fo7iEt0007))**: Single cell images from the ovarian cancer Xenium dataset extracted with scPortrait.

## Featurizing Single Cell Images with ConvNeXt

To find similarities and differences between individual cells in our image dataset, and to ultimately integrate different single cell datasets and modalities, we have to embed all cells into a unified representation. To do this, we first have to derive common features describing each cell based on its image. Multiple approaches to achieve this have been described, which broadly fall into two categories:

1. Using pre-engineered ways to calculate single-cell image features, such as using the convex hull of the DAPI stain to calculate a nucleus outline and area. [CellProfiler](https://github.com/afermg/cp_measure) provides a collection of such features.
2. Using automatic feature extractors that learn descriptive features from image data. This is currently done using deep learning with models based on architectures including convolutional neural networks (CNNs) and vision transformers (ViTs).

Here, we use [ConvNeXt](https://arxiv.org/abs/2201.03545), a CNN that was trained to classify images in [imageNet](https://ieeexplore.ieee.org/document/5206848), a collection of natural images. We hypothesize that ConvNeXt has learned a feature set that is useful to describe images, and can therefore identify cellular phenotypes despite not having been trained on images of cells. The images in imageNet are 3-channel RGB images. Hence, ConvNeXt accepts three input channels. We chose to use the ATP1A1, E-Cadherin, CD45 (#2), 18S (#3) and AlphaSMA/Vimentin (#4) channels to featurize our cells. With the `scPortrait` `Dataloader` we can then calculate ConvNeXt features for all cells in the Xenium dataset. Using a `umap` visualization to inspect this embedding, we find that the expression of a number of genes varies across cells with different morphological features (**Figure 5**).

<div style="text-align: center">
<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/vdUZBbdtiawnXUWX0000.png" width="700" style="padding: 0;"/>
</div>

**Figure 5 ([source](https://lamin.ai/scportrait/examples/transform/GgYLvhXloKY20002))**: UMAP representation of ConvNeXt image features of individual segmented cells in an ovarian cancer tissue region. Each dot corresponds to a single cell. Colors correspond to the expression of the indicated genes across cells.

# Data & code availability

- Analyses of this blog post: https://lamin.ai/scportrait/examples
- scPortrait souce code: https://github.com/MannLabs/scPortrait
- A guide for working with `scportrait` and `lamindb`: [docs.lamin.ai/sc-imaging](https://docs.lamin.ai/sc-imaging)
