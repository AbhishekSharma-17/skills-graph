# Structured Output — Pydantic Models & Typed Responses

Forces the agent to return data matching a Pydantic model schema.

## Define a Pydantic Model

```python
from pydantic import BaseModel

class PersonInfo(BaseModel):
    """Information about a person."""
    name: str | None = None
    age: int | None = None
    occupation: str | None = None
```

## Non-Streaming Structured Output

```python
response = await agent.run(
    "John Smith is a 35-year-old software engineer.",
    response_format=PersonInfo,
)

if response.value:
    person = response.value  # PersonInfo instance
    print(f"Name: {person.name}")        # "John Smith"
    print(f"Age: {person.age}")          # 35
    print(f"Occupation: {person.occupation}")  # "software engineer"
else:
    print("No structured data found")
    print(f"Raw text: {response.text}")
```

## Streaming Structured Output

Two approaches — iterate for real-time text, then get parsed value:

### Approach 1: Stream text, then parse

```python
stream = agent.run(
    query,
    stream=True,
    options={"response_format": PersonInfo},
)

# Stream raw text to user
async for update in stream:
    if update.text:
        print(update.text, end="", flush=True)

# Get parsed structured result
final = await stream.get_final_response()
if final.value:
    person = final.value
    print(f"\nParsed: {person.name}, age {person.age}")
```

### Approach 2: Skip streaming, just get parsed result

```python
stream = agent.run(
    query,
    stream=True,
    options={"response_format": PersonInfo},
)

# Skip iteration — go directly to final
final = await stream.get_final_response()
if final.value:
    person = final.value
```

## Complete Example

```python
import asyncio
from agent_framework.openai import OpenAIResponsesClient
from pydantic import BaseModel

class CityInfo(BaseModel):
    """Structured information about a city."""
    city: str
    description: str

async def main():
    agent = OpenAIResponsesClient().as_agent(
        name="CityAgent",
        instructions="Describe cities in structured format.",
    )

    # Non-streaming
    result = await agent.run(
        "Tell me about Paris, France",
        options={"response_format": CityInfo},
    )
    if result.value:
        print(f"City: {result.value.city}")
        print(f"Description: {result.value.description}")

    # Streaming
    stream = agent.run(
        "Tell me about Tokyo, Japan",
        stream=True,
        options={"response_format": CityInfo},
    )
    async for update in stream:
        if update.text:
            print(update.text, end="", flush=True)
    print()

    final = await stream.get_final_response()
    if final.value:
        print(f"City: {final.value.city}")
        print(f"Description: {final.value.description}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Complex Models

```python
from pydantic import BaseModel, Field
from typing import Optional

class Address(BaseModel):
    street: str
    city: str
    state: str
    zip_code: str = Field(description="5-digit ZIP code")

class Employee(BaseModel):
    name: str
    title: str
    department: str
    salary: Optional[float] = None
    address: Optional[Address] = None
    skills: list[str] = Field(default_factory=list, description="List of skills")

# Use with agent
result = await agent.run(
    "Extract employee info from: John Doe, Senior Engineer, Engineering dept...",
    response_format=Employee,
)
```

## Provider Support

| Provider | Structured Output |
|---|:-:|
| Azure OpenAI Responses | ✅ |
| OpenAI Responses | ✅ |
| Azure AI Foundry | ✅ |
| Anthropic Claude | ✅ |
| Ollama | ✅ |
| GitHub Copilot | ❌ |

## Tips

- Use `Optional` fields with defaults for data that may be missing
- Add `Field(description="...")` for complex fields to guide the model
- The `response.value` is `None` if parsing fails — always check it
- Structured output works with both `response_format=` param and `options={"response_format": ...}`
- Nested models (model within model) are supported
