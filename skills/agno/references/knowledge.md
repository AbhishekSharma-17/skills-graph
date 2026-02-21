# Agno Knowledge System

Knowledge gives agents access to documents, databases, and domain expertise via RAG (Retrieval-Augmented Generation).

**Pipeline**: `Content → Reader → Chunker → Embedder → VectorDB → Agent`

Two RAG modes:
- **Agentic RAG** (`search_knowledge=True`): Agent gets a `search_knowledge_base()` tool and decides when/what to search (recommended)
- **Traditional RAG** (`add_knowledge_to_context=True`): Results always injected into context

## Quick Start

```python
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.chroma import ChromaDb

knowledge = Knowledge(
    vector_db=ChromaDb(collection="docs", path="tmp/chromadb"),
)
knowledge.insert(url="https://docs.agno.com/introduction.md", skip_if_exists=True)

agent = Agent(knowledge=knowledge, search_knowledge=True)
agent.print_response("What is Agno?")
```

## Knowledge Class API

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `Optional[str]` | `None` | Name of the knowledge base — used for identification and logging |
| `description` | `Optional[str]` | `None` | Description of the knowledge base content |
| `vector_db` | `Optional[VectorDb]` | `None` | Vector database instance for storing embeddings (LanceDb, ChromaDb, PgVector, Pinecone, etc.) |
| `contents_db` | `Optional[BaseDb]` | `None` | Database for tracking content metadata — required for `enable_agentic_knowledge_filters` |
| `max_results` | `int` | `10` | Maximum number of search results returned per query |
| `readers` | `Optional[Dict[str, Reader]]` | `None` | Dictionary of custom readers for processing different file types (e.g. `{"pdf": PDFReader()}`) |

```python
from agno.knowledge.knowledge import Knowledge

knowledge = Knowledge(
    name="my-kb",
    description="Company docs",
    vector_db=vector_db,
    contents_db=contents_db,
    max_results=5,
)
```

### insert() Method Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `Optional[str]` | `None` | Display name for the content being inserted |
| `path` | `Optional[str]` | `None` | File or directory path to ingest |
| `url` | `Optional[str]` | `None` | URL to fetch and ingest |
| `content` | `Optional[str]` | `None` | Raw text content to ingest directly |
| `metadata` | `Optional[Dict[str, Any]]` | `None` | Metadata to attach to the content (used for filtering) |
| `reader` | `Optional[Reader]` | `None` | Custom reader for this specific insert (overrides default) |
| `upsert` | `bool` | `True` | If True, update existing content; if False, skip duplicates |

```python
knowledge.insert(path="documents/", metadata={"dept": "eng"}, upsert=True)
knowledge.insert(url="https://example.com/doc.pdf", reader=PDFReader())
await knowledge.ainsert(path="docs/")  # Async version
```

### search() Method Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | Required | The search query string |
| `limit` | `Optional[int]` | `None` | Max results to return (overrides `max_results`) |
| `filters` | `Optional[Dict[str, Any]]` | `None` | Metadata filters to narrow results (e.g. `{"dept": "eng"}`) |

```python
results = knowledge.search(query="deployment", limit=5, filters={"dept": "eng"})
results = await knowledge.asearch(query="deployment")  # Async version
```

### Content Management Methods

| Method | Description |
|--------|-------------|
| `get_content(limit, page, sort_by)` | Paginated content listing — returns `(content_list, total)` |
| `get_content_by_id(content_id)` | Get a specific content item by ID |
| `remove_content_by_id(content_id)` | Delete a specific content item |
| `remove_all_content()` | Delete all content from the knowledge base |
| `get_filters()` | Get all valid filter keys from stored metadata |
| `validate_filters(filters)` | Validate filter dict — returns `(valid, invalid)` |

```python
content_list, total = knowledge.get_content(limit=20, page=1, sort_by="created_at")
valid_filters = knowledge.get_filters()
valid, invalid = knowledge.validate_filters({"dept": "eng", "bad": "x"})
```

## Agent Integration

```python
# Agentic RAG (recommended)
agent = Agent(knowledge=knowledge, search_knowledge=True)

# Traditional RAG
agent = Agent(knowledge=knowledge, search_knowledge=False, add_knowledge_to_context=True)

# With default filters
agent = Agent(knowledge=knowledge, search_knowledge=True, knowledge_filters={"user_id": "123"})

# With agentic filtering (agent auto-infers filters; needs contents_db)
agent = Agent(knowledge=knowledge, search_knowledge=True, enable_agentic_knowledge_filters=True)

# Per-query filter override
agent.print_response("Question?", knowledge_filters={"type": "policy"})
```

## Sub-References

Read only what the task requires:

| Reference | File | Read When |
|-----------|------|-----------|
| **Vector Databases** | `references/knowledge/vector-databases.md` | Choosing or configuring a vector DB (PgVector, Chroma, LanceDB, Pinecone, Qdrant, 20+ options) |
| **Embedders** | `references/knowledge/embedders.md` | Choosing or configuring an embedding provider (OpenAI, Gemini, Cohere, Ollama, 14+ options) |
| **Readers** | `references/knowledge/readers.md` | Loading specific file types (PDF, CSV, web, YouTube, etc.), custom readers, async processing |
| **Chunking** | `references/knowledge/chunking.md` | Choosing or configuring chunking strategies (fixed, semantic, recursive, code, markdown, etc.) |
| **Search & Retrieval** | `references/knowledge/search-retrieval.md` | Search types (vector/keyword/hybrid), reranking, custom retrievers, filtering, contents DB |
| **Examples** | `references/knowledge/examples.md` | Complete production-ready examples and performance optimization patterns |
