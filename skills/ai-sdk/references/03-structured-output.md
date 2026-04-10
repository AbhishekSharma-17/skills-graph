# Structured Output

> Source: https://ai-sdk.dev/docs/ai-sdk-core/generating-structured-data

## Overview

AI SDK generates type-safe, validated structured data using the `output` property on `generateText` and `streamText`. Supports Zod schemas, Valibot schemas, and raw JSON Schema. Output types include objects, arrays, choices, and unstructured JSON.

## Output Types

### Output.object() — Typed Objects

```typescript
import { generateText, Output } from 'ai';
import { z } from 'zod';

const { output } = await generateText({
  model: 'anthropic/claude-sonnet-4.5',
  output: Output.object({
    schema: z.object({
      name: z.string().describe('Recipe name'),
      servings: z.number().describe('Number of servings'),
      ingredients: z.array(z.object({
        name: z.string(),
        amount: z.string(),
        unit: z.string(),
      })),
      steps: z.array(z.string()),
      prepTimeMinutes: z.number(),
    }),
  }),
  prompt: 'Generate a vegetarian pasta recipe.',
});

// output is fully typed: { name: string, servings: number, ... }
console.log(output.name, output.ingredients.length);
```

### Output.array() — Typed Arrays

```typescript
const { output, elementStream } = streamText({
  model: 'openai/gpt-5.2',
  output: Output.array({
    element: z.object({
      name: z.string(),
      role: z.string(),
      backstory: z.string(),
    }),
  }),
  prompt: 'Generate 5 RPG characters.',
});

// Stream validated elements one at a time
for await (const character of elementStream) {
  console.log(character.name); // Each element is complete and validated
}
```

### Output.choice() — Enum Selection

```typescript
const { output } = await generateText({
  model: 'anthropic/claude-sonnet-4.5',
  output: Output.choice({
    options: ['positive', 'negative', 'neutral'],
  }),
  prompt: 'Classify the sentiment: "This product is amazing!"',
});

// output: 'positive'
```

### Output.json() — Unstructured JSON

```typescript
const { output } = await generateText({
  model: 'openai/gpt-5.2',
  output: Output.json(),
  prompt: 'Return the data as JSON.',
});

// output is unknown — no schema validation
```

### Output.text() — Plain Text (Default)

```typescript
const { output } = await generateText({
  model: 'anthropic/claude-sonnet-4.5',
  output: Output.text(),
  prompt: 'Hello!',
});
// Same as not specifying output at all
```

## Schema Best Practices

### Descriptive Schemas

```typescript
const eventSchema = z.object({
  title: z.string().describe('Event name, max 100 chars'),
  date: z.string().describe('ISO 8601 date format (YYYY-MM-DD)'),
  location: z.object({
    venue: z.string().describe('Venue name'),
    city: z.string(),
    country: z.string().describe('ISO 3166-1 alpha-2 country code'),
  }),
  attendees: z.number().describe('Expected number of attendees'),
  tags: z.array(z.string()).describe('2-5 relevant tags'),
});
```

### Optional Fields

```typescript
const profileSchema = z.object({
  name: z.string(),
  email: z.string().email(),
  bio: z.string().optional().describe('Short bio, if available'),
  website: z.string().url().optional(),
});
```

### Enums and Literals

```typescript
const taskSchema = z.object({
  title: z.string(),
  priority: z.enum(['low', 'medium', 'high', 'critical']),
  status: z.literal('pending'),
  dueDate: z.string().nullable(),
});
```

## Streaming Structured Output

### Partial Object Stream

```typescript
const { partialOutputStream } = streamText({
  model: 'anthropic/claude-sonnet-4.5',
  output: Output.object({
    schema: z.object({
      summary: z.string(),
      keyPoints: z.array(z.string()),
      sentiment: z.enum(['positive', 'negative', 'neutral']),
    }),
  }),
  prompt: 'Analyze this article...',
});

for await (const partial of partialOutputStream) {
  // partial has optional fields as they stream in
  if (partial.summary) {
    updateUI(partial.summary);
  }
}
```

### Element Stream (Arrays)

```typescript
const { elementStream } = streamText({
  model: 'openai/gpt-5.2',
  output: Output.array({
    element: z.object({
      question: z.string(),
      answer: z.string(),
      difficulty: z.enum(['easy', 'medium', 'hard']),
    }),
  }),
  prompt: 'Generate 10 trivia questions about space.',
});

for await (const item of elementStream) {
  // Each item is fully validated before emission
  addToQuiz(item);
}
```

## Combining with Tools

Structured output works alongside tool calling:

```typescript
import { generateText, Output, tool } from 'ai';
import { z } from 'zod';

const { output } = await generateText({
  model: 'anthropic/claude-sonnet-4.5',
  tools: {
    getWeather: tool({
      description: 'Get current weather',
      inputSchema: z.object({ city: z.string() }),
      execute: async ({ city }) => ({ temp: 72, condition: 'sunny' }),
    }),
    getNews: tool({
      description: 'Get latest news headlines',
      inputSchema: z.object({ topic: z.string() }),
      execute: async ({ topic }) => ({ headlines: ['...'] }),
    }),
  },
  output: Output.object({
    schema: z.object({
      recommendation: z.string(),
      reasoning: z.string(),
      confidence: z.number().min(0).max(1),
    }),
  }),
  maxSteps: 5,
  prompt: 'Should I go to the beach today in San Francisco?',
});
```

Note: generating structured output counts as a step in multi-step execution.

## Output Metadata

```typescript
const { output } = await generateText({
  model: 'openai/gpt-5.2',
  output: Output.object({
    name: 'WeatherReport',
    description: 'A structured weather report for a city.',
    schema: z.object({
      city: z.string(),
      temperature: z.number(),
      conditions: z.string(),
    }),
  }),
  prompt: 'Weather report for Tokyo.',
});
```

## Error Handling

```typescript
import { generateText, Output, NoObjectGeneratedError } from 'ai';

try {
  const { output } = await generateText({
    model: 'anthropic/claude-sonnet-4.5',
    output: Output.object({ schema: mySchema }),
    prompt: 'Generate structured data.',
  });
} catch (error) {
  if (NoObjectGeneratedError.isInstance(error)) {
    console.error('Failed to generate valid object');
    console.error('Raw text:', error.text);
    console.error('Cause:', error.cause);
    console.error('Usage:', error.usage);
  }
}
```

### Streaming Error Handling

```typescript
const result = streamText({
  model: 'openai/gpt-5.2',
  output: Output.object({ schema: mySchema }),
  prompt: 'Generate data.',
  onError: ({ error }) => {
    console.error('Stream error:', error);
  },
});
```

## Accessing Reasoning

```typescript
const result = await generateText({
  model: 'anthropic/claude-sonnet-4.5',
  output: Output.object({ schema: mySchema }),
  prompt: 'Complex analysis...',
  providerOptions: {
    anthropic: {
      thinking: { type: 'enabled', budgetTokens: 5000 },
    },
  },
});

console.log(result.reasoning); // Model's thinking process
console.log(result.output);    // Structured result
```

## Common Pitfalls

1. **Schema too complex** — Deeply nested schemas reduce generation quality; flatten when possible
2. **Missing descriptions** — `.describe()` on fields significantly improves output quality
3. **No maxSteps with tools** — If combining tools + output, set `maxSteps` or output won't generate
4. **Streaming partial types** — `partialOutputStream` has all fields as optional (Partial<T>)
5. **Large arrays** — Very large arrays may hit token limits; use `maxTokens` appropriately

## Related Topics

- Text generation → [02-generating-text](02-generating-text.md)
- Tool calling → [04-tool-calling](04-tool-calling.md)
- Agents → [05-agents](05-agents.md)
