# Tool Calling / Function Calling

> Source: [docs.vllm.ai](https://docs.vllm.ai/) — v0.22.1

## Table of Contents
- [Overview](#overview)
- [Enabling Tool Calling](#enabling-tool-calling)
- [Tool Choice Modes](#tool-choice-modes)
- [Supported Models and Parsers](#supported-models-and-parsers)
- [API Request Format](#api-request-format)
- [Multi-Turn Tool Use](#multi-turn-tool-use)
- [Streaming with Tools](#streaming-with-tools)
- [Custom Tool Parsers](#custom-tool-parsers)
- [Benchmarking](#benchmarking)
- [Common Pitfalls](#common-pitfalls)

## Overview

vLLM supports OpenAI-compatible function calling (tool use) through the Chat Completions API. Models can decide when and how to call tools, and vLLM extracts the tool call arguments from the model's output using model-specific parsers.

Tool calling requires:
1. A model that was trained for function calling
2. The correct tool call parser for that model family
3. Server flags to enable the feature

## Enabling Tool Calling

```bash
vllm serve <model> \
    --enable-auto-tool-choice \
    --tool-call-parser <parser-name>
```

| Flag | Required | Description |
|------|----------|-------------|
| `--enable-auto-tool-choice` | Yes | Enables the model to autonomously generate tool calls |
| `--tool-call-parser` | Yes | Specifies which parser extracts tool calls from output |
| `--tool-parser-plugin` | No | Register a custom tool parser module |
| `--chat-template` | No | Custom template for tool-role message formatting |

## Tool Choice Modes

The `tool_choice` parameter in requests controls tool calling behavior:

| Mode | Behavior | Decoding |
|------|----------|----------|
| `"auto"` | Model decides whether to call tools | Parser-based extraction |
| `"required"` | Model must produce at least one tool call | Structured output constrained |
| `"none"` | No tool calls allowed | Standard generation |
| `{"type": "function", "function": {"name": "X"}}` | Force call to specific function X | Structured output constrained |

Named function and `"required"` modes use structured outputs to guarantee valid JSON matching the parameter schema. `"auto"` mode relies on the parser to extract tool calls from free-form output.

## Supported Models and Parsers

| Model Family | Parser | Notes |
|-------------|--------|-------|
| Hermes (Nous Research) | `hermes` | Hermes 2 Pro and newer |
| Mistral | `mistral` | Mistral-7B-Instruct-v0.3+ |
| Llama 3.x | `llama3_json` | Llama 3.1, 3.2 (JSON format) |
| Llama 4 | `pythonic` | Recommended for Llama 4 |
| Qwen 2.5 | `hermes` | Works with Hermes parser |
| Qwen 3 | `qwen3_xml` | XML-based tool format |
| DeepSeek V3 | `deepseek_v3` | DeepSeek-V3 specific |
| DeepSeek V3.1 | `deepseek_v31` | Updated parser |
| IBM Granite | `granite` / `granite4` | Multiple variants |
| InternLM | `internlm` | InternLM2 models |
| Jamba | `jamba` | AI21 Jamba models |
| xLAM | `xlam` | Salesforce xLAM |
| FunctionGemma | `functiongemma` | Google FunctionGemma |
| OpenAI OSS | `openai` | GPT-4-style format |

### Example with Llama 3.1

```bash
vllm serve meta-llama/Llama-3.1-70B-Instruct \
    --enable-auto-tool-choice \
    --tool-call-parser llama3_json \
    --tensor-parallel-size 2
```

### Example with Qwen 2.5

```bash
vllm serve Qwen/Qwen2.5-72B-Instruct \
    --enable-auto-tool-choice \
    --tool-call-parser hermes
```

## API Request Format

### Defining Tools

```python
from openai import OpenAI

client = OpenAI(api_key="EMPTY", base_url="http://localhost:8000/v1")

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name, e.g. 'San Francisco, CA'",
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                    },
                },
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                },
                "required": ["query"],
            },
        },
    },
]

response = client.chat.completions.create(
    model="meta-llama/Llama-3.1-70B-Instruct",
    messages=[{"role": "user", "content": "What's the weather in Paris?"}],
    tools=tools,
    tool_choice="auto",
)
```

### Handling Tool Call Responses

```python
message = response.choices[0].message

if message.tool_calls:
    for tool_call in message.tool_calls:
        print(f"Function: {tool_call.function.name}")
        print(f"Arguments: {tool_call.function.arguments}")
        print(f"Call ID: {tool_call.id}")
```

## Multi-Turn Tool Use

Implement a complete tool-calling loop:

```python
import json

messages = [{"role": "user", "content": "What's the weather in Paris and London?"}]

while True:
    response = client.chat.completions.create(
        model="model-name",
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )

    assistant_message = response.choices[0].message
    messages.append(assistant_message.model_dump())

    if not assistant_message.tool_calls:
        print(f"Final answer: {assistant_message.content}")
        break

    for tool_call in assistant_message.tool_calls:
        args = json.loads(tool_call.function.arguments)

        # Execute the tool (your implementation)
        if tool_call.function.name == "get_weather":
            result = f"Weather in {args['location']}: 22°C, sunny"
        else:
            result = "No results found"

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result,
        })
```

## Streaming with Tools

Tool calls can be streamed — the function name and arguments arrive incrementally:

```python
stream = client.chat.completions.create(
    model="model-name",
    messages=[{"role": "user", "content": "What's the weather?"}],
    tools=tools,
    tool_choice="auto",
    stream=True,
)

tool_calls = {}
for chunk in stream:
    delta = chunk.choices[0].delta
    if delta.tool_calls:
        for tc in delta.tool_calls:
            idx = tc.index
            if idx not in tool_calls:
                tool_calls[idx] = {"name": "", "arguments": ""}
            if tc.function.name:
                tool_calls[idx]["name"] += tc.function.name
            if tc.function.arguments:
                tool_calls[idx]["arguments"] += tc.function.arguments

for idx, tc in tool_calls.items():
    print(f"Tool: {tc['name']}, Args: {tc['arguments']}")
```

## Custom Tool Parsers

Implement custom parsers for models not covered by built-in parsers:

```python
from vllm.entrypoints.openai.tool_parsers import ToolParser, ToolParserManager

class MyToolParser(ToolParser):
    def adjust_request(self, request):
        """Modify the chat completion request before processing."""
        return request

    def extract_tool_calls(self, model_output, request):
        """Extract tool calls from non-streaming output."""
        # Parse model_output to find tool calls
        # Return list of ToolCall objects
        ...

    def extract_tool_calls_streaming(self, previous_text, current_text, delta_text, ...):
        """Extract tool calls from streaming output chunks."""
        ...

# Register the parser
ToolParserManager.register_lazy_module("my_parser", "path.to.module", "MyToolParser")
```

Use with:
```bash
vllm serve model \
    --enable-auto-tool-choice \
    --tool-call-parser my_parser \
    --tool-parser-plugin path.to.module
```

## Benchmarking

Use the Berkeley Function Calling Leaderboard (BFCL) dataset to measure tool-calling performance:

```bash
vllm bench serve \
    --model meta-llama/Llama-3.1-70B-Instruct \
    --dataset-name bfcl \
    --enable-auto-tool-choice \
    --tool-call-parser llama3_json
```

This measures latency and throughput on realistic function-calling workloads.

## Common Pitfalls

1. **Missing --enable-auto-tool-choice** — tool calls silently won't work without this flag; the model generates text instead
2. **Wrong parser for model** — using `hermes` parser with Llama 3.1 won't extract calls correctly; match the parser to the model
3. **strict parameter has no effect** — vLLM accepts but ignores OpenAI's `strict` field on tool definitions
4. **Parallel tool calls** — some models (e.g., Mistral 7B) struggle with multiple simultaneous tool calls; test before relying on parallel calls
5. **Auto mode argument quality** — in `"auto"` mode, arguments may be malformed or violate the schema since extraction is parser-based, not constrained; use `"required"` mode for guaranteed schema compliance
6. **Streaming tool call assembly** — tool call arguments arrive in chunks; you must concatenate them before parsing as JSON
