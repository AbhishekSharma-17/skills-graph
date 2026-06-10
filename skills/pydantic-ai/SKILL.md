---
name: pydantic-ai
description: "Type-safe Python agent framework for building production-grade GenAI applications with Pydantic validation, structured outputs, and dependency injection. MANDATORY TRIGGERS: pydantic-ai, pydantic_ai, PydanticAI, pydantic ai agent. Also trigger when the user wants to build type-safe AI agents in Python, create structured LLM outputs with Pydantic models, implement dependency injection for agents, use tools/capabilities with LLMs, or build multi-agent systems with Python type safety. When in doubt about whether to use this skill for Python AI agent tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["ai-agents", "pydantic", "llm", "structured-output", "type-safe", "python", "tools", "mcp", "evals"]
---

# Pydantic AI

> Source: [pydantic.dev/docs/ai](https://pydantic.dev/docs/ai/) | Version tracked: 1.107.0 | `pip install pydantic-ai`

## Reference Files

| File | Read When |
|------|-----------|
| `references/00-overview.md` | Starting with Pydantic AI, understanding architecture, installation, quick start |
| `references/01-agents.md` | Creating agents, system prompts, instructions, running agents, model settings |
| `references/02-dependencies.md` | Dependency injection, RunContext, typed deps, overriding for tests |
| `references/03-output.md` | Structured output types, output functions, validators, unions, image output |
| `references/04-tools.md` | Function tools, @agent.tool decorators, prepare callbacks, retries, dynamic tools |
| `references/05-capabilities.md` | Capabilities, AbstractCapability, on-demand loading, bundling tools+hooks |
| `references/06-hooks.md` | Lifecycle hooks, model request hooks, tool hooks, output hooks, wrap hooks |
| `references/07-streaming.md` | Streaming text, structured output streaming, stream events, cancellation |
| `references/08-models.md` | Model providers, OpenAI/Anthropic/Google/Ollama config, fallbacks, concurrency |
| `references/09-multi-agent.md` | Multi-agent delegation, handoff, programmatic orchestration, agent-as-tool |
| `references/10-mcp.md` | MCP client integration, FastMCP toolset, native MCP tools, MCP server mode |
| `references/11-testing-evals.md` | TestModel, FunctionModel, agent.override, Pydantic Evals, online evaluation |
| `references/12-logfire-observability.md` | Logfire integration, OpenTelemetry traces, debugging, monitoring agents |

## Installation

```bash
pip install pydantic-ai            # Full install (all providers + Logfire)
pip install pydantic-ai-slim       # Minimal — add provider extras as needed
pip install 'pydantic-ai[ui]'      # Web chat UI support
pip install 'pydantic-ai[evals]'   # Evaluation framework
```

## Quick Reference

- [Docs](https://pydantic.dev/docs/ai/) | [GitHub](https://github.com/pydantic/pydantic-ai) | [PyPI](https://pypi.org/project/pydantic-ai/)
