# Socket.IO TypeScript Support

> Source: https://socket.io/docs/v4/typescript/

## Table of Contents

- [Type System Overview](#type-system-overview)
- [Defining Event Interfaces](#defining-event-interfaces)
- [Server-Side Types](#server-side-types)
- [Client-Side Types](#client-side-types)
- [Typed Namespaces](#typed-namespaces)
- [Inter-Server Events](#inter-server-events)
- [Socket Data Typing](#socket-data-typing)
- [Common Patterns](#common-patterns)

## Type System Overview

Socket.IO provides first-class TypeScript support through four generic interfaces:

1. **`ClientToServerEvents`** — events the client sends to the server
2. **`ServerToClientEvents`** — events the server sends to clients
3. **`InterServerEvents`** — events between servers in multi-node setups
4. **`SocketData`** — type for the `socket.data` attribute

These interfaces provide IDE autocomplete and compile-time type checking for event names, payloads, and acknowledgement callbacks.

## Defining Event Interfaces

```typescript
interface ServerToClientEvents {
  "chat:message": (msg: { user: string; text: string; timestamp: number }) => void;
  "user:joined": (username: string) => void;
  "user:left": (username: string) => void;
  "room:members": (members: string[]) => void;
}

interface ClientToServerEvents {
  "chat:send": (text: string, callback: (result: { id: string }) => void) => void;
  "room:join": (roomName: string) => void;
  "room:leave": (roomName: string) => void;
}

interface InterServerEvents {
  ping: () => void;
  "user:count": (count: number) => void;
}

interface SocketData {
  userId: string;
  username: string;
  role: "user" | "admin" | "moderator";
  joinedAt: Date;
}
```

## Server-Side Types

### Typed Server

```typescript
import { Server } from "socket.io";

const io = new Server<
  ClientToServerEvents,
  ServerToClientEvents,
  InterServerEvents,
  SocketData
>(httpServer);

io.on("connection", (socket) => {
  // socket is fully typed

  // Autocomplete for event names and payloads
  socket.emit("chat:message", {
    user: "Alice",
    text: "Hello!",
    timestamp: Date.now()
  });

  // Type error: unknown event
  // socket.emit("unknown:event", data); // TS error

  // Type error: wrong payload shape
  // socket.emit("chat:message", "wrong"); // TS error

  // Typed listener with callback
  socket.on("chat:send", (text, callback) => {
    // text is string, callback is (result: { id: string }) => void
    callback({ id: "msg-123" });
  });

  // Typed socket.data
  socket.data.userId = "user-123";
  socket.data.role = "admin";
  // socket.data.role = "superadmin"; // TS error
});

// Typed broadcasting
io.emit("user:joined", "Alice");
io.to("room1").emit("chat:message", {
  user: "System",
  text: "Welcome!",
  timestamp: Date.now()
});
```

### Typed Namespace

```typescript
import { Server, Namespace } from "socket.io";

const io = new Server<
  ClientToServerEvents,
  ServerToClientEvents,
  InterServerEvents,
  SocketData
>(httpServer);

// Namespace inherits types
const chatNsp: Namespace<
  ClientToServerEvents,
  ServerToClientEvents,
  InterServerEvents,
  SocketData
> = io.of("/chat");
```

## Client-Side Types

```typescript
import { io, Socket } from "socket.io-client";

// Client reverses the order: ServerToClient first, then ClientToServer
const socket: Socket<ServerToClientEvents, ClientToServerEvents> = io(
  "http://localhost:3000"
);

// Typed listener
socket.on("chat:message", (msg) => {
  // msg is { user: string; text: string; timestamp: number }
  console.log(`${msg.user}: ${msg.text}`);
});

// Typed emit with callback
socket.emit("chat:send", "Hello!", (result) => {
  // result is { id: string }
  console.log(`Message sent: ${result.id}`);
});

// Promise-based with types
const result = await socket.emitWithAck("chat:send", "Hello!");
// result is { id: string }
```

## Typed Namespaces

Each namespace can define its own event interfaces:

```typescript
// Chat namespace events
interface ChatClientToServer {
  "message:send": (text: string) => void;
  "typing:start": () => void;
  "typing:stop": () => void;
}

interface ChatServerToClient {
  "message:receive": (msg: { from: string; text: string }) => void;
  "typing:update": (users: string[]) => void;
}

// Admin namespace events
interface AdminClientToServer {
  "user:ban": (userId: string, reason: string) => void;
  "stats:request": (callback: (stats: SystemStats) => void) => void;
}

interface AdminServerToClient {
  "user:banned": (userId: string) => void;
  "stats:update": (stats: SystemStats) => void;
}

// Server
const chatNsp = io.of("/chat") as Namespace<
  ChatClientToServer,
  ChatServerToClient
>;
const adminNsp = io.of("/admin") as Namespace<
  AdminClientToServer,
  AdminServerToClient
>;

// Clients
const chatSocket: Socket<ChatServerToClient, ChatClientToServer> = io("/chat");
const adminSocket: Socket<AdminServerToClient, AdminClientToServer> = io("/admin");
```

## Inter-Server Events

For multi-node setups, type the events exchanged between servers:

```typescript
interface InterServerEvents {
  ping: () => void;
  "user:count": (count: number) => void;
  "broadcast:message": (msg: { room: string; event: string; data: unknown }) => void;
}

const io = new Server<
  ClientToServerEvents,
  ServerToClientEvents,
  InterServerEvents,
  SocketData
>(httpServer);

// io.serverSideEmit is typed
io.serverSideEmit("user:count", 42);
```

## Socket Data Typing

```typescript
interface SocketData {
  userId: string;
  username: string;
  role: "user" | "admin";
}

io.on("connection", (socket) => {
  // Typed data access
  socket.data.userId = "123";
  socket.data.username = "Alice";
  socket.data.role = "admin";

  // Available in fetchSockets
  const sockets = await io.fetchSockets();
  for (const s of sockets) {
    console.log(s.data.username); // typed
  }
});
```

## Common Patterns

### Shared Type Package

```typescript
// types/socket-events.ts — shared between client and server
export interface ServerToClientEvents {
  "chat:message": (msg: ChatMessage) => void;
  "notification": (n: Notification) => void;
}

export interface ClientToServerEvents {
  "chat:send": (text: string, ack: (id: string) => void) => void;
}

export interface ChatMessage {
  id: string;
  user: string;
  text: string;
  timestamp: number;
}
```

### Type-Safe Event Map Helper

```typescript
type EventNames<T> = keyof T & string;
type EventParams<T, K extends keyof T> = T[K] extends (...args: infer P) => void
  ? P
  : never;
```

### Validation Reminder

TypeScript types are compile-time only. Always validate at runtime:

```typescript
import { z } from "zod";

const ChatSendSchema = z.object({
  text: z.string().min(1).max(1000),
});

socket.on("chat:send", (text, callback) => {
  const result = ChatSendSchema.safeParse({ text });
  if (!result.success) {
    callback({ error: "Invalid message" });
    return;
  }
  // proceed with validated data
});
```
