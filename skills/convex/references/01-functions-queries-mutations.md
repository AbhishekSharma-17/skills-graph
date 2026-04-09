# Functions: Queries & Mutations

> Source: [docs.convex.dev/functions](https://docs.convex.dev/functions) | convex v1.34.x

## Table of Contents

- [Queries](#queries)
- [Query Context](#query-context)
- [Mutations](#mutations)
- [Mutation Context](#mutation-context)
- [Argument Validation](#argument-validation)
- [Database Read Operations](#database-read-operations)
- [Database Write Operations](#database-write-operations)
- [Transactions and OCC](#transactions-and-occ)
- [Internal Functions](#internal-functions)
- [Helper Functions](#helper-functions)

## Queries

Queries read data from the database. They are **cached**, **reactive**, and **deterministic** — they re-execute automatically when underlying data changes, and connected clients receive updates in real-time.

### Defining a Query

```typescript
// convex/tasks.ts
import { query } from "./_generated/server";
import { v } from "convex/values";

export const getTask = query({
  args: { taskId: v.id("tasks") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.taskId);
  },
});
```

### Query Rules

- **No side effects** — Cannot call external APIs, write to database, or use `Date.now()`
- **Deterministic** — Same inputs always produce same outputs (enables caching)
- **Read-only** — Only `ctx.db` read methods available (no `insert`, `patch`, `replace`, `delete`)
- **Automatically cached** — Results cached and invalidated when underlying data changes
- **Reactive** — Client subscriptions auto-update when query results change

## Query Context

The `ctx` object in queries provides:

```typescript
ctx.db          // Database reader (query, get)
ctx.auth        // Authentication info (getUserIdentity)
ctx.storage     // File storage (getUrl, getMetadata)
```

### Reading Data

```typescript
// Get a single document by ID
const task = await ctx.db.get(args.taskId);

// Query a table (full scan)
const allTasks = await ctx.db.query("tasks").collect();

// Query with ordering
const recent = await ctx.db
  .query("tasks")
  .order("desc")  // by _creationTime descending
  .take(10);

// Get first matching document
const first = await ctx.db.query("tasks").first();

// Get exactly one document (throws if 0 or 2+)
const unique = await ctx.db.query("tasks")
  .withIndex("by_email", (q) => q.eq("email", email))
  .unique();
```

## Mutations

Mutations write data to the database. They run in **serializable ACID transactions** — either all changes commit or none do. Convex automatically retries mutations that encounter conflicts.

### Defining a Mutation

```typescript
// convex/tasks.ts
import { mutation } from "./_generated/server";
import { v } from "convex/values";

export const createTask = mutation({
  args: { text: v.string(), completed: v.boolean() },
  handler: async (ctx, args) => {
    const taskId = await ctx.db.insert("tasks", {
      text: args.text,
      completed: args.completed,
    });
    return taskId;
  },
});
```

### Mutation Rules

- **Transactional** — All database operations are atomic
- **No side effects** — Cannot call external APIs or use `fetch`
- **Deterministic** — Enables automatic conflict detection and retry
- **Can schedule** — Can schedule actions and other functions for later execution

## Mutation Context

The `ctx` object in mutations provides:

```typescript
ctx.db          // Database reader + writer
ctx.auth        // Authentication info
ctx.storage     // File storage (upload, delete)
ctx.scheduler   // Schedule future function execution
```

## Argument Validation

All public functions **must** define argument validators. This provides runtime validation and TypeScript type inference:

```typescript
import { v } from "convex/values";

export const createUser = mutation({
  args: {
    name: v.string(),
    email: v.string(),
    age: v.optional(v.number()),
    role: v.union(v.literal("admin"), v.literal("user")),
    tags: v.array(v.string()),
    metadata: v.object({
      source: v.string(),
      referrer: v.optional(v.string()),
    }),
  },
  handler: async (ctx, args) => {
    // args is fully typed based on validators above
    return await ctx.db.insert("users", args);
  },
});
```

### Validator Types

| Validator | TypeScript Type | Example |
|-----------|----------------|---------|
| `v.string()` | `string` | `"hello"` |
| `v.number()` | `number` | `42`, `3.14` |
| `v.boolean()` | `boolean` | `true` |
| `v.null()` | `null` | `null` |
| `v.int64()` | `bigint` | `123n` |
| `v.float64()` | `number` | `3.14` |
| `v.bytes()` | `ArrayBuffer` | Binary data |
| `v.id("table")` | `Id<"table">` | Document reference |
| `v.array(inner)` | `Array<T>` | `[1, 2, 3]` |
| `v.object({...})` | `{...}` | Nested objects |
| `v.optional(inner)` | `T \| undefined` | Optional fields |
| `v.union(a, b)` | `A \| B` | Multiple types |
| `v.literal(val)` | Literal type | Exact value |
| `v.any()` | `any` | Escape hatch |
| `v.record(k, v)` | `Record<K, V>` | Dynamic keys |

### Return Value Validators

```typescript
export const getCount = query({
  args: {},
  returns: v.number(),
  handler: async (ctx) => {
    const items = await ctx.db.query("items").collect();
    return items.length;
  },
});
```

## Database Read Operations

```typescript
// Get by ID (returns null if not found)
const doc = await ctx.db.get(id);

// Query a table
const results = await ctx.db.query("tableName")
  .withIndex("indexName", (q) => q.eq("field", value))
  .filter((q) => q.gt(q.field("score"), 100))
  .order("asc")  // "asc" (default) or "desc"
  .take(50);      // limit results

// Collect all results (up to 1024 docs by default)
const all = await ctx.db.query("tableName").collect();

// Pagination
const page = await ctx.db.query("tableName")
  .order("desc")
  .paginate(paginationOpts);
// Returns: { page: Doc[], isDone: boolean, continueCursor: string }
```

## Database Write Operations

```typescript
// Insert a new document (returns the new ID)
const id = await ctx.db.insert("tasks", {
  text: "Buy groceries",
  completed: false,
});

// Patch (partial update — merge fields)
await ctx.db.patch(id, {
  completed: true,
  completedAt: Date.now(),
});

// Replace (full document replacement)
await ctx.db.replace(id, {
  text: "Buy groceries",
  completed: true,
  completedAt: Date.now(),
});

// Delete a document
await ctx.db.delete(id);
```

### Table Name Safety

Always pass the table name as the first argument for ID-based operations:

```typescript
// Recommended: explicit table name
await ctx.db.get("tasks", taskId);
await ctx.db.patch("tasks", taskId, { completed: true });
await ctx.db.delete("tasks", taskId);
```

## Transactions and OCC

Convex uses **Optimistic Concurrency Control (OCC)**:

1. Mutation runs and records all reads and writes
2. At commit time, Convex checks if any read data has changed
3. If conflict detected, the mutation is **automatically retried** from scratch
4. If no conflict, all writes commit atomically

### Implications

- Mutations are retried automatically — they must be **idempotent** with respect to database state
- Side effects (API calls, emails) are forbidden in mutations because retries would duplicate them
- Use **actions** for side effects, scheduled from mutations

```typescript
// Pattern: mutation schedules an action for side effects
export const createOrder = mutation({
  args: { items: v.array(v.id("products")), userId: v.id("users") },
  handler: async (ctx, args) => {
    const orderId = await ctx.db.insert("orders", {
      userId: args.userId,
      items: args.items,
      status: "pending",
    });
    // Schedule the side-effect-having work
    await ctx.scheduler.runAfter(0, internal.orders.processPayment, {
      orderId,
    });
    return orderId;
  },
});
```

## Internal Functions

Internal functions can only be called from other Convex functions (not from clients):

```typescript
import { internalQuery, internalMutation } from "./_generated/server";

export const getUser = internalQuery({
  args: { userId: v.id("users") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.userId);
  },
});

export const updateBalance = internalMutation({
  args: { userId: v.id("users"), amount: v.number() },
  handler: async (ctx, args) => {
    const user = await ctx.db.get(args.userId);
    if (!user) throw new Error("User not found");
    await ctx.db.patch(args.userId, {
      balance: user.balance + args.amount,
    });
  },
});
```

Use `internal.moduleName.functionName` to reference them:

```typescript
import { internal } from "./_generated/api";
await ctx.runMutation(internal.users.updateBalance, { userId, amount: 50 });
```

## Helper Functions

Extract shared logic into plain TypeScript functions:

```typescript
// convex/model/users.ts
import { QueryCtx, MutationCtx } from "./_generated/server";
import { Id } from "./_generated/dataModel";

export async function getActiveUser(ctx: QueryCtx, userId: Id<"users">) {
  const user = await ctx.db.get(userId);
  if (!user || user.deletedAt) return null;
  return user;
}

// convex/tasks.ts
import { getActiveUser } from "./model/users";

export const listMyTasks = query({
  args: {},
  handler: async (ctx) => {
    const identity = await ctx.auth.getUserIdentity();
    if (!identity) throw new Error("Not authenticated");
    const user = await getActiveUser(ctx, identity.subject as Id<"users">);
    if (!user) throw new Error("User not found");
    return await ctx.db
      .query("tasks")
      .withIndex("by_user", (q) => q.eq("userId", user._id))
      .collect();
  },
});
```

## Related References

- Actions and HTTP endpoints: `02-functions-actions-http.md`
- Schema and validators: `03-database-schemas.md`
- Indexes and query performance: `04-indexes-performance.md`
- Best practices: `11-best-practices.md`
