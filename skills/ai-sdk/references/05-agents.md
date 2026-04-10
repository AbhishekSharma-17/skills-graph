# Agents

> Source: https://ai-sdk.dev/docs/agents/overview

## Overview

Agents combine LLMs, tools, and execution loops to accomplish complex multi-step tasks. AI SDK v6 introduces the `Agent` interface and `ToolLoopAgent` class for building production-ready agents with minimal boilerplate.

## Core Concepts

An agent requires three components:
1. **Language Model** — Processes input, determines next actions
2. **Tools** — Extend capabilities (API calls, file ops, database queries)
3. **Loop** — Orchestrates execution, manages context, handles stopping conditions

## ToolLoopAgent

The primary agent implementation. Handles tool execution loops, context management, and stopping conditions automatically.

```typescript
import { ToolLoopAgent, tool } from 'ai';
import { z } from 'zod';

const researchAgent = new ToolLoopAgent({
  model: 'anthropic/claude-sonnet-4.5',
  instructions: 'You are a research assistant. Find accurate information and cite sources.',
  tools: {
    search: tool({
      description: 'Search the web for information',
      inputSchema: z.object({ query: z.string() }),
      execute: async ({ query }) => await webSearch(query),
    }),
    readPage: tool({
      description: 'Read content from a URL',
      inputSchema: z.object({ url: z.string().url() }),
      execute: async ({ url }) => await fetchPage(url),
    }),
  },
  maxSteps: 15,
});
```

### Generating Responses

```typescript
// Simple generation
const { text } = await researchAgent.generate({
  prompt: 'What are the latest developments in quantum computing?',
});

// With message history
const { text } = await researchAgent.generate({
  messages: [
    { role: 'user', content: 'Research quantum computing' },
    { role: 'assistant', content: 'I found several recent developments...' },
    { role: 'user', content: 'Focus on error correction specifically' },
  ],
});
```

### Streaming Agent Responses

```typescript
const result = researchAgent.stream({
  prompt: 'Summarize recent AI safety papers.',
});

for await (const chunk of result.textStream) {
  process.stdout.write(chunk);
}
```

## Agent Configuration

```typescript
const agent = new ToolLoopAgent({
  // Required
  model: 'anthropic/claude-sonnet-4.5',
  tools: { /* ... */ },

  // Optional
  instructions: 'System prompt for the agent',
  maxSteps: 20,           // Max tool-calling iterations
  temperature: 0.7,       // Model temperature
  maxTokens: 4096,        // Max tokens per step

  // Lifecycle hooks
  onStepFinish: ({ text, toolCalls, usage }) => {
    console.log('Step done:', toolCalls?.length, 'tools called');
  },
  onFinish: ({ text, steps, totalUsage }) => {
    console.log(`Completed in ${steps.length} steps`);
  },
});
```

## Call Options (Type-Safe Context)

Inject dynamic context per request without modifying agent definition:

```typescript
import { ToolLoopAgent, tool, CallOptions } from 'ai';
import { z } from 'zod';

// Define typed call options
interface MyOptions extends CallOptions {
  userId: string;
  permissions: string[];
}

const agent = new ToolLoopAgent<MyOptions>({
  model: 'anthropic/claude-sonnet-4.5',
  tools: {
    getProfile: tool({
      description: 'Get user profile',
      inputSchema: z.object({}),
      execute: async (_, { options }) => {
        // Access typed options
        return await db.getUser(options.userId);
      },
    }),
  },
});

// Pass options at call time
const { text } = await agent.generate({
  prompt: 'Show my profile',
  options: { userId: 'user_123', permissions: ['read', 'write'] },
});
```

## Agent Interface

`Agent` is an interface — implement custom agents:

```typescript
import { Agent, AgentGenerateResult, AgentStreamResult } from 'ai';

class CustomAgent implements Agent {
  async generate(options): Promise<AgentGenerateResult> {
    // Custom generation logic
    // Could implement RAG, routing, or custom loops
  }

  stream(options): AgentStreamResult {
    // Custom streaming logic
  }
}
```

## Subagents

Decompose complex tasks into specialized sub-agents:

```typescript
const codeAgent = new ToolLoopAgent({
  model: 'anthropic/claude-sonnet-4.5',
  instructions: 'You write clean TypeScript code.',
  tools: { writeFile, runTests },
});

const reviewAgent = new ToolLoopAgent({
  model: 'anthropic/claude-sonnet-4.5',
  instructions: 'You review code for bugs and style issues.',
  tools: { readFile, createComment },
});

// Orchestrator delegates to subagents
const orchestrator = new ToolLoopAgent({
  model: 'anthropic/claude-sonnet-4.5',
  instructions: 'Coordinate code writing and review.',
  tools: {
    writeCode: tool({
      description: 'Write code for a feature',
      inputSchema: z.object({ spec: z.string() }),
      execute: async ({ spec }) => {
        const { text } = await codeAgent.generate({ prompt: spec });
        return text;
      },
    }),
    reviewCode: tool({
      description: 'Review written code',
      inputSchema: z.object({ code: z.string() }),
      execute: async ({ code }) => {
        const { text } = await reviewAgent.generate({ prompt: `Review: ${code}` });
        return text;
      },
    }),
  },
});
```

## Memory

Maintain context across interactions:

```typescript
import { ToolLoopAgent } from 'ai';

// Simple conversation memory
const conversationHistory: Message[] = [];

const agent = new ToolLoopAgent({
  model: 'anthropic/claude-sonnet-4.5',
  tools: { /* ... */ },
});

async function chat(userMessage: string) {
  conversationHistory.push({ role: 'user', content: userMessage });

  const { text, steps } = await agent.generate({
    messages: conversationHistory,
  });

  conversationHistory.push({ role: 'assistant', content: text });
  return text;
}
```

### With Anthropic Memory Tool

```typescript
import { anthropic } from '@ai-sdk/anthropic';

const agent = new ToolLoopAgent({
  model: anthropic('claude-sonnet-4-5-20250514'),
  tools: {
    memory: anthropic.tools.memory(), // Built-in memory management
    // ... other tools
  },
});
```

## Workflow Patterns

For deterministic flows, use explicit control rather than agent loops:

### Sequential Pipeline

```typescript
async function analyzeAndReport(topic: string) {
  // Step 1: Research
  const { text: research } = await generateText({
    model: 'anthropic/claude-sonnet-4.5',
    tools: { search },
    maxSteps: 5,
    prompt: `Research: ${topic}`,
  });

  // Step 2: Analyze
  const { output: analysis } = await generateText({
    model: 'anthropic/claude-sonnet-4.5',
    output: Output.object({ schema: analysisSchema }),
    prompt: `Analyze this research: ${research}`,
  });

  // Step 3: Generate report
  const { text: report } = await generateText({
    model: 'anthropic/claude-sonnet-4.5',
    prompt: `Write a report based on: ${JSON.stringify(analysis)}`,
  });

  return report;
}
```

### Conditional Branching

```typescript
async function handleRequest(input: string) {
  // Classify intent
  const { output: intent } = await generateText({
    model: 'anthropic/claude-sonnet-4.5',
    output: Output.choice({ options: ['question', 'task', 'complaint'] }),
    prompt: `Classify: ${input}`,
  });

  // Route to appropriate handler
  switch (intent) {
    case 'question':
      return await questionAgent.generate({ prompt: input });
    case 'task':
      return await taskAgent.generate({ prompt: input });
    case 'complaint':
      return await supportAgent.generate({ prompt: input });
  }
}
```

## Loop Control

### Stop Conditions

```typescript
import { stopWhen, stepCountIs, toolCallIs } from 'ai';

const agent = new ToolLoopAgent({
  model: 'anthropic/claude-sonnet-4.5',
  tools: { research, submit },
  stopWhen: toolCallIs('submit'), // Stop when submit tool is called
});
```

### Prepare Step

Customize each step before execution:

```typescript
const agent = new ToolLoopAgent({
  model: 'anthropic/claude-sonnet-4.5',
  tools: { /* ... */ },
  prepareStep: ({ stepNumber, previousSteps }) => {
    if (stepNumber > 8) {
      return { instructions: 'Wrap up and provide final answer.' };
    }
    return {};
  },
});
```

## Agent UI Stream

Connect agents to frontend UIs:

```typescript
// Server (Next.js route)
import { createAgentUIStreamResponse } from 'ai';

export async function POST(req: Request) {
  const { messages } = await req.json();

  return createAgentUIStreamResponse({
    agent: myAgent,
    messages,
  });
}
```

## Common Pitfalls

1. **Infinite loops** — Always set `maxSteps` to prevent runaway agents
2. **Token explosion** — Long conversations accumulate tokens; implement summarization
3. **Tool overload** — Too many tools confuse the model; keep focused toolsets
4. **Missing error handling** — Wrap tool execution in try/catch
5. **No observability** — Use `onStepFinish` to log agent behavior for debugging

## Related Topics

- Tool calling → [04-tool-calling](04-tool-calling.md)
- MCP integration → [08-mcp-integration](08-mcp-integration.md)
- Middleware → [10-middleware-and-telemetry](10-middleware-and-telemetry.md)
