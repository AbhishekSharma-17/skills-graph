---
name: claude-agent-sdk
description: "Build AI agents programmatically with the Claude Agent SDK (Python and TypeScript). Provides the same tools, agent loop, and context management that power Claude Code, but as a library. MANDATORY TRIGGERS: claude-agent-sdk, claude agent sdk, claude_agent_sdk, @anthropic-ai/claude-agent-sdk, ClaudeAgentOptions, ClaudeSDKClient. Also trigger when user wants to build AI agents with Claude programmatically, create agent loops with tools, use Claude Code SDK, orchestrate subagents, or deploy autonomous coding agents. When in doubt about whether to use this skill for agent SDK tasks, use it."
license: MIT
metadata:
  version: "1.5.0"
  author: Abhishek Sharma
  tags: ["claude", "agent-sdk", "ai-agents", "anthropic", "tools", "mcp", "python", "claude-sdk"]
---

# Claude Agent SDK — Skill Router

> Build and deploy AI agents with the same tools, agent loop, and context management that power Claude Code.

**Source:** [platform.claude.com/docs](https://platform.claude.com/docs/en/agent-sdk/overview) | **Python:** `claude-agent-sdk` v0.1.51 | **TypeScript:** `@anthropic-ai/claude-agent-sdk` v0.2.86

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Quickstart** | `references/00-overview.md` | Getting started, installation, architecture, authentication, first agent |
| **Configuration** | `references/01-configuration.md` | ClaudeAgentOptions, model selection, effort, thinking, environment variables |
| **Built-in Tools** | `references/02-built-in-tools.md` | All 17+ built-in tools with params, when-to-use, Claude call JSON examples, cost/perf, decision tree, common patterns |
| **Custom Tools** | `references/03-custom-tools.md` | @tool decorator, tool() function, naming convention (`mcp__server__name`), input schemas, return types, annotations, complete end-to-end example |
| **MCP Integration** | `references/04-mcp-integration.md` | MCP servers, stdio/HTTP/SSE/SDK transports, .mcp.json, tool naming |
| **Hooks** | `references/05-hooks.md` | PreToolUse, PostToolUse, hook matchers, callbacks, async hooks |
| **Permissions** | `references/06-permissions.md` | Permission modes, canUseTool, evaluation order, security |
| **Sessions** | `references/07-sessions.md` | Multi-turn, ClaudeSDKClient, resume, fork, session management |
| **Subagents** | `references/08-subagents.md` | AgentDefinition, spawning, model selection, tool scoping, limitations |
| **Structured Outputs** | `references/09-structured-outputs.md` | output_format, JSON Schema, Pydantic, Zod, validation |
| **Deployment** | `references/10-deployment.md` | System requirements, deployment patterns, sandboxes, cost, security |
| **Streaming** | `references/11-streaming.md` | StreamEvent, partial messages, streaming vs single mode, building UIs |
| **User Input** | `references/12-user-input.md` | AskUserQuestion, approval flows, canUseTool, option previews |
| **Agent Loop & Errors** | `references/13-agent-loop.md` | Turns, compaction, stop reasons, error types, rate limits, cost tracking |
| **System Prompts & Features** | `references/14-system-prompts-features.md` | CLAUDE.md, skills, plugins, slash commands, output styles |
| **Secure Deployment** | `references/15-secure-deployment.md` | Docker hardening, credential management, proxies, isolation |
| **query() & Messages** | `references/16-query-and-messages.md` | query() function signature, AssistantMessage/ResultMessage dataclass fields, TextBlock/ToolUseBlock/ThinkingBlock, all message types, 7 patterns, permission priority, minimum viable options |
| **ClaudeSDKClient** | `references/17-client.md` | Stateful multi-turn client, constructor, lifecycle, all 14 methods with params/examples/when-to-use, ClaudeSDKClient-only features, 8 patterns, typical usage flow, minimum viable client |
| **ClaudeAgentOptions** | `references/18-claude-agent-options.md` | All 38 parameters with type/default/when-to-use/when-not-to-use/example, provider env vars, permission mode table, TypeScript name mapping, TypeScript-only params, decision matrix for 7 use cases |
| **Transport** | `references/19-transport.md` | Communication pipe architecture, SubprocessCLITransport internals, Transport ABC (6 methods), JSON-Lines wire protocol, when to use custom transport, 5 use cases (Mock/WebSocket/SSH/HTTP/MessageQueue), step-by-step build guide |
| **Middleware & Proxy** | `references/20-middleware.md` | 3-layer model (Transport/Hooks/can_use_tool), decision matrix, 9 use cases with full code (audit logging, security filtering, cost tracking, metrics, input transformation, rate limiting, caching, auth/multi-tenancy, token counting), composition patterns, hooks return cheat sheet, all 10 hook events table, can_use_tool unique powers |

## Installation

```bash
# Python
pip install 

uv add claude-agent-sdk

# TypeScript
npm install @anthropic-ai/claude-agent-sdk
```

## Quick Reference

- **Docs:** https://platform.claude.com/docs/en/agent-sdk/overview
- **GitHub (Python):** https://github.com/anthropics/claude-agent-sdk-python
- **GitHub (TypeScript):** https://github.com/anthropics/claude-agent-sdk-typescript
- **PyPI:** https://pypi.org/project/claude-agent-sdk/
- **npm:** https://www.npmjs.com/package/@anthropic-ai/claude-agent-sdk
