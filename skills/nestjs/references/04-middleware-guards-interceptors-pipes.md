# NestJS — Middleware, Guards, Interceptors & Pipes

> Source: [docs.nestjs.com/middleware](https://docs.nestjs.com/middleware) | @nestjs/core 11.x

## Table of Contents

- [Request Pipeline Overview](#request-pipeline-overview)
- [Middleware](#middleware)
- [Guards](#guards)
- [Interceptors](#interceptors)
- [Pipes](#pipes)
- [Execution Order](#execution-order)
- [Binding Levels](#binding-levels)
- [Common Pitfalls](#common-pitfalls)

## Request Pipeline Overview

NestJS processes requests through a specific pipeline:

```
Client Request
  → Middleware
    → Guards
      → Interceptors (before)
        → Pipes
          → Route Handler
        → Interceptors (after)
      → Exception Filters (on error)
  → Response
```

Each layer has a specific responsibility and can short-circuit the pipeline.

## Middleware

Middleware functions execute before the route handler. They have access to `request`, `response`, and `next`. Identical to Express middleware.

### Class Middleware

```typescript
import { Injectable, NestMiddleware } from '@nestjs/common';
import { Request, Response, NextFunction } from 'express';

@Injectable()
export class LoggerMiddleware implements NestMiddleware {
  use(req: Request, res: Response, next: NextFunction) {
    const start = Date.now();
    res.on('finish', () => {
      const duration = Date.now() - start;
      console.log(`${req.method} ${req.url} ${res.statusCode} ${duration}ms`);
    });
    next();
  }
}
```

### Functional Middleware

```typescript
export function corsMiddleware(req: Request, res: Response, next: NextFunction) {
  res.header('Access-Control-Allow-Origin', '*');
  next();
}
```

### Applying Middleware

```typescript
import { MiddlewareConsumer, Module, NestModule, RequestMethod } from '@nestjs/common';

@Module({
  controllers: [UsersController, OrdersController],
})
export class AppModule implements NestModule {
  configure(consumer: MiddlewareConsumer) {
    consumer
      .apply(LoggerMiddleware)
      .forRoutes('*');  // All routes

    consumer
      .apply(AuthMiddleware)
      .exclude(
        { path: 'auth/login', method: RequestMethod.POST },
        { path: 'auth/register', method: RequestMethod.POST },
      )
      .forRoutes(UsersController, OrdersController);
  }
}
```

### Global Middleware

```typescript
// main.ts
const app = await NestFactory.create(AppModule);
app.use(helmet());
app.use(compression());
```

## Guards

Guards determine whether a request will be handled by the route handler. They implement the `CanActivate` interface and are the primary mechanism for authentication and authorization.

### Basic Guard

```typescript
import { Injectable, CanActivate, ExecutionContext } from '@nestjs/common';

@Injectable()
export class AuthGuard implements CanActivate {
  constructor(private authService: AuthService) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const request = context.switchToHttp().getRequest();
    const token = this.extractToken(request);
    if (!token) return false;

    try {
      const payload = await this.authService.verifyToken(token);
      request.user = payload;
      return true;
    } catch {
      return false;
    }
  }

  private extractToken(request: Request): string | undefined {
    const [type, token] = request.headers.authorization?.split(' ') ?? [];
    return type === 'Bearer' ? token : undefined;
  }
}
```

### Role-Based Guard with Custom Decorator

```typescript
// roles.decorator.ts
import { SetMetadata } from '@nestjs/common';
export const ROLES_KEY = 'roles';
export const Roles = (...roles: string[]) => SetMetadata(ROLES_KEY, roles);

// roles.guard.ts
@Injectable()
export class RolesGuard implements CanActivate {
  constructor(private reflector: Reflector) {}

  canActivate(context: ExecutionContext): boolean {
    const requiredRoles = this.reflector.getAllAndOverride<string[]>(ROLES_KEY, [
      context.getHandler(),
      context.getClass(),
    ]);
    if (!requiredRoles) return true;

    const { user } = context.switchToHttp().getRequest();
    return requiredRoles.some(role => user.roles?.includes(role));
  }
}

// Usage
@Controller('admin')
@UseGuards(AuthGuard, RolesGuard)
export class AdminController {
  @Get('dashboard')
  @Roles('admin')
  getDashboard() {
    return 'Admin dashboard';
  }
}
```

### ExecutionContext

`ExecutionContext` extends `ArgumentsHost` and provides metadata about the current execution:

```typescript
const ctx = context.switchToHttp();
const request = ctx.getRequest<Request>();
const response = ctx.getResponse<Response>();

// For WebSockets
const wsCtx = context.switchToWs();
const client = wsCtx.getClient();
const data = wsCtx.getData();

// For GraphQL
const gqlCtx = GqlExecutionContext.create(context);
const args = gqlCtx.getArgs();

// Handler and class metadata
const handler = context.getHandler();  // Route handler method
const controller = context.getClass(); // Controller class
```

## Interceptors

Interceptors sit between the client and the route handler. They can transform the result, extend behavior, override functions, or handle errors — using RxJS observables.

### Response Transformation

```typescript
import { CallHandler, ExecutionContext, Injectable, NestInterceptor } from '@nestjs/common';
import { Observable, map } from 'rxjs';

@Injectable()
export class TransformInterceptor<T> implements NestInterceptor<T, { data: T }> {
  intercept(context: ExecutionContext, next: CallHandler): Observable<{ data: T }> {
    return next.handle().pipe(
      map(data => ({ data, timestamp: new Date().toISOString() })),
    );
  }
}
// Response: { data: {...}, timestamp: "2026-..." }
```

### Logging Interceptor

```typescript
@Injectable()
export class LoggingInterceptor implements NestInterceptor {
  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const now = Date.now();
    const req = context.switchToHttp().getRequest();

    return next.handle().pipe(
      tap(() => {
        console.log(`${req.method} ${req.url} — ${Date.now() - now}ms`);
      }),
    );
  }
}
```

### Cache Interceptor

```typescript
@Injectable()
export class CacheInterceptor implements NestInterceptor {
  private cache = new Map<string, { data: any; expiry: number }>();

  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const req = context.switchToHttp().getRequest();
    const key = req.url;
    const cached = this.cache.get(key);

    if (cached && cached.expiry > Date.now()) {
      return of(cached.data);
    }

    return next.handle().pipe(
      tap(data => {
        this.cache.set(key, { data, expiry: Date.now() + 60_000 });
      }),
    );
  }
}
```

### Timeout Interceptor

```typescript
@Injectable()
export class TimeoutInterceptor implements NestInterceptor {
  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    return next.handle().pipe(
      timeout(5000),
      catchError(err => {
        if (err instanceof TimeoutError) {
          throw new RequestTimeoutException();
        }
        throw err;
      }),
    );
  }
}
```

## Pipes

Pipes transform and validate input data. They run before the route handler receives the arguments.

### Built-in Pipes

| Pipe | Purpose |
|------|---------|
| `ValidationPipe` | Validate DTOs with class-validator |
| `ParseIntPipe` | Parse string → integer |
| `ParseFloatPipe` | Parse string → float |
| `ParseBoolPipe` | Parse string → boolean |
| `ParseUUIDPipe` | Validate UUID format |
| `ParseArrayPipe` | Parse and validate arrays |
| `ParseEnumPipe` | Validate enum values |
| `DefaultValuePipe` | Provide default when value is undefined |

### Using Built-in Pipes

```typescript
@Get(':id')
findOne(@Param('id', ParseIntPipe) id: number) {}

@Get()
findAll(
  @Query('page', new DefaultValuePipe(1), ParseIntPipe) page: number,
  @Query('active', new DefaultValuePipe(true), ParseBoolPipe) active: boolean,
) {}

@Get(':status')
findByStatus(@Param('status', new ParseEnumPipe(UserStatus)) status: UserStatus) {}
```

### Custom Pipe

```typescript
import { PipeTransform, Injectable, BadRequestException } from '@nestjs/common';

@Injectable()
export class ParseDatePipe implements PipeTransform<string, Date> {
  transform(value: string): Date {
    const date = new Date(value);
    if (isNaN(date.getTime())) {
      throw new BadRequestException(`"${value}" is not a valid date`);
    }
    return date;
  }
}

@Get()
findByDate(@Query('from', ParseDatePipe) from: Date) {}
```

### Global ValidationPipe

```typescript
// main.ts
app.useGlobalPipes(new ValidationPipe({
  whitelist: true,
  forbidNonWhitelisted: true,
  transform: true,
  transformOptions: {
    enableImplicitConversion: true,
  },
}));
```

## Execution Order

When multiple layers are applied, the exact execution order is:

1. **Global middleware** → module middleware
2. **Global guards** → controller guards → route guards
3. **Global interceptors** → controller interceptors → route interceptors (before handler)
4. **Global pipes** → controller pipes → route pipes → route parameter pipes
5. **Route handler**
6. **Interceptors** (after handler, in reverse order)
7. **Exception filters** (on error, closest filter first)

## Binding Levels

Each component can be bound at multiple levels:

### Method Level

```typescript
@Get()
@UseGuards(AuthGuard)
@UseInterceptors(LoggingInterceptor)
@UsePipes(ValidationPipe)
findAll() {}
```

### Controller Level

```typescript
@Controller('users')
@UseGuards(AuthGuard)
@UseInterceptors(LoggingInterceptor)
export class UsersController {}
```

### Global Level (main.ts)

```typescript
app.useGlobalGuards(new AuthGuard());
app.useGlobalInterceptors(new LoggingInterceptor());
app.useGlobalPipes(new ValidationPipe());
app.useGlobalFilters(new HttpExceptionFilter());
```

### Global Level (module-based — supports DI)

```typescript
import { APP_GUARD, APP_INTERCEPTOR, APP_PIPE, APP_FILTER } from '@nestjs/core';

@Module({
  providers: [
    { provide: APP_GUARD, useClass: AuthGuard },
    { provide: APP_INTERCEPTOR, useClass: LoggingInterceptor },
    { provide: APP_PIPE, useClass: ValidationPipe },
    { provide: APP_FILTER, useClass: HttpExceptionFilter },
  ],
})
export class AppModule {}
```

## Common Pitfalls

1. **Middleware can't access route metadata** — use guards for role/permission checks that need `@SetMetadata()`
2. **Guard returning `false` throws `ForbiddenException`** — throw a custom exception for specific error messages
3. **Interceptors use RxJS** — must return an `Observable`, not a plain value
4. **Global components from `main.ts` can't inject dependencies** — use the module-based `APP_GUARD`/`APP_PIPE` pattern instead
5. **Multiple guards are AND logic** — all must return `true`; first `false` rejects the request
6. **Pipe errors bypass interceptors** — validation failures skip the "after" interceptor phase
