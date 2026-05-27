# Mastra — Suspend & Resume

> Source: [mastra.ai/docs/workflows/suspend-and-resume](https://mastra.ai/docs/workflows/suspend-and-resume) · `@mastra/core` v1.37.x

## Table of Contents

- [Overview](#overview)
- [Suspending a Workflow](#suspending-a-workflow)
- [Resuming a Workflow](#resuming-a-workflow)
- [Suspend and Resume Schemas](#suspend-and-resume-schemas)
- [Identifying Suspended Runs](#identifying-suspended-runs)
- [Recovering Suspended Runs](#recovering-suspended-runs)
- [Sleep Methods](#sleep-methods)
- [Restarting Active Runs](#restarting-active-runs)
- [Human-in-the-Loop Patterns](#human-in-the-loop-patterns)
- [Pitfalls](#pitfalls)

## Overview

Workflows can be paused mid-execution to collect additional data, wait for API callbacks, throttle costly operations, or request human-in-the-loop input. The execution state is preserved as a snapshot in your storage provider, enabling resumption from the exact point of pause.

## Suspending a Workflow

Call `suspend()` inside a step's `execute` function:

```typescript
const approvalStep = createStep({
  id: 'approval',
  inputSchema: z.object({ amount: z.number() }),
  outputSchema: z.object({ approved: z.boolean(), amount: z.number() }),
  execute: async ({ inputData, resumeData, suspend }) => {
    // Check if we have resume data from a previous resume
    const { approved } = resumeData ?? {}

    if (!approved) {
      // Suspend and wait for human input
      return await suspend({ reason: `Approve payment of $${inputData.amount}?` })
    }

    // Continue after approval
    return { approved: true, amount: inputData.amount }
  },
})
```

The pattern: check `resumeData` first. If absent (first execution), `suspend()`. On resume, `resumeData` contains the data passed in `resume()`.

## Resuming a Workflow

Pass matching data via `resume()`:

```typescript
// Start the workflow
const run = await workflow.createRun()
const result = await run.start({ inputData: { amount: 500 } })

// Result is suspended
if (result.status === 'suspended') {
  console.log('Suspended at:', result.suspended) // Step paths

  // Resume with approval data
  const finalResult = await run.resume({
    step: approvalStep,               // Type-safe step reference
    resumeData: { approved: true },   // Must match resumeSchema
  })

  console.log(finalResult.result) // { approved: true, amount: 500 }
}
```

### Resume Targets

```typescript
// By step object (type-safe, recommended)
await run.resume({ step: approvalStep, resumeData: { approved: true } })

// By step ID string
await run.resume({ step: 'approval', resumeData: { approved: true } })

// Resume last suspended step (omit step)
await run.resume({ resumeData: { approved: true } })
```

## Suspend and Resume Schemas

Define explicit schemas for suspend/resume operations:

```typescript
const approvalStep = createStep({
  id: 'approval',
  inputSchema: z.object({ amount: z.number(), description: z.string() }),
  outputSchema: z.object({ approved: z.boolean(), amount: z.number() }),
  suspendSchema: z.object({
    reason: z.string(),
    requestDetails: z.string(),
  }),
  resumeSchema: z.object({
    approved: z.boolean(),
    reviewerNote: z.string().optional(),
  }),
  execute: async ({ inputData, resumeData, suspend }) => {
    if (!resumeData?.approved) {
      return await suspend({
        reason: 'Payment requires approval',
        requestDetails: `$${inputData.amount} for ${inputData.description}`,
      })
    }
    return { approved: true, amount: inputData.amount }
  },
})
```

Access suspend context via `suspendData` during resume to understand why the pause occurred.

## Identifying Suspended Runs

```typescript
const result = await run.start({ inputData })

if (result.status === 'suspended') {
  // Array of suspended step/workflow paths
  console.log(result.suspended)
  // e.g., [['approval']] or [['inner-workflow', 'review-step']]
}
```

## Recovering Suspended Runs

Use `createWorkflowStateReader()` to retrieve suspended runs from storage:

```typescript
import { createWorkflowStateReader } from '@mastra/core/workflows'

const reader = createWorkflowStateReader(result.state)

// Get the suspended step info
const suspendedStep = reader.getSuspendedStep()

// Get labels for resume buttons
const approveLabel = reader.getResumeLabel('approve')
```

### Listing Active Runs

```typescript
// Find all running or waiting workflow runs
const activeRuns = await mastra.listActiveWorkflowRuns('my-workflow')
// Returns runs with status 'running' or 'waiting'
```

## Sleep Methods

Sleep pauses the workflow at the workflow level (status = `waiting`), unlike `suspend()` which pauses at the step level (status = `suspended`):

### Timed Sleep

```typescript
workflow
  .then(step1)
  .sleep(5000)       // Pause 5 seconds
  .then(step2)
  .commit()
```

### Sleep Until Date

```typescript
workflow
  .then(step1)
  .sleepUntil(new Date('2026-06-01T00:00:00Z'))
  .then(step2)
  .commit()
```

## Restarting Active Runs

```typescript
// Restart a specific run from the last active step
await run.restart()

// Restart all active runs of a workflow
await myWorkflow.restartAllActiveWorkflowRuns()
```

## Human-in-the-Loop Patterns

### Approval Gate

```typescript
const reviewStep = createStep({
  id: 'review',
  inputSchema: z.object({ content: z.string(), author: z.string() }),
  outputSchema: z.object({ content: z.string(), status: z.string() }),
  resumeSchema: z.object({
    approved: z.boolean(),
    feedback: z.string().optional(),
  }),
  execute: async ({ inputData, resumeData, suspend }) => {
    if (!resumeData) {
      return await suspend({
        content: inputData.content,
        author: inputData.author,
      })
    }
    if (!resumeData.approved) {
      return { content: inputData.content, status: 'rejected' }
    }
    return { content: inputData.content, status: 'approved' }
  },
})
```

### Multi-Step Approval Chain

```typescript
const workflow = createWorkflow({
  id: 'multi-approval',
  inputSchema: z.object({ proposal: z.string() }),
  outputSchema: z.object({ status: z.string() }),
})
  .then(managerReviewStep)    // First approval gate
  .then(directorReviewStep)   // Second approval gate
  .then(publishStep)
  .commit()
```

Each step can independently suspend and resume, with state preserved between suspensions.

### HTTP Endpoint Resume

```typescript
// In your API route
app.post('/api/approve/:runId', async (req, res) => {
  const { runId } = req.params
  const { approved, note } = req.body

  const workflow = mastra.getWorkflow('approval-workflow')
  const run = await workflow.getRun(runId)

  const result = await run.resume({
    step: 'review',
    resumeData: { approved, reviewerNote: note },
  })

  res.json({ status: result.status })
})
```

## Pitfalls

1. **Always check `resumeData` before suspending** — the execute function runs both on initial execution and after resume
2. **Storage is required** — suspend/resume persists state to your storage provider. Configure `LibSQLStore` or similar
3. **Sleep vs Suspend** — `sleep()` is time-based (status: `waiting`), `suspend()` is data-based (status: `suspended`)
4. **Resume data must match `resumeSchema`** — type mismatches cause runtime errors
5. **Nested workflow suspensions** — when a sub-workflow suspends, the parent's `suspended` array contains the full path (e.g., `['inner-workflow', 'review-step']`)
