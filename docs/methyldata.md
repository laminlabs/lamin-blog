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

[MethylGPT](https://github.com/albert-ying/MethylGPT)[^ying24] is a transformer-based foundation model trained on over 150,000 human methylation profiles across tissue types, donor ages, and disease conditions — one of the largest curated DNA methylation corpora to date.

MethylGPT was trained on 226,555 DNA methylation profiles (154,063 after QC and deduplication) from 5,281 datasets. The preprocessed default pretraining dataset covers 49,156 CpG sites across diverse tissue types, conditions, and developmental stages. The model learns representations of CpG sites that capture local genomic context and higher-order chromosomal features, achieving a Pearson correlation of 0.929 for methylation value prediction.

The project distributes its pretraining data as parquet shards on static storage: compact methylation files (sample `id` plus a `data` column listing ~49k beta values) and matching sample metadata files live in separate directories, with no unified way to query them.

We ingested this corpus into [`laminlabs/methyldata`](https://lamin.ai/laminlabs/methyldata): a public LaminDB instance where you can browse dataset blocks in a graphical interface, query by tissue, disease, cell line, or ethnicity, filter individual samples by age or case/control status, and load matched beta matrices through a single API. We also generated wide beta matrices (one column per CpG site) from the compact files to make downstream analysis easier.

For example, you might want blood samples aged 18–65 to train an epigenetic clock[^horvath13][^hannum13] — a downstream task MethylGPT benchmarks include[^ying24].
In the original bundle, that means opening metadata and methylation parquet shards one by one, filtering rows by hand, and matching the right files for each dataset block.
In the database, you express what you care about as entities — tissue, disease, file type — and join metadata with beta values programmatically.

## Query and load training data

Each dataset block pairs sample metadata with a matching beta matrix, linked via artifact features.
The snippet below narrows to blood at both the artifact and sample level; the [MethylGPT Data Querying and Loading Tutorial](https://lamin.ai/laminlabs/methyldata/transform/Jxbyx3uaPNcu000C) scales this across the full corpus, adds an age filter, caches wide beta parquets (~49k columns) before load, and trains an age-prediction model with lineage.

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

# sample-level: blood rows in the first block
meta_blood_ds = meta_artifacts_blood.order_by("key").open().filter(pc.field("tissue") == "blood")
meta_df = meta_blood_ds.to_table().to_pandas()

# each metadata block links to its matching beta matrix via an artifact feature
meta_artifact = meta_artifacts_blood.order_by("key").first()
beta_artifact = meta_artifact.features["beta_artifact"]
beta_df = beta_artifact.load()

# beta uses column `id`; metadata uses `GSM_ID`
df = beta_df.merge(meta_df, left_on="id", right_on="GSM_ID")
```

See also [Stream datasets from storage](https://docs.lamin.ai/arrays) and explore the instance on [lamin.ai/laminlabs/methyldata](https://lamin.ai/laminlabs/methyldata).

## Sample metadata

Each dataset block includes a sample metadata parquet from the MethylGPT bundle, validated in LaminDB against the [`methylgpt_metadata`](https://lamin.ai/laminlabs/methyldata/schema/5IKjIq3L4vd29c0j) schema.

<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/XChydSOI1H7DVCRB0000.png" width="700">

In LaminDB, annotations are at the **artifact** level: SQL aggregates over these tables tag each dataset block with the tissues, diseases, cell lines, and ethnicities it contains.
To subset individual samples — by age, case/control status, or treatment — open metadata parquets as a single [PyArrow dataset](https://docs.lamin.ai/arrays) and filter across shards, as in the snippet above.

## Methods

We mirrored the MethylGPT type3 pretraining bundle in LaminDB under the `MethylGPT` project.
Type3 is MethylGPT's default pretraining panel of 49,156 CpG sites; training profiles were sourced from the [EWAS data hub](https://ngdc.cncb.ac.cn/ewas/datahub)[^ewas26][^ewas22].
For each dataset block, three linked artifact types are registered and tagged with [`FileType`](https://lamin.ai/laminlabs/methyldata/ulabels/BWc6wSdK) ULabels (`sample_metadata`, `beta`, `preprocessed`):

- **Sample metadata** (`.parquet`, `methylGPT/sample_metadata/`) — biological and experimental annotations per sample, including GEO metadata sourced via [ClockBase](https://doi.org/10.1101/2023.02.28.530532)[^clockbase23].
- **Beta values** (`.parquet`, `methylGPT/beta/`) — wide-format methylation matrices with one column per CpG site (~49k probes), generated by us from the compact parquet files.
- **Preprocessed datasets** (`.parquet`, `methylGPT/processed_dataset/processed_type3_parquet_shuffled/`) — the compact format MethylGPT expects for inference: a sample `id` column and a `data` column with lists of beta values per sample (see the [inference guide](https://github.com/albert-ying/MethylGPT/blob/main/docs/inference_guide.md#data-format)).

Metadata and beta artifacts within a block are linked bidirectionally via `meta_artifact` and `beta_artifact` artifact features.
A shared **CpG probe reference** (`methylGPT/probe_ids_type3.csv`) maps column order to Illumina probe IDs for the type3 panel.
Artifact-level labels (tissues, diseases, cell lines, ethnicities) are computed as SQL aggregates over each block's sample metadata table at ingest time.

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
