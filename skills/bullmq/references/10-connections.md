# BullMQ — Connections & Redis Configuration

> Source: [docs.bullmq.io/guide/connections](https://docs.bullmq.io/guide/connections)

## Overview

BullMQ requires a Redis-compatible backend for all operations. It supports multiple Redis client libraries (ioredis, node-redis, Bun's built-in client, Valkey Glide) and various Redis-compatible services. Each BullMQ class consumes at least one Redis connection.

## Default Connection

Without configuration, BullMQ connects to `localhost:6379`:

```typescript
import { Queue } from 'bullmq';

// Connects to localhost:6379
const queue = new Queue('my-queue');
```

### Custom Connection

```typescript
const queue = new Queue('my-queue', {
  connection: {
    host: 'redis.example.com',
    port: 6379,
    password: 'secret',
    db: 0,
    tls: {},  // enable TLS
  },
});
```

## Redis Client Adapters

### ioredis (Default)

```typescript
import IORedis from 'ioredis';

// Create a shared connection
const connection = new IORedis({
  host: 'redis.example.com',
  port: 6379,
  password: 'secret',
  maxRetriesPerRequest: null,  // REQUIRED for workers
});

// Share across queue instances
const queue1 = new Queue('queue-1', { connection });
const queue2 = new Queue('queue-2', { connection });
```

### node-redis (v5+)

```typescript
import { createClient } from 'redis';
import { createNodeRedisClient, Queue } from 'bullmq';

const rawClient = createClient({ url: 'redis://localhost:6379' });
await rawClient.connect();

const connection = createNodeRedisClient(rawClient);
const queue = new Queue('my-queue', { connection });
```

### Bun Built-in Client

```typescript
import { RedisClient } from 'bun';
import { createBunRedisClient, Queue } from 'bullmq';

const rawClient = new RedisClient('redis://localhost:6379');
const connection = createBunRedisClient(rawClient);
const queue = new Queue('my-queue', { connection });
```

### Valkey Glide

```typescript
import { createValkeyGlideClient, Queue } from 'bullmq';

const connection = createValkeyGlideClient(rawClient);
const queue = new Queue('my-queue', { connection });
```

## Global Client Factory

Override the default Redis client creation for all BullMQ instances:

```typescript
import { RedisConnection, Queue, Worker } from 'bullmq';
import { createClient } from 'redis';
import { createNodeRedisClient } from 'bullmq';

RedisConnection.clientFactory = (opts) => {
  const rawClient = createClient({
    socket: { host: opts.host, port: opts.port },
    password: opts.password,
    database: opts.db,
  });
  return createNodeRedisClient(rawClient);
};

// All new instances now use node-redis
const queue = new Queue('my-queue', {
  connection: { host: 'redis.example.com', port: 6379 },
});
```

## Connection Reuse

### Queue Instances (Producers)

Multiple queues can share a single connection:

```typescript
const connection = new IORedis();

const emailQueue = new Queue('emails', { connection });
const reportQueue = new Queue('reports', { connection });
```

### Worker Instances

Workers need `maxRetriesPerRequest: null` for shared connections:

```typescript
const connection = new IORedis({ maxRetriesPerRequest: null });

const worker1 = new Worker('queue-1', processor1, { connection });
const worker2 = new Worker('queue-2', processor2, { connection });
```

**Important:** Workers and QueueEvents internally duplicate their connection for blocking operations. This means each Worker/QueueEvents instance creates 2 Redis connections.

## Connection Count Planning

| Class | Connections Used |
|-------|-----------------|
| Queue | 1 |
| Worker | 2 (main + blocking subscriber) |
| QueueEvents | 2 (main + stream subscriber) |
| FlowProducer | 1 |

Example: 3 queues + 3 workers + 1 QueueEvents = 3 + 6 + 2 = **11 connections**.

## Key Configuration Settings

### maxRetriesPerRequest

```typescript
// Queues (producers): default is fine, fail fast on disconnect
const queue = new Queue('queue', {
  connection: { host: 'localhost' },  // uses default maxRetriesPerRequest
});

// Workers: MUST be null for persistent reconnection
const worker = new Worker('queue', processor, {
  connection: {
    host: 'localhost',
    maxRetriesPerRequest: null,  // REQUIRED
  },
});
```

### enableOfflineQueue

```typescript
// Queues: disable to fail fast when Redis is down
const queue = new Queue('queue', {
  connection: { enableOfflineQueue: false },
});

// Workers: enable for persistent retry
const worker = new Worker('queue', processor, {
  connection: { enableOfflineQueue: true, maxRetriesPerRequest: null },
});
```

### Key Prefix

```typescript
// Use BullMQ's prefix option — NOT ioredis keyPrefix
const queue = new Queue('emails', {
  prefix: 'myapp',  // keys: myapp:emails:*
  connection: { host: 'localhost' },
});

// WARNING: Do NOT use ioredis keyPrefix
const connection = new IORedis({ keyPrefix: 'myapp' }); // BROKEN
```

## Redis Configuration Requirements

### Required Settings

```redis
# MANDATORY — prevents BullMQ keys from being evicted
maxmemory-policy noeviction
```

### Recommended Settings

```redis
# Enable AOF persistence with ~1s sync interval
appendonly yes
appendfsync everysec

# Enable RDB snapshots as backup
save 900 1
save 300 10
save 60 10000
```

## Compatible Redis Backends

| Backend | Notes |
|---------|-------|
| Redis 6.2+ | Full support |
| Redis 7.x | Full support, recommended |
| Dragonfly | Supported with some caveats |
| AWS MemoryDB | Full support |
| AWS ElastiCache | Full support |
| Upstash | Works but may have rate limits |
| KeyDB | Community-reported compatibility |

### Dragonfly Configuration

```typescript
const queue = new Queue('my-queue', {
  connection: {
    host: 'dragonfly.example.com',
    port: 6379,
  },
});
```

### AWS MemoryDB / ElastiCache

```typescript
const queue = new Queue('my-queue', {
  connection: {
    host: 'my-cluster.abc123.memorydb.us-east-1.amazonaws.com',
    port: 6379,
    tls: {},  // TLS required for MemoryDB
  },
});
```

## Connection Error Handling

```typescript
const worker = new Worker('queue', processor, {
  connection: { host: 'redis.example.com', maxRetriesPerRequest: null },
});

worker.on('error', (err) => {
  if (err.message.includes('ECONNREFUSED')) {
    console.error('Redis connection lost, will auto-reconnect');
  } else {
    console.error('Worker error:', err);
  }
});
```

BullMQ implements exponential backoff for reconnection: minimum 1 second, maximum 20 seconds.

## Common Pitfalls

1. **`maxRetriesPerRequest: null` required for workers** — without this, workers throw after a few retries during temporary disconnections
2. **Never use ioredis `keyPrefix`** — it conflicts with BullMQ's internal key management; use BullMQ's `prefix` option
3. **`maxmemory-policy` must be `noeviction`** — arbitrary key eviction breaks queue state completely
4. **Count your connections** — each Worker/QueueEvents uses 2 connections; plan for managed Redis connection limits
5. **TLS for cloud Redis** — AWS MemoryDB and many managed services require TLS

## Related Topics

- [Queues](./01-queues.md) — Queue creation and management
- [Workers](./02-workers.md) — Worker connection needs
- [Production](./12-production-nestjs.md) — Production Redis configuration
