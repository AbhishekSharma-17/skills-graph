# Weaviate — Model Provider Integrations

> Source: [docs.weaviate.io](https://docs.weaviate.io/weaviate/model-providers) | Version: v1.37

## Table of Contents
- [Overview](#overview)
- [Provider Capabilities](#provider-capabilities)
- [API Key Configuration](#api-key-configuration)
- [OpenAI](#openai)
- [Cohere](#cohere)
- [Google (Vertex AI / Gemini)](#google-vertex-ai--gemini)
- [Anthropic](#anthropic)
- [AWS Bedrock](#aws-bedrock)
- [Ollama (Local)](#ollama-local)
- [Hugging Face](#hugging-face)
- [Other Providers](#other-providers)
- [Vectorizer Property Control](#vectorizer-property-control)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

Weaviate integrates with model providers for three capabilities:
- **Embedding (Vectorizer)**: Convert text/images to vector embeddings
- **Generative**: Generate text responses for RAG queries
- **Reranking**: Re-score search results for better precision

When configured, Weaviate automatically vectorizes data on insert and queries — no manual embedding pipeline needed.

## Provider Capabilities

| Provider | Embedding | Generative | Reranking |
|----------|-----------|------------|-----------|
| OpenAI | text2vec-openai | generative-openai | — |
| Azure OpenAI | text2vec-openai (Azure) | generative-openai (Azure) | — |
| Cohere | text2vec-cohere | generative-cohere | reranker-cohere |
| Google | text2vec-google, multi2vec-google | generative-google | — |
| Anthropic | — | generative-anthropic | — |
| AWS Bedrock | text2vec-aws | generative-aws | — |
| Mistral | text2vec-mistral | generative-mistral | — |
| Ollama | text2vec-ollama | generative-ollama | — |
| Hugging Face | text2vec-huggingface | — | reranker-transformers |
| Voyage AI | text2vec-voyageai | — | reranker-voyageai |
| Jina AI | text2vec-jinaai | — | reranker-jinaai |
| NVIDIA | text2vec-nvidia, multi2vec-nvidia | generative-nvidia | reranker-nvidia |
| Contextual AI | — | generative-contextual | reranker-contextual |
| Weaviate | text2vec-weaviate | — | — |

## API Key Configuration

Pass model provider API keys in the client connection headers:

### Python

```python
import weaviate
from weaviate.classes.init import Auth

client = weaviate.connect_to_weaviate_cloud(
    cluster_url="https://your-cluster.weaviate.network",
    auth_credentials=Auth.api_key("your-weaviate-key"),
    headers={
        "X-OpenAI-Api-Key": "sk-...",
        "X-Cohere-Api-Key": "...",
        "X-Google-Api-Key": "...",
        "X-Anthropic-Api-Key": "...",
        "X-AWS-Access-Key": "...",
        "X-AWS-Secret-Key": "...",
    },
)
```

### TypeScript

```typescript
const client = await weaviate.connectToWeaviateCloud(
  'https://your-cluster.weaviate.network',
  {
    authCredentials: new weaviate.ApiKey('your-weaviate-key'),
    headers: {
      'X-OpenAI-Api-Key': 'sk-...',
      'X-Cohere-Api-Key': '...',
    },
  }
);
```

For Docker deployments, set keys as environment variables or pass via headers.

## OpenAI

### Embedding

```python
from weaviate.classes.config import Configure

client.collections.create(
    "Article",
    vector_config=Configure.Vectors.text2vec_openai(
        model="text-embedding-3-small",  # or text-embedding-3-large, text-embedding-ada-002
        dimensions=1536,
    ),
    properties=[...],
)
```

### Generative

```python
client.collections.create(
    "Article",
    vector_config=Configure.Vectors.text2vec_openai(),
    generative_config=Configure.Generative.openai(
        model="gpt-4o",
        temperature=0.7,
        max_tokens=1000,
    ),
    properties=[...],
)
```

## Cohere

### Embedding + Reranking

```python
client.collections.create(
    "Article",
    vector_config=Configure.Vectors.text2vec_cohere(
        model="embed-english-v3.0",  # or embed-multilingual-v3.0
    ),
    reranker_config=Configure.Reranker.cohere(
        model="rerank-english-v3.0",
    ),
    generative_config=Configure.Generative.cohere(
        model="command-r-plus",
    ),
    properties=[...],
)
```

## Google (Vertex AI / Gemini)

### Embedding + Generative

```python
client.collections.create(
    "Article",
    vector_config=Configure.Vectors.text2vec_google(
        model="text-embedding-004",
    ),
    generative_config=Configure.Generative.google(
        model="gemini-1.5-pro",
    ),
    properties=[...],
)
```

### Multimodal Embedding

```python
Configure.Vectors.multi2vec_google(
    image_fields=["image"],
    text_fields=["description"],
)
```

## Anthropic

Generative only (no embedding model):

```python
client.collections.create(
    "Article",
    vector_config=Configure.Vectors.text2vec_openai(),  # Use another provider for embedding
    generative_config=Configure.Generative.anthropic(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
    ),
    properties=[...],
)
```

## AWS Bedrock

```python
client.collections.create(
    "Article",
    vector_config=Configure.Vectors.text2vec_aws(
        model="amazon.titan-embed-text-v2:0",
        region="us-east-1",
    ),
    generative_config=Configure.Generative.aws(
        model="anthropic.claude-3-sonnet-20240229-v1:0",
        region="us-east-1",
    ),
    properties=[...],
)
```

## Ollama (Local)

Run embeddings and generation locally with Ollama:

```python
client.collections.create(
    "Article",
    vector_config=Configure.Vectors.text2vec_ollama(
        model="nomic-embed-text",
        api_endpoint="http://host.docker.internal:11434",
    ),
    generative_config=Configure.Generative.ollama(
        model="llama3",
        api_endpoint="http://host.docker.internal:11434",
    ),
    properties=[...],
)
```

When running Weaviate in Docker, use `host.docker.internal` to reach Ollama on the host machine.

## Hugging Face

### Embedding (API)

```python
Configure.Vectors.text2vec_huggingface(
    model="sentence-transformers/all-MiniLM-L6-v2",
)
```

### Self-Hosted Transformers

```python
Configure.Vectors.text2vec_transformers()  # Requires transformer container
```

## Other Providers

```python
# Mistral
Configure.Vectors.text2vec_mistral(model="mistral-embed")
Configure.Generative.mistral(model="mistral-large-latest")

# Voyage AI
Configure.Vectors.text2vec_voyageai(model="voyage-3")
Configure.Reranker.voyageai(model="rerank-2")

# Jina AI
Configure.Vectors.text2vec_jinaai(model="jina-embeddings-v3")
Configure.Reranker.jinaai(model="jina-reranker-v2-base-multilingual")

# NVIDIA
Configure.Vectors.text2vec_nvidia(model="nvidia/nv-embedqa-e5-v5")
Configure.Generative.nvidia()
Configure.Reranker.nvidia()

# Databricks
Configure.Vectors.text2vec_databricks(model="databricks-gte-large-en")
Configure.Generative.databricks(model="databricks-meta-llama-3-70b-instruct")

# FriendliAI (Generative only)
Configure.Generative.friendliai(model="meta-llama-3.1-8b-instruct")
```

## Vectorizer Property Control

Control which properties are vectorized:

```python
from weaviate.classes.config import Property, DataType

Property(
    name="title",
    data_type=DataType.TEXT,
    skip_vectorization=False,          # Include in vector (default)
    vectorize_property_name=True,      # Include property name in vector input
)

Property(
    name="internalId",
    data_type=DataType.TEXT,
    skip_vectorization=True,           # Exclude from vector
)
```

By default, all TEXT properties are vectorized. Set `skip_vectorization=True` for metadata fields (IDs, codes, dates) that shouldn't influence semantic search.

## Common Pitfalls

1. **Missing API key header**: Each provider has a specific header name (e.g., `X-OpenAI-Api-Key`, `X-Cohere-Api-Key`). Wrong header names silently fail.

2. **Mixing providers**: Using OpenAI for embedding but forgetting to add the generative config means RAG queries won't work. Each capability (embedding, generative, reranking) must be configured separately.

3. **Ollama networking in Docker**: When Weaviate runs in Docker, `localhost` inside the container doesn't reach the host. Use `host.docker.internal` for Ollama.

4. **Model deprecation**: Embedding models get deprecated (e.g., Ada-002 → text-embedding-3-small). Collections keep using the configured model, but you should migrate to avoid API deprecation.

5. **Vectorizing metadata fields**: If you don't exclude internal IDs, codes, or timestamps from vectorization, they pollute the semantic space. Set `skip_vectorization=True` on metadata properties.

## Related Topics

- Overview & Setup → `00-overview.md`
- RAG → `08-rag.md`
- Reranking → `09-reranking-aggregation.md`
- Vector Configuration → `02-vector-config.md`
