# Search & Retrieval

## Search Types

```python
from agno.vectordb.search import SearchType

SearchType.vector    # Semantic similarity (default)
SearchType.keyword   # Full-text / keyword match
SearchType.hybrid    # Combines vector + keyword (recommended for production)
```

Set on the vector DB:
```python
vector_db = PgVector(
    table_name="embeddings",
    db_url=db_url,
    search_type=SearchType.hybrid,
)
```

## Agentic RAG (recommended)

Agent gets a `search_knowledge_base()` tool and autonomously decides when to search, how to reformulate queries, and whether to search multiple times.

```python
agent = Agent(
    knowledge=knowledge,
    search_knowledge=True,
)
```

## Traditional RAG

Always injects knowledge results into context before the model call:

```python
agent = Agent(
    knowledge=knowledge,
    search_knowledge=False,
    add_knowledge_to_context=True,
)
```

## Hybrid Search with Reranking

Combines vector similarity + keyword matching, then reranks results for best quality:

```python
from agno.knowledge.reranker.cohere import CohereReranker
from agno.vectordb.pgvector import PgVector, SearchType

vector_db = PgVector(
    table_name="embeddings",
    db_url=db_url,
    search_type=SearchType.hybrid,
    reranker=CohereReranker(model="rerank-v3.5", top_n=10),
)
```

## Filtering & Metadata

### Adding Metadata on Insert

```python
knowledge.insert(
    path="resumes/",
    metadata={
        "user_id": "jordan_mitchell",
        "document_type": "cv",
        "department": "engineering",
        "year": 2025,
        "access_level": "internal",
    }
)
```

### Manual Filtering

```python
# Agent-level default filters
agent = Agent(
    knowledge=knowledge,
    search_knowledge=True,
    knowledge_filters={"user_id": "jordan_mitchell"},
)

# Per-query filter override
agent.print_response("What are Jordan's skills?", knowledge_filters={"document_type": "cv"})

# Direct search with filters
results = knowledge.search(
    query="programming experience",
    filters={"user_id": "jordan_mitchell", "year": 2025},
)
```

### Agentic Filtering

Agent analyzes the query and available filter keys to automatically apply relevant filters. Requires a `contents_db`.

```python
from agno.db.postgres import PostgresDb

contents_db = PostgresDb(
    db_url="postgresql+psycopg://ai:ai@localhost:5532/ai",
    knowledge_table="knowledge_contents",
)

knowledge = Knowledge(
    vector_db=vector_db,
    contents_db=contents_db,
)

agent = Agent(
    knowledge=knowledge,
    search_knowledge=True,
    enable_agentic_knowledge_filters=True,
)

# Agent auto-filters based on query context
agent.print_response("What skills does Jordan Mitchell have?")
```

### Filter Discovery

```python
valid_filters = knowledge.get_filters()
valid, invalid = knowledge.validate_filters({"dept": "eng", "bad_key": "x"})
```

### Supported DBs for Filtering

ChromaDB, LanceDB, Milvus, MongoDB, PgVector, Pinecone, Qdrant, Weaviate.

## Contents Database

Tracks metadata about ingested content. Optional but required for agentic filtering and content management.

```python
# PostgreSQL (recommended)
from agno.db.postgres import PostgresDb
contents_db = PostgresDb(db_url="postgresql+psycopg://ai:ai@localhost:5532/ai", knowledge_table="knowledge_contents")

# SQLite
from agno.db.sqlite import SqliteDb
contents_db = SqliteDb(db_file="knowledge.db")

# MongoDB
from agno.db.mongo import MongoDb
contents_db = MongoDb(uri="mongodb://localhost:27017", database="agno_db")

# In-Memory (testing)
from agno.db.in_memory import InMemoryDb
contents_db = InMemoryDb()
```

Contents DB schema fields: `id`, `name`, `description`, `metadata` (dict), `type`, `size`, `linked_to`, `access_count`, `status`, `status_message`, `created_at`, `updated_at`, `external_id`.

## Custom Retrievers

Replace the default search with completely custom retrieval logic.

### Basic Custom Retriever

```python
from typing import Optional
from agno.agent import Agent

def knowledge_retriever(
    query: str,
    agent: Optional[Agent] = None,
    num_documents: int = 5,
    **kwargs
) -> Optional[list[dict]]:
    results = knowledge.search(query, max_results=num_documents)
    return [doc.to_dict() for doc in results]

agent = Agent(knowledge_retriever=knowledge_retriever, search_knowledge=True)
```

### Query Reformulation

```python
def knowledge_retriever(query: str, num_documents: int = 5, **kwargs) -> list[dict]:
    expanded = query.replace("vacation", "vacation PTO paid time off")
    expanded = expanded.replace("WFH", "work from home remote")
    results = knowledge.search(expanded, max_results=num_documents)
    return [doc.to_dict() for doc in results]
```

### Multi-Source Retrieval

```python
def knowledge_retriever(query: str, num_documents: int = 5, **kwargs) -> list[dict]:
    policy_results = policy_knowledge.search(query, max_results=3)
    faq_results = faq_knowledge.search(query, max_results=3)

    all_results = []
    seen_ids = set()
    for doc in policy_results + faq_results:
        if doc.id not in seen_ids:
            all_results.append(doc.to_dict())
            seen_ids.add(doc.id)
    return all_results[:num_documents]
```

### Direct Vector DB Query (Qdrant)

```python
from agno.knowledge.embedder.openai import OpenAIEmbedder
from qdrant_client import QdrantClient

embedder = OpenAIEmbedder(id="text-embedding-3-small")
qdrant_client = QdrantClient(url="http://localhost:6333")

def knowledge_retriever(query: str, num_documents: int = 5, **kwargs) -> Optional[list[dict]]:
    try:
        query_embedding = embedder.get_embedding(query)
        results = qdrant_client.query_points(
            collection_name="recipes",
            query=query_embedding,
            limit=num_documents,
        )
        return results.model_dump().get("points")
    except Exception as e:
        print(f"Search error: {e}")
        return None

agent = Agent(knowledge_retriever=knowledge_retriever, search_knowledge=True)
```
