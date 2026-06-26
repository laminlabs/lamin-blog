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

[MethylGPT](https://github.com/albert-ying/MethylGPT)[^ying24] is a transformer-based foundation model trained on over 150,000 human methylation profiles across tissue types, donor ages, and disease conditions sourced from the [EWAS data hub](https://ngdc.cncb.ac.cn/ewas/datahub)[^ewas26][^ewas22]. To simplify API-based queries for these datasets, we seeded the extensible `methyldata` [database](https://lamin.ai/laminlabs/methyldata) with a curated version of the MethylGPT training data.

Subset the corpus by tissue, disease, or donor demographics, however, and the friction shows: methylation profiles and sample metadata live in separate parquet shards and static downloads, with no unified way to query them.
We ingested MethylGPT's type3 pretraining data into LaminDB and annotated each artifact with structured metadata — tissues, diseases, cell lines, and more — aggregated from the underlying sample tables via SQL queries.
We share [`laminlabs/methyldata`](https://lamin.ai/laminlabs/methyldata) as a public LaminDB instance where dataset blocks can be queried and loaded through a single API.

## What's in the database

The database mirrors the MethylGPT pretraining bundle and adds artifact-level annotations.
For each dataset block, three linked artifact types are registered:

- **Processed datasets** (`.parquet`, `methylGPT/processed_dataset/processed_type3_parquet_shuffled/`) — the compact format MethylGPT expects: a sample `id` column and a `data` column with lists of ~49,000 beta values per sample (see the [inference guide](https://github.com/albert-ying/MethylGPT/blob/main/docs/inference_guide.md#data-format)).
- **Beta values** (`.parquet`, `methylGPT/beta/`) — wide-format methylation matrices with one column per CpG site, derived from the compact parquet files.
- **Sample metadata** (`.parquet`, `methylGPT/sample_metadata/`) — biological and experimental annotations for each sample, including GEO metadata sourced via ClockBase.

A shared **CpG probe reference** (`methylGPT/probe_ids_type3.csv`) maps column order to Illumina probe IDs for the type3 panel.

## Sample metadata

Each dataset block includes a sample metadata parquet file validated against the [`methylgpt_metadata`](https://lamin.ai/laminlabs/methyldata/schema/5IKjIq3L4vd29c0j) schema.

<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/XChydSOI1H7DVCRB0000.png" width="700">

In LaminDB, annotations are at the **artifact** level: SQL aggregates over these tables tag each dataset block with the tissues, diseases, cell lines, and ethnicities it contains.

To subset individual samples — by age, case/control status, or treatment — open metadata parquets as a single [PyArrow dataset](https://docs.lamin.ai/arrays) and filter across shards; the [MethylGPT Data Querying and Loading Tutorial](https://lamin.ai/laminlabs/methyldata/transform/Jxbyx3uaPNcu000C) shows how.

## Query and load training data

The [MethylGPT Data Querying and Loading Tutorial](https://lamin.ai/laminlabs/methyldata/transform/Jxbyx3uaPNcu000C) walks through the full workflow: query blood samples aged 18–65 across the corpus, load their beta matrices, and train an age-prediction model — a classic epigenetic clock application[^horvath13][^hannum13][^altumage22][^trapp21] and one of MethylGPT's benchmarks[^ying24].
Each dataset block pairs sample metadata with a matching beta matrix, linked via artifact features:

```python
import lamindb as ln
import pyarrow.compute as pc

db = ln.DB("laminlabs/methyldata")
project = db.Project.get(name="MethylGPT")
file_types = db.ULabel.filter(type__name="FileType").lookup()

# all sample-metadata blocks in the project
meta_artifacts = project.artifacts.filter(ulabels=file_types.sample_metadata)

# artifact-level: SQL labels tag blocks that contain blood (not every row is blood)
blood = db.bionty.Tissue.get(name="blood")
meta_artifacts_blood = meta_artifacts.filter(tissues=blood)

# sample-level: stream rows from the first block
meta_blood_ds = meta_artifacts_blood.order_by("key").open().filter(pc.field("tissue") == "blood")
meta_df = meta_blood_ds.to_table().to_pandas()

# each metadata block links to its matching beta matrix via an artifact feature
meta_artifact = meta_artifacts_blood.order_by("key").first()
beta_artifact = meta_artifact.features["beta_artifact"]
beta_df = beta_artifact.load()

# beta uses column `id`; metadata uses `GSM_ID`
df = beta_df.merge(meta_df, left_on="id", right_on="GSM_ID")
```

It scales this to the full corpus: artifact-level queries by tissue, PyArrow filtering across metadata shards, caching wide beta parquets (~49k columns) before load, and training a model with lineage.
See also [Stream datasets from storage](https://docs.lamin.ai/arrays) and explore the instance on [lamin.ai/laminlabs/methyldata](https://lamin.ai/laminlabs/methyldata) — [34 `methylgpt_metadata` artifacts](https://lamin.ai/laminlabs/methyldata/artifacts?filter[and][0][or][0][is_latest][eq]=true&filter[and][1][or][0][schema.name][eq]=methylgpt_metadata), tagged with [`FileType`](https://lamin.ai/laminlabs/methyldata/ulabels/BWc6wSdK) ULabels.

## Author contributions

Altana curated the metadata, generated the wide tables, and developed the example notebook.

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

[^altumage22]: de Lima Camillo LP, Lapierre LR, Singh R (2022). A pan-tissue DNA-methylation epigenetic clock based on deep learning. [npj Aging](https://doi.org/10.1038/s41514-022-00085-y).

[^trapp21]: Trapp A, Kerepesi C, Gladyshev VN (2021). Profiling epigenetic age in single cells. [Nature Aging](https://doi.org/10.1038/s43587-021-00134-3).

[^ewas26]: Yang F, Xiong Z, Zong W et al. (2026). EWAS Open Platform 2026: a deeply integrated resource for epigenome-wide association studies. [Nucleic Acids Res](https://doi.org/10.1093/nar/gkaf1155).

[^ewas22]: Xiong Z, Yang F, Li M et al. (2022). EWAS Open Platform: integrated data, knowledge and toolkit for epigenome-wide association study. [Nucleic Acids Res](https://doi.org/10.1093/nar/gkab972).
