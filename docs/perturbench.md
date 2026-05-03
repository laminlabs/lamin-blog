---
title: "The PerturBench datasets in LaminDB"
date: 2026-04-05
author: namsaraeva*, ishitajain9717*, sunnyosun, yanwu2014, falexwolf
affiliation:
  namsaraeva: Lamin Labs, Munich
  ishitajain9717: Lamin Labs, Munich
  sunnyosun: Lamin Labs, Munich
  yanwu2014: Altos Labs, Redwood City
  falexwolf: Lamin Labs, Munich
db: https://lamin.ai/altoslabs/perturbench
repo: https://github.com/altoslabs/perturbench
tweet: TBD
linkedin: TBD
---

The PerturBench database contains six curated datasets for evaluating machine learning models that predict how cells' transcriptional states respond to genetic or chemical perturbations.

## The datasets

[PerturBench](https://github.com/altoslabs/perturbench) (Wu, Wershof, Shmon, Nassar, Osinski, Eksi, Yan et al., 2025)[^wu26] introduced a comprehensive framework for benchmarking machine learning (ML) models that predict single-cell transcriptomic responses to perturbations. It addresses the problem that published models are often evaluated on inconsistent benchmarks, making it hard to compare results across studies.
The framework includes six datasets spanning genetic and chemical perturbations at different scales:

| Dataset                                                                                | Perturbation type | Number of cells | Reference      | Lineage                                                                           |
| -------------------------------------------------------------------------------------- | ----------------- | --------------- | -------------- | --------------------------------------------------------------------------------- |
| [Norman19](https://lamin.ai/altoslabs/perturbench/artifact/givpxz10Nce9GZU7)           | Genetic           | 91,168 cells    | [^norman19]    | ![](https://lamin-site-assets.s3.amazonaws.com/.lamindb/rx0HTSN1zzdzXrQ20000.png) |
| [Srivatsan20](https://lamin.ai/altoslabs/perturbench/artifact/cFNvt9rQt0kEGkhj)        | Chemical          | 178,213 cells   | [^srivatsan20] | ![](https://lamin-site-assets.s3.amazonaws.com/.lamindb/QAlH61B4G7gvllzR0000.png) |
| [Frangieh21](https://lamin.ai/altoslabs/perturbench/artifact/eA1ej5uzGWKXrEax)         | Genetic           | 218,331 cells   | [^frangieh21]  | ![](https://lamin-site-assets.s3.amazonaws.com/.lamindb/LZrunW7bhaNpTMyx0000.png) |
| [McFalineFigueroa23](https://lamin.ai/altoslabs/perturbench/artifact/GnL8Spg9MReCzhrs) | Genetic           | 892,800 cells   | [^mcfaline23]  | ![](https://lamin-site-assets.s3.amazonaws.com/.lamindb/DWYAIVFtzMnWZZfZ0000.png) |
| [Jiang24](https://lamin.ai/altoslabs/perturbench/artifact/bEKTIM2ephr7Ks3t)            | Genetic           | 1,628,476 cells | [^jiang24]     | ![](https://lamin-site-assets.s3.amazonaws.com/.lamindb/JvxJOGt6DKI3hrWR0000.png) |
| [OP3](https://lamin.ai/altoslabs/perturbench/artifact/bY8zl3NwmHqYt5zT)                | Chemical          | 298,087 cells   | [^szalata24]   | ![](https://lamin-site-assets.s3.amazonaws.com/.lamindb/YrfaJYZRs0rRI5kj0000.png) |

These datasets originate from different labs, use different experimental protocols, and were originally stored in different formats: some as Seurat objects, others as `.h5ad` files. Getting them into a state where ML models can be trained on them requires substantial data wrangling: format conversion, quality control, normalization, metadata harmonization, and the construction of meaningful train/val/test splits.

The original PerturBench codebase hosts processed datasets on [Hugging Face](https://huggingface.co/datasets/altoslabs/perturbench/tree/main) as gzipped `.h5ad` files. But these files alone don't reveal how the processing was done, what changed between versions, or how the train/val/test splits relate to the processed data.

All six datasets in lamin contain the obs columns required by the PerturBench training pipeline (`condition`, `cell_type`, `treatment`, `perturbation_type`, `dose`, etc.). Five of them are byte-equivalent to the gzipped `.h5ad` files on HuggingFace (within the small tie-breaking noise of `seurat_v3` HVG selection across scanpy versions). Srivatsan20 is the exception: its HuggingFace upload was produced by the chemCPA preprocessing pipeline (Lotfollahi et al., 2022), not by `curate_Srivatsan20.ipynb`, so it ships with extra chemCPA-specific columns (`_scvi_cell_type`, `ood_split`, `perturbation_raw`) that the lamin curation does not reproduce. The lamin Srivatsan20 file is the output of the public curation notebook and is fully usable for PerturBench training.

## How it differs from pertdata

[Pertdata](https://lamin.ai/laminlabs/pertdata) is a broad collection of perturbational single-cell datasets, currently around 25, spanning genetic and chemical perturbations across many tissues and cell systems. It is designed to give researchers easy programmatic access to as many published perturbation screens as possible, in a consistent AnnData layout.

PerturBench has a narrower goal: a *fixed* benchmark for comparing perturbation-prediction models. It includes six datasets selected to cover distinct prediction tasks — combinatorial CRISPRa (Norman19), large-scale chemical screens (Srivatsan20, McFaline23), Perturb-CITE-seq (Frangieh21), multi-stimulus CRISPRi (Jiang24), and a NeurIPS competition dataset (OP3). For each, the repository ships pre-defined splits and tuned model hyperparameters, so a benchmark number on one of these datasets is directly comparable across publications.

The two databases are complementary: pertdata for breadth and exploration, PerturBench for reproducible model evaluation against a community-vetted baseline.

## The datasets in LaminDB

The [`altoslabs/perturbench`](https://lamin.ai/altoslabs/perturbench) database captures the entire curation and split-building pipeline with full data lineage. Here's what's inside:

- **Raw data ingestion.** We ingested all raw datasets from the PerturBench publication by registering them as LaminDB artifacts with URLs pointing to their original sources (e.g. Zenodo).
- **Curation transforms.** The PerturBench team developed dedicated curation notebooks (prefixed with `curate_`), handling format conversion, scRNA-seq preprocessing with scanpy, and metadata harmonization. We registered these notebooks as LaminDB transforms, linking them to their input and output artifacts to establish full lineage.
- **ML split construction.** The train/val/test splits from PerturBench's GitHub [repo](https://github.com/altoslabs/perturbench/tree/main/notebooks/neurips2025) were built through additional notebooks, which were also registered as transforms. For example, the Frangieh21 and Jiang24 splits were generated from the `build_jiang24_frangieh21_splits.ipynb` [notebook](https://lamin.ai/altoslabs/perturbench/transform/AdHN7pqkuP5J). Splits are stored as `.csv` artifacts linked to their corresponding processed datasets.
- **Fetching the datasets from LaminDB.** The datasets can be fetched from lamindb using `ln.Artifact.get(key=...)`. For more on querying and loading artifacts, see the [lamindb query/search docs](https://docs.lamin.ai/query-search).

The process can be visualized in the data lineage graph, for example, for the Jiang24 and Frangieh21 datasets:

<div style="text-align: center">
<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/X6UYqnvFVrsSXoqT0000.png" width="700">
</div>

Two curation pipelines converge on a shared split-building notebook. On the top path, four raw Seurat `.rds` files (IFNG, IFNB, INS, TGFB, and TNFA perturbation conditions) feed into `curate_Jiang24_step2.ipynb`, producing a processed `.h5ad.gz` file. On the bottom path, a raw `.h5ad` file (`Frangieh2021_RNA.h5ad`) feeds into `curate_Frangieh21.ipynb`, producing another processed `.h5ad.gz`. Both processed datasets then feed into `build_jiang24_frangieh21_splits.ipynb`, which produces two split artifacts: the Frangieh21 split shown here, and a Jiang24 split (not shown).

## Explore the database

The database is publicly available at [lamin.ai/altoslabs/perturbench](https://lamin.ai/altoslabs/perturbench). You can browse all artifacts, inspect lineage graphs, and see which transforms produced which outputs. To access the data programmatically:

```python
import lamindb as ln

# connect the database
db = ln.DB("altoslabs/perturbench")

# list artifacts in the database
df = db.Artifact.to_dataframe()

# query the processed Frangieh21 dataset
artifact = db.Artifact.get(description="Frangieh21 processed dataset")

# describe the context of that artifact
artifact.describe()

# load an AnnData object into memory
adata = artifact.load()
```

## Using the datasets to train a model

The PerturBench repository ships pre-tuned Hydra configs for six baseline models — [CPA](https://github.com/altoslabs/perturbench/blob/main/src/perturbench/configs/model/cpa.yaml), [Biolord](https://github.com/altoslabs/perturbench/blob/main/src/perturbench/configs/model/biolord.yaml), [SAMS-VAE](https://github.com/altoslabs/perturbench/blob/main/src/perturbench/configs/model/sams_vae.yaml), [Linear additive](https://github.com/altoslabs/perturbench/blob/main/src/perturbench/configs/model/linear_additive.yaml), [Latent additive](https://github.com/altoslabs/perturbench/blob/main/src/perturbench/configs/model/latent_additive.yaml), and [Decoder only](https://github.com/altoslabs/perturbench/blob/main/src/perturbench/configs/model/decoder_only.yaml) — each tuned per dataset.

A typical run pulls a dataset and its matching split from lamin, then hands them to the trainer:

```python
import lamindb as ln

adata    = ln.Artifact.get(key="norman19_cpa_hvg_normalized_curated.h5ad").load()
split_df = ln.Artifact.get(key="split_6.csv").load()

# python -m perturbench.modelcore.train \
#     experiment=neurips2025/norman19/linear_best_params_norman19
```

## Work in progress

A follow-up post will discuss metadata management of perturbational datasets in depth. Defining and standardizing metadata for perturbation experiments, from perturbation type and dosage to control definitions and cell state annotations.

## Author contributions

`*` These authors contributed equally.

Altana & Ishita curated the datasets, scripts, and notebooks with LaminDB.

Sunny & Yan advised on the project. Yan developed the original curation notebooks & scripts.

Alex supervised the project.

## Code & data availability

- Database: [lamin.ai/altoslabs/perturbench](https://lamin.ai/altoslabs/perturbench)
- PerturBench GitHub repository: [github.com/altoslabs/perturbench](https://github.com/altoslabs/perturbench)
- PerturBench publication: [arxiv.org/abs/2408.10609](https://arxiv.org/abs/2408.10609)
- Datasets on HuggingFace: [https://huggingface.co/datasets/altoslabs/perturbench/tree/main](https://huggingface.co/datasets/altoslabs/perturbench/tree/main)

## How to cite

```
Namsaraeva A, Wu Y, Wolf A & Sun S (2026). The PerturBench datasets in LaminDB. Lamin Blog. https://blog.lamin.ai/perturbench
```

[^wu26]: Yan Wu, Esther Wershof, Sebastian M Schmon, Marcel Nassar, Błażej Osiński, Ridvan Eksi, Zichao Yan, Rory Stark, Kun Zhang, Thore Graepel. PerturBench: Benchmarking Machine Learning Models for Cellular Perturbation Analysis. https://arxiv.org/abs/2408.10609.

[^norman19]: Norman et al., Science 2019. https://doi.org/10.1126/science.aax4438

[^srivatsan20]: Srivatsan et al., Science 2020. https://doi.org/10.1126/science.aax6234

[^frangieh21]: Frangieh et al., Nat Genet. 2021. https://doi.org/10.1038/s41588-021-00779-1

[^mcfaline23]: McFaline-Figueroa et al., Cell Genomics 2024. https://doi.org/10.1016/j.xgen.2023.100487

[^jiang24]: Jiang et al., Nat Cell Biology 2025. https://doi.org/10.1038/s41556-025-01622-z

[^szalata24]: Szałata et al., NeurIPS 2024. https://openreview.net/forum?id=WTI4RJYSVm
