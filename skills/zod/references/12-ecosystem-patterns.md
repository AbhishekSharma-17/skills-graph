# Ecosystem and Integration Patterns

> Source: [zod.dev/ecosystem](https://zod.dev/ecosystem), [zod.dev/library-authors](https://zod.dev/library-authors)

## Table of Contents

- [tRPC Integration](#trpc-integration)
- [React Hook Form](#react-hook-form)
- [Next.js Server Actions](#nextjs-server-actions)
- [Express / Fastify Middleware](#express--fastify-middleware)
- [Prisma Integration](#prisma-integration)
- [Environment Variables](#environment-variables)
- [Library Author Guide](#library-author-guide)
- [Standard Schema](#standard-schema)
- [Ecosystem Tools](#ecosystem-tools)

---

## tRPC Integration

tRPC uses Zod for end-to-end type-safe APIs without code generation:

```typescript
import { initTRPC } from "@trpc/server";
import { z } from "zod";

const t = initTRPC.create();

const appRouter = t.router({
  getUser: t.procedure
    .input(z.object({
      id: z.string(),
    }))
    .query(async ({ input }) => {
      // input is typed as { id: string }
      return await db.user.findUnique({ where: { id: input.id } });
    }),

  createUser: t.procedure
    .input(z.object({
      name: z.string().min(1),
      email: z.email(),
      role: z.enum(["admin", "user"]).default("user"),
    }))
    .mutation(async ({ input }) => {
      return await db.user.create({ data: input });
    }),
});
```

## React Hook Form

Use `@hookform/resolvers/zod` for Zod-powered form validation:

```typescript
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

const FormSchema = z.object({
  email: z.email({ error: "Invalid email" }),
  password: z.string().min(8, { error: "At least 8 characters" }),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  error: "Passwords don't match",
  path: ["confirmPassword"],
});

type FormData = z.infer<typeof FormSchema>;

function LoginForm() {
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(FormSchema),
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register("email")} />
      {errors.email && <span>{errors.email.message}</span>}

      <input type="password" {...register("password")} />
      {errors.password && <span>{errors.password.message}</span>}

      <input type="password" {...register("confirmPassword")} />
      {errors.confirmPassword && <span>{errors.confirmPassword.message}</span>}

      <button type="submit">Login</button>
    </form>
  );
}
```

## Next.js Server Actions

Validate server action inputs with Zod:

```typescript
"use server";

import { z } from "zod";

const CreatePostSchema = z.object({
  title: z.string().min(1).max(200),
  content: z.string().min(10),
  tags: z.array(z.string()).max(5).default([]),
});

export async function createPost(formData: FormData) {
  const result = CreatePostSchema.safeParse({
    title: formData.get("title"),
    content: formData.get("content"),
    tags: formData.getAll("tags"),
  });

  if (!result.success) {
    return {
      errors: z.flattenError(result.error).fieldErrors,
    };
  }

  await db.post.create({ data: result.data });
  return { success: true };
}
```

## Express / Fastify Middleware

### Express Validation Middleware

```typescript
import { z, ZodType } from "zod";
import { Request, Response, NextFunction } from "express";

function validate(schema: ZodType) {
  return (req: Request, res: Response, next: NextFunction) => {
    const result = schema.safeParse(req.body);
    if (!result.success) {
      return res.status(400).json({
        errors: z.flattenError(result.error).fieldErrors,
      });
    }
    req.body = result.data;
    next();
  };
}

// Usage
app.post("/api/users",
  validate(z.object({
    name: z.string(),
    email: z.email(),
  })),
  (req, res) => {
    // req.body is validated
    res.json({ user: req.body });
  }
);
```

### Query Parameter Validation

```typescript
function validateQuery(schema: ZodType) {
  return (req: Request, res: Response, next: NextFunction) => {
    const result = schema.safeParse(req.query);
    if (!result.success) {
      return res.status(400).json({
        errors: z.flattenError(result.error).fieldErrors,
      });
    }
    req.query = result.data;
    next();
  };
}

app.get("/api/search",
  validateQuery(z.object({
    q: z.string().min(1),
    page: z.coerce.number().int().positive().default(1),
    limit: z.coerce.number().int().positive().max(100).default(20),
  })),
  handler
);
```

## Prisma Integration

Generate Zod schemas from Prisma models with `prisma-zod-generator`:

```typescript
// Manually define schemas matching Prisma models
const UserCreateInput = z.object({
  name: z.string(),
  email: z.email(),
  role: z.enum(["ADMIN", "USER"]).default("USER"),
});

const UserUpdateInput = UserCreateInput.partial();

const UserWhereInput = z.object({
  id: z.string().optional(),
  email: z.email().optional(),
  role: z.enum(["ADMIN", "USER"]).optional(),
});
```

## Environment Variables

Robust env var parsing with Zod:

```typescript
import { z } from "zod";

const EnvSchema = z.object({
  // Required
  DATABASE_URL: z.string().url(),
  REDIS_URL: z.string().url(),
  JWT_SECRET: z.string().min(32),

  // With defaults
  PORT: z.coerce.number().int().default(3000),
  NODE_ENV: z.enum(["development", "production", "test"]).default("development"),
  LOG_LEVEL: z.enum(["debug", "info", "warn", "error"]).default("info"),

  // Optional
  SENTRY_DSN: z.string().url().optional(),
  SMTP_HOST: z.string().optional(),

  // Boolean from string
  DEBUG: z.stringbool().default(false),
  ENABLE_CACHE: z.stringbool().default(true),
});

export type Env = z.infer<typeof EnvSchema>;

// Parse and export — fails fast on missing/invalid vars
export const env = EnvSchema.parse(process.env);
```

## Library Author Guide

### Peer Dependencies

```json
{
  "peerDependencies": {
    "zod": "^3.25.0 || ^4.0.0"
  }
}
```

### Import from Versioned Subpaths

```typescript
// Always use versioned subpaths
import * as z4 from "zod/v4/core"; // shared core
import * as z3 from "zod/v3";      // v3 specific

// Never import from "zod" directly in libraries
```

### Accept Schemas Generically

```typescript
import * as z4 from "zod/v4/core";

// Correct: preserves type info
function process<T extends z4.$ZodType>(schema: T): z4.output<T> {
  return z4.parse(schema, data);
}

// Support both v3 and v4
type AnySchema = z3.ZodTypeAny | z4.$ZodType;

function isZod4(schema: AnySchema): schema is z4.$ZodType {
  return "_zod" in schema;
}
```

## Standard Schema

For libraries that want to accept any validation library (Zod, Valibot, ArkType, etc.):

```typescript
import type { StandardSchemaV1 } from "@standard-schema/spec";

function validate<T>(schema: StandardSchemaV1<T>, data: unknown): T {
  const result = schema["~standard"].validate(data);
  if (result.issues) throw new Error("Validation failed");
  return result.value as T;
}
```

Zod implements the Standard Schema interface automatically.

## Ecosystem Tools

### Code Generation (Zod → X)
- **zod-openapi** — Generate OpenAPI v3.x from Zod schemas
- **prisma-zod-generator** — Prisma model → Zod schema
- **zod2md** — Zod schema → Markdown documentation

### Code Generation (X → Zod)
- **orval** — OpenAPI → Zod schemas + API client
- **Hey API** — OpenAPI → TypeScript with Zod
- **kubb** — OpenAPI → Zod, React Query, etc.

### Testing
- **@traversable/zod-test** — Fuzz testing with Zod schemas
- **zod-schema-faker** — Generate fake data from Zod schemas
- **zocker** — Mock data generation

### Utilities
- **zod-playground** — Interactive schema testing
- **eslint-plugin-zod-x** — ESLint rules for Zod
- **babel-plugin-zod-hoist** — Performance optimization
