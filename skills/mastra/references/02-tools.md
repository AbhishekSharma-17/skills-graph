# Mastra — Tools

> Source: [mastra.ai/docs/agents/using-tools](https://mastra.ai/docs/agents/using-tools-and-mcp) · `@mastra/core` v1.37.x

## Table of Contents

- [Overview](#overview)
- [Creating Tools](#creating-tools)
- [Schema Libraries](#schema-libraries)
- [Tool Execution](#tool-execution)
- [Attaching Tools to Agents](#attaching-tools-to-agents)
- [Runtime Tool Control](#runtime-tool-control)
- [Output Shaping](#output-shaping)
- [Transform for UI](#transform-for-ui)
- [MCP Server Integration](#mcp-server-integration)
- [Composite Tool Types](#composite-tool-types)
- [Common Patterns](#common-patterns)
- [Pitfalls](#pitfalls)

## Overview

Tools extend agents with the ability to call external APIs, run computations, access databases, or perform any operation the LLM cannot do natively. Every tool is a typed function with validated input/output schemas.

## Creating Tools

```typescript
import { createTool } from '@mastra/core/tools'
import { z } from 'zod'

export const weatherTool = createTool({
  id: 'get-weather',
  description: 'Get current weather for a location',
  inputSchema: z.object({
    city: z.string().describe('City name'),
    units: z.enum(['celsius', 'fahrenheit']).default('celsius'),
  }),
  outputSchema: z.object({
    temperature: z.number(),
    condition: z.string(),
    humidity: z.number(),
  }),
  execute: async ({ city, units }) => {
    const response = await fetch(`https://wttr.in/${city}?format=j1`)
    const data = await response.json()
    return {
      temperature: units === 'celsius' ? data.temp_C : data.temp_F,
      condition: data.weatherDesc,
      humidity: data.humidity,
    }
  },
})
```

### Tool Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | `string` | Yes | Unique identifier |
| `description` | `string` | Yes | What the tool does (shown to LLM) |
| `inputSchema` | `Schema` | Yes | Input validation schema |
| `outputSchema` | `Schema` | No | Output type schema |
| `execute` | `async (input) => output` | Yes | Tool implementation |
| `toModelOutput` | `(result) => any` | No | Shape result for LLM context |
| `transform` | `(result, target) => any` | No | Shape result for UI/transcript |

## Schema Libraries

Mastra supports any schema compliant with Standard JSON Schema:

```typescript
// Zod (recommended)
inputSchema: z.object({ query: z.string() })

// Valibot
import { toStandardJsonSchema } from '@valibot/to-standard-json-schema'
inputSchema: toStandardJsonSchema(v.object({ query: v.string() }))

// ArkType
import { type } from 'arktype'
inputSchema: type({ query: 'string' })
```

## Tool Execution

The `execute` function receives the validated input and returns the output:

```typescript
execute: async ({ city, units }) => {
  // Access external APIs
  const data = await fetchWeather(city)

  // Run computations
  const temp = units === 'celsius' ? data.temp_C : data.temp_F

  // Return typed output
  return { temperature: temp, condition: data.desc, humidity: data.humidity }
}
```

The execute function can call any async operation: HTTP requests, database queries, file operations, other tools, or even other agents.

## Attaching Tools to Agents

```typescript
import { Agent } from '@mastra/core/agent'
import { weatherTool, searchTool, calcTool } from './tools'

const agent = new Agent({
  id: 'multi-tool-agent',
  name: 'Multi-Tool Agent',
  instructions: `You have access to weather, search, and calculator tools.
Use the appropriate tool based on the user's question.`,
  model: 'openai/gpt-5.4',
  tools: { weatherTool, searchTool, calcTool },
})
```

The tool name exposed to the LLM comes from the object key, not the `id` property. `{ weatherTool }` produces `toolName: "weatherTool"` in responses.

## Runtime Tool Control

Restrict which tools are available per request:

```typescript
// Only allow specific tools
await agent.generate('Check the weather in Paris', {
  activeTools: ['weatherTool'],
})

// Force tool use
await agent.generate('What is 2 + 2?', {
  toolChoice: 'required',
})

// Prevent tool use
await agent.generate('Just answer from memory', {
  toolChoice: 'none',
})

// Force a specific tool
await agent.generate('Look up the weather', {
  toolChoice: { type: 'tool', toolName: 'weatherTool' },
})
```

## Output Shaping

### toModelOutput

Transform rich results into smaller representations the model receives, keeping context window efficient:

```typescript
const dbTool = createTool({
  id: 'query-db',
  description: 'Query the database',
  inputSchema: z.object({ sql: z.string() }),
  outputSchema: z.object({ rows: z.array(z.any()), count: z.number() }),
  execute: async ({ sql }) => {
    const rows = await db.query(sql)
    return { rows, count: rows.length }
  },
  toModelOutput: (result) => {
    // Only send summary to model, not full rows
    return { count: result.count, preview: result.rows.slice(0, 3) }
  },
})
```

The full result is still available in `toolResults` — `toModelOutput` only affects what the LLM sees.

## Transform for UI

Shape results differently for display and transcript targets:

```typescript
const searchTool = createTool({
  id: 'search',
  description: 'Search the web',
  inputSchema: z.object({ query: z.string() }),
  outputSchema: z.object({ results: z.array(z.object({ title: z.string(), url: z.string() })) }),
  execute: async ({ query }) => { /* ... */ },
  transform: (result, { target }) => {
    if (target === 'display') {
      return result.results.map(r => `[${r.title}](${r.url})`).join('\n')
    }
    return result  // 'transcript' gets the full object
  },
})
```

## MCP Server Integration

Connect to Model Context Protocol servers for remote tools:

```typescript
import { MCPClient } from '@mastra/mcp'

const mcpClient = new MCPClient({
  servers: {
    github: {
      command: 'npx',
      args: ['-y', '@modelcontextprotocol/server-github'],
      env: { GITHUB_TOKEN: process.env.GITHUB_TOKEN },
    },
    filesystem: {
      command: 'npx',
      args: ['-y', '@modelcontextprotocol/server-filesystem', '/workspace'],
    },
  },
})

// Get tools from MCP servers
const mcpTools = await mcpClient.getTools()

const agent = new Agent({
  id: 'mcp-agent',
  name: 'MCP Agent',
  instructions: 'You can interact with GitHub and the filesystem.',
  model: 'openai/gpt-5.4',
  tools: { ...mcpTools },
})
```

### Authoring MCP Servers

Mastra can also serve your tools as an MCP server:

```bash
npx mastra build --mcp
```

This exposes registered tools via the MCP protocol.

## Composite Tool Types

### Agents as Tools (Supervisor Pattern)

Subagents registered on a supervisor are automatically converted to tools named `agent-<key>`:

```typescript
const supervisor = new Agent({
  id: 'supervisor',
  agents: { researcher, writer },  // Become tools: agent-researcher, agent-writer
})
```

### Workflows as Tools

Workflows can be used as agent tools named `workflow-<key>`:

```typescript
const agent = new Agent({
  id: 'workflow-agent',
  tools: { myWorkflow },  // Becomes tool: workflow-myWorkflow
})
```

The workflow's `inputSchema` and `outputSchema` are used for tool validation.

## Common Patterns

### Tool with Database Access

```typescript
const queryTool = createTool({
  id: 'query-users',
  description: 'Search users by name or email',
  inputSchema: z.object({
    query: z.string(),
    limit: z.number().default(10),
  }),
  outputSchema: z.object({
    users: z.array(z.object({ id: z.string(), name: z.string(), email: z.string() })),
  }),
  execute: async ({ query, limit }) => {
    const users = await db.user.findMany({
      where: { OR: [{ name: { contains: query } }, { email: { contains: query } }] },
      take: limit,
    })
    return { users }
  },
})
```

### Tool Requiring Approval

```typescript
const deleteUserTool = createTool({
  id: 'delete-user',
  description: 'Permanently delete a user account',
  inputSchema: z.object({ userId: z.string() }),
  outputSchema: z.object({ deleted: z.boolean() }),
  requireApproval: true,
  execute: async ({ userId }) => {
    await db.user.delete({ where: { id: userId } })
    return { deleted: true }
  },
})
```

## Pitfalls

1. **Write clear descriptions** — the LLM uses `description` to decide when to call a tool. Vague descriptions lead to incorrect tool selection
2. **Tool name = object key** — `{ fetchWeather: weatherTool }` means the LLM sees `fetchWeather`, not the tool's `id`
3. **Handle errors in execute** — uncaught errors crash the agent loop. Wrap external calls in try/catch
4. **Use `toModelOutput`** for large results — sending 1000 database rows to the LLM wastes context and increases cost
5. **Validate external data** — don't trust API responses blindly; the `outputSchema` validates your return value
