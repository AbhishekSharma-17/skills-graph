# CrewAI Memory & Knowledge

> Source: https://docs.crewai.com/en/concepts/memory

## Overview

CrewAI provides two complementary systems for giving agents access to information:
- **Memory** — Learned context from agent interactions (short-term, long-term, entity)
- **Knowledge** — Pre-loaded information sources (documents, files, databases) via RAG

## Memory System

### Unified Memory API

CrewAI uses a single `Memory` class that intelligently manages different memory types. It uses an LLM to analyze content when saving (inferring scope, categories, importance) and supports adaptive-depth recall with composite scoring.

### Memory Types

| Type | Scope | Purpose |
|------|-------|---------|
| Short-term | Single crew execution | Context within current run |
| Long-term | Across executions | Learnings that persist |
| Entity | Named entities | Facts about people, orgs, concepts |
| User | Per-user | User preferences and history |

### Enabling Memory on a Crew

```python
from crewai import Crew, Process

crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, writing_task],
    process=Process.sequential,
    memory=True,  # Enables all memory types
    embedder={
        "provider": "openai",
        "config": {
            "model": "text-embedding-3-small",
        },
    },
    verbose=True,
)
```

### Memory with Different Embedders

```python
# OpenAI embeddings
crew = Crew(
    ...,
    memory=True,
    embedder={
        "provider": "openai",
        "config": {"model": "text-embedding-3-small"},
    },
)

# Google embeddings
crew = Crew(
    ...,
    memory=True,
    embedder={
        "provider": "google",
        "config": {"model": "models/embedding-001"},
    },
)

# Ollama (local) embeddings
crew = Crew(
    ...,
    memory=True,
    embedder={
        "provider": "ollama",
        "config": {"model": "nomic-embed-text"},
    },
)
```

### Agent-Level Memory

```python
agent = Agent(
    role="Customer Support",
    goal="Help customers efficiently",
    backstory="Experienced support agent.",
    memory=True,  # Agent retains context across interactions
)
```

### Standalone Memory Usage

```python
from crewai.memory import Memory

memory = Memory(
    embedder={
        "provider": "openai",
        "config": {"model": "text-embedding-3-small"},
    }
)

# Save a memory
memory.save(
    content="The user prefers Python over JavaScript for backend work.",
    metadata={"category": "preference", "user_id": "user_123"},
)

# Recall memories
results = memory.search(
    query="What programming language does the user prefer?",
    limit=5,
)
for result in results:
    print(f"Score: {result.score}, Content: {result.content}")
```

### Memory Scopes

```python
from crewai.memory import Memory

memory = Memory(...)

# Save with scope
memory.save(
    content="Project deadline is March 15th",
    metadata={"scope": "project", "project_id": "proj_abc"},
)

# Save user-scoped memory
memory.save(
    content="User prefers concise responses",
    metadata={"scope": "user", "user_id": "user_123"},
)
```

### Resetting Memory

```bash
# CLI command to reset all memory
crewai reset-memories --all

# Reset specific types
crewai reset-memories --short
crewai reset-memories --long
crewai reset-memories --entity
```

## Knowledge System (RAG)

### Overview

Knowledge Sources provide structured ingestion of documents for retrieval-augmented generation. Agents can access relevant context from various data formats.

### Supported Knowledge Sources

| Source | Class | Formats |
|--------|-------|---------|
| Text files | `TextKnowledgeSource` | .txt, .md |
| PDF files | `PDFKnowledgeSource` | .pdf |
| CSV files | `CSVKnowledgeSource` | .csv |
| JSON files | `JSONKnowledgeSource` | .json |
| Excel files | `ExcelKnowledgeSource` | .xlsx, .xls |
| Raw strings | `StringKnowledgeSource` | In-memory text |

### Adding Knowledge to a Crew

```python
from crewai import Agent, Task, Crew, Process
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource

# Create knowledge sources
product_docs = TextFileKnowledgeSource(
    file_paths=["docs/product_guide.md", "docs/faq.md"],
)

technical_specs = PDFKnowledgeSource(
    file_paths=["specs/architecture.pdf"],
)

# Agent with knowledge
support_agent = Agent(
    role="Product Support Specialist",
    goal="Answer customer questions using product documentation",
    backstory="Expert on the product with access to all documentation.",
    knowledge_sources=[product_docs, technical_specs],
)
```

### Knowledge Source Configuration

```python
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource

source = TextFileKnowledgeSource(
    file_paths=["docs/guide.md"],
    chunk_size=1000,      # Characters per chunk
    chunk_overlap=200,    # Overlap between chunks
)
```

### String Knowledge Source

```python
from crewai.knowledge.source.string_knowledge_source import StringKnowledgeSource

company_info = StringKnowledgeSource(
    content="Our company was founded in 2020. We specialize in AI solutions. "
            "Our main product is an AI-powered analytics platform.",
    metadata={"type": "company_info"},
)
```

### JSON Knowledge Source

```python
from crewai.knowledge.source.json_knowledge_source import JSONKnowledgeSource

api_docs = JSONKnowledgeSource(
    file_paths=["docs/api_reference.json"],
)
```

### CSV Knowledge Source

```python
from crewai.knowledge.source.csv_knowledge_source import CSVKnowledgeSource

customer_data = CSVKnowledgeSource(
    file_paths=["data/customers.csv"],
)
```

### Crew-Level Knowledge

```python
crew = Crew(
    agents=[support_agent, analyst],
    tasks=[support_task, analysis_task],
    process=Process.sequential,
    knowledge_sources=[product_docs, technical_specs],  # Shared across all agents
    embedder={
        "provider": "openai",
        "config": {"model": "text-embedding-3-small"},
    },
)
```

## Knowledge Storage

Knowledge is stored in ChromaDB by default. The storage layer handles:
- Chunking documents into segments
- Generating embeddings for each chunk
- Storing in vector database
- Semantic search at query time

### Custom Storage Configuration

```python
crew = Crew(
    ...,
    knowledge_sources=[product_docs],
    embedder={
        "provider": "openai",
        "config": {
            "model": "text-embedding-3-small",
            "api_key": "sk-...",
        },
    },
)
```

## Memory + Knowledge Together

```python
crew = Crew(
    agents=[support_agent],
    tasks=[support_task],
    process=Process.sequential,
    memory=True,              # Learns from interactions
    knowledge_sources=[docs], # Has reference material
    embedder={
        "provider": "openai",
        "config": {"model": "text-embedding-3-small"},
    },
)
```

## Common Pitfalls

1. **No embedder configured** — Memory and knowledge require an embedder
2. **Huge documents without chunking** — Large files need proper chunk_size
3. **Forgetting to reset memory in dev** — Stale memory from prior runs confuses agents
4. **Over-relying on memory** — Memory is probabilistic; critical facts belong in task descriptions
5. **Wrong embedding model** — Match embedder to your language (multilingual models for non-English)
