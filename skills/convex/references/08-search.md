# Search

> Source: [docs.convex.dev/search](https://docs.convex.dev/search) | convex v1.34.x

## Table of Contents

- [Full-Text Search](#full-text-search)
- [Search Index Definition](#search-index-definition)
- [Executing Text Searches](#executing-text-searches)
- [Vector Search](#vector-search)
- [Vector Index Definition](#vector-index-definition)
- [Running Vector Searches](#running-vector-searches)
- [Vector Filtering](#vector-filtering)
- [RAG Pattern](#rag-pattern)
- [Limits](#limits)

## Full-Text Search

Full-text search enables keyword and phrase search within document fields. Unlike regular queries, it searches *within* string content. Results are ranked by relevance (BM25) and are reactive — search results update in real-time.

## Search Index Definition

```typescript
// convex/schema.ts
export default defineSchema({
  articles: defineTable({
    title: v.string(),
    body: v.string(),
    category: v.string(),
    authorId: v.id("users"),
  })
    .searchIndex("search_body", {
      searchField: "body",
      filterFields: ["category", "authorId"],
    })
    .searchIndex("search_title", {
      searchField: "title",
      filterFields: ["category"],
    }),
});
```

Each search index has:
- **One searchField** — The string field to search within
- **Up to 16 filterFields** — Fields for equality filtering (optional)
- **staged** flag — For large table backfilling (optional)

## Executing Text Searches

```typescript
import { query } from "./_generated/server";
import { v } from "convex/values";

export const searchArticles = query({
  args: { searchTerm: v.string(), category: v.optional(v.string()) },
  handler: async (ctx, args) => {
    let q = ctx.db
      .query("articles")
      .withSearchIndex("search_body", (q) => {
        let search = q.search("body", args.searchTerm);
        if (args.category) {
          search = search.eq("category", args.category);
        }
        return search;
      });

    return await q.take(20);
  },
});
```

### Search Expression Rules

The `.withSearchIndex()` filter must contain:
1. Exactly **one** `.search()` call on the search field
2. Zero or more `.eq()` calls on filter fields

```typescript
// Search with filter
.withSearchIndex("search_body", (q) =>
  q.search("body", "react hooks")
    .eq("category", "tutorials")
    .eq("authorId", userId)
)

// Search without filter
.withSearchIndex("search_body", (q) =>
  q.search("body", "react hooks")
)

// Filter for missing fields
.withSearchIndex("search_body", (q) =>
  q.search("body", "react hooks")
    .eq("category", undefined)  // Only docs without category
)
```

### How Text Matching Works

- Search terms are split by whitespace and punctuation
- Matching is case-insensitive
- The **last term** supports prefix matching (typeahead)
- All terms must match (AND logic)

```
"react hooks"     → matches "React Hooks tutorial" (case-insensitive)
"r"               → matches "react", "request" (prefix match)
"react h"         → "react" exact + "h" prefix match
```

### Additional Filtering

Apply post-search filters with `.filter()`:

```typescript
const results = await ctx.db
  .query("articles")
  .withSearchIndex("search_body", (q) => q.search("body", searchTerm))
  .filter((q) => q.gt(q.field("_creationTime"), oneDayAgo))
  .take(10);
```

**Performance tip:** Put as many conditions into `.withSearchIndex()` as possible. `.filter()` runs after search and counts toward the 1024-document scan limit.

### Result Ordering

Results are ordered by **relevance** using BM25 scoring. Factors include:
- Search term frequency in the document
- Document length
- Exact match count
- Document recency

`.order()` is not supported with search indexes — results always come in relevance order.

## Vector Search

Vector search finds documents similar to a provided vector embedding. It powers semantic search, recommendations, and RAG applications.

**Key difference from text search:** Vector search is only available in **actions** (not queries or mutations).

## Vector Index Definition

```typescript
export default defineSchema({
  documents: defineTable({
    title: v.string(),
    body: v.string(),
    category: v.string(),
    embedding: v.array(v.float64()),
  }).vectorIndex("by_embedding", {
    vectorField: "embedding",
    dimensions: 1536,  // Must match your embedding model
    filterFields: ["category"],
  }),
});
```

Vector index config:
- **vectorField** — Field containing the embedding array
- **dimensions** — Vector size (2–4096, must match your model)
- **filterFields** — Up to 16 fields for pre-filtering (optional)

## Running Vector Searches

```typescript
import { action, internalQuery } from "./_generated/server";
import { internal } from "./_generated/api";
import { v } from "convex/values";

export const semanticSearch = action({
  args: { query: v.string() },
  handler: async (ctx, args) => {
    // Step 1: Generate embedding from query text
    const embedding = await generateEmbedding(args.query);

    // Step 2: Search for similar documents
    const results = await ctx.vectorSearch("documents", "by_embedding", {
      vector: embedding,
      limit: 10,
    });
    // results: [{ _id, _score }, ...]

    // Step 3: Load full documents
    const documents = await ctx.runQuery(
      internal.documents.getByIds,
      { ids: results.map((r) => r._id) },
    );

    return documents;
  },
});

// Helper to load documents by ID
export const getByIds = internalQuery({
  args: { ids: v.array(v.id("documents")) },
  handler: async (ctx, args) => {
    return await Promise.all(args.ids.map((id) => ctx.db.get(id)));
  },
});
```

### Generate Embeddings (OpenAI Example)

```typescript
import OpenAI from "openai";

const openai = new OpenAI();

async function generateEmbedding(text: string): Promise<number[]> {
  const response = await openai.embeddings.create({
    model: "text-embedding-3-small",
    input: text,
  });
  return response.data[0].embedding;
}
```

### VectorSearchQuery Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `vector` | `number[]` | Yes | Query embedding (must match index dimensions) |
| `limit` | `number` | No | Results count (1–256, default 10) |
| `filter` | Function | No | Pre-filter on filterFields |

### Return Value

```typescript
{
  _id: Id<"documents">,
  _score: number,  // Cosine similarity (-1 to 1, higher = more similar)
}[]
```

## Vector Filtering

```typescript
// Single filter
const results = await ctx.vectorSearch("documents", "by_embedding", {
  vector: embedding,
  limit: 10,
  filter: (q) => q.eq("category", "tutorials"),
});

// OR filter on one field
const results = await ctx.vectorSearch("documents", "by_embedding", {
  vector: embedding,
  limit: 10,
  filter: (q) =>
    q.or(q.eq("category", "tutorials"), q.eq("category", "guides")),
});

// OR filter across fields
const results = await ctx.vectorSearch("documents", "by_embedding", {
  vector: embedding,
  limit: 10,
  filter: (q) =>
    q.or(q.eq("category", "tutorials"), q.eq("language", "python")),
});
```

## RAG Pattern

Retrieval-Augmented Generation using Convex vector search:

```typescript
export const askQuestion = action({
  args: { question: v.string() },
  handler: async (ctx, args) => {
    // 1. Embed the question
    const questionEmbedding = await generateEmbedding(args.question);

    // 2. Find relevant documents
    const results = await ctx.vectorSearch("documents", "by_embedding", {
      vector: questionEmbedding,
      limit: 5,
    });

    // 3. Load document content
    const docs = await ctx.runQuery(internal.documents.getByIds, {
      ids: results.map((r) => r._id),
    });

    // 4. Build context for LLM
    const context = docs
      .filter(Boolean)
      .map((d) => d!.body)
      .join("\n\n");

    // 5. Generate answer with context
    const response = await openai.chat.completions.create({
      model: "gpt-4o",
      messages: [
        {
          role: "system",
          content: `Answer based on this context:\n\n${context}`,
        },
        { role: "user", content: args.question },
      ],
    });

    return response.choices[0].message.content;
  },
});
```

### Storing Embeddings on Insert

```typescript
export const addDocument = action({
  args: { title: v.string(), body: v.string(), category: v.string() },
  handler: async (ctx, args) => {
    const embedding = await generateEmbedding(args.body);

    await ctx.runMutation(internal.documents.insert, {
      title: args.title,
      body: args.body,
      category: args.category,
      embedding,
    });
  },
});
```

## Limits

### Full-Text Search

| Constraint | Limit |
|-----------|-------|
| Search fields per index | 1 |
| Filter fields per index | 16 |
| Terms per search expression | 16 |
| Filter expressions per query | 8 |
| Scanned results | 1,024 |
| Best language support | English / Latin-script |

### Vector Search

| Constraint | Limit |
|-----------|-------|
| Vector fields per index | 1 |
| Dimensions range | 2–4,096 |
| Filter fields per index | 16 |
| Vector indexes per table | 4 |
| Filter expressions per search | 64 |
| Max results per search | 256 |

## Related References

- Database indexes: `04-indexes-performance.md`
- Actions (required for vector search): `02-functions-actions-http.md`
- AI patterns: `10-ai-agents.md`
