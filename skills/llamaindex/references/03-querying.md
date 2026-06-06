# Querying

> Source: [developers.llamaindex.ai — Querying](https://developers.llamaindex.ai/python/framework/module_guides/querying/) | Version: 0.14.22

## Table of Contents
- [Overview](#overview)
- [Query Engines](#query-engines)
- [Chat Engines](#chat-engines)
- [Retrievers](#retrievers)
- [Response Synthesizers](#response-synthesizers)
- [Node Postprocessors](#node-postprocessors)
- [Routers](#routers)
- [Structured Output](#structured-output)
- [Streaming](#streaming)
- [Common Patterns](#common-patterns)

## Overview

The querying stage takes a user question, retrieves relevant context from an index, and synthesizes an LLM response. LlamaIndex decomposes querying into composable modules:

```
User Query → Retriever → Node Postprocessors → Response Synthesizer → Response
```

## Query Engines

A query engine is the end-to-end interface for single-turn question answering:

### Basic Usage

```python
query_engine = index.as_query_engine()
response = query_engine.query("What are the main conclusions?")

print(response)
print(response.source_nodes)
print(response.metadata)
```

### Configuration

```python
query_engine = index.as_query_engine(
    similarity_top_k=5,
    response_mode="compact",
    streaming=True,
)
```

### Response Modes

| Mode | Behavior |
|------|----------|
| `refine` | Iterate over each node, refining the answer sequentially |
| `compact` | Stuff as many nodes as possible into one prompt, then refine |
| `tree_summarize` | Build a tree of summaries bottom-up, return root summary |
| `simple_summarize` | Truncate all nodes to fit in one prompt |
| `no_text` | Return retrieved nodes only, no LLM synthesis |
| `accumulate` | Generate a response per node, then concatenate |
| `compact_accumulate` | Compact version of accumulate |

**Default:** `compact` — balances context coverage with API cost.

### Custom Query Engine

```python
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.response_synthesizers import get_response_synthesizer

retriever = index.as_retriever(similarity_top_k=10)
synthesizer = get_response_synthesizer(response_mode="tree_summarize")

query_engine = RetrieverQueryEngine(
    retriever=retriever,
    response_synthesizer=synthesizer,
)
```

## Chat Engines

Chat engines maintain conversation history for multi-turn interactions:

### Basic Usage

```python
chat_engine = index.as_chat_engine()
response = chat_engine.chat("Tell me about the project.")
response = chat_engine.chat("What were the key metrics?")

chat_engine.reset()
```

### Chat Modes

```python
chat_engine = index.as_chat_engine(
    chat_mode="condense_plus_context",
)
```

| Mode | Behavior |
|------|----------|
| `best` | Selects the best mode based on the index type |
| `condense_question` | Condenses chat history + new question into a standalone query |
| `condense_plus_context` | Condenses question, then retrieves context |
| `context` | Always retrieves context for each message |
| `simple` | Simple chat without retrieval (LLM only) |
| `react` | Uses ReAct agent with query engine as a tool |

### Streaming Chat

```python
chat_engine = index.as_chat_engine(streaming=True)
response = chat_engine.stream_chat("Explain the findings.")
for token in response.response_gen:
    print(token, end="", flush=True)
```

## Retrievers

Retrievers fetch relevant nodes from an index without LLM synthesis:

### Basic Retriever

```python
retriever = index.as_retriever(similarity_top_k=5)
nodes = retriever.retrieve("search query")

for node in nodes:
    print(f"Score: {node.score:.4f}")
    print(f"Text: {node.text[:200]}")
    print(f"Metadata: {node.metadata}")
```

### Retriever Types

| Retriever | Description |
|-----------|-------------|
| `VectorIndexRetriever` | Semantic similarity via embeddings (default for VectorStoreIndex) |
| `BM25Retriever` | Keyword-based retrieval using BM25 scoring |
| `AutoMergingRetriever` | Merges child nodes into parent when threshold is met |
| `RecursiveRetriever` | Recursively retrieves through node references |
| `RouterRetriever` | Routes queries to appropriate sub-retrievers |
| `QueryFusionRetriever` | Generates multiple queries, fuses results |
| `EnsembleRetriever` | Combines results from multiple retrievers |

### Hybrid Retrieval (Vector + BM25)

```python
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.retrievers import QueryFusionRetriever

vector_retriever = index.as_retriever(similarity_top_k=5)
bm25_retriever = BM25Retriever.from_defaults(
    nodes=nodes, similarity_top_k=5
)

hybrid_retriever = QueryFusionRetriever(
    retrievers=[vector_retriever, bm25_retriever],
    similarity_top_k=10,
    num_queries=1,
    mode="reciprocal_rerank",
)
```

## Response Synthesizers

Transform retrieved nodes into a final response:

```python
from llama_index.core.response_synthesizers import get_response_synthesizer

synthesizer = get_response_synthesizer(
    response_mode="tree_summarize",
    streaming=True,
)

response = synthesizer.synthesize(
    query="Summarize the findings.",
    nodes=retrieved_nodes,
)
```

### Custom Prompts

```python
from llama_index.core import PromptTemplate

custom_prompt = PromptTemplate(
    "Context:\n{context_str}\n\n"
    "Using the context above, answer: {query_str}\n"
    "Answer in bullet points."
)

query_engine = index.as_query_engine(
    text_qa_template=custom_prompt,
)
```

## Node Postprocessors

Transform, filter, or re-rank nodes after retrieval but before synthesis:

```python
from llama_index.core.postprocessor import (
    SimilarityPostprocessor,
    KeywordNodePostprocessor,
)

query_engine = index.as_query_engine(
    node_postprocessors=[
        SimilarityPostprocessor(similarity_cutoff=0.7),
        KeywordNodePostprocessor(required_keywords=["revenue"]),
    ],
)
```

### Available Postprocessors

| Postprocessor | Purpose |
|---------------|---------|
| `SimilarityPostprocessor` | Filter by minimum similarity score |
| `KeywordNodePostprocessor` | Filter by required/excluded keywords |
| `MetadataReplacementPostProcessor` | Replace node text with metadata value |
| `LongContextReorder` | Reorder nodes for long-context models |
| `SentenceTransformerRerank` | Re-rank using a cross-encoder model |
| `CohereRerank` | Re-rank using Cohere's reranking API |
| `LLMRerank` | Re-rank using an LLM as judge |
| `TimeWeightedPostprocessor` | Bias toward more recent nodes |

### Re-ranking Example

```python
from llama_index.postprocessor.cohere_rerank import CohereRerank

reranker = CohereRerank(
    api_key="...",
    top_n=5,
)

query_engine = index.as_query_engine(
    similarity_top_k=20,
    node_postprocessors=[reranker],
)
```

Retrieve broadly (top_k=20), then re-rank to the top 5 most relevant.

## Routers

Route queries to different query engines or retrievers based on the query:

```python
from llama_index.core.query_engine import RouterQueryEngine
from llama_index.core.selectors import LLMSingleSelector
from llama_index.core.tools import QueryEngineTool

tools = [
    QueryEngineTool.from_defaults(
        query_engine=financial_engine,
        description="Answers questions about financial data.",
    ),
    QueryEngineTool.from_defaults(
        query_engine=technical_engine,
        description="Answers questions about technical specs.",
    ),
]

router_engine = RouterQueryEngine(
    selector=LLMSingleSelector.from_defaults(),
    query_engine_tools=tools,
)
```

## Structured Output

Force query engine responses into Pydantic models:

```python
from pydantic import BaseModel
from llama_index.core.query_engine import RetrieverQueryEngine

class AnalysisResult(BaseModel):
    summary: str
    confidence: float
    key_points: list[str]

query_engine = index.as_query_engine(
    response_mode="compact",
    output_cls=AnalysisResult,
)
response = query_engine.query("Analyze the report.")
```

## Streaming

### Streaming Query Engine

```python
query_engine = index.as_query_engine(streaming=True)
response = query_engine.query("Explain the concept.")
response.print_response_stream()
```

### Async Queries

```python
response = await query_engine.aquery("What happened?")
```

## Common Patterns

### Sub-Question Query Engine

Decomposes complex queries into sub-questions across multiple data sources:

```python
from llama_index.core.query_engine import SubQuestionQueryEngine
from llama_index.core.tools import QueryEngineTool

tools = [
    QueryEngineTool.from_defaults(engine, description="...") 
    for engine in engines
]
sub_question_engine = SubQuestionQueryEngine.from_defaults(
    query_engine_tools=tools,
)
```

### Citation Query Engine

Returns responses with source citations:

```python
from llama_index.core.query_engine import CitationQueryEngine

citation_engine = CitationQueryEngine.from_args(index, similarity_top_k=5)
response = citation_engine.query("What are the findings?")
print(response.source_nodes)
```
