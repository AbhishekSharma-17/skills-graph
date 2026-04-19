# Supabase — AI & Vectors

> Source: https://supabase.com/docs/guides/ai

## Table of Contents

- [Overview](#overview)
- [Enabling pgvector](#enabling-pgvector)
- [Storing Vectors](#storing-vectors)
- [Generating Embeddings](#generating-embeddings)
- [Similarity Search](#similarity-search)
- [Vector Indexes](#vector-indexes)
- [Hybrid Search](#hybrid-search)
- [RAG Pattern](#rag-retrieval-augmented-generation-pattern)
- [Metadata Filtering](#metadata-filtering)
- [Common Pitfalls](#common-pitfalls)

## Overview

Supabase provides a complete AI toolkit built on PostgreSQL and pgvector. The philosophy: "the best vector database is the database you already have." Store embeddings alongside your relational data, use SQL for vector operations, and leverage Postgres extensions for hybrid search — all without a separate vector database.

## Enabling pgvector

```sql
create extension if not exists vector;
```

This is pre-installed on all Supabase projects. Just enable it.

## Storing Vectors

```sql
create table documents (
  id bigint generated always as identity primary key,
  title text not null,
  content text not null,
  embedding vector(1536),  -- OpenAI text-embedding-3-small dimension
  metadata jsonb default '{}',
  created_at timestamptz default now()
);

-- For other models, adjust the dimension:
-- vector(384)  — all-MiniLM-L6-v2
-- vector(768)  — nomic-embed-text
-- vector(1024) — Cohere embed-english-v3
-- vector(3072) — OpenAI text-embedding-3-large
```

## Generating Embeddings

### Via Edge Function (OpenAI)

```typescript
import OpenAI from "npm:openai@4"

const openai = new OpenAI({ apiKey: Deno.env.get('OPENAI_API_KEY') })

Deno.serve(async (req) => {
  const { text } = await req.json()

  const response = await openai.embeddings.create({
    model: 'text-embedding-3-small',
    input: text,
  })

  const embedding = response.data[0].embedding

  // Store in database
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  )

  const { error } = await supabase
    .from('documents')
    .insert({ title: 'Doc', content: text, embedding })

  return new Response(JSON.stringify({ success: !error }), {
    headers: { 'Content-Type': 'application/json' },
  })
})
```

### Via Python

```python
from openai import OpenAI
from supabase import create_client

openai_client = OpenAI()
supabase = create_client(url, key)

def embed_and_store(title: str, content: str):
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=content,
    )
    embedding = response.data[0].embedding

    supabase.table("documents").insert({
        "title": title,
        "content": content,
        "embedding": embedding,
    }).execute()
```

## Similarity Search

### Basic Vector Search (SQL Function)

```sql
create or replace function match_documents(
  query_embedding vector(1536),
  match_threshold float default 0.78,
  match_count int default 10
)
returns table (
  id bigint,
  title text,
  content text,
  similarity float
)
language sql stable
as $$
  select
    id,
    title,
    content,
    1 - (embedding <=> query_embedding) as similarity
  from documents
  where 1 - (embedding <=> query_embedding) > match_threshold
  order by embedding <=> query_embedding
  limit match_count;
$$;
```

Call from the client:

```typescript
const { data, error } = await supabase.rpc('match_documents', {
  query_embedding: queryVector,
  match_threshold: 0.78,
  match_count: 5,
})
```

### Distance Operators

| Operator | Distance Metric | Use Case |
|----------|----------------|----------|
| `<=>` | Cosine distance | Most common, normalized vectors |
| `<->` | L2 (Euclidean) distance | When magnitude matters |
| `<#>` | Negative inner product | Max inner product search |

## Vector Indexes

Without an index, pgvector does exact nearest-neighbor search (brute force). Add indexes for large datasets:

### HNSW Index (Recommended)

Hierarchical Navigable Small World — best for most use cases:

```sql
create index on documents
using hnsw (embedding vector_cosine_ops)
with (m = 16, ef_construction = 64);

-- Distance-specific operator classes:
-- vector_cosine_ops   for <=> (cosine)
-- vector_l2_ops       for <-> (L2)
-- vector_ip_ops       for <#> (inner product)
```

### IVFFlat Index

Faster to build, slightly less accurate:

```sql
create index on documents
using ivfflat (embedding vector_cosine_ops)
with (lists = 100);  -- sqrt(row_count) is a good starting point
```

### Index Sizing Guidelines

| Rows | Index Type | Notes |
|------|-----------|-------|
| < 10K | None needed | Exact search is fast enough |
| 10K–100K | HNSW | Good balance of speed and accuracy |
| 100K–1M | HNSW (tuned) | Increase `m` and `ef_construction` |
| > 1M | HNSW or IVFFlat | Consider partitioning |

## Hybrid Search (Semantic + Keyword)

Combine vector similarity with full-text search:

```sql
create or replace function hybrid_search(
  query_text text,
  query_embedding vector(1536),
  match_count int default 10,
  full_text_weight float default 1,
  semantic_weight float default 1,
  rrf_k int default 50
)
returns table (
  id bigint,
  title text,
  content text,
  score float
)
language sql stable
as $$
with full_text as (
  select id, row_number() over (
    order by ts_rank_cd(to_tsvector('english', content), websearch_to_tsquery(query_text)) desc
  ) as rank
  from documents
  where to_tsvector('english', content) @@ websearch_to_tsquery(query_text)
  limit match_count * 2
),
semantic as (
  select id, row_number() over (
    order by embedding <=> query_embedding
  ) as rank
  from documents
  limit match_count * 2
)
select
  d.id,
  d.title,
  d.content,
  coalesce(1.0 / (rrf_k + ft.rank), 0) * full_text_weight +
  coalesce(1.0 / (rrf_k + s.rank), 0) * semantic_weight as score
from documents d
left join full_text ft on d.id = ft.id
left join semantic s on d.id = s.id
where ft.id is not null or s.id is not null
order by score desc
limit match_count;
$$;
```

## RAG (Retrieval-Augmented Generation) Pattern

```typescript
// 1. Embed the user's question
const embeddingResponse = await openai.embeddings.create({
  model: 'text-embedding-3-small',
  input: userQuestion,
})
const queryEmbedding = embeddingResponse.data[0].embedding

// 2. Find relevant documents
const { data: docs } = await supabase.rpc('match_documents', {
  query_embedding: queryEmbedding,
  match_threshold: 0.78,
  match_count: 5,
})

// 3. Build context from retrieved documents
const context = docs.map(d => d.content).join('\n\n')

// 4. Generate answer with context
const completion = await openai.chat.completions.create({
  model: 'gpt-4o',
  messages: [
    {
      role: 'system',
      content: `Answer based on this context:\n\n${context}`,
    },
    { role: 'user', content: userQuestion },
  ],
})
```

## Metadata Filtering

Combine vector search with metadata filters:

```sql
create or replace function search_with_metadata(
  query_embedding vector(1536),
  filter_metadata jsonb default '{}',
  match_count int default 10
)
returns table (id bigint, title text, content text, similarity float)
language sql stable
as $$
  select id, title, content,
    1 - (embedding <=> query_embedding) as similarity
  from documents
  where metadata @> filter_metadata
  order by embedding <=> query_embedding
  limit match_count;
$$;
```

```typescript
const { data } = await supabase.rpc('search_with_metadata', {
  query_embedding: vector,
  filter_metadata: { category: 'engineering', language: 'en' },
  match_count: 10,
})
```

## Common Pitfalls

1. **Wrong vector dimensions** — The dimension in your column must match your embedding model exactly. Mismatches cause insert errors.
2. **Not indexing large tables** — Without an index, search is O(n). Add HNSW for datasets > 10K rows.
3. **Using the wrong distance metric** — Use cosine (`<=>`) for normalized embeddings (OpenAI, Cohere). Use L2 (`<->`) only when magnitude matters.
4. **Storing embeddings without the source text** — Always store the original content alongside the vector. You need it for RAG context.
5. **Not using `security definer`** — Match functions need to bypass RLS to scan the full table, then filter results. Use `security definer` with care.
6. **Ignoring hybrid search** — Pure vector search misses exact keyword matches. Combine with full-text search for production RAG systems.
