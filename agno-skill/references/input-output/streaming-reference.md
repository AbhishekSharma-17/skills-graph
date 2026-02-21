# Agno Streaming & I/O Reference

## Contents
- [Streaming](#streaming)
- [Agent I/O Parameters Quick Reference](#agent-io-parameters-quick-reference)
- [Teams Structured I/O](#teams-structured-io)
- [Full Example: Multimodal Agent with Structured Output](#full-example-multimodal-agent-with-structured-output)

---

## Streaming

### Sync streaming

```python
agent = Agent(model=OpenAIResponses(id="gpt-4o"), markdown=True)
agent.print_response("Explain concurrency vs parallelism", stream=True)
```

### Consuming stream events manually

```python
from agno.agent import AgentRunEvent

stream = agent.run("Tell me a story", stream=True, stream_events=True)

for event in stream:
    if event.event == AgentRunEvent.run_content:
        print(event.content, end="", flush=True)
    elif event.event == AgentRunEvent.tool_call_started:
        print("\n[Tool call started]")
    elif event.event == AgentRunEvent.tool_call_completed:
        print("[Tool call completed]")
```

### Async streaming

```python
async for event in agent.arun("Tell me a story", stream=True, stream_events=True):
    print(event.content, end="", flush=True)
```

---

## Agent I/O Parameters Quick Reference

| Parameter | Type | Default | Purpose |
|-----------|------|---------|---------|
| `input_schema` | `Type[BaseModel]` | None | Validate input against Pydantic model |
| `output_schema` | `Type[BaseModel]` | None | Structured Pydantic output |
| `use_json_mode` | bool | False | Force JSON response (fallback for models without native structured output) |
| `structured_outputs` | bool | None | Use model-enforced structured output API |
| `expected_output` | str | None | Natural language guidance for response format |
| `output_model` | Model | None | Secondary model to refine/polish response |
| `output_model_prompt` | str | None | Prompt for the output model |
| `parser_model` | Model | None | Secondary model to parse response into schema |
| `parser_model_prompt` | str | None | Prompt for the parser model |
| `parse_response` | bool | True | Auto-convert response to output_schema |
| `save_response_to_file` | str | None | Save response content to file |
| `send_media_to_model` | bool | True | Send media to LLM (vs only to tools) |
| `store_media` | bool | True | Persist media in database |

### run() method signature

```python
response = agent.run(
    input="...",                    # str, dict, BaseModel, message list
    stream=False,                  # Token-by-token streaming
    stream_events=False,           # Emit intermediate events
    user_id=None,                  # User identifier
    session_id=None,               # Session identifier
    session_state=None,            # Dict for persistent state
    output_schema=None,            # Per-run schema override
    images=None,                   # List[Image]
    audio=None,                    # List[Audio]
    videos=None,                   # List[Video]
    files=None,                    # List[File]
    debug_mode=None,
)
# Returns RunOutput (or Iterator[RunOutputEvent] if stream=True)
```

### RunOutput object

```python
response = agent.run("...")
response.content          # str or BaseModel (if output_schema set)
response.metrics          # Token usage, timing
response.response_audio   # Audio output (if model supports it)
response.messages         # Full message history
```

---

## Teams Structured I/O

Teams support all the same structured I/O patterns as agents — input schema validation, output schema, parser model, output model, and per-run schema overrides. The syntax is identical:

```python
from agno.team import Team

team = Team(
    name="Analysis Team",
    model=OpenAIResponses(id="gpt-4o"),
    members=[researcher, analyst],
    input_schema=ResearchRequest,
    output_schema=AnalysisReport,
)

response = team.run(input={"topic": "AI", "depth": 7})
report: AnalysisReport = response.content
```

---

## Full Example: Multimodal Agent with Structured Output

```python
from pydantic import BaseModel, Field
from typing import List
from agno.agent import Agent
from agno.media import Image
from agno.models.openai import OpenAIResponses
from agno.tools.hackernews import HackerNewsTools


class ImageReport(BaseModel):
    subject: str = Field(description="Main subject of the image")
    description: str = Field(description="Detailed description")
    colors: List[str] = Field(description="Dominant colors")
    related_news: List[str] = Field(description="Related news headlines")
    sentiment: str = Field(description="Overall mood: positive, neutral, or negative")


agent = Agent(
    model=OpenAIResponses(id="gpt-4o"),
    tools=[HackerNewsTools()],
    output_schema=ImageReport,
    instructions=[
        "Analyze the image thoroughly",
        "Search HackerNews for related stories",
        "Combine visual analysis with news context",
    ],
)

response = agent.run(
    "Analyze this image and find related news",
    images=[Image(url="https://upload.wikimedia.org/wikipedia/commons/0/0c/GoldenGateBridge-001.jpg")],
)

report: ImageReport = response.content
print(f"Subject: {report.subject}")
print(f"Colors: {', '.join(report.colors)}")
print(f"Sentiment: {report.sentiment}")
for headline in report.related_news:
    print(f"  - {headline}")
```
