# Loading Data

> Source: [developers.llamaindex.ai — Loading](https://developers.llamaindex.ai/python/framework/module_guides/loading/) | Version: 0.14.22

## Table of Contents
- [Overview](#overview)
- [Documents and Nodes](#documents-and-nodes)
- [SimpleDirectoryReader](#simpledirectoryreader)
- [LlamaHub Readers](#llamahub-readers)
- [Creating Documents Manually](#creating-documents-manually)
- [Node Parsers and Text Splitters](#node-parsers-and-text-splitters)
- [Metadata Extraction](#metadata-extraction)
- [LlamaParse](#llamaparse)
- [Common Patterns](#common-patterns)

## Overview

Loading is the first stage of the RAG pipeline. LlamaIndex ingests data from diverse sources into `Document` objects, then transforms them into `Node` objects — the atomic units used for indexing and retrieval.

```
Data Sources → Readers → Documents → Transformations → Nodes → Index
```

## Documents and Nodes

### Document

A `Document` is a container for data from a single source, holding text content and metadata:

```python
from llama_index.core import Document

doc = Document(
    text="LlamaIndex is an AI framework.",
    metadata={"source": "manual", "author": "team"},
    doc_id="doc-001",
)
```

Key attributes:
- `text` — The content string
- `metadata` — Dict of key-value pairs carried through to retrieval
- `doc_id` — Unique identifier (auto-generated if not provided)
- `excluded_llm_metadata_keys` — Metadata keys hidden from LLM context
- `excluded_embed_metadata_keys` — Metadata keys excluded from embeddings

### Node (TextNode)

A `Node` is a chunk of a Document with relationships to other nodes:

```python
from llama_index.core.schema import TextNode, NodeRelationship, RelatedNodeInfo

node = TextNode(
    text="A chunk of text.",
    id_="node-001",
    metadata={"section": "intro"},
)

node.relationships[NodeRelationship.PARENT] = RelatedNodeInfo(
    node_id="doc-001"
)
```

Relationships track parent documents, previous/next nodes, and child nodes for hierarchical retrieval.

## SimpleDirectoryReader

The built-in reader for loading files from a local directory:

```python
from llama_index.core import SimpleDirectoryReader

# Load all supported files from a directory
documents = SimpleDirectoryReader("./data").load_data()

# Load specific files
documents = SimpleDirectoryReader(
    input_files=["./report.pdf", "./notes.txt"]
).load_data()

# Recursive loading with file filtering
documents = SimpleDirectoryReader(
    input_dir="./data",
    recursive=True,
    required_exts=[".pdf", ".md", ".txt"],
    exclude=["*.tmp"],
).load_data()
```

Supported file types include: `.pdf`, `.docx`, `.pptx`, `.txt`, `.md`, `.csv`, `.epub`, `.html`, `.jpg`, `.png`, and more via `llama-index-readers-file`.

Key parameters:
- `input_dir` — Directory path to read from
- `input_files` — List of specific file paths
- `recursive` — Whether to recurse into subdirectories
- `required_exts` — Only load files with these extensions
- `exclude` — Glob patterns to exclude
- `filename_as_id` — Use filename as document ID
- `file_metadata` — Callable that returns metadata dict for each file path

### Custom Metadata per File

```python
def get_meta(file_path: str) -> dict:
    return {"file_name": file_path, "category": "research"}

reader = SimpleDirectoryReader("./data", file_metadata=get_meta)
documents = reader.load_data()
```

## LlamaHub Readers

[LlamaHub](https://llamahub.ai/) provides 100+ data connectors for diverse sources:

```bash
pip install llama-index-readers-web
pip install llama-index-readers-database
pip install llama-index-readers-notion
```

### Web Page Reader

```python
from llama_index.readers.web import SimpleWebPageReader

reader = SimpleWebPageReader()
documents = reader.load_data(urls=["https://example.com/docs"])
```

### Database Reader

```python
from llama_index.readers.database import DatabaseReader

reader = DatabaseReader(uri="postgresql://user:pass@localhost/db")
documents = reader.load_data(query="SELECT text, title FROM articles")
```

### Notion Reader

```python
from llama_index.readers.notion import NotionPageReader

reader = NotionPageReader(integration_token="secret_...")
documents = reader.load_data(page_ids=["page-id-1", "page-id-2"])
```

### Popular Readers

| Reader | Package | Source |
|--------|---------|--------|
| `SimpleWebPageReader` | `llama-index-readers-web` | Web pages |
| `DatabaseReader` | `llama-index-readers-database` | SQL databases |
| `NotionPageReader` | `llama-index-readers-notion` | Notion pages |
| `SlackReader` | `llama-index-readers-slack` | Slack channels |
| `GoogleDocsReader` | `llama-index-readers-google` | Google Docs |
| `GithubRepositoryReader` | `llama-index-readers-github` | GitHub repos |
| `WikipediaReader` | `llama-index-readers-wikipedia` | Wikipedia |
| `S3Reader` | `llama-index-readers-s3` | AWS S3 files |

## Creating Documents Manually

Build documents from any data source:

```python
from llama_index.core import Document

docs = [
    Document(
        text="Product A: high-performance widget for enterprise use.",
        metadata={"category": "enterprise", "product_id": "A001"},
    ),
    Document(
        text="Product B: budget-friendly option for small teams.",
        metadata={"category": "smb", "product_id": "B002"},
    ),
]
```

### From DataFrames

```python
import pandas as pd
from llama_index.core import Document

df = pd.read_csv("data.csv")
documents = [
    Document(
        text=row["content"],
        metadata={"title": row["title"], "date": row["date"]},
    )
    for _, row in df.iterrows()
]
```

## Node Parsers and Text Splitters

Transform Documents into Nodes with configurable chunking:

### SentenceSplitter (recommended default)

```python
from llama_index.core.node_parser import SentenceSplitter

splitter = SentenceSplitter(
    chunk_size=1024,
    chunk_overlap=20,
)
nodes = splitter.get_nodes_from_documents(documents)
```

### TokenTextSplitter

```python
from llama_index.core.node_parser import TokenTextSplitter

splitter = TokenTextSplitter(
    chunk_size=1024,
    chunk_overlap=20,
    separator=" ",
)
```

### Specialized Parsers

| Parser | Use Case |
|--------|----------|
| `SentenceSplitter` | General text, respects sentence boundaries |
| `TokenTextSplitter` | Fixed token-length chunks |
| `HTMLNodeParser` | HTML documents, preserves structure |
| `JSONNodeParser` | JSON data, preserves hierarchy |
| `MarkdownNodeParser` | Markdown files, splits by headers |
| `CodeSplitter` | Source code, respects language syntax |
| `SentenceWindowNodeParser` | Creates nodes with surrounding context window |
| `HierarchicalNodeParser` | Multi-level chunking for auto-merging retrieval |

### Global Configuration

```python
from llama_index.core import Settings
Settings.chunk_size = 1024
Settings.chunk_overlap = 20
```

## Metadata Extraction

Automatically extract metadata from document content:

```python
from llama_index.core.extractors import (
    TitleExtractor,
    SummaryExtractor,
    QuestionsAnsweredExtractor,
    KeywordExtractor,
)
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter

pipeline = IngestionPipeline(
    transformations=[
        SentenceSplitter(chunk_size=512),
        TitleExtractor(nodes=5),
        SummaryExtractor(summaries=["self"]),
        KeywordExtractor(keywords=10),
    ]
)
nodes = pipeline.run(documents=documents)
```

Extractors add metadata keys like `document_title`, `section_summary`, `excerpt_keywords` to each node automatically.

## LlamaParse

LlamaIndex's managed document parsing API for complex documents (PDFs with tables, charts, images):

```bash
pip install llama-index-readers-llama-parse
```

```python
from llama_parse import LlamaParse

parser = LlamaParse(
    api_key="llx-...",
    result_type="markdown",
)
documents = parser.load_data("./complex-report.pdf")
```

LlamaParse handles:
- Multi-column layouts
- Tables with merged cells
- Charts and figures
- Headers and footers
- Mathematical notation

## Common Patterns

### Loading with Progress

```python
documents = SimpleDirectoryReader("./data").load_data(show_progress=True)
```

### Filtering Metadata at Query Time

```python
doc = Document(
    text="Sensitive internal data...",
    metadata={"source": "internal", "dept": "finance"},
    excluded_llm_metadata_keys=["dept"],
    excluded_embed_metadata_keys=["source"],
)
```

### Combining Multiple Sources

```python
from llama_index.core import SimpleDirectoryReader
from llama_index.readers.web import SimpleWebPageReader

file_docs = SimpleDirectoryReader("./docs").load_data()
web_docs = SimpleWebPageReader().load_data(urls=["https://example.com"])
all_docs = file_docs + web_docs
```
