# NestJS — WebSockets & Events

> Source: [docs.nestjs.com/websockets/gateways](https://docs.nestjs.com/websockets/gateways) | @nestjs/websockets 11.x

## Table of Contents

- [WebSocket Gateways](#websocket-gateways)
- [Socket.IO Integration](#socketio-integration)
- [Rooms & Namespaces](#rooms--namespaces)
- [Guards & Interceptors](#guards--interceptors)
- [WS Adapters](#ws-adapters)
- [EventEmitter2](#eventemitter2)
- [Server-Sent Events (SSE)](#server-sent-events-sse)
- [CQRS Basics](#cqrs-basics)
- [Common Pitfalls](#common-pitfalls)

## WebSocket Gateways

Gateways are the WebSocket equivalent of controllers. They handle incoming messages and can broadcast to connected clients.

```bash
npm install @nestjs/websockets @nestjs/platform-socket.io socket.io
```

### Basic Gateway

```typescript
import {
  WebSocketGateway,
  SubscribeMessage,
  MessageBody,
  WebSocketServer,
  ConnectedSocket,
  OnGatewayInit,
  OnGatewayConnection,
  OnGatewayDisconnect,
} from '@nestjs/websockets';
import { Server, Socket } from 'socket.io';

@WebSocketGateway({
  cors: { origin: '*' },
})
export class ChatGateway
  implements OnGatewayInit, OnGatewayConnection, OnGatewayDisconnect
{
  @WebSocketServer()
  server: Server;

  afterInit(server: Server) {
    console.log('WebSocket server initialized');
  }

  handleConnection(client: Socket) {
    console.log(`Client connected: ${client.id}`);
  }

  handleDisconnect(client: Socket) {
    console.log(`Client disconnected: ${client.id}`);
  }

  @SubscribeMessage('message')
  handleMessage(
    @MessageBody() data: { room: string; content: string },
    @ConnectedSocket() client: Socket,
  ) {
    this.server.to(data.room).emit('message', {
      sender: client.id,
      content: data.content,
      timestamp: new Date(),
    });
    return { event: 'message', data: 'Message sent' };
  }
}
```

### Register in Module

```typescript
@Module({
  providers: [ChatGateway, ChatService],
})
export class ChatModule {}
```

## Socket.IO Integration

### Custom Port & Namespace

```typescript
@WebSocketGateway(8080, {
  namespace: 'chat',
  cors: {
    origin: ['http://localhost:3000'],
    credentials: true,
  },
  transports: ['websocket', 'polling'],
})
export class ChatGateway {}
```

### Client Connection (browser)

```typescript
import { io } from 'socket.io-client';

const socket = io('http://localhost:8080/chat', {
  auth: { token: 'jwt-token-here' },
});

socket.on('connect', () => {
  console.log('Connected:', socket.id);
});

socket.emit('message', { room: 'general', content: 'Hello!' });

socket.on('message', (data) => {
  console.log('Received:', data);
});
```

### Acknowledgements

```typescript
@SubscribeMessage('createRoom')
handleCreateRoom(
  @MessageBody() data: { name: string },
  @ConnectedSocket() client: Socket,
): WsResponse<any> {
  const room = this.chatService.createRoom(data.name);
  client.join(room.id);
  return { event: 'roomCreated', data: room };
}
```

## Rooms & Namespaces

```typescript
@SubscribeMessage('joinRoom')
handleJoinRoom(
  @MessageBody() data: { roomId: string },
  @ConnectedSocket() client: Socket,
) {
  client.join(data.roomId);
  this.server.to(data.roomId).emit('userJoined', {
    userId: client.id,
    roomId: data.roomId,
  });
}

@SubscribeMessage('leaveRoom')
handleLeaveRoom(
  @MessageBody() data: { roomId: string },
  @ConnectedSocket() client: Socket,
) {
  client.leave(data.roomId);
  this.server.to(data.roomId).emit('userLeft', { userId: client.id });
}

broadcastToRoom(roomId: string, event: string, data: any) {
  this.server.to(roomId).emit(event, data);
}

broadcastExceptSender(client: Socket, roomId: string, event: string, data: any) {
  client.to(roomId).emit(event, data);
}

broadcastToAll(event: string, data: any) {
  this.server.emit(event, data);
}
```

### Typing Indicator Example

```typescript
@SubscribeMessage('typing')
handleTyping(
  @MessageBody() data: { roomId: string; isTyping: boolean },
  @ConnectedSocket() client: Socket,
) {
  client.to(data.roomId).emit('userTyping', {
    userId: client.id,
    isTyping: data.isTyping,
  });
}
```

## Guards & Interceptors

Guards and interceptors work with WebSocket gateways:

```typescript
@Injectable()
export class WsJwtGuard implements CanActivate {
  constructor(private jwtService: JwtService) {}

  canActivate(context: ExecutionContext): boolean {
    const client = context.switchToWs().getClient<Socket>();
    const token = client.handshake.auth?.token;

    try {
      const payload = this.jwtService.verify(token);
      client.data.user = payload;
      return true;
    } catch {
      throw new WsException('Unauthorized');
    }
  }
}

@WebSocketGateway()
@UseGuards(WsJwtGuard)
export class ChatGateway {
  @SubscribeMessage('message')
  handleMessage(
    @ConnectedSocket() client: Socket,
    @MessageBody() data: any,
  ) {
    const user = client.data.user;
    // user is available from the guard
  }
}
```

### WS Exception Filter

```typescript
@Catch(WsException)
export class WsExceptionFilter implements ExceptionFilter {
  catch(exception: WsException, host: ArgumentsHost) {
    const client = host.switchToWs().getClient<Socket>();
    client.emit('error', {
      message: exception.getError(),
      timestamp: new Date().toISOString(),
    });
  }
}
```

## WS Adapters

### Using ws instead of Socket.IO

```bash
npm install @nestjs/platform-ws ws
```

```typescript
import { WsAdapter } from '@nestjs/platform-ws';

const app = await NestFactory.create(AppModule);
app.useWebSocketAdapter(new WsAdapter(app));
```

### Custom Redis Adapter (scaling)

```typescript
import { IoAdapter } from '@nestjs/platform-socket.io';
import { createAdapter } from '@socket.io/redis-adapter';
import { createClient } from 'redis';

export class RedisIoAdapter extends IoAdapter {
  private adapterConstructor: ReturnType<typeof createAdapter>;

  async connectToRedis(): Promise<void> {
    const pubClient = createClient({ url: 'redis://localhost:6379' });
    const subClient = pubClient.duplicate();
    await Promise.all([pubClient.connect(), subClient.connect()]);
    this.adapterConstructor = createAdapter(pubClient, subClient);
  }

  createIOServer(port: number, options?: any) {
    const server = super.createIOServer(port, options);
    server.adapter(this.adapterConstructor);
    return server;
  }
}

// main.ts
const redisAdapter = new RedisIoAdapter(app);
await redisAdapter.connectToRedis();
app.useWebSocketAdapter(redisAdapter);
```

## EventEmitter2

Internal event-driven communication between modules:

```bash
npm install @nestjs/event-emitter
```

```typescript
// app.module.ts
import { EventEmitterModule } from '@nestjs/event-emitter';

@Module({
  imports: [EventEmitterModule.forRoot()],
})
export class AppModule {}
```

### Emitting Events

```typescript
import { EventEmitter2 } from '@nestjs/event-emitter';

@Injectable()
export class OrdersService {
  constructor(private eventEmitter: EventEmitter2) {}

  async create(dto: CreateOrderDto): Promise<Order> {
    const order = await this.ordersRepo.save(dto);

    this.eventEmitter.emit('order.created', new OrderCreatedEvent(order));
    return order;
  }
}
```

### Listening to Events

```typescript
import { OnEvent } from '@nestjs/event-emitter';

@Injectable()
export class NotificationsListener {
  @OnEvent('order.created')
  handleOrderCreated(event: OrderCreatedEvent) {
    this.emailService.sendOrderConfirmation(event.order);
  }

  @OnEvent('order.*')
  handleAllOrderEvents(event: any) {
    this.logger.log('Order event received', event);
  }

  @OnEvent('order.created', { async: true })
  async handleOrderCreatedAsync(event: OrderCreatedEvent) {
    await this.analyticsService.trackPurchase(event.order);
  }
}
```

## Server-Sent Events (SSE)

One-way streaming from server to client over HTTP:

```typescript
import { Sse, MessageEvent } from '@nestjs/common';
import { Observable, fromEvent, map } from 'rxjs';

@Controller('notifications')
export class NotificationsController {
  constructor(private eventEmitter: EventEmitter2) {}

  @Sse('stream')
  stream(): Observable<MessageEvent> {
    return fromEvent(this.eventEmitter, 'notification').pipe(
      map((data: any) => ({
        data: JSON.stringify(data),
        type: 'notification',
      })),
    );
  }
}
```

Client-side:
```typescript
const source = new EventSource('/notifications/stream');
source.addEventListener('notification', (event) => {
  const data = JSON.parse(event.data);
  console.log('Notification:', data);
});
```

## CQRS Basics

```bash
npm install @nestjs/cqrs
```

```typescript
@Module({
  imports: [CqrsModule],
  providers: [CreateOrderHandler, OrderCreatedHandler],
})
export class OrdersModule {}

// Command
export class CreateOrderCommand {
  constructor(
    public readonly userId: number,
    public readonly items: OrderItem[],
  ) {}
}

// Command Handler
@CommandHandler(CreateOrderCommand)
export class CreateOrderHandler implements ICommandHandler<CreateOrderCommand> {
  constructor(private eventBus: EventBus) {}

  async execute(command: CreateOrderCommand): Promise<Order> {
    const order = await this.ordersRepo.save(command);
    this.eventBus.publish(new OrderCreatedEvent(order));
    return order;
  }
}

// Query
export class GetOrderQuery {
  constructor(public readonly orderId: number) {}
}

@QueryHandler(GetOrderQuery)
export class GetOrderHandler implements IQueryHandler<GetOrderQuery> {
  async execute(query: GetOrderQuery): Promise<Order> {
    return this.ordersRepo.findOne(query.orderId);
  }
}

// Controller
@Controller('orders')
export class OrdersController {
  constructor(
    private commandBus: CommandBus,
    private queryBus: QueryBus,
  ) {}

  @Post()
  create(@Body() dto: CreateOrderDto) {
    return this.commandBus.execute(new CreateOrderCommand(dto.userId, dto.items));
  }

  @Get(':id')
  findOne(@Param('id', ParseIntPipe) id: number) {
    return this.queryBus.execute(new GetOrderQuery(id));
  }
}
```

## Common Pitfalls

1. **CORS for WebSockets** — must configure CORS in the `@WebSocketGateway()` options, not in main.ts
2. **Socket.IO version mismatch** — client and server Socket.IO major versions must match
3. **Multiple instances** — in-memory Socket.IO doesn't scale; use Redis adapter for horizontal scaling
4. **Event listener memory leaks** — unsubscribe from EventEmitter2 in `onModuleDestroy`
5. **SSE connection limits** — browsers limit SSE connections per domain (usually 6); use WebSockets for many connections
6. **WsException not caught by HTTP filters** — use separate WS exception filters
