# Weaviate — Agents

> Source: [docs.weaviate.io](https://docs.weaviate.io/agents) | Version: v1.37

## Table of Contents
- [Overview](#overview)
- [Query Agent](#query-agent)
- [Query Agent Setup](#query-agent-setup)
- [Ask Mode](#ask-mode)
- [Search Mode](#search-mode)
- [Conversational Follow-Ups](#conversational-follow-ups)
- [Transformation Agent](#transformation-agent)
- [Transformation Setup](#transformation-setup)
- [Transform Operations](#transform-operations)
- [Personalization Agent](#personalization-agent)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

Weaviate Agents are pre-built agentic services that run on Weaviate Cloud. They use LLMs to translate natural language into database operations, eliminating the need to write explicit queries.

| Agent | Purpose | Status |
|-------|---------|--------|
| **Query Agent** | Natural language search and Q&A over your data | GA |
| **Transformation Agent** | Enrich and transform data in-place using LLMs | Technical Preview |
| **Personalization Agent** | Personalized recommendations based on user profiles | Technical Preview |

All agents require Weaviate Cloud — they are not available for self-hosted instances.

## Query Agent

The Query Agent translates natural language questions into Weaviate queries (vector, keyword, hybrid, filtered, aggregation), executes them, and returns synthesized answers.

```
User: "What are the top-rated shoes under $70?"
  → Agent analyzes question and collection schemas
  → Constructs: hybrid search + price filter + sort by rating
  → Returns: synthesized answer with supporting objects
```

### Capabilities

- Automatic search type selection (vector, keyword, hybrid)
- Dynamic filter construction from natural language
- Cross-collection queries
- Aggregation queries (count, average, etc.)
- Multi-turn conversations with context

## Query Agent Setup

### Python

```python
import weaviate
from weaviate.classes.init import Auth
from weaviate.agents.query import QueryAgent

client = weaviate.connect_to_weaviate_cloud(
    cluster_url="https://your-cluster.weaviate.network",
    auth_credentials=Auth.api_key("your-weaviate-key"),
    headers={"X-OpenAI-Api-Key": "sk-..."},
)

agent = QueryAgent(
    client=client,
    collections=["Product", "Review", "Category"],
)
```

### TypeScript

```typescript
import weaviate from 'weaviate-client';
import { QueryAgent } from 'weaviate-agents';

const client = await weaviate.connectToWeaviateCloud(
  'https://your-cluster.weaviate.network',
  {
    authCredentials: new weaviate.ApiKey('your-weaviate-key'),
    headers: { 'X-OpenAI-Api-Key': 'sk-...' },
  }
);

const agent = new QueryAgent(client, {
  collections: [
    { name: 'Product', targetVector: ['name_description_vector'] },
    'Review',
    'Category',
  ],
});
```

### Installation

```bash
# Python
pip install weaviate-agents

# TypeScript
npm install weaviate-agents
```

## Ask Mode

Performs search and generates a synthesized answer:

### Python

```python
response = agent.ask(
    "What are the best-reviewed vintage shoes under $60?"
)
response.display()

# Access structured response
print(response.final_answer)
print(f"Sources: {len(response.sources)}")
```

### TypeScript

```typescript
const response = await agent.ask(
  'What are the best-reviewed vintage shoes under $60?'
);
response.display();

console.log(response.finalAnswer);
console.log(`Sources: ${response.sources.length}`);
```

## Search Mode

Returns relevant objects without generating an answer — useful for retrieval-only use cases:

### Python

```python
response = agent.search(
    "Find vintage shoes under $70",
    limit=10,
)
for obj in response.search_results.objects:
    print(f"{obj.properties['name']} — ${obj.properties['price']}")
```

### TypeScript

```typescript
const response = await agent.search('Find vintage shoes under $70', {
  limit: 10,
});
for (const obj of response.searchResults.objects) {
  console.log(`${obj.properties.name} — $${obj.properties.price}`);
}
```

## Conversational Follow-Ups

Maintain context across multiple questions:

### Python

```python
from weaviate.agents.classes import ChatMessage

# First question
response1 = agent.ask("What vintage shoes are available under $60?")

# Follow-up with context
conversation = [
    ChatMessage(role="assistant", content=response1.final_answer),
    ChatMessage(
        role="user",
        content="Show me the same but above $200 instead.",
    ),
]
response2 = agent.ask(conversation)
response2.display()
```

### TypeScript

```typescript
import { ChatMessage } from 'weaviate-agents';

const response1 = await agent.ask('What vintage shoes are available under $60?');

const conversation: ChatMessage[] = [
  { role: 'assistant', content: response1.finalAnswer },
  { role: 'user', content: 'Show me the same but above $200 instead.' },
];
const response2 = await agent.ask(conversation);
response2.display();
```

## Transformation Agent

Enriches or transforms existing data in Weaviate using generative models. The agent reads specified properties, generates new values, and writes them back.

### Use Cases

- Generate summaries from long-form content
- Extract keywords/tags from text
- Translate content to other languages
- Classify or categorize objects
- Generate embeddings descriptions

## Transformation Setup

```python
from weaviate.agents.transformation import TransformationAgent
from weaviate.agents.classes import Operations
from weaviate.classes.config import DataType

client = weaviate.connect_to_weaviate_cloud(
    cluster_url="https://your-cluster.weaviate.network",
    auth_credentials=Auth.api_key("your-weaviate-key"),
    headers={"X-OpenAI-Api-Key": "sk-..."},
)
```

## Transform Operations

### Append New Properties

Add new properties with AI-generated values:

```python
from weaviate.agents.classes import Operations
from weaviate.classes.config import DataType

add_topics = Operations.append_property(
    property_name="topics",
    data_type=DataType.TEXT_ARRAY,
    view_properties=["abstract", "title"],  # Properties to read for context
    instruction="Generate 5 distinct topic tags based on the abstract and title.",
)

add_summary = Operations.append_property(
    property_name="summary",
    data_type=DataType.TEXT,
    view_properties=["abstract", "body"],
    instruction="Write a 2-sentence summary of this research paper.",
)

agent = TransformationAgent(
    client=client,
    collection="ResearchPapers",
    operations=[add_topics, add_summary],
)

# Execute transformation (async)
response = agent.update_all()
print(f"Workflow ID: {response.workflow_id}")

# Check status
status = agent.get_status(workflow_id=response.workflow_id)
print(f"Status: {status}")
```

### Update Existing Properties

Replace existing property values:

```python
update_category = Operations.update_property(
    property_name="category",
    view_properties=["title", "description"],
    instruction="Classify this product into one of: Electronics, Clothing, Home, Food, Other.",
)

agent = TransformationAgent(
    client=client,
    collection="Products",
    operations=[update_category],
)
response = agent.update_all()
```

### Operation Parameters

| Parameter | Description |
|-----------|-------------|
| `property_name` | Target property to create/update |
| `data_type` | Data type for new properties (TEXT, TEXT_ARRAY, INT, etc.) |
| `view_properties` | Source properties the LLM reads for context |
| `instruction` | Natural language instruction for the LLM |

## Personalization Agent

The Personalization Agent (Technical Preview) provides personalized recommendations based on user interaction history and preferences. It maintains user profiles and uses them to customize search results.

Setup and usage patterns are similar to the Query Agent but include user profile management and preference tracking.

## Common Pitfalls

1. **Weaviate Cloud only**: All agents require Weaviate Cloud. They are not available for Docker or Kubernetes self-hosted deployments.

2. **Collection descriptions matter**: The Query Agent uses collection and property descriptions to understand your data model. Provide clear descriptions for better query accuracy.

3. **Transformation is async**: `update_all()` returns immediately with a workflow ID. Poll `get_status()` to track progress. Don't assume completion.

4. **Transformation in preview**: The Transformation Agent is in technical preview. Do not use on production data — it may modify objects unexpectedly.

5. **Agent token costs**: Agents make multiple LLM calls per request (analysis, query construction, response generation). Monitor costs, especially with large result sets.

6. **Named vectors with Query Agent**: For collections with named vectors, specify `targetVector` in the collection configuration. The agent needs to know which vector to search.

## Related Topics

- Overview & Setup → `00-overview.md`
- RAG → `08-rag.md`
- Model Providers → `11-model-providers.md`
- Hybrid Search → `06-hybrid-search.md`
