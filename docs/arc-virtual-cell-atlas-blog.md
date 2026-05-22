---
title: "Querying the 154k artifacts and 600M cells of the Arc Virtual Cell Atlas with a simple API & UI"
date: 2026-05-20
author: sunnyosun, Koncopd, fredericenard, chaichontat, falexwolf
affiliation:
  sunnyosun: Lamin Labs, Munich
  fredericenard: Lamin Labs, Munich
  chaichontat: Lamin Labs, Munich
  Koncopd: Lamin Labs, Munich
  falexwolf: Lamin Labs, Munich
db: https://lamin.ai/laminlabs/arc-virtual-cell-atlas
---

The [Arc Virtual Cell Atlas](https://arcinstitute.org/tools/virtualcellatlas) represents a monumental leap in single-cell genomics, offering a massive collection of scRNA-seq datasets encompassing 1.4 billion cells across 300,000 artifacts[^youngblut25][^zhang25]. To make this treasure trove of data seamlessly accessible to the community, we have mirrored the entire atlas on [LaminHub](https://lamin.ai/laminlabs/arc-virtual-cell-atlas).

```{note}

This is a post in a series of posts on biological data atlases.

```

You can jump right in with our [Lamin docs tutorial](https://docs.lamin.ai/arc-virtual-cell-atlas).

## The Accessibility Challenge

While the original Arc Virtual Cell Atlas is an incredible resource, navigating it can be a daunting task. The primary pain point for many researchers is the lack of a dedicated user interface or a simple query mechanism.

Without a UI, performing basic exploratory tasks—such as filtering datasets by specific organisms, tissues, or cell lines—becomes a challenge. Researchers are often forced to download massive amounts of data just to figure out if it contains the specific subsets they need. This creates significant friction and slows down the pace of discovery.

## Subsecond Queries at Gigascale

By mirroring the atlas on LaminDB, we've solved the accessibility challenge. LaminDB is built to effortlessly handle gigascale data, and it has no problem managing the scale of 300,000 artifacts holding 1.4 billion cells as observations.

What does this mean for you? Lightning-fast, **subsecond queries**. You can instantly query for specific datasets based on rich metadata without downloading a single byte of the actual data matrices.

Furthermore, LaminHub provides a powerful and intuitive UI that allows users to seamlessly browse, filter, and explore artifacts visually. You can now easily find exactly what you're looking for with just a few clicks.

<div style="text-align: center">
<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/hjNR9gl58w1n8Jb30000.png" width="700" style="padding: 0;">
</div>

## A Unified Ecosystem for Atlases

This release is part of Lamin's broader ecosystem of accessible biological data. Lamin hosts several such foundational atlases, including CELLxGENE and Hubmap.

The immense value here lies in standardization: you can access multiple disparate atlases through the exact same Python API (`lamindb`) and rely on similar data conventions across the board.

By utilizing a unified ecosystem, researchers can significantly reduce the time spent on data wrangling and accelerate cross-atlas analysis, enabling more robust and comprehensive biological insights.

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

We encourage you to explore the atlas on [LaminHub](https://lamin.ai/laminlabs/arc-virtual-cell-atlas), try out the API in your notebooks, and read the full [documentation](https://docs.lamin.ai/arc-virtual-cell-atlas) to see how it can accelerate your research.

## References

[^youngblut25]: Youngblut ND et al. (2025). scBaseCount: an AI agent-curated, uniformly processed, and continually expanding single cell data repository. [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.02.27.640494).

[^zhang25]: Zhang JQ et al. (2025). Tahoe-100M: A Giga-Scale Single-Cell Perturbation Atlas for Context-Dependent Gene Function and Cellular Modeling. [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.02.20.639398).
