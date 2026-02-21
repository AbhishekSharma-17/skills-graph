# Embedder Providers

All embedding model providers supported by Agno.

## Provider Index

| Provider | Class | Import | Default Model |
|----------|-------|--------|---------------|
| OpenAI | `OpenAIEmbedder` | `from agno.embedder.openai import OpenAIEmbedder` | `text-embedding-3-small` |
| Azure OpenAI | `AzureOpenAIEmbedder` | `from agno.embedder.azure_openai import AzureOpenAIEmbedder` | Configurable |
| Google | `GeminiEmbedder` | `from agno.embedder.google import GeminiEmbedder` | `text-embedding-004` |
| Anthropic (via Voyage) | `VoyageEmbedder` | `from agno.embedder.voyage import VoyageEmbedder` | `voyage-3` |
| Cohere | `CohereEmbedder` | `from agno.embedder.cohere import CohereEmbedder` | `embed-english-v3.0` |
| Mistral | `MistralEmbedder` | `from agno.embedder.mistral import MistralEmbedder` | `mistral-embed` |
| Ollama | `OllamaEmbedder` | `from agno.embedder.ollama import OllamaEmbedder` | Configurable |
| HuggingFace | `HuggingFaceEmbedder` | `from agno.embedder.huggingface import HuggingFaceEmbedder` | Configurable |
| Together | `TogetherEmbedder` | `from agno.embedder.together import TogetherEmbedder` | Configurable |
| Fireworks | `FireworksEmbedder` | `from agno.embedder.fireworks import FireworksEmbedder` | Configurable |
| SentenceTransformer | `SentenceTransformerEmbedder` | `from agno.embedder.sentence_transformer import SentenceTransformerEmbedder` | `all-MiniLM-L6-v2` |
| FastEmbed | `FastEmbedEmbedder` | `from agno.embedder.fastembed import FastEmbedEmbedder` | Configurable |

## Common Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | `str` | Model identifier |
| `dimensions` | `Optional[int]` | Embedding dimensions (usually set by model) |
| `api_key` | `Optional[str]` | API key (or via environment variable) |

## Quick Start Examples

### OpenAI Embedder (Recommended)
```python
from agno.embedder.openai import OpenAIEmbedder

embedder = OpenAIEmbedder(
    id="text-embedding-3-small",
    dimensions=1536
)
```

### Google Gemini Embedder
```python
from agno.embedder.google import GeminiEmbedder

embedder = GeminiEmbedder(
    id="text-embedding-004",
    dimensions=768
)
```

### Cohere Embedder
```python
from agno.embedder.cohere import CohereEmbedder

embedder = CohereEmbedder(
    id="embed-english-v3.0",
    dimensions=1024
)
```

### Ollama (Local)
```python
from agno.embedder.ollama import OllamaEmbedder

embedder = OllamaEmbedder(
    id="nomic-embed-text",
    dimensions=768,
    base_url="http://localhost:11434"
)
```

### HuggingFace
```python
from agno.embedder.huggingface import HuggingFaceEmbedder

embedder = HuggingFaceEmbedder(
    id="sentence-transformers/all-MiniLM-L6-v2",
    dimensions=384
)
```

## Provider Categories

### Cloud-Based (API)
- OpenAI
- Azure OpenAI
- Google
- Cohere
- Mistral
- Together
- Fireworks
- Voyage (Anthropic partnership)

### Local/Self-Hosted
- Ollama
- HuggingFace
- SentenceTransformer
- FastEmbed

## Model Characteristics

| Provider | Dimensions | Speed | Quality | Cost |
|----------|-----------|-------|---------|------|
| OpenAI (3-small) | 1536 | Fast | Excellent | Standard |
| OpenAI (3-large) | 3072 | Medium | Premium | Higher |
| Google | 768 | Fast | Excellent | Standard |
| Cohere | 1024 | Medium | Excellent | Standard |
| Voyage | 1024 | Medium | Excellent | Standard |
| Mistral | 1024 | Fast | Good | Low |
| SentenceTransformer | 384-768 | Very Fast | Good | Free |
| Ollama | Variable | Variable | Good | Free |

## Environment Variables

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Google
export GOOGLE_API_KEY="..."

# Cohere
export COHERE_API_KEY="..."

# Azure OpenAI
export AZURE_OPENAI_API_KEY="..."
export AZURE_OPENAI_ENDPOINT="https://..."

# Voyage
export VOYAGE_API_KEY="..."

# Mistral
export MISTRAL_API_KEY="..."
```

## Integration with Vector Stores

```python
from agno.vectordb.pgvector import PgVector
from agno.embedder.openai import OpenAIEmbedder

vector_db = PgVector(
    db_url="postgresql+psycopg://user:pass@localhost/db",
    table_name="documents",
    embedder=OpenAIEmbedder(id="text-embedding-3-small"),
)
```

## Cross-References

→ Vector Store Providers: `references/vector-store-providers.md`
→ Knowledge concepts: `references/knowledge.md`
→ Knowledge bases: `references/knowledge-bases.md`
