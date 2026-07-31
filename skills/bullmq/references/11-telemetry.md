# BullMQ — Telemetry & Observability

> Source: [docs.bullmq.io/guide/telemetry](https://docs.bullmq.io/guide/telemetry)

## Overview

BullMQ provides a Telemetry interface that integrates with OpenTelemetry — the de-facto standard for distributed tracing and metrics. The `bullmq-otel` package provides the OpenTelemetry-compliant implementation, enabling automatic trace propagation across queue boundaries and job lifecycle visibility.

## Installation

```bash
# BullMQ OpenTelemetry integration
npm install bullmq-otel

# OpenTelemetry SDK (required)
npm install @opentelemetry/sdk-node \
  @opentelemetry/sdk-trace-node \
  @opentelemetry/exporter-trace-otlp-http \
  @opentelemetry/resources \
  @opentelemetry/semantic-conventions
```

## Basic Setup

### Configure Queue with Telemetry

```typescript
import { Queue } from 'bullmq';
import { BullMQOtel } from 'bullmq-otel';

const queue = new Queue('my-queue', {
  connection: { host: '127.0.0.1', port: 6379 },
  telemetry: new BullMQOtel('my-service'),
});
```

### Configure Worker with Telemetry

```typescript
import { Worker } from 'bullmq';
import { BullMQOtel } from 'bullmq-otel';

const worker = new Worker(
  'my-queue',
  async (job) => {
    // Processing is automatically traced
    return { processed: true };
  },
  {
    connection: { host: '127.0.0.1', port: 6379 },
    telemetry: new BullMQOtel('my-service'),
  }
);
```

### Configure FlowProducer with Telemetry

```typescript
import { FlowProducer } from 'bullmq';
import { BullMQOtel } from 'bullmq-otel';

const flowProducer = new FlowProducer({
  connection: { host: '127.0.0.1', port: 6379 },
  telemetry: new BullMQOtel('my-service'),
});
```

## OpenTelemetry SDK Setup

Set up the OTel SDK to export traces to a backend (Jaeger, Grafana Tempo, Datadog, etc.):

```typescript
// tracing.ts — load before any BullMQ imports
import { NodeSDK } from '@opentelemetry/sdk-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { Resource } from '@opentelemetry/resources';
import { ATTR_SERVICE_NAME } from '@opentelemetry/semantic-conventions';

const sdk = new NodeSDK({
  resource: new Resource({
    [ATTR_SERVICE_NAME]: 'my-worker-service',
  }),
  traceExporter: new OTLPTraceExporter({
    url: 'http://localhost:4318/v1/traces', // Jaeger OTLP endpoint
  }),
});

sdk.start();

process.on('SIGTERM', () => {
  sdk.shutdown().then(() => process.exit(0));
});
```

## Traces

When telemetry is enabled, BullMQ automatically creates spans for:

### Producer Spans
- **Queue.add** — span created when a job is added to the queue
- **FlowProducer.add** — span for flow creation

### Consumer Spans
- **Worker.process** — span wrapping the entire processor function execution
- Automatically linked to the producer span via trace context propagation

### Span Attributes

Spans include useful attributes:

| Attribute | Description |
|-----------|-------------|
| `messaging.system` | `bullmq` |
| `messaging.destination` | Queue name |
| `messaging.message.id` | Job ID |
| `messaging.operation` | `publish` or `process` |
| `bullmq.job.name` | Job name |
| `bullmq.job.attempts` | Number of attempts made |

## Trace Context Propagation

Traces automatically propagate across process boundaries through job metadata:

```
Service A (Producer)        Redis        Service B (Worker)
┌─────────────┐                         ┌──────────────────┐
│ queue.add() │ ──── job + context ────> │ worker.process() │
│  [Span A]   │                         │    [Span B]      │
└─────────────┘                         └──────────────────┘
      │                                         │
      └─────────── Same Trace ID ───────────────┘
```

This enables end-to-end visibility: a request that triggers a background job shows the full trace from HTTP request through queue processing.

## Metrics

BullMQ's built-in metrics (separate from OTel) track job completion and failure rates:

```typescript
const queue = new Queue('my-queue', {
  metrics: {
    maxDataPoints: 60 * 24, // 24 hours of per-minute data
  },
});

// Retrieve completed metrics
const completed = await queue.getMetrics('completed');
// { meta: { count: 1000, prevCount: 950 }, data: [...] }

// Retrieve failed metrics
const failed = await queue.getMetrics('failed');
```

### Custom Prometheus Exporter

Build a Prometheus-compatible metrics endpoint:

```typescript
import { Queue } from 'bullmq';
import express from 'express';

const app = express();
const queue = new Queue('tasks');

app.get('/metrics', async (req, res) => {
  const counts = await queue.getJobCounts(
    'wait', 'active', 'completed', 'failed', 'delayed'
  );

  const metrics = [
    `# TYPE bullmq_jobs_waiting gauge`,
    `bullmq_jobs_waiting{queue="tasks"} ${counts.wait}`,
    `# TYPE bullmq_jobs_active gauge`,
    `bullmq_jobs_active{queue="tasks"} ${counts.active}`,
    `# TYPE bullmq_jobs_completed counter`,
    `bullmq_jobs_completed{queue="tasks"} ${counts.completed}`,
    `# TYPE bullmq_jobs_failed counter`,
    `bullmq_jobs_failed{queue="tasks"} ${counts.failed}`,
    `# TYPE bullmq_jobs_delayed gauge`,
    `bullmq_jobs_delayed{queue="tasks"} ${counts.delayed}`,
  ].join('\n');

  res.set('Content-Type', 'text/plain');
  res.send(metrics);
});

app.listen(9090);
```

## Running Jaeger Locally

```bash
# Start Jaeger all-in-one with OTLP support
docker run -d --name jaeger \
  -e COLLECTOR_OTLP_ENABLED=true \
  -p 16686:16686 \
  -p 4317:4317 \
  -p 4318:4318 \
  jaegertracing/all-in-one:latest
```

Access the Jaeger UI at `http://localhost:16686` to view traces.

## Taskforce.sh Dashboard

BullMQ offers an official monitoring dashboard at [taskforce.sh](https://taskforce.sh) that provides:

- Real-time queue monitoring
- Job inspection and management
- Worker status tracking
- Metrics visualization

```typescript
// Connect via Taskforce agent
// See https://taskforce.sh for setup instructions
```

## Bull Board (Open Source)

[Bull Board](https://github.com/felixmosh/bull-board) is a popular open-source dashboard:

```bash
npm install @bull-board/api @bull-board/express
```

```typescript
import { createBullBoard } from '@bull-board/api';
import { BullMQAdapter } from '@bull-board/api/bullMQAdapter';
import { ExpressAdapter } from '@bull-board/express';

const serverAdapter = new ExpressAdapter();
serverAdapter.setBasePath('/admin/queues');

createBullBoard({
  queues: [new BullMQAdapter(queue)],
  serverAdapter,
});

app.use('/admin/queues', serverAdapter.getRouter());
```

## Common Pitfalls

1. **Load tracing setup before BullMQ** — OTel SDK must be initialized before any BullMQ imports for auto-instrumentation
2. **Both producer and worker need telemetry** — trace context only propagates if both sides have `BullMQOtel` configured
3. **Metrics data points are bounded** — set `maxDataPoints` high enough for your retention needs
4. **Connection overhead** — telemetry adds minimal overhead but increases the data stored in Redis

## Related Topics

- [Events](./09-events.md) — Event-based monitoring
- [Production](./12-production-nestjs.md) — Production monitoring setup
- [Workers](./02-workers.md) — Worker configuration
