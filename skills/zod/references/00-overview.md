# Zod Overview

> Source: [zod.dev](https://zod.dev)

## Table of Contents

- [What is Zod](#what-is-zod)
- [Key Features](#key-features)
- [Installation](#installation)
- [Core Concepts](#core-concepts)
- [Basic Usage](#basic-usage)
- [Parsing vs Safe Parsing](#parsing-vs-safe-parsing)
- [Zod Mini](#zod-mini)
- [TypeScript Requirements](#typescript-requirements)
- [When to Use Zod](#when-to-use-zod)

---

## What is Zod

Zod is a TypeScript-first schema declaration and validation library. You define a schema, and Zod guarantees that data conforms to it at runtime while providing full static type inference at compile time.

Key value proposition: **define once, get both runtime validation and TypeScript types**.

```typescript
import { z } from "zod";

const UserSchema = z.object({
  name: z.string(),
  email: z.email(),
  age: z.number().int().positive(),
});

// Infer the TypeScript type from the schema
type User = z.infer<typeof UserSchema>;
// { name: string; email: string; age: number }

// Runtime validation
const user = UserSchema.parse(someInput);
```

## Key Features

- **Zero dependencies** — no external packages required
- **Tiny bundle** — 2kb gzipped core
- **Immutable API** — all methods return new schema instances
- **Composable** — schemas compose with `.extend()`, `.merge()`, `.pipe()`
- **Rich ecosystem** — integrates with tRPC, React Hook Form, Prisma, and more
- **JSON Schema** — native conversion to/from JSON Schema
- **Codecs** — bidirectional transforms (new in v4)
- **Registries** — attach structured metadata to schemas
- **35+ locales** — built-in i18n for error messages
- **Works everywhere** — Node.js, browsers, edge runtimes

## Installation

```bash
# npm
npm install zod

# pnpm
pnpm add zod

# yarn
yarn add zod

# bun
bun add zod
```

### Zod Mini (tree-shakable)

```bash
npm install @zod/mini
```

Import from the mini package:

```typescript
import { z } from "zod/mini";
```

## Core Concepts

### Schema Definition

A schema is a validator that describes the shape and constraints of data:

```typescript
// Primitive schemas
const name = z.string();
const age = z.number();
const active = z.boolean();

// Object schemas
const Player = z.object({
  username: z.string(),
  xp: z.number(),
  active: z.boolean(),
});
```

### Parsing

`.parse()` validates input and returns a typed, deeply-cloned result:

```typescript
const result = Player.parse({
  username: "billie",
  xp: 100,
  active: true,
});
// result is typed as { username: string; xp: number; active: boolean }
```

If validation fails, `.parse()` throws a `ZodError`:

```typescript
try {
  Player.parse({ username: 42 });
} catch (e) {
  if (e instanceof z.ZodError) {
    console.log(e.issues);
  }
}
```

### Type Inference

Extract TypeScript types from any schema:

```typescript
type Player = z.infer<typeof Player>;
// { username: string; xp: number; active: boolean }
```

For schemas with transforms (different input/output types):

```typescript
const schema = z.string().transform((val) => val.length);
type Input = z.input<typeof schema>;   // string
type Output = z.output<typeof schema>; // number
```

## Basic Usage

### Defining and Parsing

```typescript
import { z } from "zod";

// Define schema
const Config = z.object({
  host: z.string(),
  port: z.number().int().positive(),
  debug: z.boolean().default(false),
});

// Parse unknown data (e.g., from JSON, env vars, API)
const config = Config.parse(JSON.parse(rawJson));
// config is fully typed: { host: string; port: number; debug: boolean }
```

### Async Parsing

For schemas with async refinements or transforms:

```typescript
const schema = z.string().refine(async (val) => {
  return await checkUniqueness(val);
});

const result = await schema.parseAsync("hello");
```

## Parsing vs Safe Parsing

### `.parse()` — Throws on Failure

```typescript
// Throws ZodError if invalid
const data = schema.parse(input);
```

### `.safeParse()` — Returns Result Object

```typescript
const result = schema.safeParse(input);

if (result.success) {
  console.log(result.data); // typed output
} else {
  console.log(result.error); // ZodError
}
```

### Async variants

```typescript
await schema.parseAsync(input);
await schema.safeParseAsync(input);
```

## Zod Mini

Zod Mini (`@zod/mini`) is a tree-shakable distribution weighing ~1.9kb gzipped:

```typescript
import { z } from "zod/mini";

const schema = z.object({
  name: z.string(),
  age: z.number(),
});
```

Key differences from full Zod:
- No built-in string validations (use `.check()` instead)
- Requires explicit locale configuration
- Designed for bundle-sensitive frontend applications
- Same type inference capabilities

## TypeScript Requirements

- **TypeScript 5.5+** required
- **`strict: true`** must be enabled in `tsconfig.json`
- Both `zod` and `@zod/mini` require strict mode

```json
{
  "compilerOptions": {
    "strict": true
  }
}
```

## When to Use Zod

**Ideal for:**
- API request/response validation
- Form input validation
- Environment variable parsing
- Configuration file validation
- Runtime type checking at system boundaries
- Data transformation pipelines
- OpenAPI/JSON Schema generation
- LLM structured output validation

**Not needed for:**
- Internal function arguments (TypeScript handles this)
- Performance-critical hot paths (adds overhead)
- Simple type assertions (use `as` or type guards)

## Common Patterns

### Environment Variables

```typescript
const EnvSchema = z.object({
  DATABASE_URL: z.string().url(),
  PORT: z.coerce.number().int().default(3000),
  NODE_ENV: z.enum(["development", "production", "test"]),
  DEBUG: z.coerce.boolean().default(false),
});

export const env = EnvSchema.parse(process.env);
```

### API Response Validation

```typescript
const ApiResponse = z.object({
  data: z.array(UserSchema),
  pagination: z.object({
    page: z.number(),
    totalPages: z.number(),
  }),
});

const response = await fetch("/api/users");
const validated = ApiResponse.parse(await response.json());
```

### Discriminated Union for Events

```typescript
const Event = z.discriminatedUnion("type", [
  z.object({ type: z.literal("click"), x: z.number(), y: z.number() }),
  z.object({ type: z.literal("keypress"), key: z.string() }),
  z.object({ type: z.literal("scroll"), delta: z.number() }),
]);

type Event = z.infer<typeof Event>;
```
