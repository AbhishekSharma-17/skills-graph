# Framework Integrations

> Source: [langfuse.com/docs/integrations/overview](https://langfuse.com/docs/integrations/overview)

## Table of Contents

- [Overview](#overview)
- [OpenAI SDK](#openai-sdk)
- [LangChain / LangGraph](#langchain--langgraph)
- [LlamaIndex](#llamaindex)
- [Vercel AI SDK](#vercel-ai-sdk)
- [LiteLLM](#litellm)
- [CrewAI](#crewai)
- [Haystack](#haystack)
- [Other Integrations](#other-integrations)
- [Custom Integration via API](#custom-integration-via-api)

---

## Overview

Langfuse integrates with 50+ LLM frameworks and providers. Integration methods:

1. **Native SDK wrappers** — Drop-in replacements (OpenAI, LangChain)
2. **Callback handlers** — Framework-specific hooks
3. **OpenTelemetry** — Standards-based, language-agnostic
4. **REST API** — Direct HTTP calls for custom integrations

## OpenAI SDK

### Python — Drop-In Wrapper

```python
# Replace: from openai import OpenAI
from langfuse.openai import openai

# All calls automatically traced
response = openai.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}],
    # Langfuse-specific parameters (optional)
    name="my-chat",
    metadata={"feature": "greeting"},
    trace_id="custom-trace-id",
    session_id="session-123",
    user_id="user-456",
    tags=["production"],
)
```

Supports all OpenAI features: streaming, function calling, vision, embeddings, assistants.

### TypeScript — observeOpenAI

```typescript
import OpenAI from "openai";
import { observeOpenAI } from "@langfuse/openai";

const openai = observeOpenAI(new OpenAI(), {
  generationName: "my-chat",
  userId: "user-123",
});

const res = await openai.chat.completions.create({
  model: "gpt-4o",
  messages: [{ role: "user", content: "Hello!" }],
});
```

## LangChain / LangGraph

### Python

```python
from langfuse.langchain import CallbackHandler

handler = CallbackHandler(
    user_id="user-123",
    session_id="session-456",
    tags=["production"],
)

# Use with chains
response = chain.invoke(
    {"input": "Hello"},
    config={"callbacks": [handler]},
)

# Use with agents
response = agent.invoke(
    {"messages": [{"role": "user", "content": "Search for X"}]},
    config={"callbacks": [handler]},
)

# Use with LangGraph
response = graph.invoke(
    {"messages": [HumanMessage(content="Plan a trip")]},
    config={"callbacks": [handler]},
)
```

### TypeScript

```typescript
import { CallbackHandler } from "@langfuse/langchain";

const handler = new CallbackHandler({
  userId: "user-123",
  sessionId: "session-456",
});

const result = await chain.invoke(
  { input: "Hello" },
  { callbacks: [handler] }
);
```

The callback handler captures:
- All LLM calls with prompts, responses, and token usage
- Tool invocations and their results
- Chain/graph execution flow
- Retriever queries and results
- Errors and retries

## LlamaIndex

### Python

```python
from langfuse.llama_index import LlamaIndexInstrumentor

# Initialize once at app startup
instrumentor = LlamaIndexInstrumentor()
instrumentor.start()

# All LlamaIndex operations are now traced
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

documents = SimpleDirectoryReader("./data").load_data()
index = VectorStoreIndex.from_documents(documents)

query_engine = index.as_query_engine()
response = query_engine.query("What is Langfuse?")

# Cleanup
instrumentor.stop()
```

Captures: embeddings, vector store queries, LLM calls, response synthesis, node postprocessing.

## Vercel AI SDK

Requires OTEL setup (see `05-opentelemetry.md`):

```typescript
// instrumentation.ts
import { NodeSDK } from "@opentelemetry/sdk-node";
import { LangfuseSpanProcessor } from "@langfuse/otel";
const sdk = new NodeSDK({ spanProcessors: [new LangfuseSpanProcessor()] });
sdk.start();

// app/api/chat/route.ts
import { generateText, streamText } from "ai";
import { openai } from "@ai-sdk/openai";

const { text } = await generateText({
  model: openai("gpt-4o"),
  prompt: "Hello!",
  experimental_telemetry: { isEnabled: true },
});

// Streaming
const result = streamText({
  model: openai("gpt-4o"),
  messages: [{ role: "user", content: "Hello!" }],
  experimental_telemetry: {
    isEnabled: true,
    metadata: { userId: "user-123" },
  },
});
```

## LiteLLM

LiteLLM provides a unified interface for 100+ LLM providers. Langfuse integrates as a callback:

```python
import litellm

# Set Langfuse as callback
litellm.success_callback = ["langfuse"]
litellm.failure_callback = ["langfuse"]

# Environment variables required
# LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST

response = litellm.completion(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}],
    metadata={
        "trace_name": "my-request",
        "trace_user_id": "user-123",
        "session_id": "session-456",
        "tags": ["production"],
    },
)
```

### LiteLLM Proxy

For team-wide LLM gateway with built-in Langfuse tracing:

```yaml
# litellm_config.yaml
litellm_settings:
  success_callback: ["langfuse"]

environment_variables:
  LANGFUSE_PUBLIC_KEY: "pk-lf-..."
  LANGFUSE_SECRET_KEY: "sk-lf-..."
  LANGFUSE_HOST: "https://cloud.langfuse.com"
```

## CrewAI

```python
import os

os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-..."
os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-..."
os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "https://cloud.langfuse.com/api/public/otel"

from crewai import Agent, Task, Crew

# CrewAI automatically emits OTEL traces when configured
crew = Crew(agents=[agent], tasks=[task])
result = crew.kickoff()
```

## Haystack

```python
from haystack_integrations.components.connectors.langfuse import (
    LangfuseConnector,
)

tracer = LangfuseConnector(
    public_key="pk-lf-...",
    secret_key="sk-lf-...",
    name="haystack-pipeline",
)

# Add to pipeline
pipeline.add_component("tracer", tracer)
```

## Other Integrations

| Framework | Integration Type | Notes |
|-----------|-----------------|-------|
| **DSPy** | Callback | `dspy.settings.configure(trace_provider="langfuse")` |
| **Instructor** | OpenAI wrapper | Use `langfuse.openai` wrapper — traces structured outputs |
| **Anthropic** | OTEL | Via OpenLIT or OpenLLMetry instrumentation |
| **AWS Bedrock** | OTEL | Via OpenLIT auto-instrumentation |
| **Google Vertex AI** | OTEL | Via OpenLIT auto-instrumentation |
| **Cohere** | OTEL | Via OpenLIT auto-instrumentation |
| **Groq** | OpenAI-compatible | Use `langfuse.openai` with Groq's OpenAI-compatible API |

## Custom Integration via API

For frameworks without native support, use the REST API directly:

```bash
# Create a trace
curl -X POST "https://cloud.langfuse.com/api/public/ingestion" \
  -H "Authorization: Basic $(echo -n 'pk-lf-...:sk-lf-...' | base64)" \
  -H "Content-Type: application/json" \
  -d '{
    "batch": [{
      "id": "trace-1",
      "type": "trace-create",
      "timestamp": "2024-01-01T00:00:00Z",
      "body": {
        "name": "custom-trace",
        "input": {"query": "hello"},
        "output": {"response": "world"}
      }
    }]
  }'
```

The batch ingestion endpoint accepts traces, spans, generations, events, and scores in a single request.
