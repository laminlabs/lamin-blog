---
title: "Tracking PerturBench datasets with LaminDB: Full lineage from raw data to ML-ready splits"
date: 2026-02-24
author: namsaraeva, sunnyosun, yanwu2024, falexwolf
orcid:
  namsaraeva: 0000-0001-6071-9410
  sunnyosun: 0000-0002-2365-0888
  falexwolf: 0000-0002-8760-7838
affiliation:
  namsaraeva: Lamin Labs, Munich
  sunnyosun: Lamin Labs, Munich
  yanwu2024: Altos Labs, Redwood City
  falexwolf: Lamin Labs, Munich
db: https://lamin.ai/altoslabs/perturbench
repo: https://github.com/altoslabs/perturbench
tweet: TBD
linkedin: TBD
---

---

Perturbation response prediction — training ML models to predict how cells respond to genetic or chemical perturbations — is a rapidly growing area in computational biology. However, before you can benchmark any model, you need clean, well-curated data with a clear record of how it was processed. 

We used LaminDB to track all datasets and curation notebooks from the [PerturBench](https://arxiv.org/abs/2408.10609) publication, and the result is a [public Lamin instance](https://lamin.ai/altoslabs/perturbench).

---

## Why perturbation benchmarking needs data infrastructure

[PerturBench](https://github.com/altoslabs/perturbench) (Wu, Wershof, Schmon, Nassar et al., 2025) introduced a comprehensive framework for benchmarking ML models that predict single-cell transcriptomic responses to perturbations. It tackles a real problem: published models are often evaluated on inconsistent benchmarks with different datasets and metrics, making it hard to know what actually works.

The framework includes six diverse datasets spanning genetic and chemical perturbations at different scales:

| Dataset | Perturbation type | Scale | Source |
|---|---|---|---|
| Norman19 | Genetic | 91,168 cells | [Norman et al., Science 2019](https://doi.org/10.1126/science.aax4438) |
| Srivatsan20 | Chemical | 178,213 cells | [Srivatsan et al., Science 2020](https://doi.org/10.1126/science.aax6234) |
| Frangieh21 | Genetic | 218,331 cells | [Frangieh et al., Nat Genet. 2021](https://doi.org/10.1038/s41588-021-00779-1) |
| McFalineFigueroa23 | Genetic | 892,800 cells | [McFaline-Figueroa et al., Cell Genomics 2024](https://doi.org/10.1016/j.xgen.2023.100487) |
| Jiang24 | Genetic | 1,628,476 cells | [Jiang et al., Nat Cell Biology 2025](https://doi.org/10.1038/s41556-025-01622-z) |
| OP3 | Chemical | 298,087 cells | [Szałata et al., NeurIPS 2024](https://openreview.net/forum?id=WTI4RJYSVm) |

These datasets originate from different labs, use different experimental protocols, and were originally stored in different formats: some as Seurat objects, others as `.h5ad` files. Getting them into a state where ML models can train on them requires substantial data wrangling: format conversion, quality control, normalization, metadata harmonization, and the construction of meaningful train/val/test splits.

The original PerturBench codebase hosts processed datasets on [Hugging Face](https://huggingface.co/datasets/altoslabs/perturbench/tree/main) as gzipped `.h5ad` files. But these files alone don't tell you _how_ the processing was done, _what_ changed between versions, or _how_ the train/val/test splits relate to the processed data. This is where LaminDB helps.

## What we built

The [`altoslabs/perturbench`](https://lamin.ai/altoslabs/perturbench) Lamin instance captures the entire curation and split-building pipeline with full data lineage. Here's what's inside:

**Raw data ingestion.** We ingested all raw datasets from the PerturBench publication: registering them as LaminDB artifacts with URLs pointing to their original sources (e.g. Zenodo).

**Curation transforms.** The PerturBench team developed dedicated curation notebooks (prefixed with `curate_`), handling format conversion, scRNA-seq preprocessing with scanpy, and metadata harmonization. We registered these notebooks as LaminDB transforms, linking them to their input and output artifacts to establish full lineage.

**ML split construction.** The train/val/test splits from PerturBench's GitHub [repo](https://github.com/altoslabs/perturbench/tree/main/notebooks/neurips2025) were built through additional notebooks, which were also registered as transforms. For example, the Frangieh21 and Jiang24 splits were generated from the `build_jiang24_frangieh21_splits.ipynb` [notebook](https://lamin.ai/altoslabs/perturbench/transform/AdHN7pqkuP5J). Splits are stored as `.csv` artifacts linked to their corresponding processed datasets.

## Clean lineage from raw data to ML splits

The real advantage is visible in the lineage graphs. Take the lineage of Jiang24 and Frangieh21 datasets as an example (**Figure 1**):

<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/X6UYqnvFVrsSXoqT0000.png" width="700">

**Figure 1**: Lineage graph for the Jiang24 and Frangieh21 datasets on [lamin.ai/altoslabs/perturbench](https://lamin.ai/altoslabs/perturbench). Two curation pipelines converge on a shared split-building notebook. On the top path, four raw Seurat `.rds` files (IFNG, IFNB, INS, TGFB, and TNFA perturbation conditions) feed into `curate_Jiang24_step2.ipynb`, producing a processed `.h5ad.gz` file. On the bottom path, a raw `.h5ad` file (`Frangieh2021_RNA.h5ad`) feeds into `curate_Frangieh21.ipynb`, producing another processed `.h5ad.gz`. Both processed datasets then feed into `build_jiang24_frangieh21_splits.ipynb`, which produces two split artifacts: the Frangieh21 split shown here, and a Jiang24 split (not shown).

The lineage graph reads left to right: raw input → curation notebook → processed dataset → split-building notebook → ML-ready splits. Every node is a tracked artifact or transform with a unique identifier. This gives you an advantage of **traceability**. If a model produces unexpected results on a particular dataset, you can trace the training data all the way back to the raw source. The lineage graph makes it immediately clear which raw file, which curation script, and which split-building step were involved.

## Explore the instance

The full instance is publicly available at [lamin.ai/altoslabs/perturbench](https://lamin.ai/altoslabs/perturbench). You can browse all artifacts, inspect lineage graphs, and see which transforms produced which outputs. To access the data programmatically:

```python
import lamindb as ln

# connect to the instance
db = ln.DB("altoslabs/perturbench")

# list all artifacts
df = db.Artifact.to_dataframe()

# access the processed Frangieh21 dataset
artifact = db.Artifact.get(description="Frangieh21 processed dataset")
adata = artifact.load()
```

## Author contributions

Altana ingested all raw datasets and registered PerturBench's curation notebooks as transforms in the Lamin instance, and wrote the post.

Sunny supervised Altana and provided technical and scientific feedback, and reviewed the post.

Yan developed the curation and preprocessing notebooks and provided the datasets.

Alex supervised the work and reviewed the post.

## Code & data availability

- Lamin instance: [lamin.ai/altoslabs/perturbench](https://lamin.ai/altoslabs/perturbench)
- PerturBench GitHub repository: [github.com/altoslabs/perturbench](https://github.com/altoslabs/perturbench)
- PerturBench publication: [arxiv.org/abs/2408.10609](https://arxiv.org/abs/2408.10609)
- Datasets on Hugging Face: [https://huggingface.co/datasets/altoslabs/perturbench/tree/main](https://huggingface.co/datasets/altoslabs/perturbench/tree/main)

## Citation

```
Namsaraeva A, Sun S, Wu Y & Wolf A (2026). Tracking PerturBench datasets with LaminDB: Full lineage from raw data to ML-ready splits. Lamin Blog.
https://blog.lamin.ai/perturbench
```