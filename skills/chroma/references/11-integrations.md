# Chroma — Integrations

> Source: [docs.trychroma.com/integrations](https://docs.trychroma.com/integrations)

## Table of Contents

- [Overview](#overview)
- [LangChain](#langchain)
- [LlamaIndex](#llamaindex)
- [Haystack](#haystack)
- [Anthropic MCP](#anthropic-mcp)
- [Google ADK](#google-adk)
- [DeepEval](#deepeval)
- [Streamlit](#streamlit)
- [Mem0](#mem0)
- [Framework Comparison](#framework-comparison)
- [Common Pitfalls](#common-pitfalls)

## Overview

Chroma integrates with major AI/ML frameworks as a vector store backend. Most integrations are maintained by the framework teams and available as separate packages.

**Supported frameworks:**
- LangChain (Python + JS)
- LlamaIndex
- Haystack (deepset)
- Anthropic MCP
- Google ADK
- DeepEval
- Streamlit
- Mem0
- OpenLIT / OpenLLMetry (observability)
- Braintrust, Contextual AI, VoltAgent

## LangChain

Chroma is a first-class vector store in LangChain for RAG pipelines.

### Installation

```bash
pip install langchain-chroma
```

### Basic Usage

```python
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Create vector store from documents
vectorstore = Chroma.from_documents(
    documents=docs,
    embedding=embeddings,
    collection_name="langchain_docs",
    persist_directory="./chroma_langchain",
)

# Similarity search
results = vectorstore.similarity_search(
    "What is a vector database?",
    k=5,
)

# As a retriever for RAG chains
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 5},
)
```

### With Metadata Filtering

```python
results = vectorstore.similarity_search(
    "deployment guide",
    k=5,
    filter={"source": "docs"},
)
```

### Persistent Storage

```python
# Create with persistence
vectorstore = Chroma(
    collection_name="my_collection",
    embedding_function=embeddings,
    persist_directory="./chroma_db",
)

# Load existing
vectorstore = Chroma(
    collection_name="my_collection",
    embedding_function=embeddings,
    persist_directory="./chroma_db",
)
```

### Client-Server Mode

```python
import chromadb

chroma_client = chromadb.HttpClient(host="localhost", port=8000)

vectorstore = Chroma(
    client=chroma_client,
    collection_name="my_collection",
    embedding_function=embeddings,
)
```

## LlamaIndex

Chroma serves as a vector store for LlamaIndex's indexing and retrieval.

### Installation

```bash
pip install llama-index-vector-stores-chroma
```

### Basic Usage

```python
import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import VectorStoreIndex, StorageContext

chroma_client = chromadb.PersistentClient(path="./chroma_db")
chroma_collection = chroma_client.get_or_create_collection("llama_docs")

vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# Index documents
index = VectorStoreIndex.from_documents(
    documents,
    storage_context=storage_context,
)

# Query
query_engine = index.as_query_engine()
response = query_engine.query("What is Chroma?")
```

### Load Existing Index

```python
chroma_client = chromadb.PersistentClient(path="./chroma_db")
chroma_collection = chroma_client.get_collection("llama_docs")

vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
index = VectorStoreIndex.from_vector_store(vector_store)
```

## Haystack

Chroma integrates as a document store in Haystack pipelines.

### Installation

```bash
pip install chroma-haystack
```

### Basic Usage

```python
from haystack_integrations.document_stores.chroma import ChromaDocumentStore

document_store = ChromaDocumentStore(
    collection_name="haystack_docs",
    persist_path="./chroma_haystack",
)

# Write documents
from haystack import Document

docs = [
    Document(content="Chroma is a vector database", meta={"source": "docs"}),
]
document_store.write_documents(docs)

# Use in retrieval pipeline
from haystack_integrations.components.retrievers.chroma import ChromaQueryTextRetriever

retriever = ChromaQueryTextRetriever(document_store=document_store)
results = retriever.run(query="vector database", top_k=5)
```

## Anthropic MCP

Chroma provides an MCP (Model Context Protocol) server for use with Claude and other MCP-compatible AI assistants.

### Setup

```bash
# Install Chroma MCP server
pip install chromadb-mcp
```

### Configuration

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "chroma": {
      "command": "chromadb-mcp",
      "args": ["--path", "./chroma-data"]
    }
  }
}
```

The MCP server exposes tools for creating collections, adding documents, querying, and managing data through natural language interactions.

## Google ADK

Integration with Google's Agent Development Kit.

```python
from google.adk.tools import ChromaRetriever

retriever = ChromaRetriever(
    collection_name="my_collection",
    chroma_client=client,
)
```

## DeepEval

Use Chroma as the knowledge base for RAG evaluation.

```python
from deepeval.dataset import EvaluationDataset

# Chroma stores the context for evaluation
# DeepEval measures retrieval quality metrics
```

## Streamlit

Build interactive apps with Chroma-powered search.

```python
import streamlit as st
import chromadb

@st.cache_resource
def get_collection():
    client = chromadb.PersistentClient(path="./chroma_data")
    return client.get_or_create_collection("docs")

collection = get_collection()

query = st.text_input("Search documents:")
if query:
    results = collection.query(query_texts=[query], n_results=5)
    for doc, dist in zip(results["documents"][0], results["distances"][0]):
        st.write(f"**Score: {1 - dist:.3f}**")
        st.write(doc)
        st.divider()
```

## Mem0

Use Chroma as the backend for Mem0's AI memory layer.

```python
from mem0 import Memory

config = {
    "vector_store": {
        "provider": "chroma",
        "config": {
            "collection_name": "agent_memory",
            "path": "./chroma_mem0",
        }
    }
}

memory = Memory.from_config(config)
memory.add("User prefers Python over JavaScript", user_id="user1")
results = memory.search("programming preferences", user_id="user1")
```

## Framework Comparison

| Framework | Package | Use Case |
|-----------|---------|----------|
| **LangChain** | `langchain-chroma` | RAG chains, agents, document loaders |
| **LlamaIndex** | `llama-index-vector-stores-chroma` | Index construction, query engines |
| **Haystack** | `chroma-haystack` | Pipeline-based retrieval, hybrid search |
| **MCP** | `chromadb-mcp` | Claude/AI assistant tool use |
| **Streamlit** | Direct `chromadb` | Interactive search apps |

## Common Pitfalls

1. **Embedding function conflicts** — LangChain and LlamaIndex use their own embedding wrappers. Don't mix framework embeddings with Chroma's native embedding functions on the same collection.

2. **Persistence path sharing** — Don't access the same persistent Chroma directory from multiple framework integrations simultaneously. Use client-server mode for shared access.

3. **Version compatibility** — Framework integration packages may lag behind the main Chroma release. Check compatibility before upgrading `chromadb`.

4. **LangChain filter syntax** — LangChain uses `filter=` (not `where=`) for metadata filtering. The syntax differs from Chroma's native API.

5. **MCP server is separate** — The MCP server package (`chromadb-mcp`) is separate from the main `chromadb` package. Install both if you need programmatic access and MCP.
