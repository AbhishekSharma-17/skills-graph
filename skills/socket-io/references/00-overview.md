# Socket.IO Overview

> Source: https://socket.io/docs/v4/ | Version: 4.8.3

## What Is Socket.IO?

Socket.IO is a library that enables real-time, bidirectional, event-based communication between web clients and servers. It consists of two parts:

- **Server library** (`socket.io`) — runs on Node.js
- **Client library** (`socket.io-client`) — runs in browsers or Node.js

Socket.IO is NOT a plain WebSocket implementation. It provides a higher-level API with automatic reconnection, packet buffering, acknowledgements, broadcasting, multiplexing (namespaces), and room-based message routing.

## Architecture

Socket.IO is built on two layers:

### Engine.IO (Low-Level)

Handles transport negotiation and connection lifecycle:

- **HTTP Long-Polling** — successive GET/POST requests; universally supported
- **WebSocket** — persistent bidirectional connection; ~99.84% browser support
- **WebTransport** — newer protocol; ~84.48% browser support; better in lossy networks

Connections start with HTTP long-polling for reliability, then upgrade to WebSocket. This avoids the failure modes of WebSocket-first approaches behind proxies/firewalls.

### Socket.IO (High-Level)

Built on top of Engine.IO, adds:

- Automatic reconnection with exponential backoff
- Packet buffering during disconnection
- Acknowledgements (request-response pattern)
- Broadcasting to all or subsets of clients
- Multiplexing via namespaces
- Room-based targeted messaging
- Connection state recovery

## When to Use Socket.IO

**Good fit:**
- Chat applications and messaging
- Live notifications and activity feeds
- Collaborative editing (Google Docs-style)
- Live dashboards and monitoring
- Multiplayer game state synchronization
- IoT device communication
- Auction/bidding systems
- Live location tracking

**Not ideal for:**
- Simple REST API calls (use HTTP)
- One-directional server push only (consider SSE)
- Binary streaming (consider WebRTC or raw WebSocket)
- Serverless environments (connections are long-lived)

## Installation

```bash
# Server (Node.js)
npm install socket.io

# Client (browser or Node.js)
npm install socket.io-client

# CDN (browser)
# <script src="https://cdn.socket.io/4.8.3/socket.io.min.js"></script>
```

## Minimal Example

### Server

```javascript
import { createServer } from "node:http";
import { Server } from "socket.io";

const httpServer = createServer();
const io = new Server(httpServer, {
  cors: { origin: "http://localhost:3000" }
});

io.on("connection", (socket) => {
  console.log(`Client connected: ${socket.id}`);

  socket.on("chat message", (msg) => {
    io.emit("chat message", msg); // broadcast to all
  });

  socket.on("disconnect", (reason) => {
    console.log(`Client disconnected: ${reason}`);
  });
});

httpServer.listen(3000);
```

### Client

```javascript
import { io } from "socket.io-client";

const socket = io("http://localhost:3000");

socket.on("connect", () => {
  console.log(`Connected: ${socket.id}`);
  socket.emit("chat message", "Hello!");
});

socket.on("chat message", (msg) => {
  console.log(`Received: ${msg}`);
});

socket.on("disconnect", (reason) => {
  console.log(`Disconnected: ${reason}`);
});
```

## Connection Lifecycle

```
Client                          Server
  |                               |
  |--- HTTP long-polling -------->|  (handshake)
  |<-- session id, config --------|
  |                               |
  |--- WebSocket upgrade -------->|  (transport upgrade)
  |<-- 101 Switching Protocols ---|
  |                               |
  |<========= events ==========>|   (bidirectional)
  |                               |
  |<-- PING --------------------- |  (heartbeat)
  |--- PONG -------------------->|
  |                               |
```

### Heartbeat Mechanism

The server sends periodic PING packets (default every 25 seconds). If no PONG response arrives within `pingTimeout` (default 20 seconds), the connection is considered dead.

### Transport Upgrade

1. Connection starts with HTTP long-polling
2. Client attempts WebSocket upgrade
3. Outgoing buffer is emptied; current transport set to read-only
4. WebSocket connection is established
5. Old transport is closed

## Key Concepts Summary

| Concept | Description |
|---------|-------------|
| **Event** | Named message with optional payload and callback |
| **Room** | Server-side channel for targeted broadcasting |
| **Namespace** | Multiplexed channel over a single connection |
| **Adapter** | Component for multi-server broadcasting |
| **Middleware** | Function executed on every incoming connection |
| **Acknowledgement** | Callback-based request-response pattern |
| **Volatile** | Fire-and-forget event (dropped if not deliverable) |

## Version Compatibility

| Server | Client | Compatible |
|--------|--------|------------|
| v4.x | v4.x | Yes |
| v4.x | v3.x | Yes |
| v4.x | v2.x | Only with `allowEIO3: true` |
| v3.x | v2.x | No |

## Ecosystem

| Package | Purpose |
|---------|---------|
| `socket.io` | Server library |
| `socket.io-client` | Client library |
| `@socket.io/redis-adapter` | Redis adapter for scaling |
| `@socket.io/redis-streams-adapter` | Redis Streams adapter |
| `@socket.io/mongo-adapter` | MongoDB adapter |
| `@socket.io/postgres-adapter` | PostgreSQL adapter |
| `@socket.io/cluster-adapter` | Node.js cluster adapter |
| `@socket.io/sticky` | Sticky sessions for cluster |
| `@socket.io/admin-ui` | Admin dashboard |
