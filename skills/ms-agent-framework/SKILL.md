---
name: ms-agent-framework
description: "Expert skill for building AI agent systems with Microsoft Agent Framework (Python). MANDATORY TRIGGERS: Microsoft Agent Framework, agent-framework, Azure AI agents, Azure OpenAI agents. Also trigger when the user is building production AI agents, multi-agent orchestrations, agentic workflows on Azure, or discussing concepts like tools, semantic kernel, middleware, or memory in Python. When in doubt, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["agent framework", "python", "azure", "multi-agent"]
---

# Microsoft Agent Framework — Python Expert Skill

> **Version:** 1.0.0b260130 (Public Preview) | **Python only** | **Repo:** https://github.com/microsoft/agent-framework

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Framework Overview** | `references/00-framework-overview.md` | "what is this framework", "critical rules", "setup", "architecture", "common errors" |
| **Getting Started** | `references/01-getting-started.md` | "create a bot", "AI assistant", "hello world" |
| **Running Agents** | `references/02-running-agents.md` | "run agents", "streaming vs non-streaming", "ResponseStream" |
| **Structured Output** | `references/03-structured-output.md` | "JSON output", "typed response", "Pydantic" |
| **Tools (Function)** | `references/04-tools-function.md` | "call a function", "agent uses tools", "@tool decorator" |
| **Tools (Hosted)** | `references/05-tools-hosted.md` | "search the web", "MCP servers", "code interpreter" |
| **RAG** | `references/06-rag.md` | "search docs", "knowledge base" |
| **Sessions & Memory** | `references/07-sessions.md` | "remember things", "conversation history" |
| **Memory Providers** | `references/08-memory.md` | context providers, custom memory providers |
| **Middleware** | `references/09-middleware.md` | "intercept", "filter", "transform output" |
| **Model Providers** | `references/10-providers.md` | Azure OpenAI, OpenAI, Anthropic, Ollama, GitHub |
| **Workflows** | `references/11-workflows-core.md` | "pipeline", "execution graph", handlers, edges, events |
| **Multi-Agent** | `references/12a-orchestration-sequential.md` | "multiple agents", "coordination", sequential, parallel, handoff |
| **Deployment** | `references/13-deployment.md` | "Azure Functions", "host serverless", "A2A", "OpenAI compatible" |
| **Declarative** | `references/14-declarative.md` | "YAML workflow", "config-based agent" |
| **Observability** | `references/15-observability.md` | "debug", "trace", "OpenTelemetry" |
| **Multimodal** | `references/16-multimodal.md` | "vision", "analyze images" |
| **Custom Agents** | `references/17-custom-agents.md` | "own agent", "extend framework" |
| **Security & Purview** | `references/19-security.md` | "guardrails", "content safety", compliance, audit |
| **M365 Integration** | `references/21-m365-integration.md` | "Copilot agent", "Teams", "Graph API" |
| **Design Patterns** | `references/22-design-patterns-core.md` | "pattern for reflection / debate / supervisor / pipeline" |
| **Advanced Patterns** | `references/23-design-patterns-advanced.md` | circuit breakers, load balancing, batching |

## Installation

```bash
pip install agent-framework --pre
az login  # For Azure authentication
```

## Version Tracking

- **Skill version:** 1.0.0 | **Snapshot:** 2026-02-21
- Version metadata: `VERSION.json`
- Update checker: `python scripts/check-updates.py`
- Changelog: `CHANGELOG.md`

