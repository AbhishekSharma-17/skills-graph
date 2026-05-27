# Mastra — Workflow Control Flow

> Source: [mastra.ai/docs/workflows/control-flow](https://mastra.ai/docs/workflows/control-flow) · `@mastra/core` v1.37.x

## Table of Contents

- [Overview](#overview)
- [Sequential: .then()](#sequential-then)
- [Parallel: .parallel()](#parallel-parallel)
- [Branching: .branch()](#branching-branch)
- [Data Transform: .map()](#data-transform-map)
- [Do-Until Loop: .dountil()](#do-until-loop-dountil)
- [Do-While Loop: .dowhile()](#do-while-loop-dowhile)
- [Array Iteration: .foreach()](#array-iteration-foreach)
- [Nested Workflows in Control Flow](#nested-workflows-in-control-flow)
- [Pattern Selection Guide](#pattern-selection-guide)
- [Pitfalls](#pitfalls)

## Overview

Workflows compose steps using control flow methods. Each method determines how schemas connect and how data flows between steps.

## Sequential: .then()

Chain steps sequentially. Each step's output feeds the next step's input:

```typescript
workflow
  .then(step1)  // Takes workflow input
  .then(step2)  // Receives step1's output
  .then(step3)  // Receives step2's output
  .commit()
```

## Parallel: .parallel()

Run multiple steps simultaneously against the same input:

```typescript
const formatStep = createStep({
  id: 'format-step',
  inputSchema: z.object({ text: z.string() }),
  outputSchema: z.object({ formatted: z.string() }),
  execute: async ({ inputData }) => ({ formatted: inputData.text.toUpperCase() }),
})

const countStep = createStep({
  id: 'count-step',
  inputSchema: z.object({ text: z.string() }),
  outputSchema: z.object({ count: z.number() }),
  execute: async ({ inputData }) => ({ count: inputData.text.length }),
})

workflow
  .parallel([formatStep, countStep])
  .then(combineStep)
  .commit()
```

**Output structure** — keyed by step ID:

```typescript
{
  "format-step": { formatted: "HELLO" },
  "count-step": { count: 5 }
}
```

**Downstream step** must accept the combined shape:

```typescript
const combineStep = createStep({
  id: 'combine',
  inputSchema: z.object({
    'format-step': z.object({ formatted: z.string() }),
    'count-step': z.object({ count: z.number() }),
  }),
  outputSchema: z.object({ summary: z.string() }),
  execute: async ({ inputData }) => ({
    summary: `${inputData['format-step'].formatted} (${inputData['count-step'].count} chars)`,
  }),
})
```

If any parallel step fails, the entire parallel block fails. Build resilience with try/catch inside steps.

## Branching: .branch()

Execute different steps based on runtime conditions:

```typescript
workflow
  .branch([
    [async ({ inputData }) => inputData.value > 10, highValueStep],
    [async ({ inputData }) => inputData.value <= 10, lowValueStep],
  ])
  .then(finalStep)
  .commit()
```

**Rules:**
- All branch steps must share the same `inputSchema`
- All branch steps must share the same `outputSchema`
- Conditions are evaluated in order; first `true` wins
- Only one branch executes per run

**Output** — keyed by the executed branch step ID:

```typescript
// If first condition true:
{ "high-value-step": { result: "High: 15" } }
```

**Handling branches downstream** with optional fields:

```typescript
const finalStep = createStep({
  id: 'final',
  inputSchema: z.object({
    'high-value-step': z.object({ result: z.string() }).optional(),
    'low-value-step': z.object({ result: z.string() }).optional(),
  }),
  execute: async ({ inputData }) => {
    const result = inputData['high-value-step']?.result
      || inputData['low-value-step']?.result
    return { message: result }
  },
})
```

## Data Transform: .map()

Transform step outputs to match the next step's input schema:

```typescript
workflow
  .then(step1)
  .map(async ({ inputData }) => ({
    // Transform step1's output to step2's input shape
    bar: `transformed: ${inputData.foo}`,
  }))
  .then(step2)
  .commit()
```

### Map Helper Functions

```typescript
.map(async ({ inputData, getStepResult, getInitData }) => {
  // Access any previous step's result
  const step1Result = getStepResult('step-1')

  // Access workflow's initial input
  const initData = getInitData()

  return { combined: `${step1Result.value} + ${initData.original}` }
})
```

### Declarative Mapping with mapVariable

```typescript
.map(mapVariable({
  sourceStepId: 'step-1',
  sourceField: 'originalName',
  targetField: 'newName',
}))
```

## Do-Until Loop: .dountil()

Repeat a step until a condition becomes true. Executes at least once:

```typescript
const incrementStep = createStep({
  id: 'increment',
  inputSchema: z.object({ number: z.number() }),
  outputSchema: z.object({ number: z.number() }),
  execute: async ({ inputData }) => ({ number: inputData.number + 1 }),
})

workflow
  .then(initStep)
  .dountil(
    incrementStep,
    async ({ inputData }) => inputData.number > 10
  )
  .commit()
```

Each iteration receives the previous iteration's output.

## Do-While Loop: .dowhile()

Repeat a step while a condition remains true. Executes at least once:

```typescript
workflow
  .then(initStep)
  .dowhile(
    incrementStep,
    async ({ inputData }) => inputData.number < 10
  )
  .commit()
```

### Preventing Infinite Loops

Use `iterationCount` in the condition:

```typescript
.dountil(step, async ({ inputData, iterationCount }) => {
  if (iterationCount >= 100) {
    throw new Error('Maximum iterations reached')
  }
  return inputData.done === true
})
```

## Array Iteration: .foreach()

Apply the same step to each element in an array:

```typescript
const processItem = createStep({
  id: 'process-item',
  inputSchema: z.object({ value: z.number() }),
  outputSchema: z.object({ doubled: z.number() }),
  execute: async ({ inputData }) => ({ doubled: inputData.value * 2 }),
})

const workflow = createWorkflow({
  inputSchema: z.array(z.object({ value: z.number() })),
  outputSchema: z.array(z.object({ doubled: z.number() })),
})
  .foreach(processItem)
  .commit()
```

**Concurrency control:**

```typescript
// Sequential (default)
.foreach(processItem)

// Process 4 items simultaneously
.foreach(processItem, { concurrency: 4 })
```

**Aggregating results:**

```typescript
const aggregateStep = createStep({
  id: 'aggregate',
  inputSchema: z.array(z.object({ doubled: z.number() })),
  outputSchema: z.object({ total: z.number() }),
  execute: async ({ inputData }) => ({
    total: inputData.reduce((sum, item) => sum + item.doubled, 0),
  }),
})

workflow
  .foreach(processItem, { concurrency: 4 })
  .then(aggregateStep)  // Receives full array
  .commit()
```

**Flattening nested foreach:**

```typescript
workflow
  .foreach(chunkStep)
  .foreach(embedStep)
  .map(async ({ inputData }) => inputData.flat())
  .then(finalStep)
  .commit()
```

## Nested Workflows in Control Flow

Use sub-workflows inside `.foreach()` for multi-step processing per item:

```typescript
const processDoc = createWorkflow({
  id: 'process-doc',
  inputSchema: z.object({ url: z.string() }),
  outputSchema: z.object({ embeddings: z.array(z.number()) }),
})
  .then(downloadStep)
  .then(chunkStep)
  .then(embedStep)
  .commit()

const batchWorkflow = createWorkflow({
  id: 'batch',
  inputSchema: z.array(z.object({ url: z.string() })),
  outputSchema: z.array(z.object({ embeddings: z.array(z.number()) })),
})
  .foreach(processDoc, { concurrency: 3 })
  .commit()
```

Sub-workflows in `.parallel()`:

```typescript
workflow
  .parallel([pipelineA, pipelineB])
  .then(mergeStep)
  .commit()
```

## Pattern Selection Guide

| Method | Use When | Input → Output |
|--------|----------|---------------|
| `.then()` | Sequential processing | `T → U` |
| `.parallel()` | Different ops on same input | `T → { stepId: U }` |
| `.foreach()` | Same op on array items | `T[] → U[]` |
| `.branch()` | Conditional path selection | `T → { branchId: U }` |
| `.dountil()` | Repeat until condition true | `T → T` (same shape) |
| `.dowhile()` | Repeat while condition true | `T → T` (same shape) |
| `.map()` | Transform between steps | `T → U` (custom transform) |

**`.parallel()` vs `.foreach()`:**
- `.parallel()` — same input, different processing (fan-out/fan-in)
- `.foreach()` — different inputs, same processing (map-reduce)

## Pitfalls

1. **Parallel/foreach are synchronization barriers** — the next step waits for ALL branches/items to complete
2. **Branch conditions are evaluated in order** — the first `true` wins, so put the most specific condition first
3. **Loop conditions receive the step output** — make sure the condition checks the right field
4. **Foreach input must be an array** — use `.map()` to reshape if needed
5. **Nested foreach creates nested arrays** — flatten with `.map(({ inputData }) => inputData.flat())`
