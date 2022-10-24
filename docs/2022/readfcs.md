---
title: "readfcs: Read FCS files"
date: 2022-08-27
number: 1
doi: 10.56528/rfcs
author: sunnyosun, falexwolf
orcid:
  sunnyosun: 0000-0002-2365-0888
  falexwolf: 0000-0002-8760-7838
affiliation:
  sunnyosun: Lamin Labs, Munich
  falexwolf: Lamin Labs, Munich
docs: https://lamin.ai/docs/readfcs
repo: https://github.com/laminlabs/readfcs
tweet:
linkedin:
---

[readfcs](https://lamin.ai/docs/readfcs) is a lightweight open-source Python package that loads data and metadata from Flow Cytometry Standard (FCS) files into `DataFrame` and `AnnData` objects, allowing users to flexibly use downstream analytical tools.

With this, it fills a gap among existing FCS readers in the Python ecosystem: These are either part of comprehensive analytical packages (e.g., FlowIO by {ct}`White21`, cytopy by {ct}`Burton21`) that operate on data structures tailored to specific downstream analyses or they do not offer support for `AnnData` objects {cp}`Yurtsev22`.

For the main data and metadata functionality, readfcs builds on fcsparser {cp}`Yurtsev22`.
In addition to `FCSParser`, readfcs offers compensation, indexing channels by markers, and structuring metadata in `AnnData`.

readfcs is used by pytometry {cp}`Buttner22`.

## Acknowledgments

We are grateful to Maren Büttner for valuable discussions.

## Author contributions

Sunny & Alex conceived the project.
Sunny developed the software.

## Citation

Cite the software and this report as:

```
Sun, S. & Wolf, A. (2022). readfcs: Read FCS files. Lamin Reports. https://doi.org/10.56528/rfcs
```

## References

<ol>

<li id="Yurtsev22">

Yurtsev E (2022). FCSParser - a python package for reading fcs files. [GitHub](https://github.com/eyurtsev/fcsparser).

</li><li id="White21">

White S, Quinn J, Enzor J, Staats J, Mosier S M, Almarode J, Denny T N, Weinhold K J, Ferrari G & Chan C (2021). FlowKit: A Python toolkit for integrated manual and automated cytometry analysis workflows. [Frontiers in Immunology, 12](https://doi.org/10.3389/fimmu.2021.768541). [GitHub](https://github.com/whitews/flowio).

</li><li id="Burton21">

Burton R (2021). CytoPy - a cytometry analysis framework for Python. [GitHub](https://github.com/burtonrj/CytoPy).

</li><li id="Buttner22">

Büttner M, Hempel F, Ryborz T, Theis FJ & Schultze JL (2022). Pytometry: Flow & mass cytometry analytics. [bioRxiv](https://doi.org/10.1101/2022.10.10.511546). [GitHub](https://github.com/buettnerlab/pytometry).

</li>

</ol>
