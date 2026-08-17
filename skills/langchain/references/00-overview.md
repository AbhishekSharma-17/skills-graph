# LangChain Overview

> Source: https://docs.langchain.com — langchain v1.3.15

## Table of Contents

- [What Is LangChain](#what-is-langchain)
- [Core Architecture](#core-architecture)
- [Package Structure](#package-structure)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Key Abstractions](#key-abstractions)
- [When to Use LangChain](#when-to-use-langchain)
- [Ecosystem](#ecosystem)

## What Is LangChain

LangChain is the most popular Python framework for building LLM-powered applications and agents. With 144K+ GitHub stars, it provides a unified interface across 80+ model providers, composable primitives for chains and pipelines, and a complete toolkit for retrieval-augmented generation (RAG).

The core equation: **Agent = Model + Harness**. LangChain provides the harness — tools, prompts, middleware, state management — while you choose the model.

## Core Architecture

LangChain is built around three layers:

1. **langchain-core** — Base abstractions: messages, runnables, prompts, tools, callbacks, output parsers
2. **langchain** — Higher-level chains, agents (`create_agent`), and orchestration
3. **langchain-{provider}** — Model integrations (OpenAI, Anthropic, Google, etc.)

Everything implements the **Runnable** interface with three methods:
- `.invoke(input)` — Single input, single output
- `.stream(input)` — Single input, streamed output
- `.batch(inputs)` — Multiple inputs, multiple outputs

Each method has an async counterpart: `.ainvoke()`, `.astream()`, `.abatch()`.

## Package Structure

```
langchain-core          # Base abstractions (messages, runnables, tools)
langchain               # Chains, agents, create_agent, LCEL
langchain-community     # Community integrations (vector stores, loaders)
langchain-openai        # OpenAI / Azure OpenAI models
langchain-anthropic     # Anthropic Claude models
langchain-google-genai  # Google Gemini models
langchain-aws           # AWS Bedrock models
langgraph               # Stateful multi-actor orchestration
langsmith               # Tracing, evaluation, monitoring
```

## Installation

### Minimal Install

```bash
pip install langchain
```

### With a Provider

```bash
pip install langchain langchain-openai
# or
pip install langchain langchain-anthropic
# or
pip install langchain langchain-google-genai
```

### With Extras

```bash
pip install langchain[anthropic,openai]
```

### Full RAG Stack

```bash
pip install langchain langchain-openai langchain-community faiss-cpu
```

### Environment Setup

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export LANGSMITH_API_KEY="lsv2_..."
export LANGSMITH_TRACING=true
```

## Quick Start

### Basic Chat Model

```python
from langchain_openai import ChatOpenAI

model = ChatOpenAI(model="gpt-4o")
response = model.invoke("Explain quantum computing in one sentence.")
print(response.content)
```

### With Prompt Template

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a {role}."),
    ("human", "{question}")
])

model = ChatOpenAI(model="gpt-4o")
chain = prompt | model
response = chain.invoke({"role": "physicist", "question": "What is dark matter?"})
print(response.content)
```

### Agent with Tools

```python
from langchain.agents import create_agent
from langchain.tools import tool

@tool
def search(query: str) -> str:
    """Search for information on the web."""
    return f"Results for: {query}"

agent = create_agent(model="anthropic:claude-sonnet-4-6", tools=[search])
result = agent.invoke({
    "messages": [{"role": "user", "content": "Search for Python 3.13 features"}]
})
```

## Key Abstractions

| Abstraction | Purpose | Module |
|-------------|---------|--------|
| **ChatModel** | Unified LLM interface | `langchain_core.language_models` |
| **Messages** | Conversation representation | `langchain_core.messages` |
| **PromptTemplate** | Parameterized prompts | `langchain_core.prompts` |
| **Runnable** | Composable pipeline unit | `langchain_core.runnables` |
| **Tool** | Model-callable functions | `langchain_core.tools` |
| **OutputParser** | Structured response parsing | `langchain_core.output_parsers` |
| **DocumentLoader** | External data ingestion | `langchain_community.document_loaders` |
| **TextSplitter** | Document chunking | `langchain_text_splitters` |
| **Embeddings** | Text to vector conversion | `langchain_core.embeddings` |
| **VectorStore** | Similarity search storage | `langchain_core.vectorstores` |
| **Retriever** | Document retrieval interface | `langchain_core.retrievers` |
| **Callback** | Lifecycle event hooks | `langchain_core.callbacks` |

## When to Use LangChain

**Use LangChain when:**
- Building applications that call LLMs with tools, structured output, or RAG
- You need a unified interface across multiple model providers
- Building agents that reason and act in loops
- You want composable pipelines with LCEL
- You need tracing and observability via LangSmith

**Use LangGraph instead when:**
- You need deterministic multi-step workflows with branching
- Building multi-agent systems with complex state
- You need human-in-the-loop approval flows with persistence

**Use neither when:**
- A single API call with no composition is sufficient
- You want minimal dependencies and direct SDK usage

## Ecosystem

| Product | Purpose |
|---------|---------|
| **LangChain** | Agent harness, chains, tools |
| **LangGraph** | Stateful orchestration, multi-actor workflows |
| **LangSmith** | Tracing, evaluation, monitoring |
| **Deep Agents** | Batteries-included agent with filesystem, memory, subagents |
| **LangServe** | Deploy chains as REST APIs |

## Python Version Support

LangChain requires Python >=3.10 and supports Python 3.10, 3.11, 3.12, 3.13, and 3.14.
