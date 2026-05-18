# Bun -- WebSockets

> Source: [bun.sh/docs/api/websockets](https://bun.sh/docs/api/websockets) | Native WebSocket server and pub/sub

## Table of Contents

- [WebSocket Server with Bun.serve()](#websocket-server-with-bunserve)
- [Upgrading HTTP to WebSocket](#upgrading-http-to-websocket)
- [WebSocket Handler Methods](#websocket-handler-methods)
- [Sending Messages](#sending-messages)
- [Pub/Sub System](#pubsub-system)
- [Per-Socket Data](#per-socket-data)
- [Compression](#compression)
- [Backpressure Handling](#backpressure-handling)
- [Client-Side WebSocket](#client-side-websocket)
- [Scalable Chat Pattern](#scalable-chat-pattern)
- [Common Pitfalls](#common-pitfalls)

---

## WebSocket Server with Bun.serve()

Bun has native WebSocket support built into `Bun.serve()` -- no external packages needed.

```typescript
const server = Bun.serve({
  port: 3000,
  fetch(req, server) {
    if (new URL(req.url).pathname === "/ws") {
      const upgraded = server.upgrade(req);
      if (!upgraded) return new Response("Upgrade failed", { status: 400 });
      return undefined;
    }
    return new Response("HTTP endpoint");
  },
  websocket: {
    open(ws) { console.log("Client connected"); },
    message(ws, message) { ws.send(`Echo: ${message}`); },
    close(ws, code, reason) { console.log(`Disconnected: ${code}`); },
  },
});
```

### Configuration options

```typescript
Bun.serve({
  fetch(req, server) { /* ... */ },
  websocket: {
    open(ws) {},
    message(ws, message) {},
    close(ws, code, reason) {},
    drain(ws) {},           // Backpressure relieved
    ping(ws, data) {},
    pong(ws, data) {},

    maxPayloadLength: 16 * 1024 * 1024,  // 16 MB max message
    idleTimeout: 120,                      // Seconds before closing idle
    backpressureLimit: 1024 * 1024,        // 1 MB threshold
    closeOnBackpressureLimit: false,
    sendPings: true,                       // Auto ping/pong
    perMessageDeflate: true,               // Compression
  },
});
```

## Upgrading HTTP to WebSocket

The upgrade happens inside `fetch`. You can inspect the HTTP request (headers, cookies, auth) before deciding whether to upgrade.

### Authenticated upgrade with data

```typescript
interface SocketData {
  userId: string;
  username: string;
  role: "admin" | "user";
}

Bun.serve<SocketData>({
  async fetch(req, server) {
    if (new URL(req.url).pathname !== "/ws") return new Response("Not found", { status: 404 });

    const token = req.headers.get("Authorization")?.replace("Bearer ", "");
    if (!token) return Response.json({ error: "Missing token" }, { status: 401 });

    const user = await verifyToken(token);
    if (!user) return Response.json({ error: "Invalid token" }, { status: 401 });

    const upgraded = server.upgrade(req, {
      data: { userId: user.id, username: user.name, role: user.role },
    });
    if (!upgraded) return new Response("Upgrade failed", { status: 400 });
    return undefined;
  },
  websocket: {
    open(ws) { console.log(`${ws.data.username} connected`); },
    message(ws, msg) { console.log(`Message from ${ws.data.username}: ${msg}`); },
  },
});
```

### Upgrade with query parameters

```typescript
Bun.serve<{ room: string; name: string }>({
  fetch(req, server) {
    const url = new URL(req.url);
    if (url.pathname !== "/ws") return new Response("Not found", { status: 404 });

    server.upgrade(req, {
      data: {
        room: url.searchParams.get("room") ?? "general",
        name: url.searchParams.get("name") ?? "Anonymous",
      },
    });
    return undefined;
  },
  websocket: {
    open(ws) {
      ws.subscribe(ws.data.room);
      ws.publish(ws.data.room, `${ws.data.name} joined`);
    },
    message(ws, msg) { ws.publish(ws.data.room, `${ws.data.name}: ${msg}`); },
    close(ws) {
      ws.publish(ws.data.room, `${ws.data.name} left`);
      ws.unsubscribe(ws.data.room);
    },
  },
});
```

## WebSocket Handler Methods

### message(ws, message)

The `message` parameter is `string` (text) or `Buffer` (binary) depending on what the client sent.

```typescript
message(ws, message) {
  if (typeof message === "string") {
    const parsed = JSON.parse(message);
    switch (parsed.type) {
      case "chat": ws.publish("chat", message); break;
      case "ping": ws.send(JSON.stringify({ type: "pong", timestamp: Date.now() })); break;
    }
  } else {
    // Binary message (Buffer)
    console.log(`Binary: ${message.byteLength} bytes`);
    ws.send(message);
  }
}
```

### close(ws, code, reason)

Standard close codes: 1000 (normal), 1001 (going away), 1006 (abnormal), 1011 (unexpected).

### drain(ws)

Called when the send buffer has been flushed. Use to resume sending after backpressure.

## Sending Messages

```typescript
// Text
ws.send("Hello, client!");
ws.send(JSON.stringify({ type: "notification", title: "New message" }));

// Binary
ws.send(Buffer.from([0x01, 0x02, 0x03]));
ws.send(new Uint8Array([72, 101, 108, 108, 111]));

// Return value indicates result
const result = ws.send("data");
//  > 0 = bytes sent successfully
//  0   = message was queued (backpressure)
//  -1  = connection is closed
```

## Pub/Sub System

Bun includes a built-in pub/sub system. Topics are lightweight string identifiers with no external broker required.

### Subscribe, publish, and unsubscribe

```typescript
Bun.serve<{ username: string }>({
  fetch(req, server) {
    const url = new URL(req.url);
    if (url.pathname === "/ws") {
      server.upgrade(req, {
        data: { username: url.searchParams.get("name") ?? "Anonymous" },
      });
      return undefined;
    }
    return new Response("Not found", { status: 404 });
  },
  websocket: {
    open(ws) {
      ws.subscribe("global-chat");
      ws.subscribe(`user:${ws.data.username}`);
      ws.publish("global-chat", JSON.stringify({
        type: "system", message: `${ws.data.username} joined`,
      }));
    },
    message(ws, msg) {
      // publish sends to all subscribers EXCEPT the sender
      ws.publish("global-chat", JSON.stringify({
        type: "chat", from: ws.data.username, message: String(msg),
      }));
    },
    close(ws) {
      ws.publish("global-chat", JSON.stringify({
        type: "system", message: `${ws.data.username} left`,
      }));
    },
  },
});
```

### Server-level publish (from HTTP endpoints)

```typescript
const server = Bun.serve({
  async fetch(req, server) {
    const url = new URL(req.url);

    if (req.method === "POST" && url.pathname === "/api/broadcast") {
      const body = await req.json();
      const count = server.publish("global-chat", JSON.stringify({
        type: "broadcast", message: body.message,
      }));
      return Response.json({ delivered_to: count });
    }

    if (url.pathname === "/ws") { server.upgrade(req); return undefined; }
    return new Response("Not found", { status: 404 });
  },
  websocket: {
    open(ws) { ws.subscribe("global-chat"); },
    message(ws, msg) { ws.publish("global-chat", String(msg)); },
  },
});
```

### Subscriber management

```typescript
const count = server.subscriberCount("global-chat");       // Topic subscriber count
const isSub = ws.isSubscribed("global-chat");               // Per-socket check
```

## Per-Socket Data

Type custom state via the generic parameter of `Bun.serve<T>()`. Set data during `server.upgrade()`, mutate properties during the connection lifetime.

```typescript
interface Session {
  userId: string;
  username: string;
  rooms: Set<string>;
}

Bun.serve<Session>({
  fetch(req, server) {
    server.upgrade(req, {
      data: { userId: crypto.randomUUID(), username: "Alice", rooms: new Set() },
    });
    return undefined;
  },
  websocket: {
    message(ws, msg) {
      const parsed = JSON.parse(String(msg));
      if (parsed.action === "join") {
        ws.data.rooms.add(parsed.room);
        ws.subscribe(parsed.room);
      }
      if (parsed.action === "status") {
        ws.send(JSON.stringify({ userId: ws.data.userId, rooms: [...ws.data.rooms] }));
      }
    },
  },
});
```

## Compression

```typescript
// Simple toggle
Bun.serve({
  websocket: {
    perMessageDeflate: true,
    message(ws, msg) { ws.send(msg); },
  },
  fetch(req, server) { server.upgrade(req); return undefined; },
});

// Fine-grained: compress: "shared"|"dedicated"|"disable", threshold: min bytes
Bun.serve({
  websocket: {
    perMessageDeflate: { compress: "shared", decompress: "shared", threshold: 860 },
    message(ws, msg) { ws.send(msg); },
  },
  fetch(req, server) { server.upgrade(req); return undefined; },
});
```

| Scenario | Recommendation |
|----------|---------------|
| Short chat messages | Disable -- overhead exceeds savings |
| JSON API responses (>1KB) | Enable -- good compression ratio |
| Binary data (images, audio) | Disable -- already compressed |
| Large JSON streams | Enable -- significant bandwidth savings |
| Low-latency gaming | Disable -- compression adds latency |

## Backpressure Handling

```typescript
Bun.serve<{ queue: string[] }>({
  websocket: {
    backpressureLimit: 1024 * 1024,
    message(ws, msg) {
      const buffered = ws.getBufferedAmount();
      if (buffered > 512 * 1024) {
        ws.data.queue.push(String(msg)); // Defer sending
        return;
      }
      ws.publish("feed", String(msg));
    },
    drain(ws) {
      while (ws.data.queue.length > 0) {
        const queued = ws.data.queue.shift()!;
        if (ws.send(queued) === 0) { ws.data.queue.unshift(queued); break; }
      }
    },
  },
  fetch(req, server) {
    server.upgrade(req, { data: { queue: [] } });
    return undefined;
  },
});
```

## Client-Side WebSocket

Bun supports the standard browser `WebSocket` API (useful for Bun-based clients or tests).

```typescript
// client.ts -- run with: bun client.ts
const ws = new WebSocket("ws://localhost:3000/ws?name=Alice");

ws.addEventListener("open", () => {
  console.log("Connected");
  ws.send(JSON.stringify({ type: "chat", message: "Hello!" }));
});
ws.addEventListener("message", (event) => console.log("Received:", JSON.parse(event.data)));
ws.addEventListener("close", (event) => console.log(`Disconnected: code=${event.code}`));
```

## Scalable Chat Pattern

```typescript
const onlineUsers = new Map<string, { name: string }>();

const server = Bun.serve<{ id: string; name: string; rooms: Set<string> }>({
  port: 3000,
  fetch(req, server) {
    const url = new URL(req.url);
    if (url.pathname !== "/ws") return new Response("Not found", { status: 404 });
    const name = url.searchParams.get("name");
    if (!name) return Response.json({ error: "Name required" }, { status: 400 });
    server.upgrade(req, { data: { id: crypto.randomUUID(), name, rooms: new Set() } });
    return undefined;
  },
  websocket: {
    open(ws) {
      onlineUsers.set(ws.data.id, { name: ws.data.name });
      ws.subscribe("notifications");
      ws.send(JSON.stringify({ type: "connected", userId: ws.data.id }));
    },
    message(ws, raw) {
      const msg = JSON.parse(String(raw));
      switch (msg.action) {
        case "join":
          ws.data.rooms.add(msg.room);
          ws.subscribe(msg.room);
          ws.publish(msg.room, JSON.stringify({ type: "system", message: `${ws.data.name} joined` }));
          break;
        case "leave":
          ws.publish(msg.room, JSON.stringify({ type: "system", message: `${ws.data.name} left` }));
          ws.data.rooms.delete(msg.room);
          ws.unsubscribe(msg.room);
          break;
        case "message":
          if (!ws.data.rooms.has(msg.room)) {
            ws.send(JSON.stringify({ type: "error", message: "Not in this room" }));
            return;
          }
          ws.publish(msg.room, JSON.stringify({
            type: "chat", room: msg.room, from: ws.data.name, message: msg.text,
          }));
          break;
      }
    },
    close(ws) {
      for (const room of ws.data.rooms) {
        ws.publish(room, JSON.stringify({ type: "system", message: `${ws.data.name} left` }));
      }
      onlineUsers.delete(ws.data.id);
    },
  },
});
```

## Common Pitfalls

### 1. Returning a Response after upgrade

The `fetch` handler must return `undefined` after a successful upgrade. Returning a `Response` breaks the WebSocket handshake.

### 2. Expecting publish to include the sender

`ws.publish()` sends to all subscribers *except* the sender. If the sender should also see the message, send it separately with `ws.send()`.

### 3. Passing objects directly to ws.send()

`ws.send()` accepts strings and binary data only. Passing an object results in `[object Object]`. Always `JSON.stringify()` first.

### 4. Not wrapping JSON.parse in try-catch

Clients can send malformed JSON. Always handle parse errors:

```typescript
message(ws, msg) {
  try {
    const parsed = JSON.parse(String(msg));
  } catch {
    ws.send(JSON.stringify({ type: "error", message: "Invalid JSON" }));
  }
}
```

### 5. Trying to replace ws.data entirely

You can mutate properties on `ws.data` but cannot reassign it. Use `ws.data.prop = value`, not `ws.data = newObject`.

### 6. Memory leaks from tracking maps

If you track connected users in a `Map` or `Set`, always remove entries in the `close` handler. Bun does not clean up application-level state automatically.

### 7. Not checking readyState on the client

Client-side code should verify the connection is open (`ws.readyState === WebSocket.OPEN`) before calling `ws.send()`.
