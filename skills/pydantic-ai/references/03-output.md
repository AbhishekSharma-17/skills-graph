# Output Types

> Source: [pydantic.dev/docs/ai/core-concepts/output](https://pydantic.dev/docs/ai/core-concepts/output/)

## Table of Contents

- [Overview](#overview)
- [Structured Output With Pydantic Models](#structured-output-with-pydantic-models)
- [Union and List Types](#union-and-list-types)
- [Output Functions](#output-functions)
- [Output Modes](#output-modes)
- [Output Validators](#output-validators)
- [Image Output](#image-output)
- [Optional Output](#optional-output)
- [Streaming Structured Output](#streaming-structured-output)
- [Custom JSON Schema](#custom-json-schema)
- [Common Pitfalls](#common-pitfalls)

## Overview

The `output_type` parameter controls what an agent returns. It can be plain text (default `str`), a Pydantic model, a scalar type, a union, a list, a function, or an image. Pydantic AI validates the model's response against the schema and retries on validation failure.

The output wraps in `AgentRunResult` (for `run`/`run_sync`) or `StreamedRunResult` (for `run_stream`), preserving type information through generic parameters.

## Structured Output With Pydantic Models

```python
from pydantic import BaseModel
from pydantic_ai import Agent

class CityLocation(BaseModel):
    city: str
    country: str

agent = Agent('openai:gpt-5.2', output_type=CityLocation)
result = agent.run_sync('Where were the 2012 Olympics?')
print(result.output)
# city='London' country='United Kingdom'
```

### Supported Types

- Simple scalars: `str`, `int`, `float`, `bool`
- Pydantic models: `BaseModel` subclasses
- Dataclasses: `@dataclass` classes
- TypedDict: `typing.TypedDict` subclasses
- Lists and dicts: `list[str]`, `dict[str, int]`
- Unions: `ModelA | ModelB`

## Union and List Types

Multiple output types as unions:

```python
class Box(BaseModel):
    width: int
    height: int
    depth: int
    units: str

agent = Agent(
    'openai:gpt-5-mini',
    output_type=[Box, str],
    instructions="Extract box dimensions or ask for clarification."
)
```

The model chooses which type to return based on the input.

## Output Functions

Output functions let the model call a function with generated arguments, ending the run with the function's return value.

```python
import re
from pydantic import BaseModel
from pydantic_ai import Agent, ModelRetry

class Row(BaseModel):
    name: str
    country: str

def run_sql_query(query: str) -> list[Row]:
    """Run SQL query on database."""
    if not query.startswith('SELECT *'):
        raise ModelRetry("Only 'SELECT *' is supported.")
    return execute_query(query)

sql_agent = Agent(
    'openai:gpt-5.2',
    output_type=[run_sql_query],
    instructions='Generate SQL queries for the database.'
)
```

### TextOutput (Plain Text to Function)

```python
from pydantic_ai import Agent, TextOutput

def split_words(text: str) -> list[str]:
    return text.split()

agent = Agent('openai:gpt-5.2', output_type=TextOutput(split_words))
result = agent.run_sync('Who was Albert Einstein?')
# result.output is a list[str]
```

## Output Modes

Three strategies for getting structured output from models:

### 1. Tool Output (Default)

The schema becomes a special tool's parameters. The model "calls" this tool to produce output.

```python
from pydantic_ai import Agent, ToolOutput

class Fruit(BaseModel):
    name: str
    color: str

class Vehicle(BaseModel):
    name: str
    wheels: int

agent = Agent(
    'openai:gpt-5.2',
    output_type=[
        ToolOutput(Fruit, name='return_fruit'),
        ToolOutput(Vehicle, name='return_vehicle'),
    ]
)
```

### 2. Native Output

Uses the model's built-in structured output feature (e.g., OpenAI's JSON mode):

```python
from pydantic_ai import Agent, NativeOutput

agent = Agent(
    'openai:gpt-5.2',
    output_type=NativeOutput(
        [Fruit, Vehicle],
        name='Fruit_or_vehicle',
        description='Return a fruit or vehicle.'
    )
)
```

### 3. Prompted Output

Injects the JSON schema into instructions; model returns JSON as plain text:

```python
from pydantic_ai import Agent, PromptedOutput

agent = Agent(
    'openai:gpt-5.2',
    output_type=PromptedOutput(
        [Vehicle],
        template='Return JSON matching this schema: {schema}'
    )
)
```

### End Strategy for Parallel Tool Calls

When the model makes multiple tool calls:

| Strategy | Behavior |
|----------|----------|
| `'early'` (default) | Skip remaining tools after first valid output |
| `'graceful'` | Execute all function tools, skip remaining output tools |
| `'exhaustive'` | Execute all tools; first valid output wins |

```python
agent = Agent('openai:gpt-5.2', output_type=MyOutput, end_strategy='graceful')
```

## Output Validators

Add post-processing validation with `@agent.output_validator`:

```python
from pydantic_ai import Agent, RunContext, ModelRetry

agent = Agent('openai:gpt-5.2', output_type=str)

@agent.output_validator
async def validate_length(ctx: RunContext, output: str) -> str:
    if len(output) < 50:
        raise ModelRetry('Response too short. Provide more detail.')
    return output
```

### Validation With Dependencies

```python
@agent.output_validator
async def validate_sql(ctx: RunContext[DatabaseConn], output: Success) -> Success:
    try:
        await ctx.deps.execute(f'EXPLAIN {output.sql_query}')
    except QueryError as e:
        raise ModelRetry(f'Invalid SQL: {e}')
    return output
```

### Partial Output Handling

During streaming, validators fire on partial results. Skip side effects:

```python
@agent.output_validator
def validate(ctx: RunContext, output: str) -> str:
    if ctx.partial_output:
        return output  # Don't validate partials
    if len(output) < 50:
        raise ModelRetry('Too short')
    return output
```

## Image Output

```python
from pydantic_ai import Agent, BinaryImage

agent = Agent('openai-responses:gpt-5.2', output_type=BinaryImage)
result = agent.run_sync('Generate an image of a sunset.')
# result.output is a BinaryImage instance

# Optional image with text fallback
agent = Agent('openai-responses:gpt-5.2', output_type=BinaryImage | str)
```

## Optional Output

Allow `None` responses:

```python
agent = Agent('openai:gpt-5.2', output_type=str | None)

@agent.tool_plain
def perform_action(task_id: int) -> str:
    return f'Task {task_id} done.'

result = agent.run_sync('Do task 1, then stop.')
# result.output may be None
```

## Streaming Structured Output

Stream partial structured data as it builds:

```python
from typing_extensions import NotRequired, TypedDict

class UserProfile(TypedDict):
    name: str
    dob: NotRequired[str]
    bio: NotRequired[str]

agent = Agent('openai:gpt-5.2', output_type=UserProfile)

async with agent.run_stream('Extract: Ben, born Jan 28 1990') as result:
    async for profile in result.stream_output():
        print(profile)
        # {'name': 'Ben'}
        # {'name': 'Ben', 'dob': '1990-01-28'}
        # {'name': 'Ben', 'dob': '1990-01-28', 'bio': '...'}
```

## Custom JSON Schema

When Pydantic models aren't feasible, use `StructuredDict`:

```python
from pydantic_ai import Agent, StructuredDict

HumanDict = StructuredDict(
    {'type': 'object', 'properties': {'name': {'type': 'string'}, 'age': {'type': 'integer'}}, 'required': ['name', 'age']},
    name='Human',
    description='A person with name and age'
)

agent = Agent('openai:gpt-5.2', output_type=HumanDict)
result = agent.run_sync('Create a person')
# result.output is a dict: {'name': 'John', 'age': 30}
```

## Common Pitfalls

- **No instructions with complex output** — the model needs guidance on what to extract; always pair `output_type` with clear `instructions`
- **Union ambiguity** — when using `[TypeA, TypeB]`, add descriptions to help the model choose the right type
- **NativeOutput provider support** — not all providers support native structured output; fall back to `ToolOutput` (default)
- **Streaming validators** — validators fire on partial output during streaming; check `ctx.partial_output` to skip side effects
- **ModelRetry in output functions** — raising `ModelRetry` asks the model to retry with a different set of arguments

## Related

- `01-agents.md` — Agent configuration
- `07-streaming.md` — Streaming patterns in depth
- `04-tools.md` — Tool return types
