# Ollama — Embeddings & RAG

> Source: [docs.ollama.com/capabilities/embeddings](https://docs.ollama.com/capabilities/embeddings) | Version: 0.22.x

## Table of Contents

- [Overview](#overview)
- [Embedding Models](#embedding-models)
- [Generating Embeddings](#generating-embeddings)
- [Building a RAG Pipeline](#building-a-rag-pipeline)
- [Vector Database Integration](#vector-database-integration)
- [Chunking Strategies](#chunking-strategies)
- [RAG with LangChain](#rag-with-langchain)
- [RAG with LlamaIndex](#rag-with-llamaindex)
- [Performance Optimization](#performance-optimization)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

Ollama supports embedding models that convert text into dense vector representations. These vectors capture semantic meaning, enabling similarity search, clustering, and retrieval-augmented generation (RAG).

**Key advantage:** All embeddings are generated locally — no API costs, no data leaving your machine.

## Embedding Models

| Model | Dimensions | Context | Size | Quality | Speed |
|-------|-----------|---------|------|---------|-------|
| **nomic-embed-text** | 768 | 8192 | ~500 MB | Best overall | Fast |
| **mxbai-embed-large** | 1024 | 512 | ~670 MB | High quality | Moderate |
| **all-minilm** | 384 | 256 | ~46 MB | Good for prototyping | Very fast |
| **snowflake-arctic-embed** | 1024 | 512 | ~670 MB | Strong retrieval | Moderate |
| **bge-large** | 1024 | 512 | ~670 MB | Good multilingual | Moderate |

**Recommendations:**
- **Best overall:** `nomic-embed-text` — best balance of quality, speed, and context length
- **Minimum footprint:** `all-minilm` — 46 MB, runs anywhere, fine for prototyping
- **Maximum quality:** `mxbai-embed-large` — highest retrieval accuracy
- **Long documents:** `nomic-embed-text` — 8192 token context handles full pages

## Generating Embeddings

### CLI

```bash
# Pull an embedding model
ollama pull nomic-embed-text
```

### REST API

```bash
curl http://localhost:11434/api/embeddings -d '{
  "model": "nomic-embed-text",
  "prompt": "Machine learning is a subset of artificial intelligence"
}'

# Response: {"embedding": [0.123, -0.456, 0.789, ...]}
```

### Python Library

```python
from ollama import embeddings

response = embeddings(
    model="nomic-embed-text",
    prompt="Kubernetes orchestrates containerized applications",
)
vector = response.embedding
print(f"Dimensions: {len(vector)}")  # 768
```

### OpenAI-Compatible API

```bash
curl http://localhost:11434/v1/embeddings -d '{
  "model": "nomic-embed-text",
  "input": ["First document", "Second document"]
}'
```

### Batch Embedding

```python
from ollama import Client

client = Client()
documents = [
    "Python is a programming language",
    "Docker containers isolate applications",
    "REST APIs use HTTP methods",
]

vectors = []
for doc in documents:
    resp = client.embeddings(model="nomic-embed-text", prompt=doc)
    vectors.append(resp.embedding)

print(f"Embedded {len(vectors)} documents, {len(vectors[0])} dimensions each")
```

## Building a RAG Pipeline

A complete local RAG pipeline with Ollama:

```python
import numpy as np
from ollama import embeddings, chat

def cosine_similarity(a: list[float], b: list[float]) -> float:
    a_arr, b_arr = np.array(a), np.array(b)
    return float(np.dot(a_arr, b_arr) / (np.linalg.norm(a_arr) * np.linalg.norm(b_arr)))

knowledge_base = [
    "Python 3.12 introduced type parameter syntax with the `type` statement.",
    "FastAPI is a modern web framework for building APIs with Python.",
    "Docker uses cgroups and namespaces for container isolation.",
    "Kubernetes manages container orchestration across clusters.",
    "PostgreSQL supports JSONB for semi-structured data storage.",
]

# Step 1: Embed all documents
doc_embeddings = []
for doc in knowledge_base:
    resp = embeddings(model="nomic-embed-text", prompt=doc)
    doc_embeddings.append(resp.embedding)

# Step 2: Embed the query
query = "How does Docker isolate containers?"
query_resp = embeddings(model="nomic-embed-text", prompt=query)
query_embedding = query_resp.embedding

# Step 3: Find most similar documents
similarities = [
    cosine_similarity(query_embedding, doc_emb) for doc_emb in doc_embeddings
]
top_indices = np.argsort(similarities)[-3:][::-1]

context = "\n".join(knowledge_base[i] for i in top_indices)

# Step 4: Generate answer with context
response = chat(
    model="llama3.2",
    messages=[
        {"role": "system", "content": f"Answer using only this context:\n{context}"},
        {"role": "user", "content": query},
    ],
)
print(response.message.content)
```

## Vector Database Integration

### ChromaDB

```python
import chromadb
from ollama import embeddings, chat

chroma = chromadb.Client()
collection = chroma.create_collection("docs")

documents = ["doc1 content...", "doc2 content...", "doc3 content..."]

for i, doc in enumerate(documents):
    resp = embeddings(model="nomic-embed-text", prompt=doc)
    collection.add(
        ids=[f"doc_{i}"],
        embeddings=[resp.embedding],
        documents=[doc],
    )

query_resp = embeddings(model="nomic-embed-text", prompt="search query")
results = collection.query(query_embeddings=[query_resp.embedding], n_results=3)

context = "\n".join(results["documents"][0])
response = chat(
    model="llama3.2",
    messages=[
        {"role": "system", "content": f"Answer using this context:\n{context}"},
        {"role": "user", "content": "search query"},
    ],
)
```

### Qdrant

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from ollama import embeddings

qdrant = QdrantClient(":memory:")
qdrant.create_collection(
    collection_name="docs",
    vectors_config=VectorParams(size=768, distance=Distance.COSINE),
)

documents = ["doc1...", "doc2...", "doc3..."]

points = []
for i, doc in enumerate(documents):
    resp = embeddings(model="nomic-embed-text", prompt=doc)
    points.append(PointStruct(id=i, vector=resp.embedding, payload={"text": doc}))

qdrant.upsert(collection_name="docs", points=points)

query_resp = embeddings(model="nomic-embed-text", prompt="query")
results = qdrant.search(collection_name="docs", query_vector=query_resp.embedding, limit=3)
```

## Chunking Strategies

Effective RAG requires splitting documents into appropriately sized chunks:

```python
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks by character count."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start = end - overlap
    return chunks

def chunk_by_paragraphs(text: str, max_tokens: int = 512) -> list[str]:
    """Split text by paragraphs, merging small ones."""
    paragraphs = text.split("\n\n")
    chunks = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) > max_tokens * 4:
            if current:
                chunks.append(current.strip())
            current = para
        else:
            current += "\n\n" + para if current else para
    if current:
        chunks.append(current.strip())
    return chunks
```

**Guidelines:**
- `nomic-embed-text` handles up to 8192 tokens — can embed entire pages
- `all-minilm` is limited to 256 tokens — must use smaller chunks
- Overlap of 10-20% helps maintain context across chunk boundaries
- Paragraph-based chunking preserves semantic coherence

## RAG with LangChain

```python
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

embeddings = OllamaEmbeddings(model="nomic-embed-text")
llm = ChatOllama(model="llama3.2")

splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
docs = splitter.create_documents(["your document text here..."])

vectorstore = Chroma.from_documents(docs, embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

prompt = ChatPromptTemplate.from_template(
    "Answer based on context:\n{context}\n\nQuestion: {question}"
)
chain = {"context": retriever, "question": RunnablePassthrough()} | prompt | llm
result = chain.invoke("your question here")
```

## RAG with LlamaIndex

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding

Settings.llm = Ollama(model="llama3.2", request_timeout=120)
Settings.embed_model = OllamaEmbedding(model_name="nomic-embed-text")

documents = SimpleDirectoryReader("./data").load_data()
index = VectorStoreIndex.from_documents(documents)

query_engine = index.as_query_engine()
response = query_engine.query("What is this document about?")
print(response)
```

## Performance Optimization

1. **Batch requests** — embed multiple documents in sequence to keep the model warm
2. **Cache embeddings** — store embeddings persistently; re-embedding is wasteful
3. **Model keep-alive** — set `keep_alive: "30m"` to avoid reloading between requests
4. **Use nomic-embed-text** — best throughput per quality dollar on CPU or GPU
5. **Parallel workers** — set `OLLAMA_NUM_PARALLEL=4` for concurrent embedding requests

## Common Pitfalls

1. **Wrong model type** — chat models (llama3.2, qwen3) cannot generate embeddings. Use dedicated embedding models (nomic-embed-text, all-minilm)
2. **Dimension mismatch** — vector DB dimension must match the model's output (768 for nomic, 384 for minilm). Mismatches cause errors
3. **Context overflow** — all-minilm truncates at 256 tokens. Long documents need chunking. Use nomic-embed-text for longer inputs
4. **Not normalizing** — some distance metrics require L2-normalized vectors. Ollama returns raw embeddings; normalize if using dot product
5. **Empty prompts** — sending an empty string produces a zero vector. Always validate input text
