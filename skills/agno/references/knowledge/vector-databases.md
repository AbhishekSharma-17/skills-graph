# Vector Databases

The vector DB stores embeddings and handles similarity search. Pass to `Knowledge(vector_db=...)`.

## PgVector (PostgreSQL — recommended for production)

```python
from agno.vectordb.pgvector import PgVector, SearchType

vector_db = PgVector(
    table_name="embeddings",             # Required
    db_url="postgresql+psycopg://ai:ai@localhost:5532/ai",  # Required
    embedder=OpenAIEmbedder(),           # Optional (has default)
    search_type=SearchType.hybrid,       # vector | keyword | hybrid
    distance="cosine",                   # cosine | l2 | max_inner_product
    vector_score_weight=0.5,             # For hybrid: 0=keyword only, 1=vector only
    content_language=None,               # Language for full-text search
    prefix_match=None,                   # Enable prefix matching for keyword
    schema=None,                         # Database schema
)
```

Install: `uv pip install -U agno pgvector psycopg[binary] sqlalchemy`

## ChromaDB (local, zero-setup — great for dev)

```python
from agno.vectordb.chroma import ChromaDb

vector_db = ChromaDb(
    collection="my_collection",          # Required
    path="tmp/chromadb",                 # Local storage path
    embedder=OpenAIEmbedder(),           # Optional
    persistent_client=True,              # Persist across restarts
    search_type=SearchType.hybrid,       # Optional
    distance="cosine",                   # cosine | l2 | ip
)
```

Install: `uv pip install -U agno chromadb`

## LanceDB (local serverless)

```python
from agno.vectordb.lancedb import LanceDb

vector_db = LanceDb(
    uri="tmp/lancedb",                   # Required
    table_name="vectors",                # Required
    embedder=OpenAIEmbedder(),
    search_type=SearchType.hybrid,       # vector | keyword | hybrid
    nprobes=None,                        # ANN probe count
    reranker=None,                       # Optional reranker
    use_tantivy=None,                    # Tantivy full-text search
)
```

Install: `uv pip install -U agno lancedb`

## Pinecone (managed cloud)

```python
from agno.vectordb.pineconedb import PineconeDb
from pinecone import ServerlessSpec

vector_db = PineconeDb(
    name="my-index",                     # Required
    dimension=1536,                      # Required (match embedder)
    spec=ServerlessSpec(cloud="aws", region="us-east-1"),  # Required
    embedder=OpenAIEmbedder(),
    metric="cosine",                     # cosine | euclidean | dotproduct
    api_key=None,                        # From PINECONE_API_KEY env
    namespace=None,                      # Optional namespace
    use_hybrid_search=False,
    hybrid_alpha=0.5,                    # Hybrid weight
)
```

Install: `uv pip install -U agno pinecone`

## Qdrant

```python
from agno.vectordb.qdrant import Qdrant

vector_db = Qdrant(
    collection="my_collection",
    url="http://localhost:6333",
    embedder=OpenAIEmbedder(),
)
```

Install: `uv pip install -U agno qdrant-client`

## Weaviate

```python
from agno.vectordb.weaviate import Weaviate

vector_db = Weaviate(
    collection="my_collection",
    url="http://localhost:8080",
    embedder=OpenAIEmbedder(),
)
```

Install: `uv pip install -U agno weaviate-client`

## Milvus

```python
from agno.vectordb.milvus import Milvus

vector_db = Milvus(
    collection="my_collection",
    uri="http://localhost:19530",
    embedder=OpenAIEmbedder(),
)
```

Install: `uv pip install -U agno pymilvus`

## MongoDB Atlas

```python
from agno.vectordb.mongodb import MongoDb

vector_db = MongoDb(
    collection="my_collection",
    db_name="agno_db",
    uri="mongodb+srv://user:pass@cluster.mongodb.net/",
    embedder=OpenAIEmbedder(),
)
```

Install: `uv pip install -U agno pymongo`

## All Supported Vector Databases

PgVector, ChromaDB, LanceDB, Pinecone, Qdrant, Weaviate, Milvus, MongoDB (Atlas), Redis, SingleStore, ClickHouse, Couchbase, Cassandra, SurrealDB, Upstash, Azure Cosmos DB, LightRAG (graph-based).

## Selection Guide

| Need | Best Choice |
|------|-------------|
| Dev / prototyping (zero setup) | ChromaDB or LanceDB |
| Production with Postgres | PgVector |
| Managed cloud (no infra) | Pinecone |
| High-scale / performance | Qdrant or Milvus |
| Graph-based RAG | LightRAG |
| Already using MongoDB | MongoDB Atlas |
| Serverless | Upstash |
