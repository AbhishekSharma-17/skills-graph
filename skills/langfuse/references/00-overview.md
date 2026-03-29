# Langfuse — Overview & Setup

> Source: [langfuse.com/docs](https://langfuse.com/docs) | Version: v3.162.0 | License: MIT

## Table of Contents

- [What is Langfuse](#what-is-langfuse)
- [Core Capabilities](#core-capabilities)
- [Architecture](#architecture)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Python Quickstart](#python-quickstart)
- [TypeScript Quickstart](#typescript-quickstart)
- [SDK Design Principles](#sdk-design-principles)
- [When to Use Langfuse](#when-to-use-langfuse)

---

## What is Langfuse

Langfuse is an open-source LLM engineering platform that provides observability, evaluation, and prompt management for AI applications. It records the complete lifecycle of requests as they flow through your system — capturing LLM calls, tool executions, retrieval steps, and custom logic with timing, cost, and metadata.

Key differentiators:
- **Open source** and self-hostable (MIT license)
- **OpenTelemetry-native** — built on OTEL standards, accepts OTLP traces
- **Framework-agnostic** — works with any LLM provider or framework
- **Async by design** — tracing data sent in the background, zero impact on app latency
- **50+ integrations** — LangChain, LlamaIndex, OpenAI SDK, Vercel AI SDK, LiteLLM, and more

YC W23 backed. 24K+ GitHub stars.

## Core Capabilities

### 1. Observability (Tracing)
- End-to-end request tracing with nested spans and generations
- Token usage, cost, and latency tracking per model
- Session grouping for multi-turn conversations
- User-level tracking and segmentation
- Dashboard metrics with custom filters

### 2. Prompt Management
- Version-controlled prompt storage with labels (production, staging)
- Template variables with `{{variable}}` syntax
- Client-side caching for zero-latency prompt retrieval
- Link prompts to traces to measure version performance

### 3. Evaluation
- Datasets for structured benchmarking
- Experiments to compare prompt versions and model configs
- LLM-as-a-judge for automated quality assessment
- Human annotation queues for manual review
- Custom scoring via SDKs/API

### 4. Analytics
- Cost and latency broken down by user, model, prompt version, feature
- Custom dashboards with filterable widgets
- Export to PostHog, Mixpanel, or via Metrics API

## Architecture

```
Your App ──> Langfuse SDK (async) ──> Langfuse Server
                                        ├── Web UI + API (Next.js)
                                        ├── Async Worker (event processing)
                                        ├── Postgres (OLTP)
                                        ├── ClickHouse (OLAP / analytics)
                                        ├── Redis/Valkey (cache + queue)
                                        └── S3/Blob (raw events, attachments)
```

Tracing is fully asynchronous: the SDK queues events locally and flushes in batches. Your app's response time is unaffected.

## Installation

### Python

```bash
pip install langfuse
```

### JavaScript / TypeScript

```bash
# OpenAI drop-in wrapper
npm install @langfuse/openai

# LangChain integration
npm install @langfuse/core @langfuse/langchain

# OTEL-native SDK (recommended for new projects)
npm install @langfuse/tracing @langfuse/otel @opentelemetry/sdk-node

# Vercel AI SDK
npm install ai @ai-sdk/openai @langfuse/tracing @langfuse/otel @opentelemetry/sdk-node
```

## Environment Variables

```bash
# Required for all SDKs
LANGFUSE_SECRET_KEY="sk-lf-..."
LANGFUSE_PUBLIC_KEY="pk-lf-..."

# Region-specific base URLs
LANGFUSE_BASE_URL="https://cloud.langfuse.com"       # EU (default)
LANGFUSE_BASE_URL="https://us.cloud.langfuse.com"    # US

# Self-hosted
LANGFUSE_BASE_URL="http://localhost:3000"
```

Get your keys from: Langfuse Dashboard > Project Settings > API Keys.

## Python Quickstart

### Decorator-Based (Recommended)

```python
from langfuse import observe, get_client
from langfuse.openai import openai  # Drop-in OpenAI wrapper

langfuse = get_client()

@observe()
def answer_question(question: str) -> str:
    response = openai.chat.completions.create(
        name="qa-generation",
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Answer concisely."},
            {"role": "user", "content": question},
        ],
    )
    return response.choices[0].message.content

# Traces automatically captured
result = answer_question("What is Langfuse?")
langfuse.flush()  # Required in short-lived scripts
```

### Context Manager (Low-Level)

```python
from langfuse import get_client

langfuse = get_client()

with langfuse.start_as_current_observation(
    as_type="span", name="process-request"
) as span:
    span.update(input={"query": "hello"})

    with langfuse.start_as_current_observation(
        as_type="generation", name="llm-call", model="gpt-4o"
    ) as gen:
        gen.update(output="Generated response", usage={"input": 50, "output": 20})

    span.update(output="Done")

langfuse.flush()
```

## TypeScript Quickstart

### OTEL-Native (Recommended)

```typescript
import { NodeSDK } from "@opentelemetry/sdk-node";
import { LangfuseSpanProcessor } from "@langfuse/otel";

// Initialize BEFORE any other imports
const sdk = new NodeSDK({
  spanProcessors: [new LangfuseSpanProcessor()],
});
sdk.start();

import OpenAI from "openai";
import { observeOpenAI } from "@langfuse/openai";

const openai = observeOpenAI(new OpenAI());

const res = await openai.chat.completions.create({
  messages: [{ role: "user", content: "Hello!" }],
  model: "gpt-4o",
});
```

### Manual Tracing

```typescript
import { startActiveObservation, startObservation } from "@langfuse/tracing";

await startActiveObservation("user-request", async (span) => {
  span.update({ input: { query: "What is the capital of France?" } });

  const gen = startObservation("llm-call", {
    model: "gpt-4",
    input: [{ role: "user", content: "What is the capital of France?" }],
  }, { asType: "generation" });

  gen.update({ output: { content: "Paris." } }).end();
  span.update({ output: "Success" });
});
```

## SDK Design Principles

1. **Zero latency impact** — all telemetry sent asynchronously via background batching
2. **Graceful degradation** — SDK failures never crash your app
3. **Context propagation** — nested spans inherit parent context automatically
4. **Singleton client** — `get_client()` returns a shared instance
5. **Flush on shutdown** — call `langfuse.flush()` in short-lived apps (scripts, lambdas)

## When to Use Langfuse

| Use Case | Langfuse Feature |
|----------|-----------------|
| Debug why an LLM response was wrong | Trace viewer with full prompt/response |
| Track costs across models and features | Analytics dashboards |
| A/B test prompt versions | Prompt management + experiments |
| Automated quality checks | LLM-as-a-judge evaluators |
| Regression testing before deploys | Datasets + experiments |
| Multi-turn chatbot debugging | Session grouping |
| Monitor production quality | Live evaluators + dashboards |
| Comply with data privacy reqs | Data masking + self-hosting |
