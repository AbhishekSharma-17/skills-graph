# Haystack RAG Patterns

> Source: [docs.haystack.deepset.ai](https://docs.haystack.deepset.ai) | haystack-ai 2.30.0

## Table of Contents

- [RAG Overview](#rag-overview)
- [Basic RAG Pipeline](#basic-rag-pipeline)
- [Indexing Pipeline](#indexing-pipeline)
- [Query Pipeline](#query-pipeline)
- [Advanced RAG Patterns](#advanced-rag-patterns)
- [RAG with Hybrid Retrieval](#rag-with-hybrid-retrieval)
- [Self-Correcting RAG](#self-correcting-rag)
- [RAG with Reranking](#rag-with-reranking)
- [Conversational RAG](#conversational-rag)
- [RAG Agent](#rag-agent)
- [Common Pitfalls](#common-pitfalls)

## RAG Overview

Retrieval-Augmented Generation (RAG) enhances LLM responses by grounding them in retrieved documents. A RAG system has two main pipelines:

```
Indexing:   Files → Convert → Clean → Split → Embed → Store
Querying:   Query → Retrieve → Build Prompt → Generate Answer
```

## Basic RAG Pipeline

End-to-end RAG in minimal code:

```python
from haystack import Document, Pipeline
from haystack.components.builders import ChatPromptBuilder
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.components.retrievers.in_memory import InMemoryBM25Retriever
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.dataclasses import ChatMessage

# Setup
store = InMemoryDocumentStore()
store.write_documents([
    Document(content="Python was created by Guido van Rossum in 1991."),
    Document(content="Python 3.12 introduced type parameter syntax."),
    Document(content="FastAPI is a modern Python web framework."),
])

# Build pipeline
rag = Pipeline()
rag.add_component("retriever", InMemoryBM25Retriever(document_store=store, top_k=3))
rag.add_component("prompt", ChatPromptBuilder(template=[
    ChatMessage.from_system(
        "Answer the question using ONLY the provided context. "
        "If the context doesn't contain the answer, say so.\n\n"
        "Context:\n{% for doc in documents %}\n{{ doc.content }}\n{% endfor %}"
    ),
    ChatMessage.from_user("{{ query }}"),
]))
rag.add_component("llm", OpenAIChatGenerator(model="gpt-4o-mini"))

rag.connect("retriever.documents", "prompt.documents")
rag.connect("prompt", "llm")

# Query
result = rag.run({
    "retriever": {"query": "When was Python created?"},
    "prompt": {"query": "When was Python created?"},
})
print(result["llm"]["replies"][0].text)
```

## Indexing Pipeline

Process and store documents for later retrieval:

```python
from haystack import Pipeline
from haystack.components.converters import PyPDFToDocument
from haystack.components.preprocessors import DocumentCleaner, DocumentSplitter
from haystack.components.embedders import OpenAIDocumentEmbedder
from haystack.components.writers import DocumentWriter
from haystack.document_stores.types import DuplicatePolicy

indexing = Pipeline()
indexing.add_component("converter", PyPDFToDocument())
indexing.add_component("cleaner", DocumentCleaner(
    remove_empty_lines=True,
    remove_extra_whitespaces=True,
))
indexing.add_component("splitter", DocumentSplitter(
    split_by="word",
    split_length=200,
    split_overlap=30,
    respect_sentence_boundary=True,
))
indexing.add_component("embedder", OpenAIDocumentEmbedder(
    model="text-embedding-3-small",
))
indexing.add_component("writer", DocumentWriter(
    document_store=store,
    policy=DuplicatePolicy.OVERWRITE,
))

indexing.connect("converter", "cleaner")
indexing.connect("cleaner", "splitter")
indexing.connect("splitter", "embedder")
indexing.connect("embedder", "writer")

# Index files
result = indexing.run({
    "converter": {"sources": ["docs/guide.pdf", "docs/api-ref.pdf"]}
})
print(f"Indexed {result['writer']['documents_written']} chunks")
```

### Multi-Format Indexing

```python
from haystack.components.routers import FileTypeRouter
from haystack.components.converters import (
    PyPDFToDocument, HTMLToDocument, MarkdownToDocument,
)
from haystack.components.joiners import DocumentJoiner

indexing = Pipeline()
indexing.add_component("router", FileTypeRouter(
    mime_types=["application/pdf", "text/html", "text/markdown"]
))
indexing.add_component("pdf", PyPDFToDocument())
indexing.add_component("html", HTMLToDocument())
indexing.add_component("md", MarkdownToDocument())
indexing.add_component("joiner", DocumentJoiner())
indexing.add_component("splitter", DocumentSplitter(split_by="word", split_length=200))
indexing.add_component("embedder", OpenAIDocumentEmbedder())
indexing.add_component("writer", DocumentWriter(document_store=store))

indexing.connect("router.application/pdf", "pdf")
indexing.connect("router.text/html", "html")
indexing.connect("router.text/markdown", "md")
indexing.connect("pdf", "joiner")
indexing.connect("html", "joiner")
indexing.connect("md", "joiner")
indexing.connect("joiner", "splitter")
indexing.connect("splitter", "embedder")
indexing.connect("embedder", "writer")
```

## Query Pipeline

Semantic retrieval + generation:

```python
from haystack.components.embedders import OpenAITextEmbedder
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever

query = Pipeline()
query.add_component("embedder", OpenAITextEmbedder(model="text-embedding-3-small"))
query.add_component("retriever", InMemoryEmbeddingRetriever(
    document_store=store, top_k=5
))
query.add_component("prompt", ChatPromptBuilder(template=[
    ChatMessage.from_system(
        "Answer based on the context. Cite your sources.\n\n"
        "{% for doc in documents %}"
        "[{{ loop.index }}] {{ doc.content }}\n"
        "{% endfor %}"
    ),
    ChatMessage.from_user("{{ query }}"),
]))
query.add_component("llm", OpenAIChatGenerator(model="gpt-4o-mini"))

query.connect("embedder.embedding", "retriever.query_embedding")
query.connect("retriever.documents", "prompt.documents")
query.connect("prompt", "llm")

result = query.run({
    "embedder": {"text": "How does Haystack handle retrieval?"},
    "prompt": {"query": "How does Haystack handle retrieval?"},
})
```

## Advanced RAG Patterns

### RAG with Hybrid Retrieval

Combine BM25 and embedding for better recall:

```python
from haystack.components.joiners import DocumentJoiner

rag = Pipeline()
rag.add_component("text_embedder", OpenAITextEmbedder())
rag.add_component("bm25", InMemoryBM25Retriever(document_store=store, top_k=10))
rag.add_component("embedding", InMemoryEmbeddingRetriever(document_store=store, top_k=10))
rag.add_component("joiner", DocumentJoiner(
    join_mode="reciprocal_rank_fusion",
    top_k=5,
))
rag.add_component("prompt", ChatPromptBuilder(template=rag_template))
rag.add_component("llm", OpenAIChatGenerator())

rag.connect("text_embedder.embedding", "embedding.query_embedding")
rag.connect("bm25.documents", "joiner.documents")
rag.connect("embedding.documents", "joiner.documents")
rag.connect("joiner.documents", "prompt.documents")
rag.connect("prompt", "llm")

result = rag.run({
    "bm25": {"query": "Haystack retrievers"},
    "text_embedder": {"text": "Haystack retrievers"},
    "prompt": {"query": "How do Haystack retrievers work?"},
})
```

## Self-Correcting RAG

Loop back when the output doesn't meet quality criteria:

```python
from haystack.components.validators import JsonSchemaValidator

rag = Pipeline(max_runs_per_component=3)

rag.add_component("retriever", InMemoryBM25Retriever(document_store=store))
rag.add_component("prompt", ChatPromptBuilder(template=[
    ChatMessage.from_system(
        "Answer in valid JSON: {\"answer\": \"...\", \"confidence\": 0.0-1.0}\n"
        "Context: {% for doc in documents %}{{ doc.content }}{% endfor %}"
    ),
    ChatMessage.from_user("{{ query }}"),
]))
rag.add_component("llm", OpenAIChatGenerator())
rag.add_component("validator", JsonSchemaValidator(json_schema={
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "required": ["answer", "confidence"],
}))

rag.connect("retriever.documents", "prompt.documents")
rag.connect("prompt", "llm")
rag.connect("llm.replies", "validator.messages")
rag.connect("validator.validation_error", "prompt.messages")  # Loop back on error
```

## RAG with Reranking

Add a reranker after retrieval for better precision:

```python
from haystack_integrations.components.rankers.cohere import CohereRanker

rag = Pipeline()
rag.add_component("retriever", InMemoryBM25Retriever(document_store=store, top_k=20))
rag.add_component("ranker", CohereRanker(top_k=5))
rag.add_component("prompt", ChatPromptBuilder(template=rag_template))
rag.add_component("llm", OpenAIChatGenerator())

rag.connect("retriever.documents", "ranker.documents")
rag.connect("ranker.documents", "prompt.documents")
rag.connect("prompt", "llm")

result = rag.run({
    "retriever": {"query": "How to deploy?"},
    "ranker": {"query": "How to deploy?"},
    "prompt": {"query": "How to deploy?"},
})
```

## Conversational RAG

Maintain conversation history across turns:

```python
from haystack.dataclasses import ChatMessage

messages_history = []

def chat(user_message: str):
    messages_history.append(ChatMessage.from_user(user_message))

    result = rag.run({
        "retriever": {"query": user_message},
        "prompt": {
            "query": user_message,
            "template_variables": {"messages": messages_history},
        },
    })

    reply = result["llm"]["replies"][0]
    messages_history.append(reply)
    return reply.text

# Multi-turn conversation
print(chat("What is Haystack?"))
print(chat("How does it compare to LangChain?"))
print(chat("Which one should I use for RAG?"))
```

## RAG Agent

Use an agent for dynamic retrieval decisions:

```python
from haystack.components.agents import Agent
from haystack.tools import ComponentTool

# Wrap retriever as a tool
search_tool = ComponentTool(
    component=InMemoryBM25Retriever(document_store=store, top_k=5),
    name="search_docs",
    description="Search the knowledge base for relevant documents",
)

rag_agent = Agent(
    chat_generator=OpenAIChatGenerator(model="gpt-4o"),
    tools=[search_tool],
    system_prompt=(
        "You are a documentation assistant. "
        "Search the knowledge base to answer questions accurately. "
        "Always cite the sources you find."
    ),
    max_agent_steps=5,
)

result = rag_agent.run(
    messages=[ChatMessage.from_user("How do I set up hybrid retrieval?")]
)
```

The agent decides autonomously whether to search, what queries to use, and when it has enough information to answer.

## Common Pitfalls

**Query not passed to both retriever and prompt**: In pipeline RAG, the query must be provided to both the retriever (for search) and the prompt builder (for the user question). Forgetting either breaks the pipeline.

**Using BM25 alone for semantic queries**: BM25 matches keywords, not meaning. For "How do neural networks learn?", BM25 might miss documents about "deep learning training". Use embedding retrieval or hybrid for semantic queries.

**Not evaluating RAG quality**: Use Haystack's built-in evaluators (`FaithfulnessEvaluator`, `ContextRelevanceEvaluator`) to measure and improve RAG quality. See `12-evaluation.md`.

**Prompt too long with too many documents**: Retrieving 50 documents into the prompt may exceed context limits or degrade quality. Use reranking to select the top 3-5 most relevant documents.

**No fallback for empty retrieval**: When the retriever returns no documents, the LLM hallucinates. Use a `ConditionalRouter` to handle empty results gracefully.

## Related Topics

- Retrievers → `06-retrievers.md`
- Document Stores → `07-document-stores.md`
- Prompt Building → `10-prompt-building.md`
- Evaluation → `12-evaluation.md`
