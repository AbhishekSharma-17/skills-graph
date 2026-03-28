# Type Inference

> Source: [zod.dev/api](https://zod.dev/api)

## Table of Contents

- [Basic Inference](#basic-inference)
- [Input vs Output Types](#input-vs-output-types)
- [Branded Types](#branded-types)
- [Recursive Types](#recursive-types)
- [Generic Schema Functions](#generic-schema-functions)
- [Type Utilities](#type-utilities)

---

## Basic Inference

`z.infer<>` extracts the TypeScript type from any Zod schema:

```typescript
import { z } from "zod";

const UserSchema = z.object({
  id: z.string(),
  name: z.string(),
  email: z.email(),
  age: z.number().int().optional(),
  role: z.enum(["admin", "user", "guest"]),
});

type User = z.infer<typeof UserSchema>;
// {
//   id: string;
//   name: string;
//   email: string;
//   age?: number | undefined;
//   role: "admin" | "user" | "guest";
// }
```

Use the inferred type everywhere instead of manually defining interfaces:

```typescript
function createUser(data: User): User {
  return UserSchema.parse(data);
}
```

## Input vs Output Types

When schemas include transforms, defaults, or coercion, input and output types differ.

### `z.input<>` — What Goes In

```typescript
const FormData = z.object({
  name: z.string().trim(),
  age: z.coerce.number(),
  role: z.enum(["admin", "user"]).default("user"),
});

type FormInput = z.input<typeof FormData>;
// {
//   name: string;
//   age: unknown;       // coerce accepts unknown
//   role?: "admin" | "user" | undefined;  // default makes it optional
// }
```

### `z.output<>` — What Comes Out

```typescript
type FormOutput = z.output<typeof FormData>;
// {
//   name: string;       // trimmed
//   age: number;        // coerced to number
//   role: "admin" | "user";  // default applied
// }
```

`z.infer<>` is an alias for `z.output<>`.

### Transform Example

```typescript
const ToLength = z.string().transform((val) => val.length);

type In = z.input<typeof ToLength>;   // string
type Out = z.output<typeof ToLength>; // number

ToLength.parse("hello"); // 5
```

## Branded Types

Branded types add nominal typing to prevent accidental type mixing. Two branded types with the same underlying type are **not** assignable to each other.

```typescript
const UserId = z.string().brand<"UserId">();
const PostId = z.string().brand<"PostId">();

type UserId = z.infer<typeof UserId>;
type PostId = z.infer<typeof PostId>;

const userId: UserId = UserId.parse("user-123");
const postId: PostId = PostId.parse("post-456");

// Type error — branded types are incompatible
// const wrong: UserId = postId;
```

### Practical Use

```typescript
const Currency = z.number().positive().brand<"Currency">();
type Currency = z.infer<typeof Currency>;

function addPrices(a: Currency, b: Currency): Currency {
  return Currency.parse(a + b);
}

const price = Currency.parse(9.99);
const tax = Currency.parse(0.89);
addPrices(price, tax); // OK

// addPrices(9.99, 0.89); // Type error — raw numbers not accepted
```

### Brand with Validation

```typescript
const Email = z.email().brand<"Email">();
type Email = z.infer<typeof Email>;

// Email type can only be created through validation
const email: Email = Email.parse("user@example.com");
```

## Recursive Types

Zod v4 natively supports recursive schemas:

```typescript
type Category = {
  name: string;
  children: Category[];
};

const Category: z.ZodType<Category> = z.object({
  name: z.string(),
  children: z.lazy(() => z.array(Category)),
});
```

### `z.lazy()` for Deferred Schemas

```typescript
const TreeNode: z.ZodType<TreeNode> = z.object({
  value: z.number(),
  left: z.lazy(() => TreeNode).nullable(),
  right: z.lazy(() => TreeNode).nullable(),
});

type TreeNode = {
  value: number;
  left: TreeNode | null;
  right: TreeNode | null;
};
```

### JSON Type Example

```typescript
type Json = string | number | boolean | null | Json[] | { [key: string]: Json };

const JsonSchema: z.ZodType<Json> = z.lazy(() =>
  z.union([
    z.string(),
    z.number(),
    z.boolean(),
    z.null(),
    z.array(JsonSchema),
    z.record(z.string(), JsonSchema),
  ])
);
```

## Generic Schema Functions

Write reusable functions that accept and return Zod schemas:

### Accept Any Schema

```typescript
function validate<T extends z.ZodType>(
  schema: T,
  data: unknown
): z.infer<T> {
  return schema.parse(data);
}

const user = validate(UserSchema, rawData);
// user is fully typed as User
```

### Create Schema Wrappers

```typescript
function nullable<T extends z.ZodType>(schema: T) {
  return schema.nullable();
}

function withId<T extends z.AnyZodObject>(schema: T) {
  return schema.extend({
    id: z.string(),
    createdAt: z.date(),
    updatedAt: z.date(),
  });
}

const UserWithId = withId(UserSchema);
```

### API Response Wrapper

```typescript
function apiResponse<T extends z.ZodType>(dataSchema: T) {
  return z.object({
    data: dataSchema,
    meta: z.object({
      requestId: z.string(),
      timestamp: z.number(),
    }),
  });
}

const UserResponse = apiResponse(UserSchema);
type UserResponse = z.infer<typeof UserResponse>;
```

## Type Utilities

### Extracting Schema Shape

```typescript
const User = z.object({ name: z.string(), age: z.number() });

// Get the shape type
type UserShape = typeof User.shape;
// { name: ZodString; age: ZodNumber }
```

### Checking Schema Type at Runtime

```typescript
import { z } from "zod";

function isObjectSchema(schema: z.ZodType): schema is z.AnyZodObject {
  return "_zod" in schema && schema._zod.def.type === "object";
}
```

### Type-Safe Defaults

```typescript
// In v4, .default() accepts the output type
const WithDefault = z.string()
  .transform((s) => s.length)
  .default(0); // 0 is number (output type)

type Out = z.output<typeof WithDefault>; // number

// Use .prefault() for input-type defaults
const WithPrefault = z.string()
  .transform((s) => s.length)
  .prefault("hello"); // "hello" is string (input type)
```
