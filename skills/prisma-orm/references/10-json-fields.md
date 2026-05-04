# Prisma JSON Fields

> Source: [prisma.io/docs/orm/prisma-client/special-fields-and-types/working-with-json-fields](https://www.prisma.io/docs/orm/prisma-client/special-fields-and-types/working-with-json-fields) — Prisma ORM v7.x

## Table of Contents

- [Defining JSON Fields](#defining-json-fields)
- [Reading JSON](#reading-json)
- [Writing JSON](#writing-json)
- [Simple Filtering](#simple-filtering)
- [Advanced Filtering (Path-Based)](#advanced-filtering-path-based)
- [Array Filters](#array-filters)
- [Handling Null Values](#handling-null-values)
- [Type Safety with JSON](#type-safety-with-json)
- [Common Patterns](#common-patterns)
- [Limitations](#limitations)

---

## Defining JSON Fields

```prisma
model User {
  id       Int    @id @default(autoincrement())
  settings Json   @default("{}")
  metadata Json?
  tags     Json   @default("[]")
}

model Product {
  id         Int  @id @default(autoincrement())
  attributes Json @default("{}")
  variants   Json @default("[]")
}
```

The `Json` type maps to:
- PostgreSQL: `jsonb` (default) or `json` via `@db.Json`
- MySQL: `json`
- MongoDB: native BSON object
- SQLite: not supported

## Reading JSON

JSON fields return JavaScript objects/arrays:

```typescript
const user = await prisma.user.findUnique({
  where: { id: 1 },
});

// user.settings is a JavaScript object
console.log(user.settings);
// { theme: "dark", notifications: true, language: "en" }

// Access nested properties
const theme = (user.settings as any).theme;
```

### Working with Prisma JSON Types

```typescript
import { Prisma } from "./generated/prisma/index.js";

const user = await prisma.user.findUnique({ where: { id: 1 } });

// Cast to specific types
const settings = user.settings as Prisma.JsonObject;
const tags = user.tags as Prisma.JsonArray;

// Type hierarchy:
// JsonValue = string | number | boolean | null | JsonObject | JsonArray
// JsonObject = { [key: string]: JsonValue }
// JsonArray = JsonValue[]
```

## Writing JSON

Pass JavaScript objects/arrays directly:

```typescript
// Create with JSON
const user = await prisma.user.create({
  data: {
    email: "alice@example.com",
    settings: {
      theme: "dark",
      notifications: { email: true, push: false },
      language: "en",
    },
    tags: ["developer", "typescript"],
  },
});

// Update JSON (replaces entire field)
await prisma.user.update({
  where: { id: 1 },
  data: {
    settings: {
      theme: "light",
      notifications: { email: false, push: true },
      language: "fr",
    },
  },
});
```

**Important**: Updates replace the entire JSON value. There's no built-in JSON patch — read, modify, write back:

```typescript
// Read-modify-write pattern
const user = await prisma.user.findUnique({ where: { id: 1 } });
const settings = user.settings as Record<string, unknown>;

await prisma.user.update({
  where: { id: 1 },
  data: {
    settings: { ...settings, theme: "light" },
  },
});
```

## Simple Filtering

### Exact Match

```typescript
// Match entire JSON value
const users = await prisma.user.findMany({
  where: {
    settings: {
      equals: { theme: "dark", language: "en" },
    },
  },
});

// Shorthand
const users = await prisma.user.findMany({
  where: {
    settings: { theme: "dark", language: "en" },
  },
});
```

### Not Equal

```typescript
const users = await prisma.user.findMany({
  where: {
    settings: {
      not: { theme: "dark" },
    },
  },
});
```

## Advanced Filtering (Path-Based)

Filter by nested JSON properties using `path`:

### PostgreSQL Syntax

```typescript
// Filter on object property
const users = await prisma.user.findMany({
  where: {
    settings: {
      path: ["theme"],
      equals: "dark",
    },
  },
});

// Nested property
const users = await prisma.user.findMany({
  where: {
    settings: {
      path: ["notifications", "email"],
      equals: true,
    },
  },
});

// Numeric comparison on nested value
const products = await prisma.product.findMany({
  where: {
    attributes: {
      path: ["dimensions", "weight"],
      gt: 5.0,
    },
  },
});
```

### MySQL Syntax

```typescript
// MySQL uses dot-notation strings instead of arrays
const users = await prisma.user.findMany({
  where: {
    settings: {
      path: "$. theme",
      equals: "dark",
    },
  },
});

const users = await prisma.user.findMany({
  where: {
    settings: {
      path: "$.notifications.email",
      equals: true,
    },
  },
});
```

### String Filters on JSON

```typescript
// Contains substring
const users = await prisma.user.findMany({
  where: {
    settings: {
      path: ["theme"],
      string_contains: "dark",
    },
  },
});

// Starts with
const users = await prisma.user.findMany({
  where: {
    settings: {
      path: ["language"],
      string_starts_with: "en",
    },
  },
});

// Ends with
const users = await prisma.user.findMany({
  where: {
    settings: {
      path: ["email"],
      string_ends_with: "@prisma.io",
    },
  },
});

// Case-insensitive (PostgreSQL)
const users = await prisma.user.findMany({
  where: {
    settings: {
      path: ["theme"],
      string_contains: "Dark",
      mode: "insensitive",
    },
  },
});
```

## Array Filters

### array_contains — Has Values

```typescript
// Scalar array contains value
const users = await prisma.user.findMany({
  where: {
    tags: {
      array_contains: ["typescript"],
    },
  },
});

// Contains multiple values (AND)
const users = await prisma.user.findMany({
  where: {
    tags: {
      array_contains: ["typescript", "prisma"],
    },
  },
});

// Object array contains matching object
const products = await prisma.product.findMany({
  where: {
    variants: {
      array_contains: [{ color: "red", size: "L" }],
    },
  },
});
```

### array_starts_with / array_ends_with

```typescript
// Array starts with value
const users = await prisma.user.findMany({
  where: {
    tags: {
      array_starts_with: ["featured"],
    },
  },
});

// Array ends with value
const users = await prisma.user.findMany({
  where: {
    tags: {
      array_ends_with: ["verified"],
    },
  },
});
```

### Nested Array Filtering

```typescript
// Filter on nested array
const products = await prisma.product.findMany({
  where: {
    attributes: {
      path: ["colors"],
      array_contains: ["red"],
    },
  },
});

// Filter by array index (PostgreSQL)
const users = await prisma.user.findMany({
  where: {
    settings: {
      path: ["recentSearches", "0"],
      equals: "prisma",
    },
  },
});
```

## Handling Null Values

JSON fields have two types of null:

| Type | Meaning | Constant |
|------|---------|----------|
| `JsonNull` | The JSON value `null` (stored as `null` in JSON) | `Prisma.JsonNull` |
| `DbNull` | SQL `NULL` (no value at all) | `Prisma.DbNull` |
| `AnyNull` | Either type of null (filtering only) | `Prisma.AnyNull` |

### Writing Null Values

```typescript
// Store JSON null: {"settings": null}
await prisma.user.update({
  where: { id: 1 },
  data: { metadata: Prisma.JsonNull },
});

// Store database NULL (field has no value)
await prisma.user.update({
  where: { id: 1 },
  data: { metadata: Prisma.DbNull },
});
```

### Filtering Null Values

```typescript
// Find records where metadata is JSON null
const users = await prisma.user.findMany({
  where: { metadata: { equals: Prisma.JsonNull } },
});

// Find records where metadata is DB NULL
const users = await prisma.user.findMany({
  where: { metadata: { equals: Prisma.DbNull } },
});

// Find records where metadata is either null type
const users = await prisma.user.findMany({
  where: { metadata: { equals: Prisma.AnyNull } },
});
```

**Important**: Using plain `null` in a JSON field filter is ambiguous. Always use the explicit `Prisma.JsonNull`, `Prisma.DbNull`, or `Prisma.AnyNull` constants.

## Type Safety with JSON

By default, JSON fields are typed as `Prisma.JsonValue`. For stronger typing, use `prisma-json-types-generator`:

```prisma
generator client {
  provider = "prisma-client"
  output   = "../src/generated/prisma"
}

generator jsonTypes {
  provider = "prisma-json-types-generator"
}

model User {
  id       Int  @id @default(autoincrement())
  /// [UserSettings]
  settings Json @default("{}")
}
```

```typescript
// src/json-types.d.ts
declare global {
  namespace PrismaJson {
    interface UserSettings {
      theme: "light" | "dark";
      language: string;
      notifications: {
        email: boolean;
        push: boolean;
      };
    }
  }
}
export {};
```

Now `user.settings` is typed as `UserSettings` instead of `JsonValue`.

## Common Patterns

### Feature Flags

```typescript
interface FeatureFlags {
  betaFeatures: boolean;
  maxUploadSize: number;
  allowedFormats: string[];
}

await prisma.user.update({
  where: { id: 1 },
  data: {
    settings: {
      ...(currentSettings as object),
      featureFlags: { betaFeatures: true, maxUploadSize: 100, allowedFormats: ["pdf", "png"] },
    },
  },
});
```

### EAV (Entity-Attribute-Value) Alternative

```typescript
// Instead of a separate attributes table, use JSON
const product = await prisma.product.create({
  data: {
    name: "T-Shirt",
    attributes: {
      color: "blue",
      size: "M",
      material: "cotton",
      weight_grams: 200,
    },
  },
});

// Query by attribute
const blueProducts = await prisma.product.findMany({
  where: {
    attributes: { path: ["color"], equals: "blue" },
  },
});
```

## Limitations

1. **No partial updates** — Must replace entire JSON value (read-modify-write)
2. **No key-subset selection** — Cannot select specific JSON keys; returns entire object
3. **No sorting by JSON property** — Cannot `orderBy` a nested JSON field
4. **No key-existence checks** — Cannot filter by whether a JSON key exists
5. **MySQL array object filtering** — MySQL supports `$[*].key` syntax; PostgreSQL does not
6. **SQLite not supported** — JSON type is not available for SQLite
