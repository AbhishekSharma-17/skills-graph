# Metadata and Registries

> Source: [zod.dev/metadata](https://zod.dev/metadata)

## Table of Contents

- [Overview](#overview)
- [Creating Registries](#creating-registries)
- [Registry Operations](#registry-operations)
- [Global Registry](#global-registry)
- [The `.meta()` Method](#the-meta-method)
- [The `.describe()` Method](#the-describe-method)
- [Custom Registries](#custom-registries)
- [Augmenting Global Metadata](#augmenting-global-metadata)
- [Common Patterns](#common-patterns)

---

## Overview

Zod v4 provides a **registry** system to associate schemas with structured metadata. This enables:

- Documentation generation
- Code generation
- AI structured output definitions
- Form label/description generation
- JSON Schema enrichment
- Schema introspection

## Creating Registries

A registry is a typed collection linking schemas to metadata:

```typescript
import { z } from "zod";

// Define metadata shape
const myRegistry = z.registry<{ description: string }>();

// With more fields
const formRegistry = z.registry<{
  label: string;
  placeholder?: string;
  helpText?: string;
}>();
```

## Registry Operations

### Add

```typescript
const nameSchema = z.string();
myRegistry.add(nameSchema, { description: "User's full name" });
```

### Has

```typescript
myRegistry.has(nameSchema); // true
```

### Get

```typescript
myRegistry.get(nameSchema);
// { description: "User's full name" }
```

### Remove

```typescript
myRegistry.remove(nameSchema);
```

### Clear

```typescript
myRegistry.clear(); // empties the registry
```

### Inline Registration with `.register()`

```typescript
const User = z.object({
  name: z.string().register(myRegistry, { description: "Full name" }),
  age: z.number().register(myRegistry, { description: "Age in years" }),
});

// .register() returns the original schema (chainable)
```

## Global Registry

Zod provides `z.globalRegistry` with a predefined metadata type:

```typescript
interface GlobalMeta {
  id?: string;         // unique identifier
  title?: string;      // display title
  description?: string;
  deprecated?: boolean;
  [k: string]: unknown;
}
```

### Using the Global Registry

```typescript
z.globalRegistry.add(nameSchema, {
  id: "user_name",
  title: "User Name",
  description: "The user's full legal name",
});
```

**Important**: The `id` field must be unique. Registering two schemas with the same `id` throws an error.

## The `.meta()` Method

`.meta()` is a shorthand for registering in the global registry:

```typescript
const emailSchema = z.email().meta({
  id: "email_address",
  title: "Email Address",
  description: "A valid email address",
});
```

### Reading Metadata

Call `.meta()` without arguments to retrieve:

```typescript
emailSchema.meta();
// { id: "email_address", title: "Email Address", description: "A valid email address" }
```

### Metadata Does Not Transfer Through Transforms

Since Zod methods are immutable (returning new instances), metadata is bound to specific instances:

```typescript
const A = z.string().meta({ description: "A cool string" });
A.meta(); // { description: "A cool string" }

const B = A.refine(() => true);
B.meta(); // undefined — B is a new instance
```

If you need metadata after transforms, re-register:

```typescript
const B = A.refine(() => true).meta({ description: "A refined string" });
```

## The `.describe()` Method

A convenience shorthand for setting only the `description` field:

```typescript
const schema = z.string().describe("A brief description");

// Equivalent to:
z.string().meta({ description: "A brief description" });
```

This is kept for backward compatibility with Zod 3.

## Custom Registries

### Type-Safe Metadata with Inferred Types

Use `z.$output` to reference a schema's inferred type in metadata:

```typescript
type WithExamples = { examples: z.$output[] };
const exampleRegistry = z.registry<WithExamples>();

exampleRegistry.add(z.string(), { examples: ["hello", "world"] });
exampleRegistry.add(z.number(), { examples: [1, 2, 3] });
// TypeScript enforces correct example types
```

Use `z.$input` for input type references.

### Schema Type Constraints

Restrict a registry to specific schema types:

```typescript
const stringRegistry = z.registry<
  { pattern: string },
  z.ZodString  // only string schemas allowed
>();

stringRegistry.add(z.string(), { pattern: ".*" });   // OK
// stringRegistry.add(z.number(), { pattern: ".*" }); // TypeScript error
```

## Augmenting Global Metadata

Extend `GlobalMeta` via TypeScript declaration merging:

```typescript
declare module "zod" {
  interface GlobalMeta {
    examples?: unknown[];
    component?: string;
    priority?: number;
  }
}

export {};
```

Now all `.meta()` calls accept the new fields:

```typescript
z.string().meta({
  description: "User name",
  examples: ["Alice", "Bob"],
  component: "TextInput",
  priority: 1,
});
```

## Common Patterns

### Form Generation

```typescript
const formRegistry = z.registry<{
  label: string;
  placeholder?: string;
  inputType?: "text" | "email" | "number" | "password";
}>();

const LoginForm = z.object({
  email: z.email().register(formRegistry, {
    label: "Email Address",
    placeholder: "you@example.com",
    inputType: "email",
  }),
  password: z.string().min(8).register(formRegistry, {
    label: "Password",
    placeholder: "Enter your password",
    inputType: "password",
  }),
});
```

### API Documentation

```typescript
const UserSchema = z.object({
  id: z.string().meta({ description: "Unique user identifier" }),
  name: z.string().meta({ description: "User's display name" }),
  email: z.email().meta({ description: "Primary email address" }),
  role: z.enum(["admin", "user"]).meta({
    description: "User role",
    deprecated: false,
  }),
});
```

### JSON Schema Enrichment

Metadata flows into JSON Schema conversion:

```typescript
z.globalRegistry.add(UserSchema, { id: "User" });

z.toJSONSchema(UserSchema);
// JSON Schema includes title, description from metadata
```

### Schema Catalog

```typescript
const catalog = z.registry<{
  version: string;
  owner: string;
  tags: string[];
}>();

const schemas = {
  user: z.object({ /* ... */ }).register(catalog, {
    version: "2.0",
    owner: "auth-team",
    tags: ["user", "identity"],
  }),
  order: z.object({ /* ... */ }).register(catalog, {
    version: "1.5",
    owner: "commerce-team",
    tags: ["order", "payment"],
  }),
};
```
