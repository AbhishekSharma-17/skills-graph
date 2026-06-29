# Milvus — Integrations

> Source: [milvus.io/docs/integrate_with_langchain.md](https://milvus.io/docs/integrate_with_langchain.md) | Version: 3.0-beta

## Table of Contents

- [LangChain Integration](#langchain-integration)
- [LlamaIndex Integration](#llamaindex-integration)
- [Embedding Models](#embedding-models)
- [Haystack Integration](#haystack-integration)
- [Direct pymilvus RAG Pattern](#direct-pymilvus-rag-pattern)
- [Integration Ecosystem](#integration-ecosystem)
- [Common Pitfalls](#common-pitfalls)

## Overview

Milvus integrates with popular AI/ML frameworks for building RAG pipelines, semantic search, and AI applications. The primary integration points are vector stores (LangChain, LlamaIndex), embedding models (OpenAI, Sentence Transformers), and orchestration frameworks.

## LangChain Integration

### Installation

```bash
pip install langchain langchain-milvus langchain-openai pymilvus
```

### Basic Vector Store

```python
from langchain_milvus import Milvus
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Create vector store from documents
vectorstore = Milvus.from_documents(
    documents=docs,
    embedding=embeddings,
    connection_args={"uri": "./milvus_langchain.db"},  # Milvus Lite
    collection_name="langchain_docs",
    drop_old=False,
)
```

### Similarity Search

```python
results = vectorstore.similarity_search(
    "What is retrieval augmented generation?",
    k=3,
)

for doc in results:
    print(doc.page_content[:200])
```

### Search with Score

```python
results = vectorstore.similarity_search_with_score(
    "vector database features",
    k=5,
)

for doc, score in results:
    print(f"Score: {score:.4f} — {doc.page_content[:100]}")
```

### Metadata Filtering

```python
results = vectorstore.similarity_search(
    "machine learning",
    k=3,
    expr="source == 'arxiv' and year >= 2024",
)
```

### As a Retriever (for RAG Chains)

```python
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 5},
)

# Use in a RAG chain
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

prompt = ChatPromptTemplate.from_template(
    "Answer based on context:\n{context}\n\nQuestion: {question}"
)

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | ChatOpenAI(model="gpt-4o")
)

answer = chain.invoke("How does Milvus handle vector indexing?")
```

### Server-Side Connection

```python
vectorstore = Milvus(
    embedding_function=embeddings,
    collection_name="production_docs",
    connection_args={
        "uri": "http://localhost:19530",
        "token": "root:Milvus",
    },
)
```

### Zilliz Cloud Connection

```python
vectorstore = Milvus(
    embedding_function=embeddings,
    collection_name="cloud_docs",
    connection_args={
        "uri": "https://your-cluster.zillizcloud.com",
        "token": "your-api-key",
    },
)
```

## LlamaIndex Integration

### Installation

```bash
pip install llama-index llama-index-vector-stores-milvus pymilvus
```

### Basic Usage

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.vector_stores.milvus import MilvusVectorStore

# Create Milvus vector store
vector_store = MilvusVectorStore(
    uri="./milvus_llamaindex.db",
    collection_name="llamaindex_docs",
    dim=1536,
    overwrite=False,
)

# Load documents
documents = SimpleDirectoryReader("./data").load_data()

# Create index
storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_documents(
    documents,
    storage_context=storage_context,
)

# Query
query_engine = index.as_query_engine()
response = query_engine.query("What is Milvus?")
print(response)
```

### With Metadata Filters

```python
from llama_index.core.vector_stores import MetadataFilter, MetadataFilters, FilterOperator

filters = MetadataFilters(
    filters=[
        MetadataFilter(key="source", value="docs", operator=FilterOperator.EQ),
        MetadataFilter(key="year", value=2024, operator=FilterOperator.GTE),
    ]
)

query_engine = index.as_query_engine(filters=filters)
```

### Server Connection

```python
vector_store = MilvusVectorStore(
    uri="http://localhost:19530",
    token="root:Milvus",
    collection_name="production_docs",
    dim=1536,
)
```

## Embedding Models

### OpenAI Embeddings

```python
from openai import OpenAI

openai_client = OpenAI()

def get_embedding(text, model="text-embedding-3-small"):
    response = openai_client.embeddings.create(input=text, model=model)
    return response.data[0].embedding

embedding = get_embedding("Hello, world!")
# dim=1536 for text-embedding-3-small
```

### Sentence Transformers (Local)

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

texts = ["Hello world", "Milvus is a vector database"]
embeddings = model.encode(texts).tolist()
# dim=384 for all-MiniLM-L6-v2
```

### Milvus Model (Built-in Embeddings)

```python
pip install pymilvus[model]
```

```python
from pymilvus.model.dense import SentenceTransformerEmbeddingFunction

ef = SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2",
    device="cpu",
)

docs = ["Hello world", "Milvus is great"]
embeddings = ef.encode_documents(docs)
query_embedding = ef.encode_queries(["vector database"])
```

### Cohere Embeddings

```python
import cohere

co = cohere.Client("your-api-key")

response = co.embed(
    texts=["Hello world"],
    model="embed-english-v3.0",
    input_type="search_document",
)
embedding = response.embeddings[0]
# dim=1024
```

## Haystack Integration

```python
from haystack_integrations.document_stores.milvus import MilvusDocumentStore
from haystack_integrations.components.retrievers.milvus import MilvusEmbeddingRetriever

document_store = MilvusDocumentStore(
    connection_args={"uri": "./milvus_haystack.db"},
    collection_name="haystack_docs",
)

retriever = MilvusEmbeddingRetriever(document_store=document_store)
```

## Direct pymilvus RAG Pattern

```python
from pymilvus import MilvusClient
from openai import OpenAI

milvus = MilvusClient("./rag.db")
openai_client = OpenAI()

def embed(text):
    resp = openai_client.embeddings.create(input=text, model="text-embedding-3-small")
    return resp.data[0].embedding

def ingest(texts, source="manual"):
    data = [
        {"vector": embed(t), "text": t, "source": source}
        for t in texts
    ]
    milvus.insert("knowledge_base", data)

def retrieve(query, top_k=5):
    results = milvus.search(
        collection_name="knowledge_base",
        data=[embed(query)],
        limit=top_k,
        output_fields=["text", "source"],
    )
    return [hit["entity"]["text"] for hits in results for hit in hits]

def ask(question):
    context = retrieve(question)
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": f"Answer using context:\n{'\\n'.join(context)}"},
            {"role": "user", "content": question},
        ],
    )
    return response.choices[0].message.content
```

## Integration Ecosystem

| Framework | Package | Status |
|-----------|---------|--------|
| LangChain | `langchain-milvus` | Official |
| LlamaIndex | `llama-index-vector-stores-milvus` | Official |
| Haystack | `haystack-integrations[milvus]` | Community |
| Semantic Kernel | `semantic-kernel` | Microsoft |
| Spring AI | `spring-ai-milvus-store` | Spring |
| DSPy | `dspy-ai` | Community |
| AutoGen | Direct pymilvus | Microsoft |

## Common Pitfalls

- **Dimension mismatch** — vector dimension in Milvus must match your embedding model's output exactly
- **Using wrong embedding model for queries vs. documents** — same model must be used for both
- **Not installing framework-specific package** — e.g., `langchain-milvus` is separate from `langchain`
- **Milvus Lite vs. server URI** — file path for Lite, HTTP URL for server
- **LangChain `drop_old=True`** — drops existing collection on every restart; set to `False` for persistence
