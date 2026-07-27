# Socket.IO Delivery Guarantees and Reliability

> Source: https://socket.io/docs/v4/delivery-guarantees/ | https://socket.io/docs/v4/connection-state-recovery/

## Table of Contents

- [Message Ordering](#message-ordering)
- [Delivery Semantics](#delivery-semantics)
- [Connection State Recovery](#connection-state-recovery)
- [Client-to-Server Retries](#client-to-server-retries)
- [Server-to-Client Reliability](#server-to-client-reliability)
- [Idempotency](#idempotency)

## Message Ordering

Socket.IO guarantees message ordering regardless of transport type. This is achieved through:

- TCP guarantees for both WebSocket and HTTP long-polling
- Careful upgrade mechanism that ensures no messages are lost during transport switch

Messages from A arrive at B in the same order they were sent.

## Delivery Semantics

### At Most Once (Default)

The default behavior provides no retry mechanism:

```javascript
// If connection breaks during transmission, this event may be lost
socket.emit("event", data);
```

Key behaviors:
- Events emitted while connected may be lost if the connection drops mid-flight
- Events emitted while disconnected are buffered and sent on reconnect
- Server has no buffer for disconnected clients — missed events are gone
- If the user refreshes the browser tab, all pending events are lost

### At Least Once (Client → Server)

Enable retries for client-to-server events using acknowledgements:

```javascript
// Client
const socket = io({
  ackTimeout: 10000,  // 10-second timeout per attempt
  retries: 3          // up to 3 retries
});

// Server MUST use acknowledgements
io.on("connection", (socket) => {
  socket.on("order:create", (data, callback) => {
    const order = createOrder(data);
    callback({ status: "ok", orderId: order.id }); // acknowledge receipt
  });
});

// Client emits — retries automatically if no ack received
socket.emit("order:create", orderData, (response) => {
  console.log(response.orderId);
});
```

**Limitations:**
- Only works client-to-server
- Requires server to acknowledge each event
- Pending events lost on page refresh
- May deliver duplicates — server must handle idempotency

### At Least Once (Server → Client)

No built-in mechanism. Implement manually with persistent storage:

```javascript
// Server — persist events and track delivery
io.on("connection", async (socket) => {
  const userId = socket.data.userId;

  // Send missed events since last connection
  const lastOffset = socket.handshake.auth.lastOffset || 0;
  const missedEvents = await db.events.find({
    userId,
    offset: { $gt: lastOffset }
  });

  for (const event of missedEvents) {
    socket.emit(event.name, event.data, event.offset);
  }

  // Persist new events before emitting
  socket.on("some:trigger", async (data) => {
    const event = await db.events.create({
      userId: targetUserId,
      name: "notification",
      data,
      offset: nextOffset()
    });

    io.to(`user:${targetUserId}`).emit("notification", data, event.offset);
  });
});

// Client — track last received offset
let lastOffset = localStorage.getItem("lastOffset") || 0;

const socket = io({
  auth: { lastOffset }
});

socket.on("notification", (data, offset) => {
  lastOffset = offset;
  localStorage.setItem("lastOffset", offset);
  handleNotification(data);
});
```

## Connection State Recovery

Built-in feature (v4.6.0+) that restores socket state after temporary disconnections.

### Enabling

```javascript
const io = new Server(httpServer, {
  connectionStateRecovery: {
    maxDisconnectionDuration: 2 * 60 * 1000, // 2 minutes
    skipMiddlewares: false
  }
});
```

### What Gets Recovered

On reconnection within `maxDisconnectionDuration`:
- **Socket ID** — same `socket.id` as before
- **Room memberships** — automatically rejoined
- **socket.data** — restored
- **Missed packets** — replayed in order

### Usage

```javascript
// Server
io.on("connection", (socket) => {
  if (socket.recovered) {
    // session restored — rooms rejoin automatically
    // missed events will be delivered
  } else {
    // fresh connection — set up state manually
    socket.join(`user:${socket.data.userId}`);
    // send current state
  }
});

// Client
socket.on("connect", () => {
  if (socket.recovered) {
    // state restored, missed events arriving
  } else {
    // new session, request fresh state
    socket.emit("state:request");
  }
});
```

### How It Works Internally

1. Server assigns a private session ID (separate from `socket.id`)
2. Each emitted packet includes an offset
3. On reconnection, client sends session ID + last offset
4. Server replays missed packets from its buffer

### Adapter Compatibility

| Adapter | State Recovery |
|---------|---------------|
| In-memory (built-in) | Yes |
| Redis Streams | Yes |
| MongoDB | Yes |
| Redis Pub/Sub | No |
| PostgreSQL | Partial |
| Cluster | Partial |

### Limitations

- Recovery is NOT guaranteed — always handle the `socket.recovered === false` case
- Buffer is bounded by `maxDisconnectionDuration`
- `skipMiddlewares: true` bypasses auth checks on recovery — security risk
- Doesn't survive server restart (in-memory adapter)
- `socket.disconnect()` (intentional) does NOT trigger recovery

## Client-to-Server Retries

```javascript
// Client configuration
const socket = io({
  retries: 3,        // max retry attempts per event
  ackTimeout: 5000   // timeout before retry (ms)
});

// Emit with automatic retry
socket.emit("critical:event", data, (response) => {
  // guaranteed to be called once ack received
  // or throw after all retries exhausted
});

// Promise-based with retries
try {
  const response = await socket.timeout(15000).emitWithAck("event", data);
} catch (err) {
  // all retries exhausted or total timeout reached
}
```

### Retry Behavior

1. Client emits event
2. Wait `ackTimeout` for server acknowledgement
3. If no ack, retry (up to `retries` times)
4. If all retries fail, callback receives error / promise rejects

## Idempotency

With retries enabled, servers may receive duplicate events. Implement idempotency:

```javascript
// Client — attach unique ID to each event
import { v4 as uuidv4 } from "uuid";

socket.emit("order:create", {
  idempotencyKey: uuidv4(),
  ...orderData
}, (response) => {});

// Server — deduplicate
const processedKeys = new Set(); // use Redis/DB in production

socket.on("order:create", (data, callback) => {
  if (processedKeys.has(data.idempotencyKey)) {
    // already processed — return cached result
    return callback({ status: "ok", duplicate: true });
  }

  processedKeys.add(data.idempotencyKey);
  const order = createOrder(data);
  callback({ status: "ok", orderId: order.id });
});
```

## Reliability Summary

| Scenario | Default | With Retries | With Recovery |
|----------|---------|-------------|---------------|
| Event during connection | Delivered | Delivered | Delivered |
| Event during brief disconnect | Lost | Retried (C→S) | Replayed |
| Event during long disconnect | Lost | Lost on refresh | Lost |
| Room membership after reconnect | Lost | Lost | Restored |
| Socket ID after reconnect | Changed | Changed | Preserved |
