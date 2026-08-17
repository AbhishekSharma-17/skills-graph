---
name: langchain
description: "Build LLM-powered agents and applications with LangChain — the most popular Python framework for composing chat models, tools, prompts, retrieval, and chains. MANDATORY TRIGGERS: langchain, langchain-core, LCEL, LangChain Expression Language. Also trigger when the user wants to build LLM applications with tool calling, RAG pipelines, document loaders, text splitters, embedding models, vector stores, retrievers, structured output from LLMs, or agent loops with create_agent. When in doubt about whether to use this skill for LLM application development tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["langchain", "llm", "agents", "rag", "lcel", "python", "ai"]
---

# LangChain

> Source: langchain v1.3.15 — https://docs.langchain.com

## Reference Files

| File | Read When |
|------|-----------|
| [00-overview](references/00-overview.md) | Starting with LangChain, installation, architecture, package structure |
| [01-chat-models](references/01-chat-models.md) | Initializing models, invoking, provider selection, configuration |
| [02-messages](references/02-messages.md) | Message types, content blocks, multimodal input, serialization |
| [03-prompt-templates](references/03-prompt-templates.md) | ChatPromptTemplate, composition, few-shot, partial variables |
| [04-structured-output](references/04-structured-output.md) | with_structured_output, Pydantic schemas, provider vs tool strategy |
| [05-tools](references/05-tools.md) | @tool decorator, schemas, ToolRuntime, return types, error handling |
| [06-agents](references/06-agents.md) | create_agent, middleware, state management, human-in-the-loop |
| [07-lcel-runnables](references/07-lcel-runnables.md) | Pipe operator, RunnableSequence, RunnableParallel, RunnableLambda |
| [08-retrieval-rag](references/08-retrieval-rag.md) | Document loaders, text splitters, embeddings, vector stores, RAG |
| [09-streaming](references/09-streaming.md) | stream(), astream_events(), token streaming, modes |
| [10-callbacks-tracing](references/10-callbacks-tracing.md) | Callbacks, LangSmith tracing, debugging, observability |
| [11-memory-persistence](references/11-memory-persistence.md) | Checkpointers, stores, conversation history, thread management |
| [12-integrations](references/12-integrations.md) | Provider packages, community integrations, model profiles |

## Installation

```bash
pip install langchain                     # Core framework
pip install langchain-openai              # OpenAI models
pip install langchain-anthropic           # Anthropic Claude models
pip install langchain-google-genai        # Google Gemini models
pip install langchain-community           # Community integrations
```

## Quick Reference

- Docs: https://docs.langchain.com
- API Reference: https://reference.langchain.com
- GitHub: https://github.com/langchain-ai/langchain
- PyPI: https://pypi.org/project/langchain/
