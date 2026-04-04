# OpenTelemetry — Semantic Conventions

> Source: [opentelemetry.io/docs/specs/semconv](https://opentelemetry.io/docs/specs/semconv/) | v1.40.0

## Table of Contents

- [What Are Semantic Conventions](#what-are-semantic-conventions)
- [Resource Attributes](#resource-attributes)
- [HTTP Conventions](#http-conventions)
- [Database Conventions](#database-conventions)
- [Messaging Conventions](#messaging-conventions)
- [RPC Conventions](#rpc-conventions)
- [General Conventions](#general-conventions)
- [Using Semantic Conventions in Code](#using-semantic-conventions-in-code)
- [Metric Naming Conventions](#metric-naming-conventions)
- [Best Practices](#best-practices)

---

## What Are Semantic Conventions

Semantic conventions define standard names for attributes, metrics, and spans across all OpenTelemetry implementations. They ensure that telemetry from different services, languages, and libraries is consistent and interoperable.

**Why they matter:**

- Backends can build dashboards that work across services
- Queries like "show all HTTP 500 errors" work regardless of language
- Alerting rules are portable across instrumented services
- Service maps auto-assemble from consistent attribute names

## Resource Attributes

Resource attributes identify the entity producing telemetry:

| Attribute | Example | Description |
|-----------|---------|-------------|
| `service.name` | `"order-service"` | Logical name of the service |
| `service.version` | `"2.1.0"` | Service version |
| `service.namespace` | `"shop"` | Namespace for grouping services |
| `service.instance.id` | `"pod-abc123"` | Unique instance identifier |
| `deployment.environment` | `"production"` | Deployment environment |
| `telemetry.sdk.name` | `"opentelemetry"` | SDK name |
| `telemetry.sdk.language` | `"python"` | SDK language |
| `telemetry.sdk.version` | `"1.20.0"` | SDK version |

**Infrastructure:**

| Attribute | Example | Description |
|-----------|---------|-------------|
| `host.name` | `"web-01"` | Hostname |
| `host.id` | `"i-0abc123"` | Unique host ID |
| `os.type` | `"linux"` | Operating system |
| `cloud.provider` | `"aws"` | Cloud provider |
| `cloud.region` | `"us-east-1"` | Cloud region |
| `cloud.availability_zone` | `"us-east-1a"` | Availability zone |
| `k8s.pod.name` | `"order-svc-abc"` | Kubernetes pod name |
| `k8s.namespace.name` | `"production"` | Kubernetes namespace |
| `k8s.deployment.name` | `"order-svc"` | Kubernetes deployment |
| `container.id` | `"abc123def"` | Container ID |

## HTTP Conventions

### HTTP Server Spans

| Attribute | Type | Example |
|-----------|------|---------|
| `http.request.method` | string | `"GET"`, `"POST"` |
| `http.route` | string | `"/api/users/{id}"` |
| `url.scheme` | string | `"https"` |
| `url.path` | string | `"/api/users/123"` |
| `http.response.status_code` | int | `200`, `404`, `500` |
| `server.address` | string | `"api.example.com"` |
| `server.port` | int | `443` |
| `user_agent.original` | string | `"Mozilla/5.0..."` |
| `client.address` | string | `"192.168.1.100"` |
| `network.protocol.version` | string | `"1.1"`, `"2"` |

**Span naming:** `{method} {route}` — e.g., `GET /api/users/{id}`

### HTTP Client Spans

| Attribute | Type | Example |
|-----------|------|---------|
| `http.request.method` | string | `"POST"` |
| `url.full` | string | `"https://api.example.com/v1/orders"` |
| `http.response.status_code` | int | `201` |
| `server.address` | string | `"api.example.com"` |
| `server.port` | int | `443` |

### HTTP Metrics

| Metric | Type | Unit |
|--------|------|------|
| `http.server.request.duration` | Histogram | `s` |
| `http.server.active_requests` | UpDownCounter | `1` |
| `http.server.request.body.size` | Histogram | `By` |
| `http.server.response.body.size` | Histogram | `By` |
| `http.client.request.duration` | Histogram | `s` |

## Database Conventions

| Attribute | Type | Example |
|-----------|------|---------|
| `db.system` | string | `"postgresql"`, `"mysql"`, `"redis"`, `"mongodb"` |
| `db.namespace` | string | `"mydb"` (database name) |
| `db.operation.name` | string | `"SELECT"`, `"INSERT"`, `"findOne"` |
| `db.query.text` | string | `"SELECT * FROM users WHERE id = $1"` |
| `db.collection.name` | string | `"users"` (table/collection) |
| `server.address` | string | `"db.example.com"` |
| `server.port` | int | `5432` |

**Span naming:** `{operation} {target}` — e.g., `SELECT users`, `redis GET`

**Security note:** `db.query.text` may contain sensitive data. Consider using the `attributes` processor to hash or redact it in the Collector.

## Messaging Conventions

| Attribute | Type | Example |
|-----------|------|---------|
| `messaging.system` | string | `"kafka"`, `"rabbitmq"`, `"sqs"` |
| `messaging.operation.type` | string | `"publish"`, `"receive"`, `"process"` |
| `messaging.destination.name` | string | `"orders"` (topic/queue) |
| `messaging.message.id` | string | `"msg-abc123"` |
| `messaging.kafka.consumer.group` | string | `"order-processors"` |
| `messaging.kafka.message.offset` | int | `42` |
| `messaging.message.body.size` | int | `1024` |

**Span naming:** `{destination} {operation}` — e.g., `orders publish`, `orders process`

## RPC Conventions

| Attribute | Type | Example |
|-----------|------|---------|
| `rpc.system` | string | `"grpc"`, `"jsonrpc"` |
| `rpc.service` | string | `"UserService"` |
| `rpc.method` | string | `"GetUser"` |
| `rpc.grpc.status_code` | int | `0` (OK), `2` (UNKNOWN) |
| `server.address` | string | `"grpc.example.com"` |
| `server.port` | int | `50051` |

**Span naming:** `{package}.{service}/{method}` — e.g., `myapp.UserService/GetUser`

## General Conventions

### Exception Attributes (span events)

| Attribute | Example |
|-----------|---------|
| `exception.type` | `"ValueError"` |
| `exception.message` | `"Invalid user ID"` |
| `exception.stacktrace` | Full stack trace string |

### Network Attributes

| Attribute | Example |
|-----------|---------|
| `network.transport` | `"tcp"`, `"udp"` |
| `network.protocol.name` | `"http"`, `"grpc"` |
| `network.protocol.version` | `"1.1"`, `"2"` |
| `network.peer.address` | `"10.0.0.5"` |
| `network.peer.port` | `8080` |

### Feature Flag Attributes

| Attribute | Example |
|-----------|---------|
| `feature_flag.key` | `"new-checkout-flow"` |
| `feature_flag.provider_name` | `"LaunchDarkly"` |
| `feature_flag.variant` | `"enabled"` |

## Using Semantic Conventions in Code

### Python

```python
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.semconv.resource import ResourceAttributes

# Resource
resource = Resource.create({
    ResourceAttributes.SERVICE_NAME: "my-service",
    ResourceAttributes.SERVICE_VERSION: "1.0.0",
    ResourceAttributes.DEPLOYMENT_ENVIRONMENT: "production",
})

# Span attributes
span.set_attribute(SpanAttributes.HTTP_REQUEST_METHOD, "GET")
span.set_attribute(SpanAttributes.HTTP_RESPONSE_STATUS_CODE, 200)
span.set_attribute(SpanAttributes.DB_SYSTEM, "postgresql")
```

### Node.js

```typescript
import {
  ATTR_SERVICE_NAME,
  ATTR_HTTP_REQUEST_METHOD,
  ATTR_HTTP_RESPONSE_STATUS_CODE,
  ATTR_DB_SYSTEM,
} from "@opentelemetry/semantic-conventions";

const resource = new Resource({ [ATTR_SERVICE_NAME]: "my-service" });
span.setAttribute(ATTR_HTTP_REQUEST_METHOD, "GET");
span.setAttribute(ATTR_HTTP_RESPONSE_STATUS_CODE, 200);
```

## Metric Naming Conventions

| Pattern | Example |
|---------|---------|
| `{domain}.{target}.{measurement}` | `http.server.request.duration` |
| Use dots as separators | `db.client.operation.duration` |
| Use lowercase | `process.cpu.time` |
| Use singular units | `http.server.request.body.size` |
| Include unit in metadata, not name | `unit: "ms"` not `request_duration_ms` |

## Best Practices

1. **Use semantic conventions first** — Check if a convention exists before creating custom attributes
2. **Use the semconv package** — Import constants rather than hardcoding strings
3. **Keep custom attributes namespaced** — Use `mycompany.custom.attribute` to avoid conflicts
4. **Don't duplicate standard attributes** — If auto-instrumentation sets `http.method`, don't set it again
5. **Follow naming patterns** — dot-separated, lowercase, specific-to-general ordering
6. **Check stability** — Some conventions are experimental; pin to specific semconv versions
