# ElysiaJS — WebSocket

> Source: [elysiajs.com/patterns/websocket](https://elysiajs.com/patterns/websocket) · Version 1.4.x

## Table of Contents

- [WebSocket Overview](#websocket-overview)
- [Basic WebSocket Route](#basic-websocket-route)
- [Event Handlers](#event-handlers)
- [Message Validation](#message-validation)
- [WebSocket Context](#websocket-context)
- [Broadcasting](#broadcasting)
- [Configuration](#configuration)
- [Middleware Integration](#middleware-integration)
- [Eden WebSocket Client](#eden-websocket-client)
- [Common Pitfalls](#common-pitfalls)

---

## WebSocket Overview

ElysiaJS provides first-class WebSocket support via the `.ws()` method, leveraging Bun's native WebSocket implementation (uWebSocket under the hood). WebSocket routes support the same schema validation and lifecycle hooks as HTTP routes.

```typescript
import { Elysia } from 'elysia'

new Elysia()
    .ws('/ws', {
        message(ws, message) {
            ws.send(message)
        }
    })
    .listen(3000)
```

## Basic WebSocket Route

```typescript
import { Elysia, t } from 'elysia'

const app = new Elysia()
    .ws('/chat', {
        body: t.Object({
            message: t.String()
        }),
        response: t.Object({
            reply: t.String(),
            timestamp: t.Number()
        }),
        message(ws, { message }) {
            ws.send({
                reply: message.toUpperCase(),
                timestamp: Date.now()
            })
        }
    })
    .listen(3000)
```

## Event Handlers

Four lifecycle events are available for WebSocket connections:

### open

Triggered when a new WebSocket connection is established:

```typescript
.ws('/ws', {
    open(ws) {
        console.log(`Client connected: ${ws.id}`)
        ws.send({ type: 'welcome', message: 'Connected!' })
    }
})
```

### message

Handles incoming messages from the client:

```typescript
.ws('/ws', {
    message(ws, data) {
        console.log('Received:', data)
        ws.send({ echo: data })
    }
})
```

### close

Executes when a connection is terminated:

```typescript
.ws('/ws', {
    close(ws, code, reason) {
        console.log(`Client ${ws.id} disconnected: ${code} ${reason}`)
        removeFromRoom(ws.id)
    }
})
```

### drain

Fires when the server is ready to accept more data (backpressure relief):

```typescript
.ws('/ws', {
    drain(ws) {
        console.log('Backpressure relieved, ready for more data')
    }
})
```

### Combined Example

```typescript
.ws('/chat', {
    open(ws) {
        ws.subscribe('general')
        ws.publish('general', { type: 'join', user: ws.data.username })
    },

    message(ws, { message }) {
        ws.publish('general', {
            type: 'message',
            user: ws.data.username,
            content: message,
            time: Date.now()
        })
    },

    close(ws) {
        ws.publish('general', { type: 'leave', user: ws.data.username })
        ws.unsubscribe('general')
    }
})
```

## Message Validation

WebSocket routes support the same schema validation as HTTP routes:

```typescript
.ws('/ws', {
    // Validate incoming messages
    body: t.Object({
        type: t.Union([
            t.Literal('ping'),
            t.Literal('message'),
            t.Literal('command')
        ]),
        payload: t.Optional(t.String())
    }),

    // Validate outgoing messages
    response: t.Object({
        type: t.String(),
        data: t.Any(),
        timestamp: t.Number()
    }),

    // Validate query parameters (from the upgrade URL)
    query: t.Object({
        token: t.String()
    }),

    // Validate path parameters
    params: t.Object({
        room: t.String()
    }),

    // Validate headers
    headers: t.Object({
        authorization: t.Optional(t.String())
    }),

    // Validate cookies
    cookie: t.Cookie({
        session: t.Optional(t.String())
    }),

    message(ws, { type, payload }) {
        // type and payload are fully typed
        switch (type) {
            case 'ping':
                ws.send({ type: 'pong', data: null, timestamp: Date.now() })
                break
            case 'message':
                ws.send({ type: 'echo', data: payload, timestamp: Date.now() })
                break
        }
    }
})
```

## WebSocket Context

The `ws` object provides:

| Property/Method | Description |
|----------------|-------------|
| `ws.send(data)` | Send message to this client |
| `ws.close()` | Close the connection |
| `ws.id` | Unique connection identifier |
| `ws.data` | Context data (derived values, etc.) |
| `ws.subscribe(topic)` | Subscribe to a pub/sub topic |
| `ws.unsubscribe(topic)` | Unsubscribe from a topic |
| `ws.publish(topic, data)` | Publish to all topic subscribers |
| `ws.isSubscribed(topic)` | Check topic subscription |
| `ws.raw` | Underlying Bun WebSocket |

### Accessing Request Data

```typescript
.ws('/ws', {
    open(ws) {
        // Access query, headers, params via ws.data
        const token = ws.data.query.token
        const userId = ws.data.headers.authorization
    }
})
```

## Broadcasting

### Pub/Sub Topics

```typescript
.ws('/chat/:room', {
    open(ws) {
        const room = ws.data.params.room
        ws.subscribe(room)
        ws.publish(room, { event: 'user-joined' })
    },

    message(ws, data) {
        const room = ws.data.params.room
        // Publish to all subscribers except sender
        ws.publish(room, {
            event: 'message',
            data,
            from: ws.id
        })
    },

    close(ws) {
        const room = ws.data.params.room
        ws.publish(room, { event: 'user-left' })
        ws.unsubscribe(room)
    }
})
```

### Server-Wide Broadcasting

```typescript
const app = new Elysia()
    .ws('/ws', {
        open(ws) {
            ws.subscribe('broadcast')
        },
        message(ws, data) {
            // Send to all connected clients
            app.server?.publish('broadcast', JSON.stringify(data))
        }
    })
```

## Configuration

### Per-Route Configuration

```typescript
.ws('/ws', {
    idleTimeout: 120,            // Seconds before idle disconnect (default: 120)
    maxPayloadLength: 16 * 1024, // Max message size in bytes
    backpressureLimit: 1024 * 1024, // Backpressure threshold
    perMessageDeflate: true,     // Enable compression
    sendPingsAutomatically: true, // Auto ping/pong

    message(ws, data) {
        ws.send(data)
    }
})
```

### Global WebSocket Configuration

```typescript
new Elysia({
    websocket: {
        idleTimeout: 60,
        maxPayloadLength: 1024 * 1024,
        perMessageDeflate: false
    }
})
```

## Middleware Integration

WebSocket routes support lifecycle hooks that run during the HTTP upgrade:

### Pre-Upgrade Hooks

```typescript
.ws('/ws', {
    // Runs before WebSocket upgrade
    beforeHandle({ headers }) {
        const token = headers.authorization?.split(' ')[1]
        if (!token || !verifyToken(token)) {
            return status(401, 'Unauthorized')
        }
    },

    // Transform before validation
    transform({ query }) {
        if (query.room) query.room = query.room.toLowerCase()
    },

    open(ws) {
        console.log('Authenticated client connected')
    },

    message(ws, data) {
        ws.send(data)
    }
})
```

### Using Derive with WebSocket

```typescript
app.derive(({ headers }) => ({
    user: getUserFromToken(headers.authorization)
}))

app.ws('/ws', {
    open(ws) {
        // Access derived values
        console.log(`User connected: ${ws.data.user.name}`)
    },
    message(ws, data) {
        ws.send({ from: ws.data.user.name, ...data })
    }
})
```

## Eden WebSocket Client

Type-safe WebSocket from the client:

```typescript
import { treaty } from '@elysia/eden'
import type { App } from './server'

const api = treaty<App>('localhost:3000')

// Connect to WebSocket
const ws = api.chat({ room: 'general' }).subscribe()

// Type-safe event handling
ws.on('message', ({ data }) => {
    console.log(data.reply)  // Typed from response schema
})

// Type-safe sending
ws.send({ message: 'Hello!' })  // Typed from body schema

// Close connection
ws.close()
```

## Common Pitfalls

1. **WebSocket is Bun-only for peak performance** — The WS implementation uses Bun's native uWebSocket. Node.js adapter may have limited WS support.

2. **Validation runs on upgrade** — Query, params, headers, and cookie validation happens during the HTTP upgrade, not on each message. Body validation applies per-message.

3. **publish excludes sender** — `ws.publish()` sends to all subscribers except the publishing socket. Use `app.server?.publish()` to include everyone.

4. **JSON serialization** — `ws.send()` auto-serializes objects to JSON. Sending raw strings doesn't auto-serialize — use explicit `JSON.stringify()` if needed.

5. **Eden WS only with Treaty** — Eden Fetch does not support WebSocket. Use `treaty()` for type-safe WS connections.
