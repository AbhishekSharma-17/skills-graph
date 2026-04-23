# Cloudflare Queues — Message Queue

> Source: [developers.cloudflare.com/queues](https://developers.cloudflare.com/queues/)

## Table of Contents

- [What Are Queues](#what-are-queues)
- [Setup](#setup)
- [Producer API](#producer-api)
- [Consumer API](#consumer-api)
- [Message Lifecycle](#message-lifecycle)
- [Retry and Dead Letter Queues](#retry-and-dead-letter-queues)
- [Pull Consumers](#pull-consumers)
- [Consumer Concurrency](#consumer-concurrency)
- [Limits and Pricing](#limits-and-pricing)
- [Common Patterns](#common-patterns)

## What Are Queues

Cloudflare Queues is a managed message queue service that integrates with Workers. Messages are produced by one Worker and consumed by another (or the same) Worker.

**Best for:** Background jobs, webhook processing, event-driven architectures, decoupling services, batch processing, log ingestion.

Key features:
- At-least-once delivery guarantee
- Automatic batching for efficiency
- Configurable retry with dead-letter queues
- Pull-based consumers for external systems
- Delayed message delivery (up to 24 hours)

## Setup

```bash
# Create a queue
wrangler queues create my-queue

# Create a dead-letter queue
wrangler queues create my-dlq
```

```toml
# wrangler.toml

# Producer binding
[[queues.producers]]
binding = "MY_QUEUE"
queue = "my-queue"

# Consumer configuration
[[queues.consumers]]
queue = "my-queue"
max_batch_size = 10        # Messages per batch (1-100, default 10)
max_batch_timeout = 5      # Seconds to wait for full batch (default 5)
max_retries = 3            # Retry count before DLQ (default 3)
dead_letter_queue = "my-dlq"
max_concurrency = 10       # Parallel consumer instances
```

```typescript
interface Env {
  MY_QUEUE: Queue;
}
```

## Producer API

### send() — Single Message

```typescript
// JSON message (default)
await env.MY_QUEUE.send({ userId: 123, action: "signup" });

// String message
await env.MY_QUEUE.send("process-item-456", { contentType: "text" });

// Binary message
await env.MY_QUEUE.send(new ArrayBuffer(64), { contentType: "bytes" });

// Delayed delivery (up to 86400 seconds / 24 hours)
await env.MY_QUEUE.send({ task: "cleanup" }, { delaySeconds: 300 });

// V8 serialization (supports Date, Map, Set, etc.)
await env.MY_QUEUE.send({
  timestamp: new Date(),
  data: new Map([["key", "value"]]),
}, { contentType: "v8" });
```

### sendBatch() — Multiple Messages

```typescript
await env.MY_QUEUE.sendBatch([
  { body: { userId: 1, action: "email" } },
  { body: { userId: 2, action: "email" } },
  { body: { userId: 3, action: "email" }, delaySeconds: 60 },
]);

// With shared delay for all messages
await env.MY_QUEUE.sendBatch(
  messages.map((m) => ({ body: m })),
  { delaySeconds: 120 },
);
```

### TypeScript Types

```typescript
interface Queue<Body = unknown> {
  send(body: Body, options?: QueueSendOptions): Promise<void>;
  sendBatch(messages: Iterable<MessageSendRequest<Body>>, options?: QueueSendBatchOptions): Promise<void>;
}

interface QueueSendOptions {
  contentType?: "json" | "text" | "bytes" | "v8";
  delaySeconds?: number;  // 0-86400
}

interface MessageSendRequest<Body = unknown> {
  body: Body;
  contentType?: "json" | "text" | "bytes" | "v8";
  delaySeconds?: number;
}

interface QueueSendBatchOptions {
  delaySeconds?: number;
}
```

## Consumer API

### Queue Handler

```typescript
export default {
  // Producer: sends messages
  async fetch(request: Request, env: Env): Promise<Response> {
    await env.MY_QUEUE.send({ url: request.url });
    return new Response("Queued");
  },

  // Consumer: processes messages in batches
  async queue(batch: MessageBatch, env: Env, ctx: ExecutionContext): Promise<void> {
    for (const message of batch.messages) {
      try {
        await processMessage(message.body);
        message.ack();  // Mark as processed
      } catch (err) {
        message.retry({ delaySeconds: 30 });  // Retry later
      }
    }
  },
};
```

### MessageBatch Interface

```typescript
interface MessageBatch<Body = unknown> {
  readonly queue: string;                    // Queue name
  readonly messages: readonly Message<Body>[];
  ackAll(): void;                            // Acknowledge all messages
  retryAll(options?: { delaySeconds?: number }): void;  // Retry all
}
```

### Message Interface

```typescript
interface Message<Body = unknown> {
  readonly id: string;          // Unique message ID
  readonly timestamp: Date;     // When message was sent
  readonly body: Body;          // Message payload
  readonly attempts: number;    // Processing attempt count (starts at 1)
  ack(): void;                  // Mark as successfully processed
  retry(options?: { delaySeconds?: number }): void;  // Requeue for retry
}
```

### Acknowledgment Behavior

- If handler completes without calling `ack()` or `retry()` on a message, it's **auto-acknowledged**
- If handler throws, all unacknowledged messages are **retried**
- `ackAll()` acknowledges the entire batch
- `retryAll()` retries the entire batch

## Message Lifecycle

```
Producer → Queue → Batch → Consumer Handler
                              ├── ack()     → Removed from queue
                              ├── retry()   → Back to queue (with delay)
                              └── throws    → All unacked messages retried
                                               └── max_retries exceeded → Dead Letter Queue
```

## Retry and Dead Letter Queues

```toml
[[queues.consumers]]
queue = "my-queue"
max_retries = 5              # Retry up to 5 times
dead_letter_queue = "my-dlq" # Failed messages go here
```

DLQ consumer (separate or same Worker):

```typescript
export default {
  async queue(batch: MessageBatch, env: Env): Promise<void> {
    if (batch.queue === "my-dlq") {
      for (const msg of batch.messages) {
        console.error("DLQ message:", msg.body, "attempts:", msg.attempts);
        await alertTeam(msg);
        msg.ack();
      }
    }
  },
};
```

## Pull Consumers

Consume messages from external systems via HTTP:

```bash
# Enable pull consumer
wrangler queues consumer http add my-queue
```

```typescript
// External system pulls messages
const response = await fetch(
  `https://api.cloudflare.com/client/v4/accounts/${accountId}/queues/${queueId}/messages/pull`,
  {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      visibility_timeout_ms: 30000,  // 30s to process
      batch_size: 10,
    }),
  },
);

const { result } = await response.json();
for (const msg of result.messages) {
  await processExternally(msg.body);
}

// Acknowledge processed messages
await fetch(
  `https://api.cloudflare.com/client/v4/accounts/${accountId}/queues/${queueId}/messages/ack`,
  {
    method: "POST",
    headers: { Authorization: `Bearer ${apiToken}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      acks: result.messages.map((m: any) => ({ lease_id: m.lease_id })),
    }),
  },
);
```

## Consumer Concurrency

```toml
[[queues.consumers]]
queue = "my-queue"
max_concurrency = 20   # Up to 20 parallel consumer instances
max_batch_size = 50     # Each gets up to 50 messages
```

Concurrency scales automatically based on queue depth. Set `max_concurrency` to cap parallel consumers.

## Limits and Pricing

| Limit | Free | Paid |
|-------|------|------|
| Operations/day | 10,000 | 1M/mo + $0.40/million |
| Message size | 128 KB | 128 KB |
| Batch size | 100 | 100 |
| Retention | 24 hours | 4-14 days (configurable) |
| Delay | 24 hours max | 24 hours max |
| Max queues | 100 | 10,000 |
| Consumer concurrency | 20 | 250 |

An "operation" is any send, receive, or acknowledge action.

## Common Patterns

### Background Email Sending

```typescript
// Producer — API handler
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const { to, subject, body } = await request.json<EmailRequest>();

    await env.EMAIL_QUEUE.send({ to, subject, body, createdAt: Date.now() });
    return Response.json({ status: "queued" });
  },

  // Consumer — sends the email
  async queue(batch: MessageBatch<EmailRequest>, env: Env): Promise<void> {
    for (const msg of batch.messages) {
      try {
        await sendEmail(env.RESEND_API_KEY, msg.body);
        msg.ack();
      } catch (err) {
        if (msg.attempts >= 3) {
          await logFailure(env, msg.body);
          msg.ack(); // Don't retry forever
        } else {
          msg.retry({ delaySeconds: msg.attempts * 60 });
        }
      }
    }
  },
};
```

### Fan-Out Processing

```typescript
// Single producer → multiple queues
async function fanOut(env: Env, event: AppEvent) {
  await Promise.all([
    env.ANALYTICS_QUEUE.send(event),
    env.NOTIFICATION_QUEUE.send(event),
    env.AUDIT_LOG_QUEUE.send(event),
  ]);
}
```

## Common Pitfalls

- **At-least-once delivery** — Messages may be delivered more than once. Make consumers idempotent.
- **128 KB limit** — Message body max is 128 KB. For larger payloads, store in R2 and pass the key.
- **Auto-ack on success** — If your handler completes without errors, unacknowledged messages are auto-acked. Call `retry()` explicitly for messages you want retried.
- **Consumer in same Worker** — Producer and consumer can be in the same Worker file, but the consumer handler (`queue()`) only runs when messages are delivered, not on fetch requests.
- **No FIFO guarantee** — Messages may arrive out of order. Don't rely on ordering.
