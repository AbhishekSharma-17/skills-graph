# Tools & Toolkits

Tools are Python functions that agents call to perform actions. Agno includes 120+ pre-built toolkits and supports custom tools.

## Basic Tool (Plain Function)

Any Python function with a docstring and type hints becomes a tool:

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses

def get_weather(city: str) -> str:
    """Get the weather for the given city.

    Args:
        city (str): The city to get the weather for.
    """
    return f"The weather in {city} is sunny."

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[get_weather],
)
```

Agno auto-converts the function to a JSON schema tool definition for the model.

## @tool Decorator

```python
from agno.tools import tool

@tool(
    name="fetch_stories",               # Custom tool name
    description="Get top HN stories",   # Custom description
    stop_after_tool_call=True,           # Stop agent loop after this tool
    requires_confirmation=True,          # User must confirm before execution
    requires_user_input=True,            # Needs user input before execution
    external_execution=False,            # Executed outside agent control
    show_result=True,                    # Show output in response (default True)
    tool_hooks=[logger_hook],            # Before/after execution hooks
    cache_results=True,                  # Cache results
    cache_dir="/tmp/agno_cache",         # Cache directory
    cache_ttl=3600,                      # Cache TTL in seconds
)
def get_top_stories(num_stories: int = 5) -> str:
    """Fetch the top stories."""
    ...
```

## Pydantic Model Parameters

```python
from pydantic import BaseModel, Field

class GetWeatherRequest(BaseModel):
    city: str = Field(description="The city to get the weather for")

def get_weather(request: GetWeatherRequest) -> str:
    """Get the weather for a given city."""
    return f"The weather in {request.city} is sunny."
```

## Return Types

```python
# String
def get_weather(city: str) -> str:
    return f"Weather in {city} is sunny"

# Integer
def calculate_sum(a: int, b: int) -> int:
    return a + b

# Dict
def get_user(user_id: str) -> dict:
    return {"user_id": user_id, "name": "John"}

# List
def search_products(query: str) -> list:
    return [{"id": 1, "name": "Product A", "price": 29.99}]
```

## ToolResult (for returning media)

```python
from agno.tools.function import ToolResult
from agno.media import Image

@tool
def generate_image(prompt: str) -> ToolResult:
    """Generate image from prompt."""
    image = Image(id="img_123", url="https://example.com/image.jpg", original_prompt=prompt)
    return ToolResult(content=f"Generated image for: {prompt}", images=[image])
```

## Built-in Tool Parameters (Auto-Injected)

Declare these in your function signature and they're injected automatically:

### RunContext (session state, dependencies)

```python
from agno.run import RunContext

def add_item(run_context: RunContext, item: str) -> str:
    """Add item to shopping list."""
    run_context.session_state["shopping_list"].append(item)
    return f"Shopping list: {run_context.session_state['shopping_list']}"

agent = Agent(
    session_state={"shopping_list": []},
    tools=[add_item],
    instructions="Current state: {shopping_list}",
)
```

### Agent / Team access

```python
from agno.agent import Agent

def get_instructions(agent: Agent) -> str:
    """Get the agent's instructions."""
    return agent.instructions
```

### Media parameters

```python
from typing import Optional, List
from agno.media import Image

def process_image(images: Optional[List[Image]]) -> str:
    """Process uploaded images."""
    # images auto-injected from user input
    ...
```

## Custom Toolkits

Bundle related tools into a class:

```python
from typing import List
from agno.tools import Toolkit

class ShellTools(Toolkit):
    def __init__(self, working_directory: str = "/", **kwargs):
        self.working_directory = working_directory
        tools = [self.run_shell_command]
        super().__init__(name="shell_tools", tools=tools, **kwargs)

    def run_shell_command(self, args: List[str], tail: int = 100) -> str:
        """Runs a shell command and returns the output."""
        import subprocess
        result = subprocess.run(args, capture_output=True, text=True, cwd=self.working_directory)
        return result.stdout[-tail*80:] if result.stdout else result.stderr[-tail*80:]
```

### Async Toolkits

```python
from agno.tools import Toolkit

class APITools(Toolkit):
    def __init__(self, base_url: str, timeout: float = 30.0, **kwargs):
        self.base_url = base_url
        self.timeout = timeout
        tools = [self.fetch_data, self.post_data]
        async_tools = [
            (self.afetch_data, "fetch_data"),
            (self.apost_data, "post_data"),
        ]
        super().__init__(name="api_tools", tools=tools, async_tools=async_tools, **kwargs)

    def fetch_data(self, endpoint: str) -> dict:
        """Fetch data from an API endpoint."""
        ...

    async def afetch_data(self, endpoint: str) -> dict:
        """Fetch data asynchronously."""
        ...
```

## Concurrent Tool Execution

```python
import asyncio
from agno.agent import Agent
from agno.models.openai import OpenAIResponses

async def atask1(delay: int):
    """Task 1."""
    await asyncio.sleep(delay)
    return f"Task 1 completed in {delay}s"

async def atask2(delay: int):
    """Task 2."""
    await asyncio.sleep(delay)
    return f"Task 2 completed in {delay}s"

agent = Agent(model=OpenAIResponses(id="gpt-5.2"), tools=[atask1, atask2])
asyncio.run(agent.aprint_response("Run all tasks with delay of 3s", stream=True))
```

## Using Pre-built Toolkits

```python
from agno.agent import Agent
from agno.tools.hackernews import HackerNewsTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[HackerNewsTools()],
)
agent.print_response("What are the top stories on HackerNews?", markdown=True)
```

## Pre-built Toolkit Categories (120+)

**Search**: DuckDuckGo, Tavily, SerpAPI, Exa, Google Search, Bing
**Data**: SQL, Pandas, CSV, Snowflake, BigQuery, DynamoDB
**Communication**: Email, Slack, Discord, Telegram, Twilio
**AI/Media**: DALL-E, ElevenLabs, Replicate, Stability AI
**Web**: Firecrawl, Crawl4AI, Spider, Newspaper4k
**Dev**: GitHub, GitLab, Docker, Shell, File, Code
**Finance**: Yahoo Finance, Alpha Vantage, Financial Datasets
**Productivity**: Google Calendar, Google Sheets, Notion, Todoist, Linear
**MCP**: Model Context Protocol tools via `MCPTools`
**Misc**: Wikipedia, ArXiv, YouTube, Hacker News, Calculator, Reasoning

## MCP Tools

```python
from agno.tools.mcp import MCPTools

agent = Agent(
    tools=[MCPTools(url="https://docs.agno.com/mcp")],
)
```
