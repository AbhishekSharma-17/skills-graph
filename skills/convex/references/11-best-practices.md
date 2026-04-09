# Best Practices & Patterns

> Source: [docs.convex.dev/understanding/best-practices](https://docs.convex.dev/understanding/best-practices) | convex v1.34.x

## Table of Contents

- [Await All Promises](#await-all-promises)
- [Database Query Optimization](#database-query-optimization)
- [Argument Validation](#argument-validation)
- [Access Control](#access-control)
- [Internal Functions](#internal-functions)
- [Code Organization](#code-organization)
- [Action Best Practices](#action-best-practices)
- [Table Name Safety](#table-name-safety)
- [Avoid Date.now() in Queries](#avoid-datenow-in-queries)
- [ESLint Rules](#eslint-rules)
- [Security Patterns](#security-patterns)
- [Common Anti-Patterns](#common-anti-patterns)

## Await All Promises

Always `await` async operations in Convex functions. Dangling promises cause silent failures:

```typescript
// BAD: Missing await — scheduler call may silently fail
export const bad = mutation({
  handler: async (ctx) => {
    ctx.scheduler.runAfter(0, internal.tasks.process, {}); // No await!
    ctx.db.patch(id, { status: "pending" }); // No await!
  },
});

// GOOD: All promises awaited
export const good = mutation({
  handler: async (ctx) => {
    await ctx.scheduler.runAfter(0, internal.tasks.process, {});
    await ctx.db.patch(id, { status: "pending" });
  },
});
```

**Enforcement:** Enable `@typescript-eslint/no-floating-promises` in ESLint.

## Database Query Optimization

### Use Indexes Instead of Filters

```typescript
// SLOW: Scans entire table, then filters in memory
const results = await ctx.db
  .query("orders")
  .filter((q) => q.eq(q.field("userId"), userId))
  .collect();

// FAST: Index narrows directly to matching documents
const results = await ctx.db
  .query("orders")
  .withIndex("by_user", (q) => q.eq("userId", userId))
  .collect();
```

### Limit Results with .take() or .first()

```typescript
// BAD: Loads all documents into memory
const all = await ctx.db.query("messages").collect();

// GOOD: Only load what you need
const recent = await ctx.db.query("messages").order("desc").take(50);
const latest = await ctx.db.query("messages").order("desc").first();
```

### Be Careful with .collect()

All documents returned by `.collect()` count toward database bandwidth — including those later filtered out by `.filter()`. The `.collect()` method throws if more than 1024 documents match.

**Enforcement:** Enable `@convex-dev/no-collect-in-query` ESLint rule.

### Eliminate Redundant Indexes

If you have `by_foo` and `by_foo_and_bar`, the first is redundant — the compound index covers single-field queries on `foo`. Exception: different sort orders require separate indexes.

## Argument Validation

Every public function must have argument validators:

```typescript
// BAD: No validation — security risk
export const bad = mutation({
  handler: async (ctx, args: any) => {
    await ctx.db.insert("users", args);
  },
});

// GOOD: Full validation
export const good = mutation({
  args: {
    name: v.string(),
    email: v.string(),
    role: v.union(v.literal("user"), v.literal("admin")),
  },
  handler: async (ctx, args) => {
    await ctx.db.insert("users", args);
  },
});
```

**Enforcement:** Enable `@convex-dev/require-argument-validators` ESLint rule.

## Access Control

### Check Auth in Every Public Function

```typescript
export const createPost = mutation({
  args: { title: v.string() },
  handler: async (ctx, args) => {
    const identity = await ctx.auth.getUserIdentity();
    if (!identity) throw new Error("Not authenticated");

    await ctx.db.insert("posts", {
      title: args.title,
      authorId: identity.subject,
    });
  },
});
```

### Use Unguessable IDs for Access Control

```typescript
// BAD: Email is spoofable
const user = await ctx.db
  .query("users")
  .filter((q) => q.eq(q.field("email"), args.email))
  .first();

// GOOD: Use Convex document IDs or UUIDs
const user = await ctx.db.get(args.userId);  // ID is unguessable
```

### Prefer Granular Functions

```typescript
// BAD: Generic update — attacker could modify any field
export const updateUser = mutation({
  args: { userId: v.id("users"), data: v.any() },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.userId, args.data);
  },
});

// GOOD: Specific function with specific fields
export const updateUserName = mutation({
  args: { name: v.string() },
  handler: async (ctx, args) => {
    const identity = await ctx.auth.getUserIdentity();
    if (!identity) throw new Error("Not authenticated");
    const user = await getUserByToken(ctx, identity.tokenIdentifier);
    await ctx.db.patch(user._id, { name: args.name });
  },
});
```

## Internal Functions

Use `internal` references (not `api`) for functions called within Convex:

```typescript
// BAD: api.foo is publicly callable
await ctx.scheduler.runAfter(0, api.tasks.process, { taskId });

// GOOD: internal.foo is only callable from Convex functions
await ctx.scheduler.runAfter(0, internal.tasks.process, { taskId });
```

Internal functions:
- Cannot be called from clients
- Don't need argument validators (though they're still recommended)
- Are the safe choice for scheduled functions, runQuery/runMutation targets

## Code Organization

### Helper Functions Over Deep Nesting

```typescript
// convex/model/users.ts — plain TypeScript helpers
import { QueryCtx } from "../_generated/server";

export async function getCurrentUser(ctx: QueryCtx) {
  const identity = await ctx.auth.getUserIdentity();
  if (!identity) return null;
  return await ctx.db
    .query("users")
    .withIndex("by_token", (q) =>
      q.eq("tokenIdentifier", identity.tokenIdentifier)
    )
    .unique();
}

export async function requireUser(ctx: QueryCtx) {
  const user = await getCurrentUser(ctx);
  if (!user) throw new Error("Not authenticated");
  return user;
}
```

### Thin Function Wrappers

Keep `query`, `mutation`, `action` exports thin. Move logic to helpers:

```typescript
// convex/tasks.ts
import { requireUser } from "./model/users";
import { createTask, getTasksForUser } from "./model/tasks";

export const list = query({
  args: {},
  handler: async (ctx) => {
    const user = await requireUser(ctx);
    return await getTasksForUser(ctx, user._id);
  },
});

export const create = mutation({
  args: { text: v.string() },
  handler: async (ctx, args) => {
    const user = await requireUser(ctx);
    return await createTask(ctx, user._id, args.text);
  },
});
```

### Suggested Directory Structure

```
convex/
├── _generated/        # Auto-generated (don't edit)
├── model/             # Business logic helpers
│   ├── users.ts
│   ├── tasks.ts
│   └── permissions.ts
├── schema.ts          # Database schema
├── auth.ts            # Auth config
├── http.ts            # HTTP routes
├── crons.ts           # Cron jobs
├── users.ts           # User-facing functions
├── tasks.ts           # Task functions
└── internal.ts        # Shared internal functions
```

## Action Best Practices

### Use runAction Sparingly

```typescript
// BAD: Unnecessary overhead
const result = await ctx.runAction(internal.utils.format, { text });

// GOOD: Plain function call (same runtime)
const result = formatText(text);
```

Only use `ctx.runAction` when you need a different runtime (Node.js from Convex or vice versa).

### Batch Database Operations

```typescript
// BAD: Multiple transactions, possible inconsistency
await ctx.runMutation(internal.orders.create, { items });
await ctx.runMutation(internal.inventory.deduct, { items });

// GOOD: Single transaction
await ctx.runMutation(internal.orders.createAndDeductInventory, { items });
```

## Table Name Safety

Always pass table names explicitly:

```typescript
// Recommended
await ctx.db.get("tasks", taskId);
await ctx.db.patch("tasks", taskId, { done: true });
await ctx.db.delete("tasks", taskId);
```

**Enforcement:** Enable `@convex-dev/explicit-table-ids` ESLint rule.

## Avoid Date.now() in Queries

Queries with `Date.now()` break caching and reactivity:

```typescript
// BAD: Query re-runs on every subscription tick
export const recentMessages = query({
  handler: async (ctx) => {
    const cutoff = Date.now() - 60000; // Not reactive!
    return await ctx.db
      .query("messages")
      .filter((q) => q.gt(q.field("_creationTime"), cutoff))
      .collect();
  },
});

// GOOD: Accept timestamp from client
export const recentMessages = query({
  args: { since: v.number() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("messages")
      .withIndex("by_creation_time", (q) =>
        q.gt("_creationTime", args.since)
      )
      .collect();
  },
});
```

## ESLint Rules

Install the Convex ESLint plugin:

```bash
npm install @convex-dev/eslint-plugin
```

Recommended rules:

| Rule | Purpose |
|------|---------|
| `@convex-dev/require-argument-validators` | All public functions must have arg validators |
| `@convex-dev/no-collect-in-query` | Warns on `.collect()` without limits |
| `@convex-dev/explicit-table-ids` | Requires table name in db.get/patch/delete |
| `@typescript-eslint/no-floating-promises` | Catches missing await |

## Security Patterns

1. **Validate all public function arguments** with `v` validators
2. **Check authentication** in every public function
3. **Use internal functions** for scheduled work and cross-function calls
4. **Use environment variables** for secrets (never hardcode)
5. **Validate webhook signatures** before processing
6. **Use specific functions** instead of generic update endpoints
7. **Never trust client-provided user IDs** — derive from auth token

## Common Anti-Patterns

| Anti-Pattern | Better Approach |
|-------------|-----------------|
| Calling actions directly from client | Mutation captures intent, schedules action |
| Using `api.foo` for scheduled functions | Use `internal.foo` |
| Multiple `runQuery`/`runMutation` in action | Single internal function for atomicity |
| `.collect()` without limits on large tables | `.take(n)`, pagination, or index constraints |
| `Date.now()` in queries | Accept timestamp as argument |
| Generic `update(id, data)` endpoints | Specific named mutations per operation |
| Missing `await` on promises | Always await; enable ESLint rule |

## Related References

- Functions: `01-functions-queries-mutations.md`, `02-functions-actions-http.md`
- Indexes: `04-indexes-performance.md`
- Auth: `05-authentication.md`
- Testing: `12-testing-deployment.md`
