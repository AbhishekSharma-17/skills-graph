# Claude Agent SDK — Overview & Quickstart

> Source: [platform.claude.com/docs/en/agent-sdk](https://platform.claude.com/docs/en/agent-sdk/overview) — Python v0.1.51, TypeScript v0.2.86

## Contents

- [What Is the Claude Agent SDK](#what-is-the-claude-agent-sdk)
- [Agent SDK vs Anthropic Client SDK](#agent-sdk-vs-anthropic-client-sdk)
- [Architecture: The Agent Loop](#architecture-the-agent-loop)
- [Installation](#installation)
- [Authentication](#authentication)
- [Quickstart: Python](#quickstart-python)
- [Quickstart: TypeScript](#quickstart-typescript)
- [Message Types](#message-types)
- [Processing Results](#processing-results)
- [Common Patterns](#common-patterns)
- [Key Gotchas](#key-gotchas)

## What Is the Claude Agent SDK

The Claude Agent SDK is a dedicated library for building AI agents that autonomously read files, run commands, search the web, edit code, and more. It provides the same tools, agent loop, and context management that power Claude Code, but as a programmable SDK available in both Python and TypeScript.

| Feature | Description |
|---------|-------------|
| **Agent Loop** | Claude evaluates, calls tools, processes results, repeats until done |
| **Built-in Tools** | Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch, and more |
| **Custom Tools** | Define tools as Python/TypeScript functions via in-process MCP servers |
| **MCP Integration** | Connect to external MCP servers (stdio, HTTP, SSE) |
| **Hooks** | Intercept and modify tool execution at key lifecycle points |
| **Permissions** | Fine-grained control over what tools agents can use |
| **Sessions** | Multi-turn conversations with persistence and resume |
| **Subagents** | Spawn specialized agents for focused subtasks |
| **Structured Outputs** | Get typed JSON results via JSON Schema |

## Agent SDK vs Anthropic Client SDK

| Aspect | Anthropic Client SDK | Claude Agent SDK |
|--------|---------------------|-----------------|
| Package | `anthropic` / `@anthropic-ai/sdk` | `claude-agent-sdk` / `@anthropic-ai/claude-agent-sdk` |
| Tool Loop | You implement the loop yourself | SDK manages the loop autonomously |
| Built-in Tools | None — you define all tools | File ops, Bash, search, web, and more |
| Context Management | Manual | Automatic compaction and session handling |
| Use Case | Custom LLM integrations | Autonomous coding/task agents |

**Use the Agent SDK when** you want Claude to autonomously execute multi-step tasks with file system access, command execution, and web capabilities. Use the Client SDK when you need fine-grained control over every API call.

## Architecture: The Agent Loop

```
User Prompt
    │
    v
┌─────────────────────────────────┐
│  1. Claude receives prompt       │
│     (yields SystemMessage init)  │
│                                  │
│  2. Claude evaluates & responds  │
│     (yields AssistantMessage)    │
│                                  │
│  3. SDK executes requested tools │
│     (tool results feed back)     │
│                                  │
│  4. Claude sees results, decides │
│     next action                  │
│                                  │
│  5. Repeat until no tool calls   │
│     (yields final result)        │
└─────────────────────────────────┘
    │
    v
ResultMessage (with session_id, cost, usage)
```

The SDK operates as a **long-running process** — it maintains a persistent shell, manages file operations within a working directory, and carries context from previous interactions within a session.

## Installation

### Python

```bash
pip install claude-agent-sdk
# Requires Python 3.10+
# Bundles Claude Code CLI automatically
```

### TypeScript

```bash
npm install @anthropic-ai/claude-agent-sdk
# Requires Node.js 18+
```

## Authentication

Set `ANTHROPIC_API_KEY` as an environment variable (primary method):

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Alternative Providers

| Provider | Environment Variable | Value |
|----------|---------------------|-------|
| Amazon Bedrock | `CLAUDE_CODE_USE_BEDROCK` | `1` |
| Google Vertex AI | `CLAUDE_CODE_USE_VERTEX` | `1` |
| Microsoft Azure AI Foundry | `CLAUDE_CODE_USE_FOUNDRY` | `1` |

Each provider requires additional credentials configured in their respective SDKs.

## Quickstart: Python

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    options = ClaudeAgentOptions(
        permission_mode="bypassPermissions",  # For trusted environments
        max_turns=10,
    )

    async for message in query(prompt="Create a hello.py file that prints hello world", options=options):
        if message.type == "assistant":
            for block in message.content:
                if hasattr(block, "text"):
                    print(block.text)
        elif message.type == "result":
            print(f"\nDone! Cost: ${message.total_cost_usd:.4f}")
            print(f"Session: {message.session_id}")

asyncio.run(main())
```

## Quickstart: TypeScript

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

const conversation = query({
  prompt: "Create a hello.ts file that prints hello world",
  options: {
    permissionMode: "bypassPermissions",
    maxTurns: 10,
  },
});

for await (const message of conversation) {
  if (message.type === "assistant") {
    for (const block of message.content) {
      if ("text" in block) {
        console.log(block.text);
      }
    }
  } else if (message.type === "result") {
    console.log(`\nDone! Cost: $${message.total_cost_usd.toFixed(4)}`);
    console.log(`Session: ${message.session_id}`);
  }
}
```

## Message Types

The `query()` function yields messages as an async iterator. Key message types:

| Type | Description | Key Fields |
|------|-------------|------------|
| `SystemMessage` | Initialization info | `subtype: "init"`, `mcp_servers`, `session_id` |
| `AssistantMessage` | Claude's response with text and/or tool calls | `content[]` (text blocks, tool_use blocks) |
| `ResultMessage` | Final result when agent completes | `subtype`, `duration_ms`, `total_cost_usd`, `usage`, `session_id` |

### Result Subtypes

| Subtype | Meaning |
|---------|---------|
| `success` | Agent completed normally |
| `error_max_turns` | Hit the `max_turns` limit |
| `error_max_budget_usd` | Hit the `max_budget_usd` limit |
| `error_during_execution` | Tool execution error |
| `error_max_structured_output_retries` | Structured output validation failed repeatedly |

## Processing Results

### Python

```python
async for message in query(prompt="...", options=options):
    match message.type:
        case "system":
            if message.subtype == "init":
                print(f"Session started: {message.session_id}")
        case "assistant":
            for block in message.content:
                if hasattr(block, "text"):
                    print(block.text)
                elif block.type == "tool_use":
                    print(f"Tool: {block.name}({block.input})")
        case "result":
            if message.subtype == "success":
                print(f"Completed in {message.duration_ms}ms")
                print(f"Cost: ${message.total_cost_usd:.4f}")
```

### TypeScript

```typescript
for await (const message of conversation) {
  switch (message.type) {
    case "system":
      if (message.subtype === "init") {
        console.log(`Session: ${message.session_id}`);
      }
      break;
    case "assistant":
      for (const block of message.content) {
        if ("text" in block) console.log(block.text);
        if (block.type === "tool_use") console.log(`Tool: ${block.name}`);
      }
      break;
    case "result":
      console.log(`Cost: $${message.total_cost_usd}`);
      break;
  }
}
```

## Common Patterns

### Scoped Agent with Budget

```python
options = ClaudeAgentOptions(
    max_turns=20,
    max_budget_usd=0.50,
    permission_mode="acceptEdits",
    cwd="/path/to/project",
)
```

### Streaming with Partial Messages

```python
options = ClaudeAgentOptions(
    include_partial_messages=True,  # Get incremental text chunks
)
async for message in query(prompt="...", options=options):
    if message.type == "assistant" and hasattr(message, "partial"):
        print(message.content[-1].text, end="", flush=True)
```

### Environment Variables

```python
options = ClaudeAgentOptions(
    env={"DATABASE_URL": "postgres://...", "NODE_ENV": "production"},
)
```

## Key Gotchas

1. **`query()` is async** — always use `async for` (Python) or `for await` (TypeScript)
2. **CLI bundled** — the Python SDK bundles the Claude Code CLI binary; no separate install needed
3. **Working directory matters** — tools operate relative to `cwd` (defaults to current directory)
4. **Cost adds up** — always set `max_budget_usd` in production to prevent runaway costs
5. **Compaction** — when context approaches limits, older history is automatically summarized; put persistent instructions in system prompt or CLAUDE.md, not the initial prompt
6. **Sessions are local** — stored on disk at `~/.claude/projects/<encoded-cwd>/`; the `cwd` must match when resuming

## Related Topics

- [Configuration](01-configuration.md) — All options for `ClaudeAgentOptions`
- [Built-in Tools](02-built-in-tools.md) — Available tools and how to control them
- [Deployment](10-deployment.md) — Production deployment patterns
