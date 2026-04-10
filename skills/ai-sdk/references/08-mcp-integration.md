# MCP Integration

> Source: https://ai-sdk.dev/docs/ai-sdk-core/mcp

## Overview

Model Context Protocol (MCP) enables AI SDK to connect to external tool servers. MCP servers expose tools, resources, and prompts that your agents can use — without bundling the tool logic in your application. AI SDK v6 provides stable MCP support with HTTP transport, OAuth authentication, and elicitation.

## Creating an MCP Client

```typescript
import { createMCPClient } from 'ai';

const mcpClient = await createMCPClient({
  transport: {
    type: 'sse',
    url: 'http://localhost:3001/mcp',
  },
});

// Get tools from MCP server
const tools = await mcpClient.tools();
```

## Transport Types

### SSE (Server-Sent Events)

```typescript
const client = await createMCPClient({
  transport: {
    type: 'sse',
    url: 'https://mcp-server.example.com/sse',
    headers: {
      Authorization: 'Bearer my-token',
    },
  },
});
```

### HTTP (Streamable HTTP)

```typescript
const client = await createMCPClient({
  transport: {
    type: 'http',
    url: 'https://mcp-server.example.com/mcp',
    headers: {
      'X-API-Key': process.env.MCP_API_KEY,
    },
  },
});
```

### Stdio (Local Process)

```typescript
const client = await createMCPClient({
  transport: {
    type: 'stdio',
    command: 'npx',
    args: ['-y', '@mcp-server/filesystem'],
    env: { HOME: process.env.HOME },
  },
});
```

## Using MCP Tools with Agents

```typescript
import { createMCPClient, generateText } from 'ai';

const mcpClient = await createMCPClient({
  transport: { type: 'sse', url: 'http://localhost:3001/mcp' },
});

const mcpTools = await mcpClient.tools();

const { text } = await generateText({
  model: 'anthropic/claude-sonnet-4.5',
  tools: {
    ...mcpTools,
    // Mix with local tools
    myLocalTool: tool({ /* ... */ }),
  },
  maxSteps: 10,
  prompt: 'Use the available tools to help me.',
});

// Clean up when done
await mcpClient.close();
```

## With ToolLoopAgent

```typescript
import { ToolLoopAgent, createMCPClient } from 'ai';

const filesystemClient = await createMCPClient({
  transport: {
    type: 'stdio',
    command: 'npx',
    args: ['-y', '@mcp-server/filesystem', '/tmp/workspace'],
  },
});

const agent = new ToolLoopAgent({
  model: 'anthropic/claude-sonnet-4.5',
  tools: await filesystemClient.tools(),
  maxSteps: 20,
});

const { text } = await agent.generate({
  prompt: 'List all files in the workspace and summarize their contents.',
});

await filesystemClient.close();
```

## Multiple MCP Servers

```typescript
const [dbClient, searchClient, codeClient] = await Promise.all([
  createMCPClient({
    transport: { type: 'sse', url: 'http://localhost:3001/mcp' },
  }),
  createMCPClient({
    transport: { type: 'sse', url: 'http://localhost:3002/mcp' },
  }),
  createMCPClient({
    transport: { type: 'stdio', command: 'npx', args: ['-y', '@mcp-server/code'] },
  }),
]);

const allTools = {
  ...(await dbClient.tools()),
  ...(await searchClient.tools()),
  ...(await codeClient.tools()),
};

const { text } = await generateText({
  model: 'anthropic/claude-sonnet-4.5',
  tools: allTools,
  maxSteps: 15,
  prompt: 'Query the database and search for related docs.',
});

// Cleanup
await Promise.all([dbClient.close(), searchClient.close(), codeClient.close()]);
```

## OAuth Authentication

For MCP servers requiring OAuth:

```typescript
const client = await createMCPClient({
  transport: {
    type: 'http',
    url: 'https://secure-mcp.example.com/mcp',
  },
  auth: {
    type: 'oauth',
    clientId: process.env.MCP_CLIENT_ID,
    clientSecret: process.env.MCP_CLIENT_SECRET,
    tokenUrl: 'https://auth.example.com/oauth/token',
    scopes: ['tools:read', 'tools:execute'],
  },
});
```

### With PKCE Flow

```typescript
const client = await createMCPClient({
  transport: {
    type: 'http',
    url: 'https://secure-mcp.example.com/mcp',
  },
  auth: {
    type: 'oauth',
    clientId: process.env.MCP_CLIENT_ID,
    authorizationUrl: 'https://auth.example.com/authorize',
    tokenUrl: 'https://auth.example.com/token',
    pkce: true,
    redirectUri: 'http://localhost:3000/callback',
  },
});
```

## MCP Resources

Access server-exposed data resources:

```typescript
const client = await createMCPClient({
  transport: { type: 'sse', url: 'http://localhost:3001/mcp' },
});

// List available resources
const resources = await client.resources();
console.log(resources);
// [{ uri: 'file:///config.json', name: 'Config', mimeType: 'application/json' }]

// Read a resource
const content = await client.readResource('file:///config.json');
```

## MCP Prompts

Use server-defined prompt templates:

```typescript
const client = await createMCPClient({
  transport: { type: 'sse', url: 'http://localhost:3001/mcp' },
});

// List available prompts
const prompts = await client.prompts();
// [{ name: 'code-review', description: 'Review code for issues' }]

// Get a prompt with arguments
const prompt = await client.getPrompt('code-review', {
  language: 'typescript',
  focus: 'security',
});

// Use in generation
const { text } = await generateText({
  model: 'anthropic/claude-sonnet-4.5',
  messages: prompt.messages,
});
```

## Elicitation

MCP servers can request additional user input mid-operation:

```typescript
const client = await createMCPClient({
  transport: { type: 'sse', url: 'http://localhost:3001/mcp' },
  onElicitation: async (request) => {
    // Server is asking for user input
    console.log('Server asks:', request.message);
    // Return user's response
    return { response: await getUserInput(request.message) };
  },
});
```

## Error Handling

```typescript
import { createMCPClient, MCPClientError } from 'ai';

try {
  const client = await createMCPClient({
    transport: { type: 'sse', url: 'http://unreachable:3001/mcp' },
  });
} catch (error) {
  if (error instanceof MCPClientError) {
    console.error('MCP connection failed:', error.message);
    console.error('Transport:', error.transport);
  }
}

// Tool execution errors
const { text } = await generateText({
  model: 'anthropic/claude-sonnet-4.5',
  tools: await mcpClient.tools(),
  maxSteps: 5,
  prompt: 'Do something',
  onStepFinish: ({ toolResults }) => {
    for (const result of toolResults ?? []) {
      if (result.isError) {
        console.error(`Tool ${result.toolName} failed:`, result.result);
      }
    }
  },
});
```

## Lifecycle Management

```typescript
// In a long-running server, manage MCP client lifecycle
class MCPManager {
  private clients: Map<string, MCPClient> = new Map();

  async getClient(name: string, config: MCPConfig) {
    if (!this.clients.has(name)) {
      const client = await createMCPClient(config);
      this.clients.set(name, client);
    }
    return this.clients.get(name)!;
  }

  async closeAll() {
    await Promise.all(
      Array.from(this.clients.values()).map(c => c.close())
    );
    this.clients.clear();
  }
}
```

## Common Pitfalls

1. **Forgetting to close** — Always call `client.close()` to prevent resource leaks
2. **Tool name collisions** — Multiple MCP servers may expose same-named tools; namespace them
3. **Stdio in serverless** — Stdio transport spawns a process; doesn't work in serverless environments
4. **Auth token expiry** — Use OAuth with refresh tokens for long-lived connections
5. **Network timeouts** — Set appropriate timeouts for remote MCP servers

## Related Topics

- Tool calling → [04-tool-calling](04-tool-calling.md)
- Agents → [05-agents](05-agents.md)
- Deployment → [12-deployment-patterns](12-deployment-patterns.md)
