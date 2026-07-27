# Socket.IO Events and Acknowledgements

> Source: https://socket.io/docs/v4/emitting-events/ | https://socket.io/docs/v4/listening-to-events/

## Table of Contents

- [Basic Events](#basic-events)
- [Broadcasting](#broadcasting)
- [Acknowledgements](#acknowledgements)
- [Volatile Events](#volatile-events)
- [Catch-All Listeners](#catch-all-listeners)
- [Reserved Events](#reserved-events)
- [Emit Cheat Sheet](#emit-cheat-sheet)

## Basic Events

Socket.IO uses a simple event-based model inspired by Node.js EventEmitter. Events are named messages with optional payloads.

### Emitting Events

```javascript
// Server to client
socket.emit("hello", "world");

// Client to server
socket.emit("hello", "world");

// Multiple arguments
socket.emit("update", arg1, arg2, arg3);

// With an object
socket.emit("user:update", { name: "Alice", age: 30 });
```

### Supported Data Types

```javascript
// All serializable types work
socket.emit("event", "string");
socket.emit("event", 42);
socket.emit("event", { key: "value" });
socket.emit("event", [1, 2, 3]);
socket.emit("event", Buffer.from([1, 2, 3]));     // binary
socket.emit("event", new Uint8Array([1, 2, 3]));  // typed array

// No need for JSON.stringify — objects are serialized automatically
```

### Serialization Caveats

```javascript
// Date objects are converted to strings
socket.emit("event", new Date());
// Received as: "2026-07-28T..."

// Map and Set must be manually serialized
const map = new Map([["key", "value"]]);
socket.emit("event", [...map.entries()]);

// Custom serialization via toJSON()
class User {
  toJSON() { return { id: this.id, name: this.name }; }
}
```

### Listening for Events

```javascript
// Persistent listener
socket.on("event", (data) => {
  console.log(data);
});

// One-time listener
socket.once("event", (data) => {
  console.log(data); // fires only once
});

// Remove specific listener
const handler = (data) => {};
socket.on("event", handler);
socket.off("event", handler);

// Remove all listeners for an event
socket.removeAllListeners("event");
```

## Broadcasting

Broadcasting sends events to multiple clients.

### Server-Side Broadcasting

```javascript
io.on("connection", (socket) => {
  // To ALL connected clients (including sender)
  io.emit("event", data);

  // To ALL except sender
  socket.broadcast.emit("event", data);

  // To a specific room (excluding sender)
  socket.to("room1").emit("event", data);

  // To multiple rooms (union — excluding sender)
  socket.to("room1").to("room2").emit("event", data);

  // To a room, excluding another room
  socket.to("room1").except("room2").emit("event", data);

  // To ALL in a room (including sender if in room)
  io.to("room1").emit("event", data);

  // To ALL except a room
  io.except("room1").emit("event", data);

  // To a specific socket by ID
  io.to(socketId).emit("event", data);
});
```

### Namespace-Scoped Broadcasting

```javascript
const adminNsp = io.of("/admin");

// Broadcast within namespace
adminNsp.emit("event", data);

// Target room within namespace
adminNsp.to("managers").emit("event", data);
```

## Acknowledgements

Acknowledgements provide a request-response pattern over events.

### Callback-Based

```javascript
// Client sends, waits for server response
socket.emit("create:user", { name: "Alice" }, (response) => {
  console.log(response); // { status: "ok", id: 123 }
});

// Server handles and responds
io.on("connection", (socket) => {
  socket.on("create:user", (data, callback) => {
    const user = createUser(data);
    callback({ status: "ok", id: user.id });
  });
});
```

### Promise-Based (v4.6.0+)

```javascript
// Client — emitWithAck returns a Promise
try {
  const response = await socket.emitWithAck("create:user", { name: "Alice" });
  console.log(response); // { status: "ok", id: 123 }
} catch (err) {
  // timeout or error
}

// Server — return value becomes the acknowledgement
io.on("connection", (socket) => {
  socket.on("create:user", async (data) => {
    const user = await createUser(data);
    return { status: "ok", id: user.id };
  });
});
```

### With Timeout

```javascript
// Callback style
socket.timeout(5000).emit("event", data, (err, response) => {
  if (err) {
    // server did not acknowledge within 5 seconds
  } else {
    console.log(response);
  }
});

// Promise style
try {
  const response = await socket.timeout(5000).emitWithAck("event", data);
} catch (err) {
  // timeout
}
```

### Broadcasting with Acknowledgement

```javascript
// Server acknowledges from multiple clients
io.timeout(5000).emit("event", (err, responses) => {
  if (err) {
    // some clients did not acknowledge
  } else {
    console.log(responses); // array of responses from each client
  }
});
```

## Volatile Events

Volatile events are dropped if the client is not ready to receive them. Useful for data that becomes stale quickly (cursor position, game state).

```javascript
// Server
socket.volatile.emit("cursor:move", { x: 120, y: 450 });

// Client
socket.volatile.emit("heartbeat", Date.now());
```

Key behavior:
- NOT buffered during disconnection
- NOT retried on failure
- Think of it like UDP — fire and forget

## Catch-All Listeners

### Incoming Events

```javascript
// Listen to ALL incoming events
socket.onAny((eventName, ...args) => {
  console.log(`Received: ${eventName}`, args);
});

// Prepend to listener list
socket.prependAny((eventName, ...args) => {
  // runs first
});

// Remove catch-all
socket.offAny(handler);
socket.offAny(); // remove all
```

### Outgoing Events

```javascript
// Listen to ALL outgoing events
socket.onAnyOutgoing((eventName, ...args) => {
  console.log(`Sending: ${eventName}`, args);
});

socket.prependAnyOutgoing((eventName, ...args) => {});
socket.offAnyOutgoing(handler);
```

### Use Cases

- Logging/debugging all events
- Analytics/metrics collection
- Event forwarding/proxying

## Reserved Events

These event names are reserved and cannot be used for application events:

**Server-side:**
- `connect` / `connection`
- `disconnect`
- `disconnecting`
- `newListener`
- `removeListener`

**Client-side:**
- `connect`
- `connect_error`
- `disconnect`
- `disconnecting`
- `newListener`
- `removeListener`

## Emit Cheat Sheet

```
Server:
  io.emit()                     → all clients
  io.to("room").emit()          → all in room
  io.except("room").emit()      → all except room
  socket.emit()                 → to sender only
  socket.broadcast.emit()       → all except sender
  socket.to("room").emit()      → room members except sender
  socket.to("room")
        .except("other").emit() → room minus other, minus sender

Client:
  socket.emit()                 → to server
  socket.volatile.emit()        → to server, drop if disconnected
```

## Common Patterns

### Request-Response Pattern

```javascript
// Server
socket.on("api:getUser", async (userId, callback) => {
  try {
    const user = await db.users.findById(userId);
    callback({ status: "ok", data: user });
  } catch (err) {
    callback({ status: "error", message: err.message });
  }
});

// Client
const { status, data } = await socket.emitWithAck("api:getUser", "user-123");
```

### Event Namespacing Convention

```javascript
// Use colons for namespace-like event naming
socket.on("chat:message", (msg) => {});
socket.on("chat:typing", (user) => {});
socket.on("user:update", (data) => {});
socket.on("user:delete", (id) => {});
socket.on("file:upload:progress", (pct) => {});
```

### Typed Emit Helper

```javascript
function emitWithRetry(socket, event, data, maxRetries = 3) {
  return new Promise((resolve, reject) => {
    let attempts = 0;
    const tryEmit = () => {
      attempts++;
      socket.timeout(5000).emit(event, data, (err, response) => {
        if (err && attempts < maxRetries) {
          tryEmit();
        } else if (err) {
          reject(new Error(`Failed after ${maxRetries} attempts`));
        } else {
          resolve(response);
        }
      });
    };
    tryEmit();
  });
}
```
