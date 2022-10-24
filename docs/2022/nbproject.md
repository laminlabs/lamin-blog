---
title: "nbproject: Manage Jupyter notebooks"
date: 2022-08-29
number: 2
doi: 10.56528/nbp
author: Koncopd, Zethson, falexwolf
orcid:
  Koncopd: 0000-0002-4944-6586
  Zethson: 0000-0002-8937-3457
  falexwolf: 0000-0002-8760-7838
affiliation:
  Koncopd: Helmholtz Munich
  Zethson: Helmholtz Munich
  falexwolf: Lamin Labs, Munich
docs: https://lamin.ai/docs/nbproject
repo: https://github.com/laminlabs/nbproject
tweet: https://twitter.com/falexwolf/status/1567053722919882752
linkedin: https://www.linkedin.com/posts/falexwolf_new-tool-nbproject-helps-manage-jupyter-activity-6972823453892542464-Hvxz?utm_source=share&utm_medium=member_desktop
---

## Abstract

[nbproject](https://lamin.ai/docs/nbproject) is an open-source Python tool to help manage Jupyter notebooks with metadata, dependency, and integrity tracking.
A draft-to-publish workflow creates more reproducible notebooks with context.

There are a number of approaches to address reproducibility & manageability problems of computational R&D projects.
nbproject complements - and should be combined with - approaches that are based on modularizing notebooks into pipelines, containerizing compute environments, or managing notebooks on centralized platforms.

## Introduction

Over the past 11 years, Jupyter notebooks [{ct}`Pérez07`, {ct}`Kluyver16`] have become data scientists' most popular user interface {cp}`Perkel18`.[^origin]
Today, GitHub hosts about 9M publicly accessible notebooks in active repositories at exponential growth (**Figure 1**).
VS Code made notebooks an integral component of its developer experience {cp}`Dias21` and many cloud services offer a workbench built around Jupyter Lab.

[^origin]: It was 2011 when Granger wrote the code for the IPython Notebook server and user interface [Jupyter18].

```{figure-md}

<img width="600" alt="nbestimate of GitHub-hosted notebooks" src="https://lamin-site-assets.s3.amazonaws.com/hx9TkXgXGMt5hC02sTetK-1.png">

**Figure 1: Number of public GitHub-hosted Jupyter notebooks.** The graph is from [nbestimate](https://github.com/parente/nbestimate) and was generated in July 2022 {cp}`Parente22` (MIT license). The kink in December 2020 was caused by GitHub changing their query results to exclude repositories without activity for the past year.
```

Nonetheless, the average notebook-based data science workflow has a severe reproducibility problem [{ct}`Perkel18`, {ct}`Balogh22`].[^famousgrus]
In addition, large notebook-based projects are hard to manage and often develop into an organic collection of notebook files that are hard to navigate.
The situation seems particularly severe in biology, where even scientific results that are published in high impact journals often come with disorganized, hard-to-reproduce collections of notebooks.

[^famousgrus]: Famous became "I don't like notebooks" by Joel Grus [Grus18].

## Problems of notebooks

1. The overarching project is an unstructured collection of notebooks, code, and data files.
2. Notebook cells are non-consecutively executed.[^grusbalogh][^opinionsconsecutivenss]
3. Package dependencies are missing [{ct}`Balogh21a`, {ct}`Balogh22`].
4. Data dependencies are missing.
5. Pipeline dependencies (previous data transformations) are missing.
6. Notebook has low code quality {cp}`Grotov22`.[^codequality]

[^grusbalogh]: “I have seen programmers get frustrated when notebooks don’t behave as expected, usually because they inadvertently run code cells out of order." [Grus18], quoted in [Balogh22] & [Perkel18].
[^opinionsconsecutivenss]: Laura Norén: “Restart and run all or it didn’t happen” [[source](https://twitter.com/digitalFlaneuse/status/996481061092806658)]. Kyle Cranmer: "Idea: A 'clean state' badge at top of notebook that is green if notebook was in restart+rerun all state, and red otherwise" [[source](https://twitter.com/KyleCranmer/status/996488486667587584)]. Andreas Mueller: "The badge would be indeed a nicer way to express 'all cells are numbered consecutively starting at 0'" [[source](https://twitter.com/amuellerml/status/996738771642191872)]. Alex remembers bioRxiv-co-founder Richard Sever & CarbonPlan-founder Jeremy Freeman - then Director of Comp Bio at CZI - express similar opinions at the Human Cell Atlas Comp Tools meeting in Aptos in May 2018.
[^codequality]: "Jupyter notebooks also encourage poor coding practice, he [Joel Grus] says, by making it difficult to organize code logically, break it into reusable modules and develop tests to ensure the code is working properly." [Perkel18]

## Why notebooks, then?

Notebooks are highly popular across the full breadth of computational sciences & engineering.[^universe]
Notebooks are the standard for prototyping and analysis, while ML Ops tools (see [Appendix](ml-ops-tools)) are the standard for optimizing narrow classes of models.

Optimizing narrow classes of models though typically doesn't yield the biggest gains towards progress in computational biology.
Computational biology often stops optimizing ML models at stages that other fields would consider prototyping[^cheptsov] and has always been data-centric {cp}`Ng22` through its tight dependence of computational (drylab) on wetlab experiments.
Between wetlab experiments, data generation conditions often change so drastically that data scientists' greatest efforts are spent on assembling & cleaning the data.
Hence, instead of optimizing a narrow class of computational models, computational biologists need to continuously conceive new ways of taming and modeling data.

<!-- prettier-ignore -->
[^universe]: "There you were, doing your work using Jupyter Notebooks, cleaning and analyzing that massive data set to model the expansion of the Universe [...].
    Notebooks in VS Code should feel natural so that you can seamlessly move between crafting your code files and your notebook modeling the Universe in Python." [Diaz21]
[^cheptsov]: And for prototyping, even critical assessments of notebooks call them out as the "industry standard": "In fairness to Jupyter notebooks, they have become the standard way of prototyping ML models all over the industry. Because the notebooks are interactive and support visual outputs, there is no better way of exploring data and sharing the results." [Cheptsov22]

Notebooks' “computational narrative” offers a format for this type of work: A "document that allows researchers to supplement their code and data with analysis, hypotheses and conjecture", according to Brian Granger {cp}`Peres18`.
"Notebooks are a form of interactive computing, an environment in which users execute code, see what happens, modify and repeat in a kind of iterative conversation between researcher and data. [...] Notebooks allow more powerful connections between topics, theories, data and results”, according to Lorena Barba {cp}`Peres18`.

## Existing solutions to problems

Today, problems 5 & 6 are addressed to varying degrees by notebook platforms that allow using notebooks in ML pipelines and help with decomposing them into smaller code modules.
Examples for this are Elyra {cp}`Resende18` (**Figure 2**), Ploomber [{ct}`Blancas20`, {ct}`Blancas21a`, {ct}`Blancas21b`] and Orchest {cp}`Lamers21`.
The latter two and most other notebook platforms ([Appendix](notebook-platforms)) also manage (package) computational environments to execute notebooks, and with that, address problem 3.

An interesting alternative approach to making notebooks more reproducible consists in storing the history of users' actions, as offered by Verdant [{ct}`Kery19a`, {ct}`Kery19b`].

To the authors' knowledge, all other notebook platforms ([Appendix](notebook-platforms)) do not focus on reproducibility and manageability, but on the allocation of compute & storage resources.

```{figure-md}

<img width="600" alt="Elyra pipeline" src="https://lamin-site-assets.s3.amazonaws.com/e2G7k9EVul4JbfsEYAy5W-1.png">

**Figure 2: Example for an Elyra notebook pipeline.** From the [Elyra examples repository](https://github.com/elyra-ai/examples/tree/main/pipelines/introduction-to-generic-pipelines), MIT licensed {cp}`Resende18`.
```

## Solutions chosen by nbproject

nbproject complements pipeline and compute environment packaging solutions: nbproject is a lightweight Python package that works without connecting to any centralized platform. It addresses problems as follows:

1. _Project is an unstructured collection of notebooks, code, and data files._ nbproject allows configuring arbitrary project- and management-related metadata. Its id and version fields allow anchoring notebooks in a graph of R&D operations of an entire team.
2. _Notebook cells aren't consecutively executed._ nbproject provides a publishing workflow that checks for consecutiveness & the presence of a title and versions the notebook.
3. _Package dependencies are missing._ nbproject offers a visual way to track packages, which complements packaging solutions.
4. _Data dependencies are missing._ nbproject integrates well with [LaminDB](https://lamin.ai/docs/db).
5. _Pipeline dependencies are missing._ nbproject allows sketching pipelines manually. When integrated with LaminDB, it provides full provenance automatically.
6. _Notebook has low code quality._ The publishing workflow encourages small modular notebooks with most code residing in versioned packages.

## Design choices

nbproject's two most important features are tracking & displaying metadata and offering a publishing workflow.

### Tracking & displaying metadata

The header (**Figure 3**) is inspired by popular notebook tools, like [Notion](https://notion.com), ELNs in biology, and Jupyter notebook platforms.
Any user opening their own or someone else's notebook is provided with relevant context for interpreting the notebook content:
a universal ID, a version, time stamps, important dependencies, and arbitrary additional metadata.
While most notebook platforms also provide IDs and other metadata for notebooks ([Appendix](notebook-metadata)), to our knowledge, only nbproject offers an API to access such metadata.

The metadata header display depends on the computing environment in which the notebook is run: If the environment differs from the stored package dependencies, mismatching versions can readily be seen as both stored and live dependencies are displayed.
This typically occurs when multiple users collaborate on notebooks and the receiver of a notebook tries to re-run the notebook of a sender (**Figure 3**).

<style>
table td, table td * {
    vertical-align: top;
}
</style>

| Sender                                                                                          | Receiver                                                                                        |
| ----------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| <img height="200" src="https://lamin-site-assets.s3.amazonaws.com/B6S2Mws8gkpzvSryGzsxk-1.png"> | <img height="220" src="https://lamin-site-assets.s3.amazonaws.com/18gKT0WJbnlnHCwqTnevR-1.png"> |

<center><b>Figure 3: Metadata header for sender & receiver, respectively.</b></center><br>

### The publishing workflow

nbproject suggests publishing notebooks before sharing them with a receiver (**Figure 4**).
After an editing phase in "draft" mode, publishing the notebook writes dependencies to the metadata store, checks for the integrity of the notebook (consecutiveness & title), and sets a version number.

Hence, if a user receives a published notebook, they know that the latest dependencies are stored within it, are provided with a version number, and see whether the notebook was consecutively executed.

```{figure-md}

<img width="600" alt="Publishing workflow." src="https://lamin-site-assets.s3.amazonaws.com/NHq29ckKVrrTYsNdG0KjT-1.gif">

**Figure 4: Publishing workflow.** Made with Kat by Sunny Sun.
```

### Semantic vs. full dependency tracking

The visual display of mismatching package dependencies between compute environments should be seen in the broader context of reproducibility vs. determinism.
Reproducibility is “the ability of an independent research team to produce the same results using the same method based on the documentation made by the original team” (adapted from {cp}`Gunderson18`).
Computational determinism, in addition, requires the bit-exact same output for the same input.
Whereas targeted experimentation or the certification of models for sensitive application areas should run in deterministic environments {cp}`Heumos22`, reproducibility is sufficient for many applications.

Highly deterministic environments can be created with Docker & conda and managed on most data platforms.
However, they don't ensure scientific correctness of results.
In fact, deterministic environments can lead to results that are _only_ reproducible on highly specific environments, say, if they depend on certain data type precisions or greedy algorithms.
If a team always uses the exact same environments they will never learn that such a result is indeed only bit-wise correct, but not scientifically correct.
The scientific correctness of a robust statistical result, by contrast, should reproduce in many different compute environments as long as basic conditions are met.[^correctness]

[^correctness]: Related: See [Peter Wang talk about](https://youtu.be/X0-SXS6zdEQ?t=864) correctness in computing systems.

Hence, policies in R&D teams may vary from using the same Docker container for all computations to making Docker containers for each analysis to not using Docker at all and running analysis on a variety of environments, cross-checking them among team members for robustness.

### Testing notebooks in CI

Just like software, notebooks should be tested in continuous integration (CI).
As nbproject needs to communicate with a Python kernel, a server, and the frontend of Jupyter editors, we couldn't use `nbmake` and related existing testing infrastructure:
[nbproject-test](https://pypi.org/project/nbproject-test).
Instead of relying on the availability of a server in CI environments, `nbproject-test` executes notebooks with `nbclient`, infers notebook paths and passes these as environment variables to `nbproject`.

## Acknowledgements

We are grateful to Sunny Sun & Alex Trapp for providing early feedback and to Sunny for making the GIF of Figure 4.

We are grateful to the Jupyter project developers, in particular, Jeremy Tuloup for ipylab.

## Author contributions

Sergei & Alex developed the software.
Alex conceived the project.
Lukas provided extensive beta testing and his perspective on determinism vs. reproducibility, which he added to this report.
Alex wrote the report with help from Sergei & Lukas.

## Citation

Cite the software and this report as:

```
Rybakov, S., Heumos, L., & Wolf, A. (2022). nbproject: Manage Jupyter notebooks. Lamin Reports. https://doi.org/10.56528/nbp
```

## Appendix

(ml-ops-tools)=

### General ML Ops tools

This is a non-comprehensive list of ML Ops tools centered around helping to organize the model development & deployment cycle.

Most of these track data storage, a model registry, and offer ways of creating pipelines.

- [MetaFlow](https://metaflow.org/): A framework for real-life data science.
- [dvc](https://dvc.org/): Open-source Version Control System for Machine Learning Projects with strong git inspiration.
- [Neptune AI](https://neptune.ai/): Experiment tracking and model registry for production teams.
- [Kedro](https://kedro.readthedocs.io/): Kedro is an open-source Python framework for creating reproducible, maintainable and modular data science code.
- [MLFlow](https://mlflow.org/): An open source platform for the machine learning lifecycle.
- [Zen ML](https://zenml.io/): Build portable, production-ready MLOps pipelines.
- [dstack](https://dstack.ai/): Your new home for building AI apps.

(notebook-platforms)=

### Dedicated notebook platforms

Solutions that offer building pipelines or experiment tracking based on notebooks, as discussed in the main text:

- [Ploomber](https://ploomber.io/): Data & ML Ops platform. For notebooks, it uses ipytext to turn notebooks into diffable code files, and allows creating pipelines.
- [Orchest](https://www.orchest.io/): Data & ML Ops platform. Offers pipelines for notebooks and scripts.
- [Verdant](https://github.com/mkery/Verdant): Track user edit histories of notebooks.
- [Elyra](https://github.com/elyra-ai/elyra): Pipelines for notebooks and scripts.

Solutions offering compute allocation, storage connection, and environment management:

- [Binder](https://mybinder.org/)
- [Jupyter Hub](https://jupyter.org/hub)
- [Saturn Cloud](https://saturncloud.io/)
- [Google Colab](https://colab.research.google.com/)
- [AWS Sagemaker](https://docs.aws.amazon.com/sagemaker/latest/dg/notebooks.html)
- [Azure Notebooks](https://visualstudio.microsoft.com/vs/features/notebooks-at-microsoft/)
- [Gradient](https://gradient.run/notebooks)
- [Deepnote](https://deepnote.com/)
- [Jovian](https://jovian.ai/docs/)

Notebook tracking in data platforms, with provenance features typically through pipelines are provided by leading data platforms: Databricks (MLFlow), Snowflake, Domino Data Labs, Palantir, Cloudera.

Projects related to managing notebooks, some of them mentioned in a popular blog post from Netflix {cp}`Ufford18`:

- [Bookstore](https://github.com/nteract/bookstore): Notebook storage and publishing workflows for the masses. No longer maintained.
- [Commuter](https://github.com/nteract/commuter): Notebook sharing hub based on an nteract server.
- [nbss](https://github.com/notebook-sharing-space/nbss): Notebook sharing hub.
- [nbdev](https://github.com/fastai/nbdev): Turn notebook projects into Python development projects.
- [Papermill](https://github.com/nteract/papermill): Parametrize & execute Jupyter notebooks at scale.
- [ML Exchange](https://ml-exchange.org/notebooks): Open source data platform with notebook support.
- [ExecutableBooks](https://github.com/executablebooks): Publish notebooks with [metadata](https://jupyterbook.org/content/metadata.html).

(notebook-metadata)=

### Metadata tracking

There are two existing open-source projects concerned with general metadata management for notebooks: nbmetalog {cp}`Moreno21` and [nbmeta](https://nbmeta.readthedocs.io/en/latest/). While the latter seems no longer maintained, the former provides a convenient way to access session & execution metadata about the notebook.

There were suggestions for assigning IDs to notebooks in Project Jupyter itself (see [here](https://github.com/jupyter/nbformat/issues/148)).
IDs for notebook cells are meanwhile a [standard](https://nbformat.readthedocs.io/en/latest/format_description.html#cell-ids).

Google Colab provides an ID, time stamps, provenance & authorship metadata like this:

```
"metadata": {
  "colab": {
    "name": "post_run_cell",
    "provenance": [
      {
        "file_id": "1Rgt3Q7hVgp4Dj8Q7ARp7G8lRC-0k8TgF",
        "timestamp": 1560453945720
      },
      {
        "file_id": "https://gist.github.com/blois/057009f08ff1b4d6b7142a511a04dad1#file-post_run_cell-ipynb",
        "timestamp": 1560453945720
      }
    ],
    "provenance": [],
    "collapsed_sections": [],
    "authorship_tag": "ABX9TyPeUMNWCzl3N44NkFSS3tg0",
    "include_colab_link": true
  }
  ...
}
```

Deepnote provides metadata like this:

```
"metadata": {
  "orig_nbformat": 2,
  "deepnote": {
   "is_reactive": false
  },
  "deepnote_notebook_id": "b9694295-92fc-4a3f-98b3-f31609abf37a",
  "deepnote_execution_queue": []
 }
```

## References

<ol>

<li id="Balogh22">

Balogh (2022). Data Science Notebook Life-Hacks I Learned From Ploomber. [Machine Learning Mastery Blog](https://machinelearningmastery.com/data-science-notebook-life-hacks-i-learned-from-ploomber/).

</li><li id="Blancas20">

Blancas (2020). Introducing Ploomber. [Ploomber Blog](https://ploomber.io/blog/ploomber/).

</li><li id="Blancas21a">

Blancas (2021a). On writing clean Jupyter notebooks. [Ploomber Blog](https://ploomber.io/blog/clean-nbs/).

</li><li id="Blancas21b">

Blancas (2021b). We need a Ruby on Rails for Machine Learning. [Ploomber Blog](https://ploomber.io/blog/rails4ml/).

</li><li id="Cheptsov22">

Cheptsov (2022). Notebooks and MLOps. Choose one. [MLOps Fluff](https://mlopsfluff.dstack.ai/p/notebooks-and-mlops-choose-one).

</li><li id="Dias21">

Dias (2021). The Coming of Age of Notebooks. [VS Code Blog](https://code.visualstudio.com/blogs/2021/08/05/notebooks).

</li><li id="Gunderson18">

Odd Erik Gundersen and Sigbjørn Kjensmo (2018). State of the Art: Reproducibility in Artificial Intelligence. [Proceedings of the AAAI Conference on Artificial Intelligence, 32(1)](https://doi.org/10.1609/aaai.v32i1.11503).

</li><li id="Heumos22">

Heumos, Ehmele, Kuhn, Menden, Miller, Lemke, Gabernet & Nahnsen: mlf-core: a framework for deterministic machine learning. [arXiv:2104.07651](https://arxiv.org/abs/2104.07651)

</li><li id="Lamers21">

Lamers (2021). Hello, World! [Orchest Blog](https://www.orchest.io/blog/hello-world).

</li><li id="Resende18">

Resende, Chin, Titzler & Elyra Development Team (2018). Elyra extends JupyterLab with an AI centric approach. [GitHub](https://github.com/elyra-ai/elyra).

</li><li id="Grotov22">

Grotov, Titov, Sotnikov, Golubev & Bryksin (2022). A Large-Scale Comparison of Python Code in Jupyter Notebooks and Scripts. [arXiv:2203.16718](https://arxiv.org/abs/2203.16718).

</li><li id="Grus18">

Grus (2018). I don't like notebooks. [YouTube](https://www.youtube.com/watch?v=7jiPeIFXb6U).

</li><li id="Jupyter18">

Jupyter (2018). Jupyter receives the ACM Software System Award. [Project Jupyter Blog](https://blog.jupyter.org/jupyter-receives-the-acm-software-system-award-d433b0dfe3a2).

</li><li id="Kery19a">

Kery (2019). Verdant: A version control tool for JupyterLab that automatically records the history of your experimentation while you work. [GitHub](https://github.com/mkery/Verdant).

</li><li id="Kery19b">

Kery, John, O'Flaherty, Horvath & Myers (2019). Towards effective foraging by data scientists to find past analysis choices. [CHI '19 #92](https://doi.org/10.1145/3290605.3300322).

</li><li id="Kluyver16">

Kluyver, Ragan-Kelley, Pérez, Granger, Bussonnier, Frederic, Kelley, Hamrick, Grout, Corlay, Ivanov, Avila, Abdalla, Willing & Jupyter Development Team (2016). Jupyter Notebooks – a publishing format for reproducible computational workflows. [Positioning and Power in Academic Publishing: Players, Agents and Agendas 87–90](http://doi.org/10.3233/978-1-61499-649-1-87).

</li><li id="Perkel18">

Perkel (2018). Why Jupyter is data scientists’ computational notebook of choice. [Nature 563, 145](https://doi.org/10.1038/d41586-018-07196-1).

</li><li id="Pérez07">

Pérez & Granger (2007). IPython: A system for interactive scientific computing. [Computing in science & engineering 9, 21](https://doi.org/10.1109/MCSE.2007.53).

</li><li id="Moreno21">

Moreno (2021). nbmetalog helps you log Jupyter notebook metadata. [GitHub](https://github.com/mmore500/nbmetalog).

</li><li id="Ng22">

Ng & Strickland (2022). Andrew NG: Unbiggen AI. [IEEE Spectrum](https://spectrum.ieee.org/andrew-ng-data-centric-ai).

</li><li id="Parente22">

Parente (2022). Estimate of Public Jupyter Notebooks on GitHub. [GitHub](https://github.com/parente/nbestimate).

</li><li id="Ufford">

Ufford, Pacer, Seal & Kelley (2018). Beyond Interactive: Notebook Innovation at Netflix. [Netflix Tech Blog](https://netflixtechblog.com/notebook-innovation-591ee3221233).

</ol>
