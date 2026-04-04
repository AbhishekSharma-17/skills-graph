# OpenTelemetry — Logs

> Source: [opentelemetry.io/docs/concepts/signals/logs](https://opentelemetry.io/docs/concepts/signals/logs/)

## Table of Contents

- [OTel Logs Approach](#otel-logs-approach)
- [Log Data Model](#log-data-model)
- [Log Severity Levels](#log-severity-levels)
- [Logs Bridge API](#logs-bridge-api)
- [Python Logging Integration](#python-logging-integration)
- [Node.js Logging Integration](#nodejs-logging-integration)
- [Correlating Logs with Traces](#correlating-logs-with-traces)
- [Collector Log Processing](#collector-log-processing)
- [Structured vs Unstructured Logs](#structured-vs-unstructured-logs)
- [Best Practices](#best-practices)
- [Common Pitfalls](#common-pitfalls)

---

## OTel Logs Approach

Unlike traces and metrics where OTel provides new APIs, for logs OTel takes a **bridge approach** — it integrates with existing logging frameworks (Python's `logging`, Winston, Pino, Log4j) rather than replacing them. This means:

1. **Application developers** continue using their existing logging library
2. **The OTel Logs Bridge API** connects the logging library to the OTel pipeline
3. **Log records** are enriched with trace context (trace_id, span_id) automatically
4. **The Collector** can receive, process, and export logs alongside traces and metrics

```
┌─────────────┐     ┌───────────────┐     ┌────────────┐
│ Python      │     │ OTel Logs     │     │ OTel       │
│ logging     │────▶│ Bridge API    │────▶│ Collector  │──▶ Backend
│ stdlib      │     │ + Handler     │     │            │
└─────────────┘     └───────────────┘     └────────────┘
```

## Log Data Model

Every OTel log record contains these fields:

| Field | Type | Description |
|-------|------|-------------|
| `Timestamp` | nanoseconds | When the event occurred |
| `ObservedTimestamp` | nanoseconds | When the log was collected |
| `TraceId` | bytes | Associated trace ID (from active span) |
| `SpanId` | bytes | Associated span ID (from active span) |
| `TraceFlags` | byte | W3C trace flags (sampled bit) |
| `SeverityText` | string | Log level string (`INFO`, `ERROR`, etc.) |
| `SeverityNumber` | int | Numeric severity (1-24) |
| `Body` | any | The log message content |
| `Resource` | map | Service identity (name, version, environment) |
| `InstrumentationScope` | map | Logger name and version |
| `Attributes` | map | Additional structured key-value data |

## Log Severity Levels

OTel defines a numeric severity scale that maps to common logging frameworks:

| OTel Number | OTel Name | Python | Node.js (Winston) |
|-------------|-----------|--------|-------------------|
| 1-4 | TRACE | — | silly |
| 5-8 | DEBUG | DEBUG | debug |
| 9-12 | INFO | INFO | info |
| 13-16 | WARN | WARNING | warn |
| 17-20 | ERROR | ERROR | error |
| 21-24 | FATAL | CRITICAL | — |

## Logs Bridge API

The Bridge API is for **logging library authors and integrators**, not application developers. It provides:

- **LoggerProvider**: Factory for creating Loggers (configured once at startup)
- **Logger**: Emits log records (used by bridge implementations)
- **LogRecord**: The data structure representing a single log entry
- **LogRecordProcessor**: Processes records before export (similar to SpanProcessor)
- **LogRecordExporter**: Sends records to backends

## Python Logging Integration

```python
import logging
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import (
    BatchLogRecordProcessor,
    ConsoleLogRecordExporter,
)
from opentelemetry.sdk.resources import Resource

# 1. Configure LoggerProvider
resource = Resource.create({"service.name": "my-service"})
logger_provider = LoggerProvider(resource=resource)

# 2. Add a processor with an exporter
logger_provider.add_log_record_processor(
    BatchLogRecordProcessor(ConsoleLogRecordExporter())
)
set_logger_provider(logger_provider)

# 3. Attach OTel handler to Python logging
handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)

# 4. Configure Python logging as usual
logging.basicConfig(level=logging.INFO, handlers=[handler])
logger = logging.getLogger(__name__)

# 5. Use standard Python logging — OTel handles the rest
logger.info("Order processed", extra={"order_id": "ORD-123", "amount": 99.99})
logger.error("Payment failed", extra={"order_id": "ORD-456", "error": "card_declined"})
```

### With OTLP exporter:

```python
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter

logger_provider.add_log_record_processor(
    BatchLogRecordProcessor(
        OTLPLogExporter(endpoint="localhost:4317", insecure=True)
    )
)
```

## Node.js Logging Integration

```typescript
import { LoggerProvider, BatchLogRecordProcessor } from "@opentelemetry/sdk-logs";
import { OTLPLogExporter } from "@opentelemetry/exporter-logs-otlp-grpc";
import { logs } from "@opentelemetry/api-logs";

const loggerProvider = new LoggerProvider();
loggerProvider.addLogRecordProcessor(
  new BatchLogRecordProcessor(new OTLPLogExporter({ url: "http://localhost:4317" }))
);
logs.setGlobalLoggerProvider(loggerProvider);

// With Winston bridge
import { OpenTelemetryTransportV3 } from "@opentelemetry/winston-transport";
import winston from "winston";

const logger = winston.createLogger({
  transports: [
    new winston.transports.Console(),
    new OpenTelemetryTransportV3(),  // Sends to OTel pipeline
  ],
});

logger.info("Order processed", { order_id: "ORD-123" });
```

## Correlating Logs with Traces

The main value of OTel logs is automatic correlation with traces. When a log is emitted within an active span, the log record automatically includes the trace_id and span_id:

```python
from opentelemetry import trace

tracer = trace.get_tracer("my.service")
logger = logging.getLogger(__name__)

def process_order(order_id):
    with tracer.start_as_current_span("process_order") as span:
        # This log automatically includes trace_id and span_id
        logger.info(f"Processing order {order_id}")

        try:
            charge_payment(order_id)
        except Exception as e:
            # Error log is correlated with the same trace
            logger.error(f"Payment failed for {order_id}: {e}")
            span.set_status(trace.Status(trace.StatusCode.ERROR))
            raise
```

**Result:** In your observability backend, you can click on a trace and see all related logs, or click on a log and jump to its trace.

## Collector Log Processing

The Collector can receive logs from multiple sources and process them:

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
  # Parse log files directly
  filelog:
    include: [/var/log/myapp/*.log]
    operators:
      - type: json_parser
        timestamp:
          parse_from: attributes.timestamp
          layout: "%Y-%m-%dT%H:%M:%S.%LZ"

processors:
  # Filter out noisy logs
  filter:
    logs:
      exclude:
        match_type: strict
        bodies: ["health check"]
  # Add attributes
  attributes:
    actions:
      - key: environment
        value: production
        action: insert

exporters:
  otlp:
    endpoint: loki:4317

service:
  pipelines:
    logs:
      receivers: [otlp, filelog]
      processors: [filter, attributes]
      exporters: [otlp]
```

## Structured vs Unstructured Logs

| Type | Example | OTel Recommendation |
|------|---------|-------------------|
| **Structured** | `{"level":"INFO","msg":"order processed","order_id":"123"}` | Preferred — attributes map directly |
| **Semi-structured** | `2026-01-01 INFO order_id=123 order processed` | Parseable with Collector operators |
| **Unstructured** | `Order 123 processed successfully` | Least useful — hard to query |

**Best approach:** Use structured logging with your framework, and let OTel handle the export:

```python
import structlog

# structlog naturally produces structured logs
logger = structlog.get_logger()
logger.info("order.processed", order_id="ORD-123", amount=99.99, currency="USD")
```

## Best Practices

1. **Use the bridge API** — Don't replace your logging framework; bridge it to OTel
2. **Include trace context** — The main value of OTel logs is trace correlation
3. **Use structured logging** — Key-value attributes are searchable; plain strings are not
4. **Set severity correctly** — Map your framework's levels to OTel severity numbers
5. **Use BatchLogRecordProcessor** — Same as traces: don't block on synchronous export
6. **Add resource attributes** — `service.name`, `service.version`, `deployment.environment`

## Common Pitfalls

1. **Using the Logger API directly** — The Logs Bridge API is for library authors. Application developers should use their standard logging framework with an OTel bridge/handler.
2. **Missing trace correlation** — If logs don't include trace_id, ensure the LoggingHandler is attached and spans are active when logs are emitted.
3. **Double-exporting** — If you bridge to OTel AND write to stdout, and the Collector also reads stdout, you get duplicates. Choose one path.
4. **Log volume explosion** — Unlike sampled traces, logs are usually not sampled. Use the Collector's filter processor to drop noisy logs.
