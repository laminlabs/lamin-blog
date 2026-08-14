---
title: "Extracting single-cell morphology and subcellular protein localisation from Xenium data with scPortrait"
date: 2026-08-14
author: sophiamaedler, nik-as
affiliation:
  sophiamaedler: Matthias Mann Lab
  nik-as: Fabian Theis Lab
db: https://lamin.ai/scportrait/examples
---

Spatial transcriptomics measures RNA abundance and spatial localization in tissue and is routinely complemented by fluorescence microscopy imaging.
Here, we show how to extract single-cell images from these data by segmenting tissue slides with the Python-based scPortrait toolkit.
We then embed the single-cell images with a neural network to identify cells with distinct morphologies and intracellular protein distributions.
Mapping the image-derived representation onto transcriptomic space reveals distinct transcriptomic subpopulations.

We study a publicly available [Xenium dataset](https://lamin.ai/scportrait/examples/artifact/maZ6xBiJ48hYVMc9) from an ovarian cancer patient.
This dataset includes more than 120 million transcripts from more than 400,000 cells, along with fluorescence images showing staining of multiple cellular structures and proteins, including the cell membrane and nucleus.

We will extract and analyze single-cell images from this dataset using the Python-based toolkit scPortrait[^scportrait]. Our workflow consists of:

1. Loading Xenium data as a SpatialData[^spatialdata] object
2. Loading the immunohistochemistry images into scPortrait
3. Using the cytosol segmentation provided as part of the dataset to extract single-cell images with scPortrait
4. Deriving single-cell image features with the convolutional neural network ConvNeXt[^convnext] pretrained on natural images

## Loading Xenium Data

After loading the Xenium dataset into a SpatialData object we can inspect the tissue sample that was profiled (**Figure 1**).

<div style="text-align: center">
<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/j9yhX6gjAMF0QstE0000.png" width="400" style="padding: 0;"/>
</div>

**Figure 1 ([source](https://lamin.ai/scportrait/examples/transform/OofR70fo7iEt0007))**: H&E staining of the 10x Genomics Xenium ovarian cancer tissue sample.

Zooming in further, we can see that the different fluorescence microscopy imaging channels capture different aspects of cellular composition that allow us to differentiate between cells in the tissue (**Figure 2**). The stained structures are summarized in Table 1.

<div style="text-align: center">
<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/eQxraEWXKSeB7kMe0000.png" width="700" style="padding: 0;"/>
</div>

**Figure 2 ([source](https://lamin.ai/scportrait/examples/transform/OofR70fo7iEt0007))**: Fluorescence microscopy images of different proteins and subcellular structures in a small region of the ovarian cancer Xenium dataset.

| Channel | Stain                    | Description                                                                                                                                          |
| ------- | ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1       | DAPI                     | DNA                                                                                                                                                  |
| 2       | ATP1A1, E-Cadherin, CD45 | **ATP1A1, E-Cadherin:** Epithelial markers<br>**CD45:** Pan-lymphocyte marker                                                                        |
| 3       | 18S                      | Ribosomal RNA, used for [segmentation](https://www.10xgenomics.com/support/software/xenium-onboard-analysis/latest/algorithms-overview/segmentation) |
| 4       | AlphaSMA/Vimentin        | **AlphaSMA:** Smooth Muscle Actin, a cytoskeletal protein<br>**Vimentin:** A cytoskeletal protein used as a soft-tissue tumor marker                 |
| 5       | None                     | Dummy Channel                                                                                                                                        |

**Table 1**: Summary of the fluorescent stains used in the ovarian cancer Xenium dataset.

## Generating single-cell images

To generate a single-cell image dataset we apply a segmentation mask to the image, and then extract images of individual cells. The Xenium dataset provides a segmentation mask already (**Figure 3**).

<div style="text-align: center">
<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/vfTvQso0dF5vXLl30001.png" width="500" style="padding: 0;"/>
</div>

**Figure 3 ([source](https://lamin.ai/scportrait/examples/transform/OofR70fo7iEt0007))**: Segmentation masks from the ovarian cancer Xenium dataset loaded into scPortrait.

After loading the sdata object into an `scPortrait` project, we can run `scPortrait.extract()` to extract a single-cell image dataset (**Figure 4**).

<div style="text-align: center">
<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/VDLiYGGEcoHQMaR60000.png" width="700" style="padding: 0;"/>
</div>

**Figure 4 ([source](https://lamin.ai/scportrait/examples/transform/OofR70fo7iEt0007))**: Single-cell images from the ovarian cancer Xenium dataset extracted with scPortrait.

## Featurizing single-cell images

To find similarities and differences between individual cells in our image dataset, and to ultimately integrate different single-cell datasets and modalities, we have to embed all cells into a unified representation. To do this, we first have to derive common features describing each cell based on its image. Multiple approaches to achieve this have been described, which broadly fall into two categories:

1. Using pre-engineered ways to calculate single-cell image features, such as using the convex hull of the DAPI stain to calculate a nucleus outline and area. [CellProfiler](https://github.com/afermg/cp_measure) provides a collection of such features.
2. Using automatic feature extractors that learn descriptive features from image data. This is currently done using deep learning with models based on architectures including convolutional neural networks (CNNs) and vision transformers (ViTs).

Here, we use ConvNeXt,[^convnext] a CNN that was trained to classify images in imageNet,[^imagenet] a collection of natural images. We hypothesize that ConvNeXt has learned a feature set that is useful to describe images, and can therefore identify cellular phenotypes despite not having been trained on images of cells. The images in imageNet are 3-channel RGB images. Hence, ConvNeXt accepts three input channels. We chose to use the ATP1A1, E-Cadherin, CD45 (#2), 18S (#3) and AlphaSMA/Vimentin (#4) channels to featurize our cells. With the `scPortrait` `Dataloader` we can then calculate ConvNeXt features for all cells in the Xenium dataset. Using a `umap` visualization to inspect this embedding, we find populations of cells corresponding to different morphologies and intracellular marker protein distributions (**Figure 5**). Overlaying this image-based embedding with transcriptome information for each cell reveals that cellular differences identified via image-based features are accompanied by gene expression changes. For example, we identify a morphologically distinct population of cells that expresses the collagen gene _COL5A1_.(**Figure 5**).

<div style="text-align: center">
<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/vdUZBbdtiawnXUWX0000.png" width="700" style="padding: 0;"/>
</div>

**Figure 5 ([source](https://lamin.ai/scportrait/examples/transform/GgYLvhXloKY20002))**: UMAP representation of ConvNeXt image features of individual segmented cells in an ovarian cancer tissue region. Each dot corresponds to a single cell. Colors correspond to the expression of the indicated genes across cells.

## Data & code availability

The blog post roughly follows this guide for working with `scportrait` and `lamindb`: [docs.lamin.ai/sc-imaging](https://docs.lamin.ai/sc-imaging). For source code, see:

- Analyses of this blog post: https://lamin.ai/scportrait/examples
- The scPortrait library: https://github.com/MannLabs/scPortrait

## How to cite

```
Mädler SC & Schmacke NA (2026). Extracting single-cell morphology and subcellular protein localisation from Xenium data with scPortrait. Lamin Blog. https://blog.lamin.ai/scportrait
```

## Acknowledgements

We thank Lukas Heumos for support in creating [docs.lamin.ai/sc-imaging](https://docs.lamin.ai/sc-imaging).

## References

[^nature-methods]: Nature Methods (2021). Method of the Year 2020: spatially resolved transcriptomics. [Nature Methods](https://www.nature.com/articles/s41592-020-01033-y).

[^scportrait]: Mann Labs. scPortrait: A Python toolkit for single-cell image analysis. [GitHub](https://github.com/MannLabs/scPortrait).

[^spatialdata]: SpatialData. A unified spatial omics data framework for Python. [SpatialData](https://spatialdata.scverse.org).

[^convnext]: Liu Z et al. (2022). A ConvNet for the 2020s. [arXiv:2201.03545](https://arxiv.org/abs/2201.03545).

[^imagenet]: Deng J et al. (2009). ImageNet: A large-scale hierarchical image database. [doi:10.1109/CVPR.2009.5206848](https://ieeexplore.ieee.org/document/5206848).
