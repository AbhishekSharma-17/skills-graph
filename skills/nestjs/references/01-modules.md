# NestJS — Modules

> Source: [docs.nestjs.com/modules](https://docs.nestjs.com/modules) | @nestjs/core 11.x

## Table of Contents

- [Module Basics](#module-basics)
- [The @Module Decorator](#the-module-decorator)
- [Feature Modules](#feature-modules)
- [Shared Modules](#shared-modules)
- [Global Modules](#global-modules)
- [Dynamic Modules](#dynamic-modules)
- [Lazy-Loaded Modules](#lazy-loaded-modules)
- [Module Reference](#module-reference)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## Module Basics

Modules are the fundamental organizational unit in NestJS. Every application has at least one module — the root module (`AppModule`). Modules encapsulate providers (services), controllers, and imports from other modules.

```typescript
import { Module } from '@nestjs/common';
import { UsersController } from './users.controller';
import { UsersService } from './users.service';

@Module({
  controllers: [UsersController],
  providers: [UsersService],
  exports: [UsersService],
})
export class UsersModule {}
```

## The @Module Decorator

The `@Module()` decorator takes a single metadata object with these properties:

| Property | Purpose |
|----------|---------|
| `imports` | List of modules whose exported providers are needed in this module |
| `controllers` | Controllers that belong to this module |
| `providers` | Providers (services, repositories, factories) available via DI within this module |
| `exports` | Subset of `providers` that should be available to other modules importing this one |

```typescript
@Module({
  imports: [DatabaseModule, AuthModule],
  controllers: [UsersController, ProfileController],
  providers: [UsersService, UsersRepository],
  exports: [UsersService],
})
export class UsersModule {}
```

### Import Flow

```
AppModule
├── imports: [UsersModule, AuthModule, DatabaseModule]
│
UsersModule
├── imports: [DatabaseModule]      ← Can use DatabaseModule exports
├── providers: [UsersService]
├── exports: [UsersService]        ← Available to AppModule and siblings
│
AuthModule
├── imports: [UsersModule]         ← Can use UsersService
├── providers: [AuthService]
```

## Feature Modules

Feature modules group related functionality. Use `nest generate module` to scaffold:

```bash
nest g module users
nest g module orders
nest g module products
```

### Typical Feature Module Layout

```
users/
├── users.module.ts
├── users.controller.ts
├── users.service.ts
├── users.repository.ts
├── dto/
│   ├── create-user.dto.ts
│   └── update-user.dto.ts
├── entities/
│   └── user.entity.ts
├── interfaces/
│   └── user.interface.ts
└── guards/
    └── user-owner.guard.ts
```

### Register in AppModule

```typescript
@Module({
  imports: [
    UsersModule,
    OrdersModule,
    ProductsModule,
    DatabaseModule,
    AuthModule,
  ],
})
export class AppModule {}
```

## Shared Modules

Every module is a shared module by default. Once created, it can be reused by any module that imports it. When you export a provider, any module importing yours can use it.

```typescript
@Module({
  providers: [EmailService],
  exports: [EmailService],
})
export class EmailModule {}

@Module({
  imports: [EmailModule],
  providers: [UsersService],   // UsersService can inject EmailService
})
export class UsersModule {}

@Module({
  imports: [EmailModule],
  providers: [OrdersService],  // OrdersService can also inject EmailService
})
export class OrdersModule {}
```

### Re-exporting Modules

A module can re-export modules it imports:

```typescript
@Module({
  imports: [CommonModule],
  exports: [CommonModule],    // Re-export so importers get CommonModule too
})
export class CoreModule {}
```

## Global Modules

Use `@Global()` to make a module available everywhere without importing:

```typescript
import { Global, Module } from '@nestjs/common';

@Global()
@Module({
  providers: [ConfigService, LoggerService],
  exports: [ConfigService, LoggerService],
})
export class CoreModule {}
```

Register the global module once in `AppModule`:
```typescript
@Module({
  imports: [CoreModule],  // Register once, available everywhere
})
export class AppModule {}
```

**Use sparingly** — global modules reduce explicitness. Best for cross-cutting concerns like config, logging, or database connections.

## Dynamic Modules

Dynamic modules allow configuring a module at import time. Essential for modules that need configuration (database connections, API keys, etc.).

### Creating a Dynamic Module

```typescript
import { DynamicModule, Module } from '@nestjs/common';

@Module({})
export class DatabaseModule {
  static forRoot(options: DatabaseOptions): DynamicModule {
    return {
      module: DatabaseModule,
      global: true,
      providers: [
        {
          provide: 'DATABASE_OPTIONS',
          useValue: options,
        },
        DatabaseService,
      ],
      exports: [DatabaseService],
    };
  }

  static forFeature(entities: any[]): DynamicModule {
    const providers = entities.map(entity => ({
      provide: `${entity.name}_REPOSITORY`,
      useFactory: (db: DatabaseService) => db.getRepository(entity),
      inject: [DatabaseService],
    }));

    return {
      module: DatabaseModule,
      providers,
      exports: providers,
    };
  }
}
```

### Using Dynamic Modules

```typescript
// Root module — configure once
@Module({
  imports: [
    DatabaseModule.forRoot({
      host: 'localhost',
      port: 5432,
      database: 'mydb',
    }),
  ],
})
export class AppModule {}

// Feature module — register entities
@Module({
  imports: [DatabaseModule.forFeature([User, Order])],
})
export class UsersModule {}
```

### Async Dynamic Modules

```typescript
@Module({})
export class DatabaseModule {
  static forRootAsync(options: {
    imports?: any[];
    useFactory: (...args: any[]) => Promise<DatabaseOptions> | DatabaseOptions;
    inject?: any[];
  }): DynamicModule {
    return {
      module: DatabaseModule,
      global: true,
      imports: options.imports || [],
      providers: [
        {
          provide: 'DATABASE_OPTIONS',
          useFactory: options.useFactory,
          inject: options.inject || [],
        },
        DatabaseService,
      ],
      exports: [DatabaseService],
    };
  }
}

// Usage with ConfigService
@Module({
  imports: [
    DatabaseModule.forRootAsync({
      imports: [ConfigModule],
      useFactory: (config: ConfigService) => ({
        host: config.get('DB_HOST'),
        port: config.get('DB_PORT'),
      }),
      inject: [ConfigService],
    }),
  ],
})
export class AppModule {}
```

## Lazy-Loaded Modules

Lazy loading defers module initialization until needed, reducing startup time:

```typescript
import { Injectable } from '@nestjs/common';
import { LazyModuleLoader } from '@nestjs/core';

@Injectable()
export class ReportService {
  constructor(private lazyModuleLoader: LazyModuleLoader) {}

  async generateReport() {
    const { ReportModule } = await import('./report.module');
    const moduleRef = await this.lazyModuleLoader.load(() => ReportModule);
    const reportGenerator = moduleRef.get(ReportGeneratorService);
    return reportGenerator.create();
  }
}
```

**Limitations:** Lazy-loaded modules cannot register controllers, resolvers, or gateways — only providers.

## Module Reference

`ModuleRef` lets you retrieve providers dynamically at runtime:

```typescript
import { Injectable, OnModuleInit } from '@nestjs/common';
import { ModuleRef } from '@nestjs/core';

@Injectable()
export class TaskRunner implements OnModuleInit {
  private service: UsersService;

  constructor(private moduleRef: ModuleRef) {}

  onModuleInit() {
    this.service = this.moduleRef.get(UsersService);
  }

  async runForTransient() {
    const scoped = await this.moduleRef.resolve(TransientService);
    return scoped.process();
  }
}
```

## Common Patterns

### Barrel Exports

```typescript
// shared/index.ts
export * from './shared.module';
export * from './services/logger.service';
export * from './guards/auth.guard';
```

### Module Composition

```typescript
@Module({
  imports: [
    ConfigModule.forRoot(),
    TypeOrmModule.forRootAsync({
      imports: [ConfigModule],
      useFactory: (config: ConfigService) => config.get('database'),
      inject: [ConfigService],
    }),
    AuthModule,
    UsersModule,
    OrdersModule,
  ],
})
export class AppModule {}
```

## Common Pitfalls

1. **Circular module imports** — use `forwardRef(() => OtherModule)` in both modules
2. **Not exporting providers** — if another module needs your service, add it to `exports`
3. **Overusing @Global()** — makes dependencies implicit; prefer explicit imports
4. **Dynamic module without `module` property** — the `module` key is required in the returned `DynamicModule`
5. **Lazy-loaded controllers** — controllers in lazy modules won't register routes
6. **Importing a module multiple times** — NestJS deduplicates, but dynamic modules with different configs create separate instances
