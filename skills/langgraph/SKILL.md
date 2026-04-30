---
name: langgraph
description: "LangGraph agent orchestration framework for building stateful, multi-actor AI applications as graphs with durable execution, human-in-the-loop, and streaming. MANDATORY TRIGGERS: langgraph, LangGraph, lang graph, StateGraph, langgraph-prebuilt, create_react_agent, langgraph checkpoint. Also trigger when user wants to build stateful AI agents with graph-based workflows, create multi-agent systems with supervisor or swarm patterns, implement human-in-the-loop agent workflows, add persistence and memory to LLM applications, or orchestrate complex agent pipelines with conditional routing. When in doubt about whether to use this skill for AI agent orchestration tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["langgraph", "ai-agents", "state-machine", "graph", "multi-agent", "human-in-the-loop", "streaming", "persistence", "langchain", "orchestration"]
---

# LangGraph — Skill Router

> Agent orchestration framework for building resilient, stateful AI applications as directed graphs.

**Source:** [docs.langchain.com/oss/python/langgraph](https://docs.langchain.com/oss/python/langgraph/overview) | **Package:** `langgraph` v1.x | **License:** MIT

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Setup** | `references/00-overview.md` | Getting started, installation, quickstart, when to use LangGraph |
| **Graph API** | `references/01-graph-api.md` | StateGraph, add_node, add_edge, add_conditional_edges, compile |
| **State Management** | `references/02-state-management.md` | State schema, TypedDict, Pydantic, reducers, MessagesState |
| **Functional API** | `references/03-functional-api.md` | @entrypoint, @task, lightweight workflows without graph structure |
| **Persistence & Checkpointing** | `references/04-persistence-checkpointing.md` | Checkpointers, SQLite, Postgres, thread management, durable execution |
| **Memory** | `references/05-memory.md` | Short-term memory, long-term memory, BaseStore, semantic memory |
| **Streaming** | `references/06-streaming.md` | Stream modes, token streaming, custom streaming, async patterns |
| **Human-in-the-Loop** | `references/07-human-in-the-loop.md` | interrupt(), Command, breakpoints, approval workflows, time-travel |
| **Tool Integration** | `references/08-tool-integration.md` | Tool calling, ToolNode, tool binding, routing, error handling |
| **Prebuilt Agents** | `references/09-prebuilt-agents.md` | create_react_agent, ReAct pattern, prebuilt components, customization |
| **Multi-Agent Systems** | `references/10-multi-agent.md` | Supervisor, swarm, handoffs, Command routing, agent teams |
| **Subgraphs & Composition** | `references/11-subgraphs.md` | Nested graphs, state mapping, parent-child communication |
| **Deployment & Production** | `references/12-deployment.md` | LangGraph Platform, LangSmith, Cloud/self-hosted, testing patterns |

## Installation

```bash
# Core package
pip install -U langgraph

# With prebuilt agents
pip install -U langgraph langgraph-prebuilt

# Checkpoint backends (pick one)
pip install langgraph-checkpoint-sqlite
pip install langgraph-checkpoint-postgres

# With LangChain integrations
pip install langchain-openai langchain-anthropic
```

## Quick Reference

- **Docs:** https://docs.langchain.com/oss/python/langgraph/overview
- **GitHub:** https://github.com/langchain-ai/langgraph
- **PyPI:** https://pypi.org/project/langgraph/
- **LangSmith:** https://smith.langchain.com
- **Discord:** https://discord.gg/langchain
