# Refinements and Transforms

> Source: [zod.dev/api](https://zod.dev/api)

## Table of Contents

- [Refinements](#refinements)
- [SuperRefine](#superrefine)
- [Check](#check)
- [Transforms](#transforms)
- [Pipes](#pipes)
- [Preprocess](#preprocess)
- [Apply](#apply)
- [Common Patterns](#common-patterns)

---

## Refinements

`.refine()` adds custom validation logic to any schema. The function receives the parsed value and returns `true` (valid) or `false` (invalid).

```typescript
const PositiveEven = z.number().refine(
  (n) => n > 0 && n % 2 === 0,
  { error: "Must be a positive even number" }
);

PositiveEven.parse(4);  // OK
PositiveEven.parse(-2); // throws
PositiveEven.parse(3);  // throws
```

### Refinement Options

```typescript
z.string().refine(
  (val) => val.length > 8,
  {
    error: "Password too short",  // error message
    abort: true,                   // stop validation on failure
    path: ["password"],            // custom error path
  }
);
```

### Async Refinements

```typescript
const UniqueUsername = z.string().refine(
  async (username) => {
    const exists = await db.users.findUnique({ where: { username } });
    return !exists;
  },
  { error: "Username already taken" }
);

// Must use async parsing
await UniqueUsername.parseAsync("alice");
```

**Important**: Schemas with async refinements cannot use `.parse()` — you must use `.parseAsync()` or `.safeParseAsync()`.

### Abort Early

When `abort: true` is set, validation stops at this refinement if it fails:

```typescript
const schema = z.string()
  .refine((s) => s.length > 0, { error: "Required", abort: true })
  .refine((s) => s.includes("@"), { error: "Must contain @" });

// If empty string, only "Required" error is returned
```

## SuperRefine

`.superRefine()` provides full control over error generation, allowing multiple issues with custom codes:

```typescript
const Password = z.string().superRefine((val, ctx) => {
  if (val.length < 8) {
    ctx.addIssue({
      code: "custom",
      message: "Password must be at least 8 characters",
    });
  }
  if (!/[A-Z]/.test(val)) {
    ctx.addIssue({
      code: "custom",
      message: "Password must contain an uppercase letter",
    });
  }
  if (!/[0-9]/.test(val)) {
    ctx.addIssue({
      code: "custom",
      message: "Password must contain a number",
    });
  }
});
```

### Aborting in SuperRefine

Return `z.NEVER` to stop validation and prevent downstream refinements:

```typescript
z.string().superRefine((val, ctx) => {
  if (!val) {
    ctx.addIssue({ code: "custom", message: "Required" });
    return z.NEVER; // stop here
  }
});
```

## Check

`.check()` is a lower-level refinement API. Useful for reusable validators and performance-critical code:

```typescript
const isPositive = z.check<number>((val) => {
  if (val <= 0) return { error: "Must be positive" };
});

const PositiveNumber = z.number().check(isPositive);
```

With string formats in Zod Mini:

```typescript
import { z } from "zod/mini";

const Email = z.string().check(z.email);
```

## Transforms

`.transform()` modifies the value during parsing. Input and output types can differ:

```typescript
const ToLength = z.string().transform((val) => val.length);

type In = z.input<typeof ToLength>;   // string
type Out = z.output<typeof ToLength>; // number

ToLength.parse("hello"); // 5
```

### Chaining Transforms

```typescript
const ProcessedEmail = z.string()
  .trim()
  .toLowerCase()
  .transform((email) => ({
    full: email,
    domain: email.split("@")[1],
    local: email.split("@")[0],
  }));

ProcessedEmail.parse("  USER@Example.COM  ");
// { full: "user@example.com", domain: "example.com", local: "user" }
```

### Transform with Validation

```typescript
const SafeInt = z.string().transform((val, ctx) => {
  const parsed = parseInt(val, 10);
  if (isNaN(parsed)) {
    ctx.addIssue({
      code: "custom",
      message: "Not a valid integer",
    });
    return z.NEVER;
  }
  return parsed;
});

SafeInt.parse("42");    // 42
SafeInt.parse("hello"); // throws "Not a valid integer"
```

## Pipes

`.pipe()` chains a schema after a transform, creating a pipeline:

```typescript
// Parse string → coerce to number → validate as positive integer
const PortNumber = z.coerce.number().pipe(z.int().positive().lte(65535));

PortNumber.parse("8080"); // 8080
PortNumber.parse("abc");  // throws (coerce fails)
PortNumber.parse("-1");   // throws (not positive)
```

### Multi-Step Pipeline

```typescript
const JsonString = z.string()
  .transform((str) => JSON.parse(str))
  .pipe(z.object({
    name: z.string(),
    value: z.number(),
  }));

JsonString.parse('{"name":"test","value":42}');
// { name: "test", value: 42 }
```

## Preprocess

`.preprocess()` transforms data **before** validation:

```typescript
const NumericString = z.preprocess(
  (val) => (typeof val === "string" ? parseInt(val, 10) : val),
  z.number().int()
);

NumericString.parse("42"); // 42
NumericString.parse(42);   // 42
```

**Note**: In v4, `z.preprocess()` returns a `ZodPipe` internally.

## Apply

`.apply()` integrates external transformation functions into a schema chain:

```typescript
function doubleIfPositive(n: number): number {
  return n > 0 ? n * 2 : n;
}

const schema = z.number().apply(doubleIfPositive);

schema.parse(5);  // 10
schema.parse(-3); // -3
```

## Common Patterns

### Cross-Field Validation

```typescript
const PasswordForm = z.object({
  password: z.string().min(8),
  confirmPassword: z.string(),
}).refine(
  (data) => data.password === data.confirmPassword,
  {
    error: "Passwords don't match",
    path: ["confirmPassword"],
  }
);
```

### Date Range Validation

```typescript
const DateRange = z.object({
  startDate: z.iso.date(),
  endDate: z.iso.date(),
}).refine(
  (data) => new Date(data.startDate) < new Date(data.endDate),
  {
    error: "End date must be after start date",
    path: ["endDate"],
  }
);
```

### Conditional Validation

```typescript
const Notification = z.object({
  type: z.enum(["email", "sms", "push"]),
  destination: z.string(),
}).refine(
  (data) => {
    if (data.type === "email") return data.destination.includes("@");
    if (data.type === "sms") return /^\+\d{10,}$/.test(data.destination);
    return true;
  },
  { error: "Invalid destination for notification type" }
);
```

### Slug Generator Transform

```typescript
const Slugify = z.string().transform((val) =>
  val
    .toLowerCase()
    .replace(/[^\w\s-]/g, "")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .trim()
);

Slugify.parse("Hello World! 🌍"); // "hello-world-"
```
