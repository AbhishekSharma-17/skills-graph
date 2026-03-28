# Error Handling

> Source: [zod.dev/error-customization](https://zod.dev/error-customization), [zod.dev/error-formatting](https://zod.dev/error-formatting)

## Table of Contents

- [ZodError](#zoderror)
- [Error Customization](#error-customization)
- [Error Maps](#error-maps)
- [Error Precedence](#error-precedence)
- [Error Formatting](#error-formatting)
- [Internationalization](#internationalization)
- [Common Patterns](#common-patterns)

---

## ZodError

When `.parse()` fails, it throws a `ZodError` containing an `.issues` array:

```typescript
try {
  z.string().parse(42);
} catch (e) {
  if (e instanceof z.ZodError) {
    console.log(e.issues);
    // [{
    //   code: "invalid_type",
    //   expected: "string",
    //   message: "Invalid input: expected string, received number",
    //   path: [],
    // }]
  }
}
```

### Safe Parsing (No Exceptions)

```typescript
const result = z.string().safeParse(42);

if (!result.success) {
  console.log(result.error.issues);
  // Same ZodError, no try/catch needed
}
```

### Issue Properties

Each issue contains:
- `code` — issue type (`"invalid_type"`, `"too_small"`, `"custom"`, etc.)
- `message` — human-readable error message
- `path` — array describing the error location (e.g., `["address", "city"]`)
- Additional properties depending on the code (e.g., `expected`, `minimum`, `maximum`)

## Error Customization

### String Messages

Pass a string to any validator for a custom error message:

```typescript
z.string("Must be a string");
z.string().min(5, "Too short");
z.number().max(100, "Too large");
```

### Object Form

```typescript
z.string({ error: "Must be a string" });
z.string().min(5, { error: "Too short" });
```

### Function Form (Error Maps)

Use a function for dynamic error messages based on the issue:

```typescript
z.string({
  error: (issue) => {
    if (issue.input === undefined) return "Required";
    return "Must be a string";
  },
});
```

## Error Maps

Error maps are functions that receive issue context and return a message string (or `undefined` to defer):

```typescript
z.number().min(10, {
  error: (issue) => {
    if (issue.code === "too_small") {
      return `Value must be at least ${issue.minimum}`;
    }
  },
});
```

### Issue Context Properties

The `issue` object provides:
- `code` — the issue code
- `input` — the raw input value
- `inst` — the schema instance that generated the issue
- `path` — error location path
- Type-specific properties: `expected`, `minimum`, `maximum`, `inclusive`, etc.

### Per-Parse Error Maps

Override errors for a single parse call:

```typescript
schema.parse(data, {
  error: (issue) => "Custom per-parse error",
});
```

### Global Error Map

Configure errors for all validations:

```typescript
z.config({
  customError: (issue) => {
    if (issue.code === "invalid_type") {
      return `Expected ${issue.expected}, got ${typeof issue.input}`;
    }
    return undefined; // defer to default
  },
});
```

## Error Precedence

From highest to lowest priority:

1. **Schema-level** — `z.string({ error: "..." })`
2. **Per-parse** — `schema.parse(data, { error: fn })`
3. **Global config** — `z.config({ customError: fn })`
4. **Locale** — built-in locale messages

Return `undefined` from a higher-priority map to defer to the next level.

## Error Formatting

### `z.prettifyError()` — Human-Readable String

```typescript
const result = z.object({
  username: z.string(),
  age: z.number(),
}).safeParse({ username: 42, age: "old" });

if (!result.success) {
  console.log(z.prettifyError(result.error));
}
// Output:
// ✖ Invalid input: expected string, received number
//   → at username
// ✖ Invalid input: expected number, received string
//   → at age
```

### `z.treeifyError()` — Nested Object Structure

```typescript
const tree = z.treeifyError(result.error);

tree.properties?.username?.errors;
// ["Invalid input: expected string, received number"]

tree.properties?.age?.errors;
// ["Invalid input: expected number, received string"]
```

Use optional chaining (`?.`) when accessing nested properties.

### `z.flattenError()` — Flat Object (Best for Forms)

```typescript
const flat = z.flattenError(result.error);
// {
//   formErrors: [],                    // top-level errors
//   fieldErrors: {
//     username: ["Expected string"],
//     age: ["Expected number"],
//   }
// }
```

Ideal for mapping to form field error states.

### `z.formatError()` (Deprecated)

Use `z.treeifyError()` instead. `z.formatError()` uses `_errors` fields instead of `errors`.

## Internationalization

### Built-in Locales

Zod provides 35+ locales:

```typescript
import { en } from "zod/locales";
import { es } from "zod/locales";
import { fr } from "zod/locales";
import { ja } from "zod/locales";
import { ko } from "zod/locales";
import { zh } from "zod/locales";
// ar, de, pt, ru, and 25+ more
```

### Configuring a Locale

```typescript
import { es } from "zod/locales";

z.config(es());
// All default error messages are now in Spanish
```

### Zod Mini Requires Explicit Locale

```typescript
import { z } from "zod/mini";
import { en } from "zod/locales";

z.config(en());
```

### Reporting Input in Errors

By default, Zod excludes input data from error issues (security):

```typescript
// Include input in error issues
z.string().parse(42, { reportInput: true });
```

## Common Patterns

### Form Validation with Field Errors

```typescript
const FormSchema = z.object({
  email: z.email({ error: "Invalid email" }),
  password: z.string().min(8, { error: "At least 8 characters" }),
  age: z.number().int().positive({ error: "Must be a positive integer" }),
});

function validateForm(data: unknown) {
  const result = FormSchema.safeParse(data);
  if (!result.success) {
    return z.flattenError(result.error).fieldErrors;
    // { email?: string[], password?: string[], age?: string[] }
  }
  return null;
}
```

### API Error Response

```typescript
function handleValidationError(error: z.ZodError) {
  return {
    status: 400,
    body: {
      message: "Validation failed",
      errors: error.issues.map((issue) => ({
        field: issue.path.join("."),
        message: issue.message,
        code: issue.code,
      })),
    },
  };
}
```

### Contextual Error Messages

```typescript
const UserSchema = z.object({
  name: z.string({
    error: (iss) => iss.input === undefined
      ? "Name is required"
      : "Name must be a string",
  }).min(2, { error: "Name must be at least 2 characters" }),

  email: z.email({
    error: (iss) => iss.input === undefined
      ? "Email is required"
      : "Please enter a valid email address",
  }),
});
```
