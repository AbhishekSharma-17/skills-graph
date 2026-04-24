---
name: nestjs
description: "NestJS progressive Node.js framework for scalable server-side applications with TypeScript, dependency injection, modules, and decorators. MANDATORY TRIGGERS: nestjs, NestJS, nest.js, @nestjs, nest framework, nest backend. Also trigger when user wants to build scalable Node.js backends with dependency injection, create modular TypeScript APIs, implement microservices with Node.js, add GraphQL or WebSocket support to a Node server, or use decorator-based controllers and providers. When in doubt about whether to use this skill for Node.js backend tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["nestjs", "nodejs", "typescript", "backend", "dependency-injection", "microservices", "graphql", "websockets", "rest-api", "enterprise"]
---

# NestJS — Skill Router

> Progressive Node.js framework for building efficient, reliable, and scalable server-side applications.

**Source:** [docs.nestjs.com](https://docs.nestjs.com) | **Package:** `@nestjs/core` v11.x | **License:** MIT

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Setup** | `references/00-overview.md` | Getting started, CLI, project structure, platform selection |
| **Modules** | `references/01-modules.md` | Module system, feature modules, dynamic modules, global modules |
| **Controllers & Routing** | `references/02-controllers-routing.md` | Route handlers, request objects, DTOs, status codes, headers |
| **Providers & DI** | `references/03-providers-dependency-injection.md` | Services, injection, custom providers, scopes, circular deps |
| **Request Pipeline** | `references/04-middleware-guards-interceptors-pipes.md` | Middleware, guards, interceptors, pipes, execution order |
| **Exception Handling** | `references/05-exception-filters.md` | Built-in exceptions, custom filters, validation, error responses |
| **Authentication & Auth** | `references/06-authentication-authorization.md` | JWT, Passport, guards, roles, RBAC, session-based auth |
| **Database Integration** | `references/07-database-integration.md` | TypeORM, Prisma, Mongoose, repository pattern, migrations |
| **GraphQL** | `references/08-graphql.md` | Code-first, schema-first, resolvers, subscriptions, federation |
| **Microservices** | `references/09-microservices.md` | Transport layers, message patterns, gRPC, Kafka, NATS, Redis |
| **WebSockets & Events** | `references/10-websockets-events.md` | Gateways, rooms, namespaces, EventEmitter2, SSE |
| **Testing** | `references/11-testing.md` | Unit tests, integration tests, E2E, testing module, mocking |
| **Config, Swagger & DevOps** | `references/12-configuration-swagger.md` | ConfigModule, env validation, OpenAPI, health checks, logging |

## Installation

```bash
# Create new project
npm i -g @nestjs/cli
nest new my-project

# Or with npx (no global install)
npx @nestjs/cli new my-project

# Core packages
npm install @nestjs/core @nestjs/common @nestjs/platform-express reflect-metadata rxjs
```

## Quick Reference

- **Docs:** https://docs.nestjs.com
- **GitHub:** https://github.com/nestjs/nest
- **npm:** https://www.npmjs.com/package/@nestjs/core
- **Discord:** https://discord.gg/nestjs
- **Courses:** https://courses.nestjs.com
