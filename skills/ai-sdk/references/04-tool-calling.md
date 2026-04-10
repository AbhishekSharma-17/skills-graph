# Tool Calling

> Source: https://ai-sdk.dev/docs/ai-sdk-core/tool-calling

## Overview

Tools extend LLM capabilities beyond text generation. The model decides when and how to call tools based on the conversation context. AI SDK handles the execution loop, passing results back to the model automatically.

## Defining Tools

```typescript
import { tool } from 'ai';
import { z } from 'zod';

const weatherTool = tool({
  description: 'Get the current weather for a location',
  inputSchema: z.object({
    city: z.string().describe('City name'),
    units: z.enum(['celsius', 'fahrenheit']).default('celsius'),
  }),
  execute: async ({ city, units }) => {
    const data = await fetchWeather(city, units);
    return { temperature: data.temp, condition: data.condition };
  },
});
```

### Tool Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `description` | string | Yes | What the tool does (helps model decide when to use it) |
| `inputSchema` | ZodSchema | Yes | Input validation schema |
| `execute` | async function | Yes* | Execution function |
| `needsApproval` | boolean \| function | No | Human-in-the-loop approval |
| `inputExamples` | object[] | No | Example inputs for guidance |
| `toModelOutput` | function | No | Custom model-facing output |

*Tools without `execute` are "client-side tools" — the client handles execution.

## Using Tools with generateText

```typescript
import { generateText, tool } from 'ai';
import { z } from 'zod';

const { text, toolCalls, toolResults } = await generateText({
  model: 'anthropic/claude-sonnet-4.5',
  tools: {
    weather: tool({
      description: 'Get weather for a city',
      inputSchema: z.object({ city: z.string() }),
      execute: async ({ city }) => ({ temp: 72, condition: 'sunny' }),
    }),
    search: tool({
      description: 'Search the web',
      inputSchema: z.object({ query: z.string() }),
      execute: async ({ query }) => ({ results: ['...'] }),
    }),
  },
  prompt: 'What is the weather in Tokyo?',
});
```

## Multi-Step Tool Calling

Enable iterative tool use with `maxSteps`:

```typescript
const { text, steps } = await generateText({
  model: 'anthropic/claude-sonnet-4.5',
  tools: {
    search: tool({ /* ... */ }),
    calculate: tool({ /* ... */ }),
    summarize: tool({ /* ... */ }),
  },
  maxSteps: 10, // Allow up to 10 tool-calling iterations
  prompt: 'Research the GDP of France, calculate growth rate, and summarize.',
});

// steps contains each LLM call and tool execution
for (const step of steps) {
  console.log('Step:', step.toolCalls?.map(tc => tc.toolName));
}
```

## Tool Choice

Control which tools the model can use:

```typescript
// Let model decide (default)
toolChoice: 'auto'

// Force a specific tool
toolChoice: { type: 'tool', toolName: 'weather' }

// Require any tool (no plain text response)
toolChoice: 'required'

// Disable all tools for this call
toolChoice: 'none'
```

```typescript
const { text } = await generateText({
  model: 'anthropic/claude-sonnet-4.5',
  tools: { weather, search },
  toolChoice: { type: 'tool', toolName: 'weather' },
  prompt: 'Tell me about Tokyo.',
});
```

## Tool Execution Approval (Human-in-the-Loop)

### Simple Boolean

```typescript
const dangerousTool = tool({
  description: 'Delete a file from the filesystem',
  inputSchema: z.object({ path: z.string() }),
  needsApproval: true, // Always requires approval
  execute: async ({ path }) => {
    await fs.unlink(path);
    return { deleted: path };
  },
});
```

### Function-Based Approval

```typescript
const deployTool = tool({
  description: 'Deploy to production',
  inputSchema: z.object({
    service: z.string(),
    environment: z.enum(['staging', 'production']),
  }),
  needsApproval: ({ environment }) => {
    return environment === 'production'; // Only approve for prod
  },
  execute: async ({ service, environment }) => {
    return await deploy(service, environment);
  },
});
```

### Handling Approval in UI

When `needsApproval` triggers, the tool call appears with status `'requires-approval'`. The client must approve or deny before execution proceeds.

## Input Examples

Guide the model with example inputs:

```typescript
const queryTool = tool({
  description: 'Query the database',
  inputSchema: z.object({
    sql: z.string().describe('SQL query to execute'),
  }),
  inputExamples: [
    { sql: 'SELECT name, email FROM users WHERE active = true' },
    { sql: 'SELECT COUNT(*) FROM orders WHERE date > NOW() - INTERVAL 7 DAY' },
  ],
  execute: async ({ sql }) => await db.query(sql),
});
```

## Custom Model Output

Control what gets sent back to the model (save tokens):

```typescript
const searchTool = tool({
  description: 'Search documents',
  inputSchema: z.object({ query: z.string() }),
  execute: async ({ query }) => {
    const results = await search(query); // Full results with metadata
    return results;
  },
  toModelOutput: (result) => {
    // Send only titles back to model (token-efficient)
    return result.map(r => r.title).join('\n');
  },
});
```

## Strict Mode

Per-tool opt-in for native schema validation:

```typescript
const strictTool = tool({
  description: 'Strict validated tool',
  inputSchema: z.object({ value: z.number() }),
  execute: async ({ value }) => value * 2,
  experimental_strict: true, // Enable native strict mode
});
```

## Dynamic Tools

Generate tools at runtime based on context:

```typescript
import { dynamicTool } from 'ai';

const { text } = await generateText({
  model: 'anthropic/claude-sonnet-4.5',
  tools: {
    dynamic: dynamicTool({
      description: 'Dynamically generated tool',
      inputSchema: z.object({ action: z.string() }),
      factory: async ({ action }) => {
        // Return appropriate tool based on action
        return tool({
          inputSchema: z.object({ param: z.string() }),
          execute: async ({ param }) => `Executed ${action} with ${param}`,
        });
      },
    }),
  },
  prompt: 'Do something dynamic.',
});
```

## Streaming with Tools

```typescript
const result = streamText({
  model: 'anthropic/claude-sonnet-4.5',
  tools: { weather, search },
  maxSteps: 5,
  prompt: 'Weather and news for NYC?',
});

for await (const event of result.fullStream) {
  switch (event.type) {
    case 'tool-call':
      console.log(`Calling ${event.toolName}(${JSON.stringify(event.args)})`);
      break;
    case 'tool-result':
      console.log(`Result: ${JSON.stringify(event.result)}`);
      break;
    case 'text-delta':
      process.stdout.write(event.textDelta);
      break;
  }
}
```

## Stop Conditions

Control when the tool loop ends:

```typescript
import { generateText, stopWhen, stepCountIs, toolCallIs } from 'ai';

const { text } = await generateText({
  model: 'anthropic/claude-sonnet-4.5',
  tools: { research, summarize },
  stopWhen: stepCountIs(5), // Stop after 5 steps
  prompt: 'Research this topic.',
});

// Or stop when specific tool is called
stopWhen: toolCallIs('finalAnswer')
```

## Provider-Specific Tools

Some providers offer built-in tools:

```typescript
// Anthropic: Code execution
import { anthropic } from '@ai-sdk/anthropic';

const { text } = await generateText({
  model: anthropic('claude-sonnet-4-5-20250514'),
  tools: {
    code: anthropic.tools.codeExecution(),
    memory: anthropic.tools.memory(),
    search: anthropic.tools.toolSearch({ regex: /^(weather|news)/ }),
  },
  prompt: 'Calculate fibonacci(20)',
});
```

## Common Pitfalls

1. **Missing maxSteps** — Without it, only one tool call round occurs
2. **No description** — Tools without good descriptions won't be called appropriately
3. **Schema too vague** — Use `.describe()` on parameters for better tool use
4. **Forgetting async** — `execute` must be async even for sync operations
5. **Large tool results** — Use `toModelOutput` to avoid sending huge results back to model
6. **Too many tools** — Models perform worse with 20+ tools; use tool search or dynamic tools

## Related Topics

- Agents → [05-agents](05-agents.md)
- MCP integration → [08-mcp-integration](08-mcp-integration.md)
- Structured output → [03-structured-output](03-structured-output.md)
