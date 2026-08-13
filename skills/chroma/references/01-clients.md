# Chroma — Clients

> Source: [docs.trychroma.com/docs/run-chroma/clients](https://docs.trychroma.com/docs/run-chroma/clients)

## Table of Contents

- [Client Types Overview](#client-types-overview)
- [Ephemeral Client](#ephemeral-client)
- [Persistent Client](#persistent-client)
- [HTTP Client](#http-client)
- [Async HTTP Client](#async-http-client)
- [Cloud Client](#cloud-client)
- [TypeScript Client](#typescript-client)
- [Rust Client](#rust-client)
- [Utility Methods](#utility-methods)
- [Common Pitfalls](#common-pitfalls)

## Client Types Overview

| Client | Language | Storage | Use Case |
|--------|----------|---------|----------|
| `Client()` | Python | In-memory | Testing, experiments |
| `PersistentClient()` | Python | Local disk | Dev, small production |
| `HttpClient()` | Python | Remote server | Multi-process production |
| `AsyncHttpClient()` | Python | Remote server | Async applications |
| `CloudClient()` | Python | Chroma Cloud | Managed production |
| `ChromaClient()` | TypeScript | Remote server | Node.js / browser |
| `ChromaHttpClient` | Rust | Remote server | Rust applications |

## Ephemeral Client

In-memory database — data is lost when the process exits. Use for unit tests and quick experiments.

```python
import chromadb

client = chromadb.Client()

collection = client.create_collection(name="test")
collection.add(ids=["1"], documents=["test document"])
# Data is gone when client is garbage collected
```

## Persistent Client

Saves data to a local directory. Automatically persists changes on every operation.

```python
import chromadb

# Defaults to .chroma/ if no path provided
client = chromadb.PersistentClient(path="./my-chroma-data")

collection = client.get_or_create_collection(name="docs")
collection.add(ids=["1"], documents=["persisted to disk"])

# Data survives process restarts
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | `str` | `".chroma"` | Directory for database files |

## HTTP Client

Connects to a Chroma server running as a separate process. Use for multi-process access and production deployments.

**Start the server first:**

```bash
chroma run --path /db_path
# Listens on localhost:8000 by default
```

**Connect from Python:**

```python
import chromadb

client = chromadb.HttpClient(host="localhost", port=8000)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `host` | `str` | `"localhost"` | Server hostname |
| `port` | `int` | `8000` | Server port |
| `ssl` | `bool` | `False` | Enable HTTPS |
| `tenant` | `str` | `"default_tenant"` | Tenant identifier |
| `database` | `str` | `"default_database"` | Database name |

## Async HTTP Client

Same API as `HttpClient` but all blocking methods are async. Use in async applications (FastAPI, async agents).

```python
import chromadb
import asyncio

async def main():
    client = await chromadb.AsyncHttpClient(host="localhost", port=8000)
    
    collection = await client.create_collection(name="docs")
    await collection.add(ids=["1"], documents=["async document"])
    
    results = await collection.query(
        query_texts=["search term"],
        n_results=5,
    )
    return results

asyncio.run(main())
```

## Cloud Client

Connects to Chroma Cloud. Requires an API key from [trychroma.com](https://trychroma.com/signup).

```python
import chromadb

client = chromadb.CloudClient(
    tenant="your-tenant-id",
    database="your-database-name",
    api_key="your-api-key",
)

collection = client.get_or_create_collection(name="docs")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tenant` | `str` | Required | Your tenant ID |
| `database` | `str` | Required | Database name |
| `api_key` | `str` | From env | API key (or set `CHROMA_API_KEY`) |
| `cloud_host` | `str` | `"api.trychroma.com"` | Cloud endpoint |
| `cloud_port` | `int` | `443` | Cloud port |

**Regions:**

| Region | Endpoint |
|--------|----------|
| AWS US East (Virginia) | `api.trychroma.com` (default) |
| GCP Europe West (Belgium) | `europe-west1.gcp.trychroma.com` |

**Environment variables** (auto-detected):
- `CHROMA_API_KEY` — API key
- `CHROMA_TENANT` — Tenant ID
- `CHROMA_DATABASE` — Database name

## TypeScript Client

Requires a running Chroma server (no embedded mode in TypeScript).

```typescript
import { ChromaClient } from "chromadb";

// Default: localhost:8000
const client = new ChromaClient();

// Custom configuration
const client = new ChromaClient({
  host: "YOUR-HOST",
  port: "YOUR-PORT",
  ssl: true,
  tenant: "my-tenant",
  database: "my-database",
});
```

## Rust Client

```rust
use chroma::ChromaHttpClient;
use chroma::ChromaHttpClientOptions;

// Default configuration
let client = ChromaHttpClient::new(Default::default());

// Custom endpoint
let options = ChromaHttpClientOptions {
    endpoint: "http://localhost:8000".parse()?,
    ..Default::default()
};
let client = ChromaHttpClient::new(options);
```

## Utility Methods

Available on all client types:

```python
# Verify connection
heartbeat = client.heartbeat()

# Reset database (destructive — removes all data)
client.reset()
```

## Common Pitfalls

1. **Embedding function mismatch** — The embedding function used to `add` data must match the one used to `query`. If you don't specify one, Chroma uses `all-MiniLM-L6-v2` by default.

2. **TypeScript requires a server** — Unlike Python, there is no embedded mode. Always start `chroma run` first.

3. **PersistentClient path conflicts** — Only one process should access a persistent database at a time. For multi-process access, use `HttpClient` with a Chroma server.

4. **Cloud API key in env** — For production, set `CHROMA_API_KEY` as an environment variable rather than hardcoding it.

5. **Thin client for serverless** — Use `pip install chromadb-client` instead of `chromadb` in serverless functions to avoid heavy dependencies (sentence-transformers, ONNX).
