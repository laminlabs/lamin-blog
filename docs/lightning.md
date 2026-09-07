---
title: "Managing artifacts, features, and ML experiments in a unified way"
date: 2026-05-20
author: Zethson, falexwolf, jorenretel
affiliation:
  Zethson: Lamin Labs, Munich
  falexwolf: Lamin Labs, Munich
  jorenretel: Pfizer, Berlin
---

When training deep learning models, keeping track of model checkpoints alongside the datasets and code that produced them is essential for reproducibility.
Existing experiment trackers like Weights & Biases, MLflow, and others excel at logging metrics over time, but don't natively capture the full lineage of input data, output checkpoints, and source code in a single queryable database.

We built a [PyTorch Lightning](https://lightning.ai/docs/pytorch/stable/) integration for LaminDB that bridges this gap.
The `ll.Checkpoint` callback automatically registers every model checkpoint as a LaminDB artifact — annotated with training metrics, linked to input datasets, and traced back to the notebook or script that produced it.
It composes with W&B, MLflow, and other tracking frameworks rather than replacing them.
The integration is event-driven: once Lamin persists an artifact, downstream systems can react through observer callbacks.

## The problem

A typical training run produces checkpoints that you want to:

1. **Query by metrics** — find the best checkpoint across runs by `val_loss`, `epoch`, etc.
2. **Trace to input data** — know which dataset version the model was trained on.
3. **Trace to source code** — know which script or notebook produced it.
4. **Share with collaborators** — make checkpoints discoverable and downloadable without sharing file paths.

W&B and MLflow handle (1) well.
LaminDB handles (2), (3), and (4).
The Lightning integration connects both worlds.

## How Lightning saves checkpoints today

Before showing the integration, it helps to recall what plain PyTorch Lightning already does.

Checkpointing is handled by the `ModelCheckpoint` callback.
You tell it how to name files (`filename`), which metric to watch (`monitor`), and how many of the best ones to keep (`save_top_k`).
Where the files actually land is usually inherited from the trainer's logger — its `save_dir`, run name, and version together form the checkpoint directory (when several loggers are configured, the first one decides).
During training it writes `.ckpt` files to disk and keeps the top-k around, deleting the rest as better checkpoints appear.

If you launch training through [`LightningCLI`](https://lightning.ai/docs/pytorch/stable/cli/lightning_cli.html), there is a second callback worth knowing: `SaveConfigCallback`.
It takes the fully resolved configuration of your run — every model, data, and trainer setting merged from your YAML files and command line — and writes it to a `config.yaml` next to your logs.
That file is what makes a run reproducible: it records exactly how the run was set up.

Both callbacks stop at the filesystem.
The checkpoints and the config end up as files on disk, but nothing links them to the dataset they were trained on or the code that produced them, and nothing makes them queryable afterwards.
That is the gap the LaminDB integration fills.

## The `ll.Checkpoint` callback

`lamindb.integrations.lightning` provides a `Checkpoint` callback that extends Lightning's `ModelCheckpoint`.
Drop it into any `Trainer`:

```python
import lightning as pl
import lamindb as ln
from lamindb.integrations import lightning as ll

# define custom metrics you want to track on each checkpoint artifact
metrics_to_annotate = ["train_loss", "val_loss", "current_epoch"]
for metric in metrics_to_annotate:
    dtype = int if metric == "current_epoch" else float
    ln.Feature(name=metric, dtype=dtype).save()

# save built-in lightning features (run + artifact scope)
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

By default, a checkpoint's artifact key mirrors the directory layout Lightning uses on disk, for example `lightning_logs/version_0/checkpoints/epoch=9-step=30.ckpt`, except for that the "version_0" part of
that path is replaced by the globally unique Lamin run UID (`run_uid_is_version=True`, the default).

We do this to prevent key clashes. On a single, long-lived machine, Lightning's logger auto-increments the version directory each run — `version_0`, `version_1`, and so on — so runs wouldn't overwrite one another.
But on a different machine or a fresh container the counter resets to `version_0`, so unrelated runs there produce the same path and the second silently overwrites the first.

The checkpoint then lands under something like `lightning_logs/<run-uid>/checkpoints/epoch=9-step=30.ckpt`, giving every run its own namespace — no collisions, even across machines or containers.

With Lamin features such as `is_last_model` and `model_rank` (described below), you can already query for the latest or best checkpoint directly, so you usually don't need Lightning's separate `save_last` filename convention.

If you launch training through `LightningCLI`, pair the checkpoint callback with `ll.SaveConfigCallback`.
Where plain Lightning's `SaveConfigCallback` only writes `config.yaml` to disk, the LaminDB version *also* uploads that config as an artifact next to the checkpoints, so the run's configuration becomes part of the same queryable lineage:

```python
from lightning.pytorch.cli import LightningCLI
from lamindb.integrations import lightning as ll

cli = LightningCLI(
    MyModel,
    MyDataModule,
    trainer_defaults={
        "callbacks": [ll.Checkpoint(monitor="val_loss", save_top_k=3)],
    },
    save_config_callback=ll.SaveConfigCallback,
)
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

## Composing with metric tracking dashboards

The callback composes naturally with Weights & Biases.
Pass the W&B run ID as a run-level feature to keep both systems in sync:

```python
from lightning.pytorch.loggers import WandbLogger

wandb_logger = WandbLogger(project="my-project")

# no dirpath needed: the WandbLogger drives the artifact key and the Lamin run
# UID keeps runs from colliding. The W&B run is linked as a queryable feature.
lamindb_callback = ll.Checkpoint(
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

## Where do checkpoints go from here? They're not a dead end

Saving a checkpoint to LaminDB already buys you lineage, features, and a queryable registry.
For many teams, though, that is not the finish line.
You may want to take the LaminDB artifact key — or the S3 prefix where the checkpoint physically lives — and hand it to another system: a model registry, a deployment pipeline, or an internal dashboard your team already relies on.

The integration supports this without subclassing or reaching into the callback's internals.
You register a small object with the callback, and it gets notified whenever a checkpoint artifact is saved or removed.
The callback remains responsible for persisting to LaminDB; your object reacts to those events and does whatever the rest of your stack needs.

Two events are emitted:

- **A checkpoint was saved.** After LaminDB persists the checkpoint, the observer receives an `ArtifactSavedEvent` carrying the artifact's LaminDB `key`, its `storage_uri` (for example the `s3://...` location), the `kind` of artifact, and the `trainer`. This is where you register the model downstream.
- **A checkpoint was removed.** When Lightning evicts a checkpoint that dropped out of the top-k, the observer receives an `ArtifactRemovedEvent`, so you can remove the corresponding entry downstream.

An observer is any object implementing `on_artifact_saved` and `on_artifact_removed`.
Here is a minimal one that forwards every saved checkpoint to a model registry:

```python
from lamindb.integrations.lightning import (
    ArtifactObserver,
    ArtifactRemovedEvent,
    ArtifactSavedEvent,
)


class ModelRegistryObserver(ArtifactObserver):
    """Register each LaminDB checkpoint in a downstream model registry."""

    def on_artifact_saved(self, event: ArtifactSavedEvent) -> None:
        if event.kind != "checkpoint":
            return
        # event.key         -> the LaminDB artifact key
        # event.storage_uri -> where the file physically lives, e.g. s3://...
        my_registry.register(
            name=event.key,
            uri=event.storage_uri,
            step=event.trainer.global_step,
        )

    def on_artifact_removed(self, event: ArtifactRemovedEvent) -> None:
        if event.kind != "checkpoint":
            return
        my_registry.deregister(name=event.key)
```

You register an observer in one of two ways.
Pass it when you build the callback:

```python
checkpoint = ll.Checkpoint(
    monitor="val_loss",
    save_top_k=3,
    artifact_observers=[ModelRegistryObserver()],
)
```

or attach it later with `add_artifact_observer`:

```python
checkpoint = ll.Checkpoint(monitor="val_loss", save_top_k=3)
checkpoint.add_artifact_observer(ModelRegistryObserver())
```

Wiring it into a full `LightningCLI` run is unchanged — the observer rides along inside the checkpoint callback:

```python
from lightning.pytorch.cli import LightningCLI
from lamindb.integrations import lightning as ll

cli = LightningCLI(
    MyModel,
    MyDataModule,
    trainer_defaults={
        "callbacks": [
            ll.Checkpoint(
                monitor="val_loss",
                save_top_k=3,
                artifact_observers=[ModelRegistryObserver()],
            )
        ],
    },
    save_config_callback=ll.SaveConfigCallback,
)
```

LaminDB stays the source of truth for persistence and lineage, while your observer decides what the rest of your stack does with each checkpoint.
Adding another downstream system is just another observer — no forking, no overriding.

## Run-level vs. artifact-level features

The `features` dict distinguishes between two scopes:

- **`"run"`**: Features annotated on the LaminDB `Run` object.
  Use this for things constant across a training run — experiment tracker IDs, hyperparameters not already tracked via `ln.track(params=...)`.
- **`"artifact"`**: Features annotated on each checkpoint `Artifact`.
  Values set to `None` are auto-populated from Lightning metrics/trainer attributes at checkpoint time.
  This is where per-checkpoint metrics like `train_loss` and `val_loss` go.

When `ll.save_lightning_features()` has been called, the callback auto-tracks built-in features if they exist in your instance:

- Run-level: `logger_name`, `logger_version`, `max_epochs`, `max_steps`, `precision`, `accumulate_grad_batches`, `gradient_clip_val`, `monitor`, `mode`
- Artifact-level: `is_best_model`, `is_last_model`, `score`, `model_rank`, `save_weights_only`, `monitor`, `mode`

Model and datamodule hyperparameters can also be auto-annotated when matching Lamin features exist.

## Keeping `is_best_model`, `is_last_model`, and `model_rank` current

Lightning's `ModelCheckpoint` keeps its ranking in memory: as training progresses it tracks which checkpoints are the best and quietly deletes files that drop out of the top-k.
The callback mirrors that behavior in LaminDB. When Lightning evicts a checkpoint, the callback deletes the corresponding artifact — file and registry entry — so the Lamin registry stays in sync with the `save_top_k` set on disk rather than accumulating every checkpoint ever written.
That raises a question: as checkpoints come and go, how do features like `is_best_model` or `model_rank` stay truthful when a later checkpoint turns out to be better?

The answer is that, on each save, the callback doesn't just annotate the new checkpoint — it revisits the other checkpoints still saved for this run and rewrites their flags.
All checkpoints from a single run share a common **key prefix** (the run-scoped prefix described earlier), so the callback can find exactly the right set of artifacts to reconcile and won't touch checkpoints from other runs.

Concretely, every time a checkpoint is saved the callback:

1. **Clears the old "last" flag.** It finds the artifact(s) currently marked `is_last_model=True` under this run's prefix and flips them to `False`. The checkpoint being saved right now is then annotated with `is_last_model=True`. Only one checkpoint per run is ever the latest.
2. **Demotes the previous best, if dethroned.** If Lightning reports that the new checkpoint is the best so far, the callback finds the artifact currently marked `is_best_model=True` and flips it to `False`, then marks the new checkpoint `is_best_model=True`. If the new checkpoint is *not* the best, the existing best is left untouched.
3. **Re-ranks the whole set.** After the new artifact is saved, the callback queries all checkpoint artifacts under the run's prefix, sorts them by their `score` (respecting `mode="min"` or `mode="max"`), and rewrites `model_rank` on each one so the ranking reflects the current set (`model_rank=0` is the best). A checkpoint that was rank 1 yesterday becomes rank 2 the moment a better one arrives.

Updating a flag means replacing the stored value on the existing artifact — the old value is removed and the new one added — so each artifact always carries a single, correct value rather than a history of stale flags.

The practical payoff is that your queries never go stale.
`ln.Artifact.filter(is_best_model=True, ...)` always returns the current best, `is_last_model=True` always returns the most recent checkpoint, and `model_rank` always reflects the live ordering — without you having to recompute anything.

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

<div style="text-align: center">
<img width="800" src="https://lamin-site-assets.s3.us-east-1.amazonaws.com/.lamindb/oqbx2eNyNfbIsJtt0000.svg">
</div>

This renders a DAG showing the notebook/script, the input dataset (e.g., MNIST), and the output checkpoint, all linked through the LaminDB `Run`.

## Code & data availability

- Lightning integration source: [github.com/laminlabs/lamindb](https://github.com/laminlabs/lamindb) (PR [#3115](https://github.com/laminlabs/lamindb/pull/3115))
- W&B example: [docs.lamin.ai/wandb](https://docs.lamin.ai/wandb)
- MLflow example: [docs.lamin.ai/mlflow](https://docs.lamin.ai/mlflow)
- MLOps overview: [docs.lamin.ai/mlops](https://docs.lamin.ai/mlops)

## Author contributions

Lukas designed & implemented the initial version of the Lightning integration.
Alex contributed design decisions and code refactoring.
Joren designed & implemented a production-ready version of the Lightning integration.

Pull requests:

- 🚸 Optimize DB interactions in `lightning` integration [PR](https://github.com/laminlabs/lamindb/pull/3577) [@falexwolf](https://github.com/falexwolf)
- 🐛 Fix feature collisions in lightning integration [PR](https://github.com/laminlabs/lamindb/pull/3576) [@falexwolf](https://github.com/falexwolf)
- 🚸 Overhaul the pytorch `lightning` integration [PR](https://github.com/laminlabs/lamindb/pull/3425) [@Zethson](https://github.com/Zethson) [@jorenretel](https://github.com/jorenretel)
- ✨ Add pytorch `lightning` integration with a `Callback` class [PR](https://github.com/laminlabs/lamindb/pull/3115) [PR Guide](https://github.com/laminlabs/lamin-mlops/pull/30) [@Zethson](https://github.com/Zethson)

## Citation

```
Heumos L, Wolf A & Joren R (2026). Tracking PyTorch Lightning checkpoints with LaminDB. Lamin Blog.
https://blog.lamin.ai/lightning
```
