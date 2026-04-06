# Structured Outputs & Tool Calling

> Source: https://docs.litellm.ai/docs/completion/json_mode • Written for litellm v1.52.x

LiteLLM normalizes JSON mode, schema-constrained outputs, and OpenAI-style function calling across providers. You write OpenAI-format `tools` / `response_format` once and it works on Anthropic, Bedrock, Vertex, Mistral, etc.

## JSON mode

Force the model to return valid JSON:

```python
from litellm import completion

resp = completion(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "Return only JSON."},
        {"role": "user", "content": "Give me a person with name and age."},
    ],
    response_format={"type": "json_object"},
)
import json
data = json.loads(resp.choices[0].message.content)
```

Works with OpenAI, Azure OpenAI, Mistral, Together, Groq, Anthropic (newer models), Vertex Gemini, and more.

## Schema-constrained (strict) JSON

Pass a JSON schema to force a specific shape:

```python
schema = {
    "type": "json_schema",
    "json_schema": {
        "name": "Person",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "hobbies": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["name", "age", "hobbies"],
            "additionalProperties": False,
        },
    },
}

resp = completion(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Generate a sample person."}],
    response_format=schema,
)
```

For providers that don't support strict JSON natively, LiteLLM falls back to a system prompt + JSON-mode hybrid.

## Pydantic models

LiteLLM can take a Pydantic model directly as `response_format`:

```python
from pydantic import BaseModel
from litellm import completion

class Person(BaseModel):
    name: str
    age: int
    hobbies: list[str]

resp = completion(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Generate a sample person."}],
    response_format=Person,
)

person = Person.model_validate_json(resp.choices[0].message.content)
```

## Function / tool calling

Define tools in OpenAI format:

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "unit": {"type": "string", "enum": ["c", "f"]},
                },
                "required": ["city"],
            },
        },
    }
]

resp = completion(
    model="anthropic/claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": "What's the weather in Paris?"}],
    tools=tools,
    tool_choice="auto",
)

msg = resp.choices[0].message
if msg.tool_calls:
    for call in msg.tool_calls:
        print(call.function.name, call.function.arguments)
```

LiteLLM translates this to Anthropic's `tool_use` block, Bedrock's tool config, Vertex's `function_declarations`, etc. You don't change a line.

## Tool choice options

```python
tool_choice="auto"          # model decides
tool_choice="none"          # disable tools
tool_choice="required"      # must call at least one tool
tool_choice={"type": "function", "function": {"name": "get_weather"}}  # force this one
```

## Parallel tool calls

By default, models can return multiple tool calls in one response. Disable:
```python
completion(..., tools=tools, parallel_tool_calls=False)
```

## Sending tool results back

```python
messages = [
    {"role": "user", "content": "Weather in Paris?"},
    msg.model_dump(),  # the assistant message with tool_calls
    {
        "role": "tool",
        "tool_call_id": msg.tool_calls[0].id,
        "content": json.dumps({"temp": 18, "unit": "c"}),
    },
]

resp = completion(model="anthropic/claude-3-5-sonnet-20241022", messages=messages, tools=tools)
print(resp.choices[0].message.content)
```

## Function calling with Pydantic helpers

LiteLLM exposes `function_to_dict` to turn a Python function into an OpenAI tool spec:

```python
from litellm.utils import function_to_dict

def get_weather(city: str, unit: str = "c") -> str:
    """Get the current weather for a city."""
    ...

tool = {"type": "function", "function": function_to_dict(get_weather)}
```

Useful for building lightweight agent loops without LangChain/CrewAI.

## Common pitfalls

- **Tool args returned as string** — `function.arguments` is always a JSON string. `json.loads` it.
- **Provider doesn't support `parallel_tool_calls=False`** — Some providers ignore the flag and still emit multiple calls. Handle them.
- **`additionalProperties: false` missing** — OpenAI strict mode rejects schemas without it. LiteLLM does NOT auto-inject it.
- **Schema too complex** — Some providers have shallow nesting limits (Bedrock, Vertex). Test with the actual provider.
- **JSON mode without "json" in prompt** — OpenAI requires the word "JSON" appear in the messages when using `{"type": "json_object"}`. LiteLLM passes through this restriction.

## Related
- Streaming tool calls → `03-streaming.md`
- Async tool loops → `04-async.md`
