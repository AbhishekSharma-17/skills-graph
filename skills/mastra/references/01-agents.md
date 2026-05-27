# Mastra — Agents

> Source: [mastra.ai/docs/agents](https://mastra.ai/docs/agents/overview) · `@mastra/core` v1.37.x

## Table of Contents

- [Overview](#overview)
- [Creating an Agent](#creating-an-agent)
- [Agent Configuration](#agent-configuration)
- [Generating Responses](#generating-responses)
- [Streaming Responses](#streaming-responses)
- [Generation Options](#generation-options)
- [Registering Agents](#registering-agents)
- [Dynamic Configuration](#dynamic-configuration)
- [Processors](#processors)
- [Agent Approval](#agent-approval)
- [Common Patterns](#common-patterns)
- [Pitfalls](#pitfalls)

## Overview

Agents are autonomous LLM-powered entities that reason about objectives, select tools, maintain context, and iterate until producing an answer. Use agents when the task is open-ended and the steps aren't known in advance.

## Creating an Agent

```typescript
import { Agent } from '@mastra/core/agent'

export const myAgent = new Agent({
  id: 'my-agent',
  name: 'My Agent',
  instructions: 'You are a helpful research assistant. Be concise and factual.',
  model: 'openai/gpt-5.4',
})
```

## Agent Configuration

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | `string` | Yes | Unique identifier |
| `name` | `string` | Yes | Display name |
| `instructions` | `string` | Yes | System prompt defining behavior |
| `model` | `string` | Yes | Model in `provider/model-name` format |
| `tools` | `Record<string, Tool>` | No | Tools the agent can use |
| `agents` | `Record<string, Agent>` | No | Subagents (supervisor pattern) |
| `memory` | `Memory \| Function` | No | Memory instance or factory |
| `scorers` | `Record<string, ScorerConfig>` | No | Live evaluation scorers |
| `processors` | `Processor[]` | No | Input/output guardrails |

## Generating Responses

### Basic Generation

`.generate()` returns the complete response after all tool executions finish:

```typescript
const agent = mastra.getAgentById('my-agent')
const response = await agent.generate('What is the capital of France?')

console.log(response.text)        // "Paris is the capital of France."
console.log(response.toolCalls)   // Array of tool calls made
console.log(response.toolResults) // Array of tool results
console.log(response.steps)       // Array of reasoning steps
console.log(response.usage)       // Token usage statistics
```

### With Conversation History

Pass an array of messages for multi-turn conversations:

```typescript
const response = await agent.generate([
  { role: 'user', content: 'My name is Alex.' },
  { role: 'assistant', content: 'Nice to meet you, Alex!' },
  { role: 'user', content: 'What is my name?' },
])
```

## Streaming Responses

`.stream()` delivers tokens progressively:

```typescript
const stream = await agent.stream('Write a haiku about TypeScript')

// Stream text chunks
for await (const chunk of stream.textStream) {
  process.stdout.write(chunk)
}

// After stream completes, access full results
const toolCalls = await stream.toolCalls
const toolResults = await stream.toolResults
const steps = await stream.steps
const usage = await stream.usage
```

### Full Stream (all events)

```typescript
const stream = await agent.stream('Analyze this data')

for await (const event of stream.fullStream) {
  switch (event.type) {
    case 'text-delta':
      process.stdout.write(event.textDelta)
      break
    case 'tool-call':
      console.log('Calling:', event.toolName, event.args)
      break
    case 'tool-result':
      console.log('Result:', event.toolName, event.result)
      break
  }
}
```

## Generation Options

Both `.generate()` and `.stream()` accept an options object:

```typescript
const response = await agent.generate('query', {
  // Tool control
  toolChoice: 'auto',            // 'auto' | 'required' | 'none' | { type: 'tool', toolName: '...' }
  activeTools: ['weatherTool'],  // Restrict which tools are available
  maxSteps: 10,                  // Maximum tool-use iterations (default: 5)

  // Memory
  memory: {
    resource: 'user-123',        // Stable user/entity identifier
    thread: 'conv-456',          // Conversation/session ID
  },

  // Structured output
  output: myZodSchema,           // Return typed object instead of text

  // Request context
  requestContext: new Map([
    ['user-tier', 'enterprise'],
  ]),
})
```

## Registering Agents

Register agents in the Mastra instance for shared resources:

```typescript
import { Mastra } from '@mastra/core'
import { myAgent } from './agents/my-agent'

export const mastra = new Mastra({
  agents: { myAgent },
})

// Retrieve registered agent
const agent = mastra.getAgentById('my-agent')
```

Registered agents gain access to memory, logging, observability, and storage configured on the Mastra instance.

## Dynamic Configuration

Swap model or instructions at runtime based on request context:

```typescript
const agent = new Agent({
  id: 'adaptive-agent',
  name: 'Adaptive Agent',
  instructions: ({ requestContext }) => {
    const lang = requestContext.get('language') || 'en'
    return `Respond in ${lang}. Be concise.`
  },
  model: ({ requestContext }) => {
    const tier = requestContext.get('user-tier')
    return tier === 'enterprise' ? 'openai/gpt-5.4' : 'openai/gpt-5-mini'
  },
})
```

## Processors

Intercept or transform messages before and after generation:

```typescript
import { Agent } from '@mastra/core/agent'
import { PromptInjectionDetector } from '@mastra/core/agent/processors'

const agent = new Agent({
  id: 'safe-agent',
  name: 'Safe Agent',
  instructions: 'You are a helpful assistant.',
  model: 'openai/gpt-5-mini',
  processors: [
    new PromptInjectionDetector({
      model: 'openai/gpt-5-mini',
      strategy: 'block',
    }),
  ],
})
```

See `10-guardrails.md` for the full processor catalog.

## Agent Approval

Require human approval before tool execution:

```typescript
const sensitiveAgent = new Agent({
  id: 'sensitive-agent',
  name: 'Sensitive Agent',
  instructions: 'You manage user accounts.',
  model: 'openai/gpt-5.4',
  tools: {
    deleteAccount: {
      ...deleteAccountTool,
      requireApproval: true,
    },
  },
})

// During streaming, listen for approval requests
for await (const event of stream.fullStream) {
  if (event.type === 'tool-approval-request') {
    // Present to user for approval
    await event.approve() // or event.reject()
  }
}
```

## Common Patterns

### Agent with Tools and Memory

```typescript
import { Agent } from '@mastra/core/agent'
import { Memory } from '@mastra/memory'
import { searchTool, calcTool } from './tools'

export const assistantAgent = new Agent({
  id: 'assistant',
  name: 'Assistant',
  instructions: `You are a research assistant with access to search and calculation tools.
Always cite your sources. Use tools when the user asks factual questions.`,
  model: 'openai/gpt-5.4',
  tools: { searchTool, calcTool },
  memory: new Memory({
    options: { lastMessages: 20 },
  }),
})
```

### Agent with Live Evals

```typescript
import { createAnswerRelevancyScorer } from '@mastra/evals'

const agent = new Agent({
  id: 'evaluated-agent',
  name: 'Evaluated Agent',
  instructions: 'Answer questions accurately.',
  model: 'openai/gpt-5.4',
  scorers: {
    relevancy: {
      scorer: createAnswerRelevancyScorer({ model: 'openai/gpt-5-mini' }),
      sampling: { type: 'ratio', rate: 0.5 },
    },
  },
})
```

## Pitfalls

1. **Don't overload a single agent** — if an agent needs many tools and complex instructions, split into multiple specialized agents with a supervisor
2. **Match model to task** — use smaller models for simple tool routing, larger for complex reasoning
3. **Instructions matter** — be specific about behavior, format, and tool usage patterns
4. **Register agents** on the Mastra instance to get shared resources (memory, observability, storage)
5. **Use `maxSteps`** to prevent infinite tool-calling loops
