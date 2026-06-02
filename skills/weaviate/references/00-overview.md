# Weaviate — Overview & Setup

> Source: [docs.weaviate.io](https://docs.weaviate.io/weaviate) | Version: v1.37

## Table of Contents
- [What is Weaviate](#what-is-weaviate)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Client Setup](#client-setup)
- [Quickstart](#quickstart)
- [Common Pitfalls](#common-pitfalls)

---

## What is Weaviate

Weaviate is an open-source, cloud-native vector database written in Go. It stores both data objects and their vector embeddings, enabling semantic search, hybrid search (keyword + vector), retrieval augmented generation (RAG), and agent-driven workflows — all from a single database.

Key differentiators from traditional databases:
- **Semantic understanding**: searches by meaning, not just keyword matching
- **Hybrid search**: combines BM25 keyword scoring with vector similarity in one query
- **Built-in RAG**: pass search results directly to LLMs for generative answers
- **Model integrations**: auto-vectorize data with OpenAI, Cohere, Google, etc.
- **Multi-tenancy**: data isolation per tenant with hot/cold/offloaded states
- **Agents**: pre-built Query and Transformation agents for natural language workflows

## Key Features

| Feature | Description |
|---------|-------------|
| Vector search | Millisecond semantic search across billions of vectors |
| Hybrid search | Combine BM25 keyword + vector similarity in one query |
| RAG | Built-in generative search with LLM providers |
| Named vectors | Multiple vector spaces per object |
| Multi-tenancy | Tenant isolation with activity states |
| Reranking | Re-score results with cross-encoder models |
| Filtering | Rich property-based filters combinable with any search |
| Aggregation | Count, sum, avg, min, max, groupBy on search results |
| RBAC | Role-based access control |
| Replication | Multi-node with tunable consistency |
| Compression | PQ, BQ, SQ quantization for cost efficiency |

## Architecture

```
Client (Python/TS/Go/Java/C#)
    │
    ├── REST API (port 8080)
    ├── gRPC API (port 50051)
    └── GraphQL API
         │
    ┌────┴────┐
    │ Weaviate │
    │  Server  │
    └────┬────┘
         │
    ┌────┴──────────────────────┐
    │  Storage Layer            │
    │  ├── Vector Index (HNSW)  │
    │  ├── Inverted Index (BM25)│
    │  └── Object Store         │
    └───────────────────────────┘
         │
    Model Providers (OpenAI, Cohere, Ollama, etc.)
```

## Installation

### Docker Compose (Recommended for Development)

```yaml
# docker-compose.yml
services:
  weaviate:
    image: cr.weaviate.io/semitechnologies/weaviate:1.37.7
    restart: on-failure:0
    ports:
      - "8080:8080"
      - "50051:50051"
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: "true"
      PERSISTENCE_DATA_PATH: "/var/lib/weaviate"
      DEFAULT_VECTORIZER_MODULE: "none"
      CLUSTER_HOSTNAME: "node1"
```

```bash
docker compose up -d
```

### Docker Compose with Vectorizer Modules

```yaml
services:
  weaviate:
    image: cr.weaviate.io/semitechnologies/weaviate:1.37.7
    restart: on-failure:0
    ports:
      - "8080:8080"
      - "50051:50051"
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: "true"
      PERSISTENCE_DATA_PATH: "/var/lib/weaviate"
      DEFAULT_VECTORIZER_MODULE: "text2vec-openai"
      ENABLE_MODULES: "text2vec-openai,generative-openai"
      CLUSTER_HOSTNAME: "node1"
```

### Weaviate Cloud (Managed)

Create a cluster at [console.weaviate.cloud](https://console.weaviate.cloud). Provides sandbox (free) and production tiers with built-in model integrations.

### Embedded Weaviate (Experimental)

```python
import weaviate

client = weaviate.connect_to_embedded()
```

Runs Weaviate in-process — useful for testing and prototyping.

## Client Setup

### Python

```bash
pip install -U weaviate-client
```

```python
import weaviate
from weaviate.classes.init import Auth

# Connect to Weaviate Cloud
client = weaviate.connect_to_weaviate_cloud(
    cluster_url="https://your-cluster.weaviate.network",
    auth_credentials=Auth.api_key("your-weaviate-api-key"),
    headers={"X-OpenAI-Api-Key": "your-openai-key"}
)

# Connect to local Docker instance
client = weaviate.connect_to_local()

# Connect with custom URL
client = weaviate.connect_to_custom(
    http_host="localhost",
    http_port=8080,
    http_secure=False,
    grpc_host="localhost",
    grpc_port=50051,
    grpc_secure=False,
)

# Always close when done
client.close()
```

### Python Context Manager

```python
import weaviate

with weaviate.connect_to_local() as client:
    # client auto-closes when block exits
    collection = client.collections.use("Article")
    result = collection.query.near_text(query="AI news", limit=5)
```

### TypeScript / JavaScript

```bash
npm install weaviate-client
```

```typescript
import weaviate, { WeaviateClient } from 'weaviate-client';

// Connect to Weaviate Cloud
const client: WeaviateClient = await weaviate.connectToWeaviateCloud(
  'https://your-cluster.weaviate.network',
  {
    authCredentials: new weaviate.ApiKey('your-weaviate-api-key'),
    headers: { 'X-OpenAI-Api-Key': 'your-openai-key' },
  }
);

// Connect to local Docker
const client = await weaviate.connectToLocal();

// Always close when done
await client.close();
```

## Quickstart

```python
import weaviate
import weaviate.classes.config as wc

client = weaviate.connect_to_local()

# 1. Create a collection with a vectorizer
client.collections.create(
    "Article",
    vector_config=wc.Configure.Vectors.text2vec_openai(),
    generative_config=wc.Configure.Generative.openai(),
    properties=[
        wc.Property(name="title", data_type=wc.DataType.TEXT),
        wc.Property(name="body", data_type=wc.DataType.TEXT),
        wc.Property(name="category", data_type=wc.DataType.TEXT),
    ],
)

# 2. Insert data (vectors auto-generated)
articles = client.collections.use("Article")
articles.data.insert({"title": "AI Revolution", "body": "...", "category": "tech"})

# 3. Semantic search
response = articles.query.near_text(query="artificial intelligence", limit=5)
for obj in response.objects:
    print(obj.properties["title"])

# 4. Hybrid search
response = articles.query.hybrid(query="machine learning trends", alpha=0.75, limit=5)

# 5. RAG (generative search)
response = articles.generate.near_text(
    query="latest AI developments",
    limit=3,
    grouped_task="Summarize these articles in 2 sentences."
)
print(response.generated)

client.close()
```

## Common Pitfalls

1. **Forgetting to close the client**: Always call `client.close()` or use a context manager. Leaked connections cause resource exhaustion.

2. **Missing model API keys**: If using a vectorizer like `text2vec-openai`, the OpenAI API key must be in the connection headers. Without it, inserts and searches silently fail or error.

3. **Auto-schema surprises**: Weaviate auto-creates properties from data if not predefined. This can create incorrect data types. Define schemas explicitly in production.

4. **Port confusion**: REST API runs on 8080, gRPC on 50051. The Python v4 client uses gRPC by default for performance. Ensure both ports are accessible.

5. **Vector dimensionality mismatch**: If providing custom vectors, they must match the configured dimensionality. Mixing models (e.g., inserting Ada-002 vectors but querying with a different model) produces poor results.

## Related Topics

- Collections & Schema → `01-collections.md`
- Vector Configuration → `02-vector-config.md`
- Similarity Search → `04-similarity-search.md`
- Model Providers → `11-model-providers.md`
