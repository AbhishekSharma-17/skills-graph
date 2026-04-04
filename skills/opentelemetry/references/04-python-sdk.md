# OpenTelemetry — Python SDK

> Source: [opentelemetry.io/docs/languages/python](https://opentelemetry.io/docs/languages/python/)

## Table of Contents

- [Package Structure](#package-structure)
- [Auto-Instrumentation](#auto-instrumentation)
- [Manual Instrumentation Setup](#manual-instrumentation-setup)
- [Tracing API](#tracing-api)
- [Metrics API](#metrics-api)
- [Logs API](#logs-api)
- [Context Propagation](#context-propagation)
- [Resource Configuration](#resource-configuration)
- [Exporter Configuration](#exporter-configuration)
- [FastAPI Integration](#fastapi-integration)
- [Django Integration](#django-integration)
- [Flask Integration](#flask-integration)
- [Database Instrumentation](#database-instrumentation)
- [Testing with OTel](#testing-with-otel)
- [Common Pitfalls](#common-pitfalls)

---

## Package Structure

```
opentelemetry-api              # API interfaces (library dependency)
opentelemetry-sdk              # SDK implementation (app dependency)
opentelemetry-semantic-conventions  # Standard attribute names
opentelemetry-exporter-otlp    # OTLP exporter (meta-package)
├── opentelemetry-exporter-otlp-proto-grpc   # gRPC transport
├── opentelemetry-exporter-otlp-proto-http   # HTTP transport
opentelemetry-distro           # Auto-instrumentation distro
opentelemetry-instrumentation  # Auto-instrumentation bootstrapper
opentelemetry-instrumentation-<lib>  # Per-library instrumentations
```

**Python version:** 3.9+

**Signal maturity:**

| Signal | Status |
|--------|--------|
| Traces | Stable |
| Metrics | Stable |
| Logs | Stable (SDK development ongoing) |

## Auto-Instrumentation

The fastest way to add OTel to an existing application:

```bash
# Install distro and bootstrap tool
pip install opentelemetry-distro opentelemetry-instrumentation

# Auto-detect and install all available instrumentations
opentelemetry-bootstrap -a install

# Run your app with auto-instrumentation
OTEL_SERVICE_NAME=my-service \
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 \
opentelemetry-instrument python app.py
```

**What gets instrumented automatically:**

- HTTP frameworks: FastAPI, Flask, Django, aiohttp, Starlette
- HTTP clients: requests, urllib3, httpx, aiohttp-client
- Databases: psycopg2, SQLAlchemy, pymongo, redis, mysql-connector
- Message queues: celery, pika (RabbitMQ), kafka-python
- gRPC: grpcio
- AWS: boto3, botocore

## Manual Instrumentation Setup

For full control, configure the SDK programmatically:

```python
from opentelemetry import trace, metrics
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter

# Shared resource across all signals
resource = Resource.create({
    "service.name": "order-service",
    "service.version": "2.1.0",
    "deployment.environment": "production",
})

# Traces
trace_provider = TracerProvider(resource=resource)
trace_provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="localhost:4317", insecure=True))
)
trace.set_tracer_provider(trace_provider)

# Metrics
metric_reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(endpoint="localhost:4317", insecure=True),
    export_interval_millis=10000,
)
metric_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(metric_provider)

# Logs
log_provider = LoggerProvider(resource=resource)
log_provider.add_log_record_processor(
    BatchLogRecordProcessor(OTLPLogExporter(endpoint="localhost:4317", insecure=True))
)
set_logger_provider(log_provider)
```

## Tracing API

```python
tracer = trace.get_tracer("my.module")

# Context manager — automatic start/end
with tracer.start_as_current_span("operation") as span:
    span.set_attribute("key", "value")
    span.add_event("checkpoint", {"detail": "processed 100 items"})

# Decorator
@tracer.start_as_current_span("compute")
def compute_result(data):
    return expensive_computation(data)

# Get current span (from any function in the call chain)
current = trace.get_current_span()
current.set_attribute("result.count", 42)

# Exception recording
with tracer.start_as_current_span("risky") as span:
    try:
        might_fail()
    except Exception as ex:
        span.set_status(trace.Status(trace.StatusCode.ERROR, str(ex)))
        span.record_exception(ex)
        raise

# Manual span lifecycle (when context manager won't work)
span = tracer.start_span("manual")
try:
    do_work()
finally:
    span.end()
```

## Metrics API

```python
meter = metrics.get_meter("my.module")

# Counter
request_count = meter.create_counter("http.requests", unit="1")
request_count.add(1, {"method": "GET", "route": "/api/users"})

# Histogram
latency = meter.create_histogram("http.request.duration", unit="ms")
latency.record(42.5, {"method": "POST", "route": "/api/orders"})

# UpDownCounter
active = meter.create_up_down_counter("connections.active", unit="1")
active.add(1)   # connection opened
active.add(-1)  # connection closed

# Gauge
meter.create_gauge("cpu.temperature", unit="Cel").set(67.3)

# Async instrument
def memory_callback(options):
    import psutil
    yield metrics.Observation(psutil.virtual_memory().percent)

meter.create_observable_gauge("memory.percent", callbacks=[memory_callback], unit="1")
```

## Logs API

```python
import logging
from opentelemetry.sdk._logs import LoggingHandler

handler = LoggingHandler(level=logging.INFO, logger_provider=log_provider)
logging.basicConfig(level=logging.INFO, handlers=[handler])
logger = logging.getLogger("my.module")

# Standard Python logging — OTel handles enrichment and export
logger.info("Processing order", extra={"order_id": "ORD-123"})
logger.warning("Slow query detected", extra={"duration_ms": 1500, "table": "orders"})
logger.error("Failed to process payment", exc_info=True)
```

## Context Propagation

```python
from opentelemetry.propagate import inject, extract
from opentelemetry import context

# Inject context into outgoing HTTP headers
headers = {}
inject(headers)
# headers now contains: {"traceparent": "00-<trace_id>-<span_id>-01", ...}

# Extract context from incoming HTTP headers
ctx = extract(request.headers)
with tracer.start_as_current_span("handle", context=ctx):
    process_request()

# Manual context attachment for async code
token = context.attach(ctx)
try:
    do_work()
finally:
    context.detach(token)
```

## Resource Configuration

```python
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION

# From code
resource = Resource.create({
    SERVICE_NAME: "my-service",
    SERVICE_VERSION: "1.0.0",
    "deployment.environment": "production",
    "host.name": "web-01",
})

# From environment variable
# OTEL_RESOURCE_ATTRIBUTES="service.name=my-service,deployment.environment=prod"
resource = Resource.create()  # Reads env var automatically
```

## Exporter Configuration

```python
# OTLP/gRPC (most common)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
exporter = OTLPSpanExporter(
    endpoint="localhost:4317",
    insecure=True,         # No TLS (dev only)
    headers={"api-key": "secret"},
    timeout=10,            # seconds
)

# OTLP/HTTP
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
exporter = OTLPSpanExporter(endpoint="http://localhost:4318/v1/traces")

# Console (debugging)
from opentelemetry.sdk.trace.export import ConsoleSpanExporter
exporter = ConsoleSpanExporter()

# Configure via environment variables (no code changes)
# OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
# OTEL_EXPORTER_OTLP_PROTOCOL=grpc
# OTEL_EXPORTER_OTLP_HEADERS=api-key=secret
```

## FastAPI Integration

```python
from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

app = FastAPI()

# Auto-instrument all routes
FastAPIInstrumentor.instrument_app(app)

# Or with custom settings
FastAPIInstrumentor.instrument_app(
    app,
    excluded_urls="health,ready",  # Skip health endpoints
    server_request_hook=lambda span, scope: span.set_attribute("custom.attr", "value"),
)

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    # Span is automatically created for this endpoint
    return {"user_id": user_id}
```

## Django Integration

```python
# settings.py
INSTALLED_APPS = [
    "opentelemetry.instrumentation.django",
    # ...
]

# Or programmatic setup in manage.py / wsgi.py
from opentelemetry.instrumentation.django import DjangoInstrumentor
DjangoInstrumentor().instrument()
```

## Flask Integration

```python
from flask import Flask
from opentelemetry.instrumentation.flask import FlaskInstrumentor

app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)
```

## Database Instrumentation

```python
# SQLAlchemy
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
SQLAlchemyInstrumentor().instrument(engine=engine)

# psycopg2
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
Psycopg2Instrumentor().instrument()

# Redis
from opentelemetry.instrumentation.redis import RedisInstrumentor
RedisInstrumentor().instrument()
```

## Testing with OTel

```python
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory import InMemorySpanExporter

def setup_test_telemetry():
    """Create an in-memory exporter for test assertions."""
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return exporter

def test_order_creates_span():
    exporter = setup_test_telemetry()
    process_order("ORD-123")

    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "process_order"
    assert spans[0].attributes["order.id"] == "ORD-123"

    exporter.clear()
```

## Common Pitfalls

1. **Importing SDK in library code** — Libraries should only import `opentelemetry-api`. The application configures the SDK. If no SDK is configured, the API becomes a no-op.

2. **Not shutting down providers** — Call `trace_provider.shutdown()` and `metric_provider.shutdown()` on app exit or you lose buffered data.

3. **Blocking the event loop** — Use gRPC exporter for async apps (it's non-blocking). HTTP exporter blocks during export.

4. **Missing `opentelemetry-bootstrap`** — Auto-instrumentation won't detect libraries unless you run `opentelemetry-bootstrap -a install` to install instrumentation packages.

5. **Context loss in async code** — In Python's asyncio, context propagates automatically. But with thread pools or multiprocessing, you must explicitly propagate context.

6. **Over-instrumenting** — Don't add manual spans inside auto-instrumented frameworks. FastAPI auto-instrumentation already creates spans for each request — adding more creates noise.
