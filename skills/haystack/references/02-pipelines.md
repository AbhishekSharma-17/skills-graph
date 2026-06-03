# Haystack Pipelines

> Source: [docs.haystack.deepset.ai/docs/pipelines](https://docs.haystack.deepset.ai/docs/pipelines) | haystack-ai 2.30.0

## Table of Contents

- [What Are Pipelines](#what-are-pipelines)
- [Creating a Pipeline](#creating-a-pipeline)
- [Connecting Components](#connecting-components)
- [Running Pipelines](#running-pipelines)
- [Pipeline Branching](#pipeline-branching)
- [Pipeline Loops](#pipeline-loops)
- [Async Pipelines](#async-pipelines)
- [Pipeline Serialization](#pipeline-serialization)
- [Pipeline Validation](#pipeline-validation)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## What Are Pipelines

Pipelines are directed multigraphs of Haystack components. They define data flow between components, support branching, loops, and conditional routing, and handle validation and execution ordering automatically.

Key properties:
- Components added in any order — connections define the graph
- Type-safe connections validated at build time
- Data flows only between connected components (no global state)
- Support both synchronous and asynchronous execution

## Creating a Pipeline

Four steps: instantiate, add components, connect, run.

```python
from haystack import Pipeline
from haystack.components.converters import TextFileToDocument
from haystack.components.preprocessors import DocumentCleaner, DocumentSplitter

pipe = Pipeline()

# Step 1: Add components (order doesn't matter)
pipe.add_component("converter", TextFileToDocument())
pipe.add_component("cleaner", DocumentCleaner())
pipe.add_component("splitter", DocumentSplitter(split_by="sentence", split_length=3))

# Step 2: Connect components
pipe.connect("converter", "cleaner")
pipe.connect("cleaner", "splitter")

# Step 3: Run
result = pipe.run({"converter": {"sources": ["data/article.txt"]}})
```

## Connecting Components

### Basic Connection

When a component has a single output and the next has a single matching input:

```python
pipe.connect("converter", "cleaner")
```

### Explicit Input/Output Names

When components have multiple inputs or outputs:

```python
pipe.connect("retriever.documents", "prompt.documents")
pipe.connect("prompt.prompt", "llm.messages")
```

Format: `"component_name.output_name"` → `"component_name.input_name"`

### Multiple Connections from One Output

A single output can feed multiple components (fanout):

```python
pipe.connect("splitter.documents", "embedder.documents")
pipe.connect("splitter.documents", "writer.documents")
```

### Greedy Variadic Inputs

Some inputs accept connections from multiple sources and consume data as it arrives:

```python
pipe.connect("bm25_retriever.documents", "joiner.documents")
pipe.connect("embedding_retriever.documents", "joiner.documents")
```

## Running Pipelines

### Basic Execution

Pass inputs as a dict mapping component names to their input values:

```python
result = pipe.run({
    "retriever": {"query": "What is Haystack?"},
    "prompt": {"query": "What is Haystack?"},
})
```

### Accessing Outputs

Results are a dict mapping component names to their outputs:

```python
# Access the last component's output
answer = result["llm"]["replies"][0].text

# Access intermediate results (if component is a pipeline output)
documents = result["retriever"]["documents"]
```

### Passing Extra Parameters

Override component defaults at runtime:

```python
result = pipe.run({
    "retriever": {"query": "Haystack", "top_k": 5},
    "llm": {"generation_kwargs": {"temperature": 0.7}},
})
```

## Pipeline Branching

### Parallel Branches

Use routers to split data flow across branches:

```python
from haystack.components.routers import FileTypeRouter
from haystack.components.converters import (
    PyPDFToDocument,
    HTMLToDocument,
    MarkdownToDocument,
)
from haystack.components.joiners import DocumentJoiner

pipe = Pipeline()
pipe.add_component("router", FileTypeRouter(
    mime_types=["application/pdf", "text/html", "text/markdown"]
))
pipe.add_component("pdf_converter", PyPDFToDocument())
pipe.add_component("html_converter", HTMLToDocument())
pipe.add_component("md_converter", MarkdownToDocument())
pipe.add_component("joiner", DocumentJoiner())

pipe.connect("router.application/pdf", "pdf_converter")
pipe.connect("router.text/html", "html_converter")
pipe.connect("router.text/markdown", "md_converter")
pipe.connect("pdf_converter", "joiner")
pipe.connect("html_converter", "joiner")
pipe.connect("md_converter", "joiner")
```

### Conditional Routing

Use `ConditionalRouter` with Jinja2 conditions:

```python
from haystack.components.routers import ConditionalRouter

routes = [
    {
        "condition": "{{ documents|length > 0 }}",
        "output": "has_docs",
        "output_name": "has_docs",
        "output_type": list[Document],
    },
    {
        "condition": "{{ documents|length == 0 }}",
        "output": "{{ query }}",
        "output_name": "no_docs",
        "output_type": str,
    },
]

pipe.add_component("router", ConditionalRouter(routes=routes))
```

## Pipeline Loops

Components can loop back for iterative processing. Useful for self-correcting pipelines:

```python
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.components.validators import JsonSchemaValidator

pipe = Pipeline()
pipe.add_component("generator", OpenAIChatGenerator())
pipe.add_component("validator", JsonSchemaValidator(json_schema=my_schema))

pipe.connect("generator.replies", "validator.messages")
# Loop back on validation failure
pipe.connect("validator.validation_error", "generator.messages")
```

The pipeline runs the loop until the validator passes or `max_runs_per_component` is reached (default: 100).

### Setting Loop Limits

```python
pipe = Pipeline(max_runs_per_component=5)
```

## Async Pipelines

Use `AsyncPipeline` for parallel component execution:

```python
from haystack import AsyncPipeline

pipe = AsyncPipeline()
pipe.add_component("embedder", OpenAITextEmbedder())
pipe.add_component("retriever", QdrantEmbeddingRetriever(document_store=store))

pipe.connect("embedder", "retriever")

# Async execution
result = await pipe.run_async({
    "embedder": {"text": "What is Haystack?"}
})
```

`AsyncPipeline` runs independent components in parallel — if two components have no data dependency, they execute concurrently. Particularly useful for I/O-bound operations like API calls.

## Pipeline Serialization

### Save to YAML

```python
pipe_yaml = pipe.dumps()  # Returns YAML string
pipe.dump(open("pipeline.yaml", "w"))  # Write to file
```

### Load from YAML

```python
pipe = Pipeline.loads(yaml_string)  # From string
pipe = Pipeline.load(open("pipeline.yaml"))  # From file
```

### Dict Round-Trip

```python
pipe_dict = pipe.to_dict()
restored = Pipeline.from_dict(pipe_dict)
```

Serialization captures the full pipeline graph — component types, init parameters, and connections. Custom components need `to_dict()`/`from_dict()` methods for serialization.

## Pipeline Validation

Validation runs at connection time and catches:

- Component doesn't exist in the pipeline
- Output/input type mismatches
- Missing required inputs
- Circular dependencies without proper exit conditions

```python
# This raises a PipelineValidationError if types don't match
pipe.connect("embedder.embedding", "retriever.query_embedding")
```

Error messages are detailed and suggest fixes.

## Common Patterns

### RAG Pipeline

```python
pipe = Pipeline()
pipe.add_component("retriever", InMemoryBM25Retriever(document_store=store))
pipe.add_component("prompt", ChatPromptBuilder(template=rag_template))
pipe.add_component("llm", OpenAIChatGenerator())

pipe.connect("retriever.documents", "prompt.documents")
pipe.connect("prompt", "llm")
```

### Indexing Pipeline

```python
pipe = Pipeline()
pipe.add_component("converter", PyPDFToDocument())
pipe.add_component("splitter", DocumentSplitter(split_by="word", split_length=200))
pipe.add_component("embedder", OpenAIDocumentEmbedder())
pipe.add_component("writer", DocumentWriter(document_store=store))

pipe.connect("converter", "splitter")
pipe.connect("splitter", "embedder")
pipe.connect("embedder", "writer")
```

### Hybrid Retrieval

```python
pipe = Pipeline()
pipe.add_component("bm25", InMemoryBM25Retriever(document_store=store))
pipe.add_component("embedding", InMemoryEmbeddingRetriever(document_store=store))
pipe.add_component("joiner", DocumentJoiner())

pipe.connect("bm25", "joiner")
pipe.connect("embedding", "joiner")
```

## Common Pitfalls

**Forgetting to connect components**: Added but unconnected components are silently ignored.

**Passing wrong input structure to `run()`**: Inputs must be nested under component names:

```python
# Wrong
pipe.run({"query": "hello"})

# Right
pipe.run({"retriever": {"query": "hello"}})
```

**Not providing all required inputs**: If a component has required inputs with no defaults and no incoming connections, you must provide them in `run()`.

**Infinite loops**: Without `max_runs_per_component`, loops can run indefinitely. Always set a reasonable limit.

## Related Topics

- Components → `01-components.md`
- Agents (pipeline-based) → `03-agents.md`
- RAG patterns → `11-rag-patterns.md`
- Prompt building → `10-prompt-building.md`
