# Indexes & Query Performance

> Source: [docs.convex.dev/database/indexes](https://docs.convex.dev/database/indexes) | convex v1.34.x

## Table of Contents

- [Index Fundamentals](#index-fundamentals)
- [Defining Indexes](#defining-indexes)
- [Querying with Indexes](#querying-with-indexes)
- [Compound Indexes](#compound-indexes)
- [Sorting with Indexes](#sorting-with-indexes)
- [Pagination](#pagination)
- [Filter vs Index](#filter-vs-index)
- [Staged Indexes](#staged-indexes)
- [Performance Guidelines](#performance-guidelines)
- [Index Limits](#index-limits)

## Index Fundamentals

Indexes organize documents for fast retrieval. Without an index, queries scan every document in the table. With an index, Convex can jump directly to matching documents.

Every table automatically has:
- `by_id` — Index on `_id` (built-in, always available)
- `by_creation_time` — Index on `_creationTime` (auto-created)

## Defining Indexes

```typescript
// convex/schema.ts
export default defineSchema({
  messages: defineTable({
    channel: v.id("channels"),
    author: v.id("users"),
    body: v.string(),
    priority: v.number(),
  })
    // Single-field index
    .index("by_channel", ["channel"])

    // Compound index (multiple fields)
    .index("by_channel_author", ["channel", "author"])

    // Index for sorting
    .index("by_priority", ["priority"])

    // Nested field index
    .index("by_metadata_type", ["metadata.type"]),
});
```

**Important:** `_creationTime` is automatically appended as the last field in every index. This means `["channel"]` is actually `["channel", "_creationTime"]`.

## Querying with Indexes

Use `.withIndex()` to leverage an index:

```typescript
// Equality query
const channelMessages = await ctx.db
  .query("messages")
  .withIndex("by_channel", (q) => q.eq("channel", channelId))
  .collect();

// Range query (after equality)
const recentMessages = await ctx.db
  .query("messages")
  .withIndex("by_channel", (q) =>
    q
      .eq("channel", channelId)
      .gt("_creationTime", Date.now() - 24 * 60 * 60 * 1000)
  )
  .collect();

// Multiple equality + range
const userRecentMessages = await ctx.db
  .query("messages")
  .withIndex("by_channel_author", (q) =>
    q
      .eq("channel", channelId)
      .eq("author", userId)
      .gte("_creationTime", startTime)
      .lt("_creationTime", endTime)
  )
  .collect();
```

### Index Range Expression Rules

Expressions must follow index field order:

1. Zero or more `.eq()` — match exact values sequentially
2. Optional lower bound — `.gt()` or `.gte()`
3. Optional upper bound — `.lt()` or `.lte()`

```typescript
// Index: ["channel", "author", "_creationTime"]

// VALID: eq on channel, range on _creationTime (skipping author)
q.eq("channel", channelId)
// Scans all authors in channel

// VALID: eq on both, range on _creationTime
q.eq("channel", channelId).eq("author", userId)
// Narrows to specific author

// INVALID: Cannot skip channel and query author directly
q.eq("author", userId)  // COMPILE ERROR
```

## Compound Indexes

Multi-field indexes support querying on any prefix:

```typescript
// Index: by_channel_author = ["channel", "author"]
// Actually: ["channel", "author", "_creationTime"]

// Use full index
.withIndex("by_channel_author", (q) =>
  q.eq("channel", ch).eq("author", user)
)
// Returns: messages by specific user in channel, ordered by time

// Use prefix only
.withIndex("by_channel_author", (q) =>
  q.eq("channel", ch)
)
// Returns: all messages in channel, ordered by author then time

// Optimization: by_channel_author makes a separate by_channel redundant
// (unless you need different sort order)
```

## Sorting with Indexes

Results are ordered by index fields. Use `.order()` to reverse:

```typescript
// Ascending (default) — oldest first
const oldest = await ctx.db
  .query("messages")
  .withIndex("by_channel", (q) => q.eq("channel", channelId))
  .order("asc")
  .take(10);

// Descending — newest first
const newest = await ctx.db
  .query("messages")
  .withIndex("by_channel", (q) => q.eq("channel", channelId))
  .order("desc")
  .take(10);

// Leaderboard pattern
const topPlayers = await ctx.db
  .query("players")
  .withIndex("by_score", (q) => q)  // Open range on score
  .order("desc")
  .take(10);
```

## Pagination

For large result sets, use `.paginate()`:

```typescript
import { paginationOptsValidator } from "convex/server";

export const listMessages = query({
  args: {
    channelId: v.id("channels"),
    paginationOpts: paginationOptsValidator,
  },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("messages")
      .withIndex("by_channel", (q) => q.eq("channel", args.channelId))
      .order("desc")
      .paginate(args.paginationOpts);
  },
});
```

The return value:

```typescript
{
  page: Doc<"messages">[],  // Documents in this page
  isDone: boolean,           // True if no more results
  continueCursor: string,    // Pass to next paginate() call
}
```

### Client-Side Pagination (React)

```typescript
import { usePaginatedQuery } from "convex/react";

function MessageList({ channelId }) {
  const { results, status, loadMore } = usePaginatedQuery(
    api.messages.listMessages,
    { channelId },
    { initialNumItems: 25 },
  );

  return (
    <div>
      {results.map((msg) => <Message key={msg._id} message={msg} />)}
      {status === "CanLoadMore" && (
        <button onClick={() => loadMore(25)}>Load More</button>
      )}
      {status === "LoadingMore" && <Spinner />}
    </div>
  );
}
```

## Filter vs Index

`.filter()` runs **after** the index scan — it doesn't reduce the scan range:

```typescript
// SLOW: Scans all messages, then filters
const results = await ctx.db
  .query("messages")
  .filter((q) => q.eq(q.field("channel"), channelId))
  .collect();

// FAST: Index narrows to channel first
const results = await ctx.db
  .query("messages")
  .withIndex("by_channel", (q) => q.eq("channel", channelId))
  .collect();

// ACCEPTABLE: Index narrows, then filter refines
const results = await ctx.db
  .query("messages")
  .withIndex("by_channel", (q) => q.eq("channel", channelId))
  .filter((q) => q.neq(q.field("author"), blockedUserId))
  .take(50);
```

**Rule:** Put as many conditions as possible into `.withIndex()`. Use `.filter()` only for conditions that can't be expressed as index ranges.

### Filter Expressions

```typescript
.filter((q) =>
  q.and(
    q.gt(q.field("score"), 100),
    q.neq(q.field("status"), "deleted"),
    q.or(
      q.eq(q.field("type"), "post"),
      q.eq(q.field("type"), "comment"),
    ),
  )
)
```

Available operators: `eq`, `neq`, `gt`, `gte`, `lt`, `lte`, `and`, `or`, `not`

## Staged Indexes

For large tables, create indexes without blocking deployment:

```typescript
.index("by_email", { fields: ["email"], staged: true })
```

1. Deploy with `staged: true` — index starts backfilling in the background
2. Monitor progress in the dashboard
3. Once complete, remove `staged` flag and redeploy
4. Staged indexes cannot be queried until fully built

## Performance Guidelines

### Do

- Use indexes for all production queries on large tables
- Use `.take(n)` or `.first()` instead of `.collect()` for large tables
- Define compound indexes matching your most common query patterns
- Put equality filters in the index, use `.filter()` only for inequality
- Use pagination for user-facing lists

### Don't

- Don't create redundant indexes (prefix of another index)
- Don't use `.collect()` on unbounded queries in production
- Don't use `.filter()` for conditions that could be indexed
- Don't ignore index field order — it determines what queries are possible
- Don't use `Date.now()` in queries (breaks reactivity caching)

### Bandwidth

All documents returned by `.collect()` count toward database bandwidth, including those later filtered out by `.filter()`. This is why putting conditions in `.withIndex()` is critical.

## Index Limits

| Constraint | Limit |
|-----------|-------|
| Fields per index | 16 (including auto-appended `_creationTime`) |
| Indexes per table | 32 |
| Duplicate fields in index | Not allowed |
| Reserved field names | Fields starting with `_` |
| `.collect()` max documents | 1,024 (default) |

## Related References

- Schema definitions: `03-database-schemas.md`
- Search indexes: `08-search.md`
- Best practices: `11-best-practices.md`
