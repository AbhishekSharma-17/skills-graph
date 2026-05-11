# QStash — Serverless Messaging & Scheduling

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Setup](#setup)
- [Publishing Messages](#publishing-messages)
- [Configuration Headers](#configuration-headers)
- [Scheduling (Cron Jobs)](#scheduling-cron-jobs)
- [Delayed Messages](#delayed-messages)
- [URL Groups (Fan-out)](#url-groups-fan-out)
- [Queues (FIFO)](#queues-fifo)
- [Callbacks](#callbacks)
- [Dead Letter Queue (DLQ)](#dead-letter-queue-dlq)
- [Batching](#batching)
- [Flow Control](#flow-control)
- [Signature Verification](#signature-verification)
- [Deduplication](#deduplication)
- [LLM Integration](#llm-integration)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

QStash is an HTTP-based message queue and task scheduler for serverless and edge
environments. Messages are published via HTTP and delivered as HTTP requests to
your endpoints.

- **At-least-once delivery** with automatic retries and exponential backoff
- **Cron scheduling**, delayed delivery, batching (up to 100 messages per call)
- **Callbacks** for success/failure notification, Dead Letter Queue for exhausted retries
- **Flow control** with rate limiting and parallelism per delivery target
- **URL Groups** for fan-out, **Queues** for ordered FIFO delivery
- **Deduplication**, signature verification, and LLM provider proxying
- Fully serverless — no infrastructure to manage

---

## Installation

```bash
npm install @upstash/qstash    # TypeScript / JavaScript
pip install qstash              # Python
```

## Setup

Create a QStash instance at [console.upstash.com](https://console.upstash.com)
and set environment variables:

```bash
QSTASH_TOKEN=your_qstash_token
QSTASH_CURRENT_SIGNING_KEY=your_current_signing_key   # for webhook verification
QSTASH_NEXT_SIGNING_KEY=your_next_signing_key          # rotated key pair
```

Two signing keys are used so verification works during key rotation — verify
against the current key first, then fall back to the next key.

---

## Publishing Messages

### REST API

```bash
curl -XPOST \
  -H 'Authorization: Bearer <QSTASH_TOKEN>' \
  -H "Content-type: application/json" \
  -d '{"hello": "world"}' \
  'https://qstash.upstash.io/v2/publish/https://your-endpoint.com'
```

### TypeScript SDK

```typescript
import { Client } from "@upstash/qstash";
const qstash = new Client({ token: process.env.QSTASH_TOKEN! });

const res = await qstash.publishJSON({
  url: "https://your-endpoint.com/api/process",
  body: { taskId: "123", action: "process" },
});
console.log(res.messageId);
```

### Python SDK

```python
from qstash import QStash
qstash = QStash(token="your_qstash_token")

res = qstash.message.publish_json(
    url="https://your-endpoint.com/api/process",
    body={"taskId": "123", "action": "process"},
)
print(res.message_id)
```

---

## Configuration Headers

All configuration headers use the `Upstash-` prefix:

| Header | Description | Example |
|--------|-------------|---------|
| `Upstash-Method` | HTTP method for delivery (default: POST) | `GET`, `PUT` |
| `Upstash-Delay` | Delay before first delivery attempt | `60s`, `5m`, `2h` |
| `Upstash-Retries` | Number of retry attempts (default: 3) | `5` |
| `Upstash-Timeout` | Timeout for each delivery attempt | `30s` |
| `Upstash-Callback` | URL called on successful delivery | Full URL |
| `Upstash-Failure-Callback` | URL called when all retries exhausted | Full URL |
| `Upstash-Forward-*` | Custom headers forwarded to destination | Any value |
| `Upstash-Cron` | Cron expression for recurring messages | `*/5 * * * *` |
| `Upstash-Content-Based-Deduplication-Id` | Auto dedup from body hash | `true` |
| `Upstash-Deduplication-Id` | Manual deduplication identifier | Any string |

SDK equivalent:

```typescript
await qstash.publishJSON({
  url: "https://your-endpoint.com/api/process",
  body: { taskId: "123" },
  retries: 5,
  delay: 60,
  timeout: "30s",
  headers: { "Upstash-Forward-X-Custom": "value" },
});
```

---

## Scheduling (Cron Jobs)

Schedules persist across deployments — no server needs to stay running.

```typescript
// Create a schedule
const schedule = await qstash.schedules.create({
  destination: "https://your-endpoint.com/api/daily-report",
  cron: "0 9 * * *",  // Every day at 9:00 AM UTC
  body: JSON.stringify({ type: "daily-report" }),
});

// List, get, pause, resume, delete
const schedules = await qstash.schedules.list();
const details = await qstash.schedules.get(schedule.scheduleId);
await qstash.schedules.pause({ schedule: schedule.scheduleId });
await qstash.schedules.resume({ schedule: schedule.scheduleId });
await qstash.schedules.delete(schedule.scheduleId);
```

Common cron expressions: `*/5 * * * *` (every 5 min), `0 * * * *` (hourly),
`0 9 * * *` (daily 9 AM), `0 9 * * 1-5` (weekdays), `0 0 1 * *` (monthly).

---

## Delayed Messages

```typescript
await qstash.publishJSON({
  url: "https://your-endpoint.com/api/reminder",
  body: { userId: "123", message: "Follow up with client" },
  delay: 3600,  // Deliver in 1 hour (seconds)
});
```

SDK accepts seconds as integer. REST header accepts unit suffixes: `30s`, `5m`,
`2h`, `1d`. Maximum delay: 7 days.

---

## URL Groups (Fan-out)

Fan-out delivers to ALL endpoints in the group (not load balancing).

```typescript
// Create URL group with endpoints
await qstash.urlGroups.addEndpoints({
  name: "notifications",
  endpoints: [
    { url: "https://service-a.com/webhook" },
    { url: "https://service-b.com/webhook" },
  ],
});

// Publish to all endpoints in group
await qstash.publishJSON({
  urlGroup: "notifications",
  body: { event: "user.created", userId: "123" },
});

// Manage groups
await qstash.urlGroups.removeEndpoints({
  name: "notifications",
  endpoints: [{ url: "https://service-b.com/webhook" }],
});
await qstash.urlGroups.delete("notifications");
```

---

## Queues (FIFO)

Ordered delivery with configurable parallelism. Parallelism of 1 gives strict
ordering; higher values increase throughput but may deliver out of order.

```typescript
const queue = qstash.queue({ queueName: "email-queue" });

await queue.enqueueJSON({
  url: "https://your-endpoint.com/api/send-email",
  body: { to: "user@example.com", subject: "Welcome" },
});

// Set parallelism (concurrent consumers)
await qstash.queue({ queueName: "email-queue" }).upsert({
  parallelism: 3,
});
```

---

## Callbacks

Receive notifications on delivery success or failure. Callback payload includes
messageId, HTTP status, base64-encoded response body, headers, and retry count.

```typescript
await qstash.publishJSON({
  url: "https://your-endpoint.com/api/process",
  body: { taskId: "123" },
  callback: "https://your-endpoint.com/api/on-success",
  failureCallback: "https://your-endpoint.com/api/on-failure",
});
```

Callback payload structure:

```json
{
  "status": 200,
  "body": "base64-encoded-response-body",
  "sourceMessageId": "msg_xxx",
  "sourceBody": "base64-encoded-original-body",
  "retried": 0,
  "maxRetries": 3
}
```

---

## Dead Letter Queue (DLQ)

Messages that exhaust all retries move to the DLQ automatically. DLQ retains
the original body, headers, destination, and last error response.

```typescript
// List failed messages
const dlqMessages = await qstash.dlq.listMessages();
for (const msg of dlqMessages.messages) {
  console.log(`Failed: ${msg.messageId} -> ${msg.url}`);
}

// Delete (acknowledge) or bulk delete
await qstash.dlq.delete(dlqMessageId);
await qstash.dlq.deleteMany({ dlqIds: [id1, id2, id3] });
```

---

## Batching

Send up to 100 messages in a single API call. Each message can have its own
destination, config (retries, delay, headers), and body.

```typescript
const messages = await qstash.batchJSON([
  { url: "https://service-a.com/api", body: { task: "a" }, retries: 3 },
  { url: "https://service-b.com/api", body: { task: "b" }, delay: 60 },
  { url: "https://service-c.com/api", body: { task: "c" } },
]);
```

---

## Flow Control

Limit delivery rate and concurrency per key to protect downstream services.

```typescript
await qstash.publishJSON({
  url: "https://your-endpoint.com/api/process",
  body: { taskId: "123" },
  flowControl: {
    key: "process-limit",
    ratePerSecond: 10,    // Max 10 deliveries per second
    parallelism: 5,        // Max 5 concurrent in-flight deliveries
  },
});
```

Multiple messages sharing the same `key` are collectively rate-limited. Useful
for protecting external APIs, controlling concurrency on heavy handlers, and
implementing backpressure.

---

## Signature Verification

Every QStash delivery includes an `Upstash-Signature` header (a JWT with body
hash, destination URL, and expiration). Always verify in production.

### TypeScript

```typescript
import { Receiver } from "@upstash/qstash";

const receiver = new Receiver({
  currentSigningKey: process.env.QSTASH_CURRENT_SIGNING_KEY!,
  nextSigningKey: process.env.QSTASH_NEXT_SIGNING_KEY!,
});

export async function POST(request: Request) {
  const body = await request.text();
  const signature = request.headers.get("upstash-signature")!;

  const isValid = await receiver.verify({ signature, body });
  if (!isValid) {
    return new Response("Invalid signature", { status: 401 });
  }

  const data = JSON.parse(body);
  // ... handle verified message
  return new Response("OK", { status: 200 });
}
```

### Python

```python
from qstash import Receiver

receiver = Receiver(
    current_signing_key="your_current_signing_key",
    next_signing_key="your_next_signing_key",
)
is_valid = receiver.verify(
    body=request_body,
    signature=request.headers["upstash-signature"],
)
```

---

## Deduplication

Prevent duplicate processing. Duplicates with the same ID are silently ignored.

```typescript
// Manual deduplication ID
await qstash.publishJSON({
  url: "https://your-endpoint.com/api/process",
  body: { orderId: "456" },
  deduplicationId: "order-456",
});

// Content-based deduplication (hash of body)
await qstash.publishJSON({
  url: "https://your-endpoint.com/api/process",
  body: { orderId: "456" },
  contentBasedDeduplication: true,
});
```

---

## LLM Integration

QStash proxies requests to LLM providers with built-in retries, callbacks, and
flow control. Offloads long-running LLM calls from timeout-limited serverless
functions.

```typescript
await qstash.publishJSON({
  api: { name: "llm", provider: "openai" },
  body: {
    model: "gpt-4",
    messages: [
      { role: "system", content: "You are a helpful assistant." },
      { role: "user", content: "Summarize this document..." },
    ],
  },
  callback: "https://your-endpoint.com/api/llm-response",
  failureCallback: "https://your-endpoint.com/api/llm-error",
});
```

Benefits: no serverless timeouts, automatic retries on transient failures,
async response via callback, rate limiting via flow control, all messages
logged in the QStash dashboard.

---

## Common Pitfalls

- **Endpoint accessibility** — destinations must be publicly accessible HTTP(S)
  endpoints. Use ngrok or Cloudflare Tunnels for local development.
- **Message size** — max body is 1 MB. Store large payloads externally and pass
  a reference URL in the message.
- **Cron timezone** — all schedule times are in UTC.
- **Idempotent handlers** — at-least-once delivery means your handlers must be
  idempotent. Use database constraints or idempotency keys.
- **Signature verification** — strongly recommended for production. Without it
  any HTTP client can impersonate QStash.
- **Retry backoff** — retries use exponential backoff (default: 3 attempts).
- **URL Groups are fan-out** — every endpoint gets every message. For load
  balancing use a single endpoint behind your own balancer or Queues.
- **Callback body encoding** — response body in callbacks is base64-encoded.
- **Queue parallelism** — parallelism > 1 increases throughput but messages may
  complete out of order. Use 1 for strict ordering.
