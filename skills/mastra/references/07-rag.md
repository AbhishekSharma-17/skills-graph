# Mastra — RAG (Retrieval-Augmented Generation)

> Source: [mastra.ai/docs/rag](https://mastra.ai/docs/rag/overview) · `@mastra/core` v1.37.x

## Table of Contents

- [Overview](#overview)
- [RAG Pipeline](#rag-pipeline)
- [Document Initialization](#document-initialization)
- [Chunking Strategies](#chunking-strategies)
- [Embedding Generation](#embedding-generation)
- [Vector Stores](#vector-stores)
- [Similarity Retrieval](#similarity-retrieval)
- [Complete RAG Example](#complete-rag-example)
- [RAG with Agents](#rag-with-agents)
- [RAG in Workflows](#rag-in-workflows)
- [Common Patterns](#common-patterns)
- [Pitfalls](#pitfalls)

## Overview

Mastra provides standardized APIs for building RAG pipelines: document processing, chunking, embedding generation, vector storage, and similarity retrieval. The system includes built-in observability for monitoring embedding and retrieval performance.

## RAG Pipeline

The standard RAG workflow follows five steps:

```
Document → Chunk → Embed → Store → Retrieve
```

1. **Document Initialization** — load content from text, PDF, HTML, etc.
2. **Chunking** — break documents into manageable pieces
3. **Embedding** — convert chunks to vector representations
4. **Storage** — persist embeddings in a vector database
5. **Retrieval** — query for relevant chunks based on similarity

## Document Initialization

Load documents from various sources:

```typescript
import { MDocument } from '@mastra/rag'

// From plain text
const doc = MDocument.fromText('Your document content here...')

// From markdown
const doc = MDocument.fromMarkdown('# Title\n\nContent here...')

// From HTML
const doc = MDocument.fromHTML('<html><body>Content</body></html>')
```

## Chunking Strategies

Break documents into chunks for embedding:

```typescript
// Recursive chunking (recommended for most use cases)
const chunks = await doc.chunk({
  strategy: 'recursive',
  size: 512,      // Characters per chunk
  overlap: 50,    // Overlap between chunks
})
```

### Available Strategies

| Strategy | Use Case | Description |
|----------|----------|-------------|
| `recursive` | General text | Splits on natural boundaries (paragraphs, sentences) |
| `character` | Simple splitting | Fixed character-count splits |
| `token` | Token-aware | Splits based on token count |
| `markdown` | Markdown docs | Respects heading structure |
| `html` | HTML content | Preserves DOM structure |
| `json` | JSON data | Splits JSON objects |

### Recursive Chunking Options

```typescript
const chunks = await doc.chunk({
  strategy: 'recursive',
  size: 512,
  overlap: 50,
  separators: ['\n\n', '\n', '. ', ' ', ''],
})
```

## Embedding Generation

Convert chunks to vector representations:

```typescript
import { embed, embedMany } from '@mastra/rag'

// Single text
const embedding = await embed('Some text', {
  model: 'openai/text-embedding-3-small',
})

// Multiple texts (batch)
const embeddings = await embedMany(
  chunks.map(chunk => chunk.text),
  { model: 'openai/text-embedding-3-small' }
)
```

### Embedding Providers

- **OpenAI**: `openai/text-embedding-3-small`, `openai/text-embedding-3-large`
- **Cohere**: `cohere/embed-english-v3.0`, `cohere/embed-multilingual-v3.0`
- Any provider supported by the AI SDK

## Vector Stores

Mastra supports multiple vector database backends:

### PGVector (PostgreSQL)

```typescript
import { PgVector } from '@mastra/pg'

const vectorStore = new PgVector({
  connectionString: process.env.DATABASE_URL,
})

// Create index
await vectorStore.createIndex('my-documents', 1536) // dimension matches model

// Upsert embeddings
await vectorStore.upsert('my-documents', embeddings.map((embedding, i) => ({
  id: `chunk-${i}`,
  values: embedding,
  metadata: { text: chunks[i].text, source: 'doc.md' },
})))
```

### Pinecone

```typescript
import { PineconeVector } from '@mastra/pinecone'

const vectorStore = new PineconeVector({
  apiKey: process.env.PINECONE_API_KEY,
})
```

### Qdrant

```typescript
import { QdrantVector } from '@mastra/qdrant'

const vectorStore = new QdrantVector({
  url: process.env.QDRANT_URL,
  apiKey: process.env.QDRANT_API_KEY,
})
```

### MongoDB Atlas

```typescript
import { MongoDBVector } from '@mastra/mongodb'

const vectorStore = new MongoDBVector({
  connectionString: process.env.MONGODB_URL,
  dbName: 'my-db',
})
```

## Similarity Retrieval

Query the vector store for relevant chunks:

```typescript
// Embed the query
const queryEmbedding = await embed('What is the return policy?', {
  model: 'openai/text-embedding-3-small',
})

// Search for similar chunks
const results = await vectorStore.query('my-documents', queryEmbedding, {
  topK: 5,
  filter: { source: 'policies.md' },  // Optional metadata filter
})

// results: [{ id, score, metadata: { text, source } }, ...]
```

## Complete RAG Example

End-to-end pipeline:

```typescript
import { MDocument, embed, embedMany } from '@mastra/rag'
import { PgVector } from '@mastra/pg'

// 1. Initialize document
const doc = MDocument.fromText(longDocument)

// 2. Chunk
const chunks = await doc.chunk({
  strategy: 'recursive',
  size: 512,
  overlap: 50,
})

// 3. Embed
const embeddings = await embedMany(
  chunks.map(c => c.text),
  { model: 'openai/text-embedding-3-small' }
)

// 4. Store
const vectorStore = new PgVector({ connectionString: process.env.DATABASE_URL })
await vectorStore.createIndex('knowledge-base', 1536)
await vectorStore.upsert('knowledge-base', embeddings.map((emb, i) => ({
  id: `chunk-${i}`,
  values: emb,
  metadata: { text: chunks[i].text },
})))

// 5. Retrieve
const queryEmb = await embed('How do I reset my password?', {
  model: 'openai/text-embedding-3-small',
})
const results = await vectorStore.query('knowledge-base', queryEmb, { topK: 3 })

// Use results as context for an agent
const context = results.map(r => r.metadata.text).join('\n\n')
const response = await agent.generate(
  `Context:\n${context}\n\nQuestion: How do I reset my password?`
)
```

## RAG with Agents

Create a tool that performs RAG retrieval:

```typescript
const ragTool = createTool({
  id: 'knowledge-search',
  description: 'Search the knowledge base for relevant information',
  inputSchema: z.object({ query: z.string() }),
  outputSchema: z.object({ context: z.string(), sources: z.array(z.string()) }),
  execute: async ({ query }) => {
    const queryEmb = await embed(query, { model: 'openai/text-embedding-3-small' })
    const results = await vectorStore.query('knowledge-base', queryEmb, { topK: 5 })
    return {
      context: results.map(r => r.metadata.text).join('\n\n'),
      sources: results.map(r => r.metadata.source),
    }
  },
})

const ragAgent = new Agent({
  id: 'rag-agent',
  name: 'Knowledge Agent',
  instructions: `Use the knowledge-search tool to find relevant information
before answering questions. Always cite your sources.`,
  model: 'openai/gpt-5.4',
  tools: { ragTool },
})
```

## RAG in Workflows

Build a RAG pipeline as a workflow:

```typescript
const ragWorkflow = createWorkflow({
  id: 'rag-pipeline',
  inputSchema: z.object({ documents: z.array(z.string()) }),
  outputSchema: z.object({ indexed: z.number() }),
})
  .foreach(chunkStep, { concurrency: 4 })
  .then(embedStep)
  .then(storeStep)
  .commit()
```

## Common Patterns

### Hybrid Search (Semantic + Keyword)

Combine vector similarity with metadata filters:

```typescript
const results = await vectorStore.query('docs', queryEmb, {
  topK: 10,
  filter: {
    category: 'technical',
    updated_after: '2026-01-01',
  },
})
```

### Incremental Indexing

Check if a document was already indexed before re-processing:

```typescript
const docHash = crypto.createHash('md5').update(content).digest('hex')
const existing = await vectorStore.query('docs', queryEmb, {
  topK: 1,
  filter: { hash: docHash },
})
if (existing.length === 0) {
  // Index new document
}
```

## Pitfalls

1. **Chunk size matters** — too large loses precision, too small loses context. 512 chars is a good default
2. **Overlap prevents boundary loss** — 50-100 char overlap ensures no information falls between chunks
3. **Match embedding dimensions** — index dimension must match the embedding model's output size
4. **Filter by metadata** — use metadata filters to narrow search scope before semantic matching
5. **Don't embed queries differently** — use the same embedding model for documents and queries
