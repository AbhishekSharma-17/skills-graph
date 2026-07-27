# Socket.IO Middleware and Authentication

> Source: https://socket.io/docs/v4/middlewares/

## Table of Contents

- [Middleware Basics](#middleware-basics)
- [Authentication Patterns](#authentication-patterns)
- [Per-Packet Middleware](#per-packet-middleware)
- [Express Middleware Integration](#express-middleware-integration)
- [Error Handling](#error-handling)
- [Common Patterns](#common-patterns)

## Middleware Basics

A middleware function executes for every incoming connection. Middlewares run sequentially in registration order.

```javascript
io.use((socket, next) => {
  // socket.handshake contains connection metadata
  // Call next() to proceed, next(err) to reject
  if (isValid(socket.handshake)) {
    next();
  } else {
    next(new Error("Connection rejected"));
  }
});
```

### Multiple Middlewares

```javascript
// Runs in order: logging → auth → rate-limit
io.use(loggingMiddleware);
io.use(authMiddleware);
io.use(rateLimitMiddleware);

function loggingMiddleware(socket, next) {
  console.log(`Connection attempt from ${socket.handshake.address}`);
  next();
}

function authMiddleware(socket, next) {
  const token = socket.handshake.auth.token;
  if (!token) return next(new Error("Authentication required"));

  verifyToken(token)
    .then((user) => {
      socket.data.user = user;
      next();
    })
    .catch(() => next(new Error("Invalid token")));
}

function rateLimitMiddleware(socket, next) {
  if (isRateLimited(socket.handshake.address)) {
    return next(new Error("Too many connections"));
  }
  next();
}
```

### Namespace-Specific Middleware

```javascript
// Main namespace middleware
io.use(globalAuth);

// Admin namespace has additional middleware
const adminNsp = io.of("/admin");
adminNsp.use(globalAuth);     // can reuse
adminNsp.use(adminOnlyAuth);  // additional check
```

## Authentication Patterns

### JWT Token Authentication

```javascript
// Client
const socket = io("http://localhost:3000", {
  auth: {
    token: "eyJhbGciOi..."
  }
});

// Server
io.use(async (socket, next) => {
  const token = socket.handshake.auth.token;

  if (!token) {
    return next(new Error("Authentication required"));
  }

  try {
    const decoded = await jwt.verify(token, JWT_SECRET);
    socket.data.userId = decoded.sub;
    socket.data.role = decoded.role;
    next();
  } catch (err) {
    next(new Error("Invalid or expired token"));
  }
});
```

### Session-Based Authentication

```javascript
import session from "express-session";

const sessionMiddleware = session({
  secret: "my-secret",
  resave: false,
  saveUninitialized: false
});

// Share session between Express and Socket.IO
app.use(sessionMiddleware);
io.engine.use(sessionMiddleware);

io.use((socket, next) => {
  const session = socket.request.session;
  if (session && session.userId) {
    socket.data.userId = session.userId;
    next();
  } else {
    next(new Error("Not authenticated"));
  }
});
```

### Cookie-Based Authentication

```javascript
import cookie from "cookie";

io.use((socket, next) => {
  const cookies = cookie.parse(socket.handshake.headers.cookie || "");
  const sessionToken = cookies.session_token;

  if (!sessionToken) {
    return next(new Error("No session cookie"));
  }

  validateSession(sessionToken)
    .then((user) => {
      socket.data.user = user;
      next();
    })
    .catch(() => next(new Error("Invalid session")));
});
```

### Dynamic Auth (Token Refresh)

```javascript
// Client — auth as function for dynamic values
const socket = io({
  auth: (cb) => {
    cb({ token: getAccessToken() });
  }
});

// Handle expired token
socket.on("connect_error", async (err) => {
  if (err.message === "Token expired") {
    const newToken = await refreshToken();
    saveAccessToken(newToken);
    socket.connect(); // triggers auth callback again
  }
});
```

## Per-Packet Middleware

Per-packet middleware runs for every incoming event on a specific socket (not just on connection):

```javascript
io.on("connection", (socket) => {
  socket.use(([event, ...args], next) => {
    // Runs for every event received from this client
    console.log(`Event: ${event}`, args);

    // Validate event data
    if (event.startsWith("admin:") && socket.data.role !== "admin") {
      return next(new Error("Unauthorized"));
    }

    next();
  });
});
```

### Per-Packet Error Handling

```javascript
io.on("connection", (socket) => {
  socket.use(([event, ...args], next) => {
    try {
      validateEventPayload(event, args);
      next();
    } catch (err) {
      next(err);
    }
  });

  // Errors from per-packet middleware emit "error" on the socket
  socket.on("error", (err) => {
    console.error(`Packet error: ${err.message}`);
  });
});
```

## Express Middleware Integration

Since v4.6.0, Express middlewares work with `io.engine.use()`:

```javascript
import cors from "cors";
import helmet from "helmet";

// Apply to ALL HTTP requests (including upgrade)
io.engine.use(helmet());
io.engine.use(cors({ origin: "https://myapp.com" }));

// Apply only to initial handshake (not to every polling request)
io.engine.use((req, res, next) => {
  const isHandshake = !req._query.sid;
  if (isHandshake) {
    // Run expensive auth only on first request
    authMiddleware(req, res, next);
  } else {
    next();
  }
});
```

## Error Handling

### Rejecting Connections

```javascript
io.use((socket, next) => {
  const err = new Error("Not authorized");
  err.data = { content: "Please retry later" }; // sent to client
  next(err);
});
```

### Client Error Handling

```javascript
socket.on("connect_error", (err) => {
  console.log(err.message);  // "Not authorized"
  console.log(err.data);     // { content: "Please retry later" }
});
```

### Connection Error Codes

```javascript
io.engine.on("connection_error", (err) => {
  console.log(err.code);     // numeric error code
  console.log(err.message);  // human-readable message
  console.log(err.context);  // additional details
});

// Common error codes:
// 0 - Transport unknown
// 1 - Session ID unknown
// 2 - Bad handshake method
// 3 - Bad request
// 4 - Forbidden
// 5 - Unsupported protocol version
```

## Common Patterns

### Role-Based Access Control

```javascript
function requireRole(...roles) {
  return (socket, next) => {
    if (roles.includes(socket.data.user?.role)) {
      next();
    } else {
      next(new Error(`Required role: ${roles.join(" or ")}`));
    }
  };
}

io.of("/admin").use(authMiddleware);
io.of("/admin").use(requireRole("admin", "superadmin"));
```

### Rate Limiting

```javascript
const connectionCounts = new Map();

io.use((socket, next) => {
  const ip = socket.handshake.address;
  const count = connectionCounts.get(ip) || 0;

  if (count >= 10) {
    return next(new Error("Too many connections from this IP"));
  }

  connectionCounts.set(ip, count + 1);

  socket.on("disconnect", () => {
    const current = connectionCounts.get(ip) || 1;
    if (current <= 1) {
      connectionCounts.delete(ip);
    } else {
      connectionCounts.set(ip, current - 1);
    }
  });

  next();
});
```

### Logging Middleware

```javascript
io.use((socket, next) => {
  const { address, auth, query, time } = socket.handshake;
  console.log(`[${time}] Connection from ${address}`, {
    hasAuth: !!auth.token,
    query
  });
  next();
});
```

### Input Validation Middleware

```javascript
io.on("connection", (socket) => {
  socket.use(([event, ...args], next) => {
    const schema = eventSchemas.get(event);
    if (schema) {
      const result = schema.safeParse(args[0]);
      if (!result.success) {
        return next(new Error(`Validation failed: ${result.error.message}`));
      }
      args[0] = result.data; // use validated data
    }
    next();
  });
});
```
