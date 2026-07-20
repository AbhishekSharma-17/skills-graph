# Instructor — Async Patterns

> Source: https://python.useinstructor.com | v1.15.4

## Table of Contents

- [Async Client Setup](#async-client-setup)
- [Basic Async Extraction](#basic-async-extraction)
- [Concurrent Extraction with gather](#concurrent-extraction-with-gather)
- [Processing as Completed](#processing-as-completed)
- [Rate Limiting](#rate-limiting)
- [Async Streaming](#async-streaming)
- [FastAPI Integration](#fastapi-integration)
- [Error Handling in Async](#error-handling-in-async)
- [Production Patterns](#production-patterns)

## Async Client Setup

Create an async client by setting `async_client=True`:

```python
import instructor

client = instructor.from_provider(
    "openai/gpt-4o-mini",
    async_client=True,
)
```

All client methods become awaitable. The async client supports the same features as sync: retries, hooks, streaming, context.

## Basic Async Extraction

```python
import asyncio
import instructor
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int

async def main():
    client = instructor.from_provider("openai/gpt-4o-mini", async_client=True)

    user = await client.create(
        response_model=User,
        messages=[{"role": "user", "content": "Extract: Jason is 25"}],
    )
    print(user)

asyncio.run(main())
```

## Concurrent Extraction with gather

Process multiple inputs simultaneously:

```python
import asyncio

async def extract_user(client, text: str) -> User:
    return await client.create(
        response_model=User,
        messages=[{"role": "user", "content": f"Extract: {text}"}],
    )

async def main():
    client = instructor.from_provider("openai/gpt-4o-mini", async_client=True)

    texts = [
        "Jason is 25, an engineer",
        "Sarah is 30, a designer",
        "Mike is 28, a manager",
        "Lisa is 35, a director",
    ]

    users = await asyncio.gather(
        *[extract_user(client, text) for text in texts]
    )

    for user in users:
        print(f"{user.name}: {user.age}")

asyncio.run(main())
```

`asyncio.gather` returns results in input order, regardless of completion order.

## Processing as Completed

Process results as they arrive for lower time-to-first-result:

```python
async def main():
    client = instructor.from_provider("openai/gpt-4o-mini", async_client=True)

    texts = ["Jason is 25", "Sarah is 30", "Mike is 28"]

    tasks = [
        asyncio.create_task(extract_user(client, text))
        for text in texts
    ]

    for coro in asyncio.as_completed(tasks):
        user = await coro
        print(f"Completed: {user.name}: {user.age}")
        # Process immediately — don't wait for all to finish

asyncio.run(main())
```

### gather vs as_completed

| Feature | `gather` | `as_completed` |
|---------|----------|----------------|
| Result order | Input order | Completion order |
| Wait behavior | All tasks | One at a time |
| Best for | Need all results together | Progressive processing |
| Error handling | Fails all or returns exceptions | Handle per-task |

## Rate Limiting

Control concurrent requests with `asyncio.Semaphore`:

```python
async def extract_with_limit(
    sem: asyncio.Semaphore,
    client,
    text: str,
) -> User:
    async with sem:  # Limits concurrent requests
        return await client.create(
            response_model=User,
            messages=[{"role": "user", "content": f"Extract: {text}"}],
        )

async def main():
    client = instructor.from_provider("openai/gpt-4o-mini", async_client=True)
    sem = asyncio.Semaphore(5)  # Max 5 concurrent requests

    texts = [f"Person {i} is {20+i}" for i in range(50)]

    users = await asyncio.gather(
        *[extract_with_limit(sem, client, text) for text in texts]
    )

asyncio.run(main())
```

### With Backoff on Rate Limit Errors

```python
from tenacity import retry, retry_if_exception_type, wait_exponential, stop_after_attempt

@retry(
    retry=retry_if_exception_type(Exception),
    wait=wait_exponential(min=1, max=60),
    stop=stop_after_attempt(5),
)
async def extract_with_retry(client, text: str) -> User:
    return await client.create(
        response_model=User,
        messages=[{"role": "user", "content": f"Extract: {text}"}],
    )
```

## Async Streaming

### Async Partial Streaming

```python
async def stream_extraction():
    client = instructor.from_provider("openai/gpt-4o-mini", async_client=True)

    stream = await client.create_partial(
        response_model=Report,
        messages=[{"role": "user", "content": "Analyze this text..."}],
    )

    async for partial in stream:
        print(partial.model_dump())

asyncio.run(stream_extraction())
```

### Async Iterable Streaming

```python
from typing import Iterable

async def stream_people():
    client = instructor.from_provider("openai/gpt-4o-mini", async_client=True)

    people = await client.create(
        response_model=Iterable[Person],
        stream=True,
        messages=[{"role": "user", "content": "Extract all people..."}],
    )

    async for person in people:
        print(f"{person.name}: {person.age}")

asyncio.run(stream_people())
```

## FastAPI Integration

### Basic Endpoint

```python
from fastapi import FastAPI
from pydantic import BaseModel
import instructor

app = FastAPI()

client = instructor.from_provider("openai/gpt-4o-mini", async_client=True)

class ExtractRequest(BaseModel):
    text: str

class UserInfo(BaseModel):
    name: str
    age: int
    email: str | None = None

@app.post("/extract", response_model=UserInfo)
async def extract_user(request: ExtractRequest):
    return await client.create(
        response_model=UserInfo,
        messages=[{"role": "user", "content": f"Extract: {request.text}"}],
        max_retries=2,
    )
```

### Streaming Endpoint with SSE

```python
from fastapi.responses import StreamingResponse

@app.post("/extract/stream")
async def extract_stream(request: ExtractRequest):
    async def generate():
        stream = await client.create_partial(
            response_model=UserInfo,
            messages=[{"role": "user", "content": f"Extract: {request.text}"}],
        )
        async for partial in stream:
            yield f"data: {partial.model_dump_json()}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

## Error Handling in Async

```python
from instructor.exceptions import InstructorRetryException

async def safe_extract(client, text: str) -> User | None:
    try:
        return await client.create(
            response_model=User,
            messages=[{"role": "user", "content": f"Extract: {text}"}],
            max_retries=3,
        )
    except InstructorRetryException as e:
        print(f"Failed after {e.n_attempts} attempts: {text}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

async def main():
    client = instructor.from_provider("openai/gpt-4o-mini", async_client=True)

    texts = ["Jason is 25", "invalid garbage text", "Sarah is 30"]

    results = await asyncio.gather(
        *[safe_extract(client, text) for text in texts]
    )

    users = [r for r in results if r is not None]
```

## Production Patterns

### Worker Pool with Queue

```python
async def worker(
    queue: asyncio.Queue,
    client,
    results: list,
):
    while True:
        text = await queue.get()
        try:
            user = await client.create(
                response_model=User,
                messages=[{"role": "user", "content": f"Extract: {text}"}],
                max_retries=2,
            )
            results.append(user)
        except Exception as e:
            print(f"Worker error: {e}")
        finally:
            queue.task_done()

async def main():
    client = instructor.from_provider("openai/gpt-4o-mini", async_client=True)

    queue = asyncio.Queue()
    results = []

    # Create 5 workers
    workers = [
        asyncio.create_task(worker(queue, client, results))
        for _ in range(5)
    ]

    # Enqueue work
    texts = [f"Person {i} is {20+i}" for i in range(100)]
    for text in texts:
        await queue.put(text)

    # Wait for completion
    await queue.join()

    # Cancel workers
    for w in workers:
        w.cancel()

asyncio.run(main())
```

### Timeout Wrapper

```python
async def extract_with_timeout(client, text: str, timeout: float = 30.0) -> User:
    return await asyncio.wait_for(
        client.create(
            response_model=User,
            messages=[{"role": "user", "content": f"Extract: {text}"}],
        ),
        timeout=timeout,
    )
```
