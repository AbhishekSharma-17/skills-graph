# Agno Tools — Reference Router

Tools are Python functions that Agents call to interact with external systems — searching the web, running SQL, sending emails, calling APIs, etc. Agno provides 120+ pre-built toolkits and full support for custom tools.

## How Tools Work

1. Agent sends context + tool definitions to the model
2. Model responds with a tool call (or final answer)
3. Tool executes, result returns to model
4. Loop repeats until model produces a final response (no more tool calls)

Models can request **multiple tool calls** in a single response. Tools execute **concurrently** when using `arun()` or `aprint_response()`.

## Sub-References

Read only what the current task requires:

| Reference | File | Read When |
|-----------|------|-----------|
| **Creating Tools** | `references/tools/creating-tools.md` | Writing tool functions, @tool decorator, return types, ToolResult for media, Pydantic model parameters |
| **Custom Toolkits** | `references/tools/custom-toolkits.md` | Building reusable Toolkit classes, async toolkits, toolkit parameters (include/exclude tools, instructions) |
| **Advanced Patterns** | `references/tools/advanced.md` | Tool hooks (pre/post), RunContext & session state, RetryAgentRun/StopAgentRun exceptions, caching, concurrent execution, built-in params (agent, team, media) |
| **MCP Tools** | `references/tools/mcp-tools.md` | Model Context Protocol integration, transports (stdio, HTTP, SSE), connection management |
| **Search Toolkits** | `references/tools/builtin-search.md` | DuckDuckGo, Tavily, Exa, SerpAPI, ArXiv, Wikipedia, HackerNews, Pubmed, Google Search |
| **Data Toolkits** | `references/tools/builtin-data.md` | SQL, Postgres, DuckDB, CSV, Pandas, BigQuery, Redshift, Neo4j |
| **Web Scraping Toolkits** | `references/tools/builtin-web.md` | Firecrawl, Crawl4AI, Spider, Newspaper4k, Jina Reader, AgentQL, BrowserBase, Trafilatura |
| **Dev Toolkits** | `references/tools/builtin-dev.md` | GitHub, Docker, Shell, File, Python, Calculator |
| **Communication Toolkits** | `references/tools/builtin-comms.md` | Email, Slack, Discord, Telegram, Twilio, WhatsApp, Gmail, Zoom, X (Twitter) |
| **Media & AI Toolkits** | `references/tools/builtin-media.md` | DALL-E, ElevenLabs, Replicate, Fal, Giphy, Cartesia, Stability AI, OpenCV |
| **Productivity Toolkits** | `references/tools/builtin-productivity.md` | Google Calendar, Google Sheets, Notion, Linear, Jira, Todoist, Confluence, ClickUp, Shopify |

## Quick Example

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.tools.duckduckgo import DuckDuckGoTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[DuckDuckGoTools()],
    markdown=True,
)
agent.print_response("What's happening in AI today?", stream=True)
```

## Key Imports

```python
from agno.tools import tool, Toolkit          # Decorator + base class
from agno.tools.function import ToolResult    # Media returns
from agno.run import RunContext               # Session state access
from agno.exceptions import RetryAgentRun, StopAgentRun  # Control flow
from agno.media import Image, Video, Audio    # Media types
```
