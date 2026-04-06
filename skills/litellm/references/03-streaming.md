# Streaming

> Source: https://docs.litellm.ai/docs/completion/stream • Written for litellm v1.52.x

LiteLLM streams responses from any provider in OpenAI's chunked format. You write one stream-handling loop and it works everywhere.

## Sync streaming

```python
from litellm import completion

response = completion(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Write a haiku about Python."}],
    stream=True,
)

for chunk in response:
    delta = chunk.choices[0].delta.content
    if delta:
        print(delta, end="", flush=True)
```

## Async streaming

```python
import asyncio
from litellm import acompletion

async def main():
    response = await acompletion(
        model="anthropic/claude-3-5-sonnet-20241022",
        messages=[{"role": "user", "content": "Hi"}],
        stream=True,
    )
    async for chunk in response:
        delta = chunk.choices[0].delta.content
        if delta:
            print(delta, end="", flush=True)

asyncio.run(main())
```

## Chunk shape

Each chunk is an OpenAI `ChatCompletionChunk`:

```python
ModelResponseStream(
    id="chatcmpl-...",
    object="chat.completion.chunk",
    created=...,
    model="gpt-4o-mini",
    choices=[
        StreamingChoices(
            index=0,
            delta=Delta(
                role="assistant",          # only on first chunk
                content="Hello",            # incremental text
                tool_calls=[...],           # if streaming tool calls
            ),
            finish_reason=None,             # set on final chunk
        )
    ],
)
```

The first chunk usually contains `role="assistant"` with empty content. The last chunk has `finish_reason` set and `delta.content=None`.

## Reconstructing the full message

```python
chunks = []
for chunk in response:
    chunks.append(chunk)

from litellm import stream_chunk_builder
full = stream_chunk_builder(chunks, messages=messages)
print(full.choices[0].message.content)
print(full.usage.completion_tokens)
```

`stream_chunk_builder` reassembles the streamed deltas into a regular `ModelResponse`, including a usage estimate (token counts via tiktoken when the provider doesn't include them in the final chunk).

## Streaming + usage

By default, most providers do NOT send token usage in stream chunks. To force it:

```python
completion(
    model="gpt-4o-mini",
    messages=[...],
    stream=True,
    stream_options={"include_usage": True},
)
```

The final chunk then includes `chunk.usage`.

## Streaming tool calls

Tool call arguments stream piece-by-piece. Accumulate them per-call by index:

```python
from collections import defaultdict
import json

tool_calls = defaultdict(lambda: {"name": "", "arguments": ""})

for chunk in response:
    for tc in chunk.choices[0].delta.tool_calls or []:
        idx = tc.index
        if tc.function.name:
            tool_calls[idx]["name"] = tc.function.name
        if tc.function.arguments:
            tool_calls[idx]["arguments"] += tc.function.arguments

for idx, call in tool_calls.items():
    args = json.loads(call["arguments"])
    print(call["name"], args)
```

## Server-Sent Events passthrough

If you're proxying a stream to a browser (FastAPI/Starlette example):

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from litellm import acompletion

app = FastAPI()

@app.post("/chat")
async def chat(messages: list[dict]):
    async def generator():
        response = await acompletion(
            model="gpt-4o-mini",
            messages=messages,
            stream=True,
        )
        async for chunk in response:
            yield f"data: {chunk.json()}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generator(), media_type="text/event-stream")
```

## Common pitfalls

- **Forgetting `stream=True`** — Without it you get a regular response, not an iterator.
- **Skipping `None` content** — The first chunk often has `delta.content=None`. Always guard before concatenating.
- **Token counts missing** — Add `stream_options={"include_usage": True}` or use `stream_chunk_builder`.
- **Mixing sync iterator with async function** — If you call `completion(...)` (not `acompletion`) inside async code, you'll block the event loop.
- **Long streams + retries** — Retries discard partial output. Don't enable both for long generations.

## Related
- Async patterns → `04-async.md`
- Tool calling → `11-structured-outputs.md`
