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

[readfcs](https://lamin.ai/docs/readfcs) loads data and metadata from Flow Cytometry Standard (FCS) files efficiently into `DataFrame` and `AnnData` objects.
This extends existing tools, which offer parsers specific to their own downstream applications without general data structures.

Also, readfcs allows to flexibly access slots of data and metadata, and offers a robust implementation tested in continuous integration.

We build on FlowIO {cp}`White21` for the FCS reader and the `FCSFile` class of cytopy {cp}`Burton21` for preprocessing of parsed metadata.
Conversion to AnnData allows convenient access to otherwise unstructured metadata and structured data.

`readfcs` is used in pytometry {cp}`Buettner22`.

## References

<div id="White21">

White, S., Quinn, J., Enzor, J., Staats, J., Mosier, S. M., Almarode, J., Denny, T. N., Weinhold, K. J., Ferrari, G., & Chan, C. (2021). FlowKit: A Python toolkit for integrated manual and automated cytometry analysis workflows. [Frontiers in Immunology, 12](https://doi.org/10.3389/fimmu.2021.768541). [GitHub](https://github.com/whitews/flowio).

<div id="Burton21">

Burton, R. (2021). CytoPy - a cytometry analysis framework for Python. [GitHub](https://github.com/burtonrj/CytoPy).

 <div id="Buettner22">

Büttner, M., Hempel, F., Ryborz, T (2022). Pytometry: Flow & mass cytometry analytics. [GitHub](https://github.com/buettnerlab/pytometry).
