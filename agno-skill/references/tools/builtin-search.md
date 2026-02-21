# Search Toolkits

Pre-built toolkits for web search, academic research, and content discovery.

## DuckDuckGo

Free web search with no API key required.

```bash
uv pip install -U ddgs
```

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.tools.duckduckgo import DuckDuckGoTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[DuckDuckGoTools()],
    show_tool_calls=True,
    markdown=True,
)
agent.print_response("What's happening in AI today?", stream=True)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_search` | `bool` | `True` | Enable web search |
| `enable_news` | `bool` | `True` | Enable news search |
| `modifier` | `str` | `None` | Search modifier (e.g., site:example.com) |
| `fixed_max_results` | `int` | `None` | Override max results |
| `proxy` | `str` | `None` | Proxy URL |
| `timeout` | `int` | `10` | Request timeout in seconds |
| `verify_ssl` | `bool` | `True` | Verify SSL certificates |

**Functions:** `web_search`, `search_news`

---

## Tavily

AI-optimized search engine with structured results.

```bash
uv pip install -U tavily-python
export TAVILY_API_KEY=your_key
```

```python
from agno.tools.tavily import TavilyTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[TavilyTools()],
    show_tool_calls=True,
)
agent.print_response("Summarize the latest developments in quantum computing")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | `str` | env var | Tavily API key |
| `enable_search` | `bool` | `True` | Enable web search |
| `enable_search_context` | `bool` | `False` | Enable search context |
| `search_depth` | `str` | `"basic"` | `"basic"` or `"advanced"` |
| `format` | `str` | `"json"` | `"json"` or `"markdown"` |
| `max_tokens` | `int` | `6000` | Max response tokens |
| `include_answer` | `bool` | `True` | Include AI-generated answer |

**Functions:** `web_search_using_tavily`, `web_search_with_tavily`

---

## Exa

Neural search with content retrieval and similarity finding.

```bash
uv pip install -U exa-py
export EXA_API_KEY=your_key
```

```python
from agno.tools.exa import ExaTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[ExaTools(
        enable_search=True,
        enable_get_contents=True,
        enable_find_similar=True,
        enable_answer=True,
    )],
)
agent.print_response("Find recent research papers on multimodal AI")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_search` | `bool` | `True` | Enable neural search |
| `enable_get_contents` | `bool` | `False` | Retrieve full content from URLs |
| `enable_find_similar` | `bool` | `False` | Find similar content to a URL |
| `enable_answer` | `bool` | `False` | AI-powered answers from search |
| `text_length_limit` | `int` | `1000` | Max text length per result |
| `num_results` | `int` | `None` | Number of results |
| `livecrawl` | `str` | `"always"` | Live crawl policy |
| `category` | `str` | `None` | Filter: company, research paper, news, pdf, github, tweet |
| `include_domains` | `list[str]` | `None` | Only search these domains |
| `exclude_domains` | `list[str]` | `None` | Exclude these domains |
| `model` | `str` | `None` | `"exa"` or `"exa-pro"` |

**Functions:** `search_exa`, `get_contents`, `find_similar`, `exa_answer`

---

## ArXiv

Search and download academic papers from ArXiv.

```bash
uv pip install -U arxiv pypdf
```

```python
from agno.tools.arxiv import ArxivTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[ArxivTools()],
)
agent.print_response("Find recent papers on transformer architectures")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_search_arxiv` | `bool` | `True` | Enable search |
| `enable_read_arxiv_papers` | `bool` | `True` | Enable paper reading |
| `download_dir` | `Path` | `None` | Download directory for PDFs |

**Functions:** `search_arxiv`, `search_arxiv_and_update_knowledge_base`

---

## Wikipedia

Search and read Wikipedia articles with optional knowledge base integration.

```python
from agno.tools.wikipedia import WikipediaTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[WikipediaTools()],
)
agent.print_response("Tell me about the history of quantum computing")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_search_wikipedia` | `bool` | `True` | Enable search |
| `enable_search_wikipedia_and_update_knowledge_base` | `bool` | `False` | Search + add to knowledge base |
| `knowledge` | `Knowledge` | `None` | Knowledge base instance |

**Functions:** `search_wikipedia`, `search_wikipedia_and_update_knowledge_base`

---

## HackerNews

Access trending stories, discussions, and user submissions.

```python
from agno.tools.hackernews import HackerNewsTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[HackerNewsTools()],
)
agent.print_response("What are the top stories on HackerNews?")
```

**Functions:** `get_top_hackernews_stories`, `get_hackernews_user`

---

## Other Search Toolkits

| Toolkit | Import | Install | Key |
|---------|--------|---------|-----|
| SerpAPI | `from agno.tools.serpapi import SerpApiTools` | `uv pip install google-search-results` | `SERPAPI_API_KEY` |
| SerperAPI | `from agno.tools.serper import SerperApiTools` | `uv pip install serper` | `SERPER_API_KEY` |
| Pubmed | `from agno.tools.pubmed import PubmedTools` | `uv pip install xmltodict` | — |
| BaiduSearch | `from agno.tools.baidu_search import BaiduSearchTools` | — | — |
| SearxNG | `from agno.tools.searxng import SearxNGTools` | — | — |
| Linkup | `from agno.tools.linkup import LinkupTools` | `uv pip install linkup-sdk` | `LINKUP_API_KEY` |
| Valyu | `from agno.tools.valyu import ValyuTools` | `uv pip install valyu` | `VALYU_API_KEY` |
