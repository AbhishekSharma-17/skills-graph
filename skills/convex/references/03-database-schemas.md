# Database & Schemas

> Source: [docs.convex.dev/database/schemas](https://docs.convex.dev/database/schemas) | convex v1.34.x

## Table of Contents

- [Schema Overview](#schema-overview)
- [Defining Tables](#defining-tables)
- [Validator Reference](#validator-reference)
- [Optional Fields](#optional-fields)
- [Union Types](#union-types)
- [Literal and Enum Patterns](#literal-and-enum-patterns)
- [Record Types](#record-types)
- [Document IDs and References](#document-ids-and-references)
- [System Fields](#system-fields)
- [Schema Options](#schema-options)
- [TypeScript Integration](#typescript-integration)
- [Schema Migrations](#schema-migrations)
- [Common Patterns](#common-patterns)

## Schema Overview

Schemas are defined in `convex/schema.ts`. They provide:

1. **Runtime validation** — Documents are validated on every insert/update
2. **TypeScript types** — Auto-generated types for all database operations
3. **Documentation** — Self-documenting data model

Schemas are optional — you can use Convex without one, but you lose type safety and validation.

```typescript
// convex/schema.ts
import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  users: defineTable({
    name: v.string(),
    email: v.string(),
    avatarUrl: v.optional(v.string()),
    role: v.union(v.literal("admin"), v.literal("user")),
  })
    .index("by_email", ["email"])
    .index("by_role", ["role"]),

  messages: defineTable({
    authorId: v.id("users"),
    channelId: v.id("channels"),
    body: v.string(),
    edited: v.optional(v.boolean()),
  })
    .index("by_channel", ["channelId"])
    .index("by_author", ["authorId"]),

  channels: defineTable({
    name: v.string(),
    description: v.optional(v.string()),
    isPrivate: v.boolean(),
  }),
});
```

## Defining Tables

```typescript
defineTable(documentValidator)
  .index(name, fields)         // Database index
  .searchIndex(name, config)   // Full-text search index
  .vectorIndex(name, config)   // Vector similarity index
```

Each table automatically gets `_id` (unique identifier) and `_creationTime` (milliseconds since epoch) system fields.

## Validator Reference

The `v` object provides all validators:

### Primitive Types

```typescript
v.string()     // JavaScript string
v.number()     // JavaScript number (float64)
v.boolean()    // true or false
v.null()       // null
v.int64()      // 64-bit integer (BigInt in JS)
v.float64()    // Explicit float64 (same as v.number())
v.bytes()      // ArrayBuffer
```

### Complex Types

```typescript
// Object with known fields
v.object({
  name: v.string(),
  age: v.number(),
})

// Array of a type
v.array(v.string())           // string[]
v.array(v.id("users"))        // Id<"users">[]
v.array(v.object({            // Array of objects
  key: v.string(),
  value: v.number(),
}))

// Document reference
v.id("tableName")             // Id<"tableName">

// Optional (field can be omitted)
v.optional(v.string())        // string | undefined

// Union (multiple possible types)
v.union(v.string(), v.number())  // string | number

// Literal (exact value)
v.literal("active")           // "active"
v.literal(42)                 // 42
v.literal(true)               // true

// Record (dynamic keys)
v.record(v.string(), v.number())  // Record<string, number>
v.record(v.id("users"), v.boolean())  // Record<Id<"users">, boolean>

// Any (escape hatch — avoid in production)
v.any()                        // any
```

## Optional Fields

Mark fields as not required with `v.optional()`:

```typescript
defineTable({
  name: v.string(),              // Required
  bio: v.optional(v.string()),   // Optional string
  avatar: v.optional(v.id("_storage")),  // Optional file reference
})
```

Optional fields can be:
- Omitted entirely from the document
- Set to `undefined`
- Set to a valid value of the inner type

## Union Types

### Simple Value Unions

```typescript
defineTable({
  // Field can be string or number
  value: v.union(v.string(), v.number()),
})
```

### Discriminated Unions (Multiple Document Shapes)

```typescript
defineTable(
  v.union(
    v.object({
      type: v.literal("text"),
      body: v.string(),
    }),
    v.object({
      type: v.literal("image"),
      storageId: v.id("_storage"),
      caption: v.optional(v.string()),
    }),
    v.object({
      type: v.literal("link"),
      url: v.string(),
      title: v.string(),
    }),
  )
)
```

## Literal and Enum Patterns

```typescript
// Status enum pattern
defineTable({
  status: v.union(
    v.literal("draft"),
    v.literal("published"),
    v.literal("archived"),
  ),
})

// Reusable validator pattern
const statusValidator = v.union(
  v.literal("draft"),
  v.literal("published"),
  v.literal("archived"),
);

defineTable({
  status: statusValidator,
  previousStatus: v.optional(statusValidator),
})
```

## Record Types

For dynamic key-value maps:

```typescript
defineTable({
  // Map user IDs to permission levels
  permissions: v.record(v.id("users"), v.union(
    v.literal("read"),
    v.literal("write"),
    v.literal("admin"),
  )),

  // Map string keys to any value
  metadata: v.record(v.string(), v.any()),
})
```

**Constraints:**
- Keys must be string-type validators (not literals)
- `v.string()` keys accept only ASCII characters
- Nested records are allowed

## Document IDs and References

Every document has a unique `_id` of type `Id<"tableName">`:

```typescript
// Reference another table
defineTable({
  authorId: v.id("users"),      // References users table
  channelId: v.id("channels"),  // References channels table
})

// Using IDs in functions
export const getMessage = query({
  args: { messageId: v.id("messages") },
  handler: async (ctx, args) => {
    const message = await ctx.db.get(args.messageId);
    if (!message) return null;

    // Follow the reference
    const author = await ctx.db.get(message.authorId);
    return { ...message, author };
  },
});
```

### Circular References

Handle circular dependencies by making one side nullable:

```typescript
defineSchema({
  users: defineTable({
    teamId: v.id("teams"),
  }),
  teams: defineTable({
    ownerId: v.union(v.id("users"), v.null()),
  }),
});

// Create in order, then patch
const teamId = await ctx.db.insert("teams", { ownerId: null });
const userId = await ctx.db.insert("users", { teamId });
await ctx.db.patch(teamId, { ownerId: userId });
```

## System Fields

Every document automatically includes:

| Field | Type | Description |
|-------|------|-------------|
| `_id` | `Id<"tableName">` | Unique document identifier |
| `_creationTime` | `number` | Creation timestamp (ms since epoch) |

These are read-only and cannot be set manually. They don't need to be in your schema definition.

## Schema Options

```typescript
defineSchema(
  { /* tables */ },
  {
    // Disable runtime validation (keep types only)
    schemaValidation: false,

    // Allow accessing undefined tables (typed as any)
    strictTableNameTypes: false,
  }
);
```

## TypeScript Integration

Running `npx convex dev` generates types in `convex/_generated/`:

```typescript
// Use Doc<> type for document types
import { Doc, Id } from "../convex/_generated/dataModel";

type Message = Doc<"messages">;
// { _id: Id<"messages">, _creationTime: number, body: string, authorId: Id<"users">, ... }

// Use in React components
function MessageCard({ message }: { message: Doc<"messages"> }) {
  return <div>{message.body}</div>;
}

// Use Id<> for typed references
function getUser(userId: Id<"users">) { /* ... */ }
```

## Schema Migrations

Convex validates your schema on deployment:

1. **Adding a table** — Always safe
2. **Adding an optional field** — Safe (existing docs don't need it)
3. **Adding a required field** — Fails if existing docs lack the field
4. **Removing a field** — Safe (extra fields are ignored after removal)
5. **Changing a field type** — Fails if existing data doesn't match

### Migration Pattern

```typescript
// Step 1: Add the new field as optional
// messages: defineTable({ body: v.string(), formattedBody: v.optional(v.string()) })

// Step 2: Run a migration mutation to backfill
export const migrateMessages = internalMutation({
  handler: async (ctx) => {
    const messages = await ctx.db.query("messages").take(100);
    for (const msg of messages) {
      if (msg.formattedBody === undefined) {
        await ctx.db.patch(msg._id, {
          formattedBody: formatMarkdown(msg.body),
        });
      }
    }
    // Return whether there are more to process
    return messages.length === 100;
  },
});

// Step 3: After all docs migrated, make the field required
// messages: defineTable({ body: v.string(), formattedBody: v.string() })
```

## Common Patterns

### Soft Delete

```typescript
defineTable({
  // ... other fields
  deletedAt: v.optional(v.number()),
}).index("by_active", ["deletedAt"])

// Query only active documents
const active = await ctx.db
  .query("items")
  .withIndex("by_active", (q) => q.eq("deletedAt", undefined))
  .collect();
```

### Timestamps

```typescript
defineTable({
  createdAt: v.number(),
  updatedAt: v.number(),
})

// In mutation
await ctx.db.insert("items", {
  ...args,
  createdAt: Date.now(),
  updatedAt: Date.now(),
});

await ctx.db.patch(itemId, {
  ...updates,
  updatedAt: Date.now(),
});
```

### Denormalization

```typescript
// Store computed/derived data for fast reads
defineTable({
  authorId: v.id("users"),
  authorName: v.string(),  // Denormalized from users table
  body: v.string(),
})
```

## Related References

- Indexes and performance: `04-indexes-performance.md`
- Validators in functions: `01-functions-queries-mutations.md`
- Search indexes: `08-search.md`
