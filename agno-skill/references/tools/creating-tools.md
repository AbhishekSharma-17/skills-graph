# Creating Tools

Tools are Python functions that agents call to perform actions. Agno auto-converts function signatures + docstrings into JSON schema tool definitions for the model.

## Plain Function as Tool

Any Python function with type hints and a docstring becomes a tool:

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
agent.print_response("What is the weather in San Francisco?")
```

The function above auto-converts to this JSON schema for the model:

```json
{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get the weather for the given city.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "The city to get the weather for."}
            },
            "required": ["city"]
        }
    }
}
```

**Best practices for tool functions:**
- Always include a docstring with `Args:` section — the model uses this to understand what the tool does and what to pass
- Use descriptive function names (the model sees the name)
- Type-hint all parameters and return values
- Return strings for most cases; the model processes the return value as context

## @tool Decorator

The `@tool` decorator adds control over tool behavior:

```python
from agno.tools import tool

@tool(
    name="fetch_stories",               # Override function name
    description="Get top HN stories",   # Override docstring description
    stop_after_tool_call=True,           # Stop agent loop after execution
    requires_confirmation=True,          # User must confirm before execution
    requires_user_input=True,            # Needs user input before execution
    user_input_fields=["api_key"],       # Specific fields needing user input
    external_execution=False,            # If True, executed outside agent control
    show_result=True,                    # Show output in response (default True)
    cache_results=True,                  # Enable result caching
    cache_dir="/tmp/agno_cache",         # Cache directory
    cache_ttl=3600,                      # Cache TTL in seconds
    tool_hooks=[logger_hook],            # Hooks wrapping execution
    pre_hook=my_pre_hook,               # Hook before execution
    post_hook=my_post_hook,             # Hook after execution
)
def get_top_stories(num_stories: int = 5) -> str:
    """Fetch the top stories from Hacker News.

    Args:
        num_stories: Number of stories to fetch (default: 5)
    """
    import json, httpx
    response = httpx.get(
        "https://hacker-news.firebaseio.com/v0/topstories.json",
        params={"print": "pretty", "orderBy": '"$key"', "limitToFirst": num_stories},
    )
    stories = []
    for story_id in response.json()[:num_stories]:
        story = httpx.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json").json()
        stories.append({"title": story.get("title"), "url": story.get("url")})
    return json.dumps(stories)
```

### @tool Decorator Parameters

| Parameter | Type | Default | Purpose |
|-----------|------|---------|---------|
| `name` | `str` | function name | Override the tool name the model sees |
| `description` | `str` | docstring | Override the tool description |
| `stop_after_tool_call` | `bool` | `False` | Stop agent loop after this tool executes |
| `requires_confirmation` | `bool` | `False` | Require user confirmation before execution |
| `requires_user_input` | `bool` | `False` | Require user input before execution |
| `user_input_fields` | `list[str]` | `[]` | Specific fields needing user input |
| `external_execution` | `bool` | `False` | Tool executed outside agent control |
| `show_result` | `bool` | `True` | Show tool output in agent response |
| `cache_results` | `bool` | `False` | Enable result caching |
| `cache_dir` | `str` | `None` | Directory for cache files |
| `cache_ttl` | `int` | `3600` | Cache time-to-live in seconds |
| `tool_hooks` | `list[Callable]` | `[]` | Hooks wrapping execution |
| `pre_hook` | `Callable` | `None` | Hook to run before execution |
| `post_hook` | `Callable` | `None` | Hook to run after execution |

## Pydantic Model Parameters

For complex inputs, use a Pydantic model as the parameter:

```python
from pydantic import BaseModel, Field

class GetWeatherRequest(BaseModel):
    city: str = Field(description="The city to get the weather for")
    units: str = Field(default="celsius", description="Temperature units")

def get_weather(request: GetWeatherRequest) -> str:
    """Get the weather for a given city."""
    return f"The weather in {request.city} is 22 {request.units}"
```

Agno extracts the JSON schema from the Pydantic model, giving the model structured parameter descriptions.

## Return Types

Tools can return basic Python types — Agno serializes them for the model:

```python
# String (most common)
def get_weather(city: str) -> str:
    return f"Weather in {city} is sunny"

# Integer / Float
def calculate_sum(a: int, b: int) -> int:
    return a + b

# Dict (auto-serialized to JSON string)
def get_user(user_id: str) -> dict:
    return {"user_id": user_id, "name": "John", "email": "john@example.com"}

# List (auto-serialized to JSON string)
def search_products(query: str) -> list:
    return [{"id": 1, "name": "Product A", "price": 29.99}]
```

## ToolResult (Returning Media)

When tools generate images, videos, or audio, use `ToolResult` to return them as proper media artifacts:

```python
from agno.tools import tool
from agno.tools.function import ToolResult
from agno.media import Image, Video, Audio

@tool
def generate_image(prompt: str) -> ToolResult:
    """Generate an image from a text prompt."""
    # ... call image generation API ...
    image = Image(
        id="img_123",
        url="https://example.com/generated-image.jpg",
        original_prompt=prompt,
    )
    return ToolResult(
        content=f"Generated image for: {prompt}",
        images=[image],
    )

@tool
def generate_video(prompt: str) -> ToolResult:
    """Generate a video from a text prompt."""
    video = Video(id="vid_123", url="https://example.com/video.mp4")
    return ToolResult(content=f"Generated video for: {prompt}", videos=[video])

@tool
def synthesize_speech(text: str) -> ToolResult:
    """Convert text to speech."""
    audio = Audio(id="aud_123", url="https://example.com/speech.mp3")
    return ToolResult(content=f"Synthesized speech for: {text}", audios=[audio])
```

### ToolResult Fields

| Field | Type | Description |
|-------|------|-------------|
| `content` | `str` | Main text content/output (required) |
| `images` | `Optional[List[Image]]` | Generated image artifacts |
| `videos` | `Optional[List[Video]]` | Generated video artifacts |
| `audios` | `Optional[List[Audio]]` | Generated audio artifacts |

## Adding Tools to Agents

```python
from agno.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools

# Mix plain functions, decorated functions, and toolkits
agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[
        get_weather,                    # Plain function
        get_top_stories,                # @tool decorated function
        DuckDuckGoTools(),              # Pre-built toolkit instance
    ],
    show_tool_calls=True,               # Show tool calls in output
    markdown=True,
)
```
