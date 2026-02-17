---
title: "A programmatically queryable CELLxGENE LaminDB instance"
date: 2026-02-21
author: sunnyosun*, zethson*, falexwolf
orcid:
  zethson: 0000-0002-8937-3457
  falexwolf: 0000-0002-8760-7838
affiliation:
  sunnyosun: Lamin Labs, Munich
  zethson: Lamin Labs, Munich
  falexwolf: Lamin Labs, Munich
db: https://lamin.ai/laminlabs/cellxgene
repo: https://github.com/laminlabs/cellxgene-lamin
tweet: TBD
linkedin: TBD
---

---

[CZ CELLxGENE](https://cellxgene.cziscience.com/) hosts one of the largest standardized collections of single-cell RNA-seq datasets.
Its [Census](https://chanzuckerberg.github.io/cellxgene-census/) provides efficient access via TileDB-SOMA, and individual datasets are available as `.h5ad` files on S3.
However, programmatically querying *across* datasets by arbitrary metadata combinations — cell types, tissues, diseases, assays, collections, donor information — has required writing custom data wrangling code.

We maintain [`laminlabs/cellxgene`](https://lamin.ai/laminlabs/cellxgene), a public LaminDB instance that mirrors CELLxGENE data with curated, queryable metadata.
It enables you to:

1. **Query across datasets** using biological ontologies: filter `.h5ad` artifacts by cell type, tissue, disease, assay, organism, and more — all with a single API call.
2. **Access individual datasets**: cache, load into memory, or stream array slices without downloading everything.
3. **Query the concatenated Census**: slice the `tiledbsoma` store by metadata filters, directly from LaminDB.
4. **Train ML models** on collections using `MappedCollection` or `tiledbsoma` PyTorch dataloaders.
5. **Integrate with in-house data**: transfer CELLxGENE data into your own LaminDB instance and combine it with private datasets.

Here, we explain how we curate and maintain the instance, and how you can use it.

## Connecting to the instance

Getting started takes two lines:

```python
import lamindb as ln

db = ln.DB("laminlabs/cellxgene")
```

The `db` object gives you access to all registries: artifacts, collections, genes, cell types, tissues, diseases, and more.

## Querying across datasets

Every individual `.h5ad` file from CELLxGENE is registered as an `artifact` in the instance.
Each artifact is annotated with ontology-backed metadata parsed from its `obs` fields — cell types, tissues, diseases, assays, developmental stages, ethnicities, and organisms — all linked to [Bionty](https://lamin.ai/docs/bionty) registries.

This means you can query across all ~1,000 datasets with expressive filters:

```python
cell_types = db.bionty.CellType.lookup()
users = db.User.lookup()

db.Artifact.filter(
    suffix=".h5ad",
    description__contains="immune",
    size__gt=1e9,
    cell_types__name__in=["B cell", "T cell"],
    created_by=users.sunnyosun,
).order_by("created_at").to_dataframe(
    include=["cell_types__name", "created_by__handle"]
)
```

Under the hood, `cell_types__name__in` performs a join between the `Artifact` and `bionty.CellType` registries, matching on `CellType.name`.
This is the same Django ORM-style syntax used throughout LaminDB, which means queries compose naturally across any metadata dimension.

## How we curate the instance

Each CELLxGENE Census LTS release (published every six months) triggers an update of `laminlabs/cellxgene`.
The curation process:

1. **Register artifacts**: Each `.h5ad` file from the Census release is registered as an `artifact`, pointing to its S3 location on `s3://cellxgene-data-public`. No data is copied — LaminDB references the original storage.

2. **Parse and link metadata**: For each artifact, we parse the `obs` fields and link them to ontology-backed registries. Cell types are linked to the [Cell Ontology](http://obophenotype.github.io/cell-ontology/), tissues to [Uberon](http://obophenotype.github.io/uberon/), diseases to [Mondo](https://mondo.monarchinitiative.org/), assays to [EFO](https://www.ebi.ac.uk/efo/), and so on. This is what enables cross-dataset queries.

3. **Register collections**: CELLxGENE organizes datasets into collections (typically corresponding to a publication). We mirror this structure: each CELLxGENE collection maps to a `Collection` in LaminDB, grouping the relevant artifacts. Collections are versioned across Census releases.

4. **Register the Census store**: The concatenated `tiledbsoma` array is registered as a single artifact, enabling direct queries via `artifact.open()`.

The scripts that perform this curation live in [cellxgene-lamin](https://github.com/laminlabs/cellxgene-lamin), and the schema definition is part of [lamindb](https://github.com/laminlabs/lamindb/blob/main/lamindb/examples/cellxgene/_cellxgene.py).

## Inspecting a dataset

You can inspect any artifact's full metadata context:

```python
artifact = db.Artifact.get(description="Mature kidney dataset: immune")
artifact.describe()
```

This shows the dataset features (20 `obs` columns, 2 `var` columns), linked ontology labels (cell types, tissues, diseases, developmental stages), external features (e.g., number of donors), storage path, and provenance (who created it, which script, when).

## Accessing data

Three ways to access the underlying array data:

```python
# 1. Cache on disk and return local path
path = artifact.cache()

# 2. Cache and load into memory
adata = artifact.load()

# 3. Stream via a cloud-backed accessor
with artifact.open() as adata_backed:
    slice = adata_backed[adata_backed.obs.cell_type == "B cell"]
    adata_slice = slice.to_memory()
```

All three run faster from within AWS `us-west-2`, where the data is hosted.

## Querying within a collection

You can filter artifacts within a specific collection by combining metadata:

```python
organisms = db.bionty.Organism.lookup()
tissues = db.bionty.Tissue.lookup()
experimental_factors = db.bionty.ExperimentalFactor.lookup()
suspension_types = db.ULabel.filter(type__name="SuspensionType").lookup()

census = db.Collection.get(key="cellxgene-census", version="2025-01-30")
census.artifacts.filter(
    organisms=organisms.human,
    cell_types__in=[cell_types.dendritic_cell, cell_types.neutrophil],
    tissues=tissues.kidney,
    ulabels=suspension_types.cell,
    experimental_factors=experimental_factors.ln_10x_3_v2,
).order_by("size").to_dataframe()
```

## Slicing the concatenated Census

For queries that span all datasets, you can slice the TileDB-SOMA store directly:

```python
features = db.Feature.lookup(return_field="name")
assays = db.bionty.ExperimentalFactor.lookup(return_field="name")

census_artifact = db.Artifact.get(key="cell-census/2025-01-30/soma")

with census_artifact.open() as store:
    cell_metadata = (
        store["census_data"]["homo_sapiens"]
        .obs.read(
            value_filter=(
                f'{features.tissue} == "brain"'
                f' and {features.cell_type} in ["microglial cell", "neuron"]'
                f' and {features.suspension_type} == "cell"'
                f' and {features.assay} == "{assays.ln_10x_3_v3}"'
            )
        )
        .concat()
        .to_pandas()
    )
```

## Training ML models

### On a collection of `.h5ad` files

`Collection.mapped()` creates a map-style PyTorch dataset that virtually concatenates the collection's artifacts.
This supports weighted random sampling and scales across multiple GPUs (see our [array loader benchmarks](https://lamin.ai/blog/arrayloader-benchmarks)):

```python
from torch.utils.data import DataLoader

census_collection = db.Collection.get(key="cellxgene-census", version="2025-01-30")
dataset = census_collection.mapped(obs_keys=[features.cell_type], join="outer")
dataloader = DataLoader(dataset, batch_size=128, shuffle=True)

for batch in dataloader:
    pass

dataset.close()
```

### On the concatenated `tiledbsoma` store

```python
import cellxgene_census.experimental.ml as census_ml
from tiledbsoma import AxisQuery

store = census_artifact.open()
experiment = store["census_data"]["homo_sapiens"]

experiment_datapipe = census_ml.ExperimentDataPipe(
    experiment,
    measurement_name="RNA",
    X_name="raw",
    obs_query=AxisQuery(value_filter=value_filter),
    obs_column_names=[features.cell_type],
    batch_size=128,
    shuffle=True,
    soma_chunk_size=10000,
)
dataloader = census_ml.experiment_dataloader(experiment_datapipe)

for batch in dataloader:
    pass

store.close()
```

## Curating your own data against the CELLxGENE schema

If you want to contribute data to CELLxGENE or simply ensure your datasets follow the same schema, you can validate and annotate your `AnnData` objects against the `laminlabs/cellxgene` registries.
See the [curation guide](https://docs.lamin.ai/cellxgene-curate) for details.

## Integrating with in-house data

A key advantage of the LaminDB instance over querying CELLxGENE directly is composability with private data.
You can [transfer](https://docs.lamin.ai/transfer) any artifact from `laminlabs/cellxgene` into your own instance without copying data, and then query across both public and private datasets using the same API.

## Outlook

We update `laminlabs/cellxgene` with each Census LTS release.
Going forward, we plan to extend the instance with spatial transcriptomics datasets as they become available through Census.

## Code & data availability

All code used in this blog post is free & open-source.

- CELLxGENE registration utility code: [github.com/laminlabs/cellxgene-lamin](https://github.com/laminlabs/cellxgene-lamin)
- CELLxGENE LaminDB schema code: [github.com/laminlabs/lamindb](https://github.com/laminlabs/lamindb/blob/main/lamindb/examples/cellxgene/_cellxgene.py)
- The public instance: [lamin.ai/laminlabs/cellxgene](https://lamin.ai/laminlabs/cellxgene)
- Documentation: [docs.lamin.ai/cellxgene](https://docs.lamin.ai/cellxgene)

## Author contributions

`*` These authors contributed equally.

Sunny conceptualized and implemented the initial versions of the CELLxGENE instance.
Lukas refined the implementation and updated the CELLxGENE instance to more recent versions.
Alex supervised the work.

## Citation

```
Sun S, Heumos L & Wolf A (2026). A programmatically queryable CELLxGENE LaminDB instance. Lamin Blog.
https://blog.lamin.ai/cellxgene-lamindb
```