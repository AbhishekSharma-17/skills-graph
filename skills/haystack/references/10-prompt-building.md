# Haystack Prompt Building & Routing

> Source: [docs.haystack.deepset.ai/docs/promptbuilder](https://docs.haystack.deepset.ai/docs/promptbuilder) | haystack-ai 2.30.0

## Table of Contents

- [PromptBuilder](#promptbuilder)
- [ChatPromptBuilder](#chatpromptbuilder)
- [Jinja2 Templating](#jinja2-templating)
- [Template Variables](#template-variables)
- [Routers](#routers)
- [ConditionalRouter](#conditionalrouter)
- [Other Router Types](#other-router-types)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## PromptBuilder

Renders Jinja2 templates into prompts for text generators:

```python
from haystack.components.builders import PromptBuilder

builder = PromptBuilder(
    template="""Answer the question based on the context.
Context:
{% for doc in documents %}
{{ doc.content }}
{% endfor %}

Question: {{ query }}
Answer:"""
)

result = builder.run(
    query="What is Haystack?",
    documents=retrieved_docs,
)
prompt = result["prompt"]  # Rendered string
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `template` | str | Jinja2 template string |
| `required_variables` | list[str] \| `"*"` | Variables that must be provided |
| `variables` | list[str] | All expected variables |

## ChatPromptBuilder

Builds chat message lists for chat generators. The primary prompt builder for modern Haystack:

```python
from haystack.components.builders import ChatPromptBuilder
from haystack.dataclasses import ChatMessage

builder = ChatPromptBuilder(
    template=[
        ChatMessage.from_system(
            "You are a helpful assistant. Answer based on these documents:\n"
            "{% for doc in documents %}\n- {{ doc.content }}\n{% endfor %}"
        ),
        ChatMessage.from_user("{{ query }}"),
    ]
)

result = builder.run(
    query="What is Haystack?",
    documents=retrieved_docs,
)
messages = result["prompt"]  # list[ChatMessage]
```

### With Custom System Prompt

```python
builder = ChatPromptBuilder(
    template=[
        ChatMessage.from_system(
            "You are an expert on {{ topic }}. "
            "Respond in {{ language }}. "
            "Be {{ tone }}."
        ),
        ChatMessage.from_user("{{ question }}"),
    ]
)

result = builder.run(
    topic="machine learning",
    language="English",
    tone="concise and technical",
    question="Explain transformers",
)
```

### Appending to Existing Messages

Pass conversation history and append new messages:

```python
builder = ChatPromptBuilder(
    template=[
        ChatMessage.from_user("{{ query }}"),
    ]
)

result = builder.run(
    query="Follow-up question",
    template_variables={
        "messages": existing_chat_history,  # Prepended automatically
    },
)
```

## Jinja2 Templating

Haystack uses Jinja2 for template rendering with full syntax support:

### Variables

```jinja2
{{ query }}
{{ doc.content }}
{{ doc.meta.source }}
```

### Loops

```jinja2
{% for doc in documents %}
Document {{ loop.index }}: {{ doc.content }}
{% endfor %}
```

### Conditionals

```jinja2
{% if documents %}
Context:
{% for doc in documents %}
- {{ doc.content }}
{% endfor %}
{% else %}
No relevant documents found.
{% endif %}
```

### Filters

```jinja2
{{ query | upper }}
{{ documents | length }}
{{ content | truncate(200) }}
```

### Time Extension

Haystack includes Jinja2's `TimeExtension` (requires `arrow>=1.3.0`):

```jinja2
{% now 'utc' as current_time %}
Current time: {{ current_time.strftime('%Y-%m-%d %H:%M:%S') }}
```

## Template Variables

### Required Variables

Force certain variables to be provided at runtime:

```python
builder = PromptBuilder(
    template="Answer: {{ query }} using {{ context }}",
    required_variables=["query"],  # "query" must be provided
)

# This works (query provided)
builder.run(query="Hello")

# This raises an error (query missing)
builder.run(context="some context")
```

Use `"*"` to make all variables required:

```python
builder = PromptBuilder(
    template="{{ query }} {{ context }}",
    required_variables="*",
)
```

### Runtime Template Override

Replace the template at runtime:

```python
builder = PromptBuilder(template="Default: {{ query }}")

# Override template for this run
result = builder.run(
    query="Hello",
    template="Custom: {{ query }} with {{ extra }}",
    extra="bonus info",
)
```

### template_variables

Dynamic overrides for variables within pipelines:

```python
result = builder.run(
    template_variables={"documents": my_docs},
    query="What is Haystack?",
)
```

## Routers

Routers direct data flow in pipelines based on conditions.

### Available Router Types

| Router | Purpose |
|--------|---------|
| `ConditionalRouter` | Route based on Jinja2 conditions |
| `FileTypeRouter` | Route by file MIME type |
| `DocumentTypeRouter` | Route documents by MIME type |
| `DocumentLengthRouter` | Route by document content length |
| `MetadataRouter` | Route by metadata field values |
| `TextLanguageRouter` | Route by detected language |
| `LLMMessagesRouter` | Route using LLM classification |
| `TransformersTextRouter` | Route using model categorization |
| `TransformersZeroShotTextRouter` | Route using zero-shot classification |

## ConditionalRouter

The most flexible router — uses Jinja2 conditions:

```python
from haystack.components.routers import ConditionalRouter

routes = [
    {
        "condition": "{{ documents | length > 0 }}",
        "output": "{{ documents }}",
        "output_name": "has_documents",
        "output_type": list[Document],
    },
    {
        "condition": "{{ documents | length == 0 }}",
        "output": "{{ query }}",
        "output_name": "no_documents",
        "output_type": str,
    },
]

router = ConditionalRouter(routes=routes)

pipe = Pipeline()
pipe.add_component("retriever", InMemoryBM25Retriever(document_store=store))
pipe.add_component("router", router)
pipe.add_component("rag_prompt", ChatPromptBuilder(template=rag_template))
pipe.add_component("fallback_prompt", ChatPromptBuilder(template=fallback_template))

pipe.connect("retriever.documents", "router.documents")
pipe.connect("router.has_documents", "rag_prompt.documents")
pipe.connect("router.no_documents", "fallback_prompt.query")
```

### FileTypeRouter

Route files to format-specific converters:

```python
from haystack.components.routers import FileTypeRouter

router = FileTypeRouter(
    mime_types=[
        "application/pdf",
        "text/html",
        "text/markdown",
        "text/plain",
    ]
)
# Outputs: router.application/pdf, router.text/html, etc.
# Unmatched files go to: router.unclassified
```

## Other Router Types

### MetadataRouter

```python
from haystack.components.routers import MetadataRouter

router = MetadataRouter(rules={
    "technical": {"field": "meta.category", "operator": "==", "value": "tech"},
    "general": {"field": "meta.category", "operator": "!=", "value": "tech"},
})
```

### TextLanguageRouter

```python
from haystack.components.routers import TextLanguageRouter

router = TextLanguageRouter(languages=["en", "de", "fr"])
# Outputs: router.en, router.de, router.fr, router.unmatched
```

### LLMMessagesRouter

Route using LLM classification:

```python
from haystack.components.routers import LLMMessagesRouter

router = LLMMessagesRouter(
    chat_generator=OpenAIChatGenerator(),
    routes={
        "question": "The user is asking a question",
        "command": "The user is giving a command",
        "chitchat": "The user is making small talk",
    },
)
```

## Common Patterns

### RAG with Fallback

```python
routes = [
    {
        "condition": "{{ documents | length > 0 }}",
        "output": "{{ documents }}",
        "output_name": "with_context",
        "output_type": list[Document],
    },
    {
        "condition": "{{ documents | length == 0 }}",
        "output": "'No relevant documents found. Answer from general knowledge.'",
        "output_name": "without_context",
        "output_type": str,
    },
]
```

### Multi-Language Pipeline

```python
pipe.add_component("lang_router", TextLanguageRouter(languages=["en", "de"]))
pipe.add_component("en_prompt", ChatPromptBuilder(template=english_template))
pipe.add_component("de_prompt", ChatPromptBuilder(template=german_template))

pipe.connect("lang_router.en", "en_prompt")
pipe.connect("lang_router.de", "de_prompt")
```

## Common Pitfalls

**Using PromptBuilder with ChatGenerator**: Chat generators need `ChatPromptBuilder`, not `PromptBuilder`. `PromptBuilder` outputs a string; `ChatPromptBuilder` outputs `list[ChatMessage]`.

**Undefined template variables**: Undefined variables render as empty strings silently. Use `required_variables` to catch missing inputs.

**Complex Jinja2 logic in templates**: Keep templates simple. Move complex logic into custom components instead of embedding it in Jinja2.

**ConditionalRouter conditions not exhaustive**: If no condition matches, data is dropped. Ensure conditions cover all cases or add a catch-all route.

## Related Topics

- Generators → `05-generators.md`
- Pipelines → `02-pipelines.md`
- RAG patterns → `11-rag-patterns.md`
