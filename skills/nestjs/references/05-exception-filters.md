# NestJS — Exception Filters & Error Handling

> Source: [docs.nestjs.com/exception-filters](https://docs.nestjs.com/exception-filters) | @nestjs/core 11.x

## Table of Contents

- [Built-in Exceptions](#built-in-exceptions)
- [Throwing Exceptions](#throwing-exceptions)
- [Custom Exceptions](#custom-exceptions)
- [Exception Filters](#exception-filters)
- [Global Exception Filter](#global-exception-filter)
- [Catch-All Filter](#catch-all-filter)
- [Validation Error Handling](#validation-error-handling)
- [IntrinsicException (v11)](#intrinsicexception-v11)
- [Error Response Formatting](#error-response-formatting)
- [Common Pitfalls](#common-pitfalls)

## Built-in Exceptions

NestJS provides built-in HTTP exception classes that produce standard error responses:

| Exception | Status | When to Use |
|-----------|--------|-------------|
| `BadRequestException` | 400 | Invalid input, validation failure |
| `UnauthorizedException` | 401 | Missing or invalid authentication |
| `ForbiddenException` | 403 | Authenticated but insufficient permissions |
| `NotFoundException` | 404 | Resource not found |
| `MethodNotAllowedException` | 405 | HTTP method not supported |
| `NotAcceptableException` | 406 | Content type not acceptable |
| `RequestTimeoutException` | 408 | Request took too long |
| `ConflictException` | 409 | Resource conflict (e.g., duplicate email) |
| `GoneException` | 410 | Resource no longer available |
| `PayloadTooLargeException` | 413 | Request body too large |
| `UnsupportedMediaTypeException` | 415 | Content-Type not supported |
| `UnprocessableEntityException` | 422 | Semantically invalid input |
| `InternalServerErrorException` | 500 | Unexpected server error |
| `NotImplementedException` | 501 | Feature not implemented |
| `BadGatewayException` | 502 | Upstream service error |
| `ServiceUnavailableException` | 503 | Service temporarily unavailable |
| `GatewayTimeoutException` | 504 | Upstream service timeout |

All extend `HttpException`.

## Throwing Exceptions

```typescript
import { NotFoundException, ConflictException } from '@nestjs/common';

@Injectable()
export class UsersService {
  async findOne(id: number): Promise<User> {
    const user = await this.usersRepo.findOneBy({ id });
    if (!user) {
      throw new NotFoundException(`User #${id} not found`);
    }
    return user;
  }

  async create(dto: CreateUserDto): Promise<User> {
    const existing = await this.usersRepo.findOneBy({ email: dto.email });
    if (existing) {
      throw new ConflictException('Email already registered');
    }
    return this.usersRepo.save(dto);
  }
}
```

### Custom Error Response Body

```typescript
throw new BadRequestException({
  statusCode: 400,
  message: 'Validation failed',
  errors: [
    { field: 'email', message: 'Invalid email format' },
    { field: 'age', message: 'Must be at least 18' },
  ],
});
```

### Using HttpException Directly

```typescript
throw new HttpException('Custom error message', HttpStatus.FORBIDDEN);

throw new HttpException(
  {
    status: HttpStatus.FORBIDDEN,
    error: 'Access denied for this resource',
  },
  HttpStatus.FORBIDDEN,
);
```

## Custom Exceptions

Create domain-specific exceptions for better error categorization:

```typescript
export class UserNotFoundException extends NotFoundException {
  constructor(userId: number) {
    super(`User with ID ${userId} not found`);
  }
}

export class DuplicateEmailException extends ConflictException {
  constructor(email: string) {
    super(`Account with email ${email} already exists`);
  }
}

export class InsufficientBalanceException extends BadRequestException {
  constructor(required: number, available: number) {
    super({
      message: 'Insufficient balance',
      required,
      available,
    });
  }
}
```

### Non-HTTP Exception

```typescript
export class BusinessRuleViolation extends Error {
  constructor(
    public readonly rule: string,
    public readonly details: Record<string, any>,
  ) {
    super(`Business rule violation: ${rule}`);
  }
}
```

## Exception Filters

Exception filters catch exceptions thrown during request processing and control the error response.

### Basic Exception Filter

```typescript
import {
  ExceptionFilter, Catch, ArgumentsHost, HttpException, HttpStatus,
} from '@nestjs/common';
import { Request, Response } from 'express';

@Catch(HttpException)
export class HttpExceptionFilter implements ExceptionFilter {
  catch(exception: HttpException, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();
    const status = exception.getStatus();

    response.status(status).json({
      statusCode: status,
      message: exception.message,
      path: request.url,
      timestamp: new Date().toISOString(),
    });
  }
}
```

### Applying Filters

```typescript
// Method level
@Get(':id')
@UseFilters(HttpExceptionFilter)
findOne(@Param('id') id: string) {}

// Controller level
@Controller('users')
@UseFilters(HttpExceptionFilter)
export class UsersController {}

// Global level (main.ts)
app.useGlobalFilters(new HttpExceptionFilter());

// Global level (module-based, supports DI)
@Module({
  providers: [
    { provide: APP_FILTER, useClass: HttpExceptionFilter },
  ],
})
export class AppModule {}
```

## Global Exception Filter

A catch-all filter that handles all unhandled exceptions:

```typescript
@Catch()
export class AllExceptionsFilter implements ExceptionFilter {
  constructor(private readonly logger: LoggerService) {}

  catch(exception: unknown, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();

    let status = HttpStatus.INTERNAL_SERVER_ERROR;
    let message = 'Internal server error';

    if (exception instanceof HttpException) {
      status = exception.getStatus();
      const exceptionResponse = exception.getResponse();
      message = typeof exceptionResponse === 'string'
        ? exceptionResponse
        : (exceptionResponse as any).message || message;
    }

    this.logger.error(
      `${request.method} ${request.url} ${status}`,
      exception instanceof Error ? exception.stack : String(exception),
    );

    response.status(status).json({
      statusCode: status,
      message,
      path: request.url,
      timestamp: new Date().toISOString(),
    });
  }
}
```

## Catch-All Filter

Catch specific exception types using multiple `@Catch()` arguments:

```typescript
@Catch(BusinessRuleViolation)
export class BusinessExceptionFilter implements ExceptionFilter {
  catch(exception: BusinessRuleViolation, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();

    response.status(422).json({
      statusCode: 422,
      error: 'Business Rule Violation',
      rule: exception.rule,
      details: exception.details,
    });
  }
}

@Catch(TypeError, RangeError)
export class JavaScriptErrorFilter implements ExceptionFilter {
  catch(exception: TypeError | RangeError, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();

    response.status(500).json({
      statusCode: 500,
      error: exception.constructor.name,
      message: 'An unexpected error occurred',
    });
  }
}
```

## Validation Error Handling

### Default ValidationPipe Behavior

With `ValidationPipe`, class-validator errors are automatically caught and returned as 400 responses:

```json
{
  "statusCode": 400,
  "message": ["email must be an email", "name should not be empty"],
  "error": "Bad Request"
}
```

### Custom Validation Error Format

```typescript
app.useGlobalPipes(new ValidationPipe({
  whitelist: true,
  transform: true,
  exceptionFactory: (errors) => {
    const formattedErrors = errors.map(err => ({
      field: err.property,
      constraints: Object.values(err.constraints || {}),
      value: err.value,
    }));
    return new UnprocessableEntityException({
      message: 'Validation failed',
      errors: formattedErrors,
    });
  },
}));
```

## IntrinsicException (v11)

NestJS 11 introduces `IntrinsicException` for exceptions that bypass the framework's automatic logging:

```typescript
import { IntrinsicException } from '@nestjs/common';

export class SilentRedirectException extends IntrinsicException {
  constructor(public readonly url: string) {
    super();
  }
}
```

This is useful for flow control exceptions (redirects, SSE disconnects) that shouldn't pollute error logs.

## Error Response Formatting

### Consistent Error Envelope

```typescript
interface ErrorResponse {
  statusCode: number;
  message: string;
  error: string;
  details?: any;
  path: string;
  timestamp: string;
  requestId?: string;
}

@Catch()
export class GlobalExceptionFilter implements ExceptionFilter {
  catch(exception: unknown, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();

    const status = exception instanceof HttpException
      ? exception.getStatus()
      : HttpStatus.INTERNAL_SERVER_ERROR;

    const errorResponse: ErrorResponse = {
      statusCode: status,
      message: this.getMessage(exception),
      error: HttpStatus[status],
      path: request.url,
      timestamp: new Date().toISOString(),
      requestId: request.headers['x-request-id'] as string,
    };

    response.status(status).json(errorResponse);
  }

  private getMessage(exception: unknown): string {
    if (exception instanceof HttpException) {
      const response = exception.getResponse();
      return typeof response === 'string' ? response : (response as any).message;
    }
    return 'Internal server error';
  }
}
```

## Common Pitfalls

1. **Unhandled promise rejections** — NestJS catches sync and async errors from controllers/services, but not from event handlers or setTimeout callbacks
2. **Order of filters** — the closest filter to the route handler is evaluated first; global filters are last resort
3. **Filters don't catch middleware errors** — middleware errors bypass NestJS filters; handle them in the middleware itself
4. **`@Catch()` with no args catches everything** — including non-HTTP errors; always log the original error
5. **ValidationPipe errors are `BadRequestException`** — customize with `exceptionFactory` for different status codes
6. **Don't expose stack traces in production** — never send `exception.stack` to the client
