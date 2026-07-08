---
title: "Scaling anndata training to the terabyte scale with annbatch"
date: 2026-07-03
author: felix-fischer, ilan-gold, fabian-theis, falexwolf
affiliation:
  felix-fischer: Lamin Labs, Munich
  ilan-gold: Helmholtz Munich
  fabian-theis: Helmholtz Munich
  falexwolf: Lamin Labs, Munich
---

The demand for AI in omics has grown at an unprecedented rate, with state-of-the-art models now routinely trained on datasets exceeding the terabyte scale. To make that process more efficient, we developed `annbatch`,[^gold26] a high-performance data loader built on `anndata` that enables loading speeds of 60k samples/second and more, at least a factor of 3 higher than the fastest recent alternatives.

Since `anndata`[^virshup24] released a first disk-backed data loader (`AnnCollection`) in 2019, better implementations have been developed, for instance, as used in SCimilarity[^scimilarity25] or Cellarium around 2022.[^cellarium22]
Based on these improvements, some of us helped develop `MappedCollection`[^mappedcollection24] to address the need for true weighted random sampling in 2023. This came, however, at a significant performance cost compared to approaches that load contiguous chunks, such as NVIDIA Merlin[^merlin20] or the `tiledbsoma` loader of CELLxGENE.[^cellxgene-census-pytorch] In 2025, `scDataset`[^dascenzo25] and SLAF[^slaf] have been introduced with significant performance improvements.

With `annbatch`,[^gold26] we developed an `anndata`-based loader that optimizes loading contiguous chunks, assumes pre-shuffling, and uses the popular `.zarr` array format.[^zarr-v2] It reaches 60k samples/second and more[^gold26] on the Tahoe-100M dataset,[^zhang25] which stores transcriptional profiles of 100M cells (**Figure 1**). For reproducibility and to showcase the conversion of the original collection of `.h5ad` files to a collection of `.zarr` stores, benchmarks were tracked with data lineage (**Figure 2**).

<div style="text-align: center">
<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/KfBn3sfRNJLtqMEn0000.svg" width="700" style="padding: 0;">
</div>

**Figure 1 ([source](https://lamin.ai/laminlabs/arrayloader-benchmarks/artifact/AYfx4Nm2j0lpkkwK0000))**: Dataloader throughput on the Tahoe-100M dataset across three loaders, with `scDataset`[^dascenzo25] shown both with a matched block/chunk size and with its recommended settings. By clicking on `source`, you can navigate to the runs that produced the results. For example, the run producing the `annbatch` results is [here](https://lamin.ai/laminlabs/arrayloader-benchmarks/run/ZSuaqX3BWwLzwduW) with information about parameters, environment, and hardware (`ml.m5.24xlarge` on AWS).

<div style="text-align: center">
<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/yoNFOJbnwdn4dNa70002.png" width="1000" style="padding: 0;">
</div>

**Figure 2 ([explore](https://lamin.ai/laminlabs/arrayloader-benchmarks/artifact/AYfx4Nm2j0lpkkwK0000))**: Processing pipeline from the originally published Tahoe-100M, over pre-shuffled datasets, to running the data loader, to plotting Figure 1.

## Data & code availability

- Repo: [github.com/scverse/annbatch](https://github.com/scverse/annbatch)
- DB: [lamin.ai/laminlabs/arrayloader-benchmarks](https://github.com/laminlabs/arrayloader-benchmarks)
- Paper: [arXiv:2604.01949](https://arxiv.org/abs/2604.01949)

## Acknowledgements

We are grateful to Raaghav Pillai for re-running benchmarks with the latest versions after a long development process.
We thank Sergei Rybakov for early discussions, following the development of `MappedCollection`.
We thank Pavan Ramkumar for feedback and for validating early benchmarks.
We thank Davide D'Ascenzo and Sebastiano Cultrera di Montesano for discussions related to `scDataset`.

## References

[^gold26]: Gold I, Fischer F, Arnoldt L, Wolf FA & Theis FJ (2026). MCML - Annbatch Unlocks Terabyte-Scale Training of Biological Data in Anndata. [arXiv](https://arxiv.org/abs/2604.01949).

[^dascenzo25]: D'Ascenzo D & Cultrera di Montesano S (2025). scDataset: Scalable Data Loading for Deep Learning on Large-Scale Single-Cell Omics. [arXiv](https://arxiv.org/abs/2506.01883).

[^mappedcollection24]: Rybakov S, Fischer F, Wiatrak M, Gold I, Rosen Y, Sun S, Sriworarat C, Theis F, Kalfon J & Wolf A (2024). MappedCollection: Weighted random sampling from large collections of scRNA-seq datasets. Lamin Blog. [blog.lamin.ai/mapped-collection](https://blog.lamin.ai/mapped-collection).

[^scimilarity25]: Heimberg G, Kuo T, DePianto DJ, Salem O, Heigl T, Diamant N, Scalia G, Biancalani T, Turley SJ, Rock JR, Corrada Bravo H, Kaminker J, Vander Heiden JA & Regev A (2025). A cell atlas foundation model for scalable search of similar human cells. [Nature](https://www.nature.com/articles/s41586-024-08411-y).

[^cellarium22]: Cellarium AI (2022). Cellarium-ML: Distributed single-cell data analysis. [GitHub](https://github.com/cellarium-ai/cellarium-ml).

[^merlin20]: Oldridge E, Perez J, Frederickson B, Koumchatzky N, Lee M, Wang Z, Wu L, Yu F, Zamora R, Yilmaz O, Gunny A & Nguyen V (2020). Merlin: A GPU Accelerated Recommendation Framework. [ACM](https://doi.org/10.1145/3292500.3330823).

[^cellxgene-census-pytorch]: CELLxGENE Census experimental PyTorch data pipeline docs. [chanzuckerberg.github.io/cellxgene-census/notebooks/experimental/pytorch.html](https://chanzuckerberg.github.io/cellxgene-census/notebooks/experimental/pytorch.html).

[^virshup24]: Virshup I, Rybakov S, Theis FJ, Angerer P & Wolf FA (2024). anndata: Access and store annotated data matrices. _Journal of Open Source Software_, 9(101), 4371. [doi:10.21105/joss.04371](https://doi.org/10.21105/joss.04371).

[^zarr-v2]: Zarr developers (2024). Zarr storage format specification v2. [zarr-specs.readthedocs.io](https://zarr-specs.readthedocs.io/en/latest/v2/v2.0.html).

[^zhang25]: Zhang JQ et al. (2025). Tahoe-100M: A Giga-Scale Single-Cell Perturbation Atlas for Context-Dependent Gene Function and Cellular Modeling. [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.02.20.639398).

[^slaf]: Pavan Ramkumar (2025). SLAF: Sparse Lazy Array Format. [slaf-project.github.io](https://slaf-project.github.io/slaf/).
