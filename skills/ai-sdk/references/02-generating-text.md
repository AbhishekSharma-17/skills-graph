# Generating Text

> Source: https://ai-sdk.dev/docs/ai-sdk-core/generating-text

## Overview

The two primary functions for text generation are `generateText` (blocking, returns complete result) and `streamText` (non-blocking, streams response progressively). Both support tools, structured output, and comprehensive callbacks.

## generateText

Generates text and waits for the complete response. Ideal for batch processing, agents, and non-interactive workflows.

### Basic Usage

```typescript
import { generateText } from 'ai';

const { text, usage, finishReason } = await generateText({
  model: 'anthropic/claude-sonnet-4.5',
  prompt: 'Explain REST APIs in 3 sentences.',
});
```

### With System Message

```typescript
const { text } = await generateText({
  model: 'anthropic/claude-sonnet-4.5',
  system: 'You are a senior backend engineer. Be concise and practical.',
  prompt: 'How should I structure a FastAPI project?',
});
```

### With Message History

```typescript
const { text } = await generateText({
  model: 'openai/gpt-5.2',
  messages: [
    { role: 'user', content: 'What is TypeScript?' },
    { role: 'assistant', content: 'TypeScript is a typed superset of JavaScript.' },
    { role: 'user', content: 'How does it compare to Flow?' },
  ],
});
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | string \| LanguageModel | Model to use |
| `prompt` | string | Simple text prompt |
| `system` | string | System instructions |
| `messages` | Message[] | Conversation history |
| `tools` | ToolSet | Available tools |
| `output` | Output | Structured output schema |
| `maxTokens` | number | Maximum tokens to generate |
| `temperature` | number | Randomness (0-2) |
| `topP` | number | Nucleus sampling |
| `topK` | number | Top-K sampling |
| `stopSequences` | string[] | Stop generation triggers |
| `maxRetries` | number | Retry count (default: 2) |
| `abortSignal` | AbortSignal | Cancellation signal |
| `headers` | Record | Custom request headers |
| `providerOptions` | object | Provider-specific settings |

### Return Value

```typescript
const result = await generateText({ model, prompt });

result.text          // Generated text
result.content       // Content parts from final step
result.reasoning     // Reasoning text (if model supports)
result.toolCalls     // Tool calls made
result.toolResults   // Results from tool executions
result.finishReason  // 'stop' | 'length' | 'content-filter' | 'tool-calls'
result.usage         // { promptTokens, completionTokens, totalTokens }
result.totalUsage    // Cumulative usage across all steps
result.steps         // Array of all generation steps
result.response      // Raw response (headers, body)
```

### Callbacks

```typescript
const { text } = await generateText({
  model: 'anthropic/claude-sonnet-4.5',
  prompt: 'Hello',
  onStepFinish: ({ text, toolCalls, toolResults, usage, finishReason }) => {
    console.log('Step completed:', { toolCalls, usage });
  },
  onFinish: ({ text, usage, finishReason, steps }) => {
    // Save to database, log analytics, etc.
    await saveToDb({ text, tokens: usage.totalTokens });
  },
});
```

## streamText

Streams text progressively for real-time UI updates. Returns immediately — does not block.

### Basic Usage

```typescript
import { streamText } from 'ai';

const result = streamText({
  model: 'anthropic/claude-sonnet-4.5',
  prompt: 'Write a haiku about programming.',
});

// Consume as AsyncIterable
for await (const chunk of result.textStream) {
  process.stdout.write(chunk);
}
```

### Stream Properties

```typescript
const result = streamText({ model, prompt });

// Text-only stream (AsyncIterable<string>)
result.textStream

// Full event stream with metadata
result.fullStream

// Promise-based (await completion)
const finalText = await result.text;
const finalUsage = await result.usage;
const reason = await result.finishReason;
```

### fullStream Events

```typescript
for await (const event of result.fullStream) {
  switch (event.type) {
    case 'text-delta':
      console.log(event.textDelta);
      break;
    case 'tool-call':
      console.log('Tool:', event.toolName, event.args);
      break;
    case 'tool-result':
      console.log('Result:', event.result);
      break;
    case 'reasoning-delta':
      console.log('Thinking:', event.textDelta);
      break;
    case 'finish':
      console.log('Done:', event.usage);
      break;
    case 'error':
      console.error('Error:', event.error);
      break;
  }
}
```

### HTTP Response Helpers

```typescript
// Next.js App Router
export async function POST(req: Request) {
  const { messages } = await req.json();

  const result = streamText({
    model: 'anthropic/claude-sonnet-4.5',
    messages: await convertToModelMessages(messages),
  });

  // For useChat hook
  return result.toUIMessageStreamResponse();
}
```

### Stream Callbacks

```typescript
const result = streamText({
  model: 'anthropic/claude-sonnet-4.5',
  prompt: 'Tell me a story',
  onChunk: ({ chunk }) => {
    if (chunk.type === 'text-delta') {
      console.log('Received:', chunk.textDelta);
    }
  },
  onError: ({ error }) => {
    console.error('Stream error:', error);
  },
  onFinish: ({ text, usage, finishReason }) => {
    console.log('Complete:', { tokens: usage.totalTokens });
  },
});
```

### Stream Transformation

```typescript
import { streamText, smoothStream } from 'ai';

const result = streamText({
  model: 'anthropic/claude-sonnet-4.5',
  prompt: 'Write an essay',
  experimental_transform: smoothStream({
    delayInMs: 20, // Smooth out chunky delivery
  }),
});
```

## Multi-Modal Prompts

### Images

```typescript
const { text } = await generateText({
  model: 'anthropic/claude-sonnet-4.5',
  messages: [
    {
      role: 'user',
      content: [
        { type: 'text', text: 'Describe this image.' },
        { type: 'image', image: new URL('https://example.com/photo.jpg') },
      ],
    },
  ],
});
```

### Files (PDFs, Audio)

```typescript
import { readFile } from 'fs/promises';

const { text } = await generateText({
  model: 'anthropic/claude-sonnet-4.5',
  messages: [
    {
      role: 'user',
      content: [
        { type: 'text', text: 'Summarize this document.' },
        {
          type: 'file',
          data: await readFile('report.pdf'),
          mimeType: 'application/pdf',
        },
      ],
    },
  ],
});
```

## Multi-Step Generation

When tools are involved, generation may take multiple steps:

```typescript
const { text, steps } = await generateText({
  model: 'anthropic/claude-sonnet-4.5',
  tools: { /* ... */ },
  maxSteps: 10, // Maximum tool-calling iterations
  prompt: 'Research and summarize the latest AI news.',
});

console.log(`Completed in ${steps.length} steps`);
```

## Abort and Timeout

```typescript
// Timeout after 30 seconds
const { text } = await generateText({
  model: 'anthropic/claude-sonnet-4.5',
  prompt: 'Complex analysis...',
  abortSignal: AbortSignal.timeout(30_000),
});

// Manual abort
const controller = new AbortController();
setTimeout(() => controller.abort(), 10_000);

const result = streamText({
  model: 'anthropic/claude-sonnet-4.5',
  prompt: 'Long story...',
  abortSignal: controller.signal,
});
```

## Common Patterns

### Retry with Different Model

```typescript
async function generateWithFallback(prompt: string) {
  try {
    return await generateText({
      model: 'anthropic/claude-sonnet-4.5',
      prompt,
      maxRetries: 2,
    });
  } catch {
    return await generateText({
      model: 'openai/gpt-5.2',
      prompt,
      maxRetries: 2,
    });
  }
}
```

### Token Budget Management

```typescript
const { text, usage } = await generateText({
  model: 'anthropic/claude-sonnet-4.5',
  prompt: longPrompt,
  maxTokens: 1000,
});

if (usage.completionTokens >= 1000) {
  console.warn('Response may be truncated');
}
```

## Common Pitfalls

1. **streamText is not async** — Don't `await streamText(...)`, it returns synchronously
2. **Single consumption** — `textStream` can only be iterated once
3. **Missing maxSteps** — Without `maxSteps`, tool calls won't loop automatically
4. **Error swallowing** — `streamText` suppresses errors by default; use `onError` to catch them
5. **Forgetting convertToModelMessages** — UIMessage format differs from model messages

## Related Topics

- Tool calling → [04-tool-calling](04-tool-calling.md)
- Structured output → [03-structured-output](03-structured-output.md)
- Chat UI → [07-useChat-hook](07-useChat-hook.md)
- Streaming → [06-streaming-patterns](06-streaming-patterns.md)
