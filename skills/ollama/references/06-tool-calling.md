# Ollama — Tool Calling

> Source: [docs.ollama.com/capabilities/tool-calling](https://docs.ollama.com/capabilities/tool-calling) | Version: 0.22.x

## Table of Contents

- [Overview](#overview)
- [Supported Models](#supported-models)
- [Tool Definition Format](#tool-definition-format)
- [Basic Tool Calling Flow](#basic-tool-calling-flow)
- [Python Library Tool Calling](#python-library-tool-calling)
- [Streaming Tool Calls](#streaming-tool-calls)
- [Multiple Tools](#multiple-tools)
- [Tool Call Loop Pattern](#tool-call-loop-pattern)
- [OpenAI SDK Tool Calling](#openai-sdk-tool-calling)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

Tool calling (also known as function calling) allows models to request the execution of external functions. The model doesn't execute the tools — it generates a structured request that your application fulfills, then feeds the result back.

**Flow:**
1. Client sends a message with `tools` definitions
2. Model responds with `tool_calls` (function name + arguments)
3. Client executes the function and gets a result
4. Client sends the result back as a `tool` role message
5. Model generates a final response using the tool result

## Supported Models

Not all models support tool calling. Confirmed models:

| Model | Size | Tool Quality | Notes |
|-------|------|-------------|-------|
| Qwen 3 | 8B–72B | Excellent | Best overall tool calling |
| Llama 3.1 | 8B–405B | Good | Start with 8B for dev |
| Gemma 4 | 4B–27B | Good | Good for structured output |
| DeepSeek-V3 | 671B MoE | Excellent | Requires significant resources |
| Mistral | 7B | Moderate | Older, less reliable |
| Command-R+ | 104B | Good | Strong reasoning |

**Recommendation:** Start with `qwen3:8b` for development (fast, reliable). Use `qwen3:32b` or `llama3.1:70b` for production where tool selection accuracy matters.

## Tool Definition Format

Tools are defined using JSON Schema in the native API:

```json
{
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get the current weather for a city",
        "parameters": {
          "type": "object",
          "properties": {
            "city": {
              "type": "string",
              "description": "The city name, e.g. 'San Francisco'"
            },
            "unit": {
              "type": "string",
              "enum": ["celsius", "fahrenheit"],
              "description": "Temperature unit"
            }
          },
          "required": ["city"]
        }
      }
    }
  ]
}
```

## Basic Tool Calling Flow

```bash
# Step 1: Send request with tools
curl http://localhost:11434/api/chat -d '{
  "model": "qwen3:8b",
  "messages": [
    {"role": "user", "content": "What is the weather in London?"}
  ],
  "tools": [{
    "type": "function",
    "function": {
      "name": "get_weather",
      "description": "Get current weather",
      "parameters": {
        "type": "object",
        "properties": {
          "city": {"type": "string"}
        },
        "required": ["city"]
      }
    }
  }],
  "stream": false
}'

# Response includes tool_calls:
# {
#   "message": {
#     "role": "assistant",
#     "content": "",
#     "tool_calls": [{
#       "function": {
#         "name": "get_weather",
#         "arguments": {"city": "London"}
#       }
#     }]
#   }
# }

# Step 2: Execute the tool and send the result back
curl http://localhost:11434/api/chat -d '{
  "model": "qwen3:8b",
  "messages": [
    {"role": "user", "content": "What is the weather in London?"},
    {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "get_weather", "arguments": {"city": "London"}}}]},
    {"role": "tool", "content": "15°C, cloudy with light rain"}
  ],
  "stream": false
}'
```

## Python Library Tool Calling

The Python library supports passing Python functions directly as tools:

```python
from ollama import chat

def get_weather(city: str, unit: str = "celsius") -> str:
    """Get the current weather for a city."""
    return f"Weather in {city}: 18°C, partly cloudy"

def search_web(query: str) -> str:
    """Search the web for information."""
    return f"Results for '{query}': ..."

response = chat(
    model="qwen3:8b",
    messages=[{"role": "user", "content": "What's the weather in Berlin?"}],
    tools=[get_weather, search_web],
)

if response.message.tool_calls:
    for tool_call in response.message.tool_calls:
        fn_name = tool_call.function.name
        fn_args = tool_call.function.arguments
        print(f"Model wants to call: {fn_name}({fn_args})")
```

The library automatically extracts function signatures and docstrings to build tool definitions.

## Streaming Tool Calls

Tool calls can be streamed, allowing you to begin processing before the full response arrives:

```python
from ollama import chat

stream = chat(
    model="qwen3:8b",
    messages=[{"role": "user", "content": "Weather in Tokyo and Paris?"}],
    tools=[get_weather],
    stream=True,
)

for chunk in stream:
    if chunk.message.tool_calls:
        for tc in chunk.message.tool_calls:
            print(f"Tool call: {tc.function.name}({tc.function.arguments})")
    if chunk.message.content:
        print(chunk.message.content, end="")
```

## Multiple Tools

Provide multiple tools and the model selects the appropriate one:

```python
from ollama import chat

def calculate(expression: str) -> str:
    """Evaluate a mathematical expression."""
    return str(eval(expression))

def get_time(timezone: str) -> str:
    """Get current time in a timezone."""
    from datetime import datetime
    return datetime.now().isoformat()

def translate(text: str, target_language: str) -> str:
    """Translate text to a target language."""
    return f"[Translated to {target_language}]: {text}"

response = chat(
    model="qwen3:8b",
    messages=[{"role": "user", "content": "What is 42 * 17?"}],
    tools=[calculate, get_time, translate],
)
# Model selects 'calculate' with {"expression": "42 * 17"}
```

## Tool Call Loop Pattern

A complete agent loop that handles tool calls until the model produces a final answer:

```python
from ollama import chat

def get_weather(city: str) -> str:
    """Get current weather for a city."""
    weather_data = {"London": "15°C, rain", "Tokyo": "22°C, sunny"}
    return weather_data.get(city, f"No data for {city}")

tools = [get_weather]
available_fns = {"get_weather": get_weather}

messages = [{"role": "user", "content": "Compare weather in London and Tokyo"}]

while True:
    response = chat(model="qwen3:8b", messages=messages, tools=tools)
    messages.append(response.message)

    if not response.message.tool_calls:
        print(response.message.content)
        break

    for tool_call in response.message.tool_calls:
        fn = available_fns[tool_call.function.name]
        result = fn(**tool_call.function.arguments)
        messages.append({"role": "tool", "content": result})
```

## OpenAI SDK Tool Calling

Tool calling via the OpenAI compatibility layer:

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

tools = [{
    "type": "function",
    "function": {
        "name": "get_stock_price",
        "description": "Get the current stock price",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Stock ticker symbol"}
            },
            "required": ["symbol"],
        },
    },
}]

response = client.chat.completions.create(
    model="qwen3:8b",
    messages=[{"role": "user", "content": "What's AAPL trading at?"}],
    tools=tools,
    tool_choice="auto",
)

if response.choices[0].message.tool_calls:
    tc = response.choices[0].message.tool_calls[0]
    print(f"{tc.function.name}: {tc.function.arguments}")
```

## Common Pitfalls

1. **Model doesn't support tools** — Not all models handle tool calling. Use Qwen 3, Llama 3.1+, or Gemma 4. Smaller models (<7B) are unreliable.
2. **Missing tool result** — After receiving `tool_calls`, you MUST send a `tool` role message with the result before requesting the next response.
3. **Tool description quality** — Vague descriptions lead to incorrect tool selection. Be specific about what each tool does and what parameters mean.
4. **Parallel tool calls** — Models may request multiple tool calls in one response. Handle all of them before sending results back.
5. **Infinite loops** — Always add a max iteration limit to tool call loops to prevent runaway execution.
6. **JSON parsing** — Tool arguments are JSON objects. The model may occasionally produce malformed JSON with smaller models.
