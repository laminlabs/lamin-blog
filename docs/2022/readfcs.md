---
title: "readfcs: Read FCS files"
date: 2022-08-07
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

```{warning}

Early access! Published version may slightly change.
```

[readfcs](https://lamin.ai/docs/readfcs) loads data and metadata from Flow Cytometry Standard (FCS) files efficiently into generic `DataFrame` and `AnnData` objects, allowing users to flexibly use various downstream analytical tools. In comparison, existing readers are often part of comprehensive analytical packages (e.g. FlowIO {ct}`White21`, cytopy {ct}`Burton21`), which provide data structures developed for specific downstream applications.

readfcs allows to flexibly access data and metadata slots and offers a robust, tested implementation.
It uses `FCSParser` {ct}`Yurtsev22` to read and parse metadata from fcs files. In addition to `FCSParser`, it offers compensation, indexing channels by markers, and conversion to `AnnData` for convenient access to otherwise unstructured metadata.

readfcs is used by pytometry {ct}`Buttner22`.

## Citation

Cite this report as:

```
Sun, S., & Wolf, A. (2022). readfcs: Read FCS files. Lamin Reports, 1. https://doi.org/10.56528/rfcs
```

## Acknowledgement

We thank Maren Büttner for conceptual discussion of this project.

## References

<div id="Yurtsev22">

Yurtsev, E. (2022). FCSParser - a python package for reading fcs files. [GitHub](https://github.com/eyurtsev/fcsparser).

<div id="White21">

White, S., Quinn, J., Enzor, J., Staats, J., Mosier, S. M., Almarode, J., Denny, T. N., Weinhold, K. J., Ferrari, G., & Chan, C. (2021). FlowKit: A Python toolkit for integrated manual and automated cytometry analysis workflows. [Frontiers in Immunology, 12](https://doi.org/10.3389/fimmu.2021.768541). [GitHub](https://github.com/whitews/flowio).

<div id="Burton21">

Burton, R. (2021). CytoPy - a cytometry analysis framework for Python. [GitHub](https://github.com/burtonrj/CytoPy).

 <div id="Buttner22">

Büttner, M., Hempel, F., Ryborz, T (2022). Pytometry: Flow & mass cytometry analytics. [GitHub](https://github.com/buettnerlab/pytometry).
