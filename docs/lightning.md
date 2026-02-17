---
title: "Tracking PyTorch Lightning checkpoints with LaminDB"
date: 2026-02-21
author: Zethson, falexwolf
orcid:
  Zethson: 0000-0002-8937-3457
  falexwolf: 0000-0002-8760-7838
affiliation:
  Zethson: Lamin Labs, Munich
  falexwolf: Lamin Labs, Munich
db: https://lamin.ai/laminlabs/lamindata
repo: https://github.com/laminlabs/lamindb
tweet: TBD
linkedin: TBD
---

---

When training deep learning models in biology, keeping track of model checkpoints alongside the datasets and code that produced them is essential for reproducibility.
Existing experiment trackers like Weights & Biases, MLflow, and others excel at logging metrics over time, but don't natively capture the full lineage of input data, output checkpoints, and source code in a single queryable system.

We built a [PyTorch Lightning](https://lightning.ai/docs/pytorch/stable/) integration for LaminDB that bridges this gap.
The `ll.Checkpoint` callback automatically registers every model checkpoint as a LaminDB artifact — annotated with training metrics, linked to input datasets, and traced back to the notebook or script that produced it.
It composes with W&B, MLflow, and other tracking frameworks rather than replacing them.

---

## The problem

A typical training run produces checkpoints that you want to:

1. **Query by metrics** — find the best checkpoint across runs by `val_loss`, `epoch`, etc.
2. **Trace to input data** — know which dataset version the model was trained on.
3. **Trace to source code** — know which script or notebook produced it.
4. **Share with collaborators** — make checkpoints discoverable and downloadable without sharing file paths.

W&B and MLflow handle (1) well.
LaminDB handles (2), (3), and (4).
The Lightning integration connects both worlds.

## The `ll.Checkpoint` callback

`lamindb.integrations.lightning` provides a `Checkpoint` callback that extends Lightning's `ModelCheckpoint`.
Drop it into any `Trainer`:

```python
import lightning as pl
import lamindb as ln
from lamindb.integrations import lightning as ll

# define metrics you want to track on each checkpoint artifact
metrics_to_annotate = ["train_loss", "val_loss", "current_epoch"]
for metric in metrics_to_annotate:
    dtype = int if metric == "current_epoch" else float
    ln.Feature(name=metric, dtype=dtype).save()
ll.save_lightning_features()

# track the notebook/script
ln.track(params={"hidden_size": 64, "batch_size": 128})

# create the callback
lamindb_callback = ll.Checkpoint(
    dirpath="checkpoints/",
    features={
        "artifact": {
            **{metric: None for metric in metrics_to_annotate}
        },  # auto-populated per checkpoint
    },
)

trainer = pl.Trainer(
    max_epochs=10,
    callbacks=[lamindb_callback],
)
trainer.fit(model, train_dataloaders=train_loader, val_dataloaders=val_loader)
```

After training, every checkpoint is a queryable `Artifact`:

```python
ln.Artifact.filter(
    is_best_model=True,
    suffix__endswith="ckpt",
).last().describe()
```

```
Artifact: checkpoints/epoch=9-step=30.ckpt
|   description: Lightning model checkpoint
├── uid: PEgDIsCnDOBUblbS            run: ZPPuSdc (train.py)
│   kind: model                      otype: None
├── Features
│   └── current_epoch              int          9
│       is_best_model              bool         True
│       train_loss                 float        0.042
│       val_loss                   float        0.051
└── Labels
    └── .projects                  Project      My training project
```

## Composing with W&B

The callback composes naturally with Weights & Biases.
Pass the W&B run ID as a run-level feature to keep both systems in sync:

```python
from lightning.pytorch.loggers import WandbLogger

wandb_logger = WandbLogger(project="my-project")

lamindb_callback = ll.Checkpoint(
    dirpath=f"checkpoints/{wandb_logger.experiment.id}",
    features={
        "run": {
            "wandb_run_id": wandb_logger.experiment.id,
            "wandb_run_name": wandb_logger.experiment.name,
        },
        "artifact": {
            **{metric: None for metric in metrics_to_annotate}
        },
    },
)

trainer = pl.Trainer(
    max_epochs=10,
    logger=wandb_logger,
    callbacks=[lamindb_callback],
)
```

W&B captures metrics curves.
LaminDB captures data lineage and makes checkpoints queryable across runs:

| Concern                            | W&B | LaminDB |
| ---------------------------------- | --- | ------- |
| Metric curves over training        | ✓   |         |
| Query checkpoints by metric values |     | ✓       |
| Input data lineage                 |     | ✓       |
| Source code tracing                |     | ✓       |
| Shareable artifact registry        |     | ✓       |

The same pattern works with MLflow — just pass `mlflow_run_id` and `mlflow_run_name` instead.
See the [MLflow guide](https://docs.lamin.ai/mlflow) for a full example.

## Run-level vs. artifact-level features

The `features` dict distinguishes between two scopes:

- **`"run"`**: Features annotated on the LaminDB `Run` object.
  Use this for things constant across a training run — experiment tracker IDs, hyperparameters not already tracked via `ln.track(params=...)`.
- **`"artifact"`**: Features annotated on each checkpoint `Artifact`.
  Values set to `None` are auto-populated from Lightning's logged metrics at checkpoint time.
  This is where per-checkpoint metrics like `train_loss` and `val_loss` go.

Run-level features are also auto-populated with trainer configuration like `max_epochs`, `precision`, `accumulate_grad_batches`, `logger_name`, and `logger_version`.

## Querying checkpoints

After a few training runs, you can query across all checkpoints:

```python
# best checkpoint across all runs
best = ln.Artifact.filter(is_best_model=True, suffix__endswith="ckpt").last()

# all checkpoints with val_loss below a threshold
good_models = ln.Artifact.filter(
    val_loss__lt=0.05,
    suffix__endswith="ckpt",
).to_dataframe()

# checkpoints from a specific W&B run
wandb_checkpoints = ln.Artifact.filter(
    run__features__wandb_run_id="abc123",
    suffix__endswith="ckpt",
).to_dataframe()
```

To reload a checkpoint:

```python
model = LitAutoEncoder.load_from_checkpoint(best.cache())
```

## Viewing lineage

Every checkpoint's full lineage — from input dataset to source code to output model — is available via:

```python
best.view_lineage()
```

![](https://lamin-site-assets.s3.us-east-1.amazonaws.com/.lamindb/oqbx2eNyNfbIsJtt0000.svg)

This renders a DAG showing the notebook/script, the input dataset (e.g., MNIST), and the output checkpoint, all linked through the LaminDB `Run`.

## Acknowledgements

We thank Joren Retel for very helpful discussions, implementation guidance, and code contributions.

## Code & data availability

- Lightning integration source: [github.com/laminlabs/lamindb](https://github.com/laminlabs/lamindb) (PR [#3115](https://github.com/laminlabs/lamindb/pull/3115))
- W&B example: [docs.lamin.ai/wandb](https://docs.lamin.ai/wandb)
- MLflow example: [docs.lamin.ai/mlflow](https://docs.lamin.ai/mlflow)
- MLOps overview: [docs.lamin.ai/mlops](https://docs.lamin.ai/mlops)

## Author contributions

Lukas designed and implemented the Lightning integration.
Alex supervised the work.

## Citation

```
Heumos L & Wolf A (2026). Tracking PyTorch Lightning checkpoints with LaminDB. Lamin Blog.
https://blog.lamin.ai/lightning
```
