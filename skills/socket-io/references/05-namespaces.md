# Socket.IO Namespaces

> Source: https://socket.io/docs/v4/namespaces/

## What Are Namespaces?

Namespaces are communication channels that allow splitting application logic over a single shared connection. They enable multiplexing — routing multiple logical channels through one WebSocket.

Each namespace has its own isolated:
- **Event handlers** — distinct listeners per namespace
- **Rooms** — separate room groupings
- **Middlewares** — independent authentication/validation

## Main Namespace

The default namespace is `/`, accessible directly through the `io` instance:

```javascript
// These are equivalent
io.on("connection", (socket) => {});
io.of("/").on("connection", (socket) => {});
```

## Creating Namespaces

### Server-Side

```javascript
import { Server } from "socket.io";

const io = new Server(httpServer);

// Create named namespace
const adminNsp = io.of("/admin");
const chatNsp = io.of("/chat");

adminNsp.on("connection", (socket) => {
  console.log("Admin client connected");
  socket.on("admin:action", (data) => {
    // handle admin-specific events
  });
});

chatNsp.on("connection", (socket) => {
  console.log("Chat client connected");
  socket.on("message", (msg) => {
    chatNsp.emit("message", msg);
  });
});
```

### Client-Side

```javascript
import { io } from "socket.io-client";

// Connect to specific namespace
const adminSocket = io("http://localhost:3000/admin");
const chatSocket = io("http://localhost:3000/chat");

// Both share ONE WebSocket connection (multiplexed)
adminSocket.on("connect", () => { /* admin connected */ });
chatSocket.on("connect", () => { /* chat connected */ });
```

## Dynamic Namespaces

Create namespaces on-the-fly based on patterns or custom logic.

### Regex-Based

```javascript
io.of(/^\/dynamic-\d+$/).on("connection", (socket) => {
  const namespace = socket.nsp;
  console.log(`Connected to: ${namespace.name}`); // e.g., "/dynamic-42"
});

// Client connects to any matching namespace
const socket = io("/dynamic-42");
```

### Function-Based

```javascript
io.of((name, auth, next) => {
  const isAllowed = checkNamespaceAccess(name, auth);
  next(null, isAllowed); // true = allow, false = deny
}).on("connection", (socket) => {
  const namespace = socket.nsp;
  console.log(`Connected to: ${namespace.name}`);
});
```

### With Authentication

```javascript
io.of((name, auth, next) => {
  if (!auth || !auth.token) {
    return next(new Error("Authentication required"));
  }

  verifyToken(auth.token)
    .then((user) => {
      if (canAccessNamespace(user, name)) {
        next(null, true);
      } else {
        next(new Error("Forbidden"));
      }
    })
    .catch(() => next(new Error("Invalid token")));
});
```

## Namespace Middleware

Each namespace can have its own middleware chain:

```javascript
const adminNsp = io.of("/admin");

adminNsp.use((socket, next) => {
  const token = socket.handshake.auth.token;
  if (isAdmin(token)) {
    next();
  } else {
    next(new Error("Unauthorized"));
  }
});

adminNsp.on("connection", (socket) => {
  // only admin users reach here
});
```

## Namespace Properties and Methods

```javascript
const nsp = io.of("/chat");

// Properties
nsp.name;     // "/chat"
nsp.sockets;  // Map<SocketId, Socket> of connected sockets
nsp.adapter;  // the adapter instance

// Methods — same API as io.*
nsp.emit("event", data);                    // broadcast within namespace
nsp.to("room").emit("event", data);         // target room
nsp.except("room").emit("event", data);     // exclude room
nsp.use((socket, next) => { next(); });     // middleware
nsp.socketsJoin("room");                    // all sockets join room
nsp.socketsLeave("room");                   // all sockets leave room
nsp.disconnectSockets();                    // disconnect all
const sockets = await nsp.fetchSockets();   // get all sockets
```

## Auto-Cleanup of Empty Namespaces

Dynamic namespaces can leak memory if clients connect and disconnect frequently. Enable auto-cleanup:

```javascript
const io = new Server(httpServer, {
  cleanupEmptyChildNamespaces: true // v4.6.0+
});
```

When all sockets disconnect from a dynamic namespace, it is automatically removed.

## Use Cases

### Feature Separation

```javascript
const io = new Server(httpServer);

// Separate concerns into namespaces
const orders = io.of("/orders");
const support = io.of("/support");
const analytics = io.of("/analytics");

orders.on("connection", (socket) => {
  socket.on("order:create", handleCreate);
  socket.on("order:update", handleUpdate);
});

support.on("connection", (socket) => {
  socket.on("ticket:create", handleTicket);
  socket.on("ticket:reply", handleReply);
});
```

### Multi-Tenant Architecture

```javascript
// Each tenant gets its own namespace
io.of(/^\/tenant-\w+$/).on("connection", (socket) => {
  const tenantId = socket.nsp.name.replace("/tenant-", "");
  socket.data.tenantId = tenantId;

  // Events are isolated per tenant
  socket.on("data:update", (data) => {
    socket.nsp.emit("data:changed", data); // only same-tenant clients
  });
});

// Clients
const socket = io("/tenant-acme-corp");
```

### Access-Controlled Namespaces

```javascript
// Public namespace — no auth
io.of("/public").on("connection", (socket) => {
  // anyone can connect
});

// Protected namespace — requires auth
const protectedNsp = io.of("/protected");
protectedNsp.use(authMiddleware);
protectedNsp.on("connection", (socket) => {
  // only authenticated users
});

// Admin namespace — requires admin role
const adminNsp = io.of("/admin");
adminNsp.use(authMiddleware);
adminNsp.use(adminRoleMiddleware);
adminNsp.on("connection", (socket) => {
  // only admins
});
```

## Namespaces vs Rooms

| Feature | Namespace | Room |
|---------|-----------|------|
| Created by | Server code (`io.of()`) | `socket.join()` |
| Client chooses | Yes (connects to namespace) | No (server-side only) |
| Has middleware | Yes | No |
| Multiplexed | Yes (one connection) | N/A |
| Isolation | Full (events, rooms, middleware) | Partial (broadcasting scope) |
| Use case | Feature separation, auth tiers | User grouping, channels |

**Rule of thumb:** Use namespaces for architectural separation (features, access levels). Use rooms for dynamic grouping within a namespace (chat channels, document collaborators).
