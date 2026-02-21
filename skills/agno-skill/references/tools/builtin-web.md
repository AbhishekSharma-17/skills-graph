# Web Scraping Toolkits

Pre-built toolkits for crawling, scraping, and extracting content from web pages.

## Firecrawl

Cloud-based web scraping with crawling, mapping, and search capabilities.

```bash
uv pip install -U firecrawl-py
export FIRECRAWL_API_KEY=your_key
```

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.tools.firecrawl import FirecrawlTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[FirecrawlTools(
        enable_scrape=True,
        enable_crawl=True,
        enable_mapping=True,
        enable_search=True,
    )],
    show_tool_calls=True,
)
agent.print_response("Scrape the pricing page of example.com")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | `str` | env var | Firecrawl API key |
| `enable_scrape` | `bool` | `True` | Scrape single pages |
| `enable_crawl` | `bool` | `False` | Crawl multi-page sites |
| `enable_mapping` | `bool` | `False` | Map site structure |
| `enable_search` | `bool` | `False` | Search web content |
| `limit` | `int` | `10` | Max pages to crawl |
| `poll_interval` | `int` | `30` | Crawl poll interval (seconds) |
| `api_url` | `str` | `"https://api.firecrawl.dev"` | API base URL |

**Functions:** `scrape_website`, `crawl_website`, `map_website`, `search`

---

## Crawl4AI

Open-source web crawler with pruning and headless browser support.

```bash
uv pip install -U crawl4ai
```

```python
from agno.tools.crawl4ai import Crawl4AITools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[Crawl4AITools(max_length=2000)],
)
agent.print_response("Crawl https://docs.agno.com and summarize the content")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_length` | `int` | `1000` | Max content length |
| `timeout` | `int` | `60` | Request timeout (seconds) |
| `use_pruning` | `bool` | `False` | Enable content pruning |
| `pruning_threshold` | `float` | `0.48` | Pruning threshold |
| `bm25_threshold` | `float` | `1.0` | BM25 relevance threshold |
| `headless` | `bool` | `True` | Headless browser mode |
| `wait_until` | `str` | `"domcontentloaded"` | Page load wait condition |
| `enable_crawl` | `bool` | `True` | Enable crawling |

**Functions:** `web_crawler`

---

## Spider

Web search, scraping, and crawling with structured output.

```bash
uv pip install -U spider-client
```

```python
from agno.tools.spider import SpiderTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[SpiderTools()],
)
agent.print_response("Search for 'agno framework' and scrape the top result")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_results` | `int` | `None` | Max search results |
| `enable_search` | `bool` | `True` | Web search |
| `enable_scrape` | `bool` | `True` | Page scraping |
| `enable_crawl` | `bool` | `True` | Site crawling |

**Functions:** `search`, `scrape`, `crawl`

---

## Newspaper4k

Article extraction with metadata (title, authors, dates, text).

```bash
uv pip install -U newspaper4k lxml_html_clean
```

```python
from agno.tools.newspaper4k import Newspaper4kTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[Newspaper4kTools(include_summary=True)],
)
agent.print_response("Read this article: https://example.com/article")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_read_article` | `bool` | `True` | Read articles |
| `include_summary` | `bool` | `False` | Include NLP summary |
| `article_length` | `int` | `None` | Max article length |

**Functions:** `get_article_data`, `read_article`

---

## Other Web Scraping Toolkits

| Toolkit | Import | Install | Description |
|---------|--------|---------|-------------|
| Jina Reader | `from agno.tools.jina import JinaReaderTools` | — | Jina AI reader for clean text |
| AgentQL | `from agno.tools.agentql import AgentQLTools` | `uv pip install agentql` | AI-powered web scraping |
| BrowserBase | `from agno.tools.browserbase import BrowserBaseTools` | `uv pip install browserbase` | Cloud browser automation |
| Trafilatura | `from agno.tools.trafilatura import TrafilaturaTools` | `uv pip install trafilatura` | Web text extraction |
| BrightData | `from agno.tools.brightdata import BrightDataTools` | — | Proxy-based scraping |
| Website | `from agno.tools.website import WebsiteTools` | — | Basic website reading |
