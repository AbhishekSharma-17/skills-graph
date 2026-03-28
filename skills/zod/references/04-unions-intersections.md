# Unions and Intersections

> Source: [zod.dev/api](https://zod.dev/api)

## Table of Contents

- [Union](#union)
- [Discriminated Union](#discriminated-union)
- [XOR (Exclusive Union)](#xor-exclusive-union)
- [Intersection](#intersection)
- [Common Patterns](#common-patterns)

---

## Union

`z.union()` accepts a value if it matches **any** of the provided schemas. Schemas are tested in order; the first match wins.

```typescript
const StringOrNumber = z.union([z.string(), z.number()]);
type StringOrNumber = z.infer<typeof StringOrNumber>; // string | number

StringOrNumber.parse("hello"); // OK
StringOrNumber.parse(42);      // OK
StringOrNumber.parse(true);    // throws
```

### Accessing Options

```typescript
StringOrNumber.options;
// [ZodString, ZodNumber]
```

### Error Behavior

When no schema matches, Zod returns the error from the schema that parsed the "closest" (fewest issues). If all schemas fail equally, all errors are included.

## Discriminated Union

`z.discriminatedUnion()` optimizes unions where all members share a common literal field (the "discriminator"). Instead of testing every schema, Zod looks up the correct branch using the discriminator value.

```typescript
const Shape = z.discriminatedUnion("type", [
  z.object({
    type: z.literal("circle"),
    radius: z.number(),
  }),
  z.object({
    type: z.literal("rectangle"),
    width: z.number(),
    height: z.number(),
  }),
  z.object({
    type: z.literal("triangle"),
    base: z.number(),
    height: z.number(),
  }),
]);

type Shape = z.infer<typeof Shape>;
// | { type: "circle"; radius: number }
// | { type: "rectangle"; width: number; height: number }
// | { type: "triangle"; base: number; height: number }
```

### Benefits

- **Performance**: O(1) lookup instead of O(n) sequential testing
- **Better errors**: Shows only the relevant branch's errors
- **Type narrowing**: TypeScript can narrow the type based on discriminator

### Usage with Switch

```typescript
function area(shape: Shape): number {
  switch (shape.type) {
    case "circle":
      return Math.PI * shape.radius ** 2;
    case "rectangle":
      return shape.width * shape.height;
    case "triangle":
      return (shape.base * shape.height) / 2;
  }
}
```

## XOR (Exclusive Union)

`z.xor()` requires **exactly one** schema to match. If zero or more than one matches, validation fails.

```typescript
const ExactlyOne = z.xor([
  z.object({ email: z.email() }),
  z.object({ phone: z.string() }),
]);

ExactlyOne.parse({ email: "a@b.com" });               // OK
ExactlyOne.parse({ phone: "123" });                    // OK
ExactlyOne.parse({ email: "a@b.com", phone: "123" }); // throws — both match
ExactlyOne.parse({});                                   // throws — none match
```

Use XOR when you need mutually exclusive options.

## Intersection

`z.intersection()` combines two schemas. The input must satisfy **both** schemas simultaneously.

```typescript
const HasName = z.object({ name: z.string() });
const HasAge = z.object({ age: z.number() });

const Person = z.intersection(HasName, HasAge);
type Person = z.infer<typeof Person>;
// { name: string; age: number }

Person.parse({ name: "Alice", age: 30 }); // OK
Person.parse({ name: "Alice" });           // throws — missing age
```

### Intersection vs Extend

For object schemas, `.extend()` is usually preferred over `z.intersection()`:

```typescript
// Preferred — single object schema
const Person = HasName.extend({ age: z.number() });

// Works but creates intersection type
const Person = z.intersection(HasName, HasAge);
```

**When to use intersection**: Combining non-object schemas or schemas from different sources where `.extend()` isn't available.

### Intersection Errors

In v4, `z.intersection()` throws a regular `Error` (not `ZodError`) when the two schemas produce unmergeable results (e.g., different primitives).

## Common Patterns

### API Response with Error Handling

```typescript
const ApiResult = z.discriminatedUnion("status", [
  z.object({
    status: z.literal("success"),
    data: z.unknown(),
  }),
  z.object({
    status: z.literal("error"),
    code: z.number(),
    message: z.string(),
  }),
]);
```

### Event System

```typescript
const AppEvent = z.discriminatedUnion("event", [
  z.object({
    event: z.literal("user.created"),
    userId: z.string(),
    email: z.email(),
  }),
  z.object({
    event: z.literal("user.deleted"),
    userId: z.string(),
    reason: z.string().optional(),
  }),
  z.object({
    event: z.literal("order.placed"),
    orderId: z.string(),
    total: z.number(),
  }),
]);

type AppEvent = z.infer<typeof AppEvent>;
```

### Conditional Fields with XOR

```typescript
const PaymentMethod = z.xor([
  z.object({
    type: z.literal("card"),
    cardNumber: z.string(),
    expiry: z.string(),
  }),
  z.object({
    type: z.literal("bank"),
    accountNumber: z.string(),
    routingNumber: z.string(),
  }),
  z.object({
    type: z.literal("wallet"),
    walletId: z.string(),
  }),
]);
```

### Mixins with Intersection

```typescript
const Timestamped = z.object({
  createdAt: z.date(),
  updatedAt: z.date(),
});

const SoftDeletable = z.object({
  deletedAt: z.date().nullable(),
});

const BaseModel = z.intersection(Timestamped, SoftDeletable);

const User = BaseModel.and(z.object({
  name: z.string(),
  email: z.email(),
}));
```
