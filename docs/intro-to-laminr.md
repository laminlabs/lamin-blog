---
title: "An introduction to LaminR, using the PBMC 3k dataset"
date: 2026-03-26
author: tjburns08
affiliation:
  tjburns08: Burns Life Sciences Consulting, Berlin
---

There are always exciting new analyses of new data to be done with new tools. This is especially true in the current frothing cauldron of innovation around AI. But any data scientist will tell you that one of the keys to a good data science project is good data engineering practices. If your data infrastructure is bad (e.g. your data are disorganized, you don't know who did what, and so forth), you're not going to have a good time. Thus, a lot of work needs to be front loaded into how the data are going to be handled, stored, modified, and tracked over a project, while being compliant to any regulations around the data itself (e.g. in the US, HIPAA).

Here, we are going to focus on single-cell analysis as a use case...a particularly important one. If we roll the clock back to the early to mid 2010s, single-cell technologies (e.g. CyTOF, droplet-based sequencing) were still relatively new. Thus, the datasets were still relatively small compared to now. But today, we see the development of large single-cell "atlases" of increasing size, with a flagship example being Chan-Zuckerberg Initiative's (CZI's) [Billion Cells Project](https://chanzuckerberg.com/newsroom/billion-cells-project-launches-advance-ai-biology/).

If we stick with CZI for a minute, we note that their vision is around a so-called [virtual cell](https://arxiv.org/abs/2409.11654). You can think of this as an AI-based cell simulation that will allow for in-silico clinical predictions (among other things). How is this related to the Billion Cells project? In the current paradigms around generative AI (genAI), we note that they require lots of training data. Thus, the more data CZI has, the better their AI models are going to be, which is going to lead to a more fully realized vision around virtual cells. To this end, they are indeed building foundation models, with [Universal Cell Embeddings](https://www.biorxiv.org/content/10.1101/2023.11.28.568918v1) as an early example (2023) and [TranscriptFormer](https://www.biorxiv.org/content/10.1101/2025.04.25.650731v1) (2025) as a more recent one.

Between the very large datasets being fed into the AI foundation models, one emerging theme is that of managing lots and lots of data. This could be at the level of a major organization like CZI making their own foundation models with their own billion cells dataset, or a smaller academic lab taking these foundation models and fine-tuning them with their internal data.

This goes well beyond having enough disk space to store everything you have. Anyone who has worked with large and complex datasets knows that the devil is in the details. You might have multiple data scientists manipulating the data in multiple ways. Did we do a log1p transform or an asinh transform? Did we center and scale the data? I see some clusters. How did we cluster it? Did we use the default parameters or change something? And so forth. For each sample. In who knows how many samples. And of course, there is the whole issue of revisiting datasets and projects that are several years old, where the people who were working on it have moved on.

It does not matter how good your AI foundation model (or whatever you are using) is, if your datasets and the infrastructure that houses them are problematic. It's the classic term "garbage in, garbage out." So how do we handle all of this, aside from hiring a team of data engineers?

This is where [Lamin](https://lamin.ai/) comes in. Lamin is a SAAS infrastructure that specializes in dealing with data infrastructure needs that naturally arise in the current paradigm of massive datasets training massive AI models. This includes (among other things) data storage, metadata (descriptions of the data objects in question), and tracking every last line of code that did any sort of modification to any part of a data object by whom and at what time. So if a data scientist has to revisit an old dataset or one they did not work on, they'll have the information that they need.

We will use the well-known PBMC 3k dataset. This dataset has been featured in Seurat's [guided clustering tutorial](https://satijalab.org/seurat/articles/pbmc3k_tutorial.html) for a decade, and is still the common entrypoint in single-cell RNA sequencing analysis.

Here, we are going to deal with the following use case: a raw dataset is analyzed, and the Seurat object is saved as a rds file. Then, I or someone else wants to load the Seurat object and modify it. This modification is saved and the rds file is overwritten.

Lamin can track exactly what was done on the PBMC 3k dataset Seurat object, to the level of remembering what script was used for what modification. Lamin stores its data as what are called "artifacts." This is a collection of data and metadata that is stored in the cloud on Lamin's side, but accessible by the user at any time. So here is how it works.

I'm not going to cut and paste the entire guided clustering tutorial into this, but rest assured this is what was done. I'm just going to show you the extra stuff that allows for the use of Lamin's infrastructure with the analysis.

Before you even do anything with Seurat analysis whatsoever, you start by logging in. You import the Lamin command line interface (CLI) into R. You then log in, and connect. In R, it looks like this:

```r
lc <- laminr::import_module("lamin_cli")
lc$login(user = "username")
lc$connect("instance_owner/your_instance")
```

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
