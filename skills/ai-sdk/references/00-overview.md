# AI SDK Overview

> Source: https://ai-sdk.dev/docs/introduction

## What is AI SDK?

AI SDK is a TypeScript toolkit by Vercel for building AI-powered applications. It provides a unified API for working with large language models across multiple providers (OpenAI, Anthropic, Google, Mistral, and 30+ others) with first-class support for streaming, tool calling, structured output, agents, and React/Next.js integration.

## When to Use AI SDK

- Building chatbots or conversational UIs
- Streaming AI responses in real-time
- Tool calling / function calling with LLMs
- Generating structured data (JSON) from LLMs
- Building AI agents with multi-step reasoning
- Multi-provider applications (switch between OpenAI, Anthropic, etc.)
- React/Next.js applications with AI features
- Embedding and RAG (Retrieval-Augmented Generation) workflows

## Architecture Layers

AI SDK is organized into four layers:

### AI SDK Core (`ai`)
Server-side functions for text generation, structured output, tool calling, agents, embeddings, and more. Provider-agnostic.

### AI SDK UI (`@ai-sdk/react`, `@ai-sdk/svelte`, `@ai-sdk/vue`)
Framework-specific hooks for building chat interfaces, completions, and generative UIs.

### AI SDK RSC (`ai/rsc`)
React Server Components integration for streaming React components from the server.

### AI SDK Providers (`@ai-sdk/openai`, `@ai-sdk/anthropic`, etc.)
Provider implementations that connect the unified API to specific LLM services.

## Installation

```bash
# Core + provider(s)
npm install ai @ai-sdk/openai @ai-sdk/anthropic

# With React hooks
npm install @ai-sdk/react

# Full stack (Next.js)
npm install ai @ai-sdk/react @ai-sdk/openai
```

## Environment Setup

```bash
# .env.local
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_GENERATIVE_AI_API_KEY=...
```

## Quick Start — Generate Text

```typescript
import { generateText } from 'ai';

const { text } = await generateText({
  model: 'anthropic/claude-sonnet-4.5',
  prompt: 'Explain quantum computing in simple terms.',
});

console.log(text);
```

## Quick Start — Stream Text

```typescript
import { streamText } from 'ai';

const result = streamText({
  model: 'openai/gpt-5.2',
  prompt: 'Write a short story about a robot.',
});

for await (const chunk of result.textStream) {
  process.stdout.write(chunk);
}
```

## Quick Start — Chat API Route (Next.js)

```typescript
// app/api/chat/route.ts
import { streamText, UIMessage, convertToModelMessages } from 'ai';

export async function POST(req: Request) {
  const { messages }: { messages: UIMessage[] } = await req.json();

  const result = streamText({
    model: 'anthropic/claude-sonnet-4.5',
    system: 'You are a helpful assistant.',
    messages: await convertToModelMessages(messages),
  });

  return result.toUIMessageStreamResponse();
}
```

```typescript
// app/page.tsx
'use client';
import { useChat } from '@ai-sdk/react';
import { DefaultChatTransport } from 'ai';

export default function Chat() {
  const { messages, sendMessage, status } = useChat({
    transport: new DefaultChatTransport({ api: '/api/chat' }),
  });

  return (
    <div>
      {messages.map(m => (
        <div key={m.id}>
          {m.role}: {m.parts.map(p => p.type === 'text' ? p.text : null)}
        </div>
      ))}
    </div>
  );
}
```

## Quick Start — Tool Calling

```typescript
import { generateText, tool } from 'ai';
import { z } from 'zod';

const { text } = await generateText({
  model: 'anthropic/claude-sonnet-4.5',
  tools: {
    weather: tool({
      description: 'Get weather for a location',
      inputSchema: z.object({ city: z.string() }),
      execute: async ({ city }) => `${city}: 72°F, sunny`,
    }),
  },
  prompt: 'What is the weather in Tokyo?',
});
```

## Quick Start — Structured Output

```typescript
import { generateText, Output } from 'ai';
import { z } from 'zod';

const { output } = await generateText({
  model: 'openai/gpt-5.2',
  output: Output.object({
    schema: z.object({
      name: z.string(),
      ingredients: z.array(z.string()),
      steps: z.array(z.string()),
    }),
  }),
  prompt: 'Generate a pasta recipe.',
});
```

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Provider** | Service that hosts LLM models (OpenAI, Anthropic, etc.) |
| **Model** | Specific LLM instance (e.g., `claude-sonnet-4.5`) |
| **Tool** | Function the LLM can invoke during generation |
| **Agent** | LLM + tools + loop for multi-step reasoning |
| **Streaming** | Progressive response delivery for real-time UIs |
| **Structured Output** | Type-safe JSON generation with schema validation |
| **MCP** | Model Context Protocol for connecting external tool servers |
| **Middleware** | Interceptors for logging, caching, rate limiting |

## Version History

- **v6.0** (2026) — Agents, MCP stable, DevTools, tool approval, reranking
- **v5.0** (2025) — Language Model Spec v2, provider registry
- **v4.0** (2025) — AI SDK Core rewrite, streaming improvements
- **v3.0** (2024) — Generative UI, RSC support

## Common Pitfalls

1. **Forgetting `await`** — `generateText` is async; `streamText` is not (returns immediately)
2. **Provider mismatch** — Install the provider package matching your model
3. **Missing env vars** — API keys must be in environment variables
4. **Token limits** — Set `maxTokens` to avoid unexpectedly long responses
5. **Stream consumption** — Streams can only be consumed once; use `fullStream` for multiple consumers

## Related Topics

- Providers → [01-providers-and-models](01-providers-and-models.md)
- Text generation → [02-generating-text](02-generating-text.md)
- Tool calling → [04-tool-calling](04-tool-calling.md)
- Agents → [05-agents](05-agents.md)
- Chat UI → [07-useChat-hook](07-useChat-hook.md)
