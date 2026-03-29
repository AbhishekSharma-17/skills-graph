# Prompt Management

> Source: [langfuse.com/docs/prompt-management](https://langfuse.com/docs/prompt-management/overview)

## Table of Contents

- [Overview](#overview)
- [Core Concepts](#core-concepts)
- [Creating Prompts](#creating-prompts)
- [Retrieving Prompts](#retrieving-prompts)
- [Template Variables](#template-variables)
- [Versioning](#versioning)
- [Labels and Deployment](#labels-and-deployment)
- [Linking Prompts to Traces](#linking-prompts-to-traces)
- [Caching](#caching)
- [REST API](#rest-api)
- [Common Patterns](#common-patterns)
- [Pitfalls](#pitfalls)

---

## Overview

Langfuse prompt management decouples prompt iteration from code deployment. Store, version, and retrieve prompts via UI or SDK — allowing product teams to iterate on prompts without engineering deploys.

Key benefits:
- **Version history** — every edit creates a new version
- **Labels** — promote versions to production/staging without code changes
- **Zero latency** — client-side caching means prompt retrieval is instant
- **Traceability** — link prompts to traces to measure each version's performance
- **Collaboration** — non-engineers can edit prompts via the UI

## Core Concepts

### Prompt Types

| Type | Format | Use Case |
|------|--------|----------|
| `text` | String with `{{variables}}` | Single-prompt templates |
| `chat` | Array of `{role, content}` messages | Chat-based templates |

Prompt type is set at creation and cannot be changed afterward.

### Prompt Lifecycle

1. Create prompt in UI or via SDK
2. Iterate by creating new versions
3. Test with experiments/datasets
4. Promote to "production" label
5. SDK fetches the labeled version
6. Monitor performance via linked traces

## Creating Prompts

### Python SDK

```python
from langfuse import get_client

langfuse = get_client()

# Text prompt
langfuse.create_prompt(
    name="qa-prompt",
    type="text",
    prompt="You are a helpful assistant. Answer the question: {{question}}\n\nContext: {{context}}",
    labels=["staging"],
)

# Chat prompt
langfuse.create_prompt(
    name="chat-system",
    type="chat",
    prompt=[
        {"role": "system", "content": "You are {{persona}}. Be {{tone}}."},
        {"role": "user", "content": "{{user_message}}"},
    ],
    labels=["production"],
)
```

### TypeScript SDK

```typescript
import { LangfuseClient } from "@langfuse/client";

const langfuse = new LangfuseClient();

await langfuse.prompt.create({
  name: "qa-prompt",
  type: "text",
  prompt: "Answer: {{question}}\nContext: {{context}}",
  labels: ["production"],
});
```

### Creating via UI

1. Navigate to **Prompts** in the sidebar
2. Click **New Prompt**
3. Select type (text or chat)
4. Write the prompt with `{{variable}}` placeholders
5. Add labels (e.g., "production")
6. Save — version 1 is created

## Retrieving Prompts

### Python

```python
# Get the prompt with a specific label (default: "production")
prompt = langfuse.get_prompt("qa-prompt")
prompt = langfuse.get_prompt("qa-prompt", label="staging")

# Get a specific version
prompt = langfuse.get_prompt("qa-prompt", version=3)

# Compile with variables
compiled = prompt.compile(
    question="What is Langfuse?",
    context="Langfuse is an LLM observability platform.",
)
# Returns: "Answer: What is Langfuse?\nContext: Langfuse is an LLM observability platform."
```

### TypeScript

```typescript
const prompt = await langfuse.prompt.get("qa-prompt");
const compiled = prompt.compile({
  question: "What is Langfuse?",
  context: "Langfuse is an LLM observability platform.",
});
```

## Template Variables

Variables use double-brace syntax: `{{variableName}}`

```python
prompt_text = "As a {{role}}, answer about {{topic}} in {{language}}."

compiled = prompt.compile(
    role="expert",
    topic="machine learning",
    language="Spanish",
)
# "As a expert, answer about machine learning in Spanish."
```

Variable names: alphanumeric + underscores. Case-sensitive.

## Versioning

Every prompt edit creates a new version (auto-incrementing integer):
- Version 1: Initial creation
- Version 2: First edit
- Version N: Nth edit

Retrieve specific versions:

```python
# Latest version (any label)
prompt = langfuse.get_prompt("my-prompt")

# Specific version
prompt = langfuse.get_prompt("my-prompt", version=5)

# Version with specific label
prompt = langfuse.get_prompt("my-prompt", label="production")
```

## Labels and Deployment

Labels control which prompt version is served to your application. Common labels:

| Label | Purpose |
|-------|---------|
| `production` | Live traffic |
| `staging` | Pre-production testing |
| `latest` | Most recent version (auto-assigned) |

### Deployment Workflow

1. Create/edit prompt → new version created
2. Test the new version with experiments
3. If satisfied, add "production" label to the new version
4. SDK automatically fetches the new production version (after cache expires)

```python
# Your code always fetches "production" — no code change needed
prompt = langfuse.get_prompt("qa-prompt", label="production")
```

Moving labels between versions is instant in the UI — no deploy needed.

## Linking Prompts to Traces

Connect prompt usage to traces for performance tracking:

```python
@observe(as_type="generation")
def generate_answer(question: str) -> str:
    prompt = langfuse.get_prompt("qa-prompt")
    compiled = prompt.compile(question=question)

    langfuse.update_current_generation(
        prompt=prompt,  # Links this generation to the prompt version
    )

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": compiled}],
    )
    return response.choices[0].message.content
```

In the Langfuse UI:
- See which prompt version was used for each trace
- Compare metrics across prompt versions
- Filter dashboards by prompt name/version

## Caching

The SDK caches prompts client-side for performance:

- Default cache TTL: configurable (typically 60 seconds)
- Cache is in-memory — no external cache needed
- Cache miss triggers a background refresh
- Your app never blocks on prompt fetch after the first load

```python
# Configure cache TTL
langfuse = Langfuse(prompt_cache_ttl_seconds=300)  # 5 minutes
```

## REST API

### Create/Update Prompt

```
POST /api/public/v2/prompts
Content-Type: application/json
Authorization: Basic <base64(public:secret)>

{
  "name": "my-prompt",
  "type": "text",
  "prompt": "Hello {{name}}!",
  "labels": ["production"]
}
```

### Fetch Prompt

```
GET /api/public/v2/prompts/{promptName}?label=production
GET /api/public/v2/prompts/{promptName}?version=1
```

## Common Patterns

### Prompt A/B Testing

```python
import random

@observe()
def ab_test_prompt(query: str) -> str:
    variant = "variant-a" if random.random() < 0.5 else "variant-b"
    prompt = langfuse.get_prompt("qa-prompt", label=variant)
    compiled = prompt.compile(question=query)

    langfuse.update_current_generation(prompt=prompt)

    # Trace automatically tagged with prompt version
    return call_llm(compiled)
```

### Environment-Based Labels

```python
import os

env = os.getenv("ENVIRONMENT", "staging")
prompt = langfuse.get_prompt("qa-prompt", label=env)
```

## Pitfalls

1. **Changing prompt type** — Once created as "text", a prompt cannot be changed to "chat" (or vice versa). Create a new prompt with the correct type.

2. **Variable typos** — `{{variabel}}` vs `{{variable}}` will silently leave the placeholder uncompiled. Double-check variable names.

3. **Cache staleness** — After promoting a new version to "production", it takes up to the cache TTL for the SDK to pick it up. Reduce TTL for faster propagation, or restart your app.

4. **Large prompt payloads** — Very long prompts (>50KB) may add noticeable latency on cache miss. Keep prompts focused and split complex templates.
