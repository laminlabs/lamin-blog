---
title: "Re-engineering the PerturBench benchmarking tasks with data lineage"
date: 2026-05-12
author: ishitajain9717*, namsaraeva*, sunnyosun, yanwu2014, falexwolf
affiliation:
  ishitajain9717: Lamin Labs, Munich
  namsaraeva: Lamin Labs, Munich
  sunnyosun: Lamin Labs, Munich
  yanwu2014: Altos Labs, Redwood City
  falexwolf: Lamin Labs, Munich
db: https://lamin.ai/altoslabs/perturbench
repo: https://github.com/altoslabs/perturbench
linkedin: https://www.linkedin.com/feed/update/urn:li:activity:7459877823147679744/
tweet: https://x.com/falexwolf/status/2054113103449665731
---

PerturBench (Wu, Wershof, Schmon, Nassar, Osinski, Eksi, Yan, et al., NeurIPS 2025) is a framework for benchmarking machine learning models that predict cellular transcriptional response to perturbations.
Its core contributions are benchmarking tasks in the form of curated datasets and definitions of metrics, which are available from GitHub and Hugging Face, albeit without data lineage.
To make it easy to see how exactly each dataset came about and assess model performance in light of that context, we re-ran all curation workflows using lineage tracking.
We exemplify model training and evaluation, and show equivalence of the re-curated datasets with the originally deposited datasets.

While the situation has been improving in recent years through efforts like PerturBench[^wu25], published scRNA-seq-based models have often been evaluated on inconsistent benchmarks, making it hard to know what works and going counter to the fact that machine learning breakthroughs need well-curated datasets and well-defined tasks. PerturBench is one of several efforts in the field and was preceded by an [Open Problems benchmark](https://openproblems.bio/benchmarks/perturbation_prediction), published at NeurIPS 2024[^szalata24]. Another example for a similar benchmarking effort is last year's [Arc Virtual Cell Challenge](https://virtualcellchallenge.org/). For a video introduction to PerturBench, you can watch [this episode](https://youtu.be/5M0HWIjmEhQ) of Valence Labs' MultiOmics Reading Group.

The NeurIPS PerturBench submission hosts its six curated benchmarking datasets on [Hugging Face](https://huggingface.co/datasets/altoslabs/perturbench). These files, however, don't reveal how the curation was done.

<div style="text-align: center">
<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/RuJnsLkk9Bd7IRx90000.png" width="700" style="padding: 0;">
</div>

To make data lineage easy to browse and understand, we re-ran all curation steps with `ln.track()` added to the source code. You can explore the result by clicking on the link in the "Dataset + lineage" column of the following table.

| Reference                   | Perturbation | _N_             | Dataset + lineage (click the image to explore)                                                                                                                                                            |
| --------------------------- | ------------ | --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Norman19[^norman19]         | Genetic      | 91,168 cells    | <a href="https://lamin.ai/altoslabs/perturbench/artifact/DbIfhUaqAkOyJOZw"><img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/F5wgWWNMTGx9BL5I0000.png" alt="Lineage" style="padding: 0;"></a> |
| Srivatsan20[^srivatsan20]   | Chemical     | 178,213 cells   | <a href="https://lamin.ai/altoslabs/perturbench/artifact/sUlZYMsyLUPaAmap"><img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/Nw7jvVRZFYn50iEx0000.png" alt="Lineage" style="padding: 0;"></a> |
| Frangieh21[^frangieh21]     | Genetic      | 218,331 cells   | <a href="https://lamin.ai/altoslabs/perturbench/artifact/buJK5JWkcSlNifNv"><img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/Arcmerp1lo9Jh0EL0000.png" alt="Lineage" style="padding: 0;"></a> |
| McFaline24[^mcfaline24]     | Genetic      | 892,800 cells   | <a href="https://lamin.ai/altoslabs/perturbench/artifact/XeHoYYNbB9Xnf09i"><img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/B6E8PdS8KPMSkpg10000.png" alt="Lineage" style="padding: 0;"></a> |
| Jiang25[^jiang25]           | Genetic      | 1,628,476 cells | <a href="https://lamin.ai/altoslabs/perturbench/artifact/AFAZw9hLdUIQ2Szo"><img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/UfXbBKqBCJriJ4cd0000.png" alt="Lineage" style="padding: 0;"></a> |
| Szalata24 (OP3)[^szalata24] | Chemical     | 298,087 cells   | <a href="https://lamin.ai/altoslabs/perturbench/artifact/gxem2yy0fsOYQmMC"><img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/9dVOWgE09CdziuXM0000.png" alt="Lineage" style="padding: 0;"></a> |

On a high level, the data flow is:

1. Raw data ingestion: Each dataset has a dedicated notebook (prefixed with `ingestion_`) that ingests raw datasets.
2. Curation: Curation notebooks (prefixed with `curate_`) handle format conversion, preprocessing, metadata harmonization, and split generation.
3. Training and eval: Curated datasets are loaded to train and evaluate models using the `PerturBench` Python framework.

For a comparison that shows the equivalence of the original datasets and the re-curated datasets, explore [altoslabs/perturbench/transform/3bZAUr0kXokI](https://lamin.ai/altoslabs/perturbench/transform/3bZAUr0kXokI). For a full training and model evaluation run, explore [altoslabs/perturbench/transform/9dPgCiisCm1w](https://lamin.ai/altoslabs/perturbench/transform/9dPgCiisCm1w).

This post was motivated by the desire to reproduce PerturBench's training and eval results in a file-centric manner, omitting the detailed modeling of perturbational & biological metadata. Modeling and validating perturbations will be the topic of an upcoming post.

## Author contributions

`*` These authors contributed equally.

Ishita & Altana performed the computational work.

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

[^mcfaline24]: McFaline-Figueroa JL, Srivatsan SR, Hill AJ, Gasperini M, Jackson DL, Saunders L, Domcke S, Regalado SG, Lazarchuck P, Alvarez S, Monnat RJ Jr, Shendure J & Trapnell C (2024). Multiplex single-cell chemical genomics reveals the kinase dependence of the response to targeted therapy. [Cell Genomics](https://doi.org/10.1016/j.xgen.2023.100487).

[^jiang25]: Jiang L, Dalgarno C, Papalexi E, Mascio I, Wessels HH, Yun H & Satija R (2025). Systematic reconstruction of molecular pathway signatures using scalable single-cell perturbation screens. [Nature Cell Biology](https://doi.org/10.1038/s41556-025-01622-z).

[^szalata24]: Szałata A, Benz A, Cannoodt R, Cortes M, Fong J, Kuppasani S, Lieberman R, Liu T, Mas-Rosario JA, Meinl R, Nourisa J, Tumiel J, Tunjic TM, Wang M, Weber N, Zhao H, Anchang B, Theis FJ, Luecken MD & Burkhardt DB (2024). A Benchmark for Prediction of Transcriptomic Responses to Chemical Perturbations Across Cell Types. [NeurIPS](https://openreview.net/forum?id=WTI4RJYSVm).
