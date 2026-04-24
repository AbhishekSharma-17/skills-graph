# NestJS — Database Integration

> Source: [docs.nestjs.com/techniques/database](https://docs.nestjs.com/techniques/database) | @nestjs/core 11.x

## Table of Contents

- [Database Options](#database-options)
- [TypeORM Integration](#typeorm-integration)
- [Prisma Integration](#prisma-integration)
- [Mongoose Integration](#mongoose-integration)
- [Repository Pattern](#repository-pattern)
- [Transactions](#transactions)
- [Migrations](#migrations)
- [Seeding](#seeding)
- [Connection Management](#connection-management)
- [Common Pitfalls](#common-pitfalls)

## Database Options

| ORM/ODM | Package | Best For |
|---------|---------|----------|
| **TypeORM** | `@nestjs/typeorm` | SQL databases with decorator-based entities |
| **Prisma** | `prisma` + `@prisma/client` | Schema-first approach, strong typing, auto-migrations |
| **Mongoose** | `@nestjs/mongoose` | MongoDB with schema-based models |
| **Sequelize** | `@nestjs/sequelize` | SQL databases, ActiveRecord pattern |
| **MikroORM** | `@mikro-orm/nestjs` | TypeScript-first ORM, unit of work pattern |
| **Drizzle** | `drizzle-orm` | Lightweight, SQL-like TypeScript ORM |
| **Knex** | `knex` | SQL query builder (not a full ORM) |

## TypeORM Integration

### Setup

```bash
npm install @nestjs/typeorm typeorm pg
```

```typescript
// app.module.ts
import { TypeOrmModule } from '@nestjs/typeorm';

@Module({
  imports: [
    TypeOrmModule.forRootAsync({
      imports: [ConfigModule],
      useFactory: (config: ConfigService) => ({
        type: 'postgres',
        host: config.get('DB_HOST'),
        port: config.get<number>('DB_PORT'),
        username: config.get('DB_USER'),
        password: config.get('DB_PASS'),
        database: config.get('DB_NAME'),
        entities: [__dirname + '/**/*.entity{.ts,.js}'],
        synchronize: false,  // Never true in production
        logging: config.get('NODE_ENV') === 'development',
      }),
      inject: [ConfigService],
    }),
  ],
})
export class AppModule {}
```

### Entity Definition

```typescript
import { Entity, Column, PrimaryGeneratedColumn, CreateDateColumn, UpdateDateColumn, ManyToOne, OneToMany } from 'typeorm';

@Entity('users')
export class User {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ unique: true })
  email: string;

  @Column()
  name: string;

  @Column({ select: false })
  passwordHash: string;

  @Column({ type: 'enum', enum: ['active', 'inactive'], default: 'active' })
  status: string;

  @OneToMany(() => Post, post => post.author)
  posts: Post[];

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
```

### Feature Module Registration

```typescript
// users.module.ts
@Module({
  imports: [TypeOrmModule.forFeature([User])],
  controllers: [UsersController],
  providers: [UsersService],
  exports: [UsersService],
})
export class UsersModule {}
```

### Service with Repository

```typescript
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';

@Injectable()
export class UsersService {
  constructor(
    @InjectRepository(User)
    private usersRepo: Repository<User>,
  ) {}

  async findAll(page = 1, limit = 10): Promise<[User[], number]> {
    return this.usersRepo.findAndCount({
      skip: (page - 1) * limit,
      take: limit,
      order: { createdAt: 'DESC' },
    });
  }

  async findOne(id: number): Promise<User> {
    const user = await this.usersRepo.findOne({
      where: { id },
      relations: ['posts'],
    });
    if (!user) throw new NotFoundException(`User #${id} not found`);
    return user;
  }

  async create(dto: CreateUserDto): Promise<User> {
    const user = this.usersRepo.create(dto);
    return this.usersRepo.save(user);
  }

  async update(id: number, dto: UpdateUserDto): Promise<User> {
    await this.usersRepo.update(id, dto);
    return this.findOne(id);
  }

  async remove(id: number): Promise<void> {
    const result = await this.usersRepo.delete(id);
    if (result.affected === 0) throw new NotFoundException();
  }
}
```

### QueryBuilder

```typescript
async search(query: string): Promise<User[]> {
  return this.usersRepo
    .createQueryBuilder('user')
    .where('user.name ILIKE :query', { query: `%${query}%` })
    .orWhere('user.email ILIKE :query', { query: `%${query}%` })
    .leftJoinAndSelect('user.posts', 'post')
    .orderBy('user.createdAt', 'DESC')
    .take(20)
    .getMany();
}
```

## Prisma Integration

### Setup

```bash
npm install prisma @prisma/client
npx prisma init
```

```prisma
// prisma/schema.prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model User {
  id        Int      @id @default(autoincrement())
  email     String   @unique
  name      String
  posts     Post[]
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}

model Post {
  id        Int      @id @default(autoincrement())
  title     String
  content   String?
  author    User     @relation(fields: [authorId], references: [id])
  authorId  Int
  createdAt DateTime @default(now())
}
```

### PrismaService

```typescript
import { Injectable, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { PrismaClient } from '@prisma/client';

@Injectable()
export class PrismaService extends PrismaClient implements OnModuleInit, OnModuleDestroy {
  async onModuleInit() {
    await this.$connect();
  }

  async onModuleDestroy() {
    await this.$disconnect();
  }
}
```

### PrismaModule

```typescript
@Global()
@Module({
  providers: [PrismaService],
  exports: [PrismaService],
})
export class PrismaModule {}
```

### Service with Prisma

```typescript
@Injectable()
export class UsersService {
  constructor(private prisma: PrismaService) {}

  async findAll(page = 1, limit = 10) {
    const [users, total] = await Promise.all([
      this.prisma.user.findMany({
        skip: (page - 1) * limit,
        take: limit,
        orderBy: { createdAt: 'desc' },
        include: { posts: true },
      }),
      this.prisma.user.count(),
    ]);
    return { users, total };
  }

  async create(dto: CreateUserDto) {
    return this.prisma.user.create({ data: dto });
  }

  async update(id: number, dto: UpdateUserDto) {
    return this.prisma.user.update({ where: { id }, data: dto });
  }
}
```

## Mongoose Integration

### Setup

```bash
npm install @nestjs/mongoose mongoose
```

```typescript
@Module({
  imports: [
    MongooseModule.forRootAsync({
      imports: [ConfigModule],
      useFactory: (config: ConfigService) => ({
        uri: config.get<string>('MONGODB_URI'),
      }),
      inject: [ConfigService],
    }),
  ],
})
export class AppModule {}
```

### Schema Definition

```typescript
import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { HydratedDocument } from 'mongoose';

export type UserDocument = HydratedDocument<User>;

@Schema({ timestamps: true })
export class User {
  @Prop({ required: true })
  name: string;

  @Prop({ required: true, unique: true })
  email: string;

  @Prop({ type: [String], default: ['user'] })
  roles: string[];
}

export const UserSchema = SchemaFactory.createForClass(User);
```

### Service with Mongoose

```typescript
@Injectable()
export class UsersService {
  constructor(@InjectModel(User.name) private userModel: Model<User>) {}

  async findAll(): Promise<User[]> {
    return this.userModel.find().exec();
  }

  async create(dto: CreateUserDto): Promise<User> {
    return new this.userModel(dto).save();
  }
}
```

## Repository Pattern

Abstract data access behind a repository interface:

```typescript
export abstract class BaseRepository<T> {
  abstract findById(id: number): Promise<T | null>;
  abstract findAll(): Promise<T[]>;
  abstract create(data: Partial<T>): Promise<T>;
  abstract update(id: number, data: Partial<T>): Promise<T>;
  abstract delete(id: number): Promise<void>;
}

@Injectable()
export class TypeOrmUsersRepository extends BaseRepository<User> {
  constructor(
    @InjectRepository(User)
    private repo: Repository<User>,
  ) { super(); }

  async findById(id: number) { return this.repo.findOneBy({ id }); }
  async findAll() { return this.repo.find(); }
  async create(data: Partial<User>) { return this.repo.save(data); }
  async update(id: number, data: Partial<User>) {
    await this.repo.update(id, data);
    return this.findById(id);
  }
  async delete(id: number) { await this.repo.delete(id); }
}

@Module({
  providers: [
    { provide: BaseRepository, useClass: TypeOrmUsersRepository },
  ],
})
export class UsersModule {}
```

## Transactions

### TypeORM Transactions

```typescript
@Injectable()
export class OrdersService {
  constructor(private dataSource: DataSource) {}

  async createOrder(dto: CreateOrderDto): Promise<Order> {
    const queryRunner = this.dataSource.createQueryRunner();
    await queryRunner.connect();
    await queryRunner.startTransaction();

    try {
      const order = await queryRunner.manager.save(Order, dto);
      await queryRunner.manager.update(Product, dto.productId, {
        stock: () => `stock - ${dto.quantity}`,
      });
      await queryRunner.commitTransaction();
      return order;
    } catch (err) {
      await queryRunner.rollbackTransaction();
      throw err;
    } finally {
      await queryRunner.release();
    }
  }
}
```

### Prisma Transactions

```typescript
async transferFunds(fromId: number, toId: number, amount: number) {
  return this.prisma.$transaction(async (tx) => {
    const from = await tx.account.update({
      where: { id: fromId },
      data: { balance: { decrement: amount } },
    });
    if (from.balance < 0) throw new BadRequestException('Insufficient funds');

    await tx.account.update({
      where: { id: toId },
      data: { balance: { increment: amount } },
    });
  });
}
```

## Migrations

### TypeORM Migrations

```bash
# Generate migration from entity changes
npx typeorm migration:generate -d src/data-source.ts src/migrations/AddUserStatus

# Run migrations
npx typeorm migration:run -d src/data-source.ts

# Revert last migration
npx typeorm migration:revert -d src/data-source.ts
```

### Prisma Migrations

```bash
npx prisma migrate dev --name add_user_status  # Development
npx prisma migrate deploy                       # Production
npx prisma migrate reset                        # Reset database
```

## Seeding

```typescript
// seed.ts
async function seed() {
  const app = await NestFactory.createApplicationContext(AppModule);
  const usersService = app.get(UsersService);

  await usersService.create({ name: 'Admin', email: 'admin@example.com' });
  await usersService.create({ name: 'User', email: 'user@example.com' });

  await app.close();
}
seed();
```

## Connection Management

### Multiple Databases

```typescript
@Module({
  imports: [
    TypeOrmModule.forRoot({ name: 'default', ...primaryDbConfig }),
    TypeOrmModule.forRoot({ name: 'analytics', ...analyticsDbConfig }),
  ],
})
export class AppModule {}

// Use named connection
@Module({
  imports: [TypeOrmModule.forFeature([Event], 'analytics')],
})
export class AnalyticsModule {}

@Injectable()
export class AnalyticsService {
  constructor(
    @InjectRepository(Event, 'analytics')
    private eventsRepo: Repository<Event>,
  ) {}
}
```

## Common Pitfalls

1. **`synchronize: true` in production** — drops and recreates tables; always use migrations
2. **N+1 query problem** — use `relations` option or `leftJoinAndSelect` to eager-load
3. **Missing `@InjectRepository`** — TypeORM repos must be injected with the decorator
4. **Prisma client not regenerated** — run `npx prisma generate` after schema changes
5. **Connection pool exhaustion** — configure pool size: `extra: { max: 20 }` for TypeORM
6. **Raw queries without parameterization** — always use parameterized queries to prevent SQL injection
