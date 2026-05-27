# Mastra — Memory

> Source: [mastra.ai/docs/memory](https://mastra.ai/docs/memory/overview) · `@mastra/core` v1.37.x

## Table of Contents

- [Overview](#overview)
- [Memory Types](#memory-types)
- [Setup](#setup)
- [Basic Usage](#basic-usage)
- [Message History](#message-history)
- [Working Memory](#working-memory)
- [Semantic Recall](#semantic-recall)
- [Observational Memory](#observational-memory)
- [Multi-User Threads](#multi-user-threads)
- [Memory in Multi-Agent Systems](#memory-in-multi-agent-systems)
- [Dynamic Memory](#dynamic-memory)
- [Memory Processors](#memory-processors)
- [Common Patterns](#common-patterns)
- [Pitfalls](#pitfalls)

## Overview

Mastra's memory system enables agents to maintain context across conversations. It provides five complementary memory mechanisms: message history, working memory, semantic recall, observational memory, and multi-user threads.

Memory requires a storage provider and operates on two key identifiers:
- **`resource`** — stable user/entity identifier (persists across conversations)
- **`thread`** — conversation/session ID (scopes a single conversation)

## Memory Types

| Type | Purpose | Scope |
|------|---------|-------|
| Message History | Store user messages, agent replies, tool results | Thread |
| Working Memory | Persistent structured data (names, preferences, goals) | Resource |
| Semantic Recall | Retrieve past messages by meaning similarity | Resource |
| Observational Memory | Dense observation log replacing raw history | Thread |
| Multi-User Threads | Shared threads between multiple users | Thread + Resources |

## Setup

```bash
npm install @mastra/memory@latest @mastra/libsql@latest
```

Configure storage on the Mastra instance:

```typescript
import { Mastra } from '@mastra/core'
import { LibSQLStore } from '@mastra/libsql'

export const mastra = new Mastra({
  storage: new LibSQLStore({
    id: 'mastra-storage',
    url: ':memory:',  // Use 'file:./mastra.db' for persistence
  }),
})
```

Create a memory-enabled agent:

```typescript
import { Agent } from '@mastra/core/agent'
import { Memory } from '@mastra/memory'

export const memoryAgent = new Agent({
  id: 'memory-agent',
  name: 'Memory Agent',
  instructions: 'You are a helpful assistant that remembers user preferences.',
  model: 'openai/gpt-5-mini',
  memory: new Memory({
    options: {
      lastMessages: 20,  // Keep last 20 messages in context
    },
  }),
})
```

## Basic Usage

### Storing Information

```typescript
const response = await memoryAgent.generate(
  'Remember that my favorite color is blue and I prefer dark mode.',
  {
    memory: {
      resource: 'user-123',
      thread: 'conversation-456',
    },
  }
)
```

### Recalling Information

```typescript
const response = await memoryAgent.generate(
  "What's my favorite color?",
  {
    memory: {
      resource: 'user-123',
      thread: 'conversation-456',
    },
  }
)
// Agent responds with stored preference
```

## Message History

The simplest memory type — stores conversation turns and replays them as context:

```typescript
const memory = new Memory({
  options: {
    lastMessages: 50,  // Number of recent messages to include
  },
})
```

Messages are scoped to (resource, thread) pairs. Same resource, different thread = different conversation history.

## Working Memory

Persistent, structured user data that persists across threads:

```typescript
const memory = new Memory({
  options: {
    lastMessages: 20,
    workingMemory: {
      enabled: true,
      template: `
        User Profile:
        - Name: (unknown)
        - Preferences: (none yet)
        - Goals: (none yet)
      `,
    },
  },
})
```

Working memory is updated by the agent as it learns about the user. It's resource-scoped, meaning all threads for a user share the same working memory.

## Semantic Recall

Retrieve relevant past messages based on meaning rather than exact keywords:

```typescript
const memory = new Memory({
  options: {
    lastMessages: 20,
    semanticRecall: {
      enabled: true,
      topK: 5,  // Number of relevant messages to retrieve
    },
  },
})
```

Semantic recall uses embeddings to find contextually relevant past messages, even from different threads of the same resource.

## Observational Memory

Uses background agents to maintain a dense observation log that replaces raw message history as it grows:

```typescript
const memory = new Memory({
  options: {
    observationalMemory: true,
  },
})
```

Recommended for long conversations to prevent context window overflow. The background agent extracts key observations and replaces verbose message history with concise summaries.

## Multi-User Threads

Enable thread sharing between multiple users:

```typescript
const response = await agent.generate('Let me check the project status', {
  memory: {
    resource: 'user-alice',
    thread: 'project-chat',
  },
})

// Another user on the same thread
const response2 = await agent.generate('Any updates from Alice?', {
  memory: {
    resource: 'user-bob',
    thread: 'project-chat',
  },
})
```

## Memory in Multi-Agent Systems

### Automatic Isolation (Supervisor Pattern)

When a supervisor delegates to a subagent, Mastra automatically isolates memory:
- **Unique thread ID** per delegation — clean message history
- **Deterministic resource ID** — `{parentResourceId}-{agentName}` — persists across delegations

### Intentional Sharing

For agents that need shared context, use matching resource and thread IDs:

```typescript
// Resource-scoped sharing (most common)
// Both agents share working memory and semantic recall
const agentA = new Agent({
  id: 'agent-a',
  memory: sharedMemory,
})

const agentB = new Agent({
  id: 'agent-b',
  memory: sharedMemory,
})
```

## Dynamic Memory

Configure memory per request based on context:

```typescript
const agent = new Agent({
  id: 'dynamic-agent',
  name: 'Dynamic Agent',
  instructions: 'You are helpful.',
  model: 'openai/gpt-5-mini',
  memory: ({ requestContext }) => {
    const userTier = requestContext.get('user-tier')
    if (userTier === 'enterprise') {
      return new Memory({
        options: {
          lastMessages: 100,
          semanticRecall: { enabled: true, topK: 10 },
          workingMemory: { enabled: true },
        },
      })
    }
    return new Memory({
      options: { lastMessages: 10 },
    })
  },
})
```

## Memory Processors

When combined memory exceeds model context limits, processors filter and prioritize content:

```typescript
const memory = new Memory({
  options: {
    lastMessages: 50,
    semanticRecall: { enabled: true, topK: 10 },
  },
  processors: [
    // Custom processor to filter or summarize
    async (messages) => {
      return messages.filter(m => m.role !== 'system' || m.content.length < 500)
    },
  ],
})
```

## Common Patterns

### Customer Support Agent with Full Memory

```typescript
const supportAgent = new Agent({
  id: 'support',
  name: 'Support Agent',
  instructions: `You are a customer support agent. Use the customer's history
to provide personalized help. Reference their preferences and past issues.`,
  model: 'openai/gpt-5.4',
  tools: { ticketTool, orderTool },
  memory: new Memory({
    options: {
      lastMessages: 30,
      workingMemory: {
        enabled: true,
        template: `Customer Profile:
- Name: (unknown)
- Plan: (unknown)
- Past Issues: (none)
- Preferences: (none)`,
      },
      semanticRecall: { enabled: true, topK: 5 },
    },
  }),
})
```

## Pitfalls

1. **Storage is required** — memory doesn't work without a configured storage provider
2. **Don't reuse thread IDs across different resources** — causes errors and data leaks
3. **Use `resource` for the user, `thread` for the conversation** — resource persists across sessions
4. **Large `lastMessages` values** increase cost — balance context quality with token usage
5. **Enable observational memory** for long-running conversations to avoid context window overflow
6. **Semantic recall requires embeddings** — ensure your embedding model is configured
