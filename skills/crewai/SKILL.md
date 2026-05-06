---
name: crewai
description: "CrewAI multi-agent orchestration framework for building role-based AI agent teams with tasks, tools, memory, flows, and production deployment. MANDATORY TRIGGERS: crewai, CrewAI, crew ai, multi-agent crew, Agent crew, crewai-tools. Also trigger when user wants to build multi-agent systems with role-based agents, orchestrate AI teams with sequential or hierarchical processes, create event-driven agent workflows with Flows, implement agent collaboration and delegation, or deploy production agent systems. When in doubt about whether to use this skill for multi-agent orchestration tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["crewai", "multi-agent", "ai-agents", "orchestration", "crews", "tasks", "tools", "flows", "memory", "python"]
---

# CrewAI — Skill Router

> Multi-agent orchestration framework for building role-based AI agent teams that collaborate on complex tasks.

**Source:** [docs.crewai.com](https://docs.crewai.com) | **Package:** `crewai` v1.3.x | **License:** MIT

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Setup** | `references/00-overview.md` | Getting started, installation, quickstart, when to use CrewAI |
| **Agents** | `references/01-agents.md` | Agent creation, roles, goals, backstory, configuration |
| **Tasks** | `references/02-tasks.md` | Task definition, expected_output, guardrails, async tasks |
| **Crews** | `references/03-crews.md` | Crew composition, kickoff, output, callbacks, configuration |
| **Processes** | `references/04-processes.md` | Sequential, hierarchical, manager agent, planning |
| **Tools** | `references/05-tools.md` | Built-in tools, custom tools, BaseTool, @tool decorator |
| **Flows** | `references/06-flows.md` | Event-driven orchestration, @start, @listen, @router, state |
| **Memory & Knowledge** | `references/07-memory-knowledge.md` | Memory system, knowledge sources, RAG, embeddings |
| **LLM Configuration** | `references/08-llm-configuration.md` | Providers, model selection, env vars, parameters |
| **Collaboration** | `references/09-collaboration.md` | Delegation, agent communication, allow_delegation |
| **Structured Output** | `references/10-structured-output.md` | Pydantic models, JSON output, output validation |
| **MCP Integration** | `references/11-mcp-integration.md` | MCP servers, tool routing, external integrations |
| **CLI & Deployment** | `references/12-cli-deployment.md` | CLI commands, project scaffolding, production deployment |

## Installation

```bash
# Core package
pip install crewai

# With tools
pip install 'crewai[tools]'

# Using uv
uv add crewai
uv add 'crewai[tools]'

# CLI project scaffolding
crewai create crew my-project
```

## Quick Reference

- **Docs:** https://docs.crewai.com
- **GitHub:** https://github.com/crewAIInc/crewAI
- **PyPI:** https://pypi.org/project/crewai/
- **Community:** https://community.crewai.com
- **Examples:** https://github.com/crewAIInc/crewAI-examples
