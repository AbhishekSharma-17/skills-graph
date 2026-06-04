# Tables

> Source: [docs.wandb.ai/models/tables](https://docs.wandb.ai/models/tables/) | wandb 0.27.1

## Table of Contents

- [Overview](#overview)
- [Creating Tables](#creating-tables)
- [Data Types](#data-types)
- [Adding Data](#adding-data)
- [Logging Tables](#logging-tables)
- [Media in Tables](#media-in-tables)
- [From DataFrames](#from-dataframes)
- [Querying and Filtering](#querying-and-filtering)
- [Comparing Tables Across Runs](#comparing-tables-across-runs)
- [Common Patterns](#common-patterns)

## Overview

`wandb.Table` is a two-dimensional data structure for logging, visualizing, and querying tabular data. Tables support primitive types, rich media (images, audio, video), and nested structures. They are ideal for logging model predictions, dataset samples, and evaluation results.

## Creating Tables

```python
import wandb

# From column names and data
table = wandb.Table(
    columns=["id", "image", "label", "prediction", "confidence"],
    data=[
        [1, wandb.Image("img1.jpg"), "cat", "cat", 0.95],
        [2, wandb.Image("img2.jpg"), "dog", "cat", 0.60],
    ],
)
```

### Empty Table with Schema

```python
table = wandb.Table(columns=["epoch", "loss", "accuracy"])
```

## Data Types

Tables support:

| Type | Example |
|------|---------|
| Strings | `"hello"` |
| Numbers (int/float) | `42`, `3.14` |
| Booleans | `True`, `False` |
| None | `None` |
| Lists | `[1, 2, 3]` |
| Dicts | `{"key": "value"}` |
| `wandb.Image` | Images with optional overlays |
| `wandb.Audio` | Audio clips |
| `wandb.Video` | Video clips |
| `wandb.Html` | Custom HTML content |
| `wandb.Object3D` | 3D visualizations |
| `wandb.Molecule` | Molecular structures |

## Adding Data

### Row by Row

```python
table = wandb.Table(columns=["step", "loss", "accuracy"])

for step in range(100):
    loss, acc = train_step()
    table.add_data(step, loss, acc)
```

### Column at a Time

```python
table = wandb.Table(columns=["id", "text"])
table.add_column("sentiment", sentiments_list)
table.add_column("confidence", confidences_list)
```

### Bulk from Lists

```python
data = [[i, losses[i], accs[i]] for i in range(len(losses))]
table = wandb.Table(columns=["step", "loss", "accuracy"], data=data)
```

## Logging Tables

```python
with wandb.init(project="table-demo") as run:
    # Log as a metric (appears in run workspace)
    run.log({"predictions": table})

    # Log as an artifact (versioned, reusable)
    artifact = wandb.Artifact("eval-results", type="result")
    artifact.add(table, name="predictions")
    run.log_artifact(artifact)
```

### Incremental Table Logging

```python
with wandb.init() as run:
    for epoch in range(10):
        table = wandb.Table(columns=["sample", "pred", "true"])
        for sample in eval_set:
            pred = model(sample.input)
            table.add_data(sample.id, pred, sample.label)
        run.log({f"eval_epoch_{epoch}": table})
```

## Media in Tables

### Images with Bounding Boxes

```python
table = wandb.Table(columns=["ID", "Image", "Detections"])

for img_id, img, boxes in zip(ids, images, all_boxes):
    box_img = wandb.Image(
        img,
        boxes={
            "predictions": {
                "box_data": [{
                    "position": {
                        "minX": b["x1"], "minY": b["y1"],
                        "maxX": b["x2"], "maxY": b["y2"],
                    },
                    "class_id": b["class_id"],
                    "domain": "pixel",
                } for b in boxes],
                "class_labels": class_labels,
            }
        },
    )
    table.add_data(img_id, box_img, len(boxes))

run.log({"object_detection": table})
```

### Mixed Media

```python
table = wandb.Table(columns=["Audio", "Transcription", "Confidence"])
for audio, text, conf in results:
    table.add_data(
        wandb.Audio(audio, sample_rate=16000),
        text,
        conf,
    )
run.log({"transcriptions": table})
```

## From DataFrames

```python
import pandas as pd

df = pd.DataFrame({
    "model": ["resnet50", "vgg16", "efficientnet"],
    "accuracy": [0.92, 0.88, 0.94],
    "params_M": [25.6, 138.4, 5.3],
    "latency_ms": [12.3, 45.1, 8.7],
})

table = wandb.Table(dataframe=df)
run.log({"model_comparison": table})
```

### Convert Table to DataFrame

```python
api = wandb.Api()
artifact = api.artifact("entity/project/eval-results:latest")
table = artifact.get("predictions")
df = table.get_dataframe()
```

## Querying and Filtering

Tables in the W&B UI support:
- **Sort** by any column (ascending/descending)
- **Filter** by column values (equals, contains, greater than, etc.)
- **Group** by categorical columns
- **Search** across text columns
- **Pin** rows for comparison

### Programmatic Querying

```python
api = wandb.Api()
run = api.run("entity/project/run_id")

# Get table from run history
for artifact in run.logged_artifacts():
    if artifact.type == "result":
        table = artifact.get("predictions")
        df = table.get_dataframe()
        
        # Filter in pandas
        errors = df[df["prediction"] != df["ground_truth"]]
        print(f"Error rate: {len(errors) / len(df):.2%}")
```

## Comparing Tables Across Runs

Log the same table name across runs to compare in the workspace:

```python
# Run 1: baseline model
with wandb.init(project="comparison", name="baseline") as run:
    table = wandb.Table(columns=["input", "output", "score"])
    for sample in test_set:
        table.add_data(sample.text, baseline(sample.text), score(sample))
    run.log({"results": table})

# Run 2: improved model
with wandb.init(project="comparison", name="improved") as run:
    table = wandb.Table(columns=["input", "output", "score"])
    for sample in test_set:
        table.add_data(sample.text, improved(sample.text), score(sample))
    run.log({"results": table})
```

The UI allows side-by-side comparison of tables from different runs.

## Common Patterns

### Text Classification Results

```python
table = wandb.Table(columns=["Text", "True Label", "Predicted", "Confidence", "Correct"])
for sample in test_set:
    pred, conf = model.predict(sample.text)
    table.add_data(sample.text, sample.label, pred, conf, pred == sample.label)
run.log({"classification_results": table})
```

### LLM Output Comparison

```python
table = wandb.Table(columns=["Prompt", "GPT-4o", "Claude", "Human Rating"])
for prompt in prompts:
    gpt_out = gpt4o(prompt)
    claude_out = claude(prompt)
    table.add_data(prompt, gpt_out, claude_out, None)
run.log({"llm_comparison": table})
```

## Related

- Logging Media → `references/03-logging-media.md`
- Artifacts → `references/05-artifacts.md`
- Weave Evaluations → `references/10-weave-evaluations.md`
