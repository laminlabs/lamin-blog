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

## PBMC 3k dataset analysis: round 1

We will start with the flagship PBMC 3k dataset. This dataset is featured in Seurat's [guided clustering tutorial](https://satijalab.org/seurat/articles/pbmc3k_tutorial.html), a common entrypoint in single-cell RNA sequencing analysis using Seurat.

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

# For the knitting (otherwise Lamin does not recognize path)
this_rmd <- normalizePath(knitr::current_input(dir = TRUE))

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

Ok, let's have a look at the output of our work:

```r
DimPlot(cells, reduction = "umap")
```

![][image1]

The direct source of the image is [here](https://lamin.ai/laminlabs/training/transform/KFtlfbCiP9Bm0002).

And we'll go ahead and do one more from the tutorial. Coloring the UMAP by specific genes:

```r
FeaturePlot(cells, features = c("MS4A1", "GNLY", "CD3E", "CD14", "FCER1A", "FCGR3A", "LYZ", "PPBP", "CD8A"))
```

![][image2]

The direct source of this image is [here](https://lamin.ai/laminlabs/training/transform/KFtlfbCiP9Bm00020002).

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

Here is where the artifacts are, with mine being just under “last updated” in this picture:
![][image3]

Clicking on pbmc3k/pbmc3k_processed.rds shows us the artifact itself. You can see here that it is connected to the file pbmc3k.Rmd, which we had saved earlier:

![][image4]

Clicking on our transform “pbmc3k.Rmd” gives us the run report, which you can see below.
![][image5]
This image comes from [here](https://lamin.ai/laminlabs/training/transform/KFtlfbCiP9Bm0002/rUIgMcUOjXZxdrD3Olt5?filter[and][0][or][0][branch.name][eq]=main&filter[and][1][or][0][is_latest][eq]=true).

This is something that is very useful when using Lamin: you get the exact code that went into the production of the artifact. You might be able to point to the script on the computer that you used or what not. But what if this object was given to you by a colleague. Or what if you're rebooting a project that is several years old, where everyone forgot the exact details of what was done when and how? Now you have full access to these things so you can quickly pick up where you (or others) left off.

You'll note that the code visualized above is a R Markdown that is separate from this blog post, which is also written in the literate programming format. I bring up here for the sake of making the nit picky distinction for the more detail-oriented readership.

Anyway, you can get the source code, which is the code minus the output:

![][image6]

This image comes from [here](https://lamin.ai/laminlabs/training/transform/KFtlfbCiP9Bm0002).

And you can also get the environment, which is the packages and versions thereof that were loaded at the time of running the script:

![][image7]

This image comes from [here](https://lamin.ai/tjburns08/projectdata/transform/tyGjt1zD6H73).

## PBMC 3k dataset analysis: round 2

Now that we have looked at analysis of the PBMC 3k dataset in Seurat can be made into an artifact on Lamin's side using the Laminr package, we are now going to look at how to retrieve this object and modify it.

In this simple example, we are going to pull out the PBMC 3k dataset that we just stored as an artifact. We note that we ran UMAP on it in the previous run, and here we are going to run t-SNE on it. We will then save the Seurat object, now with t-SNE coordinates, and store it again as an artifact.

To this end, we make a new Rmd file. In it, we start again by connecting to the Lamin database, as we did before:

```r
lc <- laminr::import_module("lamin_cli")
lc$login(user = "username")
lc$connect("instance_owner/your_instance")
```

Then we have the same setup code as before.

```r
library(laminr)

ln <- import_module("lamindb")

# For the knitting (otherwise Lamin does not recognize path)
this_rmd <- normalizePath(knitr::current_input(dir = TRUE))

# Start a tracked run
ln$track(project = "Basic Seurat analysis", path = this_rmd)
```

From here, we are going to pull the artifact that we have saved. The artifact is going to have an ID associated with it. The way we find that ID is you go onto the Lamin website, go to your artifact, and in the upper right corner you will see some text just above the "Get" button. That's the artifact ID. It looks like this, on the right side:

![][image8]

This image comes from [here](https://lamin.ai/laminlabs/training/artifact/fNsILwJTiDMhOBvc).

Notice the "copy" button to the left of the "Get" button. Click on that. Then, you'll paste into R, like this:

```r
art <- ln$Artifact$get("VugfUMiwR8OtlnIU0002")
```

Now you have access to your artifact.

From here, we pull out the data (the Seurat object) like this:

```r
cells <- art$load()
```

And from here, we do our modification:

```r
library(Seurat)

cells <- Seurat::RunTSNE(cells)
```

Now to get the new artifact back into Lamin, we will first save it as a rds file as before. For the sake of understanding in this tutorial, we are going to save it as a different rds file rather than overwriting the first one.

```r
saveRDS(cells, "pbmc_processed_2.rds")
```

From here, we create a new artifact, but with the same key as the first one. And then we save it.

```r
ln$Artifact("pbmc_processed_2.rds", key = "pbmc3k/pbmc3k_processed.rds")$save()
```

And finish the session.

```r
ln$finish()
```

Let’s have a look at what we were able to do. We have a saved Seurat object artifact that has a t-SNE map done on it. We can see this in the image below:

![][image9]
This image is from [here](https://lamin.ai/laminlabs/training/transform/fAGSp4iqMJG0?filter%5Band%5D%5B0%5D%5Bor%5D%5B0%5D%5Bbranch.name%5D%5Beq%5D=main&filter%5Band%5D%5B1%5D%5Bor%5D%5B0%5D%5Bis_latest%5D%5Beq%5D=true).

Remember to knit the Rmd file so you can see the updated source code that went into the artifact, as shown in the “run report” as discussed above. And as before, if you did not use notebook mode on RStudio, you need to go to the command line, in the directory with the R Markdown, and run:

```
lamin save pbmc3k.Rmd
```

## Conclusions

As you can see from this post, every unit of work that you do can be more easily communicated, both with colleagues and your future self. For a given piece of data, every manipulation and the code surrounding a given manipulation is now recorded and stored.

Here, we took single-cell data and did two rounds of standard Seurat analysis on it. The first round was a standard analysis pipeline with the PBMC 3k dataset. The second round was a modification, whereby we added t-SNE to the Seurat object. Both rounds have been codified and stored. The Seurat object has been stored as an artifact on Lamin's side. You or anyone on your team can pull the artifact or previous versions of the artifact (in case you want to "roll it back" the way you would code within GitHub).

For long term projects and projects that involve collaborators, the type of infrastructure that Lamin provides is valuable, if not indispensable, for computational biology teams doing single-cell or anything else.

We note that as the datasets become larger and more complex, especially in projects that involve training or fine tuning foundation models, this type of infrastructure will become increasingly important and really show its value for the community. It is thus recommended that even if you don't need this type of infrastructure right now, you should learn the ropes around it. Because given the current trends in bioinformatics, it is inevitable that you are going to need this type of infrastructure down the line.
