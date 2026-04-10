# Deployment Patterns

> Source: https://ai-sdk.dev/docs/getting-started

## Overview

AI SDK deploys to any JavaScript runtime: Node.js, Edge, serverless functions, and long-running servers. This guide covers framework-specific patterns, environment configuration, and production best practices.

## Next.js App Router

### Route Handler

```typescript
// app/api/chat/route.ts
import { streamText, UIMessage, convertToModelMessages } from 'ai';

export const maxDuration = 60; // Increase for complex agent tasks
export const runtime = 'nodejs'; // or 'edge'

export async function POST(req: Request) {
  const { messages }: { messages: UIMessage[] } = await req.json();

  const result = streamText({
    model: 'anthropic/claude-sonnet-4.5',
    system: 'You are a helpful assistant.',
    messages: await convertToModelMessages(messages),
    maxTokens: 2048,
  });

  return result.toUIMessageStreamResponse();
}
```

### Server Actions

```typescript
// app/actions.ts
'use server';

import { generateText } from 'ai';

export async function summarize(text: string) {
  const { text: summary } = await generateText({
    model: 'anthropic/claude-sonnet-4.5',
    prompt: `Summarize: ${text}`,
  });
  return summary;
}
```

### Edge Runtime

```typescript
// app/api/chat/route.ts
export const runtime = 'edge';

export async function POST(req: Request) {
  const { messages } = await req.json();

  const result = streamText({
    model: 'openai/gpt-5.2', // Edge-compatible
    messages: await convertToModelMessages(messages),
  });

  return result.toUIMessageStreamResponse();
}
```

## Node.js / Express

```typescript
import express from 'express';
import { streamText, generateText } from 'ai';

const app = express();
app.use(express.json());

// Streaming endpoint
app.post('/api/chat', async (req, res) => {
  const result = streamText({
    model: 'anthropic/claude-sonnet-4.5',
    messages: req.body.messages,
  });

  result.pipeTextStreamToResponse(res);
});

// Non-streaming endpoint
app.post('/api/summarize', async (req, res) => {
  const { text } = await generateText({
    model: 'anthropic/claude-sonnet-4.5',
    prompt: `Summarize: ${req.body.text}`,
  });

  res.json({ summary: text });
});

app.listen(3000);
```

## Hono

```typescript
import { Hono } from 'hono';
import { streamText, convertToModelMessages } from 'ai';

const app = new Hono();

app.post('/api/chat', async (c) => {
  const { messages } = await c.req.json();

  const result = streamText({
    model: 'anthropic/claude-sonnet-4.5',
    messages: await convertToModelMessages(messages),
  });

  return result.toUIMessageStreamResponse();
});

export default app;
```

## Cloudflare Workers

```typescript
// src/index.ts
import { streamText, convertToModelMessages } from 'ai';

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method !== 'POST') {
      return new Response('Method not allowed', { status: 405 });
    }

    const { messages } = await request.json();

    const result = streamText({
      model: 'openai/gpt-5.2',
      messages: await convertToModelMessages(messages),
      // Pass API key from Worker secrets
      headers: {
        Authorization: `Bearer ${env.OPENAI_API_KEY}`,
      },
    });

    return result.toUIMessageStreamResponse();
  },
};
```

## SvelteKit

```typescript
// src/routes/api/chat/+server.ts
import { streamText, convertToModelMessages } from 'ai';
import type { RequestHandler } from './$types';

export const POST: RequestHandler = async ({ request }) => {
  const { messages } = await request.json();

  const result = streamText({
    model: 'anthropic/claude-sonnet-4.5',
    messages: await convertToModelMessages(messages),
  });

  return result.toUIMessageStreamResponse();
};
```

## Environment Variables

```bash
# .env.local (Next.js) or .env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_GENERATIVE_AI_API_KEY=AI...

# Optional: Vercel AI Gateway
AI_GATEWAY_URL=https://gateway.vercel.ai
AI_GATEWAY_API_KEY=...
```

### Runtime Configuration

```typescript
import { createOpenAI } from '@ai-sdk/openai';

// Custom base URL (proxies, gateways)
const openai = createOpenAI({
  baseURL: process.env.AI_PROXY_URL ?? 'https://api.openai.com/v1',
  apiKey: process.env.OPENAI_API_KEY,
});
```

## Production Best Practices

### Rate Limiting

```typescript
import { Ratelimit } from '@upstash/ratelimit';
import { Redis } from '@upstash/redis';

const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(10, '1m'), // 10 requests per minute
});

export async function POST(req: Request) {
  const ip = req.headers.get('x-forwarded-for') ?? '127.0.0.1';
  const { success } = await ratelimit.limit(ip);

  if (!success) {
    return new Response('Rate limited', { status: 429 });
  }

  // ... generate response
}
```

### Authentication

```typescript
import { auth } from '@/lib/auth';

export async function POST(req: Request) {
  const session = await auth();
  if (!session?.user) {
    return new Response('Unauthorized', { status: 401 });
  }

  const { messages } = await req.json();

  const result = streamText({
    model: 'anthropic/claude-sonnet-4.5',
    messages: await convertToModelMessages(messages),
    // Pass user context
    system: `User: ${session.user.name}. ${systemPrompt}`,
  });

  return result.toUIMessageStreamResponse();
}
```

### Error Handling

```typescript
export async function POST(req: Request) {
  try {
    const { messages } = await req.json();

    const result = streamText({
      model: 'anthropic/claude-sonnet-4.5',
      messages: await convertToModelMessages(messages),
    });

    return result.toUIMessageStreamResponse({
      onError: (error) => {
        // Don't leak internal errors
        console.error('[AI Error]', error);
        return 'An error occurred. Please try again.';
      },
    });
  } catch (error) {
    console.error('[Route Error]', error);
    return new Response('Internal Server Error', { status: 500 });
  }
}
```

### Timeouts

```typescript
// Next.js: extend function timeout
export const maxDuration = 60; // 60 seconds (Pro plan)

// Manual timeout
const controller = new AbortController();
const timeout = setTimeout(() => controller.abort(), 55_000);

const result = streamText({
  model: 'anthropic/claude-sonnet-4.5',
  messages,
  abortSignal: controller.signal,
});

// Clean up
result.text.finally(() => clearTimeout(timeout));
```

### CORS Configuration

```typescript
// For cross-origin clients
export async function OPTIONS() {
  return new Response(null, {
    headers: {
      'Access-Control-Allow-Origin': 'https://myapp.com',
      'Access-Control-Allow-Methods': 'POST',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
}

export async function POST(req: Request) {
  const result = streamText({ model, messages });
  
  const response = result.toUIMessageStreamResponse();
  response.headers.set('Access-Control-Allow-Origin', 'https://myapp.com');
  return response;
}
```

## Monitoring in Production

```typescript
import { generateText } from 'ai';

const { text, usage } = await generateText({
  model: 'anthropic/claude-sonnet-4.5',
  prompt: userInput,
  experimental_telemetry: {
    isEnabled: true,
    functionId: 'chat-endpoint',
    metadata: { userId, environment: 'production' },
  },
  onFinish: ({ usage, finishReason }) => {
    // Track costs
    metrics.increment('ai.tokens.total', usage.totalTokens);
    metrics.increment('ai.requests.total');
    if (finishReason === 'length') {
      metrics.increment('ai.truncated');
    }
  },
});
```

## Common Pitfalls

1. **maxDuration not set** — Serverless functions timeout at 10s by default; AI calls need more
2. **Edge incompatibility** — Some providers/features don't work on Edge runtime
3. **Exposed API keys** — Never import provider packages in client components
4. **No rate limiting** — AI APIs are expensive; always rate limit in production
5. **Missing error handling** — Unhandled errors crash the stream silently
6. **CORS issues** — Cross-origin chat UIs need proper CORS headers

## Related Topics

- Streaming → [06-streaming-patterns](06-streaming-patterns.md)
- Middleware → [10-middleware-and-telemetry](10-middleware-and-telemetry.md)
- Chat UI → [07-useChat-hook](07-useChat-hook.md)
