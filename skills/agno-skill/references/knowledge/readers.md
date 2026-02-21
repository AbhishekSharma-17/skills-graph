# Readers

Readers extract text from different file formats. Pass via `knowledge.insert(reader=...)` or let auto-detection handle it.

## PDF Reader

```python
from agno.knowledge.reader.pdf_reader import PDFReader

reader = PDFReader(
    chunk=True,                          # Enable chunking
    chunk_size=5000,                     # Characters per chunk
    chunking_strategy=None,              # Custom chunker (overrides chunk_size)
    password=None,                       # For encrypted PDFs
    read_images=False,                   # OCR for images in PDF
    split_on_pages=False,                # One document per page
    encoding="utf-8",
    name=None,                           # Override reader name
)
```

Usage:
```python
# With knowledge
knowledge.insert(path="docs/handbook.pdf", reader=PDFReader(chunk_size=3000))

# Standalone
documents = reader.read("company_handbook.pdf")
```

## CSV Reader

```python
from agno.knowledge.reader.csv_reader import CSVReader

reader = CSVReader(
    chunk=True,
    chunk_size=5000,
    chunking_strategy=None,
    encoding="utf-8",
)
```

## Markdown Reader

```python
from agno.knowledge.reader.markdown_reader import MarkdownReader

reader = MarkdownReader(
    chunk=True,
    chunk_size=5000,
    chunking_strategy=None,
)
```

## JSON Reader

```python
from agno.knowledge.reader.json_reader import JSONReader

reader = JSONReader(
    chunk=True,
    chunk_size=5000,
)
```

## Text Reader

```python
from agno.knowledge.reader.text_reader import TextReader

reader = TextReader(
    chunk=True,
    chunk_size=5000,
)
```

## PowerPoint Reader

```python
from agno.knowledge.reader.pptx_reader import PPTXReader

reader = PPTXReader(
    chunk=True,
    chunk_size=5000,
)
```

## Website Reader (web crawling)

```python
from agno.knowledge.reader.website_reader import WebsiteReader

reader = WebsiteReader(
    max_depth=2,                         # Crawl depth
    max_links=10,                        # Max pages to crawl
)

knowledge.insert(url="https://company.com/docs", reader=reader, metadata={"type": "web"})
```

## YouTube Reader

```python
from agno.knowledge.reader.youtube_reader import YouTubeReader

reader = YouTubeReader()
knowledge.insert(url="https://youtube.com/watch?v=...", reader=reader)
```

## ArXiv Reader

```python
from agno.knowledge.reader.arxiv_reader import ArxivReader

reader = ArxivReader()
knowledge.insert(url="https://arxiv.org/abs/2301.00001", reader=reader)
```

## Wikipedia Reader

```python
from agno.knowledge.reader.wikipedia_reader import WikipediaReader

reader = WikipediaReader()
knowledge.insert(url="https://en.wikipedia.org/wiki/Artificial_intelligence", reader=reader)
```

## Firecrawl Reader (advanced web scraping)

```python
from agno.knowledge.reader.firecrawl_reader import FirecrawlReader

reader = FirecrawlReader()  # Needs FIRECRAWL_API_KEY env
```

## Reader Factory (auto-detection)

```python
from agno.knowledge.reader.reader_factory import ReaderFactory

reader = ReaderFactory.get_reader_for_extension(".pdf")    # → PDFReader
reader = ReaderFactory.get_reader_for_extension(".csv")    # → CSVReader
reader = ReaderFactory.get_reader_for_url("https://youtube.com/watch?v=...")  # → YouTubeReader
```

When you call `knowledge.insert(path=...)` without a reader, Agno auto-detects the reader from the file extension.

## Custom Reader with Chunking Strategy

```python
from agno.knowledge.reader.pdf_reader import PDFReader
from agno.knowledge.chunking.semantic_chunking import SemanticChunking

reader = PDFReader(
    chunking_strategy=SemanticChunking(similarity_threshold=0.5),
)

knowledge.insert(path="documents/", reader=reader)
```

## Async Processing

```python
import asyncio

# Single file
documents = await reader.async_read("file.pdf")

# Batch async
tasks = [reader.async_read(f) for f in file_list]
all_docs = await asyncio.gather(*tasks)
```

## Document Output Structure

All readers produce `Document` objects:

```python
Document(
    content="The extracted text...",
    id="unique_id",
    name="document_name",
    meta_data={"page": 1, "source": "handbook.pdf"},
)
```

## All Supported Readers

| Reader | Import | Use For |
|--------|--------|---------|
| PDFReader | `agno.knowledge.reader.pdf_reader` | PDF documents |
| TextReader | `agno.knowledge.reader.text_reader` | Plain text files |
| MarkdownReader | `agno.knowledge.reader.markdown_reader` | Markdown files |
| CSVReader | `agno.knowledge.reader.csv_reader` | CSV data |
| FieldLabeledCSVReader | `agno.knowledge.reader.csv_reader` | CSV with field labels |
| JSONReader | `agno.knowledge.reader.json_reader` | JSON files |
| PPTXReader | `agno.knowledge.reader.pptx_reader` | PowerPoint presentations |
| ArxivReader | `agno.knowledge.reader.arxiv_reader` | Academic papers |
| WikipediaReader | `agno.knowledge.reader.wikipedia_reader` | Wikipedia articles |
| YouTubeReader | `agno.knowledge.reader.youtube_reader` | YouTube transcripts |
| WebsiteReader | `agno.knowledge.reader.website_reader` | Web crawling |
| WebSearchReader | `agno.knowledge.reader.web_search_reader` | Web search results |
| FirecrawlReader | `agno.knowledge.reader.firecrawl_reader` | Advanced web scraping |
