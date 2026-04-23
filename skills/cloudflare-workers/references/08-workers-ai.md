# Cloudflare Workers AI — ML Inference at the Edge

> Source: [developers.cloudflare.com/workers-ai](https://developers.cloudflare.com/workers-ai/)

## Table of Contents

- [What Is Workers AI](#what-is-workers-ai)
- [Setup](#setup)
- [Running Models](#running-models)
- [Text Generation (LLMs)](#text-generation-llms)
- [Text Embeddings](#text-embeddings)
- [Image Generation](#image-generation)
- [Speech Recognition](#speech-recognition)
- [Translation and Summarization](#translation-and-summarization)
- [OpenAI-Compatible API](#openai-compatible-api)
- [AI Gateway](#ai-gateway)
- [RAG with Vectorize](#rag-with-vectorize)
- [Limits and Pricing](#limits-and-pricing)
- [Common Patterns](#common-patterns)

## What Is Workers AI

Workers AI runs machine learning models on Cloudflare's global GPU network. No model hosting, no GPU provisioning — just bind and call.

**Best for:** Text generation, embeddings, RAG, image generation, speech-to-text, translation, classification — all serverless at the edge.

Key features:
- 50+ pre-deployed models (Meta Llama, Mistral, BAAI, Deepgram, etc.)
- OpenAI-compatible API endpoints
- Streaming responses
- Integration with Vectorize for RAG
- AI Gateway for caching, rate limiting, logging

## Setup

```toml
# wrangler.toml
[ai]
binding = "AI"
```

```typescript
interface Env {
  AI: Ai;
}
```

No API keys needed — the AI binding authenticates automatically via your Cloudflare account.

## Running Models

The core API is `env.AI.run()`:

```typescript
const result = await env.AI.run(modelName, inputs, options?);
```

- `modelName` — Model identifier (e.g., `@cf/meta/llama-3.1-8b-instruct`)
- `inputs` — Model-specific input object
- `options` — Optional: `{ gateway?: { id: string } }`

## Text Generation (LLMs)

### Chat Completions

```typescript
const response = await env.AI.run("@cf/meta/llama-3.1-8b-instruct", {
  messages: [
    { role: "system", content: "You are a helpful assistant." },
    { role: "user", content: "What is the capital of France?" },
  ],
  max_tokens: 256,
  temperature: 0.7,
  top_p: 0.9,
});
// response.response => "The capital of France is Paris."
```

### Streaming

```typescript
const stream = await env.AI.run("@cf/meta/llama-3.1-8b-instruct", {
  messages: [{ role: "user", content: "Write a haiku about coding" }],
  stream: true,
});

return new Response(stream, {
  headers: { "Content-Type": "text/event-stream" },
});
```

### Simple Prompt (Non-Chat)

```typescript
const response = await env.AI.run("@cf/meta/llama-3.1-8b-instruct", {
  prompt: "Explain serverless computing in one paragraph.",
});
```

### Function Calling

```typescript
const response = await env.AI.run("@cf/meta/llama-3.1-8b-instruct", {
  messages: [{ role: "user", content: "What's the weather in London?" }],
  tools: [
    {
      type: "function",
      function: {
        name: "get_weather",
        description: "Get current weather for a city",
        parameters: {
          type: "object",
          properties: {
            city: { type: "string", description: "City name" },
          },
          required: ["city"],
        },
      },
    },
  ],
});
```

### Popular Text Generation Models

| Model | Size | Notes |
|-------|------|-------|
| `@cf/meta/llama-3.1-8b-instruct` | 8B | Best general-purpose balance |
| `@cf/meta/llama-3.1-70b-instruct` | 70B | Higher quality, slower |
| `@cf/mistral/mistral-small-3.1-24b-instruct` | 24B | Strong multilingual |
| `@cf/qwen/qwen3-30b-a3b-fp8` | 30B | MoE, efficient |

## Text Embeddings

Generate vector embeddings for semantic search:

```typescript
const embeddings = await env.AI.run("@cf/baai/bge-base-en-v1.5", {
  text: ["Hello world", "How are you?"],
});
// embeddings.data => [{ values: [0.123, -0.456, ...] }, ...]

// Single text
const embedding = await env.AI.run("@cf/baai/bge-base-en-v1.5", {
  text: "What is serverless?",
});
```

### Popular Embedding Models

| Model | Dimensions | Notes |
|-------|-----------|-------|
| `@cf/baai/bge-base-en-v1.5` | 768 | Best general English |
| `@cf/baai/bge-large-en-v1.5` | 1024 | Higher quality |
| `@cf/baai/bge-m3` | 1024 | Multilingual |
| `@cf/google/embeddinggemma-300m` | 768 | Low-latency |

## Image Generation

```typescript
const image = await env.AI.run("@cf/black-forest-labs/flux-2-dev", {
  prompt: "A futuristic city skyline at sunset, digital art",
  num_steps: 20,
  width: 1024,
  height: 1024,
});
// image => ReadableStream (PNG)

return new Response(image, {
  headers: { "Content-Type": "image/png" },
});
```

### Image-to-Text (Captioning)

```typescript
const result = await env.AI.run("@cf/llava-hf/llava-1.5-7b-hf", {
  image: [...new Uint8Array(imageBuffer)],
  prompt: "Describe this image in detail",
  max_tokens: 512,
});
```

## Speech Recognition

```typescript
const audioBuffer = await request.arrayBuffer();

const result = await env.AI.run("@cf/openai/whisper-large-v3-turbo", {
  audio: [...new Uint8Array(audioBuffer)],
});
// result.text => "Hello, this is a transcription..."
// result.segments => [{ start, end, text }, ...]
```

## Translation and Summarization

### Translation

```typescript
const result = await env.AI.run("@cf/meta/m2m100-1.2b", {
  text: "Hello, how are you?",
  source_lang: "english",
  target_lang: "french",
});
// result.translated_text => "Bonjour, comment allez-vous?"
```

### Summarization

```typescript
const result = await env.AI.run("@cf/facebook/bart-large-cnn", {
  input_text: longArticleText,
  max_length: 150,
});
// result.summary => "..."
```

## OpenAI-Compatible API

Workers AI exposes OpenAI-compatible endpoints — use any OpenAI SDK:

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  apiKey: env.CLOUDFLARE_API_TOKEN,
  baseURL: `https://api.cloudflare.com/client/v4/accounts/${env.ACCOUNT_ID}/ai/v1`,
});

const completion = await client.chat.completions.create({
  model: "@cf/meta/llama-3.1-8b-instruct",
  messages: [{ role: "user", content: "Hello!" }],
});
```

Supported endpoints:
- `/v1/chat/completions` — Chat models
- `/v1/embeddings` — Embedding models

## AI Gateway

Route AI requests through Cloudflare's AI Gateway for caching, rate limiting, and analytics:

```toml
# wrangler.toml
[ai]
binding = "AI"
```

```typescript
const response = await env.AI.run("@cf/meta/llama-3.1-8b-instruct", {
  messages: [{ role: "user", content: "Hello" }],
}, {
  gateway: { id: "my-gateway" },
});
```

Gateway features:
- **Caching** — Cache identical prompts
- **Rate limiting** — Prevent abuse
- **Logging** — Full request/response logs
- **Analytics** — Usage dashboards
- **Fallbacks** — Route to alternative providers on failure

## RAG with Vectorize

Build Retrieval-Augmented Generation pipelines:

```typescript
// 1. Index documents
async function indexDocument(env: Env, id: string, text: string) {
  const embedding = await env.AI.run("@cf/baai/bge-base-en-v1.5", { text });

  await env.VECTORIZE_INDEX.upsert([{
    id,
    values: embedding.data[0].values,
    metadata: { text },
  }]);
}

// 2. Query with RAG
async function queryRAG(env: Env, question: string) {
  // Generate query embedding
  const queryEmb = await env.AI.run("@cf/baai/bge-base-en-v1.5", { text: question });

  // Search for relevant documents
  const matches = await env.VECTORIZE_INDEX.query(queryEmb.data[0].values, {
    topK: 5,
    returnMetadata: "all",
  });

  // Build context from matches
  const context = matches.matches
    .map((m) => m.metadata?.text)
    .filter(Boolean)
    .join("\n\n");

  // Generate answer with context
  const answer = await env.AI.run("@cf/meta/llama-3.1-8b-instruct", {
    messages: [
      { role: "system", content: `Answer based on this context:\n\n${context}` },
      { role: "user", content: question },
    ],
  });

  return answer.response;
}
```

## Limits and Pricing

| Resource | Free | Paid |
|----------|------|------|
| Neurons (compute units) | 10,000/day | Pay-per-use |

Pricing is per-model based on "neurons" (a normalized compute unit). Text generation costs more neurons than embeddings. Check the [pricing page](https://developers.cloudflare.com/workers-ai/platform/pricing/) for per-model rates.

| Limit | Value |
|-------|-------|
| Max input tokens | Model-dependent (typically 4K-128K) |
| Max output tokens | Model-dependent |
| Request timeout | 5 minutes |
| Concurrent requests | No hard limit (rate-limited per account) |

## Common Patterns

### Chatbot with Memory

```typescript
export class ChatBot extends DurableObject {
  private messages: Array<{ role: string; content: string }> = [];

  async chat(userMessage: string): Promise<string> {
    this.messages.push({ role: "user", content: userMessage });

    const response = await this.env.AI.run("@cf/meta/llama-3.1-8b-instruct", {
      messages: [
        { role: "system", content: "You are a helpful assistant." },
        ...this.messages.slice(-20),  // Keep last 20 messages
      ],
    });

    const reply = response.response!;
    this.messages.push({ role: "assistant", content: reply });
    await this.ctx.storage.put("messages", this.messages);
    return reply;
  }
}
```

## Common Pitfalls

- **Model names** — Always use the full `@cf/provider/model-name` format. Model names are case-sensitive.
- **Streaming type** — Streaming returns a `ReadableStream`, not a response object. Wrap in `new Response(stream)`.
- **Embedding dimensions** — Different models produce different dimensions. Match your Vectorize index dimension to your embedding model.
- **Token limits** — Each model has different context windows. Check the model card before sending long inputs.
- **Rate limits** — Free tier is limited to 10,000 neurons/day. Monitor usage in the dashboard.
