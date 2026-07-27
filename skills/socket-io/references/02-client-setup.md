# Socket.IO Client Setup

> Source: https://socket.io/docs/v4/client-installation/ | https://socket.io/docs/v4/client-options/

## Table of Contents

- [Installation](#installation)
- [Connection](#connection)
- [Client Options](#client-options)
- [Manager Class](#manager-class)
- [Socket Instance](#socket-instance)
- [Reconnection](#reconnection)
- [Connection Lifecycle](#connection-lifecycle)

## Installation

```bash
# npm
npm install socket.io-client

# Browser CDN
# <script src="https://cdn.socket.io/4.8.3/socket.io.min.js"></script>

# ES module import
import { io } from "socket.io-client";

# CommonJS
const { io } = require("socket.io-client");
```

## Connection

### Basic Connection

```javascript
import { io } from "socket.io-client";

// Connect to same origin
const socket = io();

// Connect to specific server
const socket = io("http://localhost:3000");

// Connect to namespace
const socket = io("http://localhost:3000/admin");

// Connect with options
const socket = io("http://localhost:3000", {
  autoConnect: false,
  auth: { token: "my-token" }
});
socket.connect(); // manual connect
```

### Connection Multiplexing

By default, a single Manager (WebSocket connection) is shared across Socket instances to the same origin:

```javascript
const socket1 = io("http://localhost:3000");       // namespace "/"
const socket2 = io("http://localhost:3000/admin");  // namespace "/admin"
// Both share ONE WebSocket connection

const socket3 = io("http://localhost:3000", { forceNew: true });
// Creates a SEPARATE WebSocket connection
```

## Client Options

### IO Factory Options

| Option | Default | Description |
|--------|---------|-------------|
| `forceNew` | `false` | Create new Manager (separate connection) |
| `multiplex` | `true` | Reuse existing Manager for same origin |

### Transport Options

| Option | Default | Description |
|--------|---------|-------------|
| `transports` | `["polling", "websocket", "webtransport"]` | Allowed transports |
| `upgrade` | `true` | Allow transport upgrade |
| `rememberUpgrade` | `false` | Skip polling, try WebSocket first if prior success |
| `tryAllTransports` | `false` | Try other transports on failure (v4.8.0+) |
| `path` | `/socket.io/` | Server path (must match server) |
| `withCredentials` | `false` | Send cookies cross-origin |
| `extraHeaders` | `{}` | Additional HTTP headers |
| `autoUnref` | `false` | Allow Node.js process exit with open connection |
| `closeOnBeforeunload` | `false` | Close on page unload |

### Reconnection Options

| Option | Default | Description |
|--------|---------|-------------|
| `reconnection` | `true` | Enable auto-reconnection |
| `reconnectionAttempts` | `Infinity` | Max retry attempts |
| `reconnectionDelay` | `1000` | Initial delay (ms) |
| `reconnectionDelayMax` | `5000` | Maximum delay (ms) |
| `randomizationFactor` | `0.5` | Jitter factor (0–1) to prevent thundering herd |
| `timeout` | `20000` | Connection timeout (ms) |

### Socket Options

| Option | Default | Description |
|--------|---------|-------------|
| `auth` | `{}` | Credentials sent during handshake |
| `retries` | `0` | Max packet retries (requires server ack) |
| `ackTimeout` | `undefined` | Default ack timeout (requires `retries`) |
| `autoConnect` | `true` | Connect immediately on creation |

### Auth as Function (Dynamic Credentials)

```javascript
const socket = io({
  auth: (cb) => {
    cb({ token: getLatestToken() }); // called on each connection attempt
  }
});

// Update auth between reconnections
socket.on("connect_error", (err) => {
  if (err.message === "token expired") {
    socket.auth.token = refreshToken();
    socket.connect();
  }
});
```

## Manager Class

The Manager handles the low-level Engine.IO connection and reconnection:

```javascript
const socket = io("http://localhost:3000");
const manager = socket.io; // access the Manager

// Manager events
manager.on("error", (err) => {});           // connection error
manager.on("ping", () => {});                // heartbeat received
manager.on("reconnect", (attempt) => {});    // successful reconnect
manager.on("reconnect_attempt", (n) => {});  // attempt started
manager.on("reconnect_error", (err) => {});  // attempt failed
manager.on("reconnect_failed", () => {});    // all attempts exhausted
```

## Socket Instance

### Properties

```javascript
socket.id;            // session ID (ephemeral, changes on reconnect)
socket.connected;     // boolean — currently connected
socket.disconnected;  // boolean — currently disconnected
socket.active;        // boolean — auto-reconnect will happen
socket.recovered;     // boolean — session was recovered
socket.io;            // reference to Manager
```

### Core Methods

```javascript
// Emit event
socket.emit("event", data);
socket.emit("event", data1, data2);       // multiple args
socket.emit("event", data, (ack) => {});  // with acknowledgement

// Promise-based acknowledgement
const response = await socket.emitWithAck("event", data);

// Listen for events
socket.on("event", (data) => {});
socket.once("event", (data) => {});
socket.off("event", handler);   // remove specific
socket.off("event");            // remove all for event
socket.removeAllListeners();    // remove everything

// Catch-all listeners
socket.onAny((eventName, ...args) => {
  console.log(`Received: ${eventName}`, args);
});
socket.onAnyOutgoing((eventName, ...args) => {
  console.log(`Sending: ${eventName}`, args);
});

// Modifiers
socket.volatile.emit("cursor", { x, y });     // drop if not connected
socket.compress(false).emit("data", payload);  // no compression
socket.timeout(5000).emit("event", (err, response) => {
  if (err) { /* timed out */ }
});

// Connection control
socket.connect();     // manual connect
socket.disconnect();  // manual disconnect
socket.send(data);    // shorthand for emit("message", data)
```

## Reconnection

### Automatic Reconnection

Reconnection uses exponential backoff with jitter:

```
delay = reconnectionDelay * 2^attempt * (1 ± randomizationFactor)
```

Capped at `reconnectionDelayMax`. Example with defaults:
- Attempt 1: ~1000ms (± 500ms jitter)
- Attempt 2: ~2000ms (± 1000ms jitter)
- Attempt 3: ~4000ms (± 2000ms jitter)
- Attempt 4+: capped at 5000ms

### When Reconnection Happens

- Transport error (network drop)
- Ping timeout (server unreachable)
- Server-initiated disconnect (server namespace disconnect does NOT auto-reconnect)

### When Reconnection Does NOT Happen

- Client calls `socket.disconnect()`
- Server rejects connection in middleware

Check `socket.active` after `connect_error` or `disconnect` to know if auto-reconnect is pending.

## Connection Lifecycle

### Events

```javascript
socket.on("connect", () => {
  // connected or reconnected
  // IMPORTANT: register event handlers OUTSIDE this callback
  // to prevent duplicate handlers on reconnect
});

socket.on("connect_error", (err) => {
  // connection failed
  if (socket.active) {
    // auto-reconnect will happen
  } else {
    // rejected by server — manual reconnect needed
    console.log(err.message);
  }
});

socket.on("disconnect", (reason, details) => {
  // Reasons:
  // "io server disconnect" — server called socket.disconnect()
  // "io client disconnect" — client called socket.disconnect()
  // "ping timeout" — no heartbeat response
  // "transport close" — connection was closed (e.g. user offline)
  // "transport error" — connection error (e.g. server killed)
  if (socket.active) {
    // auto-reconnect pending
  } else {
    // manual reconnect needed
  }
});
```

### Buffered Events

Events emitted while disconnected are buffered and sent upon reconnection:

```javascript
socket.emit("event", "data"); // buffered if disconnected, sent on reconnect

// Check connection before emitting if you want to skip buffering
if (socket.connected) {
  socket.emit("event", "data");
}
```

## Common Patterns

### Connection Status Indicator

```javascript
socket.on("connect", () => {
  updateStatus("connected");
});

socket.on("disconnect", () => {
  updateStatus("disconnected");
});

socket.io.on("reconnect_attempt", (attempt) => {
  updateStatus(`reconnecting (attempt ${attempt})`);
});
```

### Token Refresh on Reconnect

```javascript
const socket = io({
  auth: (cb) => {
    cb({ token: localStorage.getItem("token") });
  }
});

socket.on("connect_error", (err) => {
  if (err.message === "invalid token") {
    refreshAccessToken().then((newToken) => {
      localStorage.setItem("token", newToken);
      socket.connect();
    });
  }
});
```
