# NestJS — Testing

> Source: [docs.nestjs.com/fundamentals/testing](https://docs.nestjs.com/fundamentals/testing) | @nestjs/testing 11.x

## Table of Contents

- [Testing Overview](#testing-overview)
- [Unit Testing](#unit-testing)
- [Testing Module](#testing-module)
- [Mocking Providers](#mocking-providers)
- [Testing Controllers](#testing-controllers)
- [Testing Services](#testing-services)
- [Testing Guards & Pipes](#testing-guards--pipes)
- [Integration Testing](#integration-testing)
- [E2E Testing](#e2e-testing)
- [Testing GraphQL](#testing-graphql)
- [Testing WebSockets](#testing-websockets)
- [Test Database Setup](#test-database-setup)
- [Common Pitfalls](#common-pitfalls)

## Testing Overview

NestJS ships with Jest preconfigured. The `@nestjs/testing` package provides utilities to create a testing module that mirrors your application's module structure.

```bash
# Run all tests
npm test

# Watch mode
npm run test:watch

# Coverage
npm run test:cov

# E2E tests
npm run test:e2e
```

### Test File Conventions

```
src/
├── users/
│   ├── users.service.ts
│   ├── users.service.spec.ts      ← Unit test
│   ├── users.controller.ts
│   └── users.controller.spec.ts   ← Unit test
test/
├── users.e2e-spec.ts              ← E2E test
└── jest-e2e.json                  ← E2E Jest config
```

## Unit Testing

### Testing Module Setup

```typescript
import { Test, TestingModule } from '@nestjs/testing';

describe('UsersService', () => {
  let service: UsersService;
  let repository: Repository<User>;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        UsersService,
        {
          provide: getRepositoryToken(User),
          useValue: {
            find: jest.fn(),
            findOneBy: jest.fn(),
            save: jest.fn(),
            delete: jest.fn(),
          },
        },
      ],
    }).compile();

    service = module.get<UsersService>(UsersService);
    repository = module.get<Repository<User>>(getRepositoryToken(User));
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });
});
```

## Testing Module

The `Test.createTestingModule()` creates an isolated DI container for testing:

```typescript
const module = await Test.createTestingModule({
  imports: [UsersModule],   // Import real modules
  providers: [
    UsersService,
    {
      provide: EmailService,         // Override with mock
      useValue: { send: jest.fn() },
    },
  ],
}).compile();
```

### Overriding Providers

```typescript
const module = await Test.createTestingModule({
  imports: [UsersModule],
})
  .overrideProvider(EmailService)
  .useValue({ send: jest.fn().mockResolvedValue(true) })
  .overrideGuard(AuthGuard)
  .useValue({ canActivate: () => true })
  .overrideInterceptor(LoggingInterceptor)
  .useValue({ intercept: (ctx, next) => next.handle() })
  .overridePipe(ValidationPipe)
  .useValue({ transform: (value) => value })
  .compile();
```

## Mocking Providers

### Mock Factory

```typescript
const mockUsersService = {
  findAll: jest.fn().mockResolvedValue([
    { id: 1, name: 'Alice', email: 'alice@example.com' },
    { id: 2, name: 'Bob', email: 'bob@example.com' },
  ]),
  findOne: jest.fn().mockImplementation((id: number) =>
    Promise.resolve({ id, name: 'Alice', email: 'alice@example.com' }),
  ),
  create: jest.fn().mockImplementation((dto) =>
    Promise.resolve({ id: Date.now(), ...dto }),
  ),
  remove: jest.fn().mockResolvedValue(undefined),
};
```

### Type-Safe Mocking

```typescript
type MockType<T> = {
  [P in keyof T]?: jest.Mock;
};

const mockRepository: MockType<Repository<User>> = {
  find: jest.fn(),
  findOneBy: jest.fn(),
  save: jest.fn(),
  create: jest.fn(),
  delete: jest.fn(),
};
```

## Testing Controllers

```typescript
describe('UsersController', () => {
  let controller: UsersController;
  let service: UsersService;

  beforeEach(async () => {
    const module = await Test.createTestingModule({
      controllers: [UsersController],
      providers: [
        { provide: UsersService, useValue: mockUsersService },
      ],
    }).compile();

    controller = module.get<UsersController>(UsersController);
    service = module.get<UsersService>(UsersService);
  });

  describe('findAll', () => {
    it('should return an array of users', async () => {
      const result = await controller.findAll();
      expect(result).toHaveLength(2);
      expect(service.findAll).toHaveBeenCalled();
    });
  });

  describe('findOne', () => {
    it('should return a single user', async () => {
      const result = await controller.findOne(1);
      expect(result.id).toBe(1);
      expect(service.findOne).toHaveBeenCalledWith(1);
    });
  });

  describe('create', () => {
    it('should create a user', async () => {
      const dto: CreateUserDto = { name: 'Charlie', email: 'charlie@test.com' };
      const result = await controller.create(dto);
      expect(result.name).toBe('Charlie');
      expect(service.create).toHaveBeenCalledWith(dto);
    });
  });
});
```

## Testing Services

```typescript
describe('UsersService', () => {
  let service: UsersService;
  let repo: MockType<Repository<User>>;

  beforeEach(async () => {
    const module = await Test.createTestingModule({
      providers: [
        UsersService,
        {
          provide: getRepositoryToken(User),
          useValue: {
            findOneBy: jest.fn(),
            save: jest.fn(),
            delete: jest.fn(),
          },
        },
      ],
    }).compile();

    service = module.get(UsersService);
    repo = module.get(getRepositoryToken(User));
  });

  describe('findOne', () => {
    it('should return user when found', async () => {
      const user = { id: 1, name: 'Alice', email: 'alice@test.com' };
      repo.findOneBy.mockResolvedValue(user);

      const result = await service.findOne(1);
      expect(result).toEqual(user);
      expect(repo.findOneBy).toHaveBeenCalledWith({ id: 1 });
    });

    it('should throw NotFoundException when not found', async () => {
      repo.findOneBy.mockResolvedValue(null);

      await expect(service.findOne(999)).rejects.toThrow(NotFoundException);
    });
  });

  describe('create', () => {
    it('should save and return the user', async () => {
      const dto = { name: 'Bob', email: 'bob@test.com' };
      const saved = { id: 1, ...dto };
      repo.save.mockResolvedValue(saved);

      const result = await service.create(dto);
      expect(result).toEqual(saved);
    });
  });
});
```

## Testing Guards & Pipes

### Testing a Guard

```typescript
describe('RolesGuard', () => {
  let guard: RolesGuard;
  let reflector: Reflector;

  beforeEach(async () => {
    const module = await Test.createTestingModule({
      providers: [RolesGuard, Reflector],
    }).compile();

    guard = module.get(RolesGuard);
    reflector = module.get(Reflector);
  });

  it('should allow access when no roles required', () => {
    jest.spyOn(reflector, 'getAllAndOverride').mockReturnValue(undefined);
    const context = createMockExecutionContext({ user: { roles: ['user'] } });
    expect(guard.canActivate(context)).toBe(true);
  });

  it('should deny access when user lacks role', () => {
    jest.spyOn(reflector, 'getAllAndOverride').mockReturnValue(['admin']);
    const context = createMockExecutionContext({ user: { roles: ['user'] } });
    expect(guard.canActivate(context)).toBe(false);
  });
});
```

### Testing a Custom Pipe

```typescript
describe('ParseDatePipe', () => {
  let pipe: ParseDatePipe;

  beforeEach(() => {
    pipe = new ParseDatePipe();
  });

  it('should parse valid date string', () => {
    const result = pipe.transform('2026-04-25');
    expect(result).toBeInstanceOf(Date);
  });

  it('should throw BadRequestException for invalid date', () => {
    expect(() => pipe.transform('not-a-date')).toThrow(BadRequestException);
  });
});
```

## Integration Testing

Test multiple components working together:

```typescript
describe('Users Integration', () => {
  let module: TestingModule;
  let service: UsersService;

  beforeAll(async () => {
    module = await Test.createTestingModule({
      imports: [
        TypeOrmModule.forRoot({
          type: 'sqlite',
          database: ':memory:',
          entities: [User],
          synchronize: true,
        }),
        TypeOrmModule.forFeature([User]),
      ],
      providers: [UsersService],
    }).compile();

    service = module.get(UsersService);
  });

  afterAll(async () => {
    await module.close();
  });

  it('should create and retrieve a user', async () => {
    const user = await service.create({ name: 'Test', email: 'test@test.com' });
    expect(user.id).toBeDefined();

    const found = await service.findOne(user.id);
    expect(found.email).toBe('test@test.com');
  });
});
```

## E2E Testing

Test the full HTTP request/response cycle:

```typescript
import { INestApplication } from '@nestjs/common';
import * as request from 'supertest';

describe('UsersController (e2e)', () => {
  let app: INestApplication;

  beforeAll(async () => {
    const moduleFixture = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();

    app = moduleFixture.createNestApplication();
    app.useGlobalPipes(new ValidationPipe({ whitelist: true, transform: true }));
    await app.init();
  });

  afterAll(async () => {
    await app.close();
  });

  it('GET /users', () => {
    return request(app.getHttpServer())
      .get('/users')
      .expect(200)
      .expect((res) => {
        expect(Array.isArray(res.body)).toBe(true);
      });
  });

  it('POST /users — valid', () => {
    return request(app.getHttpServer())
      .post('/users')
      .send({ name: 'Test', email: 'test@test.com' })
      .expect(201)
      .expect((res) => {
        expect(res.body.name).toBe('Test');
        expect(res.body.id).toBeDefined();
      });
  });

  it('POST /users — validation error', () => {
    return request(app.getHttpServer())
      .post('/users')
      .send({ name: '' })
      .expect(400);
  });

  it('GET /users/:id — not found', () => {
    return request(app.getHttpServer())
      .get('/users/99999')
      .expect(404);
  });
});
```

## Testing GraphQL

```typescript
describe('Users GraphQL (e2e)', () => {
  it('query users', () => {
    return request(app.getHttpServer())
      .post('/graphql')
      .send({
        query: `
          query {
            users {
              id
              name
              email
            }
          }
        `,
      })
      .expect(200)
      .expect((res) => {
        expect(res.body.data.users).toBeInstanceOf(Array);
      });
  });
});
```

## Testing WebSockets

```typescript
import { io, Socket } from 'socket.io-client';

describe('ChatGateway (e2e)', () => {
  let app: INestApplication;
  let client: Socket;

  beforeAll(async () => {
    const module = await Test.createTestingModule({
      imports: [ChatModule],
    }).compile();

    app = module.createNestApplication();
    await app.listen(0);
    const port = app.getHttpServer().address().port;
    client = io(`http://localhost:${port}`);
  });

  afterAll(async () => {
    client.disconnect();
    await app.close();
  });

  it('should receive message acknowledgement', (done) => {
    client.emit('message', { room: 'test', content: 'hello' }, (response) => {
      expect(response).toBeDefined();
      done();
    });
  });
});
```

## Test Database Setup

Use SQLite in-memory for fast unit/integration tests, or Testcontainers for production-like databases:

```typescript
// SQLite in-memory
TypeOrmModule.forRoot({
  type: 'sqlite',
  database: ':memory:',
  entities: [User, Post],
  synchronize: true,
})

// Testcontainers (npm install @testcontainers/postgresql)
const container = await new PostgreSqlContainer().start();
// Use container.getConnectionUri() for TypeORM/Prisma
```

## Common Pitfalls

1. **Not calling `module.close()`** — database connections leak between test suites
2. **Missing `ValidationPipe` in E2E** — configure the same global pipes as main.ts
3. **Mocking too deep** — test behavior, not implementation; mock at service boundaries
4. **Shared test state** — use `beforeEach` to reset mocks: `jest.clearAllMocks()`
5. **E2E port conflicts** — use `app.listen(0)` for a random available port
6. **Async lifecycle hooks** — if a provider has `onModuleInit`, it runs during `compile()` and may fail with mocked deps
