# Haystack Overview

> Source: [docs.haystack.deepset.ai](https://docs.haystack.deepset.ai/docs/intro) | haystack-ai 2.30.0

## Table of Contents

- [What Is Haystack](#what-is-haystack)
- [Core Architecture](#core-architecture)
- [Key Concepts](#key-concepts)
- [Installation](#installation)
- [Environment Setup](#environment-setup)
- [First RAG Pipeline](#first-rag-pipeline)
- [First Agent](#first-agent)
- [When to Use Haystack](#when-to-use-haystack)
- [Haystack vs Alternatives](#haystack-vs-alternatives)

## What Is Haystack

Haystack is an open-source AI orchestration framework by deepset for building production-ready LLM applications. It provides modular, composable components for retrieval-augmented generation (RAG), autonomous agents, semantic search, and multimodal applications.

Key characteristics:
- **Modular pipeline architecture** — compose components into directed graphs
- **Model-agnostic** — OpenAI, Anthropic, Google, Hugging Face, Ollama, and 40+ providers
- **Production-grade** — used by Apple, Meta, Netflix, NVIDIA, Airbus, Databricks
- **Python-native** — Python 3.10+ with full type hints
- **Apache-2.0 licensed** — fully open source

## Core Architecture

Haystack's architecture centers on three abstractions:

```
Components → Pipelines → Applications
     ↑            ↑
  Document     Agents
   Stores
```

1. **Components** — self-contained units that perform a single task (retrieve, embed, generate, convert, etc.). Each has a `run()` method with typed inputs/outputs.
2. **Pipelines** — directed multigraphs connecting components. Support branching, loops, conditional routing, and async execution.
3. **Document Stores** — database adapters for storing/retrieving documents. Not pipeline components — they're used _by_ components like Retrievers and Writers.
4. **Agents** — loop-based components that use LLMs + tools to solve complex tasks iteratively.

## Key Concepts

### Documents

The universal data unit. Documents carry content, metadata, embeddings, and scores:

```python
from haystack import Document

doc = Document(
    content="Haystack is an AI framework.",
    meta={"source": "docs", "version": "2.30"},
    id="doc-001",
)
```

### Components

Building blocks with `run()` methods. Connected via typed inputs/outputs:

```python
from haystack import component

@component
class Greeter:
    @component.output_types(greeting=str)
    def run(self, name: str):
        return {"greeting": f"Hello, {name}!"}
```

### Pipelines

Directed graphs orchestrating component execution:

```python
from haystack import Pipeline

pipe = Pipeline()
pipe.add_component("greeter", Greeter())
pipe.run({"greeter": {"name": "World"}})
```

### Secrets

Secure credential management via environment variables:

```python
from haystack.utils import Secret

generator = OpenAIChatGenerator(
    api_key=Secret.from_env_var("OPENAI_API_KEY")
)
```

## Installation

```bash
# Core framework
pip install haystack-ai

# With specific integrations
pip install haystack-ai elasticsearch-haystack   # Elasticsearch
pip install haystack-ai qdrant-haystack           # Qdrant
pip install haystack-ai chroma-haystack           # Chroma
pip install haystack-ai pinecone-haystack         # Pinecone
pip install haystack-ai anthropic-haystack        # Anthropic
pip install haystack-ai ollama-haystack           # Ollama
pip install haystack-ai mcp-haystack              # MCP tools

# Pre-release
pip install --pre haystack-ai
```

**Python requirement**: 3.10, 3.11, 3.12, 3.13, 3.14

**Important**: The package is `haystack-ai`, not the legacy `farm-haystack` (v1.x). They are different packages.

## Environment Setup

Set API keys as environment variables:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export SERPER_API_KEY="..."
export HF_TOKEN="hf_..."
```

Or use `.env` files with `python-dotenv`:

```python
from dotenv import load_dotenv
load_dotenv()
```

## First RAG Pipeline

A complete RAG pipeline: retrieve relevant documents then generate an answer:

```python
from haystack import Document, Pipeline
from haystack.components.builders import ChatPromptBuilder
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.components.retrievers.in_memory import InMemoryBM25Retriever
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.dataclasses import ChatMessage

# 1. Create document store and add documents
doc_store = InMemoryDocumentStore()
doc_store.write_documents([
    Document(content="Haystack is an AI orchestration framework by deepset."),
    Document(content="Haystack supports RAG, agents, and semantic search."),
    Document(content="Install Haystack with: pip install haystack-ai"),
])

# 2. Build the pipeline
pipe = Pipeline()
pipe.add_component("retriever", InMemoryBM25Retriever(document_store=doc_store))
pipe.add_component("prompt", ChatPromptBuilder(
    template=[
        ChatMessage.from_system(
            "Answer based on these documents:\n"
            "{% for doc in documents %}\n{{ doc.content }}\n{% endfor %}"
        ),
        ChatMessage.from_user("{{ query }}"),
    ]
))
pipe.add_component("llm", OpenAIChatGenerator(model="gpt-4o-mini"))

# 3. Connect components
pipe.connect("retriever.documents", "prompt.documents")
pipe.connect("prompt", "llm")

# 4. Run
result = pipe.run({
    "retriever": {"query": "What is Haystack?"},
    "prompt": {"query": "What is Haystack?"},
})
print(result["llm"]["replies"][0].text)
```

## First Agent

A tool-calling agent that searches the web:

```python
from haystack.components.agents import Agent
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.dataclasses import ChatMessage
from haystack.tools import tool

@tool
def calculator(expression: str) -> str:
    """Evaluate a math expression."""
    return str(eval(expression, {"__builtins__": {}}))

agent = Agent(
    chat_generator=OpenAIChatGenerator(model="gpt-4o-mini"),
    tools=[calculator],
    system_prompt="You are a helpful assistant. Use the calculator for math.",
)

result = agent.run(
    messages=[ChatMessage.from_user("What is 42 * 17 + 89?")]
)
print(result["last_message"].text)
```

## When to Use Haystack

**Good fit:**
- Production RAG applications with multiple retrieval strategies
- Autonomous agents needing structured tool orchestration
- Multimodal search systems (text + images)
- Pipeline-based architectures needing branching, loops, and conditional logic
- Evaluating and comparing LLM pipeline performance
- Projects needing 40+ model provider integrations

**Not ideal for:**
- Simple single-API-call LLM wrappers (use the provider SDK directly)
- Non-Python projects (Haystack is Python-only)
- Real-time streaming-only applications without retrieval

## Haystack vs Alternatives

| Feature | Haystack | LangChain | LlamaIndex | DSPy |
|---------|----------|-----------|------------|------|
| Architecture | Pipeline graphs | Chains/LCEL | Index + query engine | Declarative modules |
| Strength | Modular orchestration | Broad ecosystem | Document indexing | Prompt optimization |
| Agent support | Built-in Agent component | AgentExecutor | Agent workers | N/A |
| Evaluation | Built-in evaluators | LangSmith | Built-in | Auto-optimization |
| MCP support | MCPTool/MCPToolset | MCP adapter | N/A | N/A |
| Typing | Strong typed I/O | Runnables | Weakly typed | Signatures |

## Related Topics

- Components → `01-components.md`
- Pipelines → `02-pipelines.md`
- Agents → `03-agents.md`
- RAG Patterns → `11-rag-patterns.md`
