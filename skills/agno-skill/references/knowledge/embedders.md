# Embedders

Embedders convert text to vector representations. Pass to `vector_db=VectorDB(embedder=...)`.

## OpenAI (default)

```python
from agno.knowledge.embedder.openai import OpenAIEmbedder

embedder = OpenAIEmbedder(
    id="text-embedding-3-small",         # Model ID
    dimensions=1536,                     # Output dimensions
    encoding_format="float",             # float | base64
    api_key=None,                        # From OPENAI_API_KEY env
    organization=None,
    base_url=None,                       # Custom endpoint
    enable_batch=False,                  # Batch processing
    batch_size=100,                      # Texts per batch
)
```

Reduce dimensions for speed/cost:
```python
embedder = OpenAIEmbedder(id="text-embedding-3-large", dimensions=1024)  # instead of 3072
```

## Gemini

```python
from agno.knowledge.embedder.google import GeminiEmbedder

embedder = GeminiEmbedder(
    id="gemini-embedding-001",
    api_key=None,                        # From GOOGLE_API_KEY env
)
```

## Cohere

```python
from agno.knowledge.embedder.cohere import CohereEmbedder

embedder = CohereEmbedder(
    model="embed-english-v3.0",
    api_key=None,                        # From COHERE_API_KEY env
)
```

## Ollama (local, no API key needed)

```python
from agno.knowledge.embedder.ollama import OllamaEmbedder

embedder = OllamaEmbedder(
    model="nomic-embed-text",
    base_url="http://localhost:11434",
)
```

## FastEmbed (local, fast)

```python
from agno.knowledge.embedder.qdrant_fastembed import QdrantFastEmbedder

embedder = QdrantFastEmbedder(
    model="BAAI/bge-small-en-v1.5",
)
```

## Azure OpenAI

```python
from agno.knowledge.embedder.azure_openai import AzureOpenAIEmbedder

embedder = AzureOpenAIEmbedder(
    id="text-embedding-ada-002",
    api_key=None,                        # From AZURE_OPENAI_API_KEY env
    azure_endpoint=None,                 # From AZURE_OPENAI_ENDPOINT env
    api_version="2024-02-01",
)
```

## All Supported Embedders

| Provider | Import | Env Key |
|----------|--------|---------|
| OpenAI | `agno.knowledge.embedder.openai.OpenAIEmbedder` | `OPENAI_API_KEY` |
| Gemini | `agno.knowledge.embedder.google.GeminiEmbedder` | `GOOGLE_API_KEY` |
| Cohere | `agno.knowledge.embedder.cohere.CohereEmbedder` | `COHERE_API_KEY` |
| Voyage AI | `agno.knowledge.embedder.voyageai.VoyageAIEmbedder` | `VOYAGE_API_KEY` |
| Mistral | `agno.knowledge.embedder.mistral.MistralEmbedder` | `MISTRAL_API_KEY` |
| Ollama | `agno.knowledge.embedder.ollama.OllamaEmbedder` | (local) |
| FastEmbed | `agno.knowledge.embedder.qdrant_fastembed.QdrantFastEmbedder` | (local) |
| HuggingFace | `agno.knowledge.embedder.huggingface.HuggingFaceEmbedder` | `HF_TOKEN` |
| AWS Bedrock | `agno.knowledge.embedder.aws_bedrock.AWSBedrockEmbedder` | AWS credentials |
| Azure OpenAI | `agno.knowledge.embedder.azure_openai.AzureOpenAIEmbedder` | `AZURE_OPENAI_API_KEY` |
| Fireworks | `agno.knowledge.embedder.fireworks.FireworksEmbedder` | `FIREWORKS_API_KEY` |
| Together | `agno.knowledge.embedder.together.TogetherEmbedder` | `TOGETHER_API_KEY` |
| Jina | `agno.knowledge.embedder.jina.JinaEmbedder` | `JINA_API_KEY` |
| Nebius | `agno.knowledge.embedder.nebius.NebiusEmbedder` | `NEBIUS_API_KEY` |

## Selection Guide

| Need | Best Choice |
|------|-------------|
| General purpose (cloud) | OpenAI `text-embedding-3-small` |
| High quality (cloud) | OpenAI `text-embedding-3-large` or Cohere `embed-english-v3.0` |
| Google ecosystem | Gemini `gemini-embedding-001` |
| Local / private | Ollama `nomic-embed-text` or FastEmbed |
| Speed + low latency | FastEmbed (local) |
| Enterprise / Azure | Azure OpenAI Embedder |
