# Embeddings and RAG

> Source: https://ai-sdk.dev/docs/ai-sdk-core/embeddings

## Overview

AI SDK provides `embed` and `embedMany` functions for generating vector embeddings, plus `cosineSimilarity` for comparing them. These are the building blocks for Retrieval-Augmented Generation (RAG) pipelines.

## Generating Embeddings

### Single Embedding

```typescript
import { embed } from 'ai';

const { embedding, usage } = await embed({
  model: 'openai/text-embedding-3-small',
  value: 'How to build a REST API with FastAPI',
});

// embedding: number[] (1536 dimensions for this model)
// usage: { tokens: 9 }
```

### Batch Embeddings

```typescript
import { embedMany } from 'ai';

const { embeddings, usage } = await embedMany({
  model: 'openai/text-embedding-3-small',
  values: [
    'Introduction to TypeScript',
    'Advanced React patterns',
    'Database optimization techniques',
    'CI/CD best practices',
  ],
});

// embeddings: number[][] (array of vectors, same order as input)
```

## Similarity Comparison

```typescript
import { embed, embedMany, cosineSimilarity } from 'ai';

const { embeddings } = await embedMany({
  model: 'openai/text-embedding-3-small',
  values: [
    'TypeScript generics tutorial',
    'How to cook pasta',
    'TypeScript type inference',
  ],
});

const similarity01 = cosineSimilarity(embeddings[0], embeddings[1]); // Low (~0.1)
const similarity02 = cosineSimilarity(embeddings[0], embeddings[2]); // High (~0.9)
```

## Available Embedding Models

| Provider | Model | Dimensions |
|----------|-------|-----------|
| OpenAI | text-embedding-3-large | 3072 |
| OpenAI | text-embedding-3-small | 1536 |
| Google | gemini-embedding-001 | 3072 |
| Mistral | mistral-embed | 1024 |
| Cohere | embed-english-v3.0 | 1024 |
| Cohere | embed-multilingual-v3.0 | 1024 |
| Amazon Bedrock | amazon.titan-embed-text-v1 | 1536 |

## Configuration Options

### Custom Dimensions

```typescript
const { embedding } = await embed({
  model: 'openai/text-embedding-3-small',
  value: 'Hello world',
  providerOptions: {
    openai: { dimensions: 512 }, // Reduce from 1536 to 512
  },
});
```

### Parallel Processing

```typescript
const { embeddings } = await embedMany({
  model: 'openai/text-embedding-3-small',
  values: largeDocumentArray, // 1000+ items
  maxParallelCalls: 5, // Limit concurrent API calls
});
```

### Retry and Timeout

```typescript
const { embedding } = await embed({
  model: 'openai/text-embedding-3-small',
  value: 'Important text',
  maxRetries: 3,
  abortSignal: AbortSignal.timeout(10_000),
});
```

## RAG Pipeline Pattern

### 1. Document Ingestion

```typescript
import { embedMany } from 'ai';

interface Document {
  id: string;
  content: string;
  metadata: Record<string, string>;
}

async function ingestDocuments(docs: Document[]) {
  const { embeddings } = await embedMany({
    model: 'openai/text-embedding-3-small',
    values: docs.map(d => d.content),
    maxParallelCalls: 3,
  });

  // Store in vector database
  for (let i = 0; i < docs.length; i++) {
    await vectorDb.upsert({
      id: docs[i].id,
      vector: embeddings[i],
      metadata: docs[i].metadata,
      content: docs[i].content,
    });
  }
}
```

### 2. Query and Retrieve

```typescript
import { embed } from 'ai';

async function retrieveRelevant(query: string, topK = 5) {
  const { embedding } = await embed({
    model: 'openai/text-embedding-3-small',
    value: query,
  });

  const results = await vectorDb.search({
    vector: embedding,
    topK,
    includeMetadata: true,
  });

  return results;
}
```

### 3. Generate with Context

```typescript
import { generateText } from 'ai';

async function ragQuery(userQuestion: string) {
  // Retrieve relevant documents
  const relevantDocs = await retrieveRelevant(userQuestion);

  // Build context
  const context = relevantDocs
    .map(doc => `[${doc.metadata.title}]: ${doc.content}`)
    .join('\n\n');

  // Generate answer with context
  const { text } = await generateText({
    model: 'anthropic/claude-sonnet-4.5',
    system: `Answer based on the provided context. If the context doesn't contain the answer, say so.

Context:
${context}`,
    prompt: userQuestion,
  });

  return { answer: text, sources: relevantDocs };
}
```

## Chunking Strategies

Before embedding, split large documents into chunks:

```typescript
function chunkText(text: string, options: {
  maxChunkSize?: number;
  overlap?: number;
} = {}) {
  const { maxChunkSize = 500, overlap = 50 } = options;
  const chunks: string[] = [];
  const sentences = text.split(/[.!?]\s+/);
  
  let currentChunk = '';
  for (const sentence of sentences) {
    if ((currentChunk + sentence).length > maxChunkSize && currentChunk) {
      chunks.push(currentChunk.trim());
      // Keep overlap from end of previous chunk
      const words = currentChunk.split(' ');
      currentChunk = words.slice(-Math.ceil(overlap / 5)).join(' ') + ' ' + sentence;
    } else {
      currentChunk += (currentChunk ? ' ' : '') + sentence;
    }
  }
  if (currentChunk.trim()) chunks.push(currentChunk.trim());
  
  return chunks;
}
```

## Reranking

AI SDK v6 includes native reranking for search results:

```typescript
import { rerank } from 'ai';

const results = await rerank({
  model: 'cohere/rerank-english-v3.0',
  query: 'How to deploy Next.js to production?',
  documents: [
    'Next.js deployment guide for Vercel',
    'React hooks tutorial',
    'Production deployment best practices for Next.js',
    'CSS grid layout examples',
  ],
});

// results sorted by relevance score
for (const result of results) {
  console.log(result.document, result.relevanceScore);
}
```

### Structured Document Reranking

```typescript
const results = await rerank({
  model: 'cohere/rerank-english-v3.0',
  query: 'database optimization',
  documents: [
    { title: 'Query Optimization', content: 'Index strategies for PostgreSQL...' },
    { title: 'React Performance', content: 'Memoization patterns...' },
    { title: 'Database Indexing', content: 'B-tree vs hash indexes...' },
  ],
  // Specify which fields to use for ranking
  rankFields: ['title', 'content'],
});
```

## Full RAG with Reranking

```typescript
async function advancedRag(query: string) {
  // 1. Embed query
  const { embedding } = await embed({
    model: 'openai/text-embedding-3-small',
    value: query,
  });

  // 2. Retrieve candidates (over-fetch)
  const candidates = await vectorDb.search({
    vector: embedding,
    topK: 20, // Get more than needed
  });

  // 3. Rerank for precision
  const reranked = await rerank({
    model: 'cohere/rerank-english-v3.0',
    query,
    documents: candidates.map(c => c.content),
    topN: 5, // Keep top 5 after reranking
  });

  // 4. Generate with best context
  const context = reranked.map(r => r.document).join('\n\n');
  
  const { text } = await generateText({
    model: 'anthropic/claude-sonnet-4.5',
    system: `Use this context to answer:\n${context}`,
    prompt: query,
  });

  return text;
}
```

## Embedding Middleware

Apply defaults across embedding operations:

```typescript
import { defaultEmbeddingSettingsMiddleware, wrapEmbeddingModel } from 'ai';
import { google } from '@ai-sdk/google';

const model = wrapEmbeddingModel({
  model: google.embeddingModel('gemini-embedding-001'),
  middleware: defaultEmbeddingSettingsMiddleware({
    settings: {
      providerOptions: {
        google: {
          outputDimensionality: 256,
          taskType: 'RETRIEVAL_DOCUMENT',
        },
      },
    },
  }),
});
```

## Common Pitfalls

1. **Mismatched models** — Always use the same embedding model for indexing and querying
2. **No chunking** — Embedding entire documents loses granularity; chunk first
3. **Token limits** — Embedding models have max input token limits (8K for OpenAI)
4. **Dimension mismatch** — Ensure vector DB is configured for correct dimensions
5. **Missing metadata** — Always store source metadata alongside vectors for attribution

## Related Topics

- Text generation → [02-generating-text](02-generating-text.md)
- Providers → [01-providers-and-models](01-providers-and-models.md)
- Agents → [05-agents](05-agents.md)
