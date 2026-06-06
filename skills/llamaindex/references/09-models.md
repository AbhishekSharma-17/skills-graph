# Models (LLMs and Embeddings)

> Source: [developers.llamaindex.ai — Models](https://developers.llamaindex.ai/python/framework/module_guides/models/) | Version: 0.14.22

## Table of Contents
- [Overview](#overview)
- [LLM Configuration](#llm-configuration)
- [Supported LLM Providers](#supported-llm-providers)
- [LLM Parameters](#llm-parameters)
- [Embedding Configuration](#embedding-configuration)
- [Supported Embedding Providers](#supported-embedding-providers)
- [Local Models](#local-models)
- [Tokenizer Configuration](#tokenizer-configuration)
- [Multi-Modal Models](#multi-modal-models)
- [Common Patterns](#common-patterns)

## Overview

LlamaIndex uses two model types throughout its pipeline:

- **LLMs** — Generate text responses, power agents, synthesize answers
- **Embedding models** — Convert text to vectors for semantic similarity search

Both are configured via the global `Settings` object or per-component overrides.

## LLM Configuration

### Global Setting

```python
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI

Settings.llm = OpenAI(model="gpt-4o", temperature=0.1)
```

All components (query engines, agents, extractors) use `Settings.llm` by default.

### Per-Component Override

```python
query_engine = index.as_query_engine(llm=OpenAI(model="gpt-4o-mini"))
chat_engine = index.as_chat_engine(llm=OpenAI(model="gpt-4o"))
agent = FunctionAgent(llm=OpenAI(model="gpt-4o"), tools=[...])
```

### Direct LLM Usage

```python
from llama_index.llms.openai import OpenAI

llm = OpenAI(model="gpt-4o")

# Completion
response = llm.complete("Explain RAG in one sentence.")
print(response.text)

# Chat
from llama_index.core.llms import ChatMessage

messages = [
    ChatMessage(role="system", content="You are a helpful assistant."),
    ChatMessage(role="user", content="What is LlamaIndex?"),
]
response = llm.chat(messages)
print(response.message.content)

# Streaming
for chunk in llm.stream_complete("List 5 benefits of RAG:"):
    print(chunk.delta, end="", flush=True)

# Async
response = await llm.acomplete("Async completion")
response = await llm.achat(messages)
```

## Supported LLM Providers

| Provider | Package | Example |
|----------|---------|---------|
| OpenAI | `llama-index-llms-openai` | `OpenAI(model="gpt-4o")` |
| Anthropic | `llama-index-llms-anthropic` | `Anthropic(model="claude-sonnet-4-20250514")` |
| Google Gemini | `llama-index-llms-gemini` | `Gemini(model="models/gemini-2.0-flash")` |
| AWS Bedrock | `llama-index-llms-bedrock` | `Bedrock(model="anthropic.claude-v2")` |
| Azure OpenAI | `llama-index-llms-azure-openai` | `AzureOpenAI(...)` |
| Ollama | `llama-index-llms-ollama` | `Ollama(model="llama3")` |
| HuggingFace | `llama-index-llms-huggingface` | `HuggingFaceLLM(model_name="...")` |
| Mistral | `llama-index-llms-mistralai` | `MistralAI(model="mistral-large-latest")` |
| Groq | `llama-index-llms-groq` | `Groq(model="llama3-70b-8192")` |
| Cohere | `llama-index-llms-cohere` | `Cohere(model="command-r-plus")` |
| Together AI | `llama-index-llms-together` | `TogetherLLM(model="...")` |
| Fireworks | `llama-index-llms-fireworks` | `Fireworks(model="...")` |
| LlamaCPP | `llama-index-llms-llama-cpp` | `LlamaCPP(model_path="...")` |

Install any provider: `pip install llama-index-llms-<provider>`

## LLM Parameters

Common parameters across providers:

```python
from llama_index.llms.openai import OpenAI

llm = OpenAI(
    model="gpt-4o",
    temperature=0.1,
    max_tokens=4096,
    api_key="sk-...",
    api_base="https://custom-endpoint.com/v1",
    timeout=60.0,
    max_retries=3,
    additional_kwargs={"seed": 42},
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | str | Model identifier |
| `temperature` | float | Randomness (0.0–2.0, default varies) |
| `max_tokens` | int | Maximum response tokens |
| `api_key` | str | API key (or use env var) |
| `api_base` | str | Custom API endpoint |
| `timeout` | float | Request timeout in seconds |
| `max_retries` | int | Number of retry attempts |

## Embedding Configuration

### Global Setting

```python
from llama_index.core import Settings
from llama_index.embeddings.openai import OpenAIEmbedding

Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
```

### Per-Index Override

```python
index = VectorStoreIndex.from_documents(
    documents,
    embed_model=OpenAIEmbedding(model="text-embedding-3-large"),
)
```

### Direct Embedding Usage

```python
from llama_index.embeddings.openai import OpenAIEmbedding

embed_model = OpenAIEmbedding()

# Single text
embedding = embed_model.get_text_embedding("Hello world")
print(len(embedding))  # 1536 for ada-002

# Query embedding (may use different model/prompt)
query_embedding = embed_model.get_query_embedding("search query")

# Batch embedding
embeddings = embed_model.get_text_embedding_batch(
    ["Text 1", "Text 2", "Text 3"]
)
```

### Batch Size

```python
embed_model = OpenAIEmbedding(embed_batch_size=42)
```

Default batch size is 10. Increase for throughput, decrease if hitting rate limits.

## Supported Embedding Providers

| Provider | Package | Example |
|----------|---------|---------|
| OpenAI | `llama-index-embeddings-openai` | `OpenAIEmbedding(model="text-embedding-3-small")` |
| HuggingFace | `llama-index-embeddings-huggingface` | `HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")` |
| Cohere | `llama-index-embeddings-cohere` | `CohereEmbedding(model_name="embed-english-v3.0")` |
| Google | `llama-index-embeddings-google` | `GooglePaLMEmbedding(...)` |
| Jina | `llama-index-embeddings-jinaai` | `JinaEmbedding(model="jina-embeddings-v2-base-en")` |
| Mistral | `llama-index-embeddings-mistralai` | `MistralAIEmbedding(model_name="...")` |
| Voyage | `llama-index-embeddings-voyageai` | `VoyageEmbedding(model_name="voyage-2")` |
| Azure | `llama-index-embeddings-azure-openai` | `AzureOpenAIEmbedding(...)` |
| Ollama | `llama-index-embeddings-ollama` | `OllamaEmbedding(model_name="nomic-embed-text")` |
| FastEmbed | `llama-index-embeddings-fastembed` | `FastEmbedEmbedding(model_name="...")` |

40+ total embedding integrations.

## Local Models

### Ollama (Recommended for Local LLMs)

```python
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding

Settings.llm = Ollama(model="llama3", request_timeout=120.0)
Settings.embed_model = OllamaEmbedding(model_name="nomic-embed-text")
```

### HuggingFace (Local Embeddings)

```python
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

Settings.embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-small-en-v1.5"
)
```

### LlamaCPP (GGUF Models)

```python
from llama_index.llms.llama_cpp import LlamaCPP

llm = LlamaCPP(
    model_path="./models/llama-3-8b.gguf",
    temperature=0.1,
    max_new_tokens=256,
    context_window=4096,
    model_kwargs={"n_gpu_layers": -1},
)
```

### Disable Embeddings

For use cases that don't need vector search:

```python
from llama_index.core import Settings

Settings.embed_model = "local"
```

## Tokenizer Configuration

The tokenizer must match your LLM for accurate chunk sizing:

```python
import tiktoken
from llama_index.core import Settings

# OpenAI models
Settings.tokenizer = tiktoken.encoding_for_model("gpt-4o").encode

# HuggingFace models
from transformers import AutoTokenizer
Settings.tokenizer = AutoTokenizer.from_pretrained(
    "meta-llama/Meta-Llama-3-8B"
)
```

Default tokenizer: `cl100k_base` (matches GPT-3.5/GPT-4).

## Multi-Modal Models

LlamaIndex supports multi-modal LLMs for image + text tasks:

```python
from llama_index.multi_modal_llms.openai import OpenAIMultiModal

mm_llm = OpenAIMultiModal(model="gpt-4o", max_new_tokens=300)

from llama_index.core.schema import ImageDocument

image_doc = ImageDocument(image_path="./chart.png")
response = mm_llm.complete(
    prompt="Describe this chart.",
    image_documents=[image_doc],
)
```

## Common Patterns

### Cost Optimization

```python
# Use cheaper model for embeddings, powerful model for synthesis
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
Settings.llm = OpenAI(model="gpt-4o-mini")

# Use expensive model only for final synthesis
query_engine = index.as_query_engine(
    llm=OpenAI(model="gpt-4o"),
)
```

### Provider Switching

```python
import os

if os.getenv("USE_LOCAL"):
    from llama_index.llms.ollama import Ollama
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    Settings.llm = Ollama(model="llama3")
    Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
else:
    from llama_index.llms.openai import OpenAI
    from llama_index.embeddings.openai import OpenAIEmbedding
    Settings.llm = OpenAI(model="gpt-4o")
    Settings.embed_model = OpenAIEmbedding()
```

### Custom LLM Implementation

```python
from llama_index.core.llms import CustomLLM, CompletionResponse, LLMMetadata

class MyLLM(CustomLLM):
    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(
            context_window=4096,
            num_output=256,
            model_name="my-custom-model",
        )

    def complete(self, prompt: str, **kwargs) -> CompletionResponse:
        response_text = my_model.generate(prompt)
        return CompletionResponse(text=response_text)

    def stream_complete(self, prompt: str, **kwargs):
        for chunk in my_model.stream(prompt):
            yield CompletionResponse(text=chunk, delta=chunk)
```
