# Mastra — Structured Output

> Source: [mastra.ai/docs/agents/structured-output](https://mastra.ai/docs/agents/structured-output) · `@mastra/core` v1.37.x

## Overview

Structured output lets agents return typed data objects matching predefined schemas instead of plain text. This enables clean integration with APIs, databases, and application logic.

## Basic Usage

Pass an `output` schema to `.generate()` or `.stream()`:

```typescript
import { z } from 'zod'

const response = await agent.generate('Analyze the sentiment of: I love TypeScript!', {
  output: z.object({
    text: z.string(),
    sentiment: z.enum(['positive', 'negative', 'neutral']),
    confidence: z.number().min(0).max(1),
    keywords: z.array(z.string()),
  }),
})

// response.object is fully typed
console.log(response.object.sentiment)   // 'positive'
console.log(response.object.confidence)  // 0.95
console.log(response.object.keywords)    // ['love', 'TypeScript']
```

## Schema Libraries

Any Standard JSON Schema-compatible library works:

```typescript
// Zod (recommended)
output: z.object({ name: z.string(), age: z.number() })

// Valibot
import { toStandardJsonSchema } from '@valibot/to-standard-json-schema'
output: toStandardJsonSchema(v.object({ name: v.string(), age: v.number() }))

// ArkType
import { type } from 'arktype'
output: type({ name: 'string', age: 'number' })

// Raw JSON Schema
output: {
  type: 'object',
  properties: { name: { type: 'string' }, age: { type: 'number' } },
  required: ['name', 'age'],
}
```

## Streaming Structured Output

Structured output works with streaming:

```typescript
const stream = await agent.stream('Extract entities from this text...', {
  output: z.object({
    entities: z.array(z.object({
      name: z.string(),
      type: z.enum(['person', 'org', 'location']),
    })),
  }),
})

// Stream events include partial objects
for await (const event of stream.fullStream) {
  if (event.type === 'object') {
    console.log('Partial:', event.object) // Incrementally built
  }
}

// Final typed object
const result = await stream.object
console.log(result.entities)
```

## Separate Structuring Model

Use a secondary LLM to extract structured data from the main agent's response:

```typescript
const response = await agent.generate('Write a detailed product review', {
  output: z.object({
    rating: z.number().min(1).max(5),
    pros: z.array(z.string()),
    cons: z.array(z.string()),
    summary: z.string(),
  }),
  model: 'openai/gpt-5-mini',  // Cheaper model for structuring
})
```

The main agent generates the review using its configured model, then the structuring model extracts the typed data. Increases latency but reduces cost for the structuring step.

## Model Compatibility

When models don't support tools and structured output simultaneously:

### jsonPromptInjection

Embed the schema in the system prompt instead of using API parameters:

```typescript
const response = await agent.generate('Classify this email', {
  output: z.object({ category: z.string(), priority: z.number() }),
  experimental_jsonPromptInjection: true,
})
```

### prepareStep (Workflow Pattern)

Handle tools and structuring in sequential workflow steps:

```typescript
const toolStep = createStep({
  id: 'tool-step',
  execute: async ({ inputData }) => {
    const result = await agent.generate(inputData.query)
    return { rawText: result.text }
  },
})

const structureStep = createStep({
  id: 'structure-step',
  execute: async ({ inputData }) => {
    const result = await agent.generate(inputData.rawText, {
      output: outputSchema,
      toolChoice: 'none',
    })
    return result.object
  },
})
```

## Error Handling

Three strategies for validation failures:

```typescript
const response = await agent.generate('Extract data', {
  output: mySchema,
  experimental_output: {
    onError: 'strict',    // Throw error (default)
    // onError: 'warn',   // Log warning, return partial
    // onError: 'fallback', // Return predefined fallback
    fallback: { name: 'unknown', age: 0 },
  },
})
```

| Strategy | Behavior |
|----------|----------|
| `strict` | Throws `OutputValidationError` |
| `warn` | Logs warning, returns partial object |
| `fallback` | Returns the provided fallback value |

## Common Patterns

### Data Extraction

```typescript
const extractContacts = async (text: string) => {
  const response = await agent.generate(`Extract all contacts from: ${text}`, {
    output: z.object({
      contacts: z.array(z.object({
        name: z.string(),
        email: z.string().email().optional(),
        phone: z.string().optional(),
        role: z.string().optional(),
      })),
    }),
  })
  return response.object.contacts
}
```

### Classification

```typescript
const classify = async (text: string) => {
  const response = await agent.generate(`Classify: ${text}`, {
    output: z.object({
      category: z.enum(['bug', 'feature', 'question', 'other']),
      priority: z.enum(['low', 'medium', 'high', 'critical']),
      tags: z.array(z.string()),
    }),
  })
  return response.object
}
```

### Structured Agent in Workflow

```typescript
const analyzeStep = createStep({
  id: 'analyze',
  inputSchema: z.object({ text: z.string() }),
  outputSchema: z.object({
    summary: z.string(),
    sentiment: z.enum(['positive', 'negative', 'neutral']),
  }),
  execute: async ({ inputData }) => {
    const agent = mastra.getAgentById('analyst')
    const result = await agent.generate(`Analyze: ${inputData.text}`, {
      output: z.object({
        summary: z.string(),
        sentiment: z.enum(['positive', 'negative', 'neutral']),
      }),
    })
    return result.object
  },
})
```

## Pitfalls

1. **Schema complexity** — very deeply nested schemas may cause model errors. Flatten when possible
2. **Not all models support structured output** — check provider docs. Use `jsonPromptInjection` for unsupported models
3. **Tools + structured output** — some models can't use both simultaneously. Use `prepareStep` pattern or separate structuring model
4. **Streaming partial objects** — the object builds incrementally; don't access nested properties until the stream completes
5. **Enum values** — keep enum options short and descriptive; the model performs better with clear choices
