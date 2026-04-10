# Providers and Models

> Source: https://ai-sdk.dev/docs/foundations/providers-and-models

## Overview

AI SDK abstracts provider-specific APIs behind a unified interface. Switch between OpenAI, Anthropic, Google, and 30+ providers without changing application logic.

## Supported Providers

### Major Commercial Providers

| Provider | Package | Models |
|----------|---------|--------|
| OpenAI | `@ai-sdk/openai` | GPT-5.4-pro, GPT-5.2, GPT-5, GPT-4o |
| Anthropic | `@ai-sdk/anthropic` | Claude Opus 4.6, Sonnet 4.6, Haiku 4.5 |
| Google | `@ai-sdk/google` | Gemini 2.5 Pro, Flash, Embedding |
| Google Vertex | `@ai-sdk/google-vertex` | Same models via Vertex AI |
| Azure OpenAI | `@ai-sdk/azure` | OpenAI models via Azure |
| Amazon Bedrock | `@ai-sdk/amazon-bedrock` | Claude, Titan, Llama |
| xAI | `@ai-sdk/xai` | Grok models |
| Mistral | `@ai-sdk/mistral` | Mistral Large, Pixtral |
| DeepSeek | `@ai-sdk/deepseek` | DeepSeek R1, V3 |

### Infrastructure Providers

| Provider | Package | Description |
|----------|---------|-------------|
| Together.ai | `@ai-sdk/togetherai` | Open-source model hosting |
| Groq | `@ai-sdk/groq` | Fast inference for Llama, Mixtral |
| Fireworks | `@ai-sdk/fireworks` | Optimized open-source inference |
| Cohere | `@ai-sdk/cohere` | Command R+, embeddings, reranking |
| Perplexity | `@ai-sdk/perplexity` | Search-augmented models |
| Cerebras | `@ai-sdk/cerebras` | Ultra-fast inference |

### Self-Hosted / Local

| Provider | Package | Description |
|----------|---------|-------------|
| Ollama | `ollama-ai-provider` | Local model serving |
| LM Studio | `@lmstudio/ai-sdk` | Desktop local models |
| OpenAI Compatible | `@ai-sdk/openai-compatible` | Any OpenAI-API server |

## Model String Syntax

AI SDK v6 uses a unified model string format:

```typescript
// Format: "provider/model-name"
const model = 'anthropic/claude-sonnet-4.5';
const model = 'openai/gpt-5.2';
const model = 'google/gemini-2.5-pro';
```

This requires registering providers with the AI Gateway or using provider instances directly.

## Provider Instance Usage

```typescript
import { anthropic } from '@ai-sdk/anthropic';
import { openai } from '@ai-sdk/openai';
import { google } from '@ai-sdk/google';
import { generateText } from 'ai';

// Using provider functions directly
const { text } = await generateText({
  model: anthropic('claude-sonnet-4-5-20250514'),
  prompt: 'Hello!',
});

// OpenAI with specific model
const { text: t2 } = await generateText({
  model: openai('gpt-5.2'),
  prompt: 'Hello!',
});
```

## Provider Configuration

```typescript
import { createOpenAI } from '@ai-sdk/openai';
import { createAnthropic } from '@ai-sdk/anthropic';

// Custom OpenAI configuration
const openai = createOpenAI({
  apiKey: process.env.OPENAI_API_KEY,
  baseURL: 'https://custom-endpoint.example.com/v1',
  compatibility: 'strict',
});

// Custom Anthropic configuration
const anthropic = createAnthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
  headers: { 'X-Custom': 'value' },
});
```

## Provider Registry

Register multiple providers for dynamic model selection:

```typescript
import { createProviderRegistry } from 'ai';
import { anthropic } from '@ai-sdk/anthropic';
import { openai } from '@ai-sdk/openai';

const registry = createProviderRegistry({
  anthropic,
  openai,
});

// Select model dynamically
const model = registry.languageModel('anthropic:claude-sonnet-4-5-20250514');

const { text } = await generateText({
  model,
  prompt: 'Hello!',
});
```

## Model Capabilities

Not all models support all features. Check capabilities:

| Feature | OpenAI | Anthropic | Google | Mistral |
|---------|--------|-----------|--------|---------|
| Text generation | Yes | Yes | Yes | Yes |
| Streaming | Yes | Yes | Yes | Yes |
| Tool calling | Yes | Yes | Yes | Yes |
| Image input | Yes | Yes | Yes | Yes |
| Structured output | Yes | Yes | Yes | Yes |
| Embeddings | Yes | No | Yes | Yes |
| Image generation | Yes (DALL-E) | No | Yes | No |
| Speech | Yes | No | No | No |

## Provider Options

Pass provider-specific settings without breaking the unified API:

```typescript
import { generateText } from 'ai';

const { text } = await generateText({
  model: 'anthropic/claude-sonnet-4.5',
  prompt: 'Analyze this image',
  providerOptions: {
    anthropic: {
      thinking: { type: 'enabled', budgetTokens: 5000 },
    },
  },
});
```

## Middleware System

Wrap models with cross-cutting concerns:

```typescript
import { wrapLanguageModel } from 'ai';

const wrappedModel = wrapLanguageModel({
  model: anthropic('claude-sonnet-4-5-20250514'),
  middleware: {
    transformParams: async ({ params }) => {
      console.log('Request:', params);
      return params;
    },
    wrapGenerate: async ({ doGenerate }) => {
      const start = Date.now();
      const result = await doGenerate();
      console.log(`Duration: ${Date.now() - start}ms`);
      return result;
    },
  },
});
```

## Fallback and Routing

```typescript
import { createFallbackModel } from 'ai';

// Try primary, fall back to secondary
const model = createFallbackModel([
  anthropic('claude-sonnet-4-5-20250514'),
  openai('gpt-5.2'),
]);
```

## Custom Providers

Implement the Language Model Specification for custom integrations:

```typescript
import { LanguageModel } from 'ai';

class MyCustomModel implements LanguageModel {
  readonly specificationVersion = 'v3';
  readonly modelId = 'my-model';
  readonly provider = 'my-provider';
  readonly defaultObjectGenerationMode = 'json';

  async doGenerate(options) {
    // Implementation
  }

  async doStream(options) {
    // Implementation
  }
}
```

## Common Pitfalls

1. **Wrong package** — Each provider needs its own `@ai-sdk/` package installed
2. **API key naming** — Providers expect specific env var names (e.g., `ANTHROPIC_API_KEY`)
3. **Model ID mismatch** — Provider instances use short IDs; gateway uses `provider/model` format
4. **Feature unavailability** — Check model capabilities before using features like vision or tools
5. **Rate limits** — Different providers have different rate limits; use middleware for retries

## Related Topics

- Text generation → [02-generating-text](02-generating-text.md)
- Middleware → [10-middleware-and-telemetry](10-middleware-and-telemetry.md)
- Deployment → [12-deployment-patterns](12-deployment-patterns.md)
