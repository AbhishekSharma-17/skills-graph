# Socket.IO Scaling and Adapters

> Source: https://socket.io/docs/v4/using-multiple-nodes/ | https://socket.io/docs/v4/adapter/

## Table of Contents

- [Why Scaling Matters](#why-scaling-matters)
- [Sticky Sessions](#sticky-sessions)
- [Adapters Overview](#adapters-overview)
- [Redis Adapter](#redis-adapter)
- [Other Adapters](#other-adapters)
- [Load Balancer Configuration](#load-balancer-configuration)
- [WebSocket-Only Mode](#websocket-only-mode)
- [Node.js Cluster](#nodejs-cluster)

## Why Scaling Matters

A single Socket.IO server handles connections in-memory. When scaling to multiple servers, two problems arise:

1. **Session affinity** — HTTP long-polling uses multiple requests per session; all must reach the same server
2. **Cross-server broadcasting** — `io.emit()` only reaches clients on the current server

Adapters solve #2 by relaying events between servers. Sticky sessions solve #1.

## Sticky Sessions

Sticky sessions ensure all requests from a client reach the same server instance. Required when HTTP long-polling is enabled (the default).

### Why They're Needed

HTTP long-polling uses successive HTTP requests. If request 1 goes to server A and request 2 goes to server B, server B won't recognize the session ID, returning error code 1: "Session ID unknown."

### When NOT Needed

- WebSocket-only transport (`transports: ["websocket"]`)
- Single server deployment
- Client-side load balancing

## Adapters Overview

An adapter broadcasts events to all or subsets of clients across multiple servers.

### Available Adapters

| Adapter | Package | Backend |
|---------|---------|---------|
| In-memory | Built-in | None (single server) |
| Redis | `@socket.io/redis-adapter` | Redis Pub/Sub |
| Redis Streams | `@socket.io/redis-streams-adapter` | Redis Streams |
| MongoDB | `@socket.io/mongo-adapter` | MongoDB Change Streams |
| PostgreSQL | `@socket.io/postgres-adapter` | PostgreSQL LISTEN/NOTIFY |
| Cluster | `@socket.io/cluster-adapter` | Node.js cluster IPC |
| GCP Pub/Sub | `@socket.io/gcp-pubsub-adapter` | Google Cloud Pub/Sub |
| AWS SQS | `@socket.io/aws-sqs-adapter` | Amazon SQS |
| Azure Service Bus | `@socket.io/azure-service-bus-adapter` | Azure Service Bus |

### Community Adapters

- AMQP (RabbitMQ)
- NATS

## Redis Adapter

The most common adapter for production deployments.

### Setup

```bash
npm install @socket.io/redis-adapter redis
```

```javascript
import { Server } from "socket.io";
import { createAdapter } from "@socket.io/redis-adapter";
import { createClient } from "redis";

const io = new Server(httpServer);

const pubClient = createClient({ url: "redis://localhost:6379" });
const subClient = pubClient.duplicate();

await Promise.all([pubClient.connect(), subClient.connect()]);

io.adapter(createAdapter(pubClient, subClient));

io.on("connection", (socket) => {
  // io.emit() now reaches ALL servers
  io.emit("hello", "world");
});
```

### How It Works

1. Server A calls `io.to("room1").emit("event", data)`
2. Redis adapter publishes the event to a Redis Pub/Sub channel
3. All other servers subscribed to the channel receive the event
4. Each server emits to its local clients in "room1"

### Redis Streams Adapter

Alternative with better reliability (messages aren't lost if a server is temporarily down):

```bash
npm install @socket.io/redis-streams-adapter redis
```

```javascript
import { createAdapter } from "@socket.io/redis-streams-adapter";
import { createClient } from "redis";

const client = createClient({ url: "redis://localhost:6379" });
await client.connect();

io.adapter(createAdapter(client));
```

## Other Adapters

### MongoDB Adapter

```bash
npm install @socket.io/mongo-adapter mongodb
```

```javascript
import { createAdapter } from "@socket.io/mongo-adapter";
import { MongoClient } from "mongodb";

const mongoClient = new MongoClient("mongodb://localhost:27017");
await mongoClient.connect();

const collection = mongoClient.db("socketio").collection("events");

// Create capped collection (required)
try {
  await mongoClient.db("socketio").createCollection("events", {
    capped: true,
    size: 1e6 // 1MB
  });
} catch (e) {
  // collection may already exist
}

io.adapter(createAdapter(collection));
```

### PostgreSQL Adapter

```bash
npm install @socket.io/postgres-adapter pg
```

```javascript
import { createAdapter } from "@socket.io/postgres-adapter";
import { Pool } from "pg";

const pool = new Pool({ connectionString: "postgresql://..." });

io.adapter(createAdapter(pool));
```

### Cluster Adapter

For Node.js `cluster` module (single machine, multiple processes):

```bash
npm install @socket.io/cluster-adapter
```

```javascript
import cluster from "node:cluster";
import { createAdapter, setupPrimary } from "@socket.io/cluster-adapter";

if (cluster.isPrimary) {
  setupPrimary();
  for (let i = 0; i < os.cpus().length; i++) {
    cluster.fork();
  }
} else {
  const io = new Server(httpServer);
  io.adapter(createAdapter());
}
```

## Load Balancer Configuration

### Nginx

```nginx
upstream socketio_servers {
    hash $remote_addr consistent;  # sticky by IP
    server 127.0.0.1:3001;
    server 127.0.0.1:3002;
    server 127.0.0.1:3003;
}

server {
    listen 80;
    server_name example.com;

    location /socket.io/ {
        proxy_pass http://socketio_servers;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # Must exceed pingInterval + pingTimeout (45s default)
        proxy_read_timeout 60s;
    }
}
```

### HAProxy

```
defaults
    mode http
    timeout connect 5s
    timeout client 60s
    timeout server 60s

frontend http_front
    bind *:80
    default_backend socketio_back

backend socketio_back
    balance roundrobin
    cookie io prefix indirect nocache
    server srv1 127.0.0.1:3001 check cookie srv1
    server srv2 127.0.0.1:3002 check cookie srv2
```

## WebSocket-Only Mode

Eliminates the need for sticky sessions by skipping HTTP long-polling:

```javascript
// Server
const io = new Server(httpServer, {
  transports: ["websocket"]
});

// Client
const socket = io("http://localhost:3000", {
  transports: ["websocket"]
});
```

**Trade-offs:**
- No sticky session requirement
- Slightly faster initial connection
- May fail behind restrictive proxies/firewalls that block WebSocket upgrades
- No fallback transport

## Node.js Cluster

### Using @socket.io/sticky

```bash
npm install @socket.io/sticky @socket.io/cluster-adapter
```

```javascript
import cluster from "node:cluster";
import http from "node:http";
import os from "node:os";
import { setupMaster } from "@socket.io/sticky";
import { setupPrimary, createAdapter } from "@socket.io/cluster-adapter";

if (cluster.isPrimary) {
  const httpServer = http.createServer();

  setupMaster(httpServer, {
    loadBalancingMethod: "least-connection"
  });
  setupPrimary();

  httpServer.listen(3000);

  for (let i = 0; i < os.cpus().length; i++) {
    cluster.fork();
  }
} else {
  const httpServer = http.createServer();
  const io = new Server(httpServer);

  io.adapter(createAdapter());

  io.on("connection", (socket) => {
    // works across all workers
  });
}
```

## Scaling Checklist

1. Enable an adapter (Redis is the most common choice)
2. Configure sticky sessions at the load balancer (or use WebSocket-only)
3. Set `proxy_read_timeout` > `pingInterval + pingTimeout`
4. Forward WebSocket upgrade headers (`Upgrade`, `Connection`)
5. Forward client IP (`X-Real-IP`, `X-Forwarded-For`)
6. Test cross-server broadcasting (`io.emit`, `io.to("room").emit`)
7. Test reconnection behavior after server restart
8. Monitor adapter health (Redis connection, latency)
