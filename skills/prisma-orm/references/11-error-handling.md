# Prisma Error Handling

> Source: [prisma.io/docs/orm/reference/error-reference](https://www.prisma.io/docs/orm/reference/error-reference) — Prisma ORM v7.x

## Table of Contents

- [Error Types](#error-types)
- [PrismaClientKnownRequestError](#prismaclientknownrequesterror)
- [Common Error Codes](#common-error-codes)
- [Error Handling Patterns](#error-handling-patterns)
- [Validation Errors](#validation-errors)
- [Connection Errors](#connection-errors)
- [Error Formatting](#error-formatting)
- [Common Patterns](#common-patterns)

---

## Error Types

Prisma Client throws five exception types:

| Error Type | When | Key Properties |
|------------|------|---------------|
| `PrismaClientKnownRequestError` | Query engine returns a recognized error | `code`, `meta`, `message` |
| `PrismaClientUnknownRequestError` | Query engine returns an unrecognized error | `message` |
| `PrismaClientRustPanicError` | Underlying engine crashes | `message` |
| `PrismaClientInitializationError` | Client startup fails | `errorCode`, `message` |
| `PrismaClientValidationError` | Invalid query input | `message` |

All errors include a `clientVersion` property.

## PrismaClientKnownRequestError

The most common error type with structured error codes:

```typescript
import { Prisma } from "./generated/prisma/index.js";

try {
  await prisma.user.create({
    data: { email: "alice@example.com" },
  });
} catch (e) {
  if (e instanceof Prisma.PrismaClientKnownRequestError) {
    console.log(e.code);    // "P2002"
    console.log(e.meta);    // { target: ["email"] }
    console.log(e.message); // "Unique constraint failed..."
  }
}
```

## Common Error Codes

### P2001 — Record Not Found (Where Condition)

```
The record searched for in the where condition does not exist.
```

```typescript
// Happens with findUniqueOrThrow, findFirstOrThrow
try {
  await prisma.user.findUniqueOrThrow({ where: { id: 999 } });
} catch (e) {
  if (e instanceof Prisma.PrismaClientKnownRequestError && e.code === "P2001") {
    console.log("User not found");
  }
}
```

### P2002 — Unique Constraint Violation

```
Unique constraint failed on the {constraint}
```

```typescript
try {
  await prisma.user.create({
    data: { email: "existing@example.com" },
  });
} catch (e) {
  if (e instanceof Prisma.PrismaClientKnownRequestError && e.code === "P2002") {
    const target = e.meta?.target as string[];
    console.log(`Duplicate value on: ${target.join(", ")}`);
    // target: ["email"]
  }
}
```

### P2003 — Foreign Key Constraint Failure

```
Foreign key constraint failed on the field: {field_name}
```

```typescript
try {
  await prisma.post.create({
    data: { title: "Post", authorId: 999 }, // author doesn't exist
  });
} catch (e) {
  if (e instanceof Prisma.PrismaClientKnownRequestError && e.code === "P2003") {
    console.log("Referenced record does not exist");
  }
}
```

### P2025 — Record Not Found (Operation)

```
An operation failed because it depends on one or more records that were required but not found.
```

```typescript
try {
  await prisma.user.update({
    where: { id: 999 },
    data: { name: "Updated" },
  });
} catch (e) {
  if (e instanceof Prisma.PrismaClientKnownRequestError && e.code === "P2025") {
    console.log("Record to update not found");
  }
}
```

### Other Important Codes

| Code | Description |
|------|-------------|
| `P2000` | Value too long for column type |
| `P2004` | Constraint violation (generic) |
| `P2005` | Invalid value for field type |
| `P2006` | Invalid value provided |
| `P2007` | Data validation error |
| `P2008` | Failed to parse query |
| `P2009` | Failed to validate query |
| `P2010` | Raw query failed |
| `P2011` | Null constraint violation |
| `P2012` | Missing required value |
| `P2013` | Missing required argument |
| `P2014` | Required relation violation |
| `P2015` | Related record not found |
| `P2016` | Query interpretation error |
| `P2017` | Records not connected |
| `P2018` | Required connected records not found |
| `P2019` | Input error |
| `P2020` | Value out of range |
| `P2021` | Table does not exist |
| `P2022` | Column does not exist |
| `P2024` | Timed out fetching connection from pool |
| `P2033` | Number doesn't fit in a 64-bit integer |
| `P2034` | Transaction failed due to conflict or deadlock |

## Error Handling Patterns

### Comprehensive Try-Catch

```typescript
import { Prisma } from "./generated/prisma/index.js";

async function createUser(email: string, name: string) {
  try {
    return await prisma.user.create({
      data: { email, name },
    });
  } catch (e) {
    if (e instanceof Prisma.PrismaClientKnownRequestError) {
      switch (e.code) {
        case "P2002":
          throw new ConflictError(`Email "${email}" already exists`);
        case "P2003":
          throw new BadRequestError("Invalid reference");
        default:
          throw new InternalError(`Database error: ${e.code}`);
      }
    }
    if (e instanceof Prisma.PrismaClientValidationError) {
      throw new BadRequestError("Invalid input data");
    }
    throw e;
  }
}
```

### Reusable Error Handler

```typescript
function handlePrismaError(error: unknown): never {
  if (error instanceof Prisma.PrismaClientKnownRequestError) {
    switch (error.code) {
      case "P2002": {
        const fields = (error.meta?.target as string[])?.join(", ");
        throw new ConflictError(`Unique constraint failed on: ${fields}`);
      }
      case "P2003":
        throw new BadRequestError("Referenced record does not exist");
      case "P2025":
        throw new NotFoundError("Record not found");
      case "P2024":
        throw new ServiceUnavailableError("Database connection timeout");
      default:
        throw new InternalError(`Database error [${error.code}]`);
    }
  }

  if (error instanceof Prisma.PrismaClientValidationError) {
    throw new BadRequestError("Invalid query parameters");
  }

  if (error instanceof Prisma.PrismaClientInitializationError) {
    throw new ServiceUnavailableError("Database connection failed");
  }

  throw error;
}
```

### Usage in API Routes

```typescript
// Express
app.post("/users", async (req, res, next) => {
  try {
    const user = await prisma.user.create({ data: req.body });
    res.json(user);
  } catch (e) {
    if (e instanceof Prisma.PrismaClientKnownRequestError) {
      if (e.code === "P2002") {
        return res.status(409).json({ error: "Email already taken" });
      }
    }
    next(e);
  }
});

// FastAPI (Python)
@app.post("/users")
async def create_user(data: UserCreate):
    try:
        return await prisma.user.create(data=data.model_dump())
    except PrismaError as e:
        if e.code == "P2002":
            raise HTTPException(409, "Email already taken")
        raise
```

## Validation Errors

`PrismaClientValidationError` is thrown at query build time, not at the database level:

```typescript
try {
  // Missing required field
  await prisma.user.create({
    data: { name: "Alice" }, // email is required!
  });
} catch (e) {
  if (e instanceof Prisma.PrismaClientValidationError) {
    console.log(e.message);
    // "Argument `email` is missing in data..."
  }
}

try {
  // Wrong type
  await prisma.user.create({
    data: { email: 123 as any, name: "Alice" }, // email should be string
  });
} catch (e) {
  if (e instanceof Prisma.PrismaClientValidationError) {
    console.log(e.message);
  }
}
```

## Connection Errors

```typescript
try {
  await prisma.$connect();
} catch (e) {
  if (e instanceof Prisma.PrismaClientInitializationError) {
    console.error("Failed to connect to database:", e.message);
    // Common causes:
    // - Invalid DATABASE_URL
    // - Database server unreachable
    // - Wrong credentials
    // - SSL configuration issues
  }
}
```

### Connection Pool Timeout

```typescript
try {
  await prisma.user.findMany();
} catch (e) {
  if (
    e instanceof Prisma.PrismaClientKnownRequestError &&
    e.code === "P2024"
  ) {
    console.error("Connection pool exhausted — increase pool size or reduce concurrency");
  }
}
```

## Error Formatting

Configure how errors are displayed:

```typescript
const prisma = new PrismaClient({
  adapter,
  errorFormat: "pretty",      // Human-readable (default in dev)
  // errorFormat: "colorless", // No ANSI colors
  // errorFormat: "minimal",   // Minimal output (recommended for production)
});
```

## Common Patterns

### Upsert Instead of Catching P2002

```typescript
// Instead of try/catch for duplicate
const user = await prisma.user.upsert({
  where: { email: "alice@example.com" },
  update: { name: "Alice Updated" },
  create: { email: "alice@example.com", name: "Alice" },
});
```

### Safe Delete with Not-Found Handling

```typescript
async function safeDelete(id: number) {
  try {
    return await prisma.user.delete({ where: { id } });
  } catch (e) {
    if (
      e instanceof Prisma.PrismaClientKnownRequestError &&
      e.code === "P2025"
    ) {
      return null; // Already deleted or never existed
    }
    throw e;
  }
}
```

### Retry on Transaction Conflict

```typescript
async function withRetry<T>(fn: () => Promise<T>, retries = 3): Promise<T> {
  for (let i = 0; i < retries; i++) {
    try {
      return await fn();
    } catch (e) {
      if (
        e instanceof Prisma.PrismaClientKnownRequestError &&
        e.code === "P2034" &&
        i < retries - 1
      ) {
        await new Promise((r) => setTimeout(r, 100 * 2 ** i));
        continue;
      }
      throw e;
    }
  }
  throw new Error("Unreachable");
}

const result = await withRetry(() =>
  prisma.$transaction(async (tx) => {
    // ... transaction logic
  })
);
```
