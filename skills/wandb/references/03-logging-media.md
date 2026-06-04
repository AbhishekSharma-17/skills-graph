# Logging Media

> Source: [docs.wandb.ai/models/track/log/media](https://docs.wandb.ai/models/track/log/media/) | wandb 0.27.1

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Images](#images)
- [Image Overlays](#image-overlays)
- [Audio](#audio)
- [Video](#video)
- [3D Objects](#3d-objects)
- [Molecules](#molecules)
- [HTML](#html)
- [Histograms](#histograms)
- [Plotly and Matplotlib](#plotly-and-matplotlib)
- [Performance Tips](#performance-tips)

## Overview

W&B supports logging rich media types beyond scalar metrics. All media types are subclasses of `wandb.data_types` and are passed to `run.log()` like any other value.

```bash
pip install wandb[media]
```

## Installation

Media logging requires additional dependencies:

```bash
pip install wandb[media]
```

This installs Pillow (images), soundfile (audio), moviepy + ffmpeg (video), and related libraries.

## Images

### From NumPy Arrays

```python
import numpy as np
import wandb

with wandb.init(project="media-demo") as run:
    # Single image (H, W, C) — uint8 or float [0,1]
    img_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    run.log({"example": wandb.Image(img_array, caption="Random noise")})

    # Batch of images
    images = [wandb.Image(arr, caption=f"Sample {i}") for i, arr in enumerate(batch)]
    run.log({"predictions": images})
```

### From PIL Images

```python
from PIL import Image

pil_img = Image.fromarray(array)
if pil_img.mode != "RGB":
    pil_img = pil_img.convert("RGB")
run.log({"pil_example": wandb.Image(pil_img, caption="From PIL")})
```

### From File Paths

```python
run.log({"photo": wandb.Image("path/to/image.jpg")})
```

### From PyTorch Tensors

```python
# torchvision makes_grid -> numpy -> wandb.Image
from torchvision.utils import make_grid
grid = make_grid(tensor_batch, nrow=8)
run.log({"grid": wandb.Image(grid.permute(1, 2, 0).numpy())})
```

## Image Overlays

### Segmentation Masks

```python
mask_data = np.array([[1, 2, 2, ...], ...])  # H x W, integer class IDs
class_labels = {1: "tree", 2: "car", 3: "road"}

masked_img = wandb.Image(
    image,
    masks={
        "predictions": {
            "mask_data": mask_data,
            "class_labels": class_labels,
        },
        "ground_truth": {
            "mask_data": gt_mask,
            "class_labels": class_labels,
        },
    },
)
run.log({"segmentation": masked_img})
```

### Bounding Boxes

```python
class_labels = {1: "car", 2: "pedestrian", 3: "bicycle"}

box_img = wandb.Image(
    image,
    boxes={
        "predictions": {
            "box_data": [
                {
                    "position": {
                        "minX": 0.1, "maxX": 0.4,
                        "minY": 0.2, "maxY": 0.6,
                    },
                    "class_id": 1,
                    "box_caption": "car",
                    "scores": {"confidence": 0.95},
                },
            ],
            "class_labels": class_labels,
        },
    },
)
run.log({"detections": box_img})
```

Position formats:
- **Min/max**: `{"minX", "maxX", "minY", "maxY"}` — normalized [0, 1]
- **Center**: `{"middle": [x, y], "width": w, "height": h}` — normalized [0, 1]

## Audio

```python
# From NumPy array
audio_array = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 16000))
run.log({"tone": wandb.Audio(audio_array, sample_rate=16000, caption="440Hz sine")})

# From file
run.log({"speech": wandb.Audio("recording.wav", caption="Sample utterance")})

# Batch
clips = [wandb.Audio(arr, sample_rate=sr, caption=f"Clip {i}") for i, arr in enumerate(audio_batch)]
run.log({"audio_samples": clips})
```

Limit: maximum 100 audio clips per step.

## Video

```python
# From NumPy array — shape: (T, C, H, W) or (T, H, W, C)
video_array = np.random.randint(0, 255, (30, 3, 64, 64), dtype=np.uint8)
run.log({"video": wandb.Video(video_array, fps=10, format="mp4")})

# From file
run.log({"demo": wandb.Video("output.mp4", fps=30, format="mp4")})
```

Supported formats: `gif`, `mp4`, `webm`, `ogg`. Requires `ffmpeg` and `moviepy` for NumPy arrays.

## 3D Objects

### Point Clouds

```python
# (N, 3) — x, y, z
points = np.random.randn(1000, 3).astype(np.float32)
run.log({"cloud": wandb.Object3D(points)})

# (N, 6) — x, y, z, r, g, b (RGB: 0-255)
colored_points = np.column_stack([points, np.random.randint(0, 255, (1000, 3))])
run.log({"colored_cloud": wandb.Object3D(colored_points)})
```

Array formats:
- `(N, 3)` — positions only
- `(N, 4)` — positions + category (1–14)
- `(N, 6)` — positions + RGB color (0–255)

### Lidar with Bounding Boxes

```python
run.log({"lidar": wandb.Object3D.from_point_cloud(
    points=point_list,
    boxes=[{
        "corners": [[x, y, z] for _ in range(8)],
        "color": [0, 0, 255],
        "label": "car",
        "score": 0.95,
    }],
    vectors=[{
        "start": [0, 0, 0],
        "end": [1, 0, 0],
        "color": [255, 0, 0],
    }],
    point_cloud_type="lidar/beta",
)})
```

UI truncates at 300,000 points.

### From Files

```python
run.log({"mesh": wandb.Object3D.from_file("model.pts.json")})
```

## Molecules

```python
# From PDB file
run.log({"protein": wandb.Molecule("6lu7.pdb")})

# From RDKit SMILES
run.log({"drug": wandb.Molecule.from_smiles("CC(=O)Nc1ccc(O)cc1")})

# From RDKit Mol object
import rdkit.Chem as Chem
mol = Chem.MolFromSmiles("Oc1ccc(cc1)C=Cc1cc(O)cc(c1)O")
run.log({"resveratrol": wandb.Molecule.from_rdkit(mol)})
```

Supported file types: `pdb`, `pqr`, `mmcif`, `mcif`, `cif`, `sdf`, `sd`, `gro`, `mol2`, `mmtf`.

## HTML

```python
# From string
run.log({"chart": wandb.Html('<div id="chart">...</div>')})

# From file
run.log({"report": wandb.Html(open("report.html"))})

# Without default W&B styles
run.log({"raw": wandb.Html(open("custom.html"), inject=False)})
```

## Histograms

```python
# From data
gradients = model.fc.weight.grad.numpy()
run.log({"gradients": wandb.Histogram(gradients)})

# Custom bins
run.log({"activations": wandb.Histogram(activations, num_bins=128)})

# From pre-computed histogram (numpy format)
np_hist = np.histogram(data, bins=64, density=True, range=(0.0, 1.0))
run.log({"distribution": wandb.Histogram(np_hist)})
```

Default: 64 bins. Maximum: 512 bins.

## Plotly and Matplotlib

### Plotly

```python
import plotly.express as px

fig = px.scatter(df, x="epoch", y="accuracy", color="model")
run.log({"plotly_chart": wandb.Plotly(fig)})
```

### Matplotlib

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.plot(epochs, losses)
ax.set_xlabel("Epoch")
ax.set_ylabel("Loss")
run.log({"mpl_chart": wandb.Image(fig)})
plt.close(fig)
```

### Built-in Plot Types

```python
# ROC curve
run.log({"roc": wandb.plot.roc_curve(y_true, y_probas, labels=class_names)})

# Precision-recall
run.log({"pr": wandb.plot.pr_curve(y_true, y_probas, labels=class_names)})

# Confusion matrix
run.log({"confusion": wandb.plot.confusion_matrix(
    y_true=y_true, preds=y_pred, class_names=class_names
)})
```

## Performance Tips

1. **Limit images per step** — keep <50 images per `log()` call.
2. **Downsample before logging** — resize large images before wrapping in `wandb.Image()`.
3. **Log media periodically** — every N epochs, not every batch.
4. **Use tables for large media sets** — `wandb.Table` with media columns for structured browsing.
5. **Separate media and scalar logging** — call `run.log()` for metrics every step, media less often.

## Related

- Logging Metrics → `references/02-logging-metrics.md`
- Tables → `references/07-tables.md`
- Experiment Tracking → `references/01-experiment-tracking.md`
