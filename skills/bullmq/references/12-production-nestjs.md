# BullMQ — Production & NestJS Integration

> Source: [docs.bullmq.io/guide/going-to-production](https://docs.bullmq.io/guide/going-to-production) · [docs.bullmq.io/guide/nestjs](https://docs.bullmq.io/guide/nestjs)

## Table of Contents

- [Production Checklist](#production-checklist)
- [Redis Configuration](#redis-configuration)
- [Graceful Shutdown](#graceful-shutdown)
- [Error Handling](#error-handling)
- [Security](#security)
- [Scaling](#scaling)
- [NestJS Integration](#nestjs-integration)

---

## Production Checklist

Before deploying BullMQ to production, verify these items:

| Item | Status | Detail |
|------|--------|--------|
| Redis `maxmemory-policy` | Required | Must be `noeviction` |
| Redis persistence (AOF) | Recommended | `appendfsync everysec` |
| Worker error handlers | Required | Attach `error` event listener |
| Graceful shutdown | Required | Handle SIGINT/SIGTERM |
| Auto-removal configured | Recommended | Prevent unbounded Redis growth |
| Connection retry settings | Required | Workers: `maxRetriesPerRequest: null` |
| Stalled job handling | Recommended | Configure `lockDuration` and `maxStalledCount` |
| Monitoring | Recommended | QueueEvents, metrics, or dashboard |

## Redis Configuration

### Required

```redis
# MANDATORY — never let Redis evict BullMQ keys
maxmemory-policy noeviction
```

### Recommended

```redis
# AOF persistence — ~1s write intervals balance durability and performance
appendonly yes
appendfsync everysec

# RDB snapshots as additional safety net
save 900 1
save 300 10
save 60 10000

# Adequate memory
maxmemory 2gb
```

### Connection Resilience

Differentiate connection settings by component role:

```typescript
// Queues (producers): fail fast when Redis is unavailable
const queue = new Queue('tasks', {
  connection: {
    host: 'redis.example.com',
    enableOfflineQueue: false,  // throw immediately on disconnect
  },
});

// Workers: retry indefinitely during temporary disconnections
const worker = new Worker('tasks', processor, {
  connection: {
    host: 'redis.example.com',
    maxRetriesPerRequest: null,  // never give up
    enableOfflineQueue: true,     // queue commands during disconnect
  },
});
```

BullMQ implements exponential backoff for reconnection: minimum 1 second, maximum 20 seconds.

## Graceful Shutdown

Prevent stalled jobs during deployments and restarts:

```typescript
import { Worker } from 'bullmq';

const worker = new Worker('tasks', processor);

const gracefulShutdown = async (signal: string) => {
  console.log(`Received ${signal}, closing worker...`);

  // Waits for currently active jobs to finish
  await worker.close();

  console.log('Worker closed gracefully');
  process.exit(0);
};

process.on('SIGINT', () => gracefulShutdown('SIGINT'));
process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
```

### Multiple Workers

```typescript
const workers = [
  new Worker('emails', emailProcessor),
  new Worker('reports', reportProcessor),
  new Worker('notifications', notifProcessor),
];

const shutdown = async (signal: string) => {
  console.log(`${signal} received, shutting down ${workers.length} workers...`);
  await Promise.all(workers.map(w => w.close()));
  process.exit(0);
};

process.on('SIGINT', () => shutdown('SIGINT'));
process.on('SIGTERM', () => shutdown('SIGTERM'));
```

## Error Handling

### Worker Error Events

```typescript
// REQUIRED — unhandled error events crash the process
worker.on('error', (err) => {
  logger.error('Worker error:', err);
});

queue.on('error', (err) => {
  logger.error('Queue error:', err);
});
```

### Unhandled Exceptions

```typescript
process.on('uncaughtException', (err) => {
  logger.error('Uncaught exception:', err);
  // Graceful shutdown recommended
});

process.on('unhandledRejection', (reason, promise) => {
  logger.error('Unhandled rejection:', { promise, reason });
});
```

### Processor Error Handling

```typescript
const worker = new Worker('tasks', async (job) => {
  try {
    return await processJob(job.data);
  } catch (err) {
    // Log with context
    logger.error('Job processing failed', {
      jobId: job.id,
      jobName: job.name,
      attempt: job.attemptsMade,
      error: err.message,
    });

    // Re-throw to trigger retry mechanism
    throw err;
  }
});
```

## Security

### Sensitive Data

Avoid storing sensitive data in job payloads:

```typescript
// BAD — API keys in job data
await queue.add('call-api', {
  url: 'https://api.example.com',
  apiKey: 'sk-secret-key',  // stored in Redis
});

// GOOD — reference secrets from environment/vault
await queue.add('call-api', {
  url: 'https://api.example.com',
  secretRef: 'API_KEY_EXTERNAL',  // worker reads from env
});
```

### Data Encryption

If sensitive data must be in job payloads:

```typescript
import crypto from 'crypto';

const ENCRYPTION_KEY = process.env.JOB_ENCRYPTION_KEY;

function encrypt(data: object): string {
  const iv = crypto.randomBytes(16);
  const cipher = crypto.createCipheriv('aes-256-gcm', ENCRYPTION_KEY, iv);
  const encrypted = Buffer.concat([cipher.update(JSON.stringify(data)), cipher.final()]);
  const tag = cipher.getAuthTag();
  return `${iv.toString('hex')}:${tag.toString('hex')}:${encrypted.toString('hex')}`;
}

function decrypt(encrypted: string): object {
  const [ivHex, tagHex, dataHex] = encrypted.split(':');
  const decipher = crypto.createDecipheriv('aes-256-gcm', ENCRYPTION_KEY, Buffer.from(ivHex, 'hex'));
  decipher.setAuthTag(Buffer.from(tagHex, 'hex'));
  const decrypted = Buffer.concat([decipher.update(Buffer.from(dataHex, 'hex')), decipher.final()]);
  return JSON.parse(decrypted.toString());
}

// Encrypt when adding
await queue.add('secure-task', { payload: encrypt({ ssn: '123-45-6789' }) });

// Decrypt in worker
const worker = new Worker('queue', async (job) => {
  const data = decrypt(job.data.payload);
});
```

## Scaling

### Horizontal Scaling

Deploy multiple worker processes across machines:

```typescript
// Deploy on N machines, each running:
const worker = new Worker('tasks', processor, {
  concurrency: 20,  // 20 parallel jobs per process
  connection: { host: 'redis.shared.example.com' },
});
```

### Auto-Removal for Memory

```typescript
const queue = new Queue('high-throughput', {
  defaultJobOptions: {
    removeOnComplete: { count: 500 },      // keep last 500 completed
    removeOnFail: { age: 86400, count: 1000 }, // 24h or 1000 failed
  },
});
```

### Queue Draining for Maintenance

```typescript
// Before maintenance: stop accepting new jobs
await queue.pause();

// Wait for in-flight jobs
const checkDrained = setInterval(async () => {
  const active = await queue.getJobCountByTypes('active');
  if (active === 0) {
    clearInterval(checkDrained);
    console.log('All jobs drained, safe for maintenance');
  }
}, 1000);
```

---

## NestJS Integration

### Installation

```bash
npm install @nestjs/bullmq bullmq
```

### Module Setup

```typescript
// app.module.ts
import { Module } from '@nestjs/common';
import { BullModule } from '@nestjs/bullmq';

@Module({
  imports: [
    // Global Redis connection
    BullModule.forRoot({
      connection: {
        host: 'localhost',
        port: 6379,
      },
    }),

    // Register queues
    BullModule.registerQueue({ name: 'emails' }),
    BullModule.registerQueue({ name: 'reports' }),

    // Register flow producers
    BullModule.registerFlowProducer({ name: 'order-flow' }),
  ],
})
export class AppModule {}
```

### Processor (Worker)

```typescript
// email.processor.ts
import { Processor, WorkerHost, OnWorkerEvent } from '@nestjs/bullmq';
import { Job } from 'bullmq';

@Processor('emails')
export class EmailProcessor extends WorkerHost {
  async process(job: Job<{ to: string; subject: string; body: string }>) {
    await this.mailService.send(job.data);
    return { sent: true };
  }

  @OnWorkerEvent('completed')
  onCompleted(job: Job) {
    console.log(`Email job ${job.id} completed`);
  }

  @OnWorkerEvent('failed')
  onFailed(job: Job, error: Error) {
    console.error(`Email job ${job.id} failed:`, error.message);
  }
}
```

Register as a provider:

```typescript
@Module({
  imports: [BullModule.registerQueue({ name: 'emails' })],
  providers: [EmailProcessor],
})
export class EmailModule {}
```

### Producer (Adding Jobs)

```typescript
// order.service.ts
import { InjectQueue } from '@nestjs/bullmq';
import { Queue } from 'bullmq';

@Injectable()
export class OrderService {
  constructor(@InjectQueue('emails') private emailQueue: Queue) {}

  async createOrder(order: CreateOrderDto) {
    // ... save order ...

    await this.emailQueue.add('order-confirmation', {
      to: order.email,
      subject: 'Order Confirmed',
      body: `Your order #${order.id} has been placed.`,
    }, {
      attempts: 3,
      backoff: { type: 'exponential', delay: 1000 },
    });
  }
}
```

### Flow Producer

```typescript
import { InjectFlowProducer } from '@nestjs/bullmq';
import { FlowProducer } from 'bullmq';

@Injectable()
export class OrderFlowService {
  constructor(
    @InjectFlowProducer('order-flow') private flowProducer: FlowProducer
  ) {}

  async processOrder(orderId: string) {
    await this.flowProducer.add({
      name: 'fulfill-order',
      queueName: 'orders',
      data: { orderId },
      children: [
        { name: 'validate-payment', queueName: 'payments', data: { orderId } },
        { name: 'reserve-inventory', queueName: 'inventory', data: { orderId } },
      ],
    });
  }
}
```

### Queue Events Listener

```typescript
import { QueueEventsHost, QueueEventsListener, OnQueueEvent } from '@nestjs/bullmq';

@QueueEventsListener('emails')
export class EmailEventsListener extends QueueEventsHost {
  @OnQueueEvent('completed')
  onCompleted({ jobId, returnvalue }: { jobId: string; returnvalue: string }) {
    console.log(`[Global] Email ${jobId} completed:`, returnvalue);
  }

  @OnQueueEvent('failed')
  onFailed({ jobId, failedReason }: { jobId: string; failedReason: string }) {
    console.error(`[Global] Email ${jobId} failed:`, failedReason);
  }
}
```

### Async Configuration

```typescript
BullModule.forRootAsync({
  imports: [ConfigModule],
  inject: [ConfigService],
  useFactory: (config: ConfigService) => ({
    connection: {
      host: config.get('REDIS_HOST'),
      port: config.get('REDIS_PORT'),
      password: config.get('REDIS_PASSWORD'),
    },
  }),
});
```

## Common Pitfalls

1. **Graceful shutdown is critical** — without it, active jobs become stalled on every deploy
2. **Always set error handlers** — both on workers and queues
3. **Auto-removal prevents OOM** — without cleanup, Redis grows indefinitely
4. **NestJS processors must extend `WorkerHost`** — plain classes won't work
5. **Register processors as providers** — they must be in the module's `providers` array
6. **Test with `queue.add()` mocks in NestJS** — use `@InjectQueue` for testability

## Related Topics

- [Connections](./10-connections.md) — Redis configuration
- [Telemetry](./11-telemetry.md) — OpenTelemetry observability
- [Events](./09-events.md) — Monitoring job lifecycle
