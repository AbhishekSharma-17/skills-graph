# Vector Store Providers

All vector databases supported by Agno for knowledge/RAG pipelines.

## Provider Index

| Provider | Class | Import | Key Params |
|----------|-------|--------|------------|
| PgVector | `PgVector` | `from agno.vectordb.pgvector import PgVector` | `db_url`, `table_name`, `embedder` |
| PgVector (Async) | `AsyncPgVector` | `from agno.vectordb.pgvector import AsyncPgVector` | Same as PgVector |
| ChromaDB | `ChromaDb` | `from agno.vectordb.chroma import ChromaDb` | `collection`, `path`, `embedder` |
| LanceDB | `LanceDb` | `from agno.vectordb.lancedb import LanceDb` | `uri`, `table_name`, `embedder` |
| Pinecone | `Pinecone` | `from agno.vectordb.pinecone import Pinecone` | `api_key`, `index_name`, `embedder` |
| Qdrant | `Qdrant` | `from agno.vectordb.qdrant import Qdrant` | `url`, `collection`, `embedder` |
| Weaviate | `Weaviate` | `from agno.vectordb.weaviate import Weaviate` | `url`, `collection`, `embedder` |
| Milvus | `Milvus` | `from agno.vectordb.milvus import Milvus` | `uri`, `collection_name`, `embedder` |
| MongoDB Atlas | `MongoDbAtlas` | `from agno.vectordb.mongodb import MongoDbAtlas` | `connection_string`, `database_name`, `collection_name`, `embedder` |
| SingleStore | `SingleStore` | `from agno.vectordb.singlestore import SingleStore` | `db_url`, `table_name`, `embedder` |
| Cassandra | `Cassandra` | `from agno.vectordb.cassandra import Cassandra` | `keyspace`, `table`, `embedder` |
| ClickHouse | `Clickhouse` | `from agno.vectordb.clickhouse import Clickhouse` | `host`, `table_name`, `embedder` |
| Upstash | `Upstash` | `from agno.vectordb.upstash import Upstash` | `url`, `token`, `embedder` |
| AstraDB | `AstraDb` | `from agno.vectordb.astradb import AstraDb` | `collection_name`, `embedder` |

## Quick Start Pattern

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.knowledge.pdf import PDFKnowledgeBase
from agno.vectordb.pgvector import PgVector
from agno.embedder.openai import OpenAIEmbedder

knowledge = PDFKnowledgeBase(
    path="docs/",
    vector_db=PgVector(
        db_url="postgresql+psycopg://ai:ai@localhost:5532/ai",
        table_name="pdf_docs",
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
    ),
)

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    knowledge=knowledge,
    search_knowledge=True,
)
```

## Search Types

All vector stores support:

| Search Type | Parameter | Description |
|-------------|-----------|-------------|
| Vector (semantic) | `search_type="vector"` | Default. Similarity search using embeddings |
| Keyword | `search_type="keyword"` | Text-based search (where supported) |
| Hybrid | `search_type="hybrid"` | Combined vector + keyword (PgVector, Qdrant, Weaviate) |

## Database Deployment Profiles

### Cloud-Hosted Providers
- **Pinecone**: Fully managed vector search
- **Upstash**: Serverless vector database
- **AstraDB**: Cassandra-based managed service
- **MongoDB Atlas**: Cloud NoSQL with vector search
- **Weaviate Cloud**: Managed Weaviate instance

### Self-Hosted Providers
- **PgVector**: PostgreSQL extension
- **ChromaDB**: Embedded or standalone
- **Qdrant**: Standalone or Docker
- **Milvus**: Self-hosted or managed
- **Weaviate**: Self-hosted deployment

### SQL/Relational
- **PgVector**: PostgreSQL native
- **ClickHouse**: OLAP database
- **SingleStore**: Distributed SQL

## Connection Examples

### PgVector
```python
from agno.vectordb.pgvector import PgVector
from agno.embedder.openai import OpenAIEmbedder

vector_db = PgVector(
    db_url="postgresql+psycopg://user:password@localhost/dbname",
    table_name="documents",
    embedder=OpenAIEmbedder(id="text-embedding-3-small"),
)
```

### Pinecone
```python
from agno.vectordb.pinecone import Pinecone
from agno.embedder.openai import OpenAIEmbedder

vector_db = Pinecone(
    api_key="your-api-key",
    index_name="documents",
    embedder=OpenAIEmbedder(id="text-embedding-3-small"),
)
```

### ChromaDB
```python
from agno.vectordb.chroma import ChromaDb
from agno.embedder.openai import OpenAIEmbedder

vector_db = ChromaDb(
    path="./chroma_data",
    collection="documents",
    embedder=OpenAIEmbedder(id="text-embedding-3-small"),
)
```

### Qdrant
```python
from agno.vectordb.qdrant import Qdrant
from agno.embedder.openai import OpenAIEmbedder

vector_db = Qdrant(
    url="http://localhost:6333",
    collection="documents",
    embedder=OpenAIEmbedder(id="text-embedding-3-small"),
)
```

## Performance Considerations

| Provider | Latency | Throughput | Scalability |
|----------|---------|-----------|-------------|
| Pinecone | Ultra-low | Very High | Auto-scaling |
| Qdrant | Low | High | Horizontal |
| Milvus | Low-Medium | High | Horizontal |
| PgVector | Medium | Medium | Vertical |
| ChromaDB | Low | Medium | Limited |
| Weaviate | Low-Medium | High | Horizontal |

## Cross-References

→ Knowledge concepts: `references/knowledge.md`
→ Embedders: `references/embedder-providers.md`
→ Knowledge bases: `references/knowledge-bases.md`
