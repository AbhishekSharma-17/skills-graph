# Instructor — Streaming & Partial Responses

> Source: https://python.useinstructor.com/concepts/partial | v1.15.4

## Table of Contents

- [Streaming Overview](#streaming-overview)
- [Partial Streaming](#partial-streaming)
- [Iterable Streaming](#iterable-streaming)
- [Async Streaming](#async-streaming)
- [PartialLiteralMixin](#partialliteralmixin)
- [create_partial vs create_iterable](#create_partial-vs-create_iterable)
- [Real-Time UI Patterns](#real-time-ui-patterns)
- [Limitations](#limitations)

## Streaming Overview

Instructor supports two streaming patterns:

| Pattern | Method | Use Case |
|---------|--------|----------|
| **Partial** | `create_partial()` | Stream a single object with incremental field updates |
| **Iterable** | `Iterable[T]` + `stream=True` | Stream multiple complete objects one at a time |

Both patterns yield results as the LLM generates tokens, enabling real-time UI updates.

## Partial Streaming

`create_partial()` generates incremental snapshots of a single response model. All fields are treated as `Optional` during streaming, becoming populated as tokens arrive.

```python
import instructor
from pydantic import BaseModel

class MeetingInfo(BaseModel):
    title: str
    date: str
    attendees: list[str]
    agenda: list[str]
    action_items: list[str]

client = instructor.from_provider("openai/gpt-4o-mini")

stream = client.create_partial(
    response_model=MeetingInfo,
    messages=[{
        "role": "user",
        "content": "Extract meeting details: Team standup on March 5th with Alice, Bob...",
    }],
)

for partial in stream:
    obj = partial.model_dump()
    print(obj)
    # First yield:  {"title": "Team", "date": None, "attendees": [], ...}
    # Next yield:   {"title": "Team standup", "date": None, "attendees": [], ...}
    # Next yield:   {"title": "Team standup", "date": "2026-03-05", "attendees": ["Alice"], ...}
    # Final yield:  {"title": "Team standup", "date": "2026-03-05", "attendees": ["Alice", "Bob"], ...}
```

### How It Works

1. Instructor wraps your model with `Partial[YourModel]`, making all fields `Optional`
2. As tokens stream in, incomplete JSON is parsed into partial model instances
3. Each yield is a valid Pydantic model (with `None` for unpopulated fields)
4. The final yield contains the complete, fully-populated model

## Iterable Streaming

Stream multiple objects one at a time using `Iterable[T]` with `stream=True`:

```python
from typing import Iterable

class Person(BaseModel):
    name: str
    age: int
    role: str

client = instructor.from_provider("openai/gpt-4o-mini")

people = client.create(
    response_model=Iterable[Person],
    stream=True,
    messages=[{
        "role": "user",
        "content": "Extract all people: Jason (25, engineer), Sarah (30, manager), Mike (28, designer)",
    }],
)

for person in people:
    print(f"{person.name}: {person.age}, {person.role}")
    # Yields complete Person objects one at a time
```

Each yielded object is fully validated — unlike partial streaming, you get complete instances.

### Non-Streaming Iterable

Without `stream=True`, the entire response is parsed at once:

```python
people = client.create(
    response_model=Iterable[Person],
    stream=False,  # or omit entirely
    messages=[...],
)
for person in people:
    print(person)  # All parsed from complete response
```

## Async Streaming

Both patterns work with async clients:

### Async Partial

```python
import asyncio

async def stream_meeting():
    client = instructor.from_provider(
        "openai/gpt-4o-mini",
        async_client=True,
    )

    stream = await client.create_partial(
        response_model=MeetingInfo,
        messages=[{"role": "user", "content": "..."}],
    )

    async for partial in stream:
        print(partial.model_dump())

asyncio.run(stream_meeting())
```

### Async Iterable

```python
async def stream_people():
    client = instructor.from_provider(
        "openai/gpt-4o-mini",
        async_client=True,
    )

    people = await client.create(
        response_model=Iterable[Person],
        stream=True,
        messages=[{"role": "user", "content": "..."}],
    )

    async for person in people:
        print(person)

asyncio.run(stream_people())
```

## PartialLiteralMixin

When streaming models that use `Literal` types, use `PartialLiteralMixin` to prevent parsing errors on incomplete string values:

```python
from instructor.dsl.partial import PartialLiteralMixin
from typing import Literal

class Ticket(BaseModel, PartialLiteralMixin):
    title: str
    priority: Literal["low", "medium", "high", "critical"]
    category: Literal["bug", "feature", "support"]

# Now safe to use with create_partial()
stream = client.create_partial(
    response_model=Ticket,
    messages=[...],
)
```

Without this mixin, streaming a `Literal["critical"]` may fail when only `"crit"` has been received.

## create_partial vs create_iterable

| Feature | `create_partial()` | `Iterable[T]` + `stream=True` |
|---------|-------------------|-------------------------------|
| Objects | Single | Multiple |
| Yields | Incomplete snapshots | Complete objects |
| Validation | Deferred to final | Per-object |
| Use case | Progressive UI fill | List processing |
| Fields | All become Optional | All required as defined |

### Decision Guide

```
Need to stream a single complex object? → create_partial()
Need to stream multiple objects?        → Iterable[T] + stream=True
Need all objects at once?               → Iterable[T] (no stream)
```

## Real-Time UI Patterns

### Progress Display

```python
import sys

stream = client.create_partial(
    response_model=Report,
    messages=[{"role": "user", "content": long_text}],
)

for partial in stream:
    sys.stdout.write(f"\rTitle: {partial.title or '...'} | "
                     f"Sections: {len(partial.sections or [])} | "
                     f"Status: {'Complete' if partial.conclusion else 'Generating...'}")
    sys.stdout.flush()
```

### FastAPI Server-Sent Events

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

@app.post("/extract")
async def extract_stream(text: str):
    async def generate():
        client = instructor.from_provider("openai/gpt-4o-mini", async_client=True)
        stream = await client.create_partial(
            response_model=Report,
            messages=[{"role": "user", "content": text}],
        )
        async for partial in stream:
            yield f"data: {partial.model_dump_json()}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

## Limitations

1. **No validators during partial streaming** — Pydantic validators do not run on intermediate partial results, only on the final complete object
2. **Literal types need PartialLiteralMixin** — without it, incomplete Literal values cause parsing errors
3. **Token-dependent granularity** — yield frequency depends on the provider's token chunking
4. **Not all modes support streaming** — verify your provider + mode combination supports streaming
5. **Memory** — each partial yield is a new model instance; for very large schemas, consider the memory footprint
