# Context Compression (BETA)

Context Compression manages agent context while running by automatically summarizing verbose tool results. This prevents context window overflow and keeps response quality high during multi-tool workflows.

## Docs Hierarchy

```
Context Compression BETA
├── Overview (/compression/overview)
└── Token Counting (/compression/token-counting)
```

## The Problem: Verbose Tool Results

Tool results accumulate rapidly and can exhaust the context window:

| Step | Cumulative Tokens | Notes |
|------|-------------------|-------|
| System Prompt | 1,200 | |
| User Message | 2,500 | |
| LLM Response | 4,000 | |
| Tool Call 1 | 6,500 | +2,500 |
| Tool Call 2 | 9,700 | +3,200 |
| Tool Call 3 | 12,500 | +2,800 |
| Tool Call 4 | 16,000 | +3,500 |

Context compression summarizes previous tool results when a threshold is hit, keeping only the essential information.

---

## Quick Start

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.tools.hackernews import HackerNewsTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[HackerNewsTools()],
    compress_tool_results=True,  # Enable compression (default threshold: 3 tool calls)
)

agent.print_response("Get the top stories on HackerNews about AI, ML, startups, and tech trends")
```

---

## Compression Parameters (Agent-Level)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `compress_tool_results` | `bool` | `False` | Enable automatic compression of tool results |
| `compress_tool_results_limit` | `int` | `3` | Compress after N tool calls (count-based trigger) |
| `compress_token_limit` | `int` | `None` | Compress when context exceeds this token count |
| `compress_tool_call_instructions` | `str` | `None` | Custom prompt for the compression model |
| `compression_manager` | `CompressionManager` | `None` | Custom compression configuration object |

## CompressionManager Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `BaseModel` | Required | Model to use for compression (can differ from agent model) |
| `compress_tool_results` | `bool` | `True` | Enable compression |
| `compress_tool_results_limit` | `int` | `3` | Count-based trigger threshold |
| `compress_token_limit` | `int` | `None` | Token-based trigger threshold |
| `compress_tool_call_instructions` | `str` | `None` | Custom compression prompt |

---

## Compression Triggers

| Mode | Parameter | Trigger | Best For |
|------|-----------|---------|----------|
| **Count-Based** | `compress_tool_results_limit` | After N uncompressed tool results | Predictable tool call patterns |
| **Token-Based** | `compress_token_limit` | When context exceeds token threshold | Variable result sizes, strict limits |

---

## Count-Based Compression

Compress after a fixed number of tool calls:

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.tools.hackernews import HackerNewsTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[HackerNewsTools()],
    compress_tool_results=True,
    compress_tool_results_limit=2,  # Compress after every 2 tool calls
)

agent.print_response("Find stories about AI startup funding on HackerNews")
```

## Token-Based Compression

Compress when total context exceeds a token threshold:

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.tools.hackernews import HackerNewsTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[HackerNewsTools()],
    compress_tool_results=True,
    compress_token_limit=5000,  # Compress when context exceeds 5000 tokens
)

agent.print_response("Find HackerNews discussions about OpenAI, Anthropic, Google DeepMind, and Meta AI")
```

---

## Custom CompressionManager

Use a dedicated (often smaller/faster) model for compression with custom instructions:

```python
from agno.agent import Agent
from agno.compression.manager import CompressionManager
from agno.models.openai import OpenAIResponses
from agno.tools.hackernews import HackerNewsTools

compression_manager = CompressionManager(
    model=OpenAIResponses(id="gpt-5.2"),  # Use a fast model for compression
    compress_tool_results_limit=2,
    compress_tool_call_instructions="Summarize the key findings, keeping URLs and numbers intact.",
)

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[HackerNewsTools()],
    compression_manager=compression_manager,
)

agent.print_response("Find stories about AI startup funding on HackerNews")
```

---

## Token Counting

Agno provides token counting to help you estimate context size and set thresholds:

```python
from agno.models.message import Message
from agno.models.openai import OpenAIResponses
from pydantic import BaseModel

class Answer(BaseModel):
    answer: str

model = OpenAIResponses(id="gpt-5.2")

messages = [
    Message(role="system", content="You are a concise assistant."),
    Message(role="user", content="Summarize context compression in 2 sentences."),
]

tools = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for a query.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    }
]

# Count tokens for messages + tools + output schema
tokens = model.count_tokens(messages=messages, tools=tools, output_schema=Answer)
print(f"Estimated tokens: {tokens}")
```

**Install dependencies for token counting:**

```bash
pip install tiktoken tokenizers
```

---

## How Compression Works Internally

1. Agent makes tool calls normally
2. When threshold is hit (count or tokens), compression activates
3. A compression model summarizes **all previous** tool results into a concise summary
4. Original verbose tool results are replaced with the summary in context
5. Agent continues with compressed context + new tool results
6. Process repeats when threshold is hit again

---

## Combining with Other Context Controls

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.db.sqlite import SqliteDb
from agno.tools.hackernews import HackerNewsTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=SqliteDb(db_file="tmp/agent.db"),
    tools=[HackerNewsTools()],
    # Chat history control
    add_history_to_context=True,
    num_history_runs=3,
    # Long-term memory via summaries
    enable_session_summaries=True,
    add_session_summary_to_context=True,
    # Tool result compression
    compress_tool_results=True,
    compress_tool_results_limit=3,
    instructions=["Focus on efficiency", "Preserve critical facts"],
)
```

Three layers of context management: history limits → session summaries → tool result compression.

---

## When to Use Context Compression

| Scenario | Recommended |
|----------|-------------|
| Agents with web search / API tools | Yes — results are typically verbose |
| Multi-step research workflows | Yes — many tool calls accumulate |
| Long-running sessions | Yes — combined with session summaries |
| Simple Q&A agents | No — few tool calls, overhead not worth it |
| Agents with small tool outputs | No — minimal benefit |
| Production cost-sensitive systems | Yes — saves tokens on subsequent LLM calls |
| Strict context window limits | Yes — use token-based compression |
