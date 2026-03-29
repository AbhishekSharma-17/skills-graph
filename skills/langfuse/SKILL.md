---
name: langfuse
description: "Open-source LLM observability and evaluation platform for tracing, prompt management, datasets, and cost analytics. MANDATORY TRIGGERS: langfuse, langfuse tracing, langfuse observability, langfuse evaluation, LLM observability, LLM tracing, LLM monitoring. Also trigger when user wants to trace LLM calls, monitor token usage and costs, manage prompts with versioning, evaluate LLM outputs with datasets, set up LLM-as-a-judge, or instrument AI agents with OpenTelemetry. When in doubt about whether to use this skill for LLM observability tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["langfuse", "llm-observability", "tracing", "evaluation", "prompt-management", "opentelemetry", "llm-monitoring", "ai-observability", "cost-tracking"]
---

# Langfuse — Skill Router

> Open-source LLM engineering platform: observability, evals, prompt management, and analytics.

**Source:** [langfuse.com](https://langfuse.com/docs) v3.162.0 | **Package:** `langfuse` (Python) / `@langfuse/core` (JS) | **License:** MIT

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Setup** | `references/00-overview.md` | Getting started, installation, what Langfuse is, architecture, quickstart |
| **Python SDK — Decorators** | `references/01-python-decorators.md` | @observe decorator, auto-tracing, nesting, async, input/output capture |
| **Python SDK — Low-Level** | `references/02-python-low-level.md` | Manual traces, spans, generations, context managers, flush, get_client |
| **TypeScript SDK** | `references/03-typescript-sdk.md` | JS/TS tracing, OpenTelemetry setup, observeOpenAI, startActiveObservation |
| **Tracing Concepts** | `references/04-tracing-concepts.md` | Traces, spans, generations, sessions, users, tags, metadata, environments |
| **OpenTelemetry Integration** | `references/05-opentelemetry.md` | OTLP endpoint, span processors, attribute mapping, collector config |
| **Framework Integrations** | `references/06-integrations.md` | LangChain, LlamaIndex, OpenAI SDK, Vercel AI SDK, LiteLLM, CrewAI |
| **Prompt Management** | `references/07-prompt-management.md` | Versioning, labels, templates, caching, compile, deployment workflow |
| **Evaluation & Datasets** | `references/08-evaluation-datasets.md` | Datasets, experiments, scoring, LLM-as-a-judge, annotation workflows |
| **Analytics & Dashboards** | `references/09-analytics.md` | Cost tracking, latency, token usage, custom dashboards, metrics API |
| **Self-Hosting** | `references/10-self-hosting.md` | Docker, Kubernetes, Postgres, ClickHouse, Redis, environment variables |
| **Security & Data Privacy** | `references/11-security.md` | Data masking, PII redaction, access control, SSO, compliance, encryption |
| **Best Practices** | `references/12-best-practices.md` | Production patterns, performance, error handling, migration, scaling |

## Installation

```bash
# Python
pip install langfuse

# JavaScript/TypeScript (OpenAI wrapper)
npm install @langfuse/openai

# JavaScript/TypeScript (OTEL-native)
npm install @langfuse/tracing @langfuse/otel @opentelemetry/sdk-node
```

## Quick Reference

- **Docs:** https://langfuse.com/docs
- **GitHub:** https://github.com/langfuse/langfuse
- **PyPI:** https://pypi.org/project/langfuse/
- **npm:** https://www.npmjs.com/package/@langfuse/core
