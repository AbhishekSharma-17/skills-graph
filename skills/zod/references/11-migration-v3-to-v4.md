# Migration Guide: Zod v3 to v4

> Source: [zod.dev/v4/changelog](https://zod.dev/v4/changelog)

## Table of Contents

- [Overview](#overview)
- [Error API Changes](#error-api-changes)
- [String Format Changes](#string-format-changes)
- [Object Schema Changes](#object-schema-changes)
- [Number and Integer Changes](#number-and-integer-changes)
- [Default and Coercion Changes](#default-and-coercion-changes)
- [Function Schema Changes](#function-schema-changes)
- [Refinement Changes](#refinement-changes)
- [Record and Intersection Changes](#record-and-intersection-changes)
- [Removed APIs](#removed-apis)
- [Internal Architecture Changes](#internal-architecture-changes)
- [Automated Migration](#automated-migration)

---

## Overview

Zod v4 was released as stable on July 10, 2025. Key themes:
- **14x faster** string parsing, 7x faster array parsing
- **100x fewer** TypeScript instantiations
- **Unified error API** (replaces fragmented error params)
- **Top-level string formats** (e.g., `z.email()` instead of `z.string().email()`)
- **Native JSON Schema** conversion
- **Codecs** for bidirectional transforms
- **Registries** for schema metadata

## Error API Changes

### `message` → `error`

```typescript
// v3
z.string({ message: "Bad!" });
z.string().min(5, { message: "Too short" });

// v4
z.string({ error: "Bad!" });
z.string().min(5, { error: "Too short" });
```

### `invalid_type_error` / `required_error` → `error` Function

```typescript
// v3
z.string({
  invalid_type_error: "Not a string",
  required_error: "Required",
});

// v4
z.string({
  error: (issue) =>
    issue.input === undefined ? "Required" : "Not a string",
});
```

### `errorMap` → `error`

```typescript
// v3
z.string().min(5, {
  errorMap: (issue) => ({
    message: issue.code === "too_small"
      ? `Min ${issue.minimum}`
      : "Invalid",
  }),
});

// v4
z.string().min(5, {
  error: (issue) => {
    if (issue.code === "too_small") return `Min ${issue.minimum}`;
    return undefined; // defer to default
  },
});
```

### ZodError Methods

```typescript
// v3
error.format();  // deprecated in v4
error.flatten(); // deprecated in v4

// v4
z.treeifyError(error);    // replaces .format()
z.flattenError(error);    // standalone function
z.prettifyError(error);   // new: readable string output
```

### Schema-Level Precedence

In v4, schema-level error maps take **precedence** over per-parse error maps (reversed from v3).

## String Format Changes

Formats moved to top-level functions:

```typescript
// v3                        → v4
z.string().email()           → z.email()
z.string().url()             → z.url()
z.string().uuid()            → z.uuid() (stricter) or z.guid() (lenient)
z.string().ip()              → z.ipv4() or z.ipv6()
z.string().cidr()            → z.cidrv4() or z.cidrv6()
z.string().datetime()        → z.iso.datetime()
z.string().date()            → z.iso.date()
z.string().time()            → z.iso.time()
z.string().duration()        → z.iso.duration()
z.string().base64()          → z.base64()
```

**Breaking**: `z.uuid()` in v4 enforces RFC 9562/4122. Use `z.guid()` for v3-compatible lenient UUID validation.

**Breaking**: `z.base64url()` no longer allows padding characters.

## Object Schema Changes

### `.strict()` / `.passthrough()` → Constructor Functions

```typescript
// v3
z.object({ name: z.string() }).strict();
z.object({ name: z.string() }).passthrough();

// v4
z.strictObject({ name: z.string() });
z.looseObject({ name: z.string() });
```

### Defaults in Optional Fields

```typescript
const schema = z.object({
  a: z.string().default("tuna").optional(),
});

// v3: schema.parse({}) → {}
// v4: schema.parse({}) → { a: "tuna" }
```

In v4, defaults apply even within optional fields.

### Removed Methods

- `.strip()` — removed (default behavior)
- `.nonstrict()` — removed
- `.deepPartial()` — removed
- `.merge()` — deprecated, use `.extend()` instead

## Number and Integer Changes

- `z.number()` rejects `Infinity` and `-Infinity`
- `.safe()` now behaves like `.int()` (integers only, not safe floats)
- `z.int()` validates safe integers (`Number.MIN_SAFE_INTEGER` to `MAX_SAFE_INTEGER`)

## Default and Coercion Changes

### `.default()` Accepts Output Type

```typescript
// v3: .default() accepts input type
z.string().transform(s => s.length).default("hello");

// v4: .default() accepts output type
z.string().transform(s => s.length).default(0);

// v4: use .prefault() for input-type default
z.string().transform(s => s.length).prefault("hello");
```

### `z.coerce.*` Input Type

All coerce schemas now accept `unknown` input (not just specific types).

## Function Schema Changes

`z.function()` is no longer a schema — it's a factory function:

```typescript
// v3
const fn = z.function()
  .args(z.string(), z.number())
  .returns(z.boolean());

// v4
const fn = z.function({
  input: [z.string(), z.number()],
  output: z.boolean(),
});

// Implementation
fn.implement((str, num) => str.length > num);
fn.implementAsync(async (str, num) => str.length > num);
```

### `z.promise()` Removed

```typescript
// v3
z.promise(z.string());

// v4: await before parsing
const result = schema.parse(await promise);
```

## Refinement Changes

### Type Predicates Ignored

```typescript
// v3: type narrowing worked
z.string().refine((s): s is "hello" => s === "hello");

// v4: type predicates are ignored by .refine()
// Use z.custom<T>() for type narrowing instead
```

### `ctx.path` Removed

```typescript
// v3
z.string().superRefine((val, ctx) => {
  console.log(ctx.path); // available
});

// v4: ctx.path removed for performance
// Use the path option in addIssue() instead
```

### Function Overload Removed

```typescript
// v3: second-argument function
z.string().refine(
  (val) => val.length > 5,
  (val) => ({ message: `${val} is too short` })
);

// v4: use error option
z.string().refine(
  (val) => val.length > 5,
  { error: "Too short" }
);
```

## Record and Intersection Changes

### `z.record()` — Single Argument Removed

```typescript
// v3
z.record(z.number()); // Record<string, number>

// v4: must provide both key and value schemas
z.record(z.string(), z.number());
```

### `z.intersection()` Error Type

In v4, `z.intersection()` throws a regular `Error` (not `ZodError`) for unmergeable results.

## Removed APIs

| Removed | Replacement |
|---|---|
| `z.ostring()`, `z.onumber()`, etc. | `z.string().optional()` |
| `z.literal()` with `symbol` | Not supported |
| Static `.create()` factories | Direct constructors |
| `ZodEffects` class | Internal |
| `ZodPreprocess` class | Returns `ZodPipe` |
| `ZodBranded` class | Internal |
| `z.nativeEnum()` | `z.enum()` (overloaded) |
| `.nonempty()` type narrowing | Returns `T[]` not `[T, ...T[]]` |
| `z.unknown()` optionality | No longer optional in objects |

## Internal Architecture Changes

- `ZodType<Output, Input>` — simplified generic (removed `Def`)
- `._def` moved to `._zod.def`
- Check `"_zod" in schema` to distinguish v4 from v3

## Automated Migration

Use the community codemod:

```bash
npx zod-v3-to-v4
```

This handles most mechanical changes. Manual review needed for:
- UUID validation (stricter in v4)
- Default behavior in optional fields
- Error map precedence changes
- `.safe()` behavior change
