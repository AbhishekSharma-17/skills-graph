# Socket.IO Server Setup

> Source: https://socket.io/docs/v4/server-installation/ | https://socket.io/docs/v4/server-options/

## Table of Contents

- [Installation](#installation)
- [Server Initialization](#server-initialization)
- [Framework Integration](#framework-integration)
- [Server Options](#server-options)
- [Engine.IO Options](#engineio-options)
- [Server Class API](#server-class-api)
- [Socket Instance](#socket-instance)
- [Handshake Object](#handshake-object)

## Installation

```bash
npm install socket.io
# or
yarn add socket.io
# or
pnpm add socket.io
```

## Server Initialization

### Standalone Server

```javascript
import { Server } from "socket.io";

const io = new Server(3000, {
  cors: { origin: "http://localhost:5173" }
});

io.on("connection", (socket) => {
  // handle connection
});
```

### With HTTP Server

```javascript
import { createServer } from "node:http";
import { Server } from "socket.io";

const httpServer = createServer();
const io = new Server(httpServer);

httpServer.listen(3000);
```

### With HTTPS

```javascript
import { createServer } from "node:https";
import { readFileSync } from "node:fs";
import { Server } from "socket.io";

const httpsServer = createServer({
  key: readFileSync("key.pem"),
  cert: readFileSync("cert.pem")
});

const io = new Server(httpsServer);
httpsServer.listen(3000);
```

## Framework Integration

### Express

```javascript
import express from "express";
import { createServer } from "node:http";
import { Server } from "socket.io";

const app = express();
const httpServer = createServer(app);
const io = new Server(httpServer);

app.get("/", (req, res) => {
  res.sendFile("index.html");
});

io.on("connection", (socket) => {
  // handle connection
});

httpServer.listen(3000);
// IMPORTANT: call httpServer.listen(), NOT app.listen()
```

### Koa

```javascript
import Koa from "koa";
import { createServer } from "node:http";
import { Server } from "socket.io";

const app = new Koa();
const httpServer = createServer(app.callback());
const io = new Server(httpServer);

httpServer.listen(3000);
```

### Fastify

```javascript
import Fastify from "fastify";
import { Server } from "socket.io";

const fastify = Fastify();
await fastify.listen({ port: 3000 });

const io = new Server(fastify.server, {
  cors: { origin: "*" }
});
```

## Server Options

### Socket.IO Options

| Option | Default | Description |
|--------|---------|-------------|
| `path` | `/socket.io/` | Server path for Socket.IO requests |
| `serveClient` | `true` | Serve bundled client JS at path |
| `adapter` | In-memory | Adapter for multi-server setups |
| `parser` | `socket.io-parser` | Custom message parser |
| `connectTimeout` | `45000` | Ms before disconnecting unjoined client |
| `connectionStateRecovery` | `undefined` | Enable session recovery config |
| `cleanupEmptyChildNamespaces` | `false` | Auto-remove empty dynamic namespaces |

### CORS Configuration

```javascript
const io = new Server(httpServer, {
  cors: {
    origin: ["https://myapp.com", "https://staging.myapp.com"],
    methods: ["GET", "POST"],
    credentials: true,
    allowedHeaders: ["my-custom-header"]
  }
});
```

## Engine.IO Options

| Option | Default | Description |
|--------|---------|-------------|
| `pingInterval` | `25000` | Heartbeat interval (ms) |
| `pingTimeout` | `20000` | Pong response timeout (ms) |
| `maxHttpBufferSize` | `1e6` (1 MB) | Max message size before disconnect |
| `transports` | `["polling", "websocket"]` | Allowed transports |
| `allowUpgrades` | `true` | Allow transport upgrades |
| `httpCompression` | `true` | Compress HTTP long-polling |
| `perMessageDeflate` | `false` | WebSocket compression |
| `cors` | `undefined` | CORS configuration |
| `cookie` | `false` | Cookie config for session affinity |
| `allowEIO3` | `false` | Compatibility with v2 clients |
| `allowRequest` | `undefined` | Custom request validation function |

## Server Class API

### Key Methods

```javascript
// Emit to all connected clients (main namespace)
io.emit("event", data);

// Target specific rooms
io.to("room1").emit("event", data);
io.to("room1").to("room2").emit("event", data); // union

// Exclude rooms
io.except("room1").emit("event", data);

// Access/create namespace
const nsp = io.of("/admin");

// Middleware for main namespace
io.use((socket, next) => {
  // validate
  next();
});

// Server-wide operations
io.socketsJoin("room1");         // all sockets join room
io.socketsLeave("room1");       // all sockets leave room
io.disconnectSockets();          // disconnect all
const sockets = await io.fetchSockets(); // get all sockets

// In a specific room
io.in("room1").socketsJoin("room2");
io.in("room1").disconnectSockets(true); // true = close underlying connection
```

### Server Events

```javascript
io.on("connection", (socket) => {
  // new client connected
});

io.on("new_namespace", (namespace) => {
  // dynamic namespace created
});

io.engine.on("connection_error", (err) => {
  console.log(err.req);      // the request
  console.log(err.code);     // error code
  console.log(err.message);  // error message
  console.log(err.context);  // additional context
});
```

## Socket Instance

### Properties

```javascript
io.on("connection", (socket) => {
  socket.id;          // unique session ID (ephemeral — changes on reconnect)
  socket.handshake;   // connection metadata
  socket.rooms;       // Set of joined rooms (includes own ID)
  socket.data;        // arbitrary storage, shared via fetchSockets()
  socket.conn;        // underlying Engine.IO socket
  socket.request;     // HTTP IncomingMessage
  socket.recovered;   // true if session was recovered
});
```

### Socket Methods

```javascript
// Events
socket.emit("event", data);
socket.on("event", (data) => {});
socket.once("event", (data) => {});

// Rooms
socket.join("room1");
socket.join(["room1", "room2"]);
socket.leave("room1");

// Broadcasting (to room, excluding sender)
socket.to("room1").emit("event", data);
socket.broadcast.emit("event", data); // all except sender

// Catch-all listeners
socket.onAny((eventName, ...args) => {});
socket.onAnyOutgoing((eventName, ...args) => {});

// Disconnect
socket.disconnect();     // keep transport open
socket.disconnect(true); // close transport

// Per-packet middleware
socket.use(([event, ...args], next) => {
  // runs for every incoming event on this socket
  next();
});
```

### Socket Events

```javascript
socket.on("disconnect", (reason, details) => {
  // reason: "server namespace disconnect", "client namespace disconnect",
  //         "server shutting down", "ping timeout", "transport close",
  //         "transport error", "parse error"
});

socket.on("disconnecting", (reason) => {
  // socket.rooms still available here
  for (const room of socket.rooms) {
    socket.to(room).emit("user left", socket.id);
  }
});
```

## Handshake Object

```javascript
socket.handshake = {
  headers: {},          // request headers
  query: {},            // query parameters
  auth: {},             // auth payload from client
  time: "...",          // connection timestamp
  address: "...",       // client IP address
  xdomain: false,       // cross-domain request
  secure: false,        // HTTPS connection
  issued: 1234567890,   // Unix timestamp
  url: "/socket.io/",   // request URL
}
```

## Express Middleware Compatibility

```javascript
import session from "express-session";

const sessionMiddleware = session({ secret: "keyboard cat" });

// Apply Express middleware to Engine.IO
io.engine.use(sessionMiddleware);

io.on("connection", (socket) => {
  const session = socket.request.session;
});
```
