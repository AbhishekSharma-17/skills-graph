# Haystack Converters & Preprocessors

> Source: [docs.haystack.deepset.ai/docs/converters](https://docs.haystack.deepset.ai/docs/converters) | haystack-ai 2.30.0

## Table of Contents

- [Overview](#overview)
- [File Converters](#file-converters)
- [Multi-Format Conversion](#multi-format-conversion)
- [DocumentCleaner](#documentcleaner)
- [DocumentSplitter](#documentsplitter)
- [DocumentWriter](#documentwriter)
- [Building an Indexing Pipeline](#building-an-indexing-pipeline)
- [Advanced Splitting Strategies](#advanced-splitting-strategies)
- [Common Pitfalls](#common-pitfalls)

## Overview

Document processing in Haystack follows a three-stage pipeline:

```
Raw Files → Converters → Preprocessors → Document Store
              ↓              ↓
         Convert to      Clean, split,
         Document         prepare
         objects
```

1. **Converters** — extract content from files (PDF, HTML, DOCX, etc.) into `Document` objects
2. **Preprocessors** — clean and split documents into optimal chunks
3. **Writers** — persist documents into a Document Store

## File Converters

### Built-in Converters

| Converter | Input Format | Package |
|-----------|-------------|---------|
| `PyPDFToDocument` | PDF | built-in |
| `HTMLToDocument` | HTML | built-in |
| `MarkdownToDocument` | Markdown | built-in |
| `TextFileToDocument` | Plain text | built-in |
| `CSVToDocument` | CSV | built-in |
| `DOCXToDocument` | Word (.docx) | built-in |
| `PPTXToDocument` | PowerPoint (.pptx) | built-in |
| `XLSXToDocument` | Excel (.xlsx) | built-in |
| `JSONConverter` | JSON | built-in |

### Integration Converters

| Converter | Input Format | Package |
|-----------|-------------|---------|
| `PDFMinerToDocument` | PDF (better extraction) | built-in |
| `AmazonTextractConverter` | Images/PDFs (OCR) | `amazon-bedrock-haystack` |
| `AzureOCRDocumentConverter` | Images/PDFs (OCR) | `azure-ai-haystack` |
| `MistralOCRDocumentConverter` | Images/PDFs (OCR) | `mistral-haystack` |
| `DoclingConverter` | Multi-format (advanced) | `docling-haystack` |
| `UnstructuredFileConverter` | Multi-format | `unstructured-haystack` |
| `TikaDocumentConverter` | Multi-format | `tika-haystack` |

### Basic Usage

```python
from haystack.components.converters import PyPDFToDocument

converter = PyPDFToDocument()
result = converter.run(sources=["report.pdf"])
documents = result["documents"]

for doc in documents:
    print(f"Page: {doc.meta.get('page_number')}")
    print(f"Content: {doc.content[:100]}...")
```

### With Metadata

```python
from haystack.components.converters import TextFileToDocument

converter = TextFileToDocument()
result = converter.run(
    sources=["article.txt"],
    meta={"source": "blog", "author": "Jane"},
)
```

### Image-to-Document Converters

For OCR and image content:

```python
from haystack.components.converters import ImageFileToDocument

converter = ImageFileToDocument()  # Extracts text from images via OCR
```

For feeding images to vision models:

```python
from haystack.components.converters import (
    ImageFileToImageContent,
    PDFToImageContent,
)
```

## Multi-Format Conversion

Handle multiple file types in one pipeline:

```python
from haystack.components.routers import FileTypeRouter
from haystack.components.converters import (
    PyPDFToDocument,
    HTMLToDocument,
    MarkdownToDocument,
    TextFileToDocument,
)
from haystack.components.joiners import DocumentJoiner

pipe = Pipeline()
pipe.add_component("router", FileTypeRouter(
    mime_types=["application/pdf", "text/html", "text/markdown", "text/plain"]
))
pipe.add_component("pdf", PyPDFToDocument())
pipe.add_component("html", HTMLToDocument())
pipe.add_component("md", MarkdownToDocument())
pipe.add_component("txt", TextFileToDocument())
pipe.add_component("joiner", DocumentJoiner())

pipe.connect("router.application/pdf", "pdf")
pipe.connect("router.text/html", "html")
pipe.connect("router.text/markdown", "md")
pipe.connect("router.text/plain", "txt")
pipe.connect("pdf", "joiner")
pipe.connect("html", "joiner")
pipe.connect("md", "joiner")
pipe.connect("txt", "joiner")
```

Or use `MultiFileConverter` for a simpler approach:

```python
from haystack.components.converters import MultiFileConverter

converter = MultiFileConverter()
result = converter.run(sources=["doc.pdf", "page.html", "notes.md"])
```

## DocumentCleaner

Removes noise from document content:

```python
from haystack.components.preprocessors import DocumentCleaner

cleaner = DocumentCleaner(
    remove_empty_lines=True,
    remove_extra_whitespaces=True,
    remove_repeated_substrings=False,
    remove_substrings=None,  # list[str] of patterns to remove
    remove_regex=None,       # regex pattern to remove
    unicode_normalization="NFC",
    ascii_only=False,
)

result = cleaner.run(documents=documents)
clean_docs = result["documents"]
```

### Common Cleaning Patterns

```python
# Remove headers/footers
cleaner = DocumentCleaner(
    remove_repeated_substrings=True,  # Removes repeating headers/footers
)

# Remove specific patterns
cleaner = DocumentCleaner(
    remove_regex=r"\[.*?\]",  # Remove bracket annotations
    remove_substrings=["CONFIDENTIAL", "DRAFT"],
)
```

## DocumentSplitter

Splits documents into smaller chunks for embedding and retrieval:

```python
from haystack.components.preprocessors import DocumentSplitter

splitter = DocumentSplitter(
    split_by="word",          # How to split
    split_length=200,         # Chunk size
    split_overlap=20,         # Overlap between chunks
    split_threshold=10,       # Min size for last chunk
)

result = splitter.run(documents=documents)
chunks = result["documents"]
```

### Split Modes

| Mode | Description | Best For |
|------|-------------|----------|
| `"word"` | Split by word count | General text |
| `"sentence"` | Split by sentence boundaries | Preserving sentence coherence |
| `"page"` | Split by page breaks | PDF documents |
| `"passage"` | Split by paragraph/double newline | Well-structured text |
| `"period"` | Split by periods | Simple sentence splitting |
| `"function"` | Custom split function | Special formatting |

### Split by Sentence

```python
splitter = DocumentSplitter(
    split_by="sentence",
    split_length=5,       # 5 sentences per chunk
    split_overlap=1,      # 1 sentence overlap
    language="en",        # For sentence detection
)
```

### Split by Word with Sentence Boundaries

```python
splitter = DocumentSplitter(
    split_by="word",
    split_length=200,
    split_overlap=30,
    respect_sentence_boundary=True,  # Don't split mid-sentence
)
```

### Custom Split Function

```python
def split_by_header(text: str) -> list[str]:
    import re
    return re.split(r'\n#{1,3}\s', text)

splitter = DocumentSplitter(
    split_by="function",
    splitting_function=split_by_header,
)
```

### Metadata Propagation

Split documents inherit the parent's metadata plus:
- `split_id`: chunk index (0, 1, 2, ...)
- `split_idx_start`: character start position in original
- `source_id`: parent document's ID

## DocumentWriter

Writes documents to a Document Store:

```python
from haystack.components.writers import DocumentWriter
from haystack.document_stores.types import DuplicatePolicy

writer = DocumentWriter(
    document_store=store,
    policy=DuplicatePolicy.OVERWRITE,
)

result = writer.run(documents=documents)
print(f"Written: {result['documents_written']}")
```

## Building an Indexing Pipeline

Complete pipeline: convert → clean → split → embed → write:

```python
from haystack import Pipeline
from haystack.components.converters import PyPDFToDocument
from haystack.components.preprocessors import DocumentCleaner, DocumentSplitter
from haystack.components.embedders import OpenAIDocumentEmbedder
from haystack.components.writers import DocumentWriter

indexing = Pipeline()
indexing.add_component("converter", PyPDFToDocument())
indexing.add_component("cleaner", DocumentCleaner())
indexing.add_component("splitter", DocumentSplitter(
    split_by="word",
    split_length=200,
    split_overlap=30,
    respect_sentence_boundary=True,
))
indexing.add_component("embedder", OpenAIDocumentEmbedder())
indexing.add_component("writer", DocumentWriter(
    document_store=store,
    policy=DuplicatePolicy.OVERWRITE,
))

indexing.connect("converter", "cleaner")
indexing.connect("cleaner", "splitter")
indexing.connect("splitter", "embedder")
indexing.connect("embedder", "writer")

# Index PDF files
indexing.run({"converter": {"sources": ["report.pdf", "guide.pdf"]}})
```

## Advanced Splitting Strategies

### Sentence Window

For `SentenceWindowRetriever` — keeps surrounding context:

```python
from haystack.components.preprocessors import DocumentSplitter

# Split into individual sentences
splitter = DocumentSplitter(
    split_by="sentence",
    split_length=1,
)
```

Then use `SentenceWindowRetriever` with `window_size` to fetch surrounding sentences at query time.

### Hierarchical Splitting

Split at multiple granularities for `AutoMergingRetriever`:

```python
# Parent chunks (large)
parent_splitter = DocumentSplitter(split_by="word", split_length=500)

# Child chunks (small, for retrieval)
child_splitter = DocumentSplitter(split_by="word", split_length=100)
```

## Common Pitfalls

**Chunks too large**: Embedding models have token limits (8K for OpenAI). Split documents to fit within limits.

**Chunks too small**: Very small chunks lose context. Aim for 100-300 words per chunk for most use cases.

**No overlap**: Without overlap, information at chunk boundaries may be split across chunks and missed. Use 10-15% overlap.

**Skipping cleaning**: Raw PDF/HTML text often has noise (headers, footers, artifacts). Always clean before splitting.

**Wrong split mode for content type**: Use `"sentence"` for natural language, `"word"` for general text, `"page"` for page-structured documents.

## Related Topics

- Embedders → `08-embedders.md`
- Document Stores → `07-document-stores.md`
- RAG patterns → `11-rag-patterns.md`
