---
title: "methyldata: An atlas for methylation datasets based on MethylGPT's training data"
date: 2026-06-25
author: namsaraeva, sheetalgiri, falexwolf, sunnyosun
affiliation:
  namsaraeva: Lamin Labs, Munich
  sheetalgiri: Lamin Labs, Munich
  falexwolf: Lamin Labs, Munich
  sunnyosun: Lamin Labs, Munich
db: https://lamin.ai/laminlabs/methyldata
repo: https://github.com/albert-ying/MethylGPT
tweet: TBD
linkedin: TBD
---

[MethylGPT](https://github.com/albert-ying/MethylGPT)[^ying24] is a transformer-based foundation model trained on over 150k human methylation profiles across tissue types, donor ages, and disease conditions sourced from the [EWAS data hub](https://ngdc.cncb.ac.cn/ewas/datahub)[^ewas26][^ewas22]. To simplify sharing these datasets including their annotations, we seeded the extensible [`laminlabs/methyldata`](https://lamin.ai/laminlabs/methyldata) database with a curated version of the MethylGPT training data.

Say you want to retrieve blood samples from donors between ages 18 to 65, you can query all parquet files annotated by those samples and then trust that there is a validated column `blood`:

```python
import lamindb as ln
import pyarrow.compute as pc

db = ln.DB("laminlabs/methyldata")

# get a few labels
project = db.Project.get(name="MethylGPT")
is_metadata = db.ULabel.get(name="sample_metadata")
blood = db.bionty.Tissue.get(name="blood")

# retrieve all metadata parquet files
meta_artifacts = db.Artifact.filter(projects=project, ulabels=is_metadata, tissues=blood)

# query those samples in the parquet files that match blood
with meta_artifacts.open() as meta_datasets:
    meta_df = meta_datasets.filter(pc.field("tissue") == "blood").to_table().to_pandas()
```

This query behaves as it should because the `sample_metadata` files were validated with the [`methylgpt_metadata`](https://lamin.ai/laminlabs/methyldata/schema/5IKjIq3L4vd29c0j) schema:

<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/XChydSOI1H7DVCRB0000.png" width="700">

Here is an exemplary [notebook](https://lamin.ai/laminlabs/methyldata/transform/Jxbyx3uaPNcu000C) that uses the data access to train an epigentic clock, a model that predicts chronological age based on methylation profiles.[^horvath13][^hannum13]

## Methods

We ingested the MethylGPT pretraining data[^ying24][^clockbase23] under the `MethylGPT` project.
The corpus comprises 226,555 profiles (154,063 after QC and deduplication) from 5,281 EWAS hub studies, covering 49,156 CpG sites.[^ewas26][^ewas22]
For each dataset, three `.parquet` artifact types are registered and tagged with [`FileType`](https://lamin.ai/laminlabs/methyldata/ulabels/BWc6wSdK) labels:

- **Sample metadata** — biological and experimental annotations per sample, validated with the `methylgpt_metadata` schema
- **Beta values** — wide-format methylation matrices with one column per CpG site (~49k probes)
- **Processed values** — long-format methylation matrices with a `data` column with lists of beta values per sample

## Author contributions

Altana harmonized sample metadata for LaminDB, generated the wide beta tables, and developed the example notebook.

Sheetal reviewed and refined the example notebook.

Alex helped conceive the project and write the post.

Sunny supervised the work and ingested processed datasets.

## Code & data availability

- Database: [lamin.ai/laminlabs/methyldata](https://lamin.ai/laminlabs/methyldata)
- MethylGPT repository: [github.com/albert-ying/MethylGPT](https://github.com/albert-ying/MethylGPT)
- Tutorial: [MethylGPT Data Querying and Loading Tutorial](https://lamin.ai/laminlabs/methyldata/transform/Jxbyx3uaPNcu000C)
- Docs: [docs.lamin.ai/dna-methylation](https://docs.lamin.ai/dna-methylation), [docs.lamin.ai/arrays](https://docs.lamin.ai/arrays)

## How to cite

Please cite the original references! If the database is useful to you, consider citing:

```
Namsaraeva A, Giri S, Sun S & Wolf A (2026). methyldata: An atlas for methylation datasets based on MethylGPT's training data. Lamin Blog.
https://blog.lamin.ai/methyldata
```

## References

[^ying24]: Ying K, Song J, Cui H et al. (2024). MethylGPT: a foundation model for the DNA methylome. [bioRxiv](https://doi.org/10.1101/2024.10.30.621013) | [PubMed](https://pubmed.ncbi.nlm.nih.gov/39574641/).

[^clockbase23]: Ying K, Tyshkovskiy A, Trapp A et al. (2023). ClockBase: a comprehensive platform for biological age profiling in human and mouse. [bioRxiv](https://doi.org/10.1101/2023.02.28.530532).

[^horvath13]: Horvath S (2013). DNA methylation age of human tissues and cell types. [Genome Biology](https://doi.org/10.1186/gb-2013-14-10-r115).

[^hannum13]: Hannum G, Guinney J, Zhao L et al. (2013). Genome-wide methylation profiles reveal quantitative views of human aging rates. [Molecular Cell](https://doi.org/10.1016/j.molcel.2012.10.016).

[^ewas26]: Yang F, Xiong Z, Zong W et al. (2026). EWAS Open Platform 2026: a deeply integrated resource for epigenome-wide association studies. [Nucleic Acids Res](https://doi.org/10.1093/nar/gkaf1155).

[^ewas22]: Xiong Z, Yang F, Li M et al. (2022). EWAS Open Platform: integrated data, knowledge and toolkit for epigenome-wide association study. [Nucleic Acids Res](https://doi.org/10.1093/nar/gkab972).
