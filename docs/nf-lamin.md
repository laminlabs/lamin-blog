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

Bioinformatics pipelines in Nextflow are a well-established, robust and reproducible unit of the data stack in many life science organizations.
But what about connecting Nextflow runs to upstream and downstream data flow, that is, data entry in the wetlab and analytical workflows?
Here, we present the open-source Nextflow plugin `nf-lamin`, which solves this problem with a single config line by hooking into Nextflow's internal artifact publishing system.

Analytical workflows in Python or R often start in a setting like this:

<div style="text-align: center">
<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/zy0p2pPy7SY2qvB80000.png" alt="A Slack thread: results posted as an S3 path months ago, questions arriving today." width="600" style="padding: 0;"/>
</div>

On a good day, tracing it back through output paths and execution logs just costs a certain amount of LLM tokens. In practice people just rerun the workflow with the parameters they think were used, and hope the results come close enough. For Python and R workflows, `lamindb` & `laminr` already fix the problem of data lineage: one `track()` call records the code, its execution, and the data it touched, and every artifact gets a `uid` that identifies it wherever it is stored.

`nf-lamin` brings the same traceability to Nextflow. With `nf-lamin` loaded, an artifact `uid` becomes valid Nextflow input:

```bash
nextflow run nf-core/scrnaseq --input lamin://laminlabs/lamindata/artifact/rF7oiknTdhpfqU5H
```

The plugin resolves `lamin://` URIs through Nextflow's standard `file()` mechanism, so it works for pipeline parameters, sample sheet entries & channel operations alike. The same `uid` also resolves everywhere else you work:

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

## Cross-language data lineage

`nf-lamin` tracks lineage across languages, not just within Nextflow. To show this end to end, we ran a small showcase: build a sample sheet in an R script, quantify public 10x PBMC data with `nf-core/scrnaseq`, and annotate the resulting AnnData file with CellTypist in a Jupyter notebook.

```{mermaid}
flowchart LR
    rscript("1_samplesheet.R"):::focal
    ref["GRCh38 reference"]:::artifact
    sheet["samplesheet.csv"]:::artifact
    nf("nf-core/scrnaseq"):::focal
    h5ad["raw_data.h5ad"]:::artifact
    nb("3_post_process.ipynb"):::focal
    ann["post_processed.h5ad"]:::artifact

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

Only `--input` is a `lamin://` URI here; the reference is a plain Ensembl URL. `nf-lamin` tracks both as input artifacts, so the FASTQs & reference show up in the lineage even though they never lived in LaminDB.

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
::::{tab-item} 3. Post-processing (Python)

```python
import lamindb as ln
import scanpy as sc
import celltypist
from celltypist import models

ln.track()

# the combined count matrix registered by nf-lamin during the run
adata = ln.Artifact.get("aqOOFyumixTtQNOs").load()

# celltypist expects log1p-normalised counts and gene symbols as var_names
adata.var_names = adata.var["gene_symbol"].astype(str)
adata.var_names_make_unique()
sc.pp.normalize_total(adata, target_sum=1e4)
sc.pp.log1p(adata)

# annotate immune cell types
models.download_models(model="Immune_All_Low.pkl")
predictions = celltypist.annotate(adata, model="Immune_All_Low.pkl", majority_voting=True)
adata.obs["cell_type"] = predictions.predicted_labels["majority_voting"].values

# save the annotated matrix as a new artifact
ln.Artifact.from_anndata(
    adata,
    key="annotated/pbmc8k.h5ad",
    description="CellTypist annotated PBMCs (Immune_All_Low)",
).save()

ln.finish()
```

::::
:::::

The questions from the Slack thread are now queries:

:::::{tab-set}
::::{tab-item} Python

```python
artifact = ln.Artifact.get(key="annotated/pbmc8k.h5ad")
artifact.view_lineage()
```

::::
::::{tab-item} R

```r
artifact <- ln$Artifact$get(key = "annotated/pbmc8k.h5ad")
artifact$view_lineage()
```

::::
:::::

`view_lineage()` renders the graph inline. On LaminHub it is the same graph, but every node is a link rather than a screenshot -- each one opens onto its metadata, its run report & its environment:

<div style="text-align: center">
<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/nWCSCiNymiBmzDur0000.png" alt="The full cross-language lineage of annotated/pbmc8k.h5ad on LaminHub" width="700" style="padding: 0;"/>
</div>

Opening the annotation node lands on the run that produced the file: the exact count matrix it read, the annotated `.h5ad` it wrote, and the code, report & environment behind it.

<div style="text-align: center">
<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/ANfVHymJKyZp8dRp0000.png" alt="The annotation run on LaminHub, with its input and output artifacts, code, report and environment" width="700" style="padding: 0;"/>
</div>

## Try it yourself

The complete, runnable version of this walkthrough -- samplesheet script, `nextflow.config` & annotation notebook -- lives at [github.com/rcannood/showcase-nf-lamin](https://github.com/rcannood/showcase-nf-lamin). You'll need Nextflow and Docker, R with `laminr`, and Python with `lamindb`, `scanpy` & `celltypist`. To use your own instance, connect both R and Python to it before calling `track()`. Replace the pipeline's `--input` with `lamin://<your-lamin-instance>/artifact/<samplesheet-uid>`, using the UID printed by your R script. After the pipeline finishes, replace the UID in the annotation's `ln.Artifact.get(...)` call with the combined count matrix UID registered by your run. Point the plugin at that same instance in `nextflow.config`:

```groovy
plugins {
    id 'nf-lamin'
}

lamin {
    instance = <your-lamin-instance>
    api_key  = secrets.LAMIN_API_KEY
}
```

See the [`nf-lamin` docs](https://docs.lamin.ai/nf-lamin) for the full configuration reference. If you run into a bug, please file a minimal reproducible example on the [issues page](https://github.com/laminlabs/nf-lamin/issues).

## Acknowledgements

We are grateful to the team at Pfizer, who thought alongside us about the functionality they needed and the behavior they expected, and who put the plugin through both nf-core and in-house workflows.

We are also grateful to the Nextflow team: much of the plugin infrastructure `nf-lamin` builds on -- the extension points, the plugin repository & the plugin template -- took shape over the course of its development.
