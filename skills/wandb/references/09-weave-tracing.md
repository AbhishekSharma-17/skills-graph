# Weave Tracing

> Source: [docs.wandb.ai/weave](https://docs.wandb.ai/weave/) | weave (latest)

## Table of Contents

- [Overview](#overview)
- [Installation and Setup](#installation-and-setup)
- [Core Concepts](#core-concepts)
- [Decorating Functions with @weave.op](#decorating-functions-with-weaveop)
- [Automatic LLM Provider Tracing](#automatic-llm-provider-tracing)
- [Nested Traces](#nested-traces)
- [weave.Model for Structured Experiments](#weavemodel-for-structured-experiments)
- [Cost Tracking](#cost-tracking)
- [Threads and Sessions](#threads-and-sessions)
- [Querying Traces](#querying-traces)
- [TypeScript Support](#typescript-support)
- [Common Patterns](#common-patterns)

## Overview

W&B Weave is an observability and evaluation platform for LLM applications. Where W&B Models tracks training loops with `wandb.init()` and `wandb.log()`, Weave tracks inference-time behavior — LLM calls, tool use, agent steps, and application logic.

```
W&B Models → Training workflows (epochs, gradients, checkpoints)
W&B Weave  → Application workflows (LLM calls, RAG, agents, evals)
```

## Installation and Setup

```bash
pip install weave
```

```python
import weave

# Initialize — creates project if needed
weave.init("my-team/my-llm-app")
# All subsequent @weave.op calls and LLM provider calls are auto-traced
```

Authentication uses the same `WANDB_API_KEY` as wandb.

## Core Concepts

| Concept | Description |
|---------|-------------|
| **Op** | A decorated function that auto-logs inputs, outputs, code, and timing |
| **Call** | A single execution of an Op — the logged record |
| **Trace** | A tree of related Calls sharing the same execution context |
| **Thread** | A collection of Traces representing a session or conversation |

### Hierarchy

```
Thread (session/conversation)
├── Trace 1 (user message → response)
│   ├── Call: process_query()
│   │   ├── Call: retrieve_docs()
│   │   └── Call: openai.chat.completions.create()
│   └── Call: format_response()
└── Trace 2 (follow-up message → response)
    └── ...
```

## Decorating Functions with @weave.op

The `@weave.op()` decorator automatically captures:
- Function source code (versioned)
- Input arguments
- Return value
- Execution time
- Errors and exceptions
- Parent-child relationships (nested calls)

```python
import weave

weave.init("my-project")

@weave.op()
def extract_keywords(text: str) -> list[str]:
    # Your logic here
    return ["keyword1", "keyword2"]

@weave.op()
def summarize(text: str) -> str:
    keywords = extract_keywords(text)  # Automatically nested in trace
    return f"Summary with {len(keywords)} keywords"

result = summarize("Long document text...")
# Both calls appear in the Weave UI as a trace tree
```

### Async Support

```python
@weave.op()
async def async_process(query: str) -> str:
    result = await some_async_operation(query)
    return result
```

## Automatic LLM Provider Tracing

After `weave.init()`, LLM provider calls are automatically patched — no extra code needed.

### OpenAI

```python
from openai import OpenAI

weave.init("my-project")
client = OpenAI()

# Automatically traced — no decorator needed
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}],
)
```

Traced data: model, messages, response, tokens, cost, latency.

### Anthropic

```python
from anthropic import Anthropic

weave.init("my-project")
client = Anthropic()

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}],
)
```

### Supported Providers (Auto-Patched)

| Provider | Import | Auto-Traced |
|----------|--------|-------------|
| OpenAI | `openai` | Chat, completions, embeddings, assistants |
| Anthropic | `anthropic` | Messages, tool use, streaming |
| Cohere | `cohere` | Chat, embed, rerank |
| Mistral | `mistralai` | Chat completions |
| Google AI | `google.generativeai` | Generate content |
| LiteLLM | `litellm` | All supported providers |

### Manual Patching

```python
# If auto-patching doesn't work, patch explicitly
weave.integrations.patch_openai()
weave.integrations.patch_anthropic()
```

## Nested Traces

Weave automatically nests calls based on the Python call stack:

```python
@weave.op()
def rag_pipeline(query: str) -> str:
    docs = retrieve(query)      # Child call 1
    context = format_docs(docs)  # Child call 2
    answer = generate(query, context)  # Child call 3
    return answer

@weave.op()
def retrieve(query: str) -> list[str]:
    embedding = embed(query)     # Grandchild call
    return search(embedding)

@weave.op()
def embed(text: str) -> list[float]:
    return openai_client.embeddings.create(input=text, model="text-embedding-3-small")

@weave.op()
def generate(query: str, context: str) -> str:
    return openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": f"Context: {context}"},
            {"role": "user", "content": query},
        ],
    )
```

Result in Weave UI:

```
rag_pipeline(query="What is RAG?")
├── retrieve(query="What is RAG?")
│   ├── embed(text="What is RAG?")
│   │   └── openai.embeddings.create(...)
│   └── search(...)
├── format_docs(docs=[...])
└── generate(query="What is RAG?", context="...")
    └── openai.chat.completions.create(...)
```

## weave.Model for Structured Experiments

Use `weave.Model` to version experimental parameters alongside traces:

```python
class RAGModel(weave.Model):
    system_prompt: str
    temperature: float
    model_name: str
    top_k: int

    @weave.op()
    def predict(self, question: str) -> str:
        docs = retrieve(question, top_k=self.top_k)
        response = openai_client.chat.completions.create(
            model=self.model_name,
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Context: {docs}\n\nQ: {question}"},
            ],
        )
        return response.choices[0].message.content

# Each configuration creates a new versioned model
model_v1 = RAGModel(
    system_prompt="You are a helpful assistant.",
    temperature=0.7,
    model_name="gpt-4o",
    top_k=5,
)
model_v1.predict("What is machine learning?")
```

Changing any parameter (e.g., `temperature=0.3`) creates a new model version in Weave, making it easy to compare configurations.

## Cost Tracking

Weave automatically calculates costs for supported providers using current pricing:

- OpenAI: all chat, completion, and embedding models
- Anthropic: all Claude models
- Other providers: where pricing data is available

Costs appear in the Weave UI per-call and per-trace, broken down by input/output tokens.

## Threads and Sessions

Group related traces into threads for conversation-level analysis:

```python
@weave.op()
def chat(message: str, thread_id: str) -> str:
    # Thread ID groups traces together
    return process_message(message)
```

## Querying Traces

### Via UI

The Weave UI provides:
- **Trace list** — all traces with filtering and sorting
- **Trace detail** — drill into individual traces, see call tree
- **Latency analysis** — identify slow operations
- **Error tracking** — filter failed calls
- **Cost dashboard** — aggregate spending by model, time, or function

### Via Python SDK

```python
import weave

client = weave.init("my-project")
calls = client.get_calls(
    filter={"op_name": "rag_pipeline"},
    limit=100,
)
for call in calls:
    print(f"Latency: {call.summary['latency_ms']}ms")
```

## TypeScript Support

```typescript
import * as weave from 'weave';
import { wrapOpenAI } from 'weave';
import OpenAI from 'openai';

await weave.init('my-project');
const client = wrapOpenAI(new OpenAI());

const askQuestion = weave.op(async (question: string) => {
  const response = await client.chat.completions.create({
    model: 'gpt-4o',
    messages: [{ role: 'user', content: question }],
  });
  return response.choices[0].message.content;
}, { name: 'askQuestion' });

await askQuestion('What is TypeScript?');
```

For Anthropic in TypeScript: use `wrapAnthropic()`.

## Common Patterns

### Agent Tracing

```python
@weave.op()
def agent_loop(query: str) -> str:
    messages = [{"role": "user", "content": query}]
    
    for _ in range(10):
        response = call_llm(messages)
        if response.tool_calls:
            results = execute_tools(response.tool_calls)
            messages.extend(format_tool_results(results))
        else:
            return response.content
    
    return "Max iterations reached"

@weave.op()
def execute_tools(tool_calls: list) -> list:
    return [run_tool(tc) for tc in tool_calls]
```

### RAG Pipeline with Retrieval Metrics

```python
@weave.op()
def rag_with_metrics(query: str) -> dict:
    docs = retrieve(query)
    answer = generate(query, docs)
    return {
        "answer": answer,
        "num_docs": len(docs),
        "doc_scores": [d.score for d in docs],
    }
```

## Related

- Weave Evaluations → `references/10-weave-evaluations.md`
- Integrations → `references/11-integrations.md`
- Overview → `references/00-overview.md`
