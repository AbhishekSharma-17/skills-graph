# LlamaIndex Overview

> Source: [developers.llamaindex.ai](https://developers.llamaindex.ai/python/framework/) | Version: 0.14.22

## Table of Contents
- [What is LlamaIndex](#what-is-llamaindex)
- [Architecture](#architecture)
- [Installation](#installation)
- [Core Concepts](#core-concepts)
- [Quick Start — RAG](#quick-start--rag)
- [Quick Start — Agent](#quick-start--agent)
- [Package Structure](#package-structure)
- [Configuration with Settings](#configuration-with-settings)
- [When to Use LlamaIndex](#when-to-use-llamaindex)

## What is LlamaIndex

LlamaIndex is an open-source Python framework that connects LLMs with custom data sources. It provides tools for ingesting, structuring, indexing, and querying data so LLMs can reason over private information they were never trained on.

Core capabilities:
- **Data connectors** — Ingest from 100+ sources (APIs, PDFs, databases, web pages)
- **Data indexes** — Structure data into vector embeddings and other queryable formats
- **RAG pipelines** — Retrieve relevant context and augment LLM responses
- **Agents** — Build autonomous tool-calling agents with LLM reasoning
- **Workflows** — Event-driven orchestration for complex multi-step applications
- **Structured extraction** — Extract typed data from unstructured text using Pydantic

## Architecture

LlamaIndex follows a five-stage RAG pipeline architecture:

```
Loading → Indexing → Storing → Querying → Evaluation
```

1. **Loading** — Read data from files, APIs, databases via connectors (Readers)
2. **Indexing** — Parse into Nodes, generate embeddings, build searchable indexes
3. **Storing** — Persist indexes to vector stores, document stores, or disk
4. **Querying** — Retrieve relevant context, synthesize LLM responses
5. **Evaluation** — Measure faithfulness, relevancy, and correctness

Beyond RAG, LlamaIndex supports agents, workflows, and structured data extraction as first-class patterns.

## Installation

### Quick Start (includes OpenAI defaults)

```bash
pip install llama-index
```

This installs: `llama-index-core`, `llama-index-llms-openai`, `llama-index-embeddings-openai`, `llama-index-readers-file`.

### Custom Installation (pick your providers)

```bash
pip install llama-index-core llama-index-readers-file
pip install llama-index-llms-anthropic
pip install llama-index-embeddings-huggingface
```

### Local Models (no API keys needed)

```bash
pip install llama-index-core llama-index-readers-file \
    llama-index-llms-ollama llama-index-embeddings-huggingface
```

### Environment Setup

```bash
export OPENAI_API_KEY="sk-..."
```

Default models when using OpenAI: `gpt-3.5-turbo` (LLM) and `text-embedding-ada-002` (embeddings).

## Core Concepts

| Concept | Description |
|---------|-------------|
| **Document** | Container holding text content and metadata from a data source |
| **Node** | Atomic chunk of a Document with metadata and relationships |
| **Index** | Data structure built from Nodes for efficient retrieval |
| **Embedding** | Vector representation of text for semantic similarity |
| **Retriever** | Component that finds relevant Nodes from an Index |
| **Query Engine** | End-to-end pipeline: retrieve context → synthesize response |
| **Chat Engine** | Conversational interface with memory across turns |
| **Agent** | LLM-powered autonomous system with tool-calling capability |
| **Workflow** | Event-driven, step-based execution orchestration |
| **Settings** | Global configuration for LLM, embeddings, and chunking |

## Quick Start — RAG

Build a question-answering system over local documents in 5 lines:

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

documents = SimpleDirectoryReader("./data").load_data()
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()
response = query_engine.query("What is the main topic?")
print(response)
```

This loads all files from `./data`, chunks them, generates embeddings, builds a vector index, and answers queries using retrieved context.

## Quick Start — Agent

Build a tool-calling agent:

```python
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.openai import OpenAI

def multiply(a: float, b: float) -> float:
    """Multiply two numbers and return the product."""
    return a * b

def add(a: float, b: float) -> float:
    """Add two numbers and return the sum."""
    return a + b

agent = FunctionAgent(
    tools=[multiply, add],
    llm=OpenAI(model="gpt-4o-mini"),
    system_prompt="You perform math operations using tools.",
)

import asyncio
response = asyncio.run(agent.run(user_msg="What is 20 + (2 * 4)?"))
print(response)
```

## Package Structure

LlamaIndex uses a modular package architecture:

| Package | Purpose |
|---------|---------|
| `llama-index-core` | Core abstractions, pipeline logic, no vendor lock-in |
| `llama-index-llms-*` | LLM provider integrations (openai, anthropic, ollama, etc.) |
| `llama-index-embeddings-*` | Embedding model integrations |
| `llama-index-readers-*` | Data source connectors |
| `llama-index-vector-stores-*` | Vector database integrations |
| `llama-index-callbacks-*` | Observability integrations |
| `llama-index` | Convenience bundle (core + OpenAI defaults) |

Over 300 integration packages available on [LlamaHub](https://llamahub.ai/).

## Configuration with Settings

The global `Settings` object configures defaults used across the entire application:

```python
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

Settings.llm = OpenAI(model="gpt-4o")
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
Settings.chunk_size = 1024
Settings.chunk_overlap = 20
```

Settings can be overridden at the component level:

```python
index = VectorStoreIndex.from_documents(
    documents,
    embed_model=custom_embed_model,
)
query_engine = index.as_query_engine(llm=custom_llm)
```

## When to Use LlamaIndex

| Use Case | LlamaIndex Strength |
|----------|-------------------|
| RAG over documents | Best-in-class indexing, retrieval, and synthesis |
| Agentic applications | FunctionAgent, ReActAgent with tool calling |
| Structured extraction | Pydantic-based extraction from unstructured text |
| Multi-step workflows | Event-driven Workflow class with branching/loops |
| Document parsing | LlamaParse for complex PDFs, tables, charts |
| Multi-modal search | Image + text retrieval and reasoning |
| Production RAG | Evaluation, observability, and vector store integration |

LlamaIndex vs alternatives:
- **LangChain** — LlamaIndex focuses on data indexing and retrieval; LangChain on chaining LLM calls. They integrate well together.
- **Haystack** — Similar RAG focus. LlamaIndex has more integrations (300+) and stronger agent support.
- **Direct API calls** — Use LlamaIndex when you need structured retrieval, not just prompt engineering.
