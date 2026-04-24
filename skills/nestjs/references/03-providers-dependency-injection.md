# NestJS — Providers & Dependency Injection

> Source: [docs.nestjs.com/providers](https://docs.nestjs.com/providers) | @nestjs/core 11.x

## Table of Contents

- [Provider Basics](#provider-basics)
- [Injectable Services](#injectable-services)
- [Constructor Injection](#constructor-injection)
- [Custom Providers](#custom-providers)
- [Provider Tokens](#provider-tokens)
- [Injection Scopes](#injection-scopes)
- [Optional Dependencies](#optional-dependencies)
- [Circular Dependencies](#circular-dependencies)
- [Property-Based Injection](#property-based-injection)
- [Async Providers](#async-providers)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## Provider Basics

Providers are the core building blocks of NestJS. Services, repositories, factories, helpers — any class that can be injected as a dependency is a provider. Providers are registered in a module's `providers` array and managed by the IoC container.

The key idea: classes can declare dependencies in their constructor, and the NestJS runtime resolves and injects them automatically.

## Injectable Services

```typescript
import { Injectable } from '@nestjs/common';

@Injectable()
export class UsersService {
  private readonly users: User[] = [];

  findAll(): User[] {
    return this.users;
  }

  findOne(id: number): User | undefined {
    return this.users.find(user => user.id === id);
  }

  create(dto: CreateUserDto): User {
    const user = { id: Date.now(), ...dto };
    this.users.push(user);
    return user;
  }
}
```

## Constructor Injection

The most common pattern — declare dependencies in the constructor:

```typescript
@Controller('users')
export class UsersController {
  constructor(private readonly usersService: UsersService) {}

  @Get()
  findAll() {
    return this.usersService.findAll();
  }
}
```

NestJS resolves `UsersService` from the IoC container using TypeScript's type metadata (enabled by `emitDecoratorMetadata`).

### Multiple Dependencies

```typescript
@Injectable()
export class OrdersService {
  constructor(
    private readonly usersService: UsersService,
    private readonly productsService: ProductsService,
    private readonly emailService: EmailService,
  ) {}
}
```

## Custom Providers

Beyond the standard class provider, NestJS supports several provider types:

### Value Providers (`useValue`)

```typescript
const CONFIG = {
  apiKey: 'abc123',
  maxRetries: 3,
};

@Module({
  providers: [
    {
      provide: 'APP_CONFIG',
      useValue: CONFIG,
    },
  ],
})
export class AppModule {}

// Inject with @Inject()
@Injectable()
export class ApiService {
  constructor(@Inject('APP_CONFIG') private config: typeof CONFIG) {}
}
```

### Factory Providers (`useFactory`)

```typescript
@Module({
  providers: [
    {
      provide: 'DATABASE_CONNECTION',
      useFactory: async (config: ConfigService) => {
        const connection = await createConnection({
          host: config.get('DB_HOST'),
          port: config.get<number>('DB_PORT'),
        });
        return connection;
      },
      inject: [ConfigService],
    },
  ],
})
export class DatabaseModule {}
```

### Class Providers (`useClass`)

```typescript
@Module({
  providers: [
    {
      provide: LoggerService,
      useClass:
        process.env.NODE_ENV === 'production'
          ? ProductionLoggerService
          : DevelopmentLoggerService,
    },
  ],
})
export class AppModule {}
```

### Existing Providers (`useExisting`)

Create an alias to an existing provider:

```typescript
@Module({
  providers: [
    UsersService,
    {
      provide: 'AliasedUsersService',
      useExisting: UsersService,
    },
  ],
})
export class UsersModule {}
```

## Provider Tokens

Tokens identify providers in the IoC container:

### String Tokens

```typescript
{ provide: 'API_KEY', useValue: 'secret' }

// Inject
constructor(@Inject('API_KEY') private apiKey: string) {}
```

### Symbol Tokens

```typescript
const CONNECTION = Symbol('CONNECTION');
{ provide: CONNECTION, useFactory: () => new DbConnection() }

constructor(@Inject(CONNECTION) private conn: DbConnection) {}
```

### Class Tokens (default)

```typescript
providers: [UsersService]
// Equivalent to:
providers: [{ provide: UsersService, useClass: UsersService }]

// Inject via type
constructor(private usersService: UsersService) {}
```

### InjectionToken

```typescript
import { InjectionToken } from '@nestjs/common';

interface DatabaseConfig {
  host: string;
  port: number;
}

const DATABASE_CONFIG = new InjectionToken<DatabaseConfig>('DATABASE_CONFIG');

{ provide: DATABASE_CONFIG, useValue: { host: 'localhost', port: 5432 } }
```

## Injection Scopes

By default, providers are singleton (shared across the entire application). NestJS supports three scopes:

| Scope | Lifetime | Use Case |
|-------|----------|----------|
| `DEFAULT` | Singleton — one instance for entire app | Most services |
| `REQUEST` | New instance per request | Request-specific state (e.g., tenant context) |
| `TRANSIENT` | New instance each time it's injected | Stateful per-consumer services |

```typescript
@Injectable({ scope: Scope.REQUEST })
export class RequestContextService {
  constructor(@Inject(REQUEST) private request: Request) {}

  getTenantId(): string {
    return this.request.headers['x-tenant-id'] as string;
  }
}
```

```typescript
@Injectable({ scope: Scope.TRANSIENT })
export class LoggerService {
  private context: string;

  setContext(context: string) {
    this.context = context;
  }

  log(message: string) {
    console.log(`[${this.context}] ${message}`);
  }
}
```

**Performance note:** REQUEST-scoped providers bubble up — any provider that depends on a REQUEST-scoped provider also becomes request-scoped. Use sparingly.

## Optional Dependencies

```typescript
import { Optional, Inject } from '@nestjs/common';

@Injectable()
export class HttpService {
  constructor(
    @Optional() @Inject('HTTP_OPTIONS') private options?: HttpModuleOptions,
  ) {
    this.options = options || { timeout: 5000 };
  }
}
```

## Circular Dependencies

When two providers depend on each other, use `forwardRef`:

```typescript
// users.service.ts
@Injectable()
export class UsersService {
  constructor(
    @Inject(forwardRef(() => OrdersService))
    private ordersService: OrdersService,
  ) {}
}

// orders.service.ts
@Injectable()
export class OrdersService {
  constructor(
    @Inject(forwardRef(() => UsersService))
    private usersService: UsersService,
  ) {}
}
```

For circular module imports:
```typescript
@Module({
  imports: [forwardRef(() => OrdersModule)],
})
export class UsersModule {}
```

**Best practice:** Circular dependencies are usually a design smell. Consider extracting shared logic into a third service.

## Property-Based Injection

Use when constructor injection isn't possible (e.g., base classes):

```typescript
@Injectable()
export class BaseService {
  @Inject(ConfigService)
  protected config: ConfigService;
}
```

## Async Providers

For providers that need async initialization:

```typescript
{
  provide: 'ASYNC_CONNECTION',
  useFactory: async () => {
    const connection = await createConnection(options);
    await connection.runMigrations();
    return connection;
  },
}
```

NestJS waits for the async factory to resolve before making the provider available.

## Common Patterns

### Repository Pattern

```typescript
@Injectable()
export class UsersRepository {
  constructor(
    @InjectRepository(User)
    private readonly repo: Repository<User>,
  ) {}

  async findById(id: number): Promise<User | null> {
    return this.repo.findOneBy({ id });
  }

  async save(user: Partial<User>): Promise<User> {
    return this.repo.save(user);
  }
}
```

### Strategy Pattern

```typescript
interface PaymentStrategy {
  pay(amount: number): Promise<PaymentResult>;
}

@Injectable()
export class StripePayment implements PaymentStrategy {
  async pay(amount: number) { /* ... */ }
}

@Injectable()
export class PayPalPayment implements PaymentStrategy {
  async pay(amount: number) { /* ... */ }
}

@Injectable()
export class PaymentService {
  constructor(
    @Inject('PAYMENT_STRATEGIES')
    private strategies: Map<string, PaymentStrategy>,
  ) {}

  async processPayment(method: string, amount: number) {
    const strategy = this.strategies.get(method);
    if (!strategy) throw new BadRequestException(`Unknown method: ${method}`);
    return strategy.pay(amount);
  }
}
```

### Multi-Provider (inject an array)

```typescript
const VALIDATORS = Symbol('VALIDATORS');

@Module({
  providers: [
    EmailValidator,
    PhoneValidator,
    {
      provide: VALIDATORS,
      useFactory: (email: EmailValidator, phone: PhoneValidator) => [email, phone],
      inject: [EmailValidator, PhoneValidator],
    },
  ],
})
export class ValidationModule {}
```

## Common Pitfalls

1. **Missing `@Injectable()`** — class won't be recognized as a provider
2. **Not adding to module `providers`** — injectable class must be registered in a module
3. **Using interface as token** — interfaces are erased at runtime; use string/Symbol tokens or abstract classes
4. **REQUEST scope bubbles up** — all dependents become request-scoped, hurting performance
5. **Circular deps without `forwardRef`** — causes "cannot resolve dependency" error
6. **Factory `inject` order must match params** — factory parameters must align with the `inject` array order
