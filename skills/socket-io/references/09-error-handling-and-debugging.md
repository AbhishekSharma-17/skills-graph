# Socket.IO Error Handling and Debugging

> Source: https://socket.io/docs/v4/logging-and-debugging/ | https://socket.io/docs/v4/troubleshooting-connection-issues/

## Table of Contents

- [Debug Logging](#debug-logging)
- [Connection Errors](#connection-errors)
- [Disconnect Reasons](#disconnect-reasons)
- [Troubleshooting Guide](#troubleshooting-guide)
- [Common Pitfalls](#common-pitfalls)

## Debug Logging

Socket.IO uses the `debug` package. Logs are silent by default and must be explicitly enabled.

### Server-Side (Node.js)

```bash
# All Socket.IO debug output
DEBUG=socket.io* node app.js

# Engine.IO only
DEBUG=engine* node app.js

# Both
DEBUG=engine,socket.io* node app.js

# Everything (very verbose)
DEBUG=* node app.js

# Specific components
DEBUG=socket.io:server node app.js
DEBUG=socket.io:client node app.js
DEBUG=socket.io:socket node app.js
```

### Client-Side (Browser)

```javascript
// Enable in browser console
localStorage.debug = "socket.io-client:socket";

// All client debug
localStorage.debug = "socket.io*";

// Disable
localStorage.removeItem("debug");
```

### Debug Scopes

| Scope | Shows |
|-------|-------|
| `socket.io:server` | Server lifecycle events |
| `socket.io:socket` | Individual socket events |
| `socket.io:client` | Client-side socket events |
| `engine` | Engine.IO transport events |
| `engine:ws` | WebSocket-specific events |
| `engine:polling` | HTTP long-polling events |

## Connection Errors

### Server-Side Monitoring

```javascript
io.engine.on("connection_error", (err) => {
  console.log(err.req);      // the HTTP request
  console.log(err.code);     // error code (number)
  console.log(err.message);  // error message
  console.log(err.context);  // additional context
});
```

### Error Codes

| Code | Message | Cause |
|------|---------|-------|
| 0 | Transport unknown | Invalid transport type |
| 1 | Session ID unknown | Missing sticky sessions or expired session |
| 2 | Bad handshake method | Wrong HTTP method |
| 3 | Bad request | Malformed request or missing WebSocket upgrade headers |
| 4 | Forbidden | Rejected by `allowRequest` |
| 5 | Unsupported protocol version | Client/server version mismatch |

### Client-Side Error Handling

```javascript
socket.on("connect_error", (err) => {
  console.log(err.message);  // error description
  console.log(err.data);     // additional data from server middleware

  if (socket.active) {
    // auto-reconnect will happen
    console.log("Temporary failure, retrying...");
  } else {
    // connection rejected by server
    console.log("Connection denied. Manual reconnect needed.");
  }
});
```

## Disconnect Reasons

### Server-Side Disconnect

```javascript
socket.on("disconnect", (reason, details) => {
  console.log(`Disconnected: ${reason}`);
  if (details) {
    console.log(`Description: ${details.description}`);
    console.log(`Context: ${JSON.stringify(details.context)}`);
  }
});
```

| Reason | Meaning | Auto-Reconnect |
|--------|---------|----------------|
| `"server namespace disconnect"` | Server called `socket.disconnect()` | No |
| `"client namespace disconnect"` | Client called `socket.disconnect()` | No |
| `"server shutting down"` | Server is shutting down | Yes |
| `"ping timeout"` | No heartbeat response | Yes |
| `"transport close"` | Connection closed (offline, tab close) | Yes |
| `"transport error"` | Connection error occurred | Yes |
| `"parse error"` | Invalid packet received | No |

### Client-Side Disconnect

```javascript
socket.on("disconnect", (reason, details) => {
  switch (reason) {
    case "io server disconnect":
      // server forcefully disconnected — must manually reconnect
      socket.connect();
      break;
    case "io client disconnect":
      // client intentionally disconnected
      break;
    case "ping timeout":
    case "transport close":
    case "transport error":
      // automatic reconnection will occur
      break;
  }
});
```

## Troubleshooting Guide

### Cannot Connect

**Step 1: Test the handshake endpoint**

```bash
curl "http://localhost:3000/socket.io/?EIO=4&transport=polling"
```

Expected response:
```
0{"sid":"...","upgrades":["websocket"],"pingInterval":25000,"pingTimeout":20000}
```

**Step 2: Check for common issues**

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| CORS error in console | Missing CORS config | Add `cors` to server options |
| `connect_error` with code 5 | Version mismatch | Ensure compatible client/server |
| `connect_error` with code 1 | Missing sticky sessions | Configure sticky sessions |
| `connect_error` with code 3 | Proxy blocking WebSocket | Forward `Upgrade`/`Connection` headers |
| Connection hangs | Path mismatch | Ensure `path` matches on both sides |
| Connection hangs | Middleware never calls `next()` | Check all middleware paths |

### Unexpected Disconnections

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Disconnects after ~60s | Proxy timeout | Increase `proxy_read_timeout` beyond 45s |
| Disconnects on minimize | Browser timer throttling | Upgrade to v4.1.3+ (reversed heartbeat) |
| Disconnects on large send | Exceeds `maxHttpBufferSize` | Increase limit or chunk data |
| Disconnects on long upload | Upload blocks heartbeat | Use a separate HTTP endpoint for uploads |

### WebSocket Upgrade Fails

The browser should show this request sequence:
1. `GET /socket.io/?EIO=4&transport=polling` → 200 (handshake)
2. `GET /socket.io/?EIO=4&transport=polling&sid=...` → 200 (Socket.IO handshake)
3. `POST /socket.io/?EIO=4&transport=polling&sid=...` → 200 (data)
4. `GET /socket.io/?EIO=4&transport=websocket&sid=...` → 101 (upgrade)

If #4 is missing or returns non-101:
- Check proxy/nginx WebSocket configuration
- Verify `Upgrade` and `Connection` headers are forwarded

## Common Pitfalls

### Duplicate Event Handlers

```javascript
// WRONG — registers new handler on every reconnect
socket.on("connect", () => {
  socket.on("message", handleMessage); // duplicated on reconnect!
});

// CORRECT — register handlers once, outside connect
socket.on("connect", () => {
  console.log("Connected");
});
socket.on("message", handleMessage);
```

### Late Handler Registration

```javascript
// WRONG — may miss events emitted during async operation
io.on("connection", async (socket) => {
  await longRunningTask();
  socket.on("event", handler); // events during await are lost
});

// CORRECT — register handlers first
io.on("connection", (socket) => {
  socket.on("event", handler);
  longRunningTask(); // run after registration
});
```

### Using socket.id for Persistence

```javascript
// WRONG — socket.id changes on reconnect
const users = {};
socket.on("connect", () => {
  users[socket.id] = { ... }; // lost on reconnect
});

// CORRECT — use your own user ID
socket.on("connect", () => {
  users[myUserId] = { socketId: socket.id };
});
```

### Serverless Incompatibility

Socket.IO requires long-lived connections. It is NOT compatible with:
- AWS Lambda
- Vercel Serverless Functions
- Cloudflare Workers (without Durable Objects)

Use a dedicated server or container-based deployment.

### Package Conflicts

The `express-status-monitor` package creates its own Socket.IO instance, which can interfere with your application. Remove it or configure it to use a different path.

### Missing next() in Middleware

```javascript
// WRONG — connection hangs until connectTimeout
io.use((socket, next) => {
  if (someCondition) {
    next();
  }
  // forgot next() for the else case!
});

// CORRECT
io.use((socket, next) => {
  if (someCondition) {
    next();
  } else {
    next(new Error("Rejected"));
  }
});
```
