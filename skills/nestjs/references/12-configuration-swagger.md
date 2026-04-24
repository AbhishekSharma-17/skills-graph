# NestJS — Configuration, Swagger & DevOps

> Source: [docs.nestjs.com/techniques/configuration](https://docs.nestjs.com/techniques/configuration) | @nestjs/config 4.x / @nestjs/swagger 11.x

## Table of Contents

- [ConfigModule](#configmodule)
- [Environment Validation](#environment-validation)
- [Custom Config Files](#custom-config-files)
- [OpenAPI / Swagger](#openapi--swagger)
- [Swagger Decorators](#swagger-decorators)
- [Health Checks](#health-checks)
- [Logger](#logger)
- [CORS](#cors)
- [Rate Limiting](#rate-limiting)
- [Compression & Helmet](#compression--helmet)
- [Task Scheduling](#task-scheduling)
- [Common Pitfalls](#common-pitfalls)

## ConfigModule

```bash
npm install @nestjs/config
```

### Basic Setup

```typescript
import { ConfigModule, ConfigService } from '@nestjs/config';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: ['.env.local', '.env'],
    }),
  ],
})
export class AppModule {}
```

### Using ConfigService

```typescript
@Injectable()
export class AppService {
  constructor(private config: ConfigService) {}

  getDatabaseUrl(): string {
    return this.config.get<string>('DATABASE_URL');
  }

  getPort(): number {
    return this.config.get<number>('PORT', 3000); // Default value
  }

  isProduction(): boolean {
    return this.config.get('NODE_ENV') === 'production';
  }
}
```

### Typed Configuration

```typescript
export const databaseConfig = registerAs('database', () => ({
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT, 10) || 5432,
  name: process.env.DB_NAME || 'mydb',
  username: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASS || 'postgres',
}));

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      load: [databaseConfig],
    }),
  ],
})
export class AppModule {}

// Usage with namespace
@Injectable()
export class DatabaseService {
  constructor(
    @Inject(databaseConfig.KEY)
    private dbConfig: ConfigType<typeof databaseConfig>,
  ) {
    console.log(this.dbConfig.host); // Fully typed
  }
}
```

## Environment Validation

### With Joi

```bash
npm install joi
```

```typescript
import * as Joi from 'joi';

ConfigModule.forRoot({
  isGlobal: true,
  validationSchema: Joi.object({
    NODE_ENV: Joi.string().valid('development', 'production', 'test').default('development'),
    PORT: Joi.number().default(3000),
    DATABASE_URL: Joi.string().required(),
    JWT_SECRET: Joi.string().required().min(32),
    REDIS_URL: Joi.string().optional(),
  }),
  validationOptions: {
    abortEarly: true,
  },
}),
```

### With Zod

```typescript
import { z } from 'zod';

const envSchema = z.object({
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  PORT: z.coerce.number().default(3000),
  DATABASE_URL: z.string().url(),
  JWT_SECRET: z.string().min(32),
});

type Env = z.infer<typeof envSchema>;

ConfigModule.forRoot({
  isGlobal: true,
  validate: (config: Record<string, unknown>) => {
    const result = envSchema.safeParse(config);
    if (!result.success) {
      throw new Error(`Config validation error: ${result.error.message}`);
    }
    return result.data;
  },
}),
```

## Custom Config Files

### Config per Module

```typescript
// config/auth.config.ts
export default registerAs('auth', () => ({
  jwtSecret: process.env.JWT_SECRET,
  jwtExpiresIn: process.env.JWT_EXPIRES_IN || '15m',
  refreshExpiresIn: process.env.REFRESH_EXPIRES_IN || '7d',
  bcryptRounds: parseInt(process.env.BCRYPT_ROUNDS, 10) || 10,
}));

// config/app.config.ts
export default registerAs('app', () => ({
  port: parseInt(process.env.PORT, 10) || 3000,
  name: process.env.APP_NAME || 'My API',
  corsOrigin: process.env.CORS_ORIGIN?.split(',') || ['http://localhost:3000'],
}));
```

## OpenAPI / Swagger

```bash
npm install @nestjs/swagger
```

### Setup

```typescript
import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  const config = new DocumentBuilder()
    .setTitle('My API')
    .setDescription('API documentation')
    .setVersion('1.0')
    .addBearerAuth()
    .addTag('users')
    .addTag('orders')
    .build();

  const document = SwaggerModule.createDocument(app, config);
  SwaggerModule.setup('api/docs', app, document);

  await app.listen(3000);
}
```

Access Swagger UI at `http://localhost:3000/api/docs`.

### CLI Plugin (auto-generate decorators)

```json
// nest-cli.json
{
  "compilerOptions": {
    "plugins": [
      {
        "name": "@nestjs/swagger",
        "options": {
          "classValidatorShim": true,
          "introspectComments": true
        }
      }
    ]
  }
}
```

## Swagger Decorators

```typescript
import { ApiTags, ApiOperation, ApiResponse, ApiProperty, ApiBearerAuth } from '@nestjs/swagger';

export class CreateUserDto {
  @ApiProperty({ example: 'john@example.com', description: 'User email' })
  @IsEmail()
  email: string;

  @ApiProperty({ example: 'John Doe', minLength: 2 })
  @IsString()
  @MinLength(2)
  name: string;

  @ApiProperty({ example: 'password123', minLength: 8 })
  @IsString()
  @MinLength(8)
  password: string;
}

@ApiTags('users')
@ApiBearerAuth()
@Controller('users')
export class UsersController {
  @Get()
  @ApiOperation({ summary: 'List all users' })
  @ApiResponse({ status: 200, description: 'Users retrieved', type: [User] })
  findAll() {}

  @Post()
  @ApiOperation({ summary: 'Create a new user' })
  @ApiResponse({ status: 201, description: 'User created', type: User })
  @ApiResponse({ status: 409, description: 'Email already exists' })
  create(@Body() dto: CreateUserDto) {}
}
```

### Pagination Schema

```typescript
export class PaginatedResponseDto<T> {
  @ApiProperty()
  items: T[];

  @ApiProperty({ example: 100 })
  total: number;

  @ApiProperty({ example: 1 })
  page: number;

  @ApiProperty({ example: 10 })
  limit: number;
}
```

## Health Checks

```bash
npm install @nestjs/terminus
```

```typescript
import { TerminusModule } from '@nestjs/terminus';
import { HealthCheckService, TypeOrmHealthIndicator, HttpHealthIndicator } from '@nestjs/terminus';

@Module({
  imports: [TerminusModule],
  controllers: [HealthController],
})
export class HealthModule {}

@Controller('health')
export class HealthController {
  constructor(
    private health: HealthCheckService,
    private db: TypeOrmHealthIndicator,
    private http: HttpHealthIndicator,
  ) {}

  @Get()
  check() {
    return this.health.check([
      () => this.db.pingCheck('database'),
      () => this.http.pingCheck('api', 'https://api.example.com'),
    ]);
  }

  @Get('ready')
  readiness() {
    return this.health.check([
      () => this.db.pingCheck('database'),
    ]);
  }
}
```

Response:
```json
{
  "status": "ok",
  "info": { "database": { "status": "up" } },
  "details": { "database": { "status": "up" } }
}
```

## Logger

### Built-in Logger

```typescript
import { Logger } from '@nestjs/common';

@Injectable()
export class UsersService {
  private readonly logger = new Logger(UsersService.name);

  async create(dto: CreateUserDto) {
    this.logger.log(`Creating user: ${dto.email}`);
    this.logger.debug('DTO details', JSON.stringify(dto));
    this.logger.warn('Password complexity not checked');
    this.logger.error('Failed to create user', error.stack);
  }
}
```

### Custom Logger

```typescript
const app = await NestFactory.create(AppModule, {
  logger: ['error', 'warn', 'log'],  // Filter log levels
});

// Or disable default logger and use custom
const app = await NestFactory.create(AppModule, {
  logger: false,
});
app.useLogger(new CustomLogger());
```

### NestJS 11 JSON Logging

```typescript
const app = await NestFactory.create(AppModule, {
  logger: ConsoleLogger,
});

const logger = app.get(ConsoleLogger);
logger.setLogLevels(['log', 'error', 'warn']);
```

## CORS

```typescript
// Simple
app.enableCors();

// Configured
app.enableCors({
  origin: ['http://localhost:3000', 'https://myapp.com'],
  methods: 'GET,HEAD,PUT,PATCH,POST,DELETE',
  credentials: true,
  allowedHeaders: ['Content-Type', 'Authorization'],
});

// Dynamic origin
app.enableCors({
  origin: (origin, callback) => {
    const allowedOrigins = process.env.CORS_ORIGINS?.split(',') || [];
    if (!origin || allowedOrigins.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
});
```

## Rate Limiting

```bash
npm install @nestjs/throttler
```

```typescript
import { ThrottlerModule, ThrottlerGuard } from '@nestjs/throttler';

@Module({
  imports: [
    ThrottlerModule.forRoot([
      { name: 'short', ttl: 1000, limit: 3 },     // 3 req/sec
      { name: 'medium', ttl: 10000, limit: 20 },   // 20 req/10sec
      { name: 'long', ttl: 60000, limit: 100 },    // 100 req/min
    ]),
  ],
  providers: [{ provide: APP_GUARD, useClass: ThrottlerGuard }],
})
export class AppModule {}

// Skip throttling for specific routes
@SkipThrottle()
@Get('health')
healthCheck() {}

// Custom limit per route
@Throttle({ short: { limit: 1, ttl: 1000 } })
@Post('login')
login() {}
```

## Compression & Helmet

```bash
npm install compression helmet
```

```typescript
import * as compression from 'compression';
import helmet from 'helmet';

const app = await NestFactory.create(AppModule);
app.use(helmet());
app.use(compression());
```

## Task Scheduling

```bash
npm install @nestjs/schedule
```

```typescript
import { ScheduleModule } from '@nestjs/schedule';
import { Cron, CronExpression, Interval, Timeout } from '@nestjs/schedule';

@Module({
  imports: [ScheduleModule.forRoot()],
})
export class AppModule {}

@Injectable()
export class TasksService {
  @Cron(CronExpression.EVERY_DAY_AT_MIDNIGHT)
  handleDailyCleanup() {
    this.cleanupService.removeExpiredSessions();
  }

  @Cron('0 */5 * * * *')  // Every 5 minutes
  handleMetricsCollection() {
    this.metricsService.collect();
  }

  @Interval(30000)  // Every 30 seconds
  handleHeartbeat() {
    this.healthService.ping();
  }

  @Timeout(5000)  // Once, 5 seconds after startup
  handleStartup() {
    this.warmupService.warmCache();
  }
}
```

## Common Pitfalls

1. **ConfigModule not global** — add `isGlobal: true` or import in every module that needs it
2. **Env vars are always strings** — parse numbers with `parseInt()` or use Joi/Zod coercion
3. **Swagger not reflecting changes** — delete `dist/` and rebuild; the CLI plugin caches metadata
4. **Health check blocking startup** — external service checks fail if services aren't ready at boot
5. **Rate limiter bypass** — `ThrottlerGuard` must be registered as `APP_GUARD` to apply globally
6. **Missing `.env` in production** — use platform env vars (Docker, cloud); `.env` is for development only
