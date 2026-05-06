---
title: "Re-engineering the PerturBench benchmarking tasks with data lineage"
date: 2026-05-06
author: ishitajain9717*, namsaraeva*, sunnyosun, yanwu2014, falexwolf
affiliation:
  ishitajain9717: Lamin Labs, Munich
  namsaraeva: Lamin Labs, Munich
  sunnyosun: Lamin Labs, Munich
  yanwu2014: Altos Labs, Redwood City
  falexwolf: Lamin Labs, Munich
db: https://lamin.ai/altoslabs/perturbench
repo: https://github.com/altoslabs/perturbench
tweet: TBD
linkedin: TBD
---

PerturBench (Wu, Wershof, Schmon, Nassar, Osinski, Eksi, Yan, et al., 2025)[^wu25] is a framework for benchmarking models that predict cellular transcriptional response to perturbations, featured in the Datasets and Benchmarks Track of NeurIPS 2025.
Reviewers agreed on the value of curated scRNA-seq datasets in combination with new rank-based metrics. The datasets were deposited on Hugging Face and the code on GitHub, but without data lineage.
To make it easy for anyone interested to understand how exactly each dataset and corresponding benchmarking task came about, we re-ran all curation workflows using lineage tracking, exemplify model training and evaluation, and show equivalence of the lineage-aware datasets with the originally deposited datasets.

While the situation is improving, published models in the field are often evaluated on inconsistent benchmarks, making it hard to know what works, and violating the common knowledge that all machine learning breakthroughs came from well-curated datasets and well-defined tasks. PerturBench is one of several efforts in the field and recently got featured in Valence Labs' MultiOmics Reading Group on YouTube: [youtube.com/watch?v=5M0HWIjmEhQ](https://www.youtube.com/watch?v=5M0HWIjmEhQ). Another prominent example is the [Arc Virtual Cell Challenge](https://virtualcellchallenge.org/).

Every benchmarking task is a dataset and a metric that quantifies how well a machine learning model predicts transcriptional response to perturbation.
Crucially important to the meaningfulness of the task is the meaningfulness of the dataset and the train/val/test splits, which depends on the exact steps taken during the data engineering workflow. PerturBench features six published datasets spanning genetic and chemical perturbations at different scales. The datasets originate from different labs, use different experimental protocols, and were originally stored in different formats: some as Seurat objects, others as `.h5ad` files. Getting them into a state where they can be used for a benchmarking task requires data wrangling across Python and R workflows: format conversion, quality control, normalization, metadata harmonization, and the construction of meaningful train/val/test splits.

The NeurIPS PerturBench submission hosts the six processed datasets at [huggingface.co/datasets/altoslabs/perturbench](https://huggingface.co/datasets/altoslabs/perturbench) as `.h5ad` files and separate `.csv` files encoding the splits. But these files alone don't reveal how the processing was done, what changed between versions, or how the train/val/test splits relate to the processed data.

<div style="text-align: center">
<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/RuJnsLkk9Bd7IRx90000.png" width="700">
</div>

To make data lineage easy to browse and understand, we re-ran all curation steps with `ln.track()` switched on in the [`altoslabs/perturbench`](https://lamin.ai/altoslabs/perturbench) database. You can explore it yourself by clicking on the link in the "Lineage" column of the following table.

| Dataset                                                                                | Perturbation type | Number of cells | Reference      | Lineage                                                                           |
| -------------------------------------------------------------------------------------- | ----------------- | --------------- | -------------- | --------------------------------------------------------------------------------- |
| [Norman19](https://lamin.ai/altoslabs/perturbench/artifact/givpxz10Nce9GZU7)           | Genetic           | 91,168 cells    | [^norman19]    | ![](https://lamin-site-assets.s3.amazonaws.com/.lamindb/rx0HTSN1zzdzXrQ20000.png) |
| [Srivatsan20](https://lamin.ai/altoslabs/perturbench/artifact/cFNvt9rQt0kEGkhj)        | Chemical          | 178,213 cells   | [^srivatsan20] | ![](https://lamin-site-assets.s3.amazonaws.com/.lamindb/QAlH61B4G7gvllzR0000.png) |
| [Frangieh21](https://lamin.ai/altoslabs/perturbench/artifact/eA1ej5uzGWKXrEax)         | Genetic           | 218,331 cells   | [^frangieh21]  | ![](https://lamin-site-assets.s3.amazonaws.com/.lamindb/LZrunW7bhaNpTMyx0000.png) |
| [McFalineFigueroa23](https://lamin.ai/altoslabs/perturbench/artifact/GnL8Spg9MReCzhrs) | Genetic           | 892,800 cells   | [^mcfaline23]  | ![](https://lamin-site-assets.s3.amazonaws.com/.lamindb/DWYAIVFtzMnWZZfZ0000.png) |
| [Jiang24](https://lamin.ai/altoslabs/perturbench/artifact/bEKTIM2ephr7Ks3t)            | Genetic           | 1,628,476 cells | [^jiang24]     | ![](https://lamin-site-assets.s3.amazonaws.com/.lamindb/JvxJOGt6DKI3hrWR0000.png) |
| [OP3](https://lamin.ai/altoslabs/perturbench/artifact/bY8zl3NwmHqYt5zT)                | Chemical          | 298,087 cells   | [^szalata24]   | ![](https://lamin-site-assets.s3.amazonaws.com/.lamindb/YrfaJYZRs0rRI5kj0000.png) |

On a high level, the steps are:

1. Raw data ingestion: We ingested all raw datasets from the PerturBench publication by registering them as LaminDB artifacts with URLs pointing to their original sources (e.g. Zenodo).
2. Curation: The PerturBench team developed dedicated curation notebooks (prefixed with `curate_`), handling format conversion, scRNA-seq preprocessing with scanpy, and metadata harmonization. We registered these notebooks as LaminDB transforms, linking them to their input and output artifacts to establish full lineage.
3. ML splits: The train/val/test splits from PerturBench's GitHub [repo](https://github.com/altoslabs/perturbench/tree/main/notebooks/neurips2025) were built through additional notebooks, which were also registered as transforms. For example, the Frangieh21 and Jiang24 splits were generated from the `build_jiang24_frangieh21_splits.ipynb` [notebook](https://lamin.ai/altoslabs/perturbench/transform/AdHN7pqkuP5J). Splits are stored as `.csv` artifacts linked to their corresponding processed datasets.
4. Training and eval examples: We loaded the curated datasets to train and evaluate models using the `PerturBench` framework.

Let us look at the example of the `Jiang24` and `Frangieh21` datasets:

<div style="text-align: center">
<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/X6UYqnvFVrsSXoqT0000.png" width="700">
</div>

Two curation pipelines converge on a shared split-building notebook. On the top path, four raw Seurat `.rds` files (IFNG, IFNB, INS, TGFB, and TNFA perturbation conditions) feed into `curate_Jiang24_step2.ipynb`, producing a processed `.h5ad.gz` file. On the bottom path, a raw `.h5ad` file (`Frangieh2021_RNA.h5ad`) feeds into `curate_Frangieh21.ipynb`, producing another processed `.h5ad.gz`. Both processed datasets then feed into `build_jiang24_frangieh21_splits.ipynb`, which produces two split artifacts: the Frangieh21 split shown here, and a Jiang24 split (not shown).

All six datasets in lamin contain the obs columns required by the PerturBench training pipeline (`condition`, `cell_type`, `treatment`, `perturbation_type`, `dose`, etc.). Five of them are byte-equivalent to the gzipped `.h5ad` files on HuggingFace (within the small tie-breaking noise of `seurat_v3` HVG selection across scanpy versions). Srivatsan20 is the exception: its HuggingFace upload was produced by the chemCPA preprocessing pipeline (Lotfollahi et al., 2022), not by `curate_Srivatsan20.ipynb`, so it ships with extra chemCPA-specific columns (`_scvi_cell_type`, `ood_split`, `perturbation_raw`) that the lamin curation does not reproduce. The lamin Srivatsan20 file is the output of the public curation notebook and is fully usable for PerturBench training.

The PerturBench repository ships pre-tuned Hydra configs for six baseline models — [CPA](https://github.com/altoslabs/perturbench/blob/main/src/perturbench/configs/model/cpa.yaml), [Biolord](https://github.com/altoslabs/perturbench/blob/main/src/perturbench/configs/model/biolord.yaml), [SAMS-VAE](https://github.com/altoslabs/perturbench/blob/main/src/perturbench/configs/model/sams_vae.yaml), [Linear additive](https://github.com/altoslabs/perturbench/blob/main/src/perturbench/configs/model/linear_additive.yaml), [Latent additive](https://github.com/altoslabs/perturbench/blob/main/src/perturbench/configs/model/latent_additive.yaml), and [Decoder only](https://github.com/altoslabs/perturbench/blob/main/src/perturbench/configs/model/decoder_only.yaml) — each tuned per dataset.

A typical run pulls a dataset and its matching split from lamin, then hands them to the trainer:

```python
import lamindb as ln

db = ln.DB("altoslabs/perturbench")
adata    = db.Artifact.get(key="norman19_cpa_hvg_normalized_curated.h5ad").load()
split_df = db.Artifact.get(key="split_6.csv").load()

# python -m perturbench.modelcore.train \
#     experiment=neurips2025/norman19/linear_best_params_norman19
```

## Author contributions

`*` These authors contributed equally.

Ishita & Altana curated the datasets, scripts, and notebooks with LaminDB.

Sunny & Yan advised on the project. Yan developed the original curation notebooks & scripts together with the authors of the original publication.[^wu25]

Alex supervised the project.

## Code & data availability

- database: [lamin.ai/altoslabs/perturbench](https://lamin.ai/altoslabs/perturbench)
- repo: [github.com/altoslabs/perturbench](https://github.com/altoslabs/perturbench)

## How to cite

```
Jain I, Namsaraeva A, Sun S, Wu Y & Wolf A (2026). The PerturBench datasets in LaminDB. Lamin Blog. https://blog.lamin.ai/perturbench
```

[^wu25]: Yan Wu, Esther Wershof, Sebastian M Schmon, Marcel Nassar, Błażej Osiński, Ridvan Eksi, Zichao Yan, Rory Stark, Kun Zhang, Thore Graepel. PerturBench: Benchmarking Machine Learning Models for Cellular Perturbation Analysis. The Thirty-ninth Annual Conference on Neural Information Processing Systems Datasets and Benchmarks Track 2025. https://openreview.net/forum?id=PPPDuyiZaG.

[^norman19]: Norman et al., Science 2019. https://doi.org/10.1126/science.aax4438

[^srivatsan20]: Srivatsan et al., Science 2020. https://doi.org/10.1126/science.aax6234

[^frangieh21]: Frangieh et al., Nat Genet. 2021. https://doi.org/10.1038/s41588-021-00779-1

[^mcfaline23]: McFaline-Figueroa et al., Cell Genomics 2024. https://doi.org/10.1016/j.xgen.2023.100487

[^jiang24]: Jiang et al., Nat Cell Biology 2025. https://doi.org/10.1038/s41556-025-01622-z

[^szalata24]: Szałata et al., NeurIPS 2024. https://openreview.net/forum?id=WTI4RJYSVm
