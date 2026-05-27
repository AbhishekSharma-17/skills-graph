# Mastra — Workflows

> Source: [mastra.ai/docs/workflows](https://mastra.ai/docs/workflows/overview) · `@mastra/core` v1.37.x

## Table of Contents

- [Overview](#overview)
- [Creating Steps](#creating-steps)
- [Creating Workflows](#creating-workflows)
- [Running Workflows](#running-workflows)
- [Streaming Workflows](#streaming-workflows)
- [Workflow State](#workflow-state)
- [Workflow Results](#workflow-results)
- [Nested Workflows](#nested-workflows)
- [Registering Workflows](#registering-workflows)
- [Request Context](#request-context)
- [Studio Integration](#studio-integration)
- [Pitfalls](#pitfalls)

## Overview

Workflows define deterministic sequences of typed steps with explicit control flow. Unlike agents (which reason about what to do next), workflows follow a developer-defined execution graph. Use workflows when tasks are clearly defined upfront and require predictable, repeatable execution.

## Creating Steps

Steps are the building blocks. Each step has typed input/output schemas and an async execute function:

```typescript
import { createStep } from '@mastra/core/workflows'
import { z } from 'zod'

const formatStep = createStep({
  id: 'format',
  inputSchema: z.object({ message: z.string() }),
  outputSchema: z.object({ formatted: z.string() }),
  execute: async ({ inputData }) => ({
    formatted: inputData.message.toUpperCase(),
  }),
})
```

### Step Execute Context

The `execute` function receives a rich context object:

```typescript
execute: async ({
  inputData,       // Typed input matching inputSchema
  state,           // Shared workflow state
  setState,        // Update shared state
  resumeData,      // Data from resume() after suspend
  suspend,         // Suspend execution for human input
  requestContext,   // Request-scoped values (Map)
}) => {
  // Step logic here
  return { /* matches outputSchema */ }
}
```

### Step with Agent Call

Steps can invoke agents, tools, or any async operation:

```typescript
const analyzeStep = createStep({
  id: 'analyze',
  inputSchema: z.object({ text: z.string() }),
  outputSchema: z.object({ summary: z.string(), sentiment: z.string() }),
  execute: async ({ inputData }) => {
    const agent = mastra.getAgentById('analyst')
    const result = await agent.generate(`Analyze: ${inputData.text}`, {
      output: z.object({ summary: z.string(), sentiment: z.string() }),
    })
    return result.object
  },
})
```

## Creating Workflows

Chain steps using `.then()` and finalize with `.commit()`:

```typescript
import { createWorkflow } from '@mastra/core/workflows'

export const myWorkflow = createWorkflow({
  id: 'my-workflow',
  inputSchema: z.object({ message: z.string() }),
  outputSchema: z.object({ result: z.string() }),
})
  .then(formatStep)
  .then(processStep)
  .then(outputStep)
  .commit()
```

### Schema Chaining Rules

- First step's `inputSchema` must match workflow's `inputSchema`
- Each step's `outputSchema` must match the next step's `inputSchema`
- Final step's `outputSchema` must match workflow's `outputSchema`
- Use `.map()` to transform data when schemas don't align

## Running Workflows

### Synchronous Execution

```typescript
const run = await myWorkflow.createRun()
const result = await run.start({
  inputData: { message: 'Hello world' },
})

if (result.status === 'success') {
  console.log(result.result) // Typed output
}
```

### With Request Context

```typescript
const run = await myWorkflow.createRun()
const result = await run.start({
  inputData: { message: 'Hello' },
  requestContext: new Map([
    ['user-id', 'user-123'],
    ['user-tier', 'enterprise'],
  ]),
})
```

## Streaming Workflows

Stream events during execution for real-time monitoring:

```typescript
const run = await myWorkflow.createRun()
const stream = run.stream({
  inputData: { message: 'Hello world' },
})

for await (const chunk of stream.fullStream) {
  switch (chunk.type) {
    case 'step-started':
      console.log(`Step ${chunk.stepId} started`)
      break
    case 'step-completed':
      console.log(`Step ${chunk.stepId} completed:`, chunk.output)
      break
    case 'step-failed':
      console.error(`Step ${chunk.stepId} failed:`, chunk.error)
      break
  }
}

const result = await stream.result
```

## Workflow State

Share values across steps without threading through every schema:

```typescript
const step1 = createStep({
  id: 'step-1',
  inputSchema: z.object({ message: z.string() }),
  outputSchema: z.object({ formatted: z.string() }),
  stateSchema: z.object({ counter: z.number() }),
  execute: async ({ inputData, state, setState }) => {
    // Read shared state
    console.log('Counter:', state.counter)

    // Update shared state
    setState({ ...state, counter: state.counter + 1 })

    return { formatted: inputData.message.toUpperCase() }
  },
})
```

State persists across suspend/resume cycles and is accessible from nested workflows.

## Workflow Results

Results return a discriminated union based on status:

| Status | Properties | Meaning |
|--------|-----------|---------|
| `success` | `result` | Workflow completed successfully |
| `failed` | `error` | A step threw an error |
| `suspended` | `suspendPayload`, `suspended` | Waiting for human input |
| `tripwire` | `tripwire` (reason, retry, metadata) | Guard condition triggered |
| `paused` | — | Workflow is sleeping |

```typescript
const result = await run.start({ inputData })

switch (result.status) {
  case 'success':
    console.log('Output:', result.result)
    break
  case 'failed':
    console.error('Error:', result.error)
    break
  case 'suspended':
    console.log('Waiting for input at:', result.suspended)
    break
}
```

## Nested Workflows

Reuse workflows as steps inside larger workflows:

```typescript
const innerWorkflow = createWorkflow({
  id: 'inner',
  inputSchema: z.object({ text: z.string() }),
  outputSchema: z.object({ processed: z.string() }),
})
  .then(step1)
  .then(step2)
  .commit()

const outerWorkflow = createWorkflow({
  id: 'outer',
  inputSchema: z.object({ text: z.string() }),
  outputSchema: z.object({ processed: z.string() }),
})
  .then(innerWorkflow)  // Use as a step
  .then(finalStep)
  .commit()
```

Use `cloneWorkflow()` to create independent copies tracked separately:

```typescript
import { cloneWorkflow } from '@mastra/core/workflows'
const cloned = cloneWorkflow(innerWorkflow, { id: 'cloned-inner' })
```

## Registering Workflows

```typescript
export const mastra = new Mastra({
  workflows: { myWorkflow },
})

// Retrieve with type safety
const wf = mastra.getWorkflow('my-workflow')
```

## Request Context

Access request-scoped values inside steps:

```typescript
const step = createStep({
  id: 'conditional-step',
  inputSchema: z.object({ query: z.string() }),
  outputSchema: z.object({ maxResults: z.number() }),
  execute: async ({ inputData, requestContext }) => {
    const userTier = requestContext.get('user-tier')
    return {
      maxResults: userTier === 'enterprise' ? 1000 : 50,
    }
  },
})
```

## Studio Integration

Mastra Studio visualizes workflows with:
- **Graph view** — real-time step status visualization
- **Input form** — auto-generated from workflow `inputSchema`
- **Time travel** — replay individual steps post-execution
- **State inspector** — view shared state at each step

## Pitfalls

1. **Always call `.commit()`** — forgetting this leaves the workflow in an invalid state
2. **Schema alignment** — each step's output must match the next step's input. Use `.map()` for transformations
3. **Don't mix agents and workflows unnecessarily** — use workflows for deterministic pipelines, agents for open-ended tasks
4. **Use `stateSchema`** for cross-step data — don't try to pass everything through input/output schemas
5. **Register workflows** on the Mastra instance for Studio integration and observability
