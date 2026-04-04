# OpenTelemetry — JavaScript/Node.js SDK

> Source: [opentelemetry.io/docs/languages/js](https://opentelemetry.io/docs/languages/js/)

## Table of Contents

- [Package Structure](#package-structure)
- [NodeSDK Setup](#nodesdk-setup)
- [Auto-Instrumentation](#auto-instrumentation)
- [Manual Tracing](#manual-tracing)
- [Manual Metrics](#manual-metrics)
- [Context Management](#context-management)
- [Express Integration](#express-integration)
- [Fastify Integration](#fastify-integration)
- [Next.js Integration](#nextjs-integration)
- [HTTP Client Instrumentation](#http-client-instrumentation)
- [Database Instrumentation](#database-instrumentation)
- [Exporter Configuration](#exporter-configuration)
- [Browser Instrumentation](#browser-instrumentation)
- [Common Pitfalls](#common-pitfalls)

---

## Package Structure

```
@opentelemetry/api                    # API interfaces (library dependency)
@opentelemetry/sdk-node               # Node.js SDK (one-stop setup)
@opentelemetry/sdk-trace-node         # Trace SDK for Node.js
@opentelemetry/sdk-trace-web          # Trace SDK for browsers
@opentelemetry/sdk-metrics            # Metrics SDK
@opentelemetry/sdk-logs               # Logs SDK
@opentelemetry/semantic-conventions   # Standard attribute names
@opentelemetry/auto-instrumentations-node  # All Node.js instrumentations
@opentelemetry/exporter-trace-otlp-grpc   # OTLP trace exporter (gRPC)
@opentelemetry/exporter-trace-otlp-http   # OTLP trace exporter (HTTP)
@opentelemetry/exporter-metrics-otlp-grpc # OTLP metrics exporter
```

**Runtime support:** Active or Maintenance LTS versions of Node.js. TypeScript support follows DefinitelyTyped 2-year window.

**Signal maturity:**

| Signal | Status |
|--------|--------|
| Traces | Stable |
| Metrics | Stable |
| Logs | Development |

## NodeSDK Setup

The `NodeSDK` class provides a one-stop setup for all signals:

```typescript
// tracing.ts — import BEFORE your app code
import { NodeSDK } from "@opentelemetry/sdk-node";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-grpc";
import { OTLPMetricExporter } from "@opentelemetry/exporter-metrics-otlp-grpc";
import { PeriodicExportingMetricReader } from "@opentelemetry/sdk-metrics";
import { getNodeAutoInstrumentations } from "@opentelemetry/auto-instrumentations-node";
import { Resource } from "@opentelemetry/resources";
import { ATTR_SERVICE_NAME, ATTR_SERVICE_VERSION } from "@opentelemetry/semantic-conventions";

const sdk = new NodeSDK({
  resource: new Resource({
    [ATTR_SERVICE_NAME]: "order-service",
    [ATTR_SERVICE_VERSION]: "2.1.0",
  }),
  traceExporter: new OTLPTraceExporter({ url: "http://localhost:4317" }),
  metricReader: new PeriodicExportingMetricReader({
    exporter: new OTLPMetricExporter({ url: "http://localhost:4317" }),
    exportIntervalMillis: 10000,
  }),
  instrumentations: [getNodeAutoInstrumentations()],
});

sdk.start();

// Graceful shutdown
process.on("SIGTERM", () => {
  sdk.shutdown().then(() => process.exit(0));
});
```

**Important:** The SDK must be initialized BEFORE importing your application code. Use `--require` or dynamic imports:

```bash
# Using --require flag
node --require ./tracing.js app.js

# Using --import for ESM
node --import ./tracing.mjs app.mjs
```

## Auto-Instrumentation

```bash
npm install @opentelemetry/auto-instrumentations-node
```

Auto-instruments: `http`, `express`, `fastify`, `koa`, `pg`, `mysql`, `redis`, `ioredis`, `mongodb`, `grpc`, `aws-sdk`, `fetch`, and more.

```typescript
import { getNodeAutoInstrumentations } from "@opentelemetry/auto-instrumentations-node";

const instrumentations = getNodeAutoInstrumentations({
  // Disable specific instrumentations
  "@opentelemetry/instrumentation-fs": { enabled: false },
  // Configure specific ones
  "@opentelemetry/instrumentation-http": {
    ignoreIncomingRequestHook: (req) => req.url === "/health",
  },
});
```

## Manual Tracing

```typescript
import { trace, SpanStatusCode, SpanKind } from "@opentelemetry/api";

const tracer = trace.getTracer("my.module", "1.0.0");

// Active span (recommended) — sets as current in context
function processOrder(orderId: string) {
  return tracer.startActiveSpan("process_order", (span) => {
    try {
      span.setAttribute("order.id", orderId);
      span.addEvent("validation.started");

      const result = validateAndCharge(orderId);

      span.addEvent("processing.complete", { items: result.itemCount });
      return result;
    } catch (err) {
      span.setStatus({ code: SpanStatusCode.ERROR, message: String(err) });
      span.recordException(err as Error);
      throw err;
    } finally {
      span.end();  // MUST call end()
    }
  });
}

// With span options
tracer.startActiveSpan(
  "external_call",
  {
    kind: SpanKind.CLIENT,
    attributes: { "peer.service": "payment-api" },
  },
  (span) => {
    // ...
    span.end();
  }
);

// Nested spans
function handleRequest(req: Request) {
  return tracer.startActiveSpan("handle_request", (parentSpan) => {
    const result = tracer.startActiveSpan("validate", (childSpan) => {
      const valid = validate(req);
      childSpan.end();
      return valid;
    });
    parentSpan.end();
    return result;
  });
}
```

## Manual Metrics

```typescript
import { metrics } from "@opentelemetry/api";

const meter = metrics.getMeter("my.module", "1.0.0");

// Counter
const requestCounter = meter.createCounter("http.requests", {
  unit: "1",
  description: "Total HTTP requests",
});
requestCounter.add(1, { "http.method": "GET", "http.route": "/api/users" });

// Histogram
const latencyHistogram = meter.createHistogram("http.request.duration", {
  unit: "ms",
  description: "Request latency",
});
latencyHistogram.record(42.5, { "http.method": "POST" });

// UpDownCounter
const activeConns = meter.createUpDownCounter("connections.active", { unit: "1" });
activeConns.add(1);   // connection opened
activeConns.add(-1);  // connection closed

// Observable Gauge (async)
meter.createObservableGauge("system.memory.usage", {
  unit: "By",
  description: "Process memory usage",
}).addCallback((result) => {
  const mem = process.memoryUsage();
  result.observe(mem.heapUsed, { "memory.type": "heap" });
  result.observe(mem.rss, { "memory.type": "rss" });
});
```

## Context Management

JavaScript's context management is different from Python's:

```typescript
import { context, trace } from "@opentelemetry/api";

// Get current span from context
const currentSpan = trace.getSpan(context.active());

// Run code with a specific context
const ctx = trace.setSpan(context.active(), mySpan);
context.with(ctx, () => {
  // Inside this callback, mySpan is the active span
  const innerSpan = trace.getSpan(context.active()); // === mySpan
});

// Propagate across async boundaries
async function asyncWork() {
  // context.active() automatically propagates in async/await
  return tracer.startActiveSpan("async_work", async (span) => {
    await someAsyncOperation();
    span.end();
  });
}
```

## Express Integration

```typescript
import express from "express";
import { ExpressInstrumentation } from "@opentelemetry/instrumentation-express";
import { HttpInstrumentation } from "@opentelemetry/instrumentation-http";

// Add to NodeSDK instrumentations
const sdk = new NodeSDK({
  instrumentations: [
    new HttpInstrumentation(),
    new ExpressInstrumentation({
      ignoreLayersType: ["middleware"],  // Skip middleware spans
    }),
  ],
});

// Or use auto-instrumentations which includes both
```

## Fastify Integration

```typescript
import { FastifyInstrumentation } from "@opentelemetry/instrumentation-fastify";

const sdk = new NodeSDK({
  instrumentations: [
    new FastifyInstrumentation(),
  ],
});
```

## Next.js Integration

```typescript
// instrumentation.ts (Next.js 13.4+)
export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    const { NodeSDK } = await import("@opentelemetry/sdk-node");
    const { OTLPTraceExporter } = await import("@opentelemetry/exporter-trace-otlp-http");

    const sdk = new NodeSDK({
      traceExporter: new OTLPTraceExporter(),
      instrumentations: [/* ... */],
    });
    sdk.start();
  }
}
```

```typescript
// next.config.js
module.exports = {
  experimental: {
    instrumentationHook: true,
  },
};
```

## HTTP Client Instrumentation

```typescript
import { HttpInstrumentation } from "@opentelemetry/instrumentation-http";

new HttpInstrumentation({
  // Ignore outgoing health checks
  ignoreOutgoingRequestHook: (req) =>
    req.hostname === "localhost" && req.path === "/health",

  // Add custom attributes
  requestHook: (span, request) => {
    span.setAttribute("custom.header", request.getHeader("x-request-id") ?? "");
  },

  // Capture response info
  responseHook: (span, response) => {
    span.setAttribute("http.response.content_length", response.headers["content-length"] ?? 0);
  },
});
```

## Database Instrumentation

```typescript
// PostgreSQL (pg)
import { PgInstrumentation } from "@opentelemetry/instrumentation-pg";
new PgInstrumentation({ enhancedDatabaseReporting: true });

// MongoDB
import { MongoDBInstrumentation } from "@opentelemetry/instrumentation-mongodb";
new MongoDBInstrumentation({ enhancedDatabaseReporting: true });

// Redis (ioredis)
import { IORedisInstrumentation } from "@opentelemetry/instrumentation-ioredis";
new IORedisInstrumentation();

// Prisma
import { PrismaInstrumentation } from "@prisma/instrumentation";
new PrismaInstrumentation();
```

## Exporter Configuration

```typescript
// OTLP/gRPC
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-grpc";
new OTLPTraceExporter({
  url: "http://localhost:4317",
  headers: { "api-key": "secret" },
});

// OTLP/HTTP (works in more environments)
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
new OTLPTraceExporter({ url: "http://localhost:4318/v1/traces" });

// Console (development)
import { ConsoleSpanExporter } from "@opentelemetry/sdk-trace-node";
new ConsoleSpanExporter();

// Environment variable configuration
// OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
// OTEL_EXPORTER_OTLP_HEADERS=api-key=secret
```

## Browser Instrumentation

```typescript
import { WebTracerProvider } from "@opentelemetry/sdk-trace-web";
import { ZoneContextManager } from "@opentelemetry/context-zone";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { BatchSpanProcessor } from "@opentelemetry/sdk-trace-base";
import { registerInstrumentations } from "@opentelemetry/instrumentation";
import { DocumentLoadInstrumentation } from "@opentelemetry/instrumentation-document-load";
import { FetchInstrumentation } from "@opentelemetry/instrumentation-fetch";

const provider = new WebTracerProvider({
  resource: new Resource({ [ATTR_SERVICE_NAME]: "frontend-app" }),
});

provider.addSpanProcessor(
  new BatchSpanProcessor(
    new OTLPTraceExporter({ url: "https://collector.example.com/v1/traces" })
  )
);

// Zone.js context manager for browser
provider.register({ contextManager: new ZoneContextManager() });

registerInstrumentations({
  instrumentations: [
    new DocumentLoadInstrumentation(),
    new FetchInstrumentation({ propagateTraceHeaderCorsUrls: [/api\.example\.com/] }),
  ],
});
```

## Common Pitfalls

1. **SDK not loaded before app code** — Auto-instrumentation patches modules on import. If your app imports `express` before the SDK initializes, it won't be instrumented. Use `--require` or load SDK first.

2. **Forgetting `span.end()`** — Unlike Python's context manager, JavaScript requires explicit `span.end()`. Use `try/finally` to ensure it's called.

3. **Context loss in callbacks** — Node.js async hooks handle most cases, but manual callback-based APIs may lose context. Use `context.bind()` for those.

4. **Browser CORS issues** — Browser instrumentation sends to a collector. Ensure the collector has CORS configured (`allowed_origins: ["*"]`) or use a same-origin proxy.

5. **Large bundle in browser** — OTel packages are tree-shakeable but still add size. Import only what you need for browser builds.

6. **Missing HTTP instrumentation** — Express instrumentation alone doesn't capture HTTP details. You need BOTH `HttpInstrumentation` and `ExpressInstrumentation` together.
