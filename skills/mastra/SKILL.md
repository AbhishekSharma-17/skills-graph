---
name: mastra
description: "Mastra TypeScript AI agent framework for building production-ready agents, workflows, tools, RAG, memory, evals, voice, and multi-agent systems. MANDATORY TRIGGERS: mastra, Mastra, @mastra/core, mastra-ai, createTool, createWorkflow, createStep. Also trigger when user wants to build TypeScript AI agents with tools and memory, create graph-based workflows with suspend/resume, implement RAG pipelines in TypeScript, build multi-agent supervisor systems, add voice to AI agents, or deploy AI agent servers. When in doubt about whether to use this skill for TypeScript AI agent tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["mastra", "ai-agents", "typescript", "workflows", "tools", "rag", "memory", "evals", "voice", "multi-agent"]
---

# Mastra — Skill Router

> TypeScript AI agent framework for building production-ready applications with agents, workflows, tools, and memory.

**Source:** [mastra.ai/docs](https://mastra.ai/docs) | **Package:** `@mastra/core` v1.37.x | **License:** ELv2

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Setup** | `references/00-overview.md` | Getting started, installation, project structure, when to use Mastra |
| **Agents** | `references/01-agents.md` | Agent creation, generate/stream, instructions, model routing |
| **Tools** | `references/02-tools.md` | createTool, input/output schemas, MCP servers, tool control |
| **Workflows** | `references/03-workflows.md` | createWorkflow, createStep, execution, state, streaming |
| **Control Flow** | `references/04-control-flow.md` | Parallel, branching, loops, foreach, map, nested workflows |
| **Suspend & Resume** | `references/05-suspend-resume.md` | Human-in-the-loop, suspend/resume, sleep, approval patterns |
| **Memory** | `references/06-memory.md` | Message history, working memory, semantic recall, observational memory |
| **RAG** | `references/07-rag.md` | Document processing, chunking, embeddings, vector stores, retrieval |
| **Structured Output** | `references/08-structured-output.md` | Typed responses, output schemas, streaming, error handling |
| **Multi-Agent Systems** | `references/09-multi-agent.md` | Supervisor agents, delegation, memory isolation, networks |
| **Guardrails & Safety** | `references/10-guardrails.md` | Processors, prompt injection, PII detection, moderation, cost guards |
| **Evals & Observability** | `references/11-evals-observability.md` | Scorers, live evals, tracing, logging, metrics, Studio |
| **Voice** | `references/12-voice.md` | TTS, STT, real-time voice, providers, composite voice |
| **Server & Deployment** | `references/13-server-deployment.md` | Hono server, API routes, middleware, auth, deployment options |

## Installation

```bash
# Create new project
npx create-mastra@latest

# Or add to existing project
npm install @mastra/core@latest
npm install @mastra/memory@latest      # Memory support
npm install @mastra/libsql@latest      # Storage provider
npm install @mastra/evals@latest       # Evaluation scorers
npm install @mastra/observability@latest # Tracing & metrics
```

## Quick Reference

- **Docs:** https://mastra.ai/docs
- **GitHub:** https://github.com/mastra-ai/mastra
- **npm:** https://www.npmjs.com/package/@mastra/core
- **Studio:** Built-in via `mastra dev`
- **Examples:** https://github.com/mastra-ai/mastra/tree/main/examples
