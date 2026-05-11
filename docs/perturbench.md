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

PerturBench (Wu, Wershof, Schmon, Nassar, Osinski, Eksi, Yan, et al., NeurIPS 2025) is a framework for benchmarking scRNA-seq based machine learning models that predict transcriptional response to perturbations.
Its core contribution are benchmarking tasks in form of curated datasets and definitions of metrics. They are available from GitHub and Hugging Face, but without data lineage.
To make it easy to understand how exactly each dataset came about and assess model performance in light of that context, we re-ran all curation workflows using lineage tracking.
We also exemplify model training and evaluation, and show equivalence of the lineage-aware datasets with the originally deposited datasets.

While the situation has been improving in recent years through efforts like PerturBench[^wu25], published scRNA-seq-based models have often been evaluated on inconsistent benchmarks, making it hard to know what works and going counter the fact that all machine learning breakthroughs so far originated in well-curated datasets and well-defined tasks. PerturBench is one of several efforts in the field and recently got featured in Valence Labs' MultiOmics Reading Group: [youtu.be/5M0HWIjmEhQ](https://youtu.be/5M0HWIjmEhQ). Another recent prominent example is the [Arc Virtual Cell Challenge](https://virtualcellchallenge.org/), while a similar NeurIPS 2024 contribution came in form of an [Open Problems benchmark](https://openproblems.bio/benchmarks/perturbation_prediction)[^szalata24].

Every benchmarking task in PerturBench is a dataset and a metric that quantifies how well a machine learning model predicts transcriptional response to perturbation.
Important to the meaningfulness of the task is the distribution of the dataset and the train/val/test splits, which depends on the exact steps taken during the curation workflow. PerturBench features six published datasets spanning genetic and chemical perturbations at different scales. The datasets originate from different labs, use different experimental protocols, and were originally stored in different formats: some as Seurat objects, others as `.h5ad` files. Getting them into a state where they can be used for benchmarking requires data wrangling across Python and R workflows: format conversion, quality control, normalization, metadata harmonization, and the construction of train/val/test splits.

The NeurIPS PerturBench submission hosts the six processed datasets at [huggingface.co/datasets/altoslabs/perturbench](https://huggingface.co/datasets/altoslabs/perturbench) as `.h5ad` files, with splits encoded in the `.obs` metadata of the corresponding `AnnData` objects, and in separate `.csv` files. These files alone don't reveal how the processing was done, what changed between versions, and how the train/val/test splits relate to the processed data.

<div style="text-align: center">
<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/RuJnsLkk9Bd7IRx90000.png" width="700" style="padding: 0;">
</div>

To make data lineage easy to browse and understand, we re-ran all curation steps with `ln.track()` switched on in the [`altoslabs/perturbench`](https://lamin.ai/altoslabs/perturbench) database. You can explore it by clicking on the link in the "Lineage" column of the following table.

| Reference                   | Perturbation type | Number of cells | Dataset + lineage (click the image to explore)                                                                                                                                                            |
| --------------------------- | ----------------- | --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Norman19[^norman19]         | Genetic           | 91,168 cells    | <a href="https://lamin.ai/altoslabs/perturbench/artifact/DbIfhUaqAkOyJOZw"><img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/MTyaI1pyHs5kjyVB0000.png" alt="Lineage" style="padding: 0;"></a> |
| Srivatsan20[^srivatsan20]   | Chemical          | 178,213 cells   | <a href="https://lamin.ai/altoslabs/perturbench/artifact/sUlZYMsyLUPaAmap"><img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/T0TyPozsu58ILgGo0000.png" alt="Lineage" style="padding: 0;"></a> |
| Frangieh21[^frangieh21]     | Genetic           | 218,331 cells   | <a href="https://lamin.ai/altoslabs/perturbench/artifact/buJK5JWkcSlNifNv"><img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/qCyM0WSAy85xAUVP0000.png" alt="Lineage" style="padding: 0;"></a> |
| McFaline23[^mcfaline23]     | Genetic           | 892,800 cells   | <a href="https://lamin.ai/altoslabs/perturbench/artifact/XeHoYYNbB9Xnf09i"><img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/OPVOGgL5SdieRsKD0000.png" alt="Lineage" style="padding: 0;"></a> |
| Jiang24[^jiang24]           | Genetic           | 1,628,476 cells | <a href="https://lamin.ai/altoslabs/perturbench/artifact/AFAZw9hLdUIQ2Szo"><img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/W09MZX1rF83cAwlo0000.png" alt="Lineage" style="padding: 0;"></a> |
| Szalata24 (OP3)[^szalata24] | Chemical          | 298,087 cells   | <a href="https://lamin.ai/altoslabs/perturbench/artifact/gxem2yy0fsOYQmMC"><img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/j5gok9AQHj3mt7FP0000.png" alt="Lineage" style="padding: 0;"></a> |

On a high level, the steps are:

1. Raw data ingestion: We ingested the raw datasets with lineage tracking enabled. Each dataset has a dedicated notebook (prefixed with `ingestion_`) that registers the raw artifacts in the LaminDB instance.
2. Curation: The PerturBench team developed dedicated curation notebooks (prefixed with `curate_`), handling format conversion, scRNA-seq preprocessing with scanpy, and metadata harmonization. We registered these notebooks as LaminDB transforms, and inputs (raw data) and outputs (processed data) as artifacts to establish full lineage.
3. ML splits: The train/val/test splits from PerturBench's GitHub [repo](https://github.com/altoslabs/perturbench/tree/main/notebooks/neurips2025) were built through additional notebooks, which were also registered as transforms. For example, the Frangieh21 and Jiang24 splits were generated from the curate_Frangieh21 [notebook](https://lamin.ai/altoslabs/perturbench/run/tlDauKQm4uS1OVsm) and curate_jiang24 [notebook](https://lamin.ai/altoslabs/perturbench/transform/AwSoPNuxC6Ol) respectively. Splits for the datasets are also registered as artifacts.
4. Training and eval examples: We loaded the curated datasets to train and evaluate models using the `PerturBench` framework.

Let us look at the example of the `Jiang24` and `Frangieh21` datasets (lineages shown in table):

Raw Seurat .rds files (IFNG, IFNB, INS, TGFB, and TNFA perturbation conditions) feed into `curate_jiang24.ipynb`, producing a processed `.h5ad` file. In the second lineage shown, a raw `.h5ad` file (`frangieh21.h5ad`) feeds into `curate_Frangieh21.ipynb`, producing another processed `.h5ad`. Both datasets are used to generate splits, which produces two split artifacts: the Frangieh21 split shown here, and a Jiang24 split (not shown).

All six datasets in lamin contain the obs columns required by the PerturBench training pipeline (`condition`, `cell_type`, `treatment`, `perturbation_type`, `dose`, etc.). Five of them are byte-equivalent to the gzipped `.h5ad` files on HuggingFace (within the small tie-breaking noise of `seurat_v3` HVG selection across scanpy versions). Srivatsan20 is the exception: its HuggingFace upload was produced by the chemCPA preprocessing pipeline [Srivatsan et al., 2019](https://www.science.org/doi/10.1126/science.aax6234), not by `curate_Srivatsan20.ipynb`, so it ships with extra chemCPA-specific columns (`_scvi_cell_type`, `ood_split`, `perturbation_raw`) that the lamin curation does not reproduce. The lamin Srivatsan20 file is the output of the public curation notebook and is fully usable for PerturBench training.

For a full training and model evaluation run, see, [`Jiang24 dataset`](https://lamin.ai/altoslabs/perturbench/transform/Que2xKjA1byH). For a smaller counter part see `Norman19 dataset` (https://lamin.ai/altoslabs/perturbench/transform/KxV14blvjANl).
We compared validation loss curves and evaluation/summary metrics.

For a comparison showing equivalence of the original datasets and the re-curated datasets, see [lamin.ai/altoslabs/perturbench/transform/3bZAUr0kXokI](https://lamin.ai/altoslabs/perturbench/transform/3bZAUr0kXokI).

## Author contributions

`*` These authors contributed equally.

Ishita & Altana curated the datasets, scripts, and notebooks with LaminDB.

Sunny & Yan advised on the project. Yan developed the original curation notebooks & scripts together with the authors of the original publication.

Alex supervised the project.

## Code & data availability

Database: [lamin.ai/altoslabs/perturbench](https://lamin.ai/altoslabs/perturbench). Repo: [github.com/altoslabs/perturbench](https://github.com/altoslabs/perturbench).

## How to cite

```
Jain I, Namsaraeva A, Sun S, Wu Y & Wolf A (2026). Re-engineering the PerturBench benchmarking tasks with data lineage. Lamin Blog. https://blog.lamin.ai/perturbench
```

## References

[^wu25]: Wu Y, Wershof E, Schmon SM, Nassar M, Osiński B, Eksi R, Yan Z, Stark R, Zhang K & Graepel T (2025). PerturBench: Benchmarking Machine Learning Models for Cellular Perturbation Analysis. [NeurIPS](https://openreview.net/forum?id=PPPDuyiZaG).

[^norman19]: Norman TM, Horlbeck MA, Replogle JM, Ge AY, Xu A, Jost M, Gilbert LA & Weissman JS (2019). Exploring genetic interaction manifolds constructed from rich single-cell phenotypes. [Science](https://doi.org/10.1126/science.aax4438).

[^srivatsan20]: Srivatsan SR, McFaline-Figueroa JL, Ramani V, Saunders L, Cao J, Packer J, Pliner HA, Jackson DL, Daza RM, Christiansen L, Zhang DA, Steemers F, Shendure J & Trapnell C (2020). Massively multiplex chemical transcriptomics at single-cell resolution. [Science](https://doi.org/10.1126/science.aax6234).

[^frangieh21]: Frangieh CJ, Melms JC, Thakore PI, Geiger-Schuller KR, Ho P, Luoma AM, Cleary B, Jerby-Arnon L, Garg S, Regev A & Izar B (2021). Multimodal pooled Perturb-CITE-seq screens in patient models define mechanisms of cancer immune evasion. [Nature Genetics](https://doi.org/10.1038/s41588-021-00779-1).

[^mcfaline23]: McFaline-Figueroa JL, Srivatsan SR, Hill AJ, Gasperini M, Jackson DL, Saunders L, Domcke S, Regalado SG, Lazarchuck P, Alvarez S, Monnat RJ Jr, Shendure J & Trapnell C (2024). Multiplex single-cell chemical genomics reveals the kinase dependence of the response to targeted therapy. [Cell Genomics](https://doi.org/10.1016/j.xgen.2023.100487).

[^jiang24]: Jiang L, Dalgarno C, Papalexi E, Mascio I, Wessels HH, Yun H & Satija R (2025). Systematic reconstruction of molecular pathway signatures using scalable single-cell perturbation screens. [Nature Cell Biology](https://doi.org/10.1038/s41556-025-01622-z).

[^szalata24]: Szałata A, Benz A, Cannoodt R, Cortes M, Fong J, Kuppasani S, Lieberman R, Liu T, Mas-Rosario JA, Meinl R, Nourisa J, Tumiel J, Tunjic TM, Wang M, Weber N, Zhao H, Anchang B, Theis FJ, Luecken MD & Burkhardt DB (2024). A Benchmark for Prediction of Transcriptomic Responses to Chemical Perturbations Across Cell Types. [NeurIPS](https://openreview.net/forum?id=WTI4RJYSVm).
