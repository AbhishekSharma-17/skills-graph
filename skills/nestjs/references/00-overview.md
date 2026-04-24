# NestJS — Overview & Setup

> Source: [docs.nestjs.com](https://docs.nestjs.com) | @nestjs/core 11.x

## Table of Contents

- [What Is NestJS](#what-is-nestjs)
- [Key Features](#key-features)
- [Installation & Project Setup](#installation--project-setup)
- [Project Structure](#project-structure)
- [Platform Selection: Express vs Fastify](#platform-selection-express-vs-fastify)
- [Application Lifecycle](#application-lifecycle)
- [CLI Commands](#cli-commands)
- [Monorepo Mode](#monorepo-mode)
- [Common Pitfalls](#common-pitfalls)

## What Is NestJS

NestJS is a progressive Node.js framework for building efficient, reliable, and scalable server-side applications. Built with and fully supporting TypeScript, it combines elements of OOP, FP, and FRP. Under the hood it uses Express (default) or Fastify.

Key characteristics:
- **TypeScript-first** — full type safety with decorators and metadata
- **Modular architecture** — organize code into cohesive modules
- **Dependency injection** — built-in IoC container inspired by Angular
- **Decorator-based** — controllers, routes, and metadata via decorators
- **Transport-agnostic** — supports REST, GraphQL, WebSockets, gRPC, microservices
- **65K+ GitHub stars** — massive ecosystem with 3M+ weekly npm downloads
- **Enterprise-ready** — used by Adidas, Autodesk, Roche, BMW, and more

## Key Features

| Feature | Package | Description |
|---------|---------|-------------|
| **REST APIs** | `@nestjs/core` | Controllers, routing, DTOs, validation |
| **GraphQL** | `@nestjs/graphql` | Code-first and schema-first approaches |
| **WebSockets** | `@nestjs/websockets` | Real-time bidirectional communication |
| **Microservices** | `@nestjs/microservices` | TCP, Redis, NATS, Kafka, gRPC, RabbitMQ |
| **Database** | `@nestjs/typeorm` / Prisma | TypeORM, Prisma, Mongoose, Sequelize |
| **Auth** | `@nestjs/passport` | Passport.js strategies, JWT, sessions |
| **OpenAPI** | `@nestjs/swagger` | Auto-generated Swagger documentation |
| **Config** | `@nestjs/config` | Environment variables, validation |
| **Scheduling** | `@nestjs/schedule` | Cron jobs, intervals, timeouts |
| **Queues** | `@nestjs/bull` | Background job processing with Bull/BullMQ |
| **Caching** | `@nestjs/cache-manager` | In-memory, Redis, and custom stores |
| **Health** | `@nestjs/terminus` | Health check endpoints for monitoring |
| **Events** | `@nestjs/event-emitter` | Event-driven architecture with EventEmitter2 |
| **CQRS** | `@nestjs/cqrs` | Command/Query Responsibility Segregation |
| **Throttle** | `@nestjs/throttler` | Rate limiting and throttling |

## Installation & Project Setup

### Prerequisites

- Node.js >= 20 (LTS recommended)
- npm, yarn, or pnpm

### Create a New Project

```bash
# Install CLI globally
npm i -g @nestjs/cli

# Create project (choose npm/yarn/pnpm)
nest new my-api

# Or use npx without global install
npx @nestjs/cli new my-api

# Navigate and start
cd my-api
npm run start:dev
```

The dev server starts at `http://localhost:3000` by default.

### Manual Setup

```bash
npm install @nestjs/core @nestjs/common @nestjs/platform-express reflect-metadata rxjs
```

### tsconfig.json Requirements

```json
{
  "compilerOptions": {
    "module": "commonjs",
    "declaration": true,
    "removeComments": true,
    "emitDecoratorMetadata": true,
    "experimentalDecorators": true,
    "allowSyntheticDefaultImports": true,
    "target": "ES2021",
    "sourceMap": true,
    "outDir": "./dist",
    "baseUrl": "./",
    "incremental": true,
    "strict": true
  }
}
```

## Project Structure

```
src/
├── app.module.ts          # Root module
├── app.controller.ts      # Root controller
├── app.controller.spec.ts # Root controller tests
├── app.service.ts         # Root service
├── main.ts                # Entry point — bootstraps the app
test/
├── app.e2e-spec.ts        # E2E test
└── jest-e2e.json          # E2E Jest config
nest-cli.json              # NestJS CLI configuration
```

### main.ts — Application Bootstrap

```typescript
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  // Global prefix for all routes
  app.setGlobalPrefix('api');

  // Enable CORS
  app.enableCors();

  // Enable shutdown hooks for graceful shutdown
  app.enableShutdownHooks();

  await app.listen(3000);
}
bootstrap();
```

## Platform Selection: Express vs Fastify

NestJS is platform-agnostic. Two HTTP platforms are supported out of the box:

| Aspect | Express (default) | Fastify |
|--------|-------------------|---------|
| **Package** | `@nestjs/platform-express` | `@nestjs/platform-fastify` |
| **Maturity** | Massive ecosystem, battle-tested | High-performance, schema-based |
| **Performance** | Good | ~2x throughput in benchmarks |
| **Middleware** | Express-compatible middleware | Fastify plugin ecosystem |
| **Community** | Largest Node.js middleware ecosystem | Growing fast |

### Switching to Fastify

```typescript
import { NestFactory } from '@nestjs/core';
import { FastifyAdapter, NestFastifyApplication } from '@nestjs/platform-fastify';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create<NestFastifyApplication>(
    AppModule,
    new FastifyAdapter(),
  );
  await app.listen(3000, '0.0.0.0');
}
bootstrap();
```

## Application Lifecycle

NestJS provides lifecycle hooks that execute at specific points:

| Hook | Interface | When |
|------|-----------|------|
| `onModuleInit()` | `OnModuleInit` | After the host module's dependencies are resolved |
| `onApplicationBootstrap()` | `OnApplicationBootstrap` | After all modules initialized, before listening |
| `onModuleDestroy()` | `OnModuleDestroy` | After receiving termination signal |
| `beforeApplicationShutdown()` | `BeforeApplicationShutdown` | After `onModuleDestroy()`, before connections closed |
| `onApplicationShutdown()` | `OnApplicationShutdown` | After connections closed |

```typescript
import { Injectable, OnModuleInit, OnModuleDestroy } from '@nestjs/common';

@Injectable()
export class DatabaseService implements OnModuleInit, OnModuleDestroy {
  async onModuleInit() {
    await this.connect();
  }

  async onModuleDestroy() {
    await this.disconnect();
  }
}
```

## CLI Commands

```bash
# Generate resources
nest generate module users        # nest g mo users
nest generate controller users    # nest g co users
nest generate service users       # nest g s users
nest generate resource users      # nest g res users (full CRUD)

# Build and run
nest build                        # Compile TypeScript
nest start                        # Start application
nest start --watch                # Watch mode
nest start --debug                # Debug mode

# Project info
nest info                         # Display Nest project details
```

### nest generate resource

The `resource` generator creates a complete CRUD module:

```bash
nest g resource users
# Creates:
#   users/users.module.ts
#   users/users.controller.ts
#   users/users.service.ts
#   users/dto/create-user.dto.ts
#   users/dto/update-user.dto.ts
#   users/entities/user.entity.ts
#   users/users.controller.spec.ts
#   users/users.service.spec.ts
```

## Monorepo Mode

For large projects with multiple applications sharing libraries:

```bash
# Convert to monorepo
nest generate app admin-api

# Generate a shared library
nest generate library common
```

Structure becomes:
```
apps/
├── my-api/          # Default app
└── admin-api/       # Second app
libs/
└── common/          # Shared library
nest-cli.json        # Multi-project config
```

```json
// nest-cli.json monorepo config
{
  "collection": "@nestjs/schematics",
  "monorepo": true,
  "root": "apps/my-api",
  "projects": {
    "my-api": { "type": "application", "root": "apps/my-api" },
    "admin-api": { "type": "application", "root": "apps/admin-api" },
    "common": { "type": "library", "root": "libs/common" }
  }
}
```

## Common Pitfalls

1. **Missing `reflect-metadata`** — must be imported in `main.ts` or included in tsconfig
2. **Circular dependencies** — use `forwardRef(() => Module)` to resolve
3. **Forgetting `@Injectable()`** — all providers must have this decorator
4. **Not registering providers in a module** — providers only work when added to a module's `providers` array
5. **Express vs Fastify incompatibilities** — some Express middleware won't work with Fastify
6. **Shutdown hooks** — call `app.enableShutdownHooks()` for graceful shutdown in production
7. **Global prefix doesn't apply to Swagger** — set up Swagger path separately
8. **`emitDecoratorMetadata` disabled** — DI won't work without this TypeScript compiler option
