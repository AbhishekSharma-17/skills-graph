# Mastra — Overview & Setup

> Source: [mastra.ai/docs](https://mastra.ai/docs) · `@mastra/core` v1.37.x

## What Is Mastra

Mastra is a TypeScript framework for building production-ready AI applications. Created by the team behind Gatsby.js, it provides primitives for agents, tools, workflows, memory, RAG, evals, voice, and observability — all with full type safety.

Key differentiators:
- **TypeScript-native** — end-to-end type safety, Zod/Valibot/ArkType schemas
- **Model routing** — connect to 40+ providers (OpenAI, Anthropic, Gemini, etc.) through one interface
- **Graph-based workflows** — deterministic orchestration with suspend/resume
- **Built-in Studio** — visual debugger, agent tester, workflow inspector
- **Framework-agnostic** — works with Next.js, React, Astro, Express, Hono, SvelteKit, or standalone

## When to Use Mastra

| Use Case | Mastra Primitive |
|----------|-----------------|
| Open-ended reasoning with tools | Agent |
| Deterministic multi-step pipelines | Workflow |
| External API/service calls | Tool |
| Cross-conversation context | Memory |
| Document Q&A | RAG |
| Multi-specialist coordination | Supervisor Agent |
| Quality measurement | Evals (Scorers) |
| Speech input/output | Voice |

## Installation

### New Project

```bash
npx create-mastra@latest
```

The CLI scaffolds a project with the recommended structure.

### Add to Existing Project

```bash
# Core framework
npm install @mastra/core@latest

# Optional packages
npm install @mastra/memory@latest       # Memory system
npm install @mastra/libsql@latest       # LibSQL storage
npm install @mastra/evals@latest        # Evaluation scorers
npm install @mastra/observability@latest # Tracing & metrics
```

### Environment Variables

```bash
# .env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
# Add provider keys as needed
```

## Project Structure

```
src/
  mastra/
    index.ts          # Mastra instance (entry point)
    agents/
      my-agent.ts     # Agent definitions
    tools/
      my-tool.ts      # Tool definitions
    workflows/
      my-workflow.ts  # Workflow definitions
```

## Mastra Instance

The central `Mastra` class registers all primitives and provides shared configuration:

```typescript
import { Mastra } from '@mastra/core'
import { LibSQLStore } from '@mastra/libsql'
import { myAgent } from './agents/my-agent'
import { myWorkflow } from './workflows/my-workflow'

export const mastra = new Mastra({
  agents: { myAgent },
  workflows: { myWorkflow },
  storage: new LibSQLStore({
    id: 'mastra-storage',
    url: ':memory:',       // or 'file:./mastra.db' for persistence
  }),
  server: {
    port: 4111,            // default
    host: 'localhost',
  },
})
```

## Running the Dev Server

```bash
# Start with Studio
npx mastra dev

# Access Studio UI
open http://localhost:4111
```

Studio provides:
- Agent testing with conversation UI
- Workflow graph visualization with time-travel debugging
- Trace viewer for observability
- Eval experiment runner

## Model Routing

Mastra uses a `provider/model-name` format for model selection:

```typescript
// OpenAI
model: 'openai/gpt-5.4'
model: 'openai/gpt-5-mini'

// Anthropic
model: 'anthropic/claude-sonnet-4-5-20250514'

// Google
model: 'google/gemini-2.5-flash'

// Any provider supported by the AI SDK
model: 'provider/model-name'
```

No separate provider configuration needed — just set the appropriate API key in your environment.

## Core Concepts at a Glance

### Agents
Autonomous LLM-powered entities that reason about tasks and use tools:

```typescript
import { Agent } from '@mastra/core/agent'

const agent = new Agent({
  id: 'helper',
  name: 'Helper',
  instructions: 'You are a helpful assistant.',
  model: 'openai/gpt-5-mini',
  tools: { myTool },
})
```

### Tools
Functions that agents can call to interact with external systems:

```typescript
import { createTool } from '@mastra/core/tools'
import { z } from 'zod'

const weatherTool = createTool({
  id: 'weather',
  description: 'Get current weather for a location',
  inputSchema: z.object({ city: z.string() }),
  outputSchema: z.object({ temp: z.number(), condition: z.string() }),
  execute: async ({ city }) => {
    const res = await fetch(`https://api.weather.com/${city}`)
    return res.json()
  },
})
```

### Workflows
Deterministic, graph-based pipelines with typed steps:

```typescript
import { createWorkflow, createStep } from '@mastra/core/workflows'
import { z } from 'zod'

const workflow = createWorkflow({
  id: 'pipeline',
  inputSchema: z.object({ text: z.string() }),
  outputSchema: z.object({ result: z.string() }),
})
  .then(step1)
  .then(step2)
  .commit()
```

## Agents vs Workflows

| Dimension | Agent | Workflow |
|-----------|-------|---------|
| Control | LLM decides next action | Developer defines execution graph |
| Use case | Open-ended tasks | Deterministic pipelines |
| Tool selection | Dynamic, based on reasoning | Explicit per step |
| Error handling | Retries via LLM reasoning | Step-level error schemas |
| Observability | Per-generation traces | Per-step traces with state |

Use agents when the steps aren't known in advance. Use workflows when you need predictable, repeatable execution.

## Schema Libraries

Mastra supports any schema library that outputs Standard JSON Schema:

- **Zod** (recommended) — `z.object({ ... })`
- **Valibot** — via `toStandardJsonSchema()`
- **ArkType** — `type({ ... })`
- **JSON Schema** — raw JSON Schema objects

## Next Steps

- `01-agents.md` — Creating and using agents
- `02-tools.md` — Building tools for agents
- `03-workflows.md` — Designing workflow pipelines
- `06-memory.md` — Adding memory to agents
