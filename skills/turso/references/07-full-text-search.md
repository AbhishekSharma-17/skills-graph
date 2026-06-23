# Turso Full-Text Search (Tantivy)

> Source: [docs.turso.tech/sql-reference/functions/fts](https://docs.turso.tech/sql-reference/functions/fts)

## Table of Contents
- [Overview](#overview)
- [Creating FTS Indexes](#creating-fts-indexes)
- [Tokenizers](#tokenizers)
- [Field Weights](#field-weights)
- [Search Functions](#search-functions)
- [Query Syntax](#query-syntax)
- [Index Maintenance](#index-maintenance)
- [Combining FTS with Vector Search](#combining-fts-with-vector-search)
- [Common Pitfalls](#common-pitfalls)

## Overview

Turso implements full-text search using **Tantivy** (Rust-based search engine), not SQLite's FTS3/FTS4/FTS5. This provides Unicode-aware tokenization, BM25 relevance scoring, and efficient indexing. The syntax and functions differ from standard SQLite FTS.

## Creating FTS Indexes

```sql
-- Basic FTS index on one column
CREATE INDEX articles_fts ON articles USING fts (title);

-- Multi-column FTS index
CREATE INDEX articles_fts ON articles USING fts (title, body);

-- With tokenizer configuration
CREATE INDEX articles_fts ON articles USING fts (title, body)
    WITH (tokenizer = 'default');
```

### Per-Column Tokenizer

```sql
CREATE INDEX products_fts ON products USING fts (name, description, sku)
    WITH (
        tokenizer_name = 'default',
        tokenizer_sku = 'raw'  -- Exact match on SKU field
    );
```

## Tokenizers

| Tokenizer | Behavior | Best For |
|-----------|----------|----------|
| `default` | Unicode-aware, lowercasing, punctuation splitting, 40-char limit | General text search |
| `raw` | No tokenization — entire field is one token | IDs, tags, exact codes |
| `simple` | Split on whitespace and punctuation, no lowercasing | Case-sensitive search |
| `whitespace` | Split on whitespace only | Preserving punctuation |
| `ngram` | 2-3 character n-grams | Autocomplete, substring matching |

### Ngram Tokenizer Example

```sql
CREATE INDEX products_search ON products USING fts (name)
    WITH (tokenizer = 'ngram');

-- Now "lap" matches "laptop", "lapel", etc.
SELECT * FROM products WHERE fts_match(name, 'lap');
```

## Field Weights

Assign weights to influence BM25 relevance scoring:

```sql
CREATE INDEX articles_fts ON articles USING fts (title, body)
    WITH (weights = 'title=2.0,body=1.0');
```

Higher weight = more influence on relevance score. Title matches score 2x higher than body matches.

## Search Functions

### fts_match — Filter Matching Rows

```sql
-- Single column
SELECT * FROM articles
WHERE fts_match(title, 'database');

-- Multi-column
SELECT * FROM articles
WHERE fts_match(title, body, 'database performance');
```

Returns 1 if the row matches, 0 otherwise.

### fts_score — BM25 Relevance Score

```sql
SELECT title,
       fts_score(title, body, 'database optimization') AS score
FROM articles
WHERE fts_match(title, body, 'database optimization')
ORDER BY score DESC;
```

Lower scores indicate higher relevance (BM25 convention). Order `DESC` for most relevant first.

### fts_highlight — Highlight Matched Terms

```sql
SELECT title,
       fts_highlight(title, body, '<b>', '</b>', 'database') AS highlighted
FROM articles
WHERE fts_match(title, body, 'database');
```

Wraps matched terms in the specified tags. Useful for search result display.

## Query Syntax

Turso uses Tantivy's query parser:

### Basic Queries

```sql
-- Single term (matches documents containing "database")
WHERE fts_match(title, body, 'database')

-- Multiple terms (OR — matches either term)
WHERE fts_match(title, body, 'database search')

-- Boolean AND (both terms required)
WHERE fts_match(title, body, 'database AND search')

-- Boolean NOT (exclude term)
WHERE fts_match(title, body, 'database NOT nosql')
```

### Advanced Queries

```sql
-- Exact phrase
WHERE fts_match(title, body, '"full text search"')

-- Prefix search (autocomplete)
WHERE fts_match(title, body, 'data*')

-- Column-specific search
WHERE fts_match(title, body, 'title:database')

-- Boosting (title matches score 2x)
WHERE fts_match(title, body, 'title:database^2')

-- Complex boolean
WHERE fts_match(title, body, '(database OR search) AND NOT nosql')
```

### Complete Search Endpoint Example

```typescript
app.get("/search", async (req, res) => {
  const query = req.query.q as string;
  if (!query) return res.json({ results: [] });

  const { rows } = await client.execute({
    sql: `SELECT id, title,
                 fts_highlight(title, body, '<mark>', '</mark>', ?) AS snippet,
                 fts_score(title, body, ?) AS score
          FROM articles
          WHERE fts_match(title, body, ?)
          ORDER BY score DESC
          LIMIT 20`,
    args: [query, query, query],
  });

  res.json({ results: rows });
});
```

## Index Maintenance

### Optimize Index

```sql
OPTIMIZE INDEX articles_fts;
```

Merges segments, removes tombstones from deleted documents, and improves query performance. Run after bulk inserts or periodic maintenance.

### DML Behavior

| Operation | FTS Behavior |
|-----------|-------------|
| INSERT | Indexed immediately (batched every 1000 documents internally) |
| UPDATE | Implemented as DELETE + INSERT |
| DELETE | Uses tombstones; cleaned up on `OPTIMIZE` |

### Drop Index

```sql
DROP INDEX articles_fts;
```

## Combining FTS with Vector Search

Use FTS for keyword filtering and vector search for semantic ranking:

```sql
-- Step 1: FTS pre-filter for keyword relevance
-- Step 2: Vector rerank for semantic similarity
SELECT d.title, d.content,
       fts_score(d.title, d.content, ?) AS text_score
FROM vector_top_k('docs_idx', vector32(?), 50) AS v
JOIN documents d ON d.rowid = v.id
WHERE fts_match(d.title, d.content, ?)
ORDER BY text_score DESC
LIMIT 10;
```

### Hybrid Search Pattern

```typescript
async function hybridSearch(query: string, queryEmbedding: number[]) {
  const vec = JSON.stringify(queryEmbedding);

  const { rows } = await client.execute({
    sql: `WITH vector_results AS (
            SELECT id, distance FROM vector_top_k('docs_idx', vector32(?), 100)
          ),
          fts_results AS (
            SELECT rowid, fts_score(title, content, ?) AS fts_rank
            FROM documents
            WHERE fts_match(title, content, ?)
          )
          SELECT d.title, d.content,
                 COALESCE(v.distance, 1.0) AS vec_dist,
                 COALESCE(f.fts_rank, 0.0) AS fts_rank
          FROM documents d
          LEFT JOIN vector_results v ON d.rowid = v.id
          LEFT JOIN fts_results f ON d.rowid = f.rowid
          WHERE v.id IS NOT NULL OR f.rowid IS NOT NULL
          ORDER BY (COALESCE(1.0 - v.distance, 0) * 0.7 +
                    COALESCE(f.fts_rank, 0) * 0.3) DESC
          LIMIT 10`,
    args: [vec, query, query],
  });

  return rows;
}
```

## Common Pitfalls

1. **Not Tantivy, not FTS5** — Turso uses Tantivy. SQLite FTS5 syntax (`MATCH`, `bm25()`, `snippet()`) does not work
2. **Use `fts_match()`, not `MATCH`** — The standard SQLite MATCH operator is not supported
3. **Score ordering** — `fts_score()` returns lower values for more relevant results. Use `ORDER BY score DESC` for best matches first
4. **No snippet function** — Unlike FTS5, Turso's Tantivy integration doesn't have a `snippet()` function. Use `fts_highlight()` instead
5. **Read-your-writes in transactions** — FTS index updates within a transaction are not visible to subsequent reads in the same transaction
6. **OPTIMIZE frequency** — Run `OPTIMIZE INDEX` periodically (e.g., daily cron) after bulk operations, not after every write
7. **Column count mismatch** — The number of columns in `fts_match()`, `fts_score()`, and `fts_highlight()` must match the index definition
