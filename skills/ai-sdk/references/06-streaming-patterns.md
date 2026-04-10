# Streaming Patterns

> Source: https://ai-sdk.dev/docs/foundations/streaming

## Overview

Streaming delivers LLM responses progressively, reducing perceived latency from seconds to milliseconds. AI SDK provides multiple stream types and protocols for different use cases — from simple text streaming to complex multi-part UI streams.

## Stream Types

### textStream — Simple Text

```typescript
import { streamText } from 'ai';

const result = streamText({
  model: 'anthropic/claude-sonnet-4.5',
  prompt: 'Write a poem.',
});

// As AsyncIterable
for await (const chunk of result.textStream) {
  process.stdout.write(chunk);
}

// As ReadableStream (for web APIs)
const stream: ReadableStream<string> = result.textStream;
```

### fullStream — All Events

```typescript
const result = streamText({
  model: 'anthropic/claude-sonnet-4.5',
  tools: { weather },
  maxSteps: 5,
  prompt: 'Weather in Paris?',
});

for await (const event of result.fullStream) {
  switch (event.type) {
    case 'start':
      console.log('Generation started');
      break;
    case 'start-step':
      console.log('New step:', event.stepNumber);
      break;
    case 'text-delta':
      process.stdout.write(event.textDelta);
      break;
    case 'reasoning-delta':
      console.log('[thinking]', event.textDelta);
      break;
    case 'tool-call':
      console.log('Tool:', event.toolName, event.args);
      break;
    case 'tool-result':
      console.log('Result:', event.result);
      break;
    case 'source':
      console.log('Source:', event.url);
      break;
    case 'finish-step':
      console.log('Step done:', event.usage);
      break;
    case 'finish':
      console.log('Complete:', event.finishReason, event.usage);
      break;
    case 'error':
      console.error('Error:', event.error);
      break;
  }
}
```

## UI Message Stream Protocol

The protocol used by `useChat` for rich chat interfaces:

### Server → Client Format

```typescript
// Next.js route handler
export async function POST(req: Request) {
  const { messages }: { messages: UIMessage[] } = await req.json();

  const result = streamText({
    model: 'anthropic/claude-sonnet-4.5',
    messages: await convertToModelMessages(messages),
  });

  return result.toUIMessageStreamResponse({
    sendReasoning: true,  // Include thinking tokens
    sendSources: true,    // Include citation sources
    messageMetadata: ({ part }) => {
      if (part.type === 'finish') {
        return { totalTokens: part.totalUsage.totalTokens };
      }
    },
  });
}
```

### Custom Data in Stream

```typescript
import { createUIMessageStream } from 'ai';

export async function POST(req: Request) {
  return new Response(
    createUIMessageStream({
      execute: async ({ writer }) => {
        // Write custom data parts
        writer.write({ type: 'data', data: { progress: 0.5 } });

        // Merge another stream
        const result = streamText({ model, prompt });
        writer.merge(result.toUIMessageStream());

        // More custom data
        writer.write({ type: 'data', data: { progress: 1.0 } });
      },
    }).body,
  );
}
```

## Stream Transforms

### smoothStream — Rate Smoothing

Smooth out bursty token delivery for better UX:

```typescript
import { streamText, smoothStream } from 'ai';

const result = streamText({
  model: 'anthropic/claude-sonnet-4.5',
  prompt: 'Write an essay.',
  experimental_transform: smoothStream({
    delayInMs: 20,        // Delay between chunks
    chunking: 'word',     // Split by word boundaries
  }),
});
```

### Custom Transforms

```typescript
import { streamText } from 'ai';

const result = streamText({
  model: 'openai/gpt-5.2',
  prompt: 'Hello',
  experimental_transform: new TransformStream({
    transform(chunk, controller) {
      // Modify chunks before delivery
      if (chunk.type === 'text-delta') {
        controller.enqueue({
          ...chunk,
          textDelta: chunk.textDelta.toUpperCase(),
        });
      } else {
        controller.enqueue(chunk);
      }
    },
  }),
});
```

### Chained Transforms

```typescript
experimental_transform: [
  smoothStream({ delayInMs: 10 }),
  myCustomTransform,
  anotherTransform,
]
```

## Response Helpers

### Next.js App Router

```typescript
// Standard UI message stream
return result.toUIMessageStreamResponse();

// With custom headers
return result.toUIMessageStreamResponse({
  headers: { 'X-Request-Id': requestId },
});

// Plain text stream
return result.toTextStreamResponse();
```

### Node.js / Express

```typescript
import { streamText } from 'ai';
import express from 'express';

const app = express();

app.post('/api/chat', async (req, res) => {
  const result = streamText({
    model: 'anthropic/claude-sonnet-4.5',
    prompt: req.body.prompt,
  });

  result.pipeTextStreamToResponse(res);
});
```

### Generic Web Response

```typescript
// For any runtime (Deno, Bun, Cloudflare Workers)
const result = streamText({ model, prompt });

return new Response(result.textStream, {
  headers: { 'Content-Type': 'text/plain; charset=utf-8' },
});
```

## Backpressure Handling

When consumers are slower than producers:

```typescript
const result = streamText({
  model: 'anthropic/claude-sonnet-4.5',
  prompt: 'Long response...',
});

// ReadableStream handles backpressure automatically
const reader = result.textStream.getReader();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  // Slow consumer — stream automatically pauses production
  await slowOperation(value);
}
```

## Error Handling in Streams

```typescript
const result = streamText({
  model: 'anthropic/claude-sonnet-4.5',
  prompt: 'Hello',
  onError: ({ error }) => {
    // Errors are suppressed by default (won't crash server)
    console.error('Stream error:', error);
    // Optionally send to error tracking
    Sentry.captureException(error);
  },
});
```

### Client-Side Error Handling

```typescript
// In useChat hook
const { messages, error } = useChat({
  transport: new DefaultChatTransport({ api: '/api/chat' }),
});

if (error) {
  // Display error UI
}
```

### Custom Error Messages (Security)

```typescript
return result.toUIMessageStreamResponse({
  onError: (error) => {
    // Don't leak internal errors to client
    if (error instanceof RateLimitError) {
      return 'Too many requests. Please try again later.';
    }
    return 'An error occurred. Please try again.';
  },
});
```

## Stream Resume

Resume interrupted streams (e.g., after page reload):

```typescript
// Server: include message IDs
return result.toUIMessageStreamResponse({
  messageId: generateId(),
});

// Client: resume from last message
const { messages, sendMessage } = useChat({
  transport: new DefaultChatTransport({ api: '/api/chat' }),
  initialMessages: savedMessages, // Restore from storage
});
```

## Multi-Stream Merging

Combine multiple streams into one:

```typescript
import { createUIMessageStream, streamText } from 'ai';

export async function POST(req: Request) {
  return new Response(
    createUIMessageStream({
      execute: async ({ writer }) => {
        // Run multiple generations in parallel
        const [result1, result2] = await Promise.all([
          streamText({ model, prompt: 'Part 1' }),
          streamText({ model, prompt: 'Part 2' }),
        ]);

        // Merge streams sequentially
        writer.merge(result1.toUIMessageStream());
        writer.merge(result2.toUIMessageStream());
      },
    }).body,
  );
}
```

## Common Pitfalls

1. **Consuming stream twice** — Streams are single-use; clone if needed
2. **Missing await on promises** — `result.text` is a Promise; `result.textStream` is not
3. **No error callback** — Errors are swallowed silently without `onError`
4. **Blocking stream** — Don't do heavy sync work in stream consumption
5. **Wrong response helper** — `toUIMessageStreamResponse` for useChat, `toTextStreamResponse` for plain text

## Related Topics

- Text generation → [02-generating-text](02-generating-text.md)
- Chat UI → [07-useChat-hook](07-useChat-hook.md)
- Deployment → [12-deployment-patterns](12-deployment-patterns.md)
