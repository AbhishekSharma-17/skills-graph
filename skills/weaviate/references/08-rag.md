# Weaviate — RAG (Generative Search)

> Source: [docs.weaviate.io](https://docs.weaviate.io/weaviate/search/generative) | Version: v1.37

## Table of Contents
- [Overview](#overview)
- [Generative Model Configuration](#generative-model-configuration)
- [Single Prompt (Per-Object)](#single-prompt-per-object)
- [Grouped Task (All Objects)](#grouped-task-all-objects)
- [Property Interpolation](#property-interpolation)
- [Named Vectors](#named-vectors)
- [Multimodal RAG (Images)](#multimodal-rag-images)
- [Advanced Parameters](#advanced-parameters)
- [Combining with Search Types](#combining-with-search-types)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

Retrieval Augmented Generation (RAG) in Weaviate is a two-step process:

1. **Retrieve**: Execute a search (vector, keyword, or hybrid) to find relevant objects
2. **Generate**: Pass the retrieved objects + a custom prompt to a generative LLM

This is Weaviate's built-in RAG pipeline — no external orchestration needed.

```
Query → Search (retrieve objects) → LLM (generate response) → Result
```

Two modes:
- **Single prompt**: Generates one response per retrieved object
- **Grouped task**: Generates one response for all retrieved objects combined

## Generative Model Configuration

### At Collection Creation

```python
from weaviate.classes.config import Configure

client.collections.create(
    "Article",
    vector_config=Configure.Vectors.text2vec_openai(),
    generative_config=Configure.Generative.openai(model="gpt-4o"),
    properties=[...],
)
```

### At Query Time (v1.30+)

Override the collection's default generative model per query:

```python
from weaviate.classes.generate import GenerativeConfig

response = articles.generate.near_text(
    query="AI breakthroughs",
    limit=3,
    single_prompt="Summarize: {title} — {body}",
    generative_provider=GenerativeConfig.openai(model="gpt-4o-mini"),
)
```

### Supported Providers

```python
Configure.Generative.openai(model="gpt-4o")
Configure.Generative.anthropic(model="claude-sonnet-4-20250514")
Configure.Generative.cohere(model="command-r-plus")
Configure.Generative.google(model="gemini-1.5-pro")
Configure.Generative.aws(model="...")
Configure.Generative.mistral(model="mistral-large-latest")
Configure.Generative.ollama(model="llama3")
```

## Single Prompt (Per-Object)

Generates a separate response for each retrieved object. Use `{property_name}` to interpolate object data into the prompt.

### Python

```python
articles = client.collections.use("Article")
response = articles.generate.near_text(
    query="AI developments",
    limit=3,
    single_prompt="Write a tweet about this article: {title}. Key point: {body}",
)

for obj in response.objects:
    print(f"Original: {obj.properties['title']}")
    print(f"Generated: {obj.generated}")
    print()
```

### TypeScript

```typescript
const articles = client.collections.use('Article');
const result = await articles.generate.nearText('AI developments', {
  singlePrompt: 'Write a tweet about this article: {title}. Key point: {body}',
}, { limit: 3 });

for (const obj of result.objects) {
  console.log(`Original: ${obj.properties.title}`);
  console.log(`Generated: ${obj.generated}`);
}
```

## Grouped Task (All Objects)

Generates a single response using all retrieved objects as context.

### Python

```python
response = articles.generate.near_text(
    query="AI developments",
    limit=5,
    grouped_task="Summarize the key themes across these articles in 3 bullet points.",
)

print(response.generated)  # Single combined response
```

### TypeScript

```typescript
const result = await articles.generate.nearText('AI developments', {
  groupedTask: 'Summarize the key themes across these articles in 3 bullet points.',
}, { limit: 5 });

console.log(result.generated);
```

### Limit Properties Sent to LLM

Reduce token usage by specifying which properties to include:

```python
response = articles.generate.near_text(
    query="AI developments",
    limit=5,
    grouped_task="What do these articles have in common?",
    grouped_properties=["title", "category"],  # Only send these to the LLM
)
```

## Property Interpolation

Use `{property_name}` in prompts to inject object data:

```python
prompt = """
Article: {title}
Category: {category}
Content: {body}

Generate 3 quiz questions based on this article.
"""

response = articles.generate.near_text(
    query="science",
    limit=3,
    single_prompt=prompt,
)
```

Properties used in prompts don't need to be in the return properties — Weaviate resolves them separately.

## Named Vectors

Specify the target vector for the search component:

```python
reviews = client.collections.use("ProductReview")
response = reviews.generate.near_text(
    query="excellent battery life",
    target_vector="review_vector",
    limit=3,
    single_prompt="Rate this review's sentiment (positive/neutral/negative): {review_body}",
)
```

## Multimodal RAG (Images)

Send images alongside text to vision-capable models:

```python
import base64
import requests
from weaviate.classes.generate import GenerativeConfig, GenerativeParameters

image_url = "https://example.com/photo.jpg"
base64_image = base64.b64encode(requests.get(image_url).content).decode("utf-8")

prompt = GenerativeParameters.grouped_task(
    prompt="Describe what you see in this image and relate it to the search results.",
    images=[base64_image],
)

response = articles.generate.near_text(
    query="nature photography",
    limit=3,
    grouped_task=prompt,
    generative_provider=GenerativeConfig.anthropic(model="claude-sonnet-4-20250514"),
)
```

### Image Properties from Weaviate

```python
prompt = GenerativeParameters.grouped_task(
    prompt="Compare the images stored in these objects.",
    image_properties=["thumbnail"],  # Property name storing images
)
```

## Advanced Parameters

### Debug Mode (v1.30+)

Inspect the full prompt sent to the LLM and token usage:

```python
from weaviate.classes.generate import GenerativeParameters

prompt = GenerativeParameters.single_prompt(
    prompt="Summarize: {title}",
    metadata=True,   # Return token usage
    debug=True,       # Return full prompt
)

response = articles.generate.near_text(
    query="AI",
    limit=3,
    single_prompt=prompt,
)
```

### Combined Single + Grouped

Run both modes in one query:

```python
response = articles.generate.near_text(
    query="AI developments",
    limit=3,
    single_prompt="Write a one-line summary: {title}",
    grouped_task="What's the overall trend across these articles?",
)

# Per-object summaries
for obj in response.objects:
    print(obj.generated)

# Combined analysis
print(response.generated)
```

## Combining with Search Types

RAG works with all search types via the `generate` namespace:

```python
# Vector search + RAG
articles.generate.near_text(query="AI", limit=3, grouped_task="Summarize these.")

# BM25 keyword search + RAG
articles.generate.bm25(query="deep learning", limit=3, grouped_task="Summarize these.")

# Hybrid search + RAG
articles.generate.hybrid(query="AI trends", limit=3, alpha=0.75,
                         grouped_task="Summarize these.")

# Near vector + RAG
articles.generate.near_vector(near_vector=[...], limit=3,
                              grouped_task="Summarize these.")

# Fetch by filter + RAG
from weaviate.classes.query import Filter
articles.generate.fetch_objects(
    filters=Filter.by_property("category").equal("tech"),
    limit=5,
    grouped_task="What themes emerge from these?",
)
```

## Common Pitfalls

1. **No generative config**: RAG queries fail if no generative model is configured on the collection and none is provided at query time. Always set `generative_config` on the collection or pass `generative_provider` in the query.

2. **Token limits**: Grouped tasks send all object properties to the LLM. With many objects or large text properties, you hit context limits. Use `grouped_properties` to limit what's sent.

3. **Missing API key**: The generative model's API key must be in the connection headers (e.g., `X-OpenAI-Api-Key`). Missing keys produce authentication errors.

4. **Single vs grouped confusion**: `single_prompt` generates per-object (N responses). `grouped_task` generates one response for all objects. Using `single_prompt` when you want a summary wastes tokens.

5. **Cost awareness**: Every RAG query makes an LLM API call. Grouped tasks with many objects or large text can be expensive. Monitor usage with `metadata=True`.

## Related Topics

- Similarity Search → `04-similarity-search.md`
- Hybrid Search → `06-hybrid-search.md`
- Model Providers → `11-model-providers.md`
- Weaviate Agents → `12-agents.md`
