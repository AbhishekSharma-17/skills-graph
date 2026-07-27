---
name: socket-io
description: "Real-time bidirectional event-based communication library for web applications. MANDATORY TRIGGERS: socket.io, socketio, Socket.IO, websocket events, real-time communication, bidirectional events, socket rooms, socket namespaces. Also trigger when the user wants to build real-time features, chat applications, live notifications, collaborative editing, multiplayer games, live dashboards, or any event-driven client-server communication over WebSockets. When in doubt about whether to use this skill for real-time communication tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["websocket", "real-time", "events", "rooms", "namespaces", "bidirectional", "streaming"]
---

# Socket.IO

> v4.8.3 | https://socket.io/docs/v4/ | https://github.com/socketio/socket.io

## Reference Files

| File | Read When |
|------|-----------|
| [00-overview.md](references/00-overview.md) | Starting with Socket.IO, understanding architecture, installation |
| [01-server-setup.md](references/01-server-setup.md) | Creating a server, configuration options, Express/HTTP integration |
| [02-client-setup.md](references/02-client-setup.md) | Connecting from browser or Node.js, client options, reconnection |
| [03-events-and-acknowledgements.md](references/03-events-and-acknowledgements.md) | Emitting events, broadcasting, acknowledgements, volatile events |
| [04-rooms-and-broadcasting.md](references/04-rooms-and-broadcasting.md) | Rooms, joining, leaving, targeted broadcasting, room events |
| [05-namespaces.md](references/05-namespaces.md) | Namespace creation, dynamic namespaces, multiplexing, isolation |
| [06-middleware-and-auth.md](references/06-middleware-and-auth.md) | Middleware, authentication, authorization, credential handling |
| [07-typescript.md](references/07-typescript.md) | Type definitions, typed events, server/client types, best practices |
| [08-scaling-and-adapters.md](references/08-scaling-and-adapters.md) | Multi-node scaling, adapters, sticky sessions, load balancing |
| [09-error-handling-and-debugging.md](references/09-error-handling-and-debugging.md) | Debugging, logging, disconnect reasons, troubleshooting |
| [10-delivery-and-reliability.md](references/10-delivery-and-reliability.md) | Delivery guarantees, connection state recovery, retries, ordering |
| [11-performance-and-security.md](references/11-performance-and-security.md) | Performance tuning, CORS, security patterns, memory optimization |
| [12-testing.md](references/12-testing.md) | Unit testing, integration testing, Jest/Vitest/Mocha patterns |

## Installation

```bash
# Server
npm install socket.io

# Client (browser or Node.js)
npm install socket.io-client
```

## Quick Reference

- [Official Docs](https://socket.io/docs/v4/)
- [GitHub Repository](https://github.com/socketio/socket.io)
- [npm Package](https://www.npmjs.com/package/socket.io)
- [Server API](https://socket.io/docs/v4/server-api/)
- [Client API](https://socket.io/docs/v4/client-api/)
