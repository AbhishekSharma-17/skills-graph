# Middleware and Telemetry

> Source: https://ai-sdk.dev/docs/ai-sdk-core/middleware

## Overview

AI SDK middleware wraps language models with cross-cutting concerns: logging, caching, rate limiting, guardrails, and telemetry. DevTools provides visual inspection of agent execution. OpenTelemetry integration enables production observability.

## Model Middleware

### Basic Middleware

```typescript
import { wrapLanguageModel, generateText } from 'ai';
import { anthropic } from '@ai-sdk/anthropic';

const model = wrapLanguageModel({
  model: anthropic('claude-sonnet-4-5-20250514'),
  middleware: {
    transformParams: async ({ params }) => {
      console.log('[Request]', JSON.stringify(params.prompt));
      return params;
    },
    wrapGenerate: async ({ doGenerate, params }) => {
      const start = Date.now();
      const result = await doGenerate();
      console.log(`[Response] ${Date.now() - start}ms, ${result.usage?.totalTokens} tokens`);
      return result;
    },
    wrapStream: async ({ doStream, params }) => {
      const start = Date.now();
      const { stream, ...rest } = await doStream();
      // Can transform stream here
      return { stream, ...rest };
    },
  },
});

const { text } = await generateText({ model, prompt: 'Hello' });
```

### Middleware Interface

```typescript
interface LanguageModelMiddleware {
  // Transform parameters before sending to model
  transformParams?: (options: {
    params: LanguageModelCallParams;
  }) => Promise<LanguageModelCallParams>;

  // Wrap non-streaming generation
  wrapGenerate?: (options: {
    doGenerate: () => Promise<LanguageModelGenerateResult>;
    params: LanguageModelCallParams;
  }) => Promise<LanguageModelGenerateResult>;

  // Wrap streaming generation
  wrapStream?: (options: {
    doStream: () => Promise<LanguageModelStreamResult>;
    params: LanguageModelCallParams;
  }) => Promise<LanguageModelStreamResult>;
}
```

## Common Middleware Patterns

### Logging Middleware

```typescript
const loggingMiddleware: LanguageModelMiddleware = {
  wrapGenerate: async ({ doGenerate, params }) => {
    console.log(`[LLM] model=${params.modelId} tools=${Object.keys(params.tools ?? {})}`);
    const result = await doGenerate();
    console.log(`[LLM] finish=${result.finishReason} tokens=${result.usage?.totalTokens}`);
    return result;
  },
};
```

### Caching Middleware

```typescript
const cache = new Map<string, any>();

const cachingMiddleware: LanguageModelMiddleware = {
  wrapGenerate: async ({ doGenerate, params }) => {
    const key = JSON.stringify(params.prompt);
    if (cache.has(key)) {
      return cache.get(key);
    }
    const result = await doGenerate();
    cache.set(key, result);
    return result;
  },
};
```

### Rate Limiting

```typescript
import { RateLimiter } from 'limiter';

const limiter = new RateLimiter({ tokensPerInterval: 10, interval: 'minute' });

const rateLimitMiddleware: LanguageModelMiddleware = {
  wrapGenerate: async ({ doGenerate }) => {
    await limiter.removeTokens(1);
    return doGenerate();
  },
};
```

### Guardrails / Content Filtering

```typescript
const guardrailMiddleware: LanguageModelMiddleware = {
  transformParams: async ({ params }) => {
    // Add safety system prompt
    return {
      ...params,
      system: `${params.system ?? ''}\n\nDo not generate harmful content.`,
    };
  },
  wrapGenerate: async ({ doGenerate }) => {
    const result = await doGenerate();
    // Check output
    if (containsProhibitedContent(result.text)) {
      throw new Error('Content policy violation');
    }
    return result;
  },
};
```

## DevTools

Visual inspection of LLM calls and agent execution:

### Setup

```typescript
import { devToolsMiddleware, wrapLanguageModel } from 'ai';
import { anthropic } from '@ai-sdk/anthropic';

const model = wrapLanguageModel({
  model: anthropic('claude-sonnet-4-5-20250514'),
  middleware: devToolsMiddleware(),
});
```

### Launch DevTools

```bash
npx @ai-sdk/devtools
```

### DevTools Shows

- Input parameters and complete prompts
- Output content and tool invocations
- Token usage and timing metrics
- Raw provider request/response data
- Multi-step agent execution flow

## OpenTelemetry Integration

### Setup

```typescript
import { registerOTel } from '@vercel/otel';

// Initialize at app start
registerOTel({
  serviceName: 'my-ai-app',
});
```

### Telemetry in generateText/streamText

```typescript
const { text } = await generateText({
  model: 'anthropic/claude-sonnet-4.5',
  prompt: 'Hello',
  experimental_telemetry: {
    isEnabled: true,
    functionId: 'chat-completion',
    metadata: {
      userId: 'user_123',
      sessionId: 'sess_abc',
    },
  },
});
```

### Custom Span Attributes

```typescript
experimental_telemetry: {
  isEnabled: true,
  functionId: 'summarize',
  metadata: {
    inputLength: document.length,
    model: 'claude-sonnet-4.5',
    environment: 'production',
  },
  recordInputs: true,   // Record prompts (careful with PII)
  recordOutputs: true,  // Record completions
}
```

### Exported Spans

AI SDK exports spans for:
- `ai.generateText` / `ai.streamText` — Full generation lifecycle
- `ai.generateText.doGenerate` — Individual LLM calls
- `ai.toolCall` — Tool executions
- `ai.embed` / `ai.embedMany` — Embedding operations

## Testing with Middleware

### Mock Provider for Tests

```typescript
import { MockLanguageModelV1 } from 'ai/test';

const mockModel = new MockLanguageModelV1({
  defaultObjectGenerationMode: 'json',
  doGenerate: async () => ({
    rawCall: { rawPrompt: null, rawSettings: {} },
    finishReason: 'stop',
    usage: { promptTokens: 10, completionTokens: 20 },
    text: 'Mocked response',
  }),
});

// Use in tests
const { text } = await generateText({
  model: mockModel,
  prompt: 'Test prompt',
});
expect(text).toBe('Mocked response');
```

### Simulating Streams

```typescript
import { simulateReadableStream } from 'ai/test';

const mockModel = new MockLanguageModelV1({
  doStream: async () => ({
    stream: simulateReadableStream({
      chunks: [
        { type: 'text-delta', textDelta: 'Hello' },
        { type: 'text-delta', textDelta: ' world' },
        { type: 'finish', finishReason: 'stop', usage: { promptTokens: 5, completionTokens: 2 } },
      ],
      chunkDelayInMs: 50,
    }),
    rawCall: { rawPrompt: null, rawSettings: {} },
  }),
});
```

## Error Handling Middleware

```typescript
const retryMiddleware: LanguageModelMiddleware = {
  wrapGenerate: async ({ doGenerate }) => {
    let lastError: Error | undefined;
    for (let attempt = 0; attempt < 3; attempt++) {
      try {
        return await doGenerate();
      } catch (error) {
        lastError = error as Error;
        if (isRateLimitError(error)) {
          await sleep(Math.pow(2, attempt) * 1000);
          continue;
        }
        throw error; // Don't retry non-rate-limit errors
      }
    }
    throw lastError;
  },
};
```

## Composing Multiple Middleware

```typescript
import { wrapLanguageModel } from 'ai';

// Apply multiple middleware in order (first applied = outermost)
const model = wrapLanguageModel({
  model: baseModel,
  middleware: loggingMiddleware,
});

const modelWithCache = wrapLanguageModel({
  model,
  middleware: cachingMiddleware,
});

const finalModel = wrapLanguageModel({
  model: modelWithCache,
  middleware: guardrailMiddleware,
});
```

## Common Pitfalls

1. **Middleware order matters** — Outermost middleware runs first; put logging outside caching
2. **Stream middleware complexity** — Wrapping streams requires careful handling of async iterables
3. **DevTools in production** — Only use devToolsMiddleware in development
4. **Telemetry PII** — Be careful with `recordInputs`/`recordOutputs` if prompts contain user data
5. **Mock model limitations** — Mock models don't validate tool schemas; test with real models too

## Related Topics

- Providers → [01-providers-and-models](01-providers-and-models.md)
- Agents → [05-agents](05-agents.md)
- Deployment → [12-deployment-patterns](12-deployment-patterns.md)
