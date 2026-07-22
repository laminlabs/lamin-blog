---
title: Tracking data lineage across Nextflow, Python, and R with nf-lamin
date: 2026-08-01
author: rcannood, jpfeuffer, Zethson, ap-dash, fredericenard, lazappi, tgelafr-pfzr, SZhengP, sunnyosun, andreassteffen, falexwolf
affiliation:
  andreassteffen: Pfizer, Berlin
  ap-dash: Pfizer, Berlin
  falexwolf: Lamin Labs, Munich
  fredericenard: Lamin Labs, Munich
  jpfeuffer: Pfizer, Berlin
  lazappi: Data Intuitive, Lebbeke
  rcannood: Edaro, Ghent
  sunnyosun: Lamin Labs, Munich
  SZhengP: Pfizer, Berlin
  tgelafr-pfzr: Pfizer, Berlin
  Zethson: Lamin Labs, Munich
orcid:
  andreassteffen: 0000-0002-6952-7391
  ap-dash: 0000-0002-7342-8636
  falexwolf: 0000-0002-8760-7838
  # fredericenard: ?
  jpfeuffer: 0000-0001-8948-9209
  lazappi: 0000-0001-7744-8565
  rcannood: 0000-0003-3641-729X
  sunnyosun: 0000-0002-2365-0888
  # SZhengP: ?
  # tgelafr-pfzr: ?
  Zethson: 0000-0002-8937-3457
docs: https://docs.lamin.ai/nf-lamin
repo: https://github.com/laminlabs/nf-lamin
---

nf-lamin came out of a practical need at Pfizer: tracking complete data lineage for artifacts produced across the entire stack, from wet lab metadata through Nextflow pipelines to machine learning & data visualization, in Python, Nextflow & R. This was already possible by registering Nextflow outputs with lamindb in a [post-run script](https://docs.lamin.ai/nextflow#post-run-scripts), but it was cumbersome and captured only outputs after the fact. With nf-lamin, the same artifact can be referenced from Nextflow, Python & R, and runs & artifacts are created during the execution of any Nextflow workflow. It has since been used extensively at Pfizer to run both nf-core & in-house workflows.

## Imagine opening up your laptop to this

![A Slack thread: results posted as an S3 path months ago, questions arriving today.](_static/nf-lamin-slack-thread.png)

On a good day, the forensic analysis through output paths and execution logs (if they still exist) costs an afternoon. In practice people just rerun the workflow with known parameters, and *hope* the outputs come close enough to the original outputs.

For scripts & notebooks, `lamindb` & `laminr` already fix this: one `track()` call records the code, its execution & the data it touched, and every artifact gets a `uid` that identifies it wherever it is stored. `nf-lamin` seamlessly brings the same to Nextflow, *during* the run rather than after it.

Imagine the same run, with `nf-lamin` loaded.
## Referencing LaminDB artifacts from Nextflow

Every artifact in LaminDB has a `uid`.
With `nf-lamin` loaded, that `uid` becomes a valid Nextflow input:

```bash
nextflow run nf-core/scrnaseq --input lamin://laminlabs/lamindata/artifact/PnNjE93TdZGJ
```

The plugin resolves `lamin://` URIs through Nextflow's standard `file()` mechanism, so it works for pipeline parameters, sample sheet entries & channel operations alike.


The same `uid` resolves everywhere else you work:

:::::{tab-set}
::::{tab-item} Nextflow

```groovy
reference = file("lamin://laminlabs/lamindata/artifact/PnNjE93TdZGJ")
```

::::
::::{tab-item} Python

```python
reference = ln.Artifact.get("PnNjE93TdZGJ")
```

::::
::::{tab-item} R

```r
reference <- ln$Artifact$get("PnNjE93TdZGJ")
```

::::
::::{tab-item} CLI

```bash
lamin get artifact --uid PnNjE93TdZGJ
```

::::
:::::

## Cross-language data lineage

Not only does nf-lamin enable data lineage with Nextflow, it also does so across platforms. For instance, a user might create a sample sheet in an R script, run a Nextflow workflow, and annotate the resulting AnnData file in an IPython notebook.

```{mermaid}
flowchart LR
    rscript[/"samplesheet.R"/]:::transform
    ref["reference GRCm39"]:::artifact
    sheet["samplesheet.csv"]:::artifact
    nf[/"nf-core/scrnaseq"/]:::transform
    h5ad["combined_matrix.h5ad"]:::artifact
    nb[/"annotate.ipynb"/]:::transform
    ann["annotated.h5ad"]:::artifact

    rscript --> sheet --> nf --> h5ad --> nb --> ann
    ref --> nf
```

Each step registers itself as a Run:

:::::{tab-set}
::::{tab-item} 1. Sample sheet (R)

```r
library(laminr)
ln <- import_module("lamindb")
ln$track()

fastqs <- ln$Artifact$filter(key__startswith = "raw/mouse-brain/")$to_dataframe()

samplesheet <- build_samplesheet(fastqs, min_reads = 1e6)
write.csv(samplesheet, "samplesheet.csv", row.names = FALSE)

sheet <- ln$Artifact$from_df(samplesheet, key = "samplesheets/mouse-brain.csv")$save()
sheet$uid
#> "8h2kLmQpRvXn"

ln$finish()
```

::::
::::{tab-item} 2. Pipeline (Nextflow)

```bash
nextflow run nf-core/scrnaseq \
  --input lamin://laminlabs/lamindata/artifact/8h2kLmQpRvXn \
  --fasta lamin://laminlabs/lamindata/artifact/PnNjE93TdZGJ \
  --gtf   lamin://laminlabs/lamindata/artifact/Kd7mYc2WsRtB \
  -profile docker
```

A `scrnaseq` run writes many files, so an output rule registers the `.h5ad` and ignores the rest.

:::{dropdown} nextflow.config

```groovy
plugins {
    id 'nf-lamin'
}

lamin {
    instance = "laminlabs/lamindata"
    api_key  = secrets.LAMIN_API_KEY
    project  = "mouse-brain-atlas"

    output_artifacts {
        exclude_pattern = '.*'
        rules {
            h5ad {
                pattern = /.*\.h5ad$/
            }
        }
    }
}
```

:::

::::
::::{tab-item} 3. Annotation (Python)

```python
import lamindb as ln
import celltypist

ln.track()

adata = ln.Artifact.get("Wq4nBz8LxKcD").load()

predictions = celltypist.annotate(
    adata, model="Mouse_Whole_Brain.pkl", majority_voting=True
)
adata.obs["cell_type"] = predictions.predicted_labels["majority_voting"]

ln.Artifact.from_anndata(adata, key="annotated/mouse-brain.h5ad").save()

ln.finish()
```

::::
:::::

The questions from the Slack thread are now queries:

:::::{tab-set}
::::{tab-item} Python

```python
artifact = ln.Artifact.get(key="annotated/mouse-brain.h5ad")
artifact.view_lineage()
```

::::
::::{tab-item} R

```r
artifact <- ln$Artifact$get(key = "annotated/mouse-brain.h5ad")
artifact$view_lineage()
```

::::
:::::

![Lineage graph printed in the console][image2]

The same graph is on LaminHub, where it is a link rather than a screenshot, and every node opens onto its metadata, its run report & its environment:

![The lineage graph on LaminHub][image3]

