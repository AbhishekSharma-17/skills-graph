---
name: openai-agents-sdk
description: "OpenAI Agents SDK for building multi-agent workflows with tools, handoffs, guardrails, streaming, MCP, sessions, and tracing. MANDATORY TRIGGERS: openai-agents, openai agents sdk, openai-agents-python, openai agents, Runner.run, function_tool, handoff, guardrail, MCPServerStdio, MCPServerStreamableHttp, HostedMCPTool, RunContextWrapper, AgentHooks. Also trigger when user wants to build multi-agent systems with OpenAI models, create agent orchestration with handoffs, add guardrails to LLM applications, integrate MCP servers with agents, implement streaming agent responses, or use OpenAI's official agent framework. When in doubt about whether to use this skill for OpenAI agent tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["openai", "agents", "multi-agent", "tools", "handoffs", "guardrails", "mcp", "tracing", "streaming", "python"]
---

# OpenAI Agents SDK — Skill Router

> Lightweight, powerful framework for building multi-agent workflows with tools, handoffs, guardrails, and tracing.

**Source:** [openai.github.io/openai-agents-python](https://openai.github.io/openai-agents-python/) | **Package:** `openai-agents` v0.17.x | **License:** MIT

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Setup** | `references/00-overview.md` | Getting started, installation, quickstart, architecture |
| **Agents** | `references/01-agents.md` | Agent creation, instructions, output types, hooks, cloning |
| **Tools** | `references/02-tools.md` | Function tools, hosted tools, tool search, agents as tools |
| **Running Agents** | `references/03-running-agents.md` | Runner.run, RunConfig, input management, error handling |
| **Handoffs** | `references/04-handoffs.md` | Agent delegation, input filters, callbacks, nested history |
| **Guardrails** | `references/05-guardrails.md` | Input/output validation, tripwires, tool guardrails |
| **Streaming** | `references/06-streaming.md` | Stream events, real-time output, cancellation, approvals |
| **Context** | `references/07-context.md` | RunContextWrapper, ToolContext, dependency injection |
| **Multi-Agent** | `references/08-multi-agent.md` | Orchestration patterns, manager vs handoff, visualization |
| **Models** | `references/09-models.md` | OpenAI models, non-OpenAI providers, LiteLLM, retries |
| **MCP Integration** | `references/10-mcp.md` | MCP servers, hosted MCP, tool filtering, server manager |
| **Sessions** | `references/11-sessions.md` | Conversation persistence, SQLite, SQLAlchemy, encrypted |
| **Tracing** | `references/12-tracing.md` | Built-in tracing, custom spans, processors, sensitivity |

## Installation

```bash
# Core package
pip install openai-agents

# With voice support
pip install 'openai-agents[voice]'

# With LiteLLM integration
pip install 'openai-agents[litellm]'

# Using uv
uv add openai-agents

# Set API key
export OPENAI_API_KEY=sk-...
```

## Quick Reference

- **Docs:** https://openai.github.io/openai-agents-python/
- **GitHub:** https://github.com/openai/openai-agents-python
- **PyPI:** https://pypi.org/project/openai-agents/
- **API Guide:** https://developers.openai.com/api/docs/guides/agents
- **Examples:** https://github.com/openai/openai-agents-python/tree/main/examples
