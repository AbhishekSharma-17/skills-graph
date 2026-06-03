---
name: haystack
description: "AI orchestration framework for building production-ready RAG applications, autonomous agents, and multimodal search systems. MANDATORY TRIGGERS: haystack, deepset, haystack-ai, haystack pipeline, haystack agent. Also trigger when the user wants to build RAG pipelines with modular components, create tool-calling agents with Haystack, orchestrate retrieval-augmented generation, build semantic search systems, or evaluate LLM pipelines. When in doubt about whether to use this skill for RAG orchestration or AI pipeline tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["ai", "rag", "agents", "llm", "pipelines", "search", "retrieval", "orchestration", "deepset"]
---

# Haystack

> Source: [docs.haystack.deepset.ai](https://docs.haystack.deepset.ai) | Version tracked: 2.30.0 | `pip install haystack-ai`

## Reference Files

| File | Read When |
|------|-----------|
| `references/00-overview.md` | Starting with Haystack, understanding architecture, installation |
| `references/01-components.md` | Creating custom components, understanding the component API |
| `references/02-pipelines.md` | Building pipelines, connecting components, branching, loops, async |
| `references/03-agents.md` | Building tool-calling agents, state management, multi-agent systems |
| `references/04-tools.md` | Defining tools, @tool decorator, ComponentTool, MCPTool, Toolset |
| `references/05-generators.md` | Configuring LLM generators, supported providers, streaming |
| `references/06-retrievers.md` | Retrieval strategies: BM25, embedding, hybrid, multi-query |
| `references/07-document-stores.md` | Choosing and configuring document stores, DuplicatePolicy |
| `references/08-embedders.md` | Text and document embedding, choosing embedders |
| `references/09-converters-preprocessors.md` | Converting files, splitting and cleaning documents |
| `references/10-prompt-building.md` | PromptBuilder, ChatPromptBuilder, Jinja2 templates, routers |
| `references/11-rag-patterns.md` | Building RAG applications end-to-end, indexing and retrieval |
| `references/12-evaluation.md` | Evaluating pipelines, metrics, model-based and statistical |

## Installation

```bash
pip install haystack-ai
```

## Quick Reference

- [Docs](https://docs.haystack.deepset.ai) | [GitHub](https://github.com/deepset-ai/haystack) | [PyPI](https://pypi.org/project/haystack-ai/) | [Tutorials](https://haystack.deepset.ai/tutorials)
