# Prisma Client Extensions

> Source: [prisma.io/docs/orm/prisma-client/client-extensions](https://www.prisma.io/docs/orm/prisma-client/client-extensions) — Prisma ORM v7.x

## Table of Contents

- [Overview](#overview)
- [Creating Extensions](#creating-extensions)
- [Model Extensions](#model-extensions)
- [Result Extensions (Computed Fields)](#result-extensions-computed-fields)
- [Query Extensions (Middleware)](#query-extensions-middleware)
- [Client Extensions](#client-extensions)
- [Composing Extensions](#composing-extensions)
- [Type Safety](#type-safety)
- [Common Patterns](#common-patterns)

---

## Overview

Client Extensions let you add custom functionality to Prisma Client through four component types:

| Component | Purpose | Example |
|-----------|---------|---------|
| `model` | Add custom methods to models | `prisma.user.signUp()` |
| `result` | Add computed fields to query results | `user.fullName` |
| `query` | Intercept and modify queries (middleware) | Logging, soft delete |
| `client` | Add methods to the client instance | `prisma.$log()` |

Extensions replaced the deprecated `$use()` middleware API.

## Creating Extensions

### Inline Extension

```typescript
const prisma = new PrismaClient({ adapter }).$extends({
  name: "myExtension",
  model: { /* ... */ },
  result: { /* ... */ },
  query: { /* ... */ },
  client: { /* ... */ },
});
```

### Reusable Extension

```typescript
import { Prisma } from "./generated/prisma/index.js";

const auditExtension = Prisma.defineExtension({
  name: "audit",
  query: {
    $allModels: {
      async $allOperations({ model, operation, args, query }) {
        const start = performance.now();
        const result = await query(args);
        const duration = performance.now() - start;
        console.log(`${model}.${operation}: ${duration.toFixed(2)}ms`);
        return result;
      },
    },
  },
});

const prisma = new PrismaClient({ adapter }).$extends(auditExtension);
```

## Model Extensions

Add custom methods to specific models:

```typescript
const prisma = new PrismaClient({ adapter }).$extends({
  model: {
    user: {
      async signUp(email: string, name: string) {
        return prisma.user.create({
          data: { email, name, role: "USER" },
        });
      },

      async findByEmail(email: string) {
        return prisma.user.findUnique({ where: { email } });
      },

      async softDelete(id: number) {
        return prisma.user.update({
          where: { id },
          data: { deletedAt: new Date() },
        });
      },
    },

    post: {
      async publish(id: number) {
        return prisma.post.update({
          where: { id },
          data: { published: true, publishedAt: new Date() },
        });
      },
    },
  },
});

// Usage
const user = await prisma.user.signUp("alice@example.com", "Alice");
const found = await prisma.user.findByEmail("alice@example.com");
await prisma.post.publish(1);
```

### Methods on All Models

```typescript
const prisma = new PrismaClient({ adapter }).$extends({
  model: {
    $allModels: {
      async exists<T>(
        this: T,
        where: Prisma.Args<T, "findFirst">["where"]
      ): Promise<boolean> {
        const context = Prisma.getExtensionContext(this);
        const result = await (context as any).findFirst({ where });
        return result !== null;
      },
    },
  },
});

// Usage on any model
const userExists = await prisma.user.exists({ email: "alice@example.com" });
const postExists = await prisma.post.exists({ id: 1 });
```

## Result Extensions (Computed Fields)

Add virtual computed fields to query results:

```typescript
const prisma = new PrismaClient({ adapter }).$extends({
  result: {
    user: {
      fullName: {
        needs: { firstName: true, lastName: true },
        compute(user) {
          return `${user.firstName} ${user.lastName}`;
        },
      },
    },
  },
});

const user = await prisma.user.findUnique({ where: { id: 1 } });
console.log(user.fullName); // "Alice Smith"
```

### Multiple Computed Fields

```typescript
const prisma = new PrismaClient({ adapter }).$extends({
  result: {
    user: {
      fullName: {
        needs: { firstName: true, lastName: true },
        compute(user) {
          return `${user.firstName} ${user.lastName}`;
        },
      },
      initials: {
        needs: { firstName: true, lastName: true },
        compute(user) {
          return `${user.firstName[0]}${user.lastName[0]}`;
        },
      },
    },
    post: {
      excerpt: {
        needs: { content: true },
        compute(post) {
          return post.content?.slice(0, 150) ?? "";
        },
      },
    },
  },
});
```

### Computed Fields with Sensitive Data

```typescript
const prisma = new PrismaClient({ adapter }).$extends({
  result: {
    user: {
      maskedEmail: {
        needs: { email: true },
        compute(user) {
          const [local, domain] = user.email.split("@");
          return `${local[0]}***@${domain}`;
        },
      },
    },
  },
});
```

## Query Extensions (Middleware)

Intercept queries before/after execution — the replacement for `$use()`:

### Logging All Queries

```typescript
const prisma = new PrismaClient({ adapter }).$extends({
  query: {
    $allModels: {
      async $allOperations({ model, operation, args, query }) {
        const start = performance.now();
        const result = await query(args);
        const ms = performance.now() - start;
        console.log(`${model}.${operation} took ${ms.toFixed(0)}ms`);
        return result;
      },
    },
  },
});
```

### Soft Delete

```typescript
const softDeleteExtension = Prisma.defineExtension({
  query: {
    $allModels: {
      async delete({ model, args, query }) {
        return (prisma as any)[model[0].toLowerCase() + model.slice(1)].update({
          ...args,
          data: { deletedAt: new Date() },
        });
      },
      async deleteMany({ model, args, query }) {
        return (prisma as any)[model[0].toLowerCase() + model.slice(1)].updateMany({
          ...args,
          data: { deletedAt: new Date() },
        });
      },
      async findMany({ args, query }) {
        args.where = { ...args.where, deletedAt: null };
        return query(args);
      },
      async findFirst({ args, query }) {
        args.where = { ...args.where, deletedAt: null };
        return query(args);
      },
    },
  },
});
```

### Model-Specific Query Extensions

```typescript
const prisma = new PrismaClient({ adapter }).$extends({
  query: {
    user: {
      async create({ args, query }) {
        // Hash password before creating
        if (args.data.password) {
          args.data.password = await hashPassword(args.data.password);
        }
        return query(args);
      },
      async update({ args, query }) {
        if (args.data.password && typeof args.data.password === "string") {
          args.data.password = await hashPassword(args.data.password);
        }
        return query(args);
      },
    },
  },
});
```

### Operation-Specific Hooks

```typescript
const prisma = new PrismaClient({ adapter }).$extends({
  query: {
    $allModels: {
      create({ model, args, query }) {
        console.log(`Creating ${model}`);
        return query(args);
      },
      update({ model, args, query }) {
        console.log(`Updating ${model}`);
        return query(args);
      },
      delete({ model, args, query }) {
        console.log(`Deleting ${model}`);
        return query(args);
      },
    },
  },
});
```

## Client Extensions

Add methods to the Prisma Client instance itself:

```typescript
const prisma = new PrismaClient({ adapter }).$extends({
  client: {
    async $totalUsers() {
      return prisma.user.count();
    },
    async $healthCheck() {
      try {
        await prisma.$queryRaw`SELECT 1`;
        return { status: "ok" };
      } catch {
        return { status: "error" };
      }
    },
  },
});

const total = await prisma.$totalUsers();
const health = await prisma.$healthCheck();
```

## Composing Extensions

Chain multiple extensions:

```typescript
const loggingExtension = Prisma.defineExtension({ /* ... */ });
const softDeleteExtension = Prisma.defineExtension({ /* ... */ });
const computedFieldsExtension = Prisma.defineExtension({ /* ... */ });

const prisma = new PrismaClient({ adapter })
  .$extends(loggingExtension)
  .$extends(softDeleteExtension)
  .$extends(computedFieldsExtension);
```

**Execution order**: Query extensions execute first-in, first-out (in declaration order).

**Conflict resolution**: If two extensions define the same method, the last one wins.

**Shared connection pool**: All extended clients share the same underlying connection pool.

## Type Safety

### Typing Extended Clients

```typescript
// Type the extended client for dependency injection
function createPrismaClient() {
  return new PrismaClient({ adapter })
    .$extends(loggingExtension)
    .$extends(computedFieldsExtension);
}

type ExtendedPrismaClient = ReturnType<typeof createPrismaClient>;

// Use in services
class UserService {
  constructor(private prisma: ExtendedPrismaClient) {}

  async getUser(id: number) {
    const user = await this.prisma.user.findUnique({ where: { id } });
    return user?.fullName; // computed field is typed
  }
}
```

### Typing Result Extensions

```typescript
import { Prisma } from "./generated/prisma/index.js";

// Get the type of a query result with extensions
type UserWithFullName = Prisma.UserGetPayload<{}> & { fullName: string };
```

## Common Patterns

### Multi-Tenant Extension

```typescript
function forTenant(tenantId: string) {
  return Prisma.defineExtension({
    query: {
      $allModels: {
        async $allOperations({ args, query }) {
          if (args.where) {
            args.where = { ...args.where, tenantId };
          }
          if (args.data && typeof args.data === "object") {
            (args.data as any).tenantId = tenantId;
          }
          return query(args);
        },
      },
    },
  });
}

const tenantPrisma = prisma.$extends(forTenant("tenant-123"));
```

### Audit Trail Extension

```typescript
const auditTrail = Prisma.defineExtension({
  query: {
    $allModels: {
      async create({ model, args, query }) {
        const result = await query(args);
        await prisma.auditLog.create({
          data: {
            model,
            action: "CREATE",
            recordId: String((result as any).id),
            data: JSON.stringify(args.data),
          },
        });
        return result;
      },
    },
  },
});
```
