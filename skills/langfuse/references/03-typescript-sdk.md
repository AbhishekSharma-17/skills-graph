# TypeScript SDK

> Source: [langfuse.com/docs/sdk/typescript](https://langfuse.com/docs/sdk/typescript)

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [OTEL-Native Setup](#otel-native-setup)
- [OpenAI Drop-In Wrapper](#openai-drop-in-wrapper)
- [Manual Tracing](#manual-tracing)
- [Vercel AI SDK Integration](#vercel-ai-sdk-integration)
- [LangChain Callback Handler](#langchain-callback-handler)
- [Trace Attributes](#trace-attributes)
- [Scoring](#scoring)
- [Configuration](#configuration)
- [Common Patterns](#common-patterns)
- [Pitfalls](#pitfalls)

---

## Overview

The Langfuse TypeScript SDK provides OTEL-native tracing for JavaScript and TypeScript applications. It is built on top of OpenTelemetry and converts emitted spans into rich Langfuse observations with LLM-specific features like token usage, cost tracking, and prompt linking.

## Installation

```bash
# OTEL-native SDK (recommended)
npm install @langfuse/tracing @langfuse/otel @opentelemetry/sdk-node

# OpenAI wrapper
npm install @langfuse/openai

# LangChain integration
npm install @langfuse/core @langfuse/langchain

# Vercel AI SDK
npm install ai @ai-sdk/openai @langfuse/tracing @langfuse/otel @opentelemetry/sdk-node
```

## OTEL-Native Setup

Initialize the OpenTelemetry SDK **before** importing any libraries you want to trace:

```typescript
// instrumentation.ts — must be the first import
import { NodeSDK } from "@opentelemetry/sdk-node";
import { LangfuseSpanProcessor } from "@langfuse/otel";

const sdk = new NodeSDK({
  spanProcessors: [new LangfuseSpanProcessor()],
});

sdk.start();
```

Environment variables:

```bash
LANGFUSE_SECRET_KEY="sk-lf-..."
LANGFUSE_PUBLIC_KEY="pk-lf-..."
LANGFUSE_BASE_URL="https://cloud.langfuse.com"
```

## OpenAI Drop-In Wrapper

Wrap your OpenAI client for automatic tracing:

```typescript
import OpenAI from "openai";
import { observeOpenAI } from "@langfuse/openai";

const openai = observeOpenAI(new OpenAI());

// All calls now traced
const res = await openai.chat.completions.create({
  messages: [{ role: "user", content: "Hello!" }],
  model: "gpt-4o",
});
```

With custom trace attributes:

```typescript
const openai = observeOpenAI(new OpenAI(), {
  generationName: "my-chat",
  metadata: { feature: "chatbot" },
  userId: "user-123",
  sessionId: "session-456",
  tags: ["production"],
});
```

## Manual Tracing

### startActiveObservation

Creates a span that becomes the active context for nested calls:

```typescript
import { startActiveObservation, startObservation } from "@langfuse/tracing";

const result = await startActiveObservation("process-request", async (span) => {
  span.update({
    input: { query: "What is the capital of France?" },
    metadata: { pipeline: "qa" },
  });

  // Nested generation
  const generation = startObservation(
    "llm-call",
    {
      model: "gpt-4o",
      input: [{ role: "user", content: "What is the capital of France?" }],
    },
    { asType: "generation" }
  );

  const response = await openai.chat.completions.create({
    model: "gpt-4o",
    messages: [{ role: "user", content: "What is the capital of France?" }],
  });

  generation
    .update({
      output: { content: response.choices[0].message.content },
      usage: {
        input: response.usage?.prompt_tokens,
        output: response.usage?.completion_tokens,
      },
    })
    .end();

  span.update({ output: "Successfully answered." });
  return response.choices[0].message.content;
});
```

### startObservation

Creates a standalone span (not active context):

```typescript
import { startObservation } from "@langfuse/tracing";

const span = startObservation("background-task", {
  input: { taskId: "123" },
});

// Do work...

span.update({ output: { status: "complete" } }).end();
```

## Vercel AI SDK Integration

Langfuse integrates with the Vercel AI SDK via OpenTelemetry:

```typescript
// Initialize OTEL first (see OTEL-Native Setup above)

import { generateText, streamText } from "ai";
import { openai } from "@ai-sdk/openai";

// generateText — traced automatically
const { text } = await generateText({
  model: openai("gpt-4o"),
  prompt: "What is the weather like today?",
  experimental_telemetry: { isEnabled: true },
});

// streamText — also traced
const result = streamText({
  model: openai("gpt-4o"),
  prompt: "Write a haiku about programming.",
  experimental_telemetry: { isEnabled: true },
});
```

## LangChain Callback Handler

```typescript
import { CallbackHandler } from "@langfuse/langchain";

const langfuseHandler = new CallbackHandler({
  userId: "user-123",
  sessionId: "session-456",
  tags: ["production"],
});

const response = await agent.invoke(
  { messages: [{ role: "user", content: "What's the weather?" }] },
  { callbacks: [langfuseHandler] }
);
```

## Trace Attributes

Set trace-level attributes on spans:

```typescript
import { setTraceAttributes } from "@langfuse/tracing";

// Set attributes that apply to the entire trace
setTraceAttributes({
  userId: "user-123",
  sessionId: "session-456",
  tags: ["production", "v2"],
  metadata: { feature: "search", region: "us-east" },
  release: "v2.0.1",
});
```

## Scoring

Add scores to traces programmatically:

```typescript
import { LangfuseClient } from "@langfuse/client";

const langfuse = new LangfuseClient();

// Score a trace
await langfuse.score.create({
  traceId: "trace-id",
  name: "user-feedback",
  value: 1,
  comment: "Thumbs up",
});

// Score a specific observation
await langfuse.score.create({
  traceId: "trace-id",
  observationId: "generation-id",
  name: "relevance",
  value: 0.9,
});
```

## Configuration

### LangfuseSpanProcessor Options

```typescript
new LangfuseSpanProcessor({
  secretKey: "sk-lf-...",
  publicKey: "pk-lf-...",
  baseUrl: "https://cloud.langfuse.com",
  flushAt: 15,           // Batch size before flush
  flushInterval: 1000,   // Flush interval (ms)
  enabled: true,         // Disable for testing
  sampleRate: 1.0,       // Sampling rate (0-1)
});
```

### Environment Variables

```bash
LANGFUSE_SECRET_KEY="sk-lf-..."
LANGFUSE_PUBLIC_KEY="pk-lf-..."
LANGFUSE_BASE_URL="https://cloud.langfuse.com"
LANGFUSE_ENABLED="true"
LANGFUSE_SAMPLE_RATE="1.0"
```

## Common Patterns

### Next.js API Route

```typescript
// app/api/chat/route.ts
import { startActiveObservation } from "@langfuse/tracing";

export async function POST(req: Request) {
  const { message } = await req.json();

  const response = await startActiveObservation("chat-api", async (span) => {
    span.update({ input: { message } });
    const result = await processChat(message);
    span.update({ output: { result } });
    return result;
  });

  return Response.json({ response });
}
```

### Express Middleware

```typescript
import { startActiveObservation, setTraceAttributes } from "@langfuse/tracing";

app.use((req, res, next) => {
  startActiveObservation(`${req.method} ${req.path}`, async (span) => {
    setTraceAttributes({
      metadata: { method: req.method, path: req.path },
    });
    next();
  });
});
```

## Pitfalls

1. **Import order** — The OTEL SDK must be initialized before importing libraries you want to trace. Put `instrumentation.ts` as the first import in your entry file.

2. **Missing `experimental_telemetry`** — Vercel AI SDK requires `experimental_telemetry: { isEnabled: true }` on each call. Without it, traces aren't emitted.

3. **Edge runtime** — The Node.js OTEL SDK doesn't work in edge runtimes (Cloudflare Workers, Vercel Edge). Use the Langfuse REST API directly for edge environments.

4. **Not ending observations** — Call `.end()` on manually created observations. Unended observations have inaccurate duration data.

5. **Serverless cold starts** — The OTEL SDK initialization adds a small overhead on cold starts. This is typically <100ms and only affects the first request.
