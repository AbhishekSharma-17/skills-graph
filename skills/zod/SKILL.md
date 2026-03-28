---
name: zod
description: "TypeScript-first schema validation with static type inference (Zod v4). MANDATORY TRIGGERS: zod, schema validation, z.object, z.string, z.infer, zod schema. Also trigger when building TypeScript form validation, API input parsing, runtime type checking, JSON Schema conversion, or data validation pipelines. When in doubt about whether to use this skill for TypeScript validation tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["typescript", "validation", "schema", "zod", "type-inference", "parsing"]
---

# Zod — TypeScript-First Schema Validation

> **Source**: [zod.dev](https://zod.dev) | **Tracked version**: Zod 4.x (npm `zod@^4.0.0`)

## Reference Files

| File | Read When |
|------|-----------|
| [00-overview.md](references/00-overview.md) | Getting started, installation, core concepts |
| [01-primitive-types.md](references/01-primitive-types.md) | Strings, numbers, booleans, literals, enums, coercion |
| [02-string-formats.md](references/02-string-formats.md) | Email, UUID, URL, IP, date/time format validators |
| [03-objects-collections.md](references/03-objects-collections.md) | Objects, arrays, tuples, records, maps, sets |
| [04-unions-intersections.md](references/04-unions-intersections.md) | Union, discriminated union, XOR, intersection |
| [05-type-inference.md](references/05-type-inference.md) | z.infer, z.input, z.output, branded types |
| [06-refinements-transforms.md](references/06-refinements-transforms.md) | Custom validation, transforms, pipes, preprocess |
| [07-codecs.md](references/07-codecs.md) | Bidirectional transforms, encode/decode |
| [08-error-handling.md](references/08-error-handling.md) | ZodError, error maps, formatting, i18n |
| [09-metadata-registries.md](references/09-metadata-registries.md) | Registries, global registry, .meta(), .describe() |
| [10-json-schema.md](references/10-json-schema.md) | toJSONSchema, fromJSONSchema, OpenAPI targets |
| [11-migration-v3-to-v4.md](references/11-migration-v3-to-v4.md) | Breaking changes, migration guide, codemod |
| [12-ecosystem-patterns.md](references/12-ecosystem-patterns.md) | tRPC, React Hook Form, form validation, API integration |

## Installation

```bash
npm install zod         # Full package (2kb gzipped core)
npm install @zod/mini   # Tree-shakable mini (~1.9kb gzipped)
```

Requires **TypeScript 5.5+** with `strict` mode enabled.

## Quick Reference

- [Zod Documentation](https://zod.dev)
- [Zod GitHub](https://github.com/colinhacks/zod)
- [npm: zod](https://www.npmjs.com/package/zod)
- [Zod v4 Release Notes](https://zod.dev/v4)
