# Chroma — Multimodal Embeddings

> Source: [docs.trychroma.com/docs/embeddings/multimodal](https://docs.trychroma.com/docs/embeddings/multimodal)

## Table of Contents

- [Overview](#overview)
- [Supported Modalities](#supported-modalities)
- [OpenCLIP Setup](#openclip-setup)
- [Adding Images](#adding-images)
- [Querying with Text](#querying-with-text)
- [Querying with Images](#querying-with-images)
- [Data Loaders](#data-loaders)
- [Cross-Modal Search](#cross-modal-search)
- [Common Pitfalls](#common-pitfalls)

## Overview

Chroma supports multimodal embeddings, allowing you to store and search across text and images in the same collection. This enables cross-modal retrieval — finding images with text queries and vice versa.

Multimodal support uses embedding functions that map different data types into a shared vector space (e.g., OpenCLIP maps both text and images into the same embedding space).

**Current status:** Multimodal support is available in **Python only**. TypeScript and Rust support is planned.

## Supported Modalities

| Modality | Embedding Function | Status |
|----------|-------------------|--------|
| Text | All embedding functions | Full support |
| Images | OpenCLIP, Roboflow | Python only |
| Audio | Planned | Not yet available |
| Video | Planned | Not yet available |

## OpenCLIP Setup

OpenCLIP is the built-in multimodal embedding function that processes both text and images into a unified embedding space.

```python
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction
from chromadb.utils.data_loaders import ImageLoader

embedding_function = OpenCLIPEmbeddingFunction()
data_loader = ImageLoader()
```

## Adding Images

Chroma stores image references as URIs rather than raw image data. The data loader retrieves and processes images when needed.

### Create a Multimodal Collection

```python
import chromadb

client = chromadb.Client()

embedding_function = OpenCLIPEmbeddingFunction()
data_loader = ImageLoader()

collection = client.create_collection(
    name="multimodal_collection",
    embedding_function=embedding_function,
    data_loader=data_loader,
)
```

### Add Images by URI

```python
collection.add(
    ids=["img1", "img2", "img3"],
    uris=[
        "/path/to/cat.jpg",
        "/path/to/dog.jpg",
        "/path/to/bird.jpg",
    ],
    metadatas=[
        {"label": "cat", "source": "photos"},
        {"label": "dog", "source": "photos"},
        {"label": "bird", "source": "photos"},
    ],
)
```

When URIs are provided, Chroma:
1. Uses the data loader to read the image files
2. Passes images through the embedding function
3. Stores the embeddings and URIs (not the raw images)

### Add Text Alongside Images

```python
collection.add(
    ids=["text1"],
    documents=["A fluffy orange cat sitting on a windowsill"],
    metadatas=[{"type": "description"}],
)
```

## Querying with Text

Search images using natural language descriptions.

```python
results = collection.query(
    query_texts=["a cute animal"],
    n_results=3,
    include=["uris", "distances", "metadatas", "data"],
)

print(results["uris"])       # Image paths
print(results["distances"])  # Similarity scores
```

## Querying with Images

Search using an image as the query.

```python
import numpy as np
from PIL import Image

query_image = np.array(Image.open("/path/to/query_image.jpg"))

results = collection.query(
    query_images=[query_image],
    n_results=5,
    include=["uris", "distances", "metadatas"],
)
```

## Data Loaders

Data loaders retrieve the original data from URIs when needed (e.g., when `include=["data"]` is requested in results).

### Built-in ImageLoader

Loads images from local filesystem paths.

```python
from chromadb.utils.data_loaders import ImageLoader

data_loader = ImageLoader()
```

### Include Data in Results

```python
results = collection.query(
    query_texts=["sunset landscape"],
    n_results=3,
    include=["uris", "data", "distances"],
)

# results["data"] contains the loaded image arrays
# This calls the data loader for each URI automatically
```

## Cross-Modal Search

The key capability of multimodal collections: search across different data types.

```python
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction
from chromadb.utils.data_loaders import ImageLoader

client = chromadb.Client()
ef = OpenCLIPEmbeddingFunction()
loader = ImageLoader()

collection = client.create_collection(
    name="cross_modal",
    embedding_function=ef,
    data_loader=loader,
)

# Add images
collection.add(
    ids=["img1", "img2"],
    uris=["/photos/beach.jpg", "/photos/mountain.jpg"],
    metadatas=[{"type": "image"}, {"type": "image"}],
)

# Add text descriptions
collection.add(
    ids=["text1", "text2"],
    documents=[
        "A beautiful sunset over the ocean",
        "Snow-capped peaks in winter",
    ],
    metadatas=[{"type": "text"}, {"type": "text"}],
)

# Text query finds both images and text
results = collection.query(
    query_texts=["nature scenery"],
    n_results=4,
)
# Returns both image URIs and text documents ranked by similarity

# Image query also finds both
query_img = np.array(Image.open("/photos/new_landscape.jpg"))
results = collection.query(
    query_images=[query_img],
    n_results=4,
)
```

## Common Pitfalls

1. **Python only** — Multimodal features are not available in TypeScript or Rust. Use Python for image-related workflows.

2. **URIs not URLs** — The `ImageLoader` reads from local filesystem paths, not HTTP URLs. Download images first if they are remote.

3. **One modality per update** — When updating a record, it supports only one modality at a time. Updating with a document overwrites any previous image data.

4. **OpenCLIP model size** — The OpenCLIP model is significantly larger than text-only models (~600MB+). Plan for download time and memory usage.

5. **include=["data"] triggers loading** — Including `"data"` in results causes the data loader to read every matching file from disk. For large result sets, this can be slow.

6. **Embedding space alignment** — Only use multimodal embedding functions (OpenCLIP) for cross-modal search. Standard text embedding functions cannot embed images.
