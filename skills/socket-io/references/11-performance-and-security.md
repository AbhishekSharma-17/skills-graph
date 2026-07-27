# Socket.IO Performance and Security

> Source: https://socket.io/docs/v4/performance-tuning/ | https://socket.io/docs/v4/handling-cors/

## Table of Contents

- [Performance Tuning](#performance-tuning)
- [CORS Configuration](#cors-configuration)
- [Security Best Practices](#security-best-practices)
- [Memory Optimization](#memory-optimization)
- [OS-Level Tuning](#os-level-tuning)

## Performance Tuning

### WebSocket Native Add-ons

Install optional binary packages for better WebSocket performance:

```bash
npm install bufferutil utf-8-validate
```

- `bufferutil` — faster masking/unmasking of WebSocket frame payloads
- `utf-8-validate` — faster UTF-8 validation

### Custom Parser (Binary Data)

For applications sending binary data, use msgpack instead of the default JSON parser:

```bash
npm install @socket.io/msgpack-parser
```

```javascript
// Server
import { Server } from "socket.io";
import { parser } from "@socket.io/msgpack-parser";

const io = new Server(httpServer, { parser });

// Client
import { io } from "socket.io-client";
import { parser } from "@socket.io/msgpack-parser";

const socket = io("http://localhost:3000", { parser });
```

Benefits:
- Reduces number of WebSocket frames for binary data
- More compact serialization for complex objects
- Both client and server must use the same parser

### WebSocket-Only Transport

Skip HTTP long-polling for faster initial connection:

```javascript
// Server
const io = new Server(httpServer, {
  transports: ["websocket"]
});

// Client
const socket = io({ transports: ["websocket"] });
```

**Trade-off:** No fallback for environments that block WebSocket.

### Volatile Events for High-Frequency Data

```javascript
// Don't buffer cursor positions during disconnect
socket.volatile.emit("cursor:move", { x: 120, y: 340 });

// Don't buffer game state updates
socket.volatile.emit("game:state", gameState);
```

### Compression

```javascript
// Disable per-message compression for low-latency
const io = new Server(httpServer, {
  perMessageDeflate: false // default is false
});

// Disable compression per-emit
socket.compress(false).emit("realtime:data", data);

// HTTP compression is enabled by default for long-polling
```

## CORS Configuration

### Basic Setup

```javascript
const io = new Server(httpServer, {
  cors: {
    origin: "https://myapp.com"
  }
});
```

### Full Configuration

```javascript
const io = new Server(httpServer, {
  cors: {
    origin: ["https://myapp.com", "https://staging.myapp.com"],
    methods: ["GET", "POST"],
    credentials: true,
    allowedHeaders: ["my-custom-header"],
    exposedHeaders: ["my-response-header"],
    maxAge: 86400 // 24 hours
  }
});
```

### Origin Types

```javascript
// Boolean — true reflects request origin
cors: { origin: true }

// String — single origin
cors: { origin: "https://myapp.com" }

// Regex
cors: { origin: /\.myapp\.com$/ }

// Array
cors: { origin: ["https://myapp.com", /\.myapp\.com$/] }

// Function
cors: {
  origin: (origin, callback) => {
    const allowed = allowedOrigins.includes(origin);
    callback(null, allowed ? origin : false);
  }
}
```

### Client Cross-Origin Configuration

```javascript
const socket = io("https://api.myapp.com", {
  withCredentials: true,
  extraHeaders: {
    "my-custom-header": "value"
  }
});
```

### CORS Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| Missing `Access-Control-Allow-Origin` | Server unreachable | Check server is running, test with curl |
| Credentials with wildcard origin | `origin: "*"` with `withCredentials: true` | Use specific origins |
| Missing credentials in response | Server missing `credentials: true` | Add to CORS config |

CORS only applies to browsers and only to HTTP long-polling. WebSocket connections bypass CORS.

## Security Best Practices

### Input Validation

TypeScript types do not replace runtime validation:

```javascript
import { z } from "zod";

const MessageSchema = z.object({
  text: z.string().min(1).max(5000),
  roomId: z.string().uuid()
});

socket.on("chat:send", (data, callback) => {
  const result = MessageSchema.safeParse(data);
  if (!result.success) {
    return callback({ error: "Invalid input" });
  }
  // use result.data
});
```

### Rate Limiting Events

```javascript
io.on("connection", (socket) => {
  const eventCounts = new Map();

  socket.use(([event], next) => {
    const now = Date.now();
    const key = event;
    const record = eventCounts.get(key) || { count: 0, resetAt: now + 60000 };

    if (now > record.resetAt) {
      record.count = 0;
      record.resetAt = now + 60000;
    }

    record.count++;
    eventCounts.set(key, record);

    if (record.count > 100) {
      return next(new Error("Rate limit exceeded"));
    }

    next();
  });
});
```

### Authentication Verification

```javascript
// Always validate auth, not just socket.id
io.use(async (socket, next) => {
  const token = socket.handshake.auth.token;
  try {
    const user = await verifyToken(token);
    socket.data.user = user;
    next();
  } catch {
    next(new Error("Authentication failed"));
  }
});

// Re-verify on sensitive operations
socket.on("admin:action", async (data, callback) => {
  const user = await getUserFromDb(socket.data.user.id);
  if (user.role !== "admin") {
    return callback({ error: "Forbidden" });
  }
  // proceed
});
```

### Payload Size Limits

```javascript
const io = new Server(httpServer, {
  maxHttpBufferSize: 1e6 // 1 MB max per message
});
```

### Namespace Access Control

```javascript
// Don't allow arbitrary namespace creation
io.of((name, auth, next) => {
  const allowed = ["/chat", "/notifications", "/admin"];
  if (allowed.some((prefix) => name.startsWith(prefix))) {
    next(null, true);
  } else {
    next(new Error("Unknown namespace"), false);
  }
});
```

### Connection State Recovery Security

```javascript
const io = new Server(httpServer, {
  connectionStateRecovery: {
    maxDisconnectionDuration: 2 * 60 * 1000,
    skipMiddlewares: false // IMPORTANT: keep false to re-run auth
  }
});
```

## Memory Optimization

### Discard HTTP Request Reference

After connection, the initial HTTP request is kept in memory. Discard it if not needed:

```javascript
io.on("connection", (socket) => {
  socket.conn.once("upgrade", () => {
    // transport upgraded to WebSocket
    socket.conn.request = null; // free memory
  });
});
```

### Monitor Memory

```javascript
setInterval(() => {
  const usage = process.memoryUsage();
  console.log({
    rss: `${Math.round(usage.rss / 1024 / 1024)} MB`,
    heapUsed: `${Math.round(usage.heapUsed / 1024 / 1024)} MB`,
    connections: io.engine.clientsCount
  });
}, 30000);
```

## OS-Level Tuning

### File Descriptor Limits

Default limit is ~1024. Each connection consumes one file descriptor.

```bash
# Check current limit
ulimit -n

# Increase for current session
ulimit -n 65536

# Permanent (Linux): /etc/security/limits.d/socket-io.conf
* soft nofile 65536
* hard nofile 65536
```

### Port Range

Default range: ~32,768–60,999 (~28,000 ports).

```bash
# Check current range
cat /proc/sys/net/ipv4/ip_local_port_range

# Expand range: /etc/sysctl.d/99-socket-io.conf
net.ipv4.ip_local_port_range = 1024 65535
```

### Connection Limit Symptoms

| Approximate Limit | Likely Bottleneck |
|-------------------|-------------------|
| ~1,000 connections | File descriptor limit |
| ~28,000 connections | Port range exhaustion |

### Scaling Beyond OS Limits

For 50k+ connections per server:
1. Increase file descriptors to 100k+
2. Expand port range
3. Use WebSocket-only (fewer file descriptors per connection)
4. Consider multiple IP addresses per server
5. Scale horizontally with adapters
