# Drizzle ORM — Validation (Zod Integration)

> Source: [orm.drizzle.team/docs/zod](https://orm.drizzle.team/docs/zod)

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Creating Schemas](#creating-schemas)
- [Select Schema](#select-schema)
- [Insert Schema](#insert-schema)
- [Update Schema](#update-schema)
- [Refinements](#refinements)
- [Schema Factory](#schema-factory)
- [Valibot Integration](#valibot-integration)
- [TypeBox Integration](#typebox-integration)
- [Practical Patterns](#practical-patterns)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

Drizzle provides first-class integration with validation libraries to generate runtime validation schemas from your database table definitions. This bridges the gap between compile-time type safety and runtime data validation.

Supported libraries:
- **Zod** — Most popular, built-in support
- **Valibot** — Lightweight alternative
- **TypeBox** — JSON Schema compatible

As of Drizzle ORM v1.0.0-beta, all validation integrations are built into the `drizzle-orm` package directly (the standalone `drizzle-zod` package is deprecated).

## Installation

```bash
# Zod must be installed separately
npm install zod

# Drizzle's Zod integration is built-in (no extra package needed)
# Import from drizzle-orm/zod
```

## Creating Schemas

Three schema generators map to database operations:

```typescript
import { createSelectSchema, createInsertSchema, createUpdateSchema } from 'drizzle-orm/zod';
import { pgTable, serial, text, integer, timestamp } from 'drizzle-orm/pg-core';

export const users = pgTable('users', {
  id: serial('id').primaryKey(),
  name: text('name').notNull(),
  email: text('email').notNull(),
  age: integer('age'),
  role: text('role', { enum: ['admin', 'user', 'guest'] }).default('user').notNull(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
});

const selectUserSchema = createSelectSchema(users);
const insertUserSchema = createInsertSchema(users);
const updateUserSchema = createUpdateSchema(users);
```

## Select Schema

Validates data coming FROM the database (e.g., API response validation):

```typescript
const selectUserSchema = createSelectSchema(users);

// Validates: { id: number; name: string; email: string; age: number | null; role: 'admin' | 'user' | 'guest'; createdAt: Date }

const user = selectUserSchema.parse(rawData);
```

All columns are required in select schemas (matching the actual DB output).

## Insert Schema

Validates data going INTO the database:

```typescript
const insertUserSchema = createInsertSchema(users);

// Required: name, email
// Optional: id (serial), age (nullable), role (has default), createdAt (has default)

const validated = insertUserSchema.parse({
  name: 'Alice',
  email: 'alice@example.com',
});
```

Columns with defaults, auto-increment, or nullable types become optional in insert schemas.

## Update Schema

All fields are optional (partial update):

```typescript
const updateUserSchema = createUpdateSchema(users);

// All fields optional — validates partial updates
// Generated columns are excluded

const validated = updateUserSchema.parse({
  name: 'Alice Smith',
  // Only name will be updated
});
```

## Refinements

Override or extend generated schemas per-column:

### Callback refinement

```typescript
const insertUserSchema = createInsertSchema(users, {
  // Extend the generated schema
  name: (schema) => schema.min(2).max(100),
  email: (schema) => schema.email(),
  age: (schema) => schema.min(0).max(150),
});
```

### Complete override

```typescript
import { z } from 'zod';

const insertUserSchema = createInsertSchema(users, {
  // Replace with a completely custom schema
  email: z.string().email().toLowerCase(),
  role: z.enum(['admin', 'user']),  // Restrict allowed values
  metadata: z.object({               // Custom nested object
    theme: z.string(),
    notifications: z.boolean(),
  }),
});
```

### Combining callback and override

```typescript
const insertUserSchema = createInsertSchema(users, {
  name: (schema) => schema.min(1),           // Callback: extends base
  email: z.string().email(),                  // Override: replaces base
  age: (schema) => schema.positive().max(120), // Callback: extends base
});
```

## Schema Factory

For advanced use cases like custom Zod instances or type coercion:

```typescript
import { z } from 'zod';
import { createSchemaFactory } from 'drizzle-orm/zod';

const { createInsertSchema, createSelectSchema, createUpdateSchema } = createSchemaFactory({
  // Use a custom Zod instance (e.g., with custom error map)
  zodInstance: z,

  // Auto-coerce types (useful for form data)
  coerce: {
    date: true,    // Coerce strings to Date
    number: true,  // Coerce strings to number
    boolean: true, // Coerce strings to boolean
  },
});

// Use the factory-created functions
const insertSchema = createInsertSchema(users);
```

### Coercion is useful for HTTP APIs

```typescript
const { createInsertSchema } = createSchemaFactory({
  coerce: { date: true },
});

const schema = createInsertSchema(users);

// Now accepts ISO strings for date/timestamp columns
schema.parse({
  name: 'Alice',
  email: 'alice@example.com',
  createdAt: '2024-01-15T10:30:00Z',  // Auto-coerced to Date
});
```

## Valibot Integration

```typescript
import { createSelectSchema, createInsertSchema } from 'drizzle-orm/valibot';
import * as v from 'valibot';

const insertUserSchema = createInsertSchema(users, {
  email: (schema) => v.pipe(schema, v.email()),
  name: (schema) => v.pipe(schema, v.minLength(2)),
});
```

## TypeBox Integration

```typescript
import { createSelectSchema, createInsertSchema } from 'drizzle-orm/typebox';
import { Type } from '@sinclair/typebox';

const insertUserSchema = createInsertSchema(users, {
  email: Type.String({ format: 'email' }),
});
```

## Practical Patterns

### API endpoint validation

```typescript
import { createInsertSchema, createSelectSchema } from 'drizzle-orm/zod';

const insertUserSchema = createInsertSchema(users, {
  name: (s) => s.min(1).max(100),
  email: (s) => s.email(),
});

const selectUserSchema = createSelectSchema(users);

// Express/Hono endpoint
app.post('/users', async (c) => {
  const body = insertUserSchema.parse(await c.req.json());
  const [user] = await db.insert(users).values(body).returning();
  return c.json(selectUserSchema.parse(user));
});
```

### Form validation (React)

```typescript
const createUserForm = createInsertSchema(users, {
  name: (s) => s.min(1, 'Name is required'),
  email: (s) => s.email('Invalid email address'),
}).pick({ name: true, email: true, age: true });

// Use with react-hook-form + @hookform/resolvers/zod
const form = useForm({
  resolver: zodResolver(createUserForm),
});
```

### tRPC input validation

```typescript
import { createInsertSchema } from 'drizzle-orm/zod';

const insertUserInput = createInsertSchema(users)
  .pick({ name: true, email: true, age: true });

export const userRouter = router({
  create: publicProcedure
    .input(insertUserInput)
    .mutation(async ({ input }) => {
      return db.insert(users).values(input).returning();
    }),
});
```

### Separate API schemas from DB schemas

```typescript
// schemas/user.ts
const baseInsert = createInsertSchema(users);

// Public API schema (stricter)
export const createUserInput = baseInsert
  .pick({ name: true, email: true, age: true })
  .extend({
    name: z.string().min(2).max(100),
    email: z.string().email(),
  });

// Admin API schema (more permissive)
export const adminCreateUserInput = baseInsert
  .pick({ name: true, email: true, age: true, role: true });
```

## Common Pitfalls

1. **`drizzle-zod` package is deprecated** — Import from `drizzle-orm/zod` directly. The standalone package is no longer maintained.

2. **No runtime validation by default** — `$type<T>()` on columns only provides compile-time types. You need Zod schemas for actual runtime validation.

3. **Refinements don't stack with callbacks** — If you use a callback `(schema) => schema.min(1)`, it extends the base. If you pass a raw `z.string()`, it replaces the base entirely.

4. **JSON columns generate `z.any()`** — JSON/JSONB columns without `$type<>()` generate permissive schemas. Always refine them.

5. **Enum types are preserved** — `text('role', { enum: [...] })` generates `z.enum([...])` automatically. MySQL `mysqlEnum` also maps correctly.

---

**Related:** [Schema Declaration](./01-schema-declaration.md) | [Select Queries](./04-select-queries.md)
