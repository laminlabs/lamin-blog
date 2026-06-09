---
title: "readfcs: Read FCS files"
date: 2022-08-27
doi: 10.56528/rfcs
author: sunnyosun, falexwolf
orcid:
  sunnyosun: 0000-0002-2365-0888
  falexwolf: 0000-0002-8760-7838
affiliation:
  sunnyosun: Lamin Labs, Munich
  falexwolf: Lamin Labs, Munich
docs: https://readfcs.lamin.ai
repo: https://github.com/laminlabs/readfcs
---

[readfcs](https://lamin.ai/docs/readfcs) is a lightweight open-source Python package that loads data and metadata from Flow Cytometry Standard (FCS) files into `DataFrame` and `AnnData` objects, allowing users to flexibly use downstream analytical tools.

## Filling a gap

`readfcs` fills a gap among existing FCS readers in the Python ecosystem: These are either part of comprehensive analytical packages (e.g., FlowIO,[^white21] Cytopy[^burton21]) that operate on data structures tailored to specific downstream analyses or they do not offer support for `AnnData` objects.[^yurtsev22]

For the main data and metadata functionality, readfcs builds on `fcsparser`.[^yurtsev22]
In addition to `FCSParser`, readfcs offers compensation, indexing channels by markers, and structuring metadata in `AnnData`.

`readfcs` is used by `pytometry`.[^buttner22]

## Acknowledgments

We are grateful to Maren Büttner for valuable discussions.

## Author contributions

Sunny & Alex conceived the project.
Sunny developed the software.

## Citation

If you use the results of this work in an academic context, we'd be happy if you cite `readfcs` and this report as:

```
Sun S & Wolf A (2022). readfcs: Read FCS files. Lamin Blog. https://doi.org/10.56528/rfcs
```

## References

[^yurtsev22]: Yurtsev E (2022). FCSParser - a Python package for reading FCS files. [GitHub](https://github.com/eyurtsev/fcsparser).

[^white21]: White S, Quinn J, Enzor J, Staats J, Mosier SM, Almarode J, Denny TN, Weinhold KJ, Ferrari G & Chan C (2021). FlowKit: A Python toolkit for integrated manual and automated cytometry analysis workflows. [Frontiers in Immunology, 12](https://doi.org/10.3389/fimmu.2021.768541). [GitHub](https://github.com/whitews/flowio).

[^burton21]: Burton R (2021). CytoPy - a cytometry analysis framework for Python. [GitHub](https://github.com/burtonrj/CytoPy).

[^buttner22]: Buttner M, Hempel F, Ryborz T, Theis FJ & Schultze JL (2022). Pytometry: Flow & mass cytometry analytics. [bioRxiv](https://doi.org/10.1101/2022.10.10.511546). [GitHub](https://github.com/buettnerlab/pytometry).
