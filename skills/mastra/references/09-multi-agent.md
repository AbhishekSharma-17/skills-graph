# Mastra — Multi-Agent Systems

> Source: [mastra.ai/docs/agents/supervisor-agents](https://mastra.ai/docs/agents/supervisor-agents) · `@mastra/core` v1.37.x

## Table of Contents

- [Overview](#overview)
- [Supervisor Agents](#supervisor-agents)
- [Delegation Hooks](#delegation-hooks)
- [Message Filtering](#message-filtering)
- [Memory Isolation](#memory-isolation)
- [Iteration Monitoring](#iteration-monitoring)
- [Tool Approval Propagation](#tool-approval-propagation)
- [Task Completion Scoring](#task-completion-scoring)
- [Background Tasks](#background-tasks)
- [Agent Networks (Deprecated)](#agent-networks-deprecated)
- [Common Patterns](#common-patterns)
- [Pitfalls](#pitfalls)

## Overview

Multi-agent systems distribute tasks across specialized agents rather than overloading a single agent with many tools and complex instructions. Mastra's recommended approach is the **supervisor pattern**: a coordinator agent that delegates to specialized subagents.

## Supervisor Agents

A supervisor agent coordinates multiple subagents. It uses its instructions and each subagent's `description` to decide when and how to delegate:

```typescript
import { Agent } from '@mastra/core/agent'
import { Memory } from '@mastra/memory'

const researchAgent = new Agent({
  id: 'researcher',
  name: 'Research Agent',
  description: 'Gathers factual information and returns bullet-point summaries.',
  instructions: 'Search for accurate, up-to-date information. Return concise bullet points.',
  model: 'openai/gpt-5-mini',
  tools: { searchTool, scrapeTool },
})

const writerAgent = new Agent({
  id: 'writer',
  name: 'Writer Agent',
  description: 'Creates polished content from research summaries.',
  instructions: 'Write clear, engaging content. Use research findings as source material.',
  model: 'openai/gpt-5.4',
})

const supervisor = new Agent({
  id: 'supervisor',
  name: 'Content Supervisor',
  instructions: `You coordinate research and writing tasks.
1. First, delegate research to the researcher agent.
2. Then, pass research results to the writer agent.
3. Review the final output before returning.`,
  model: 'openai/gpt-5.4',
  agents: { researchAgent, writerAgent },
  memory: new Memory({ options: { lastMessages: 20 } }),
})
```

Subagents registered on the `agents` property are automatically converted to tools named `agent-<key>` (e.g., `agent-researchAgent`, `agent-writerAgent`).

## Delegation Hooks

### onDelegationStart

Intercept before delegation occurs:

```typescript
const supervisor = new Agent({
  id: 'supervisor',
  agents: { researcher, writer },
  onDelegationStart: async (context) => {
    // Modify the delegation prompt
    context.prompt = `[Priority: HIGH] ${context.prompt}`

    // Limit iterations
    context.maxIterations = 3

    // Or reject the delegation entirely
    // return { reject: true, reason: 'Not needed for this task' }
  },
})
```

### onDelegationComplete

Inspect results after delegation finishes:

```typescript
const supervisor = new Agent({
  id: 'supervisor',
  agents: { researcher, writer },
  onDelegationComplete: async (context) => {
    // Inspect the result
    console.log('Delegation result:', context.result)

    // Inject feedback
    context.feedback = 'Good work, but add more detail next time.'

    // Or stop execution entirely
    // context.bail('Result was unsatisfactory')
  },
})
```

## Message Filtering

Control what conversation history subagents receive:

```typescript
const supervisor = new Agent({
  id: 'supervisor',
  agents: { researcher, writer },
  messageFilter: ({ messages, primitiveId }) => {
    return messages
      .filter(msg => !msg.content.includes('confidential'))
      .slice(-10)  // Only last 10 messages
  },
})
```

## Memory Isolation

Mastra automatically isolates subagent memory:

- **Unique thread ID** per delegation — subagents get clean message history
- **Deterministic resource ID** — `{parentResourceId}-{agentName}` — persists across delegations
- Subagents receive full conversation context for decision-making, but only their specific delegation prompt and response are saved to their memory

This prevents cross-contamination between unrelated delegations while maintaining continuity for repeated delegations to the same subagent.

## Iteration Monitoring

Track progress after each supervisor loop iteration:

```typescript
const supervisor = new Agent({
  id: 'supervisor',
  agents: { researcher, writer },
  onIterationComplete: async (context) => {
    // Check iteration progress
    if (context.text.length > 5000) {
      return { continue: false }  // Stop iterating
    }

    // Inject feedback for next iteration
    return {
      continue: true,
      feedback: 'Keep going, need more detail.',
    }
  },
})
```

## Tool Approval Propagation

When subagent tools have `requireApproval: true`, approval requests propagate up through the delegation chain to the supervisor's stream:

```typescript
const stream = await supervisor.stream('Delete inactive users')

for await (const event of stream.fullStream) {
  if (event.type === 'tool-approval-request') {
    console.log(`Tool: ${event.toolName}, Args: ${event.args}`)
    await event.approve()  // or event.reject()
  }
}
```

## Task Completion Scoring

Use scorers to validate task completion after each iteration:

```typescript
const supervisor = new Agent({
  id: 'supervisor',
  agents: { researcher, writer },
  scorers: {
    completeness: {
      scorer: createCompletenessScorer({ model: 'openai/gpt-5-mini' }),
      threshold: 0.8,  // Must score above 0.8 to stop iterating
    },
  },
})
```

Failed validations trigger continued iterations with scorer feedback injected into context.

## Background Tasks

Run subagent delegations as background tasks:

```typescript
const supervisor = new Agent({
  id: 'supervisor',
  agents: { researcher, writer },
  backgroundTasks: {
    tools: {
      researchAgent: { enabled: true, timeoutMs: 900_000 },  // 15 min timeout
    },
  },
})

// Stream until all background tasks complete
const stream = await supervisor.stream('Research and write about AI trends')
const result = await stream.streamUntilIdle()
```

## Agent Networks (Deprecated)

Agent networks are deprecated in favor of supervisor agents. The migration path:

```typescript
// OLD (deprecated)
const result = await agent.network('research this topic', {
  agents: { researcher, writer },
})

// NEW (recommended)
const supervisor = new Agent({
  id: 'supervisor',
  agents: { researcher, writer },
  instructions: 'Coordinate research and writing.',
})
const result = await supervisor.generate('research this topic')
```

## Common Patterns

### Specialist Team

```typescript
const codeAgent = new Agent({
  id: 'coder',
  description: 'Writes TypeScript code. Returns code blocks.',
  model: 'anthropic/claude-sonnet-4-5-20250514',
  tools: { fileTool },
})

const reviewAgent = new Agent({
  id: 'reviewer',
  description: 'Reviews code for bugs and best practices. Returns feedback.',
  model: 'openai/gpt-5.4',
})

const testAgent = new Agent({
  id: 'tester',
  description: 'Writes unit tests for TypeScript code.',
  model: 'openai/gpt-5-mini',
  tools: { testRunnerTool },
})

const leadAgent = new Agent({
  id: 'lead',
  instructions: `You are a tech lead. For feature requests:
1. Have the coder write the implementation
2. Have the reviewer check it
3. Have the tester write tests
4. Return the final approved code.`,
  model: 'openai/gpt-5.4',
  agents: { codeAgent, reviewAgent, testAgent },
})
```

### Parallel Research and Synthesis

```typescript
const supervisor = new Agent({
  id: 'research-supervisor',
  instructions: `For broad research topics:
1. Delegate to all relevant specialist agents in parallel
2. Synthesize their findings into a cohesive report`,
  model: 'openai/gpt-5.4',
  agents: { marketAgent, techAgent, complianceAgent },
})
```

## Pitfalls

1. **Write clear subagent descriptions** — the supervisor uses `description` (not `instructions`) to decide delegation
2. **Don't create deep delegation chains** — keep delegation to 2-3 levels maximum
3. **Use memory with supervisors** — memory is required for task tracking and completion detection
4. **Match model to role** — use cheaper models for simple subagents, powerful models for the supervisor
5. **Background tasks need storage** — state must persist across async boundaries
6. **Avoid circular delegations** — agent A delegating to agent B which delegates back to A
