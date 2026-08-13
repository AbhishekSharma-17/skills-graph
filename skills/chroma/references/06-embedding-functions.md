# Chroma — Embedding Functions

> Source: [docs.trychroma.com/docs/embeddings](https://docs.trychroma.com/docs/embeddings)

## Table of Contents

- [Overview](#overview)
- [Default Embedding Function](#default-embedding-function)
- [OpenAI](#openai)
- [Cohere](#cohere)
- [Google Generative AI](#google-generative-ai)
- [Hugging Face](#hugging-face)
- [Sentence Transformers](#sentence-transformers)
- [Jina AI](#jina-ai)
- [Ollama](#ollama)
- [Together AI](#together-ai)
- [Custom Embedding Functions](#custom-embedding-functions)
- [TypeScript Embedding Functions](#typescript-embedding-functions)
- [Common Pitfalls](#common-pitfalls)

## Overview

Embedding functions convert text (or images) into numeric vectors that capture semantic meaning. Chroma uses these vectors for similarity search.

Embedding functions are:
- **Linked to collections** — activated during `add`, `update`, `upsert`, and `query`
- **Persisted in configuration** — the function type and model name are stored so clients can reconstruct the function
- **Callable independently** — useful for testing and debugging

**Language support:**
- **Python:** All functions included in `chromadb`
- **TypeScript:** Separate npm packages per provider (`@chroma-core/openai`, etc.)
- **Rust:** No built-in functions — provide embeddings directly via provider SDKs

## Default Embedding Function

If no embedding function is specified, Chroma uses **Sentence Transformers** with the `all-MiniLM-L6-v2` model. This runs locally and downloads model files on first use (~80MB).

```python
import chromadb

client = chromadb.Client()
# Uses all-MiniLM-L6-v2 automatically
collection = client.create_collection(name="default_embeddings")
collection.add(ids=["1"], documents=["hello world"])
```

## OpenAI

```python
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

ef = OpenAIEmbeddingFunction(
    model_name="text-embedding-3-small",
    # api_key auto-detected from OPENAI_API_KEY env var
)

collection = client.create_collection(
    name="openai_collection",
    embedding_function=ef,
)
```

**Parameters:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `model_name` | `"text-embedding-ada-002"` | OpenAI model name |
| `api_key` | From `OPENAI_API_KEY` | API key |
| `api_key_env_var` | `"OPENAI_API_KEY"` | Custom env var name |
| `organization_id` | — | OpenAI org ID |
| `api_base` | — | Custom API endpoint (for proxies) |

**Recommended models:**
- `text-embedding-3-small` — 1536 dims, good balance of cost/quality
- `text-embedding-3-large` — 3072 dims, highest quality
- `text-embedding-ada-002` — 1536 dims, legacy

## Cohere

```python
from chromadb.utils.embedding_functions import CohereEmbeddingFunction

ef = CohereEmbeddingFunction(
    model_name="embed-english-v3.0",
    # api_key auto-detected from COHERE_API_KEY env var
)

collection = client.create_collection(
    name="cohere_collection",
    embedding_function=ef,
)
```

## Google Generative AI

```python
from chromadb.utils.embedding_functions import GoogleGenerativeAiEmbeddingFunction

ef = GoogleGenerativeAiEmbeddingFunction(
    model_name="models/embedding-001",
    # api_key from GOOGLE_API_KEY env var
)
```

## Hugging Face

Use any model from the Hugging Face Hub via their Inference API.

```python
from chromadb.utils.embedding_functions import HuggingFaceEmbeddingFunction

ef = HuggingFaceEmbeddingFunction(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    # api_key from HUGGINGFACE_API_KEY env var
)
```

## Sentence Transformers

Runs models locally — no API key needed.

```python
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

ef = SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2",
)

# Generate embeddings directly (for testing)
embeddings = ef(["test document"])
print(len(embeddings[0]))  # 384 dimensions
```

**Popular models:**
- `all-MiniLM-L6-v2` — 384 dims, fast, default
- `all-mpnet-base-v2` — 768 dims, better quality
- `multi-qa-MiniLM-L6-cos-v1` — 384 dims, optimized for Q&A

## Jina AI

```python
from chromadb.utils.embedding_functions import JinaEmbeddingFunction

ef = JinaEmbeddingFunction(
    model_name="jina-embeddings-v3",
    # api_key from JINA_API_KEY env var
)
```

## Ollama

Use locally running Ollama models for embeddings.

```python
from chromadb.utils.embedding_functions import OllamaEmbeddingFunction

ef = OllamaEmbeddingFunction(
    model_name="nomic-embed-text",
    url="http://localhost:11434",
)
```

## Together AI

```python
from chromadb.utils.embedding_functions import TogetherAIEmbeddingFunction

ef = TogetherAIEmbeddingFunction(
    model_name="togethercomputer/m2-bert-80M-8k-retrieval",
    # api_key from TOGETHER_API_KEY env var
)
```

## Custom Embedding Functions

Implement the `EmbeddingFunction` interface for custom providers or local models.

```python
from chromadb import EmbeddingFunction, Embeddings, Documents

class MyEmbeddingFunction(EmbeddingFunction[Documents]):
    def __init__(self, model_name: str):
        self.model_name = model_name
    
    def __call__(self, input: Documents) -> Embeddings:
        # input is a list of strings
        # Return a list of embedding vectors
        embeddings = []
        for doc in input:
            # Your embedding logic here
            embedding = [0.0] * 384  # placeholder
            embeddings.append(embedding)
        return embeddings

ef = MyEmbeddingFunction(model_name="my-model")
collection = client.create_collection(
    name="custom_collection",
    embedding_function=ef,
)
```

**Required interface methods for persistent functions:**
- `__call__(input: Documents) -> Embeddings` — Generate embeddings
- `get_config()` — Return serializable configuration
- `from_config(config)` — Class method to reconstruct from config

## TypeScript Embedding Functions

TypeScript uses separate npm packages per provider:

```bash
npm install @chroma-core/openai
npm install @chroma-core/cohere
npm install @chroma-core/default-embed
```

```typescript
import { OpenAIEmbeddingFunction } from "@chroma-core/openai";

const ef = new OpenAIEmbeddingFunction({
  modelName: "text-embedding-3-small",
  apiKey: process.env.OPENAI_API_KEY,
});

const collection = await client.createCollection({
  name: "openai_collection",
  embeddingFunction: ef,
});
```

## Common Pitfalls

1. **Embedding function must match across operations** — The function used to `add` must be the same one used to `query`. Mixing different models produces meaningless similarity scores.

2. **Default model downloads on first use** — `all-MiniLM-L6-v2` is ~80MB and downloads automatically. In Docker or CI, pre-download the model or use an API-based function.

3. **API keys from environment** — Most functions auto-detect keys from standard env vars (`OPENAI_API_KEY`, `COHERE_API_KEY`, etc.). Use `api_key_env_var` for non-standard variable names.

4. **Thin client has no local functions** — `chromadb-client` does not include sentence-transformers or other local models. You must use API-based functions or provide pre-computed embeddings.

5. **Dimension consistency** — All records in a collection must have the same embedding dimension. Don't change models mid-collection. Create a new collection if you switch models.

6. **get_collection needs the function** — When using `client.get_collection()`, pass the `embedding_function` parameter. The collection configuration stores the function type but needs the instance to operate.
