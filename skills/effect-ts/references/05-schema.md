# Schema

> Source: [effect.website/docs](https://effect.website/docs/schema/introduction/) | Package: `effect` v3.21.x

## Table of Contents

- [What Is Schema](#what-is-schema)
- [Basic Schemas](#basic-schemas)
- [Decoding and Encoding](#decoding-and-encoding)
- [Object Schemas (Struct)](#object-schemas-struct)
- [Branded Types](#branded-types)
- [Schema.Class — Domain Classes](#schemaclass--domain-classes)
- [Transformations](#transformations)
- [Union and Discriminated Unions](#union-and-discriminated-unions)
- [Arrays, Records, and Collections](#arrays-records-and-collections)
- [Optional and Default Values](#optional-and-default-values)
- [Schema vs Zod](#schema-vs-zod)
- [Common Pitfalls](#common-pitfalls)

## What Is Schema

Effect Schema is a bidirectional validation library built into the `effect` package. Unlike Zod which only decodes, Schema handles both decode (unknown → typed) and encode (typed → external format), making it ideal for APIs, databases, and serialization.

```typescript
import { Schema } from "effect"

const User = Schema.Struct({
  id: Schema.Number,
  name: Schema.String,
  email: Schema.String,
  createdAt: Schema.DateFromString // decodes string → Date, encodes Date → string
})

type User = typeof User.Type       // { id: number; name: string; email: string; createdAt: Date }
type UserEncoded = typeof User.Encoded // { id: number; name: string; email: string; createdAt: string }
```

## Basic Schemas

```typescript
import { Schema } from "effect"

// Primitives
Schema.String       // string
Schema.Number       // number
Schema.Boolean      // boolean
Schema.BigInt       // bigint
Schema.Date         // Date (validates it's a valid Date)
Schema.Void         // void
Schema.Unknown      // unknown
Schema.Undefined    // undefined
Schema.Null         // null
Schema.Never        // never

// Literals
Schema.Literal("active")               // "active"
Schema.Literal("admin", "user", "guest") // "admin" | "user" | "guest"

// Template literals
Schema.TemplateLiteral(Schema.String, "-", Schema.Number) // `${string}-${number}`

// Enums
enum Status { Active = "active", Inactive = "inactive" }
Schema.Enums(Status)
```

## Decoding and Encoding

```typescript
import { Schema } from "effect"

const User = Schema.Struct({
  id: Schema.Number,
  name: Schema.String,
  createdAt: Schema.DateFromString
})

// Synchronous decode (throws on failure)
const user = Schema.decodeUnknownSync(User)({
  id: 1,
  name: "Alice",
  createdAt: "2026-01-15T00:00:00Z"
})
// { id: 1, name: "Alice", createdAt: Date }

// Effect-based decode (returns Effect with typed error)
const decoded = Schema.decodeUnknown(User)(rawInput)
// Effect<User, ParseError, never>

// Encode back to external format
const encoded = Schema.encodeSync(User)(user)
// { id: 1, name: "Alice", createdAt: "2026-01-15T00:00:00.000Z" }

// Validate without transforming (asserts input matches)
const isValid = Schema.is(User)(input) // boolean
```

### Decode Modes

```typescript
// decodeUnknown — accepts unknown input, validates everything
Schema.decodeUnknown(schema)(input)

// decode — accepts the Encoded type, only runs transforms
Schema.decode(schema)(encodedInput)

// validate — checks the Type shape, no transforms
Schema.validate(schema)(typedInput)
```

## Object Schemas (Struct)

```typescript
const Product = Schema.Struct({
  id: Schema.String,
  name: Schema.NonEmptyString,
  price: Schema.Positive,        // number > 0
  tags: Schema.Array(Schema.String),
  metadata: Schema.optional(Schema.Record({
    key: Schema.String,
    value: Schema.Unknown
  }))
})
```

### Extending Structs

```typescript
const BaseEntity = Schema.Struct({
  id: Schema.String,
  createdAt: Schema.DateFromString,
  updatedAt: Schema.DateFromString
})

const User = Schema.extend(BaseEntity, Schema.Struct({
  name: Schema.String,
  email: Schema.String
}))
```

### Pick and Omit

```typescript
const UserCreate = User.pipe(Schema.omit("id", "createdAt", "updatedAt"))
const UserPublic = User.pipe(Schema.pick("id", "name"))
```

## Branded Types

Branded types prevent mixing up values with the same underlying type:

```typescript
const UserId = Schema.String.pipe(Schema.brand("UserId"))
type UserId = typeof UserId.Type // string & Brand<"UserId">

const OrderId = Schema.String.pipe(Schema.brand("OrderId"))
type OrderId = typeof OrderId.Type // string & Brand<"OrderId">

// These are different types — compiler prevents mixing them
const fetchUser = (id: UserId) => ...
const fetchOrder = (id: OrderId) => ...

// fetchUser(orderId) // Type error!
```

### Branded Types with Validation

```typescript
const Email = Schema.String.pipe(
  Schema.pattern(/^[^@]+@[^@]+\.[^@]+$/),
  Schema.brand("Email")
)
type Email = typeof Email.Type // string & Brand<"Email">

const PositiveInt = Schema.Number.pipe(
  Schema.int(),
  Schema.positive(),
  Schema.brand("PositiveInt")
)
```

## Schema.Class — Domain Classes

Create classes with built-in validation, equality, and serialization:

```typescript
class User extends Schema.Class<User>("User")({
  id: Schema.Number,
  name: Schema.NonEmptyString,
  email: Schema.String.pipe(Schema.pattern(/^[^@]+@[^@]+\.[^@]+$/)),
  role: Schema.Literal("admin", "user", "viewer"),
  createdAt: Schema.DateFromString
}) {
  get displayName() {
    return `${this.name} (${this.role})`
  }
}

// Decoding creates a class instance
const user = Schema.decodeUnknownSync(User)({
  id: 1, name: "Alice", email: "alice@example.com",
  role: "admin", createdAt: "2026-01-15T00:00:00Z"
})
user.displayName // "Alice (admin)"
user instanceof User // true

// Encoding returns a plain object
Schema.encodeSync(User)(user)
// { id: 1, name: "Alice", email: "alice@example.com", role: "admin", createdAt: "2026-01..." }
```

### Schema.TaggedClass — For Error Types

```typescript
class NotFoundError extends Schema.TaggedError<NotFoundError>()(
  "NotFoundError",
  { entity: Schema.String, id: Schema.String }
) {}
```

## Transformations

Transform data between external and internal representations:

```typescript
// Built-in transforms
Schema.DateFromString    // string ↔ Date
Schema.NumberFromString  // string ↔ number
Schema.BigIntFromString  // string ↔ bigint
Schema.BooleanFromString // "true"/"false" ↔ boolean
Schema.Split(", ")       // string ↔ string[] (split by separator)

// Custom transform
const Celsius = Schema.transform(
  Schema.Number, // from (external)
  Schema.Number, // to (internal)
  {
    decode: (fahrenheit) => (fahrenheit - 32) * 5 / 9,
    encode: (celsius) => celsius * 9 / 5 + 32
  }
)
```

### Effectful Transforms

```typescript
const UserWithProfile = Schema.transformOrFail(
  Schema.Struct({ userId: Schema.Number }),
  Schema.Struct({ userId: Schema.Number, profile: ProfileSchema }),
  {
    decode: (input) =>
      Effect.gen(function* () {
        const profile = yield* fetchProfile(input.userId)
        return { ...input, profile }
      }),
    encode: ({ profile, ...rest }) => Effect.succeed(rest)
  }
)
```

## Union and Discriminated Unions

```typescript
// Simple union
const StringOrNumber = Schema.Union(Schema.String, Schema.Number)

// Discriminated union (recommended — more efficient)
const Shape = Schema.Union(
  Schema.Struct({ _tag: Schema.Literal("Circle"), radius: Schema.Number }),
  Schema.Struct({ _tag: Schema.Literal("Rectangle"), width: Schema.Number, height: Schema.Number }),
  Schema.Struct({ _tag: Schema.Literal("Triangle"), base: Schema.Number, height: Schema.Number })
)
type Shape = typeof Shape.Type
```

## Arrays, Records, and Collections

```typescript
// Arrays
Schema.Array(Schema.String)                     // string[]
Schema.NonEmptyArray(Schema.Number)             // [number, ...number[]]
Schema.Array(Schema.String).pipe(Schema.maxItems(10)) // max 10 items

// Tuples
Schema.Tuple(Schema.String, Schema.Number)      // [string, number]

// Records
Schema.Record({ key: Schema.String, value: Schema.Number }) // Record<string, number>

// Maps
Schema.Map({ key: Schema.String, value: Schema.Number })

// Sets
Schema.Set(Schema.String)

// ReadonlyArray
Schema.Array(Schema.String).pipe(Schema.mutable) // string[] (mutable)
```

## Optional and Default Values

```typescript
const Config = Schema.Struct({
  host: Schema.String,
  port: Schema.optional(Schema.Number, { default: () => 3000 }),
  debug: Schema.optional(Schema.Boolean, { default: () => false }),
  tags: Schema.optional(Schema.Array(Schema.String)),
  description: Schema.NullOr(Schema.String) // string | null
})

// With exact optional property types
const Strict = Schema.Struct({
  name: Schema.String,
  age: Schema.optional(Schema.Number, { exact: true })
  // age?: number (not number | undefined)
})
```

## Schema vs Zod

| Feature | Schema | Zod |
|---------|--------|-----|
| Decode (unknown → typed) | Yes | Yes |
| Encode (typed → external) | Yes | No |
| Branded types | Built-in | Via .brand() |
| Classes | Schema.Class | No |
| Effectful transforms | Yes (Effect integration) | No |
| Bidirectional | Yes | One-way |
| Arbitrary (test data gen) | Yes (Schema.Arbitrary) | No |
| Pretty printing | Yes (Schema.Pretty) | No |
| JSON Schema generation | Yes | Via zod-to-json-schema |
| Bundle size (standalone) | Larger (part of Effect) | Smaller |

## Common Pitfalls

- **Don't confuse Type and Encoded**: `User.Type` is the decoded type (with Date objects). `User.Encoded` is the wire format (with date strings). Use the right one for your context.
- **Schema is strict by default**: Extra properties on input objects cause validation errors. Use `Schema.Struct({...}).pipe(Schema.extend(Schema.Record(...)))` if you need passthrough.
- **Branded types are compile-time only**: At runtime, a `UserId` is just a string. The brand prevents mixing at the type level.
- **Transforms are bidirectional**: If you define a `decode`, you must also define `encode` (or use `transformOrFail` with an effectful encode).

## Related Topics

- Error handling with Schema → `02-error-handling.md`
- Schema in HTTP APIs → `12-platform.md`
- Testing with schemas → `11-testing.md`
