---
title: "An introduction to LaminR, using the PBMC 3k dataset"
date: 2026-03-26
author: tjburns08
affiliation:
  tjburns08: Burns Life Sciences Consulting, Berlin
---

Any data scientist will tell you that one of the keys to a good data science project is good data management practices. If your data are disorganized or you don't know who did what or you can't reproduced results, it'll "bite you" and your team. Thus, thought should go into how the data are going to be handled, stored, modified, and tracked over a project. Here, we'll be using an example from single-cell analysis to illustrate how the open-source LaminR package helps with traceability and reproducibility of data analyses in R.

Anyone who has worked with large and complex datasets knows that the devil is in the details. You might have multiple data scientists and agents manipulating the data in multiple ways. Did we do a log1p transform or an asinh transform? Did we center and scale the data? I see some clusters. How did we cluster it? Did we use the default parameters or change something? And so forth. On top, there is the whole topic of revisiting datasets and projects that are several years old, where the people who were working on it have moved on, but which are now treasure troves that provide context and training data for agents.

It does not matter how good an AI foundation model (or whatever you are using) is, if your datasets and the infrastructure that hosts them are problematic. It's the classic term "garbage in, garbage out." So how do we handle all of this, aside from hiring a team of data engineers? This is where LaminR helps. It is an open-source package that specializes in dealing with data infrastructure needs that naturally arise in the current paradigm of using many big datasets with many agents and large teams to train better models. In particular, LaminR manages metadata to allow querying and finding data and it tracks every last line of code that did any sort of modification to any part of a data object by whom and at what time. So if a data scientist has to revisit an old dataset or one they did not work on, they'll have the information that they need.

To illustrate this, we use the well-known PBMC 3k dataset. This dataset has been featured in Seurat's [guided clustering tutorial](https://satijalab.org/seurat/articles/pbmc3k_tutorial.html) for a decade, and is still the common entrypoint in single-cell RNA sequencing analysis.

The present example assumes you have access to a hosted LaminDB instance via LaminHub, but you could just as well create your own instance on the command line. To connect to a hosted instance, you can use either the CLI or R:

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

Now we move to the R interface to Lamin (where you would otherwise use Python). In your script or Rmd file, you will do the following to set things up:

```r
library(laminr)
ln <- laminr::import_module("lamindb")
```

And then from here, you set up your project. Below is what that looks like. Importantly, you want Lamin to track what you do, so the code can be stored on their end and you can know what you did when you check back however many days/months/years from now:

```r
# Set up a project
proj <- ln$Project(name = "Basic Seurat analysis")$save()

# Start a tracked run
ln$track(project = "Basic Seurat analysis", path = this_rmd)

```

From here, you load the PBMC 3k dataset, and take it through whatever analysis you're going to do. Let's assume you did a standard pre-processing -> PCA -> clustering -> nonlinear dimensionality reduction set up. What you do next is save your Seurat object as a rds file.

Let's do that now. Below is the pipeline, as defined for the PBMC 3k dataset, in Seurat's [Guided Clustering Tutorial](https://satijalab.org/seurat/articles/pbmc3k_tutorial.html).

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

In other words, we have uploaded the PBMC 3k dataset, and have taken it through a standard data analysis pipeline.

Now here is where Lamin comes in.

The first thing we are going to do is store this Seurat object as an artifact on Lamin's side. Here is how we are going to do that. First, we are going to save the Seurat object as an rds file:

```r
saveRDS(cells, "pbmc3k_processed.rds")
```

The next thing we are going to do is turn it into an artifact using the following code:

```r
ln$Artifact("pbmc3k_processed.rds", key = "pbmc3k/pbmc3k_processed.rds")$save()
```

And from here, we are going to end the session, by running:

```r
ln$finish()
```

Importantly, in the R Markdown you are running, you're going to want to knit it. This allows for the visualization of a run report on Lamin's end, which is the knitted R markdown, stored on their end, so you can see what code is associated with your artifact.

Then the last thing you need to do in order for the run report to properly load, if you did not use notebook mode in R Studio. Go to the command line, in the directory that contains the R Markdown you’ve been working on (here, the file is pbmc3k.Rmd), and run:

```
lamin save pbmc3k.Rmd
```

The above saves the file pbmc3k.Rmd as a transform, to go along with your artifact “pbmc3k_processed.rds.” Now let's have a look at what things look like on their end.

If we navigate to `pbmc3k/pbmc3k_processed.rds` we see that it is connected to the notebook `pbmc3k.Rmd`, which we had saved earlier:

<div style="text-align: center">
<img width="800" src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/VMTTBgRdPy81Fb590000.png">
</div>

[Source](https://lamin.ai/laminlabs/training/artifact/VugfUMiwR8OtlnIU000L).

Clicking on the `pbmc3k.Rmd` notebook gives us the run report, which you can see below.

<div style="text-align: center">
<img width="800" src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/XTqrtXrdxkBjCIlw0000.png">
</div>

[Source](https://lamin.ai/laminlabs/training/transform/KFtlfbCiP9Bm000A).

This is something that is very useful when using Lamin: you get the exact code that went into the production of the artifact. You might be able to point to the script on the computer that you used or what not. But what if this object was given to you by a colleague. Or what if you're rebooting a project that is several years old, where everyone forgot the exact details of what was done when and how? Now you have full access to these things so you can quickly pick up where you (or others) left off.

You can also get the environment, which is the packages and versions thereof that were loaded at the time of running the script:

<div style="text-align: center">
<img width="800" src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/eGL2ZsiTk3E0pPEk0000.png">
</div>

[Source](https://lamin.ai/laminlabs/training/transform/KFtlfbCiP9Bm000A).

Every unit of work that you do can be more easily communicated, both with colleagues and your future self. For a given piece of data, every manipulation and the code surrounding a given manipulation is now recorded and stored making it easier to understand and reproduce. This becomes particularly useful in large projects where many stakeholders contribute data and analyses.
