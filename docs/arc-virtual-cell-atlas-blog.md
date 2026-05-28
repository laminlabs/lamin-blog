---
title: "Querying the 300k artifacts and 1.4B cells of the Arc Virtual Cell Atlas with a simple API & UI"
date: 2026-05-20
author: sunnyosun, Koncopd, fredericenard, chaichontat, falexwolf
affiliation:
  sunnyosun: Lamin Labs, Munich
  fredericenard: Lamin Labs, NYC
  chaichontat: Lamin Labs, NYC
  Koncopd: Lamin Labs, Munich
  falexwolf: Lamin Labs, Munich
db: https://lamin.ai/laminlabs/arc-virtual-cell-atlas
---

The [Arc Virtual Cell Atlas](https://arcinstitute.org/tools/virtualcellatlas) is one of the largest single-cell resources to date: 1.4 billion cells across 300,000 scRNA-seq artifacts[^youngblut25][^zhang25]. To make this data easier to query and explore, we mirrored the atlas on [LaminHub](https://lamin.ai/laminlabs/arc-virtual-cell-atlas).

```{note}

This is a post in a series of posts on biological data atlases.

```

You can jump right in with the [Lamin docs tutorial](https://docs.lamin.ai/arc-virtual-cell-atlas).

## The Accessibility Challenge

The original Arc Virtual Cell Atlas is a highly valuable resource, but routine exploration can be difficult without a dedicated user interface and a simple query workflow.

Without a UI, even basic tasks such as filtering datasets by organism, tissue, or cell line require extra effort. Researchers often download large files before they can confirm whether the required subsets are present. That slows down project setup and cross-study comparisons.

## Subsecond Queries at Gigascale

By mirroring the atlas on LaminDB, you can query metadata first and only load the artifacts you actually need. Here, an artifact means a versioned data file with rich metadata (for example, an `.h5ad` dataset with associated organism and tissue annotations).

LaminDB supports the full scale of this atlas, enabling fast, metadata-driven filtering across 300,000 artifacts and 1.4 billion cells.

Furthermore, LaminHub provides a powerful and intuitive UI that allows users to seamlessly browse, filter, and explore artifacts visually. You can now easily find exactly what you're looking for with just a few clicks.

<div style="text-align: center">
<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/zLm6239ndakZStoi0000.png" width="700" style="padding: 0;">
</div>

## A Unified Ecosystem for Atlases

This release is part of Lamin's broader ecosystem of accessible biological data. Lamin hosts several foundational atlases, including CELLxGENE and HuBMAP.

The immense value here lies in standardization: you can access multiple disparate atlases through the same Python API (`lamindb`) and rely on similar data conventions across the board.

This reduces data wrangling overhead and makes cross-atlas analysis easier to start and easier to reproduce.

## Getting Started

Connecting to the atlas and querying for datasets is incredibly straightforward with `lamindb`. Here is a quick example of how you can query for human brain datasets:

```python
import lamindb as ln

# Connect to the instance
db = ln.DB("laminlabs/arc-virtual-cell-atlas")

# Example query for human brain datasets
organisms = db.bionty.Organism.lookup()
tissues = db.bionty.Tissue.lookup()

h5ads_brain = db.Artifact.filter(
    organisms=organisms.human,
    tissues=tissues.brain
).distinct()

print(h5ads_brain.to_dataframe())
```

Once you've identified the artifacts you need, you can seamlessly stream or cache these files directly into memory as `AnnData` objects for immediate analysis.

## Conclusion

The `laminlabs/arc-virtual-cell-atlas` mirror brings an intuitive UI, gigascale performance, and a unified API to one of the largest single-cell atlases available today.

- browse the atlas on [LaminHub](https://lamin.ai/laminlabs/arc-virtual-cell-atlas)
- run the API example in your notebook
- read the full [documentation](https://docs.lamin.ai/arc-virtual-cell-atlas)

## References

[^youngblut25]: Youngblut ND et al. (2025). scBaseCount: an AI agent-curated, uniformly processed, and continually expanding single cell data repository. [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.02.27.640494).

[^zhang25]: Zhang JQ et al. (2025). Tahoe-100M: A Giga-Scale Single-Cell Perturbation Atlas for Context-Dependent Gene Function and Cellular Modeling. [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.02.20.639398).
