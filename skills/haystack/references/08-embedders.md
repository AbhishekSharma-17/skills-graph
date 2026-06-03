# Haystack Embedders

> Source: [docs.haystack.deepset.ai/docs/embedders](https://docs.haystack.deepset.ai/docs/embedders) | haystack-ai 2.30.0

## Table of Contents

- [What Are Embedders](#what-are-embedders)
- [Text Embedders vs Document Embedders](#text-embedders-vs-document-embedders)
- [Supported Providers](#supported-providers)
- [OpenAI Embedders](#openai-embedders)
- [Sentence Transformers](#sentence-transformers)
- [Other Providers](#other-providers)
- [Indexing vs Querying](#indexing-vs-querying)
- [Choosing an Embedder](#choosing-an-embedder)
- [Common Pitfalls](#common-pitfalls)

## What Are Embedders

Embedders transform text into dense vector representations (embeddings) that capture semantic meaning. These vectors enable similarity-based search — documents with similar meaning have nearby vectors.

Two categories:
- **Text Embedders** — embed a single string (query)
- **Document Embedders** — embed multiple documents (batch indexing)

## Text Embedders vs Document Embedders

| Feature | TextEmbedder | DocumentEmbedder |
|---------|-------------|------------------|
| Input | Single `str` | `list[Document]` |
| Output | `list[float]` embedding | Documents with `embedding` field set |
| Used in | Query/retrieval pipelines | Indexing pipelines |
| Purpose | Embed the user's query | Embed documents for storage |

```python
# Text Embedder — for queries
text_embedder = OpenAITextEmbedder(model="text-embedding-3-small")
result = text_embedder.run(text="What is Haystack?")
embedding = result["embedding"]  # list[float], length 1536

# Document Embedder — for indexing
doc_embedder = OpenAIDocumentEmbedder(model="text-embedding-3-small")
result = doc_embedder.run(documents=[Document(content="Haystack is...")])
embedded_docs = result["documents"]  # Documents now have .embedding set
```

## Supported Providers

### Cloud Providers

| Provider | Package | TextEmbedder | DocumentEmbedder |
|----------|---------|-------------|------------------|
| OpenAI | built-in | `OpenAITextEmbedder` | `OpenAIDocumentEmbedder` |
| Azure OpenAI | built-in | `AzureOpenAITextEmbedder` | `AzureOpenAIDocumentEmbedder` |
| Cohere | `cohere-haystack` | `CohereTextEmbedder` | `CohereDocumentEmbedder` |
| Google | `google-genai-haystack` | `GoogleGenAITextEmbedder` | `GoogleGenAIDocumentEmbedder` |
| Amazon Bedrock | `amazon-bedrock-haystack` | `AmazonBedrockTextEmbedder` | `AmazonBedrockDocumentEmbedder` |
| Mistral | `mistral-haystack` | `MistralTextEmbedder` | `MistralDocumentEmbedder` |
| Jina | `jina-haystack` | `JinaTextEmbedder` | `JinaDocumentEmbedder` |
| NVIDIA | `nvidia-haystack` | `NvidiaTextEmbedder` | `NvidiaDocumentEmbedder` |

### Local / Self-Hosted

| Provider | Package | TextEmbedder | DocumentEmbedder |
|----------|---------|-------------|------------------|
| Sentence Transformers | built-in | `SentenceTransformersTextEmbedder` | `SentenceTransformersDocumentEmbedder` |
| Hugging Face API | built-in | `HuggingFaceAPITextEmbedder` | `HuggingFaceAPIDocumentEmbedder` |
| Ollama | `ollama-haystack` | `OllamaTextEmbedder` | `OllamaDocumentEmbedder` |
| Fastembed | `fastembed-haystack` | `FastembedTextEmbedder` | `FastembedDocumentEmbedder` |
| vLLM | `vllm-haystack` | `VLLMTextEmbedder` | `VLLMDocumentEmbedder` |

### Sparse Embedders

| Provider | TextEmbedder | DocumentEmbedder |
|----------|-------------|------------------|
| Fastembed Sparse | `FastembedSparseTextEmbedder` | `FastembedSparseDocumentEmbedder` |

## OpenAI Embedders

Built-in, most commonly used:

```python
from haystack.components.embedders import (
    OpenAITextEmbedder,
    OpenAIDocumentEmbedder,
)

# Query embedding
text_embedder = OpenAITextEmbedder(
    model="text-embedding-3-small",
    # dimensions=512,  # Optional: reduce dimensions for efficiency
)

# Document embedding
doc_embedder = OpenAIDocumentEmbedder(
    model="text-embedding-3-small",
    batch_size=32,
    meta_fields_to_embed=["title"],  # Include metadata in embedding
)
```

### Available OpenAI Models

| Model | Dimensions | Max Tokens | Cost |
|-------|-----------|------------|------|
| `text-embedding-3-small` | 1536 | 8191 | Cheapest |
| `text-embedding-3-large` | 3072 | 8191 | Better quality |
| `text-embedding-ada-002` | 1536 | 8191 | Legacy |

## Sentence Transformers

Local embeddings, no API key needed:

```python
from haystack.components.embedders import (
    SentenceTransformersTextEmbedder,
    SentenceTransformersDocumentEmbedder,
)

# Popular models
text_embedder = SentenceTransformersTextEmbedder(
    model="sentence-transformers/all-MiniLM-L6-v2",  # 384 dims, fast
    # model="BAAI/bge-small-en-v1.5",                # 384 dims, better
    # model="sentence-transformers/all-mpnet-base-v2", # 768 dims, best
)
text_embedder.warm_up()  # Load model

doc_embedder = SentenceTransformersDocumentEmbedder(
    model="sentence-transformers/all-MiniLM-L6-v2",
    batch_size=64,
    meta_fields_to_embed=["title", "summary"],
    embedding_separator=" | ",
)
doc_embedder.warm_up()
```

## Other Providers

### Ollama

```python
from haystack_integrations.components.embedders.ollama import (
    OllamaTextEmbedder,
    OllamaDocumentEmbedder,
)

text_embedder = OllamaTextEmbedder(
    model="nomic-embed-text",
    url="http://localhost:11434",
)
```

### Cohere

```python
from haystack_integrations.components.embedders.cohere import (
    CohereTextEmbedder,
    CohereDocumentEmbedder,
)

text_embedder = CohereTextEmbedder(
    model="embed-english-v3.0",
    input_type="search_query",  # "search_document" for indexing
)
```

## Indexing vs Querying

The same embedding model must be used for both indexing and querying. The two pipelines use different embedder types:

### Indexing Pipeline (DocumentEmbedder)

```python
indexing = Pipeline()
indexing.add_component("converter", PyPDFToDocument())
indexing.add_component("splitter", DocumentSplitter(split_by="word", split_length=200))
indexing.add_component("embedder", OpenAIDocumentEmbedder())
indexing.add_component("writer", DocumentWriter(document_store=store))

indexing.connect("converter", "splitter")
indexing.connect("splitter", "embedder")
indexing.connect("embedder", "writer")
```

### Query Pipeline (TextEmbedder)

```python
query = Pipeline()
query.add_component("embedder", OpenAITextEmbedder())
query.add_component("retriever", InMemoryEmbeddingRetriever(document_store=store))

query.connect("embedder.embedding", "retriever.query_embedding")
```

## Choosing an Embedder

| Scenario | Recommendation |
|----------|---------------|
| Quick start, cloud OK | OpenAI `text-embedding-3-small` |
| Best quality, cloud OK | OpenAI `text-embedding-3-large` |
| Local, fast | `all-MiniLM-L6-v2` (Sentence Transformers) |
| Local, high quality | `BAAI/bge-large-en-v1.5` |
| Ollama-based | `nomic-embed-text` |
| Multilingual | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` |
| Cost-sensitive at scale | Fastembed (ONNX-optimized) |

## Common Pitfalls

**Different models for indexing and querying**: Documents embedded with model A cannot be searched with model B. Always use the same model and version.

**Forgetting `warm_up()`**: Local embedders (Sentence Transformers, Fastembed) need `warm_up()` to load the model. In pipelines this is automatic, but standalone usage requires explicit calls.

**Ignoring dimensions**: The embedding dimension must match the Document Store configuration. OpenAI `text-embedding-3-small` produces 1536-dimensional vectors.

**Not embedding metadata**: Use `meta_fields_to_embed` to include title, summary, or other metadata in the embedding for better retrieval:

```python
doc_embedder = OpenAIDocumentEmbedder(
    meta_fields_to_embed=["title", "category"],
)
```

**Exceeding token limits**: Long documents may exceed the embedder's token limit. Always split documents first with `DocumentSplitter`.

## Related Topics

- Retrievers → `06-retrievers.md`
- Document Stores → `07-document-stores.md`
- Converters & Preprocessors → `09-converters-preprocessors.md`
- RAG patterns → `11-rag-patterns.md`
