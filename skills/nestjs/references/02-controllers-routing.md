# NestJS — Controllers & Routing

> Source: [docs.nestjs.com/controllers](https://docs.nestjs.com/controllers) | @nestjs/core 11.x

## Table of Contents

- [Controller Basics](#controller-basics)
- [Route Decorators](#route-decorators)
- [Request Object](#request-object)
- [Route Parameters](#route-parameters)
- [Request Body & DTOs](#request-body--dtos)
- [Query Parameters](#query-parameters)
- [Headers & Status Codes](#headers--status-codes)
- [Redirects](#redirects)
- [Sub-Domain Routing](#sub-domain-routing)
- [Streaming & SSE](#streaming--sse)
- [File Upload](#file-upload)
- [Versioning](#versioning)
- [Common Pitfalls](#common-pitfalls)

## Controller Basics

Controllers handle incoming requests and return responses. Each controller is a class decorated with `@Controller()`, which takes an optional route path prefix.

```typescript
import { Controller, Get } from '@nestjs/common';

@Controller('users')
export class UsersController {
  @Get()
  findAll(): string {
    return 'All users';
  }
}
// GET /users → 'All users'
```

Register in a module:
```typescript
@Module({
  controllers: [UsersController],
  providers: [UsersService],
})
export class UsersModule {}
```

## Route Decorators

| Decorator | HTTP Method |
|-----------|------------|
| `@Get(path?)` | GET |
| `@Post(path?)` | POST |
| `@Put(path?)` | PUT |
| `@Patch(path?)` | PATCH |
| `@Delete(path?)` | DELETE |
| `@Options(path?)` | OPTIONS |
| `@Head(path?)` | HEAD |
| `@All(path?)` | All methods |

```typescript
@Controller('users')
export class UsersController {
  @Get()
  findAll() { /* GET /users */ }

  @Get(':id')
  findOne(@Param('id') id: string) { /* GET /users/:id */ }

  @Post()
  create(@Body() dto: CreateUserDto) { /* POST /users */ }

  @Put(':id')
  update(@Param('id') id: string, @Body() dto: UpdateUserDto) { /* PUT /users/:id */ }

  @Patch(':id')
  partialUpdate(@Param('id') id: string, @Body() dto: UpdateUserDto) { /* PATCH /users/:id */ }

  @Delete(':id')
  remove(@Param('id') id: string) { /* DELETE /users/:id */ }
}
```

### Route Wildcards

```typescript
@Get('ab*cd')
findAll() {
  // Matches abcd, ab_cd, abecd, etc.
}
```

## Request Object

Access the underlying request via parameter decorators:

| Decorator | Express Equivalent |
|-----------|-------------------|
| `@Request()` / `@Req()` | `req` |
| `@Response()` / `@Res()` | `res` |
| `@Next()` | `next` |
| `@Session()` | `req.session` |
| `@Param(key?)` | `req.params` / `req.params[key]` |
| `@Body(key?)` | `req.body` / `req.body[key]` |
| `@Query(key?)` | `req.query` / `req.query[key]` |
| `@Headers(name?)` | `req.headers` / `req.headers[name]` |
| `@Ip()` | `req.ip` |
| `@HostParam()` | `req.hosts` |

```typescript
@Get(':id')
findOne(
  @Param('id') id: string,
  @Query('include') include: string,
  @Headers('authorization') auth: string,
  @Ip() ip: string,
) {
  return { id, include, auth: !!auth, ip };
}
```

**Warning:** Using `@Res()` puts you in library-specific mode — you must call `res.json()` or `res.send()` manually. Prefer the `@Res({ passthrough: true })` option if you only need to set headers/cookies but want NestJS to handle the response.

## Route Parameters

```typescript
// Single param
@Get(':id')
findOne(@Param('id') id: string) {}

// Multiple params
@Get(':userId/posts/:postId')
findPost(
  @Param('userId') userId: string,
  @Param('postId') postId: string,
) {}

// All params as object
@Get(':id')
findOne(@Param() params: { id: string }) {}
```

### Pipe-Based Parsing

```typescript
import { ParseIntPipe, ParseUUIDPipe } from '@nestjs/common';

@Get(':id')
findOne(@Param('id', ParseIntPipe) id: number) {
  // id is guaranteed to be a valid integer
  // Throws 400 if invalid
}

@Get(':uuid')
findByUuid(@Param('uuid', ParseUUIDPipe) uuid: string) {}
```

## Request Body & DTOs

Data Transfer Objects define the shape of incoming data:

```typescript
// dto/create-user.dto.ts
import { IsEmail, IsString, MinLength, IsOptional } from 'class-validator';

export class CreateUserDto {
  @IsString()
  @MinLength(2)
  name: string;

  @IsEmail()
  email: string;

  @IsString()
  @MinLength(8)
  password: string;

  @IsOptional()
  @IsString()
  bio?: string;
}
```

```typescript
// Enable global validation pipe in main.ts
import { ValidationPipe } from '@nestjs/common';

app.useGlobalPipes(new ValidationPipe({
  whitelist: true,       // Strip properties not in DTO
  forbidNonWhitelisted: true,  // Throw on extra properties
  transform: true,       // Auto-transform to DTO class instance
}));
```

```typescript
@Post()
create(@Body() createUserDto: CreateUserDto) {
  return this.usersService.create(createUserDto);
}
```

### Partial DTOs for Updates

```typescript
import { PartialType } from '@nestjs/mapped-types';

export class UpdateUserDto extends PartialType(CreateUserDto) {}
// All fields from CreateUserDto become optional
```

Other mapped types: `PickType`, `OmitType`, `IntersectionType`.

## Query Parameters

```typescript
@Get()
findAll(
  @Query('page', new DefaultValuePipe(1), ParseIntPipe) page: number,
  @Query('limit', new DefaultValuePipe(10), ParseIntPipe) limit: number,
  @Query('search') search?: string,
) {
  return this.usersService.findAll({ page, limit, search });
}
// GET /users?page=2&limit=20&search=john
```

### Query DTO

```typescript
export class PaginationDto {
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  page?: number = 1;

  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  @Max(100)
  limit?: number = 10;
}

@Get()
findAll(@Query() pagination: PaginationDto) {
  return this.usersService.findAll(pagination);
}
```

## Headers & Status Codes

```typescript
import { HttpCode, Header } from '@nestjs/common';

@Post()
@HttpCode(201)
@Header('Cache-Control', 'none')
create(@Body() dto: CreateUserDto) {
  return this.usersService.create(dto);
}
```

### Custom Response Headers

```typescript
@Get()
findAll(@Res({ passthrough: true }) res: Response) {
  res.header('X-Total-Count', '100');
  return this.usersService.findAll();
}
```

## Redirects

```typescript
import { Redirect } from '@nestjs/common';

@Get('old-endpoint')
@Redirect('https://example.com/new', 301)
redirect() {}

// Dynamic redirect
@Get('docs')
@Redirect('https://docs.nestjs.com', 302)
getDocs(@Query('version') version: string) {
  if (version === '5') {
    return { url: 'https://docs.nestjs.com/v5/' };
  }
}
```

## Sub-Domain Routing

```typescript
@Controller({ host: 'admin.example.com' })
export class AdminController {
  @Get()
  index() {
    return 'Admin panel';
  }
}

@Controller({ host: ':account.example.com' })
export class AccountController {
  @Get()
  index(@HostParam('account') account: string) {
    return `Account: ${account}`;
  }
}
```

## Streaming & SSE

### Stream Response

```typescript
import { StreamableFile } from '@nestjs/common';
import { createReadStream } from 'fs';

@Get('file')
getFile(): StreamableFile {
  const file = createReadStream('./package.json');
  return new StreamableFile(file, {
    type: 'application/json',
    disposition: 'attachment; filename="package.json"',
  });
}
```

### Server-Sent Events

```typescript
import { Sse, MessageEvent } from '@nestjs/common';
import { Observable, interval, map } from 'rxjs';

@Sse('events')
sse(): Observable<MessageEvent> {
  return interval(1000).pipe(
    map((num) => ({
      data: { timestamp: Date.now(), count: num },
    })),
  );
}
```

## File Upload

```typescript
import { FileInterceptor, FilesInterceptor } from '@nestjs/platform-express';
import { UseInterceptors, UploadedFile, UploadedFiles } from '@nestjs/common';

@Post('upload')
@UseInterceptors(FileInterceptor('file'))
uploadFile(@UploadedFile() file: Express.Multer.File) {
  return { filename: file.originalname, size: file.size };
}

@Post('uploads')
@UseInterceptors(FilesInterceptor('files', 10))
uploadFiles(@UploadedFiles() files: Express.Multer.File[]) {
  return files.map(f => ({ name: f.originalname, size: f.size }));
}
```

### File Validation

```typescript
@Post('upload')
@UseInterceptors(FileInterceptor('file'))
uploadFile(
  @UploadedFile(
    new ParseFilePipe({
      validators: [
        new MaxFileSizeValidator({ maxSize: 5 * 1024 * 1024 }), // 5MB
        new FileTypeValidator({ fileType: /(jpg|jpeg|png|gif)$/ }),
      ],
    }),
  )
  file: Express.Multer.File,
) {
  return { filename: file.originalname };
}
```

## Versioning

```typescript
// main.ts — enable versioning
app.enableVersioning({
  type: VersioningType.URI, // /v1/users, /v2/users
});

// Controller-level
@Controller({ path: 'users', version: '1' })
export class UsersV1Controller {}

@Controller({ path: 'users', version: '2' })
export class UsersV2Controller {}

// Method-level
@Controller('users')
export class UsersController {
  @Version('1')
  @Get()
  findAllV1() { return 'v1'; }

  @Version('2')
  @Get()
  findAllV2() { return 'v2'; }
}
```

Versioning types: `URI` (`/v1/`), `HEADER` (custom header), `MEDIA_TYPE` (Accept header), `CUSTOM`.

## Common Pitfalls

1. **Using `@Res()` blocks NestJS response handling** — use `@Res({ passthrough: true })` if you need both
2. **Route order matters** — static routes must come before parameterized ones (`/users/profile` before `/users/:id`)
3. **Missing `class-transformer`** — `transform: true` in `ValidationPipe` requires `class-transformer` package
4. **POST default status is 201** — NestJS returns 201 for POST, 200 for others; use `@HttpCode()` to override
5. **`whitelist: true` silently strips** — unknown properties are removed; use `forbidNonWhitelisted` to throw instead
