# Chunking Strategies

Chunking splits documents into smaller pieces for embedding. Pass to readers via `chunking_strategy=...`.

## Fixed Size (fast, good default)

```python
from agno.knowledge.chunking.fixed_size_chunking import FixedSizeChunking

chunker = FixedSizeChunking(
    chunk_size=5000,                     # Characters per chunk
    overlap=0,                           # Overlap between chunks (chars)
)
```

Simple character-count splits. Add overlap to avoid cutting mid-sentence at chunk boundaries.

## Semantic (best quality, slower)

```python
from agno.knowledge.chunking.semantic_chunking import SemanticChunking

chunker = SemanticChunking(
    embedder=OpenAIEmbedder(),           # Embedder for similarity
    chunk_size=5000,                     # Max tokens per chunk
    similarity_threshold=0.5,            # 0-1: lower = more chunks
    similarity_window=3,                 # Sentences for comparison
    min_sentences_per_chunk=1,
    min_characters_per_sentence=24,
    delimiters=[". ", "! ", "? ", "\n"],
    include_delimiters="prev",           # "prev" | "next" | None
    skip_window=0,                       # Skip groups for merging
    filter_window=5,                     # Savitzky-Golay filter window
    filter_polyorder=3,                  # Filter polynomial order
    filter_tolerance=0.2,                # Filter tolerance
)
```

Groups sentences by semantic similarity. Produces the highest quality chunks but requires embedding calls during chunking.

## Recursive (fast, respects structure)

```python
from agno.knowledge.chunking.recursive_chunking import RecursiveChunking

chunker = RecursiveChunking(
    chunk_size=5000,
    overlap=0,
    separators=["\n\n", "\n", ". ", " "],  # Try in order
)
```

Tries the first separator, falls back to the next if chunks are too large. Good for structured text where paragraph/section boundaries matter.

## Document Chunking

```python
from agno.knowledge.chunking.document import DocumentChunking

chunker = DocumentChunking(
    chunk_size=5000,
    overlap=0,
)
```

Preserves document-level boundaries. Good when each document is a self-contained unit.

**Example:**
```python
import asyncio
from agno.agent import Agent
from agno.knowledge.chunking.document import DocumentChunking
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.reader.pdf_reader import PDFReader
from agno.vectordb.pgvector import PgVector

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"
knowledge = Knowledge(vector_db=PgVector(table_name="recipes_doc_chunking", db_url=db_url))

asyncio.run(knowledge.ainsert(
    url="https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf",
    reader=PDFReader(name="Doc Chunking Reader", chunking_strategy=DocumentChunking()),
))

agent = Agent(knowledge=knowledge, search_knowledge=True)
agent.print_response("How to make Thai curry?", markdown=True)
```

## Markdown Chunking

```python
from agno.knowledge.chunking.markdown import MarkdownChunking

chunker = MarkdownChunking(
    chunk_size=5000,
    overlap=0,
)
```

Splits on markdown headings and structure. Ideal for `.md` files.

**Example:**
```python
from agno.knowledge.reader.markdown_reader import MarkdownReader
from agno.knowledge.chunking.markdown import MarkdownChunking

reader = MarkdownReader(
    name="Markdown Chunking Reader",
    chunking_strategy=MarkdownChunking(),
)
knowledge.insert(url="https://github.com/agno-agi/agno/blob/main/README.md", reader=reader)
```

## CSV Row Chunking

```python
from agno.knowledge.chunking.row import RowChunking

chunker = RowChunking(
    rows_per_chunk=100,                  # Rows per chunk
    skip_header=False,
    clean_rows=True,
    include_header_in_chunks=False,
    max_chunk_size=5000,                 # Fallback character limit
)
```

Groups CSV rows together. Good for tabular data where each row is a record.

## Code Chunking (AST-based)

```python
from agno.knowledge.chunking.code import CodeChunking

chunker = CodeChunking()
```

Splits at function and class boundaries using AST parsing. Best for source code files.

## Custom Chunking

```python
from agno.knowledge.chunking.base import BaseChunker

class MyChunker(BaseChunker):
    def chunk(self, text: str) -> list[str]:
        # Your custom logic
        return chunks
```

## How to Use with Readers

```python
from agno.knowledge.reader.pdf_reader import PDFReader
from agno.knowledge.chunking.semantic_chunking import SemanticChunking

reader = PDFReader(
    chunking_strategy=SemanticChunking(similarity_threshold=0.5),
)
knowledge.insert(path="documents/", reader=reader)
```

## Selection Guide

| Strategy | Speed | Quality | Best For |
|----------|-------|---------|----------|
| FixedSize | Fast | Good | General use, large batches |
| Semantic | Slow | Best | High-quality retrieval, nuanced docs |
| Recursive | Fast | Good | Structured text (code, markdown, HTML) |
| Document | Fast | Good | Preserving document boundaries |
| Markdown | Fast | Good | Markdown files |
| Row | Fast | Good | CSV / tabular data |
| Code | Medium | Best | Source code files |

**Rules of thumb:**
- Start with FixedSize (chunk_size=3000-5000) for prototyping
- Switch to Semantic when retrieval quality matters
- Use Recursive for structured content (code, docs, HTML)
- Use the format-specific chunker (Markdown, Row, Code) when you know the format
- Add overlap (100-500 chars) to FixedSize or Recursive if answers span chunk boundaries
