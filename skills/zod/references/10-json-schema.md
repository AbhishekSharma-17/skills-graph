# JSON Schema Conversion

> Source: [zod.dev/json-schema](https://zod.dev/json-schema)

## Table of Contents

- [Overview](#overview)
- [Basic Conversion](#basic-conversion)
- [Configuration Options](#configuration-options)
- [Target Formats](#target-formats)
- [Type Mappings](#type-mappings)
- [Handling Unrepresentable Types](#handling-unrepresentable-types)
- [Custom Overrides](#custom-overrides)
- [Registry-Based Conversion](#registry-based-conversion)
- [Common Patterns](#common-patterns)

---

## Overview

Zod v4 includes native JSON Schema conversion. This is essential for:

- OpenAPI specification generation
- AI structured output definitions (LLM tool schemas)
- API documentation
- Cross-language schema sharing
- Form schema generation

## Basic Conversion

```typescript
import { z } from "zod";

const User = z.object({
  name: z.string(),
  email: z.email(),
  age: z.number().int().positive(),
});

const jsonSchema = z.toJSONSchema(User);
// {
//   type: "object",
//   properties: {
//     name: { type: "string" },
//     email: { type: "string", format: "email" },
//     age: { type: "integer", exclusiveMinimum: 0 }
//   },
//   required: ["name", "email", "age"],
//   additionalProperties: false
// }
```

## Configuration Options

`z.toJSONSchema()` accepts an options object:

```typescript
z.toJSONSchema(schema, {
  target: "draft-2020-12",  // JSON Schema version
  io: "output",             // input or output type
  unrepresentable: "throw", // how to handle non-JSON types
  cycles: "ref",            // handle recursive schemas
  reused: "inline",         // handle duplicate schemas
  metadata: myRegistry,     // attach registry metadata
});
```

### `target` — JSON Schema Version

```typescript
z.toJSONSchema(schema, { target: "draft-2020-12" }); // default
z.toJSONSchema(schema, { target: "draft-07" });
z.toJSONSchema(schema, { target: "draft-04" });
z.toJSONSchema(schema, { target: "openapi-3.0" });
```

### `io` — Input vs Output Type

```typescript
// Output type (default) — represents the parsed result
z.toJSONSchema(schema, { io: "output" });

// Input type — represents what the schema accepts
z.toJSONSchema(schema, { io: "input" });
```

This matters for schemas with transforms or defaults.

### `unrepresentable` — Non-JSON Types

```typescript
// Throw error for non-representable types (default)
z.toJSONSchema(schema, { unrepresentable: "throw" });

// Convert to {} (accepts anything)
z.toJSONSchema(schema, { unrepresentable: "any" });
```

### `cycles` — Recursive Schemas

```typescript
// Use $ref for cycles (default)
z.toJSONSchema(schema, { cycles: "ref" });

// Throw error on cycles
z.toJSONSchema(schema, { cycles: "throw" });
```

### `reused` — Duplicate Schema Definitions

```typescript
// Inline duplicates (default)
z.toJSONSchema(schema, { reused: "inline" });

// Extract to $defs with $ref
z.toJSONSchema(schema, { reused: "ref" });
```

## Target Formats

### OpenAPI 3.0

```typescript
z.toJSONSchema(schema, { target: "openapi-3.0" });
```

Differences from standard JSON Schema:
- Uses `nullable: true` instead of `oneOf` with `null`
- Omits `$schema` keyword
- Uses OpenAPI-compatible formats

### Draft-07

```typescript
z.toJSONSchema(schema, { target: "draft-07" });
```

Uses `exclusiveMinimum` as a boolean property (not a number).

## Type Mappings

| Zod Type | JSON Schema |
|---|---|
| `z.string()` | `{ type: "string" }` |
| `z.number()` | `{ type: "number" }` |
| `z.int()` | `{ type: "integer" }` |
| `z.boolean()` | `{ type: "boolean" }` |
| `z.null()` | `{ type: "null" }` |
| `z.literal("x")` | `{ const: "x" }` |
| `z.enum(["a","b"])` | `{ enum: ["a", "b"] }` |
| `z.array(z.string())` | `{ type: "array", items: { type: "string" } }` |
| `z.object({...})` | `{ type: "object", properties: {...}, additionalProperties: false }` |
| `z.union([...])` | `{ oneOf: [...] }` |
| `z.optional(x)` | Removes from `required` array |
| `z.nullable(x)` | `{ oneOf: [x, { type: "null" }] }` |
| `z.email()` | `{ type: "string", format: "email" }` |
| `z.uuid()` | `{ type: "string", format: "uuid" }` |
| `z.url()` | `{ type: "string", format: "uri" }` |
| `z.iso.datetime()` | `{ type: "string", format: "date-time" }` |
| `z.iso.date()` | `{ type: "string", format: "date" }` |
| `z.base64()` | `{ type: "string", contentEncoding: "base64" }` |
| `z.file()` | `{ type: "string", format: "binary" }` |

## Handling Unrepresentable Types

These Zod types cannot be represented in JSON Schema:

- `z.bigint()`, `z.int64()`, `z.symbol()`
- `z.undefined()`, `z.void()`
- `z.date()`, `z.map()`, `z.set()`
- `z.transform()`, `z.nan()`, `z.custom()`

With `unrepresentable: "any"`, they become `{}` (accepts anything).

## Custom Overrides

Override the JSON Schema for specific types:

```typescript
z.toJSONSchema(z.date(), {
  unrepresentable: "any",
  override: (ctx) => {
    if (ctx.zodSchema instanceof z.ZodDate) {
      ctx.jsonSchema = {
        type: "string",
        format: "date-time",
      };
    }
  },
});
```

The `ctx` object provides:
- `zodSchema` — the Zod schema being converted
- `jsonSchema` — the generated JSON Schema (mutable)

## Registry-Based Conversion

Generate interconnected schemas using registries:

```typescript
const Address = z.object({
  street: z.string(),
  city: z.string(),
}).meta({ id: "Address" });

const User = z.object({
  name: z.string(),
  address: Address,
}).meta({ id: "User" });

// Convert entire registry
const schemas = z.toJSONSchema(z.globalRegistry, {
  uri: (id) => `https://api.example.com/schemas/${id}.json`,
});
```

This generates schemas with proper `$ref` URIs for cross-referencing.

## Common Patterns

### LLM Tool Schema

```typescript
const ToolParams = z.object({
  query: z.string().meta({ description: "Search query" }),
  limit: z.number().int().default(10).meta({ description: "Max results" }),
  filters: z.object({
    category: z.enum(["news", "docs", "code"]).optional(),
    language: z.string().optional(),
  }).optional(),
});

const toolSchema = z.toJSONSchema(ToolParams);
// Ready for OpenAI function calling or Anthropic tool use
```

### OpenAPI Endpoint Schema

```typescript
const CreateUserRequest = z.object({
  name: z.string().min(1).max(100),
  email: z.email(),
  role: z.enum(["admin", "user"]).default("user"),
});

const schema = z.toJSONSchema(CreateUserRequest, {
  target: "openapi-3.0",
  io: "input",
});
```

### Experimental: fromJSONSchema

```typescript
// Convert JSON Schema back to Zod (experimental)
const zodSchema = z.fromJSONSchema({
  type: "object",
  properties: {
    name: { type: "string" },
    age: { type: "integer" },
  },
  required: ["name", "age"],
});
```

**Warning**: `z.fromJSONSchema()` is experimental and not part of Zod's stable API.
