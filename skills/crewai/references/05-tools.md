# CrewAI Tools

> Source: https://docs.crewai.com/en/concepts/tools

## Overview

Tools empower agents with capabilities beyond text generation — web searching, file operations, code execution, API calls, and more. CrewAI provides built-in tools and supports custom tool creation via class-based or decorator-based approaches.

## Built-in Tools (crewai-tools)

```bash
pip install 'crewai[tools]'
```

| Tool | Purpose |
|------|---------|
| `SerperDevTool` | Google search via Serper API |
| `WebsiteSearchTool` | Search within a specific website |
| `ScrapeWebsiteTool` | Scrape webpage content |
| `FileReadTool` | Read file contents |
| `FileWriterTool` | Write content to files |
| `DirectoryReadTool` | List directory contents |
| `PDFSearchTool` | Search within PDF documents |
| `DOCXSearchTool` | Search within DOCX files |
| `CSVSearchTool` | Search within CSV files |
| `JSONSearchTool` | Search within JSON files |
| `CodeInterpreterTool` | Execute Python code |
| `CodeDocsSearchTool` | Search code documentation |
| `GithubSearchTool` | Search GitHub repos |
| `YoutubeVideoSearchTool` | Search YouTube videos |
| `YoutubeChannelSearchTool` | Search YouTube channels |
| `BrowserbaseLoadTool` | Browser automation |
| `ComposioTool` | Composio integrations |
| `EXASearchTool` | Exa AI search |
| `FirecrawlSearchTool` | Firecrawl web scraping |
| `FirecrawlCrawlWebsiteTool` | Crawl websites |
| `FirecrawlScrapeWebsiteTool` | Scrape with Firecrawl |
| `NL2SQLTool` | Natural language to SQL |
| `PGSearchTool` | PostgreSQL search |
| `RagTool` | RAG-based retrieval |
| `DallETool` | DALL-E image generation |
| `VisionTool` | Image analysis |

## Using Built-in Tools

```python
from crewai import Agent
from crewai_tools import SerperDevTool, ScrapeWebsiteTool, FileReadTool

# Assign tools to an agent
researcher = Agent(
    role="Web Researcher",
    goal="Find accurate information online",
    backstory="Expert at finding and verifying online information.",
    tools=[
        SerperDevTool(),
        ScrapeWebsiteTool(),
    ],
)

# Task-specific tools (override agent tools)
from crewai import Task

task = Task(
    description="Read the config file and summarize.",
    expected_output="Summary of configuration.",
    agent=researcher,
    tools=[FileReadTool(file_path="config.yaml")],  # Only this tool for this task
)
```

## Custom Tools — @tool Decorator

The simplest way to create a custom tool:

```python
from crewai.tools import tool

@tool("Search Database")
def search_database(query: str) -> str:
    """Search the internal database for relevant records."""
    # Your implementation
    results = db.search(query)
    return f"Found {len(results)} records: {results}"
```

### With Multiple Parameters

```python
@tool("Calculate Metrics")
def calculate_metrics(metric_name: str, start_date: str, end_date: str) -> str:
    """Calculate business metrics for a given date range."""
    # Implementation
    value = compute_metric(metric_name, start_date, end_date)
    return f"{metric_name} from {start_date} to {end_date}: {value}"
```

### Async Tool

```python
@tool("Async API Call")
async def fetch_data(endpoint: str) -> str:
    """Fetch data from external API asynchronously."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/{endpoint}")
        return response.text
```

## Custom Tools — BaseTool Class

For more control, use the class-based approach:

```python
from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class SearchInput(BaseModel):
    """Input schema for DatabaseSearchTool."""
    query: str = Field(..., description="Search query string")
    limit: int = Field(default=10, description="Max results to return")
    category: str | None = Field(default=None, description="Filter by category")

class DatabaseSearchTool(BaseTool):
    name: str = "Database Search"
    description: str = (
        "Search the product database. Use this when you need to find "
        "products by name, category, or description."
    )
    args_schema: Type[BaseModel] = SearchInput

    def _run(self, query: str, limit: int = 10, category: str | None = None) -> str:
        results = self._search(query, limit, category)
        return f"Found {len(results)} products:\n" + "\n".join(
            f"- {r['name']}: {r['price']}" for r in results
        )

    def _search(self, query, limit, category):
        # Your database logic
        ...
```

### BaseTool with Caching

```python
class ExpensiveAPITool(BaseTool):
    name: str = "Expensive API"
    description: str = "Call an expensive external API"
    cache_function: callable = lambda self, args, result: True  # Always cache

    def _run(self, query: str) -> str:
        # Only called once per unique input
        return expensive_api_call(query)
```

### BaseTool with Custom Cache Logic

```python
class WeatherTool(BaseTool):
    name: str = "Weather Lookup"
    description: str = "Get current weather for a location"

    def cache_function(self, args: dict, result: str) -> bool:
        # Only cache if result was successful
        return "error" not in result.lower()

    def _run(self, location: str) -> str:
        return get_weather(location)
```

## Tool with Error Handling

```python
from crewai.tools import tool

@tool("Safe API Call")
def safe_api_call(endpoint: str) -> str:
    """Call external API with error handling."""
    try:
        response = requests.get(endpoint, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.Timeout:
        return "Error: API request timed out after 30 seconds"
    except requests.HTTPError as e:
        return f"Error: API returned status {e.response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"
```

## Structured Tool with Context

```python
class AnalysisTool(BaseTool):
    name: str = "Data Analysis"
    description: str = "Perform statistical analysis on datasets"
    
    # Instance attributes for state
    data_path: str = ""
    
    def __init__(self, data_path: str):
        super().__init__()
        self.data_path = data_path

    def _run(self, analysis_type: str) -> str:
        import pandas as pd
        df = pd.read_csv(self.data_path)
        if analysis_type == "summary":
            return str(df.describe())
        elif analysis_type == "correlations":
            return str(df.corr())
        return "Unknown analysis type"

# Usage
tool = AnalysisTool(data_path="data/sales.csv")
agent = Agent(role="Analyst", goal="...", backstory="...", tools=[tool])
```

## Tool Result Caching

```python
from crewai import Crew

crew = Crew(
    agents=[researcher],
    tasks=[research_task],
    cache=True,  # Enable crew-level caching (default)
)
```

Agent-level caching:

```python
agent = Agent(
    role="Researcher",
    goal="...",
    backstory="...",
    cache=True,  # Enable for this agent
    tools=[SerperDevTool()],
)
```

## Composio Integration

```python
from composio_crewai import ComposioToolSet, App

toolset = ComposioToolSet()
gmail_tools = toolset.get_tools(apps=[App.GMAIL])
slack_tools = toolset.get_tools(apps=[App.SLACK])

agent = Agent(
    role="Communication Manager",
    goal="Handle all team communications",
    backstory="Expert at managing emails and messages.",
    tools=gmail_tools + slack_tools,
)
```

## Common Pitfalls

1. **Vague tool descriptions** — LLM uses description to decide when to call; be specific
2. **Too many tools per agent** — 5-7 max; more causes confusion
3. **Missing error handling** — Tools that crash break the agent loop
4. **Not caching expensive calls** — Repeated API calls waste money and time
5. **Wrong args_schema types** — Use str for most params; agents struggle with complex types
6. **Forgetting the docstring** — @tool decorator uses the docstring as tool description
