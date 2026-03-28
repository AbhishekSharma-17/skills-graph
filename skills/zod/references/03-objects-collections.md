# Objects and Collections

> Source: [zod.dev/api](https://zod.dev/api)

## Table of Contents

- [Objects](#objects)
- [Object Variants](#object-variants)
- [Object Methods](#object-methods)
- [Arrays](#arrays)
- [Tuples](#tuples)
- [Records](#records)
- [Maps and Sets](#maps-and-sets)
- [Common Patterns](#common-patterns)

---

## Objects

`z.object()` defines an object schema with required properties. Unknown keys are **stripped** by default.

```typescript
const User = z.object({
  name: z.string(),
  email: z.email(),
  age: z.number().int().positive(),
});

type User = z.infer<typeof User>;
// { name: string; email: string; age: number }

User.parse({
  name: "Alice",
  email: "alice@example.com",
  age: 30,
  extraField: "stripped",
}); // extraField is removed from output
```

### Optional and Nullable Fields

```typescript
const Profile = z.object({
  name: z.string(),
  bio: z.string().optional(),       // string | undefined
  avatar: z.string().nullable(),    // string | null
  nickname: z.string().nullish(),   // string | null | undefined
});
```

### Default Values

```typescript
const Config = z.object({
  host: z.string().default("localhost"),
  port: z.number().default(3000),
  debug: z.boolean().default(false),
});

Config.parse({}); // { host: "localhost", port: 3000, debug: false }
```

## Object Variants

### `z.strictObject()` — Reject Unknown Keys

```typescript
const Strict = z.strictObject({
  name: z.string(),
  age: z.number(),
});

Strict.parse({ name: "Alice", age: 30, extra: true });
// throws: "Unrecognized key: extra"
```

### `z.looseObject()` — Preserve Unknown Keys

```typescript
const Loose = z.looseObject({
  name: z.string(),
  age: z.number(),
});

Loose.parse({ name: "Alice", age: 30, extra: true });
// { name: "Alice", age: 30, extra: true }
```

### `.catchall()` — Validate Unknown Keys

```typescript
const WithCatchall = z.object({
  name: z.string(),
}).catchall(z.number());

WithCatchall.parse({ name: "Alice", score: 100, rank: 5 });
// OK — extra keys must be numbers
```

## Object Methods

### `.shape` — Access Field Schemas

```typescript
const User = z.object({ name: z.string(), age: z.number() });
User.shape.name;  // z.ZodString
User.shape.age;   // z.ZodNumber
```

### `.keyof()` — Enum from Keys

```typescript
const UserKeys = User.keyof();
type UserKeys = z.infer<typeof UserKeys>; // "name" | "age"
```

### `.extend()` — Add or Override Properties

```typescript
const Employee = User.extend({
  company: z.string(),
  age: z.number().int(), // overrides age field
});
```

### `.safeExtend()` — Add Only (Error on Override)

```typescript
const WithEmail = User.safeExtend({
  email: z.email(), // OK — new field
  // name: z.string(), // would error — already exists
});
```

### `.pick()` and `.omit()` — Select/Exclude Fields

```typescript
const NameOnly = User.pick({ name: true });
// { name: string }

const NoAge = User.omit({ age: true });
// { name: string }
```

### `.partial()` — Make All Fields Optional

```typescript
const PartialUser = User.partial();
// { name?: string; age?: number }

// Partial specific fields
const PartialAge = User.partial({ age: true });
// { name: string; age?: number }
```

### `.required()` — Make All Fields Required

```typescript
const RequiredUser = PartialUser.required();
// Reverses .partial()
```

### `.readonly()` — Freeze Output

```typescript
const ImmutableUser = User.readonly();
type ImmutableUser = z.infer<typeof ImmutableUser>;
// { readonly name: string; readonly age: number }
```

## Arrays

```typescript
const StringArray = z.array(z.string());
// or
const StringArray = z.string().array();

type StringArray = z.infer<typeof StringArray>; // string[]
```

### Array Constraints

```typescript
z.array(z.string()).min(1);         // at least 1 element
z.array(z.string()).max(10);        // at most 10 elements
z.array(z.string()).length(5);      // exactly 5 elements
z.array(z.string()).nonempty();     // .min(1) alias
```

**Note**: In v4, `.nonempty()` behaves like `.min(1)` and returns `string[]` (not `[string, ...string[]]` as in v3).

### Nested Arrays

```typescript
const Matrix = z.array(z.array(z.number()));
type Matrix = z.infer<typeof Matrix>; // number[][]
```

## Tuples

Fixed-length arrays with different types per position:

```typescript
const Point = z.tuple([z.number(), z.number()]);
type Point = z.infer<typeof Point>; // [number, number]

const NameAge = z.tuple([z.string(), z.number()]);
type NameAge = z.infer<typeof NameAge>; // [string, number]
```

### Variadic Tuples (Rest Elements)

```typescript
// [string, ...number[]]
const Args = z.tuple([z.string()], z.number());

Args.parse(["hello", 1, 2, 3]); // OK
Args.parse(["hello"]);           // OK (rest is optional)
```

## Records

Key-value objects with validated keys and values:

```typescript
// string keys, number values
const Scores = z.record(z.string(), z.number());
type Scores = z.infer<typeof Scores>; // Record<string, number>

Scores.parse({ alice: 100, bob: 85 }); // OK
```

### Enum Keys

```typescript
const Role = z.enum(["admin", "user", "guest"]);
const Permissions = z.record(Role, z.boolean());
// Record<"admin" | "user" | "guest", boolean>
```

### `z.partialRecord()` — Optional Values

```typescript
const Config = z.partialRecord(z.string(), z.number());
// Partial<Record<string, number>> — values can be undefined
```

### `z.looseRecord()` — Passthrough Unknown Keys

```typescript
const Loose = z.looseRecord(z.string(), z.number());
// Unmatched keys pass through without validation
```

## Maps and Sets

### Maps

```typescript
const UserMap = z.map(z.string(), z.object({
  name: z.string(),
  age: z.number(),
}));

type UserMap = z.infer<typeof UserMap>;
// Map<string, { name: string; age: number }>
```

### Sets

```typescript
const Tags = z.set(z.string());
type Tags = z.infer<typeof Tags>; // Set<string>

// Constraints
z.set(z.string()).min(1);      // at least 1 element
z.set(z.string()).max(10);     // at most 10 elements
z.set(z.string()).size(5);     // exactly 5 elements
```

## Common Patterns

### Nested Objects

```typescript
const Address = z.object({
  street: z.string(),
  city: z.string(),
  zip: z.string().regex(/^\d{5}$/),
});

const User = z.object({
  name: z.string(),
  address: Address,
  tags: z.array(z.string()),
});
```

### Optional Fields with Defaults

```typescript
const Pagination = z.object({
  page: z.number().int().positive().default(1),
  limit: z.number().int().positive().max(100).default(20),
  sort: z.enum(["asc", "desc"]).default("asc"),
});

Pagination.parse({}); // { page: 1, limit: 20, sort: "asc" }
```

### Update Schema from Create Schema

```typescript
const CreateUser = z.object({
  name: z.string(),
  email: z.email(),
  role: z.enum(["admin", "user"]),
});

const UpdateUser = CreateUser.partial();
// All fields optional for PATCH operations
```

### API Response Wrapper

```typescript
const ApiResponse = <T extends z.ZodType>(dataSchema: T) =>
  z.object({
    success: z.boolean(),
    data: dataSchema,
    error: z.string().optional(),
  });

const UserResponse = ApiResponse(User);
```
