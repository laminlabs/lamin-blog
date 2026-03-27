---
title: "An introduction to LaminR"
date: 2026-03-26
author: tjburns08
affiliation:
  tjburns08: Burns Life Sciences Consulting, Berlin
---

Any data scientist will tell you that one of the keys to a good data science project is good data management practices. If your data are disorganized or you don't know who did what or you can't reproduced results, it'll "bite you" and your team. Thus, thought should go into how the data are going to be handled, stored, modified, and tracked over a project. Here, we'll be using an example from single-cell analysis to illustrate how the open-source LaminR package helps with traceability and reproducibility of data analyses in R.

Anyone who has worked with large and complex datasets knows that the devil is in the details. You might have multiple data scientists and agents manipulating the data in multiple ways. Did we do a log1p transform or an asinh transform? Did we center and scale the data? I see some clusters. How did we cluster it? Did we use the default parameters or change something? And so forth. On top, there is the whole topic of revisiting datasets and projects that are several years old, where the people who were working on it have moved on, but which are now treasure troves that provide context and training data for agents.

It does not matter how good an AI foundation model (or whatever you are using) is, if your datasets and the infrastructure that hosts them are problematic. It's the classic term "garbage in, garbage out." So how do we handle all of this, aside from hiring a team of data engineers? This is where LaminR helps. It is an open-source package that specializes in dealing with data infrastructure needs that naturally arise in the current paradigm of using many big datasets with many agents and large teams to train better models. In particular, LaminR manages metadata to allow querying and finding data and it tracks every last line of code that did any sort of modification to any part of a data object by whom and at what time. So if a data scientist has to revisit an old dataset or one they did not work on, they'll have the information that they need.

## PBMC 3k

To illustrate this, we use the well-known PBMC 3k dataset. This dataset has been featured in Seurat's [guided clustering tutorial](https://satijalab.org/seurat/articles/pbmc3k_tutorial.html) for a decade, and is still the common entrypoint in single-cell RNA sequencing analysis.

If you have access to a hosted LaminDB instance on [lamin.ai](https://lamin.ai) you can login and connect to it:

:::::{tab-set}
::::{tab-item} CLI

```bash
lamin login username
lamin connect instance_owner/your_instance
```

::::
::::{tab-item} R

```r
lc <- laminr::import_module("lamin_cli")
lc$login(user = "username")
lc$connect("instance_owner/your_instance")
```

::::
:::::

If you want to initialize your own database instead, use:

::::::{tab-set}
:::::{tab-item} CLI

```bash
lamin init --storage ./mydata --modules bionty
```

:::::
:::::{tab-item} R

```r
lc <- laminr::import_module("lamin_cli")
lc$init(storage = "./mydata", modules = "bionty")
```

:::::
::::::

In your script or Rmd notebook, you will do the following to set things up:

```r
library(laminr)
ln <- laminr::import_module("lamindb")
```

LaminR is based on the Python package LaminDB and `reticulate`.

Importantly, you typically want LaminR to track what you do, so all datasets will be linked to the generating code:

```r
# Start a tracked run of your script or notebook
ln$track()
```

From here, you load the PBMC 3k dataset, and take it through whatever analysis you're going to do. Let's assume you did a standard pre-processing -> PCA -> clustering -> nonlinear dimensionality reduction set up. What you do next is save your Seurat object as a rds file:

```r
library(Seurat)
library(SeuratData)

cells <- SeuratData::LoadData("pbmc3k")
cells <- NormalizeData(cells, normalization.method = "LogNormalize", scale.factor = 10000)
cells <- FindVariableFeatures(cells, selection.method = "vst", nfeatures = 2000)
all.genes <- rownames(cells)
cells <- ScaleData(cells, features = all.genes)
cells <- RunPCA(cells, features = VariableFeatures(object = cells))
cells <- FindNeighbors(cells, dims = 1:10)
cells <- FindClusters(cells, resolution = 0.5)
cells <- RunUMAP(cells, dims = 1:10)
```

We can now e.g. look at a UMAP colored by specific genes:

```r
FeaturePlot(cells, features = c("MS4A1", "GNLY", "CD3E", "CD14", "FCER1A", "FCGR3A", "LYZ", "PPBP", "CD8A"))
```

<div style="text-align: center">
<img width="800" src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/DDi04PvoNdjc9Xba0000.png">
</div>

[Source](https://lamin.ai/laminlabs/training/transform/KFtlfbCiP9Bm000A).

Let's now save this Seurat object as an artifact in LaminR:

```r
saveRDS(cells, "pbmc3k_processed.rds")
ln$Artifact("pbmc3k_processed.rds", key = "pbmc3k/pbmc3k_processed.rds")$save()
```

And from here, we are going to end the session, by running:

```r
ln$finish()
```

If you use notebook mode in RStudio, this will already upload a run report. But if you didn't, you can knit your notebook and run one of the following to save the knitted html. You can think about it as equivalent to `git push`:

:::::{tab-set}
::::{tab-item} CLI

```bash
lamin save pbmc3k.Rmd
```

::::
::::{tab-item} R

```r
lc$save("pbmc3k.Rmd")
```

::::
:::::

The above saves the file `pbmc3k.Rmd` as a "transform", which is short hand for data transformation, so that it's linked against the output file `pbmc3k/pbmc3k_processed.rds`. This is also visible on the LaminHub GUI:

<div style="text-align: center">
<img width="800" src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/VMTTBgRdPy81Fb590000.png">
</div>

[Source](https://lamin.ai/laminlabs/training/artifact/VugfUMiwR8OtlnIU000L).

Clicking on the `pbmc3k.Rmd` notebook gives us the run report, which you can see below.

<div style="text-align: center">
<img width="800" src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/XTqrtXrdxkBjCIlw0000.png">
</div>

[Source](https://lamin.ai/laminlabs/training/transform/KFtlfbCiP9Bm000A).

You can also get the environment, which is the packages and versions thereof that were loaded at the time of running the script:

<div style="text-align: center">
<img width="800" src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/eGL2ZsiTk3E0pPEk0000.png">
</div>

[Source](https://lamin.ai/laminlabs/training/transform/KFtlfbCiP9Bm000A).

Every unit of work that you do can now be easily shared and communicated, both with colleagues and your future self. For a given piece of data, every manipulation and the code surrounding a given manipulation is now recorded and stored making it easier to understand and reproduce. And this is particularly useful in large projects where many stakeholders contribute data and analyses.

## Materials

- The LaminR source code: https://github.com/laminlabs/laminr
- The LaminDB source code: https://github.com/laminlabs/lamindb

## Acknowledgements

Thanks to Luke Zappia and Robrecht Cannoodt for creating LaminR and to Alex Wolf for editing this post.

## Disclosure

Lamin engaged Tyler to illustrate a use case for LaminR. This blog post is the result of that engagement.
