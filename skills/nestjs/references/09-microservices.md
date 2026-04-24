# NestJS — Microservices

> Source: [docs.nestjs.com/microservices/basics](https://docs.nestjs.com/microservices/basics) | @nestjs/microservices 11.x

## Table of Contents

- [Overview](#overview)
- [Transport Layers](#transport-layers)
- [Creating a Microservice](#creating-a-microservice)
- [Message Patterns](#message-patterns)
- [Event-Based Communication](#event-based-communication)
- [gRPC Transport](#grpc-transport)
- [Kafka Transport](#kafka-transport)
- [NATS Transport](#nats-transport)
- [Redis Transport](#redis-transport)
- [RabbitMQ Transport](#rabbitmq-transport)
- [Hybrid Applications](#hybrid-applications)
- [Error Handling](#error-handling)
- [Common Pitfalls](#common-pitfalls)

## Overview

NestJS microservices use a transport-agnostic messaging layer. The same business logic works across TCP, Redis, NATS, Kafka, gRPC, RabbitMQ, and MQTT.

```bash
npm install @nestjs/microservices
```

Two communication patterns:
- **Request-response** — client sends a message, waits for a reply (like HTTP)
- **Event-based** — client emits an event, no response expected (fire-and-forget)

## Transport Layers

| Transport | Package | Use Case |
|-----------|---------|----------|
| **TCP** | Built-in | Simple inter-service communication |
| **Redis** | `ioredis` | Pub/sub, lightweight messaging |
| **NATS** | `nats` | High-throughput, cloud-native messaging |
| **Kafka** | `kafkajs` | Event streaming, high-volume data pipelines |
| **gRPC** | `@grpc/grpc-js` | High-performance RPC, strongly typed contracts |
| **RabbitMQ** | `amqplib` | Complex routing, reliable message delivery |
| **MQTT** | `mqtt` | IoT, lightweight pub/sub |

## Creating a Microservice

### Standalone Microservice

```typescript
// main.ts
import { NestFactory } from '@nestjs/core';
import { MicroserviceOptions, Transport } from '@nestjs/microservices';

async function bootstrap() {
  const app = await NestFactory.createMicroservice<MicroserviceOptions>(
    AppModule,
    {
      transport: Transport.TCP,
      options: { host: '0.0.0.0', port: 3001 },
    },
  );
  await app.listen();
}
bootstrap();
```

### Client Registration

```typescript
// In the calling service
@Module({
  imports: [
    ClientsModule.register([
      {
        name: 'USERS_SERVICE',
        transport: Transport.TCP,
        options: { host: 'localhost', port: 3001 },
      },
    ]),
  ],
})
export class OrdersModule {}
```

### Async Client Registration

```typescript
ClientsModule.registerAsync([
  {
    name: 'USERS_SERVICE',
    imports: [ConfigModule],
    useFactory: (config: ConfigService) => ({
      transport: Transport.TCP,
      options: {
        host: config.get('USERS_HOST'),
        port: config.get<number>('USERS_PORT'),
      },
    }),
    inject: [ConfigService],
  },
]),
```

## Message Patterns

Request-response communication using `@MessagePattern()`:

### Server Side

```typescript
import { MessagePattern, Payload } from '@nestjs/microservices';

@Controller()
export class UsersController {
  constructor(private usersService: UsersService) {}

  @MessagePattern({ cmd: 'find_user' })
  findUser(@Payload() data: { id: number }) {
    return this.usersService.findOne(data.id);
  }

  @MessagePattern({ cmd: 'create_user' })
  createUser(@Payload() data: CreateUserDto) {
    return this.usersService.create(data);
  }

  @MessagePattern({ cmd: 'find_all_users' })
  findAll(@Payload() data: { page: number; limit: number }) {
    return this.usersService.findAll(data.page, data.limit);
  }
}
```

### Client Side

```typescript
import { ClientProxy } from '@nestjs/microservices';

@Injectable()
export class OrdersService {
  constructor(
    @Inject('USERS_SERVICE') private usersClient: ClientProxy,
  ) {}

  async getUser(id: number): Promise<User> {
    return firstValueFrom(
      this.usersClient.send<User>({ cmd: 'find_user' }, { id }),
    );
  }
}
```

## Event-Based Communication

Fire-and-forget with `@EventPattern()`:

### Server Side

```typescript
@Controller()
export class NotificationsController {
  @EventPattern('user_created')
  handleUserCreated(@Payload() data: { userId: number; email: string }) {
    this.notificationsService.sendWelcomeEmail(data.email);
  }

  @EventPattern('order_placed')
  handleOrderPlaced(@Payload() data: OrderEvent) {
    this.notificationsService.notifyFulfillment(data);
  }
}
```

### Client Side

```typescript
@Injectable()
export class UsersService {
  constructor(
    @Inject('NOTIFICATIONS_SERVICE') private notificationsClient: ClientProxy,
  ) {}

  async create(dto: CreateUserDto): Promise<User> {
    const user = await this.usersRepo.save(dto);
    this.notificationsClient.emit('user_created', {
      userId: user.id,
      email: user.email,
    });
    return user;
  }
}
```

## gRPC Transport

Strongly-typed RPC using Protocol Buffers:

```bash
npm install @grpc/grpc-js @grpc/proto-loader
```

```protobuf
// proto/users.proto
syntax = "proto3";

package users;

service UsersService {
  rpc FindOne (UserById) returns (User);
  rpc FindAll (Empty) returns (UserList);
}

message UserById {
  int32 id = 1;
}

message User {
  int32 id = 1;
  string name = 2;
  string email = 3;
}

message UserList {
  repeated User users = 1;
}

message Empty {}
```

### gRPC Server

```typescript
const app = await NestFactory.createMicroservice<MicroserviceOptions>(
  AppModule,
  {
    transport: Transport.GRPC,
    options: {
      package: 'users',
      protoPath: join(__dirname, 'proto/users.proto'),
      url: '0.0.0.0:5000',
    },
  },
);
```

```typescript
@Controller()
export class UsersController {
  @GrpcMethod('UsersService', 'FindOne')
  findOne(data: { id: number }): User {
    return this.usersService.findOne(data.id);
  }
}
```

### gRPC Client

```typescript
@Module({
  imports: [
    ClientsModule.register([
      {
        name: 'USERS_PACKAGE',
        transport: Transport.GRPC,
        options: {
          package: 'users',
          protoPath: join(__dirname, 'proto/users.proto'),
          url: 'localhost:5000',
        },
      },
    ]),
  ],
})
export class OrdersModule {}

@Injectable()
export class OrdersService implements OnModuleInit {
  private usersService: UsersGrpcService;

  constructor(@Inject('USERS_PACKAGE') private client: ClientGrpc) {}

  onModuleInit() {
    this.usersService = this.client.getService<UsersGrpcService>('UsersService');
  }

  async getUser(id: number): Promise<User> {
    return firstValueFrom(this.usersService.findOne({ id }));
  }
}
```

## Kafka Transport

```typescript
const app = await NestFactory.createMicroservice<MicroserviceOptions>(
  AppModule,
  {
    transport: Transport.KAFKA,
    options: {
      client: {
        brokers: ['localhost:9092'],
        clientId: 'users-service',
      },
      consumer: { groupId: 'users-consumer' },
    },
  },
);
```

```typescript
@Controller()
export class UsersController {
  @MessagePattern('users.find')
  findUser(@Payload() data: { id: number }, @Ctx() context: KafkaContext) {
    const topic = context.getTopic();
    const partition = context.getPartition();
    return this.usersService.findOne(data.id);
  }

  @EventPattern('users.created')
  handleUserCreated(@Payload() data: UserCreatedEvent) {
    this.analyticsService.trackSignup(data);
  }
}
```

## NATS Transport

```typescript
const app = await NestFactory.createMicroservice<MicroserviceOptions>(
  AppModule,
  {
    transport: Transport.NATS,
    options: { servers: ['nats://localhost:4222'] },
  },
);
```

## Redis Transport

```typescript
const app = await NestFactory.createMicroservice<MicroserviceOptions>(
  AppModule,
  {
    transport: Transport.REDIS,
    options: { host: 'localhost', port: 6379 },
  },
);
```

## RabbitMQ Transport

```typescript
const app = await NestFactory.createMicroservice<MicroserviceOptions>(
  AppModule,
  {
    transport: Transport.RMQ,
    options: {
      urls: ['amqp://localhost:5672'],
      queue: 'users_queue',
      queueOptions: { durable: true },
    },
  },
);
```

## Hybrid Applications

Combine HTTP and microservice in the same app:

```typescript
async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  app.connectMicroservice<MicroserviceOptions>({
    transport: Transport.TCP,
    options: { port: 3001 },
  });

  app.connectMicroservice<MicroserviceOptions>({
    transport: Transport.REDIS,
    options: { host: 'localhost', port: 6379 },
  });

  await app.startAllMicroservices();
  await app.listen(3000);
}
```

## Error Handling

### RPC Exception

```typescript
import { RpcException } from '@nestjs/microservices';

@MessagePattern({ cmd: 'find_user' })
async findUser(@Payload() data: { id: number }) {
  const user = await this.usersService.findOne(data.id);
  if (!user) {
    throw new RpcException({ statusCode: 404, message: 'User not found' });
  }
  return user;
}
```

### Client-Side Error Handling

```typescript
async getUser(id: number): Promise<User> {
  return firstValueFrom(
    this.usersClient.send<User>({ cmd: 'find_user' }, { id }).pipe(
      catchError(err => {
        throw new HttpException(err.message, err.statusCode || 500);
      }),
    ),
  );
}
```

## Common Pitfalls

1. **Client not connected** — call `await this.client.connect()` in `onModuleInit` or use `firstValueFrom`
2. **Observable vs Promise** — `client.send()` returns Observable; use `firstValueFrom()` for async/await
3. **Event ordering** — events are not guaranteed in order across partitions (Kafka) or subjects (NATS)
4. **Serialization** — complex objects may not serialize correctly; stick to plain objects
5. **gRPC proto path** — must be absolute path; use `join(__dirname, 'proto/...')`
6. **Kafka consumer groups** — each service instance needs the same `groupId` for load balancing
