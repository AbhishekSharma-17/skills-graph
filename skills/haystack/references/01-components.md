# Haystack Components

> Source: [docs.haystack.deepset.ai/docs/components](https://docs.haystack.deepset.ai/docs/components) | haystack-ai 2.30.0

## Table of Contents

- [What Are Components](#what-are-components)
- [Component Protocol](#component-protocol)
- [Creating Custom Components](#creating-custom-components)
- [Input and Output Types](#input-and-output-types)
- [Component Lifecycle](#component-lifecycle)
- [Component Serialization](#component-serialization)
- [Extending Existing Components](#extending-existing-components)
- [Built-in Component Categories](#built-in-component-categories)
- [Common Pitfalls](#common-pitfalls)

## What Are Components

Components are the building blocks of Haystack pipelines. Each component performs a specific task — retrieving documents, embedding text, generating responses, converting files, or routing data. Components can run standalone or be connected in pipelines.

Key properties:
- Each has a `run()` method with typed inputs and outputs
- Inputs/outputs are validated at connection time (before execution)
- Components can have initialization parameters and runtime parameters
- Resources like models are loaded lazily via `warm_up()`

## Component Protocol

Every Haystack component must:

1. Be decorated with `@component`
2. Implement a `run()` method that returns a `dict`
3. Declare output types via `@component.output_types()` or `set_output_types()`

```python
from haystack import component

@component
class TextLengthCalculator:
    @component.output_types(length=int, is_long=bool)
    def run(self, text: str):
        length = len(text)
        return {"length": length, "is_long": length > 100}
```

## Creating Custom Components

### Basic Component

```python
from haystack import component

@component
class WelcomeTextGenerator:
    def __init__(self, prefix: str = "Hello"):
        self.prefix = prefix

    @component.output_types(welcome_text=str, note=str)
    def run(self, name: str):
        return {
            "welcome_text": f"{self.prefix}, {name}!".upper(),
            "note": "message ready",
        }
```

### Component with Optional Inputs

Use default values in `run()` to make inputs optional:

```python
@component
class Summarizer:
    @component.output_types(summary=str)
    def run(self, text: str, max_length: int = 100):
        return {"summary": text[:max_length]}
```

### Component with Dynamic Inputs

Use `set_input_type()` or `set_input_types()` for runtime-configured inputs:

```python
@component
class DynamicMerger:
    def __init__(self, inputs: list[str]):
        for input_name in inputs:
            component.set_input_type(self, input_name, str)

    @component.output_types(merged=str)
    def run(self, **kwargs):
        return {"merged": " ".join(kwargs.values())}
```

### Component with Dynamic Outputs

Use `set_output_types()` when outputs depend on initialization:

```python
@component
class DynamicRouter:
    def __init__(self, routes: list[str]):
        self.routes = routes
        component.set_output_types(
            self, **{route: str for route in routes}
        )

    def run(self, text: str, route: str):
        return {route: text}
```

## Input and Output Types

### Declaring Outputs

Two approaches:

```python
# Static (preferred) — decorator
@component
class Foo:
    @component.output_types(result=str, score=float)
    def run(self, text: str):
        return {"result": text.upper(), "score": 1.0}

# Dynamic — method call in __init__
@component
class Bar:
    def __init__(self, output_names: list[str]):
        component.set_output_types(
            self, **{name: str for name in output_names}
        )

    def run(self, text: str):
        ...
```

### Type Compatibility

Pipeline connections validate types at connection time. Compatible types include:
- Exact matches: `str → str`, `list[Document] → list[Document]`
- Greedy variadic inputs accept multiple connections of the same type
- Optional types: `Optional[str]` accepts `str` or `None`

## Component Lifecycle

### Initialization (`__init__`)

Set parameters, configure the component. No heavy resources here:

```python
@component
class MyRetriever:
    def __init__(self, top_k: int = 10, model_name: str = "default"):
        self.top_k = top_k
        self.model_name = model_name
```

### Warm-Up (`warm_up`)

Load models, establish connections. Called once before first `run()`:

```python
@component
class EmbedderComponent:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = None

    def warm_up(self):
        if self.model is None:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)

    @component.output_types(embedding=list[float])
    def run(self, text: str):
        return {"embedding": self.model.encode(text).tolist()}
```

### Execution (`run`)

Process inputs, return outputs as a dict. Called every pipeline execution:

```python
@component.output_types(result=str)
def run(self, text: str) -> dict[str, str]:
    return {"result": text.strip().lower()}
```

## Component Serialization

Components support `to_dict()` and `from_dict()` for YAML pipeline serialization:

```python
@component
class ConfigurableComponent:
    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold

    def to_dict(self):
        return {
            "type": "my_module.ConfigurableComponent",
            "init_parameters": {"threshold": self.threshold},
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data["init_parameters"])
```

Default serialization handles most cases automatically. Override only when you have non-serializable init parameters.

## Extending Existing Components

Subclass with the `@component` decorator:

```python
from haystack.components.generators.chat import OpenAIChatGenerator

@component
class LoggingGenerator(OpenAIChatGenerator):
    def __init__(self, **kwargs):
        super(LoggingGenerator, self).__init__(**kwargs)

    @component.output_types(replies=list)
    def run(self, messages, **kwargs):
        print(f"Generating with {len(messages)} messages")
        return super().run(messages=messages, **kwargs)
```

**Important**: Use `super(DerivedClass, self).__init__()` syntax to avoid initialization errors.

## Built-in Component Categories

| Category | Examples | Purpose |
|----------|----------|---------|
| Generators | `OpenAIChatGenerator`, `AnthropicChatGenerator` | LLM text generation |
| Embedders | `OpenAIDocumentEmbedder`, `SentenceTransformersTextEmbedder` | Vector embeddings |
| Retrievers | `InMemoryBM25Retriever`, `QdrantEmbeddingRetriever` | Document retrieval |
| Converters | `PyPDFToDocument`, `HTMLToDocument` | File format conversion |
| Preprocessors | `DocumentSplitter`, `DocumentCleaner` | Text preprocessing |
| Routers | `ConditionalRouter`, `FileTypeRouter` | Conditional data flow |
| Builders | `PromptBuilder`, `ChatPromptBuilder` | Prompt construction |
| Writers | `DocumentWriter` | Writing to document stores |
| Joiners | `DocumentJoiner`, `BranchJoiner` | Merging pipeline branches |
| Evaluators | `FaithfulnessEvaluator`, `SASEvaluator` | Pipeline evaluation |
| Agent | `Agent` | Autonomous tool-calling agent |
| Tools | `ToolInvoker` | Tool execution in pipelines |

## Common Pitfalls

**Mutating inputs directly**: Always work on copies to avoid side effects:

```python
# Bad — modifies the input document in place
def run(self, documents: list[Document]):
    for doc in documents:
        doc.content = doc.content.upper()  # Affects other components!
    return {"documents": documents}

# Good — use dataclasses.replace() or deepcopy
import dataclasses

def run(self, documents: list[Document]):
    return {
        "documents": [
            dataclasses.replace(doc, content=doc.content.upper())
            for doc in documents
        ]
    }
```

**Missing `@component` decorator**: Without it, the class can't be used in pipelines.

**Forgetting output type declaration**: Either `@component.output_types()` or `set_output_types()` is required.

**Heavy initialization in `__init__`**: Load models in `warm_up()`, not `__init__()`. This keeps component creation fast and enables serialization.

## Related Topics

- Pipelines → `02-pipelines.md`
- Custom components in pipelines → `02-pipelines.md`
- Built-in generators → `05-generators.md`
- Built-in retrievers → `06-retrievers.md`
