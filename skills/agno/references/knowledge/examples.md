# Knowledge — Complete Examples & Performance

## 1. Recipe Agent (Semantic Chunking + PgVector + Hybrid Search)

Full production setup with semantic chunking, hybrid search, and contents DB:

```python
import asyncio
from agno.agent import Agent
from agno.models.openai import OpenAI
from agno.knowledge.chunking.semantic_chunking import SemanticChunking
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.reader.pdf_reader import PDFReader
from agno.vectordb.pgvector import PgVector, SearchType
from agno.db.postgres import PostgresDb

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"
embedder = OpenAIEmbedder(id="text-embedding-3-small")

vector_db = PgVector(
    table_name="recipes",
    db_url=db_url,
    embedder=embedder,
    search_type=SearchType.hybrid,
)

contents_db = PostgresDb(db_url=db_url, knowledge_table="knowledge_contents")

knowledge = Knowledge(
    name="Recipe Knowledge Base",
    description="Thai and international recipes",
    vector_db=vector_db,
    contents_db=contents_db,
    max_results=5,
)

async def setup():
    await knowledge.ainsert(
        name="Thai Recipes",
        url="https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf",
        metadata={"cuisine": "thai", "type": "recipe_book"},
        reader=PDFReader(
            chunking_strategy=SemanticChunking(
                embedder=embedder,
                similarity_threshold=0.5,
            )
        ),
        skip_if_exists=True,
    )

agent = Agent(
    name="Chef Assistant",
    model=OpenAI(id="gpt-4"),
    knowledge=knowledge,
    search_knowledge=True,
    markdown=True,
)

asyncio.run(setup())
agent.print_response("How do I make chicken and galangal in coconut milk soup?")
```

## 2. Local-Only Agent (ChromaDB + Document Chunking)

Zero-infrastructure setup using local ChromaDB:

```python
from agno.agent import Agent
from agno.knowledge.chunking.document import DocumentChunking
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.reader.pdf_reader import PDFReader
from agno.vectordb.chroma import ChromaDb

knowledge = Knowledge(
    vector_db=ChromaDb(collection="local_docs", path="tmp/chromadb", persistent_client=True),
)

knowledge.insert(
    path="company_docs/",
    reader=PDFReader(chunking_strategy=DocumentChunking()),
    skip_if_exists=True,
)

agent = Agent(knowledge=knowledge, search_knowledge=True, markdown=True)
agent.print_response("Summarize our onboarding process")
```

## 3. Multi-Format Knowledge Agent

Loading PDFs, CSVs, and websites in parallel with metadata:

```python
import asyncio
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.reader.pdf_reader import PDFReader
from agno.knowledge.reader.csv_reader import CSVReader
from agno.knowledge.reader.website_reader import WebsiteReader
from agno.vectordb.pgvector import PgVector, SearchType

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

knowledge = Knowledge(
    vector_db=PgVector(table_name="multi_format", db_url=db_url, search_type=SearchType.hybrid),
)

async def load_all():
    await asyncio.gather(
        knowledge.ainsert(path="docs/policies/", reader=PDFReader(), metadata={"type": "policy"}),
        knowledge.ainsert(path="data/employees.csv", reader=CSVReader(), metadata={"type": "data"}),
        knowledge.ainsert(
            url="https://company.com/docs",
            reader=WebsiteReader(max_depth=2, max_links=10),
            metadata={"type": "web"},
        ),
    )

asyncio.run(load_all())

agent = Agent(
    knowledge=knowledge,
    search_knowledge=True,
    enable_agentic_knowledge_filters=True,
    instructions=["Search knowledge before answering", "Cite sources"],
)
```

## 4. Metadata Filtering Agent

Department-scoped knowledge with rich metadata:

```python
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.pgvector import PgVector
from agno.db.postgres import PostgresDb

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

knowledge = Knowledge(
    vector_db=PgVector(table_name="filtered_docs", db_url=db_url),
    contents_db=PostgresDb(db_url=db_url, knowledge_table="knowledge_contents"),
)

# Load with rich metadata
knowledge.insert(path="hr_policies/", metadata={"department": "hr", "type": "policy", "year": 2025})
knowledge.insert(path="eng_runbooks/", metadata={"department": "engineering", "type": "runbook", "year": 2025})

# Agent scoped to HR
hr_agent = Agent(
    knowledge=knowledge,
    search_knowledge=True,
    knowledge_filters={"department": "hr"},
)

# Agent with agentic filtering (auto-infers)
smart_agent = Agent(
    knowledge=knowledge,
    search_knowledge=True,
    enable_agentic_knowledge_filters=True,
)
```

## 5. Gemini + ChromaDB Quick Start

```python
from agno.agent import Agent
from agno.knowledge.embedder.google import GeminiEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.models.google import Gemini
from agno.vectordb.chroma import ChromaDb
from agno.vectordb.search import SearchType

knowledge = Knowledge(
    vector_db=ChromaDb(
        collection="docs",
        path="tmp/chromadb",
        persistent_client=True,
        search_type=SearchType.hybrid,
        embedder=GeminiEmbedder(id="gemini-embedding-001"),
    ),
)
knowledge.insert(url="https://docs.agno.com/introduction.md", skip_if_exists=True)

agent = Agent(
    model=Gemini(id="gemini-3-flash-preview"),
    knowledge=knowledge,
    search_knowledge=True,
    markdown=True,
)
agent.print_response("What is Agno?", stream=True)
```

## 6. Knowledge with Tools (save learnings back)

```python
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge

knowledge = Knowledge(vector_db=vector_db)

def save_learning(title: str, insight: str) -> str:
    """Save a new learning to the knowledge base."""
    knowledge.insert(name=title, text_content=insight)
    return f"Saved: {title}"

agent = Agent(
    knowledge=knowledge,
    search_knowledge=True,
    tools=[save_learning],
)
```

---

## Performance Optimization

### 1. Skip reprocessing
```python
knowledge.insert(path="documents/", skip_if_exists=True)
```

### 2. Async batch loading
```python
await asyncio.gather(
    knowledge.ainsert(path="docs/hr/"),
    knowledge.ainsert(path="docs/engineering/"),
    knowledge.ainsert(url="https://company.com/api-docs"),
)
```

### 3. Enable hybrid search + reranking
```python
from agno.knowledge.reranker.cohere import CohereReranker

vector_db = PgVector(
    table_name="docs", db_url=db_url,
    search_type=SearchType.hybrid,
    reranker=CohereReranker(model="rerank-v3.5", top_n=10),
)
```

### 4. Reduce embedding dimensions
```python
embedder = OpenAIEmbedder(id="text-embedding-3-large", dimensions=1024)  # instead of 3072
```

### 5. Use metadata filters to narrow search
```python
results = knowledge.search(query="deployment", filters={"department": "engineering", "type": "procedure"})
```

### 6. Debug search quality
```python
results = knowledge.search("your query", max_results=10)
for doc in results:
    print(doc.content[:200])
```

### 7. Monitor processing status
```python
content_list, total = knowledge.get_content()
for content in content_list:
    if content.status == "failed":
        print(f"Failed: {content.name} — {content.status_message}")
```

### 8. Test search quality before deploying
```python
test_queries = [
    "What's our vacation policy?",
    "How do I submit expenses?",
    "Remote work guidelines",
]
for query in test_queries:
    results = knowledge.search(query)
    print(f"{query} -> {results[0].content[:100]}..." if results else "No results")
```
