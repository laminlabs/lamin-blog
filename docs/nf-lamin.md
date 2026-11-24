---
title: "nf-lamin: Tracking data lineage across Nextflow pipeline runs"
date: 2026-11-19
author: rcannood, jpfeuffer, SZhengP, lazappi, tgelafr, Zethson, fredericenard, sunnyosun, ap, andreassteffen, falexwolf
affiliation:
  rcannood: Edaro, Ghent
  SZhengP: Pfizer, Cambridge, MA
  tgelafr: Pfizer, Cambridge, MA
  andreassteffen: Pfizer, Berlin
  ap: Pfizer, Berlin
  falexwolf: Lamin Labs, Munich
  fredericenard: Lamin Labs, Munich
  jpfeuffer: Pfizer, Berlin
  lazappi: Data Intuitive, Lebbeke
  sunnyosun: Lamin Labs, Munich
  Zethson: Lamin Labs, Munich
docs: https://docs.lamin.ai/nf-lamin
repo: https://github.com/laminlabs/nf-lamin
---

Nextflow pipelines are a reproducible part of the data stack in many life science organizations.
The flow around a run is often brittle: how wetlab samples and metadata enter a pipeline, and how later analyses use its outputs, can rarely be traced.
Here we present `nf-lamin`, an open-source Nextflow plugin that records that lineage without changing the pipeline.
It resolves inputs through Nextflow's `file()` mechanism and registers outputs through Nextflow's artifact publishing system.

Analytical workflows in Python or R often start in a setting like this:

<div style="text-align: center">
<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/zy0p2pPy7SY2qvB80000.png" alt="A Slack thread: results posted as an S3 path months ago, questions arriving today." width="600" style="padding: 0;"/>
</div>

On a good day, tracing sample sheets and reference genomes back through output paths and execution logs just costs a certain amount of LLM tokens. In practice people just rerun the workflow with the parameters they think were used, and hope the results come close enough. For Python and R workflows, `lamindb` & `laminr` already fix the problem of data lineage: one `track()` call records the code, its execution, and the data it touched, and every artifact gets a `uid` that identifies it wherever it is stored.

`nf-lamin` brings the same traceability to Nextflow. Enable the plugin in your Nextflow config and launch the pipeline the way you always do:

```bash
nextflow run nf-core/scrnaseq --input s3://my-bucket/samplesheet.csv --outdir s3://my-bucket/results
```

Every remote file a process reads (`s3://`, `gs://`, `https://`, ...) is linked to the run as an input artifact, and every file the pipeline publishes as an output artifact. An input that is already an artifact in LaminDB is matched by its path; anything else is registered on the fly.

:::{tip}
We recommend using `lamin://` URIs: pass an input artifact by its `uid`, and publish the outputs into your instance's storage. Lamin then manages access to the underlying S3 data for you:

```bash
nextflow run nf-core/scrnaseq --input lamin://laminlabs/lamindata/artifact/rF7oiknTdhpfqU5H --outdir lamin://laminlabs/lamindata
```

:::

The plugin resolves `lamin://` URIs through Nextflow's standard `file()` mechanism, so they work for pipeline parameters, sample sheet entries & channel operations alike. The same `uid` resolves everywhere else you work:

:::::{tab-set}
::::{tab-item} Nextflow

```groovy
samplesheet = file("lamin://laminlabs/lamindata/artifact/rF7oiknTdhpfqU5H")
```

::::
::::{tab-item} Python

```python
samplesheet = ln.Artifact.get("rF7oiknTdhpfqU5H")
```

::::
::::{tab-item} R

```r
samplesheet <- ln$Artifact$get("rF7oiknTdhpfqU5H")
```

::::
::::{tab-item} CLI

```bash
lamin get artifact --uid rF7oiknTdhpfqU5H
```

::::
:::::

## An example

`nf-lamin` tracks lineage across languages, not just within Nextflow. To show this end to end, we ran a small showcase: build a sample sheet in an R script, quantify public 10x PBMC data with `nf-core/scrnaseq`, and assign cell types to the resulting AnnData file with CellTypist in a Python script.

```{mermaid}
flowchart LR
    rscript("1_samplesheet.R"):::focal
    fastq("FASTQs"):::artifact
    ref("GRCh38 FASTA & GTF"):::artifact
    sheet("samplesheet.csv"):::artifact
    nf("nf-core/scrnaseq"):::focal
    h5ad("raw_data.h5ad"):::artifact
    nb("3_celltyping.py"):::focal
    ann("celltyped.h5ad"):::artifact

    rscript --> sheet --> nf --> h5ad --> nb --> ann
    fastq --> nf
    ref --> nf
```

Each step registers itself as a {class}`~lamindb.Run` object:

:::::{tab-set}
::::{tab-item} 1. Sample sheet (R)

```r
library(laminr)
ln <- import_module("lamindb")
ln$track()

# one sample, sequenced over two lanes (nf-core/scrnaseq's 10x PBMC 8k test data)
base <- "s3://ngi-igenomes/test-data/scrnaseq"
samplesheet <- data.frame(
  sample         = "pbmc8k",
  fastq_1        = paste0(base, c("/pbmc8k_S1_L007_R1_001.fastq.gz", "/pbmc8k_S1_L008_R1_001.fastq.gz")),
  fastq_2        = paste0(base, c("/pbmc8k_S1_L007_R2_001.fastq.gz", "/pbmc8k_S1_L008_R2_001.fastq.gz")),
  expected_cells = 10000
)
write.csv(samplesheet, "samplesheet.csv", row.names = FALSE)

# register the samplesheet; its uid becomes the pipeline input
sheet <- ln$Artifact(
  "samplesheet.csv",
  key = "showcase/pbmc8k_samplesheet.csv",
  description = "nf-core/scrnaseq samplesheet for 10x PBMC 8k (human)"
)$save()
sheet$uid
#> "rF7oiknTdhpfqU5H"

ln$finish()
```

::::
::::{tab-item} 2. Pipeline (Nextflow)

```bash
nextflow run nf-core/scrnaseq \
  -r 4.1.0 \
  -profile docker \
  -c nextflow.config \
  --input    lamin://laminlabs/lamindata/artifact/rF7oiknTdhpfqU5H \
  --fasta    https://ftp.ensembl.org/pub/release-110/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz \
  --gtf      https://ftp.ensembl.org/pub/release-110/gtf/homo_sapiens/Homo_sapiens.GRCh38.110.gtf.gz \
  --protocol 10XV2 \
  --outdir   s3://my-bucket/scrnaseq_showcase
```

None of these inputs needs special treatment. The FASTQs listed in the sample sheet are plain `s3://` paths and the reference is a plain Ensembl `https://` URL, yet `nf-lamin` links all of them to the run as input artifacts, so they show up in the lineage even though they never lived in LaminDB.

:::{note}
The sample sheet is passed as a `lamin://` URI, which references the artifact by its `uid`. This is recommended but never required: a sample sheet at a plain `s3://` path is tracked in exactly the same way.
:::

A `scrnaseq` run writes many files, so this config excludes everything by default and opts back in to the combined count matrix and the MultiQC report:

:::{dropdown} nextflow.config

```groovy
plugins {
    id 'nf-lamin'
}

lamin {
    instance     = 'laminlabs/lamindata'
    api_key      = secrets.LAMIN_API_KEY

    input_artifacts {
        rules {
            samplesheet     { include_paths = { params.input };          kind = 'dataset'; order = 1 }
            fastq_reads     { pattern = '.*\\.fastq(\\.gz)?$';           kind = 'dataset'; order = 2 }
            reference_fasta { pattern = '.*\\.(fasta|fa)(\\.gz)?$';      kind = 'dataset'; order = 3 }
            annotation      { pattern = '.*\\.(gtf|gff|gff3)(\\.gz)?$';  kind = 'dataset'; order = 4 }
        }
    }

    // exclude everything, then opt in to the files that matter
    output_artifacts {
        exclude_pattern = '.*'
        rules {
            multiqc_report         { type = 'include'; pattern = '.*multiqc_report\\.html$';                                           kind = 'report';  order = 1 }
            combined_filtered_h5ad { type = 'include'; pattern = '.*/mtx_conversions/combined_(filtered|cellbender_filter)_matrix\\.h5ad$'; kind = 'dataset'; order = 2 }
        }
    }
}

// allow a lamin:// URI as --input: skip nf-schema's ^\S+\.csv$ check
validation {
    ignoreParams = ['input']
}
```

:::

::::
::::{tab-item} 3. Cell typing (Python)

```python
import lamindb as ln
import scanpy as sc
import celltypist
from celltypist import models

ln.track()

# the combined count matrix registered by nf-lamin during the run
adata = ln.Artifact.get("SGHdW3cN3QXHJJCz").load()

# celltypist expects log1p-normalised counts and gene symbols as var_names
adata.var_names = adata.var["gene_symbol"].astype(str)
adata.var_names_make_unique()
sc.pp.normalize_total(adata, target_sum=1e4)
sc.pp.log1p(adata)

# predict immune cell types
models.download_models(model="Immune_All_Low.pkl")
predictions = celltypist.annotate(adata, model="Immune_All_Low.pkl", majority_voting=True)
adata.obs["cell_type"] = predictions.predicted_labels["majority_voting"].values

# save the cell typed matrix as a new artifact
ln.Artifact.from_anndata(
    adata,
    key="showcase/pbmc8k_celltyped.h5ad",
    description="10x PBMC 8k with CellTypist cell types (Immune_All_Low)",
).save()

ln.finish()
```

::::
:::::

The question from Slack can now be answered by exploring data lineage: the sample sheet, the FASTQs and the reference genome (FASTA & GTF) are all inputs of the pipeline run.

:::::{tab-set}
::::{tab-item} Python

```python
artifact = ln.Artifact.get(key="showcase/pbmc8k_celltyped.h5ad")
artifact.view_lineage()
```

::::
::::{tab-item} R

```r
artifact <- ln$Artifact$get(key = "showcase/pbmc8k_celltyped.h5ad")
artifact$view_lineage()
```

::::
:::::

`view_lineage()` renders the graph in the Python or R session. On the LaminHub UI, one can interactively explore each node to open their metadata (click the image to explore):

:::{figure} _static/nf-lamin/lineage.png
:alt: The full cross-language lineage of showcase/pbmc8k_celltyped.h5ad on LaminHub
:width: 700px
:align: center
:target: https://lamin.ai/laminlabs/lamindata/artifact/JvUll5j4iQDhTobi0000
:::

Every node in this graph lives in `laminlabs/lamindata`:

| Step | Run | Output artifact |
| --- | --- | --- |
| 1. Sample sheet (R) | [run](https://lamin.ai/laminlabs/lamindata/run/lImad5Q6qnIPcTAE) | [`showcase/pbmc8k_samplesheet.csv`](https://lamin.ai/laminlabs/lamindata/artifact/rF7oiknTdhpfqU5H0000) |
| 2. Pipeline (Nextflow) | [run](https://lamin.ai/laminlabs/lamindata/run/PXe4TYRvVNcRstzl) | [combined count matrix](https://lamin.ai/laminlabs/lamindata/artifact/SGHdW3cN3QXHJJCz0000) |
| 3. Cell typing (Python) | [run](https://lamin.ai/laminlabs/lamindata/run/Nsr6zK1Tqox0EX57) | [`showcase/pbmc8k_celltyped.h5ad`](https://lamin.ai/laminlabs/lamindata/artifact/JvUll5j4iQDhTobi0000) |

Opening the `nf-core/scrnaseq` node lands on the [pipeline run](https://lamin.ai/laminlabs/lamindata/run/PXe4TYRvVNcRstzl): the exact pipeline revision, the inputs it read, the outputs it published, and the Nextflow execution report. nf-core pipelines write that report by default, and `nf-lamin` attaches it to the run.

:::{figure} _static/nf-lamin/run.png
:alt: The nf-core/scrnaseq run on LaminHub, with its inputs, outputs and Nextflow execution report
:width: 700px
:align: center
:target: https://lamin.ai/laminlabs/lamindata/run/PXe4TYRvVNcRstzl
:::

## Trying it out

The complete, runnable version of this walkthrough -- samplesheet script, `nextflow.config` & cell typing script -- lives at [github.com/rcannood/showcase-nf-lamin](https://github.com/rcannood/showcase-nf-lamin). You'll need Nextflow and Docker, R with `laminr`, and Python with `lamindb`, `scanpy` & `celltypist`. To run it against your own LaminDB instance, set three environment variables and run the three steps:

```bash
export LAMIN_API_KEY=...
export LAMIN_CURRENT_INSTANCE=my-org/my-instance
export OUTDIR=s3://my-bucket/showcase/scrnaseq_pbmc8k

./1_samplesheet_pbmc8k.R  # registers the sample sheet
./2_run.sh                # runs nf-core/scrnaseq on it
./3_celltyping.py         # assigns cell types to the count matrix
```

`laminr`, `lamindb` & `nf-lamin` all read the instance and the API key from these variables, so none of the scripts needs editing.

## Code & data availability

See the previous section for the example of this blog post. The source code and the docs are here:

- Docs: https://docs.lamin.ai/nf-lamin
- Repo: https://github.com/laminlabs/nf-lamin
- Java client: https://github.com/laminlabs/lamin-api-client-java

## Acknowledgements

We are grateful to the Nextflow team for merging several pull request into Nextflow. In fact, much of the plugin infrastructure `nf-lamin` builds on -- the extension points, the plugin repository & the plugin template -- took shape over the course of `nf-lamin`'s development.

## Author contributions

Robrecht designed and implemented the `nf-lamin` plugin, Lamin's Java client, and made several pull requests to Nextflow itself to enable hooking into its publishing system.
