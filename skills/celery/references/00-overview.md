# Celery — Overview

> Source: [Celery 5.6.3 documentation](https://docs.celeryq.dev/) · Python 3.9–3.13 · BSD License

## What is Celery?

Celery is a distributed task queue for Python that processes vast amounts of messages while providing real-time processing and task scheduling. It uses a broker (RabbitMQ, Redis, SQS) to mediate between clients and workers. A single process can handle millions of tasks per minute with sub-millisecond round-trip latency.

## When to Use Celery

- **Background processing** — offload slow operations (email, PDF generation, API calls) from web requests
- **Scheduled/periodic tasks** — cron-like scheduling via Celery Beat
- **Distributed computation** — fan out CPU-intensive work across multiple workers
- **Task pipelines** — chain, group, and chord primitives for complex workflows
- **Rate-limited operations** — control throughput to external APIs
- **Retry-resilient work** — automatic retry with exponential backoff

## Architecture

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  Client  │────▶│  Broker  │────▶│  Worker  │
│ (Django, │     │ (Redis / │     │ (Prefork │
│  FastAPI)│     │ RabbitMQ)│     │  / Gevent)│
└──────────┘     └──────────┘     └──────────┘
                      │                 │
                      │           ┌─────▼─────┐
                      │           │  Result    │
                      └──────────▶│  Backend   │
                                  │ (Redis/DB) │
                                  └────────────┘
```

**Client** — sends task messages (your application code)
**Broker** — message transport (RabbitMQ, Redis, Amazon SQS, Google Pub/Sub)
**Worker** — consumes messages and executes task functions
**Result Backend** — stores task return values and state (Redis, SQLAlchemy, Django ORM, etc.)

## Installation

```bash
# Core
pip install celery

# With Redis broker and backend
pip install "celery[redis]"

# With RabbitMQ (C extension for performance)
pip install "celery[librabbitmq]"

# Multiple extras
pip install "celery[redis,msgpack,gevent]"
```

### Available Extras

| Extra | Purpose |
|-------|---------|
| `redis` | Redis transport and result backend |
| `librabbitmq` | High-performance RabbitMQ C client |
| `msgpack` | MessagePack serialization |
| `eventlet` | Eventlet concurrency pool |
| `gevent` | Gevent concurrency pool |
| `auth` | Cryptographic message signing |
| `yaml` | YAML serializer |
| `sqlalchemy` | SQLAlchemy result backend |
| `pymemcache` | Memcached result backend |
| `dynamodb` | AWS DynamoDB result backend |
| `elasticsearch` | Elasticsearch result backend |
| `gcs` | Google Cloud Storage result backend |
| `cassandra` | Apache Cassandra result backend |

## Quick Start

### 1. Create a Celery Application

```python
# tasks.py
from celery import Celery

app = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)

@app.task
def add(x, y):
    return x + y
```

### 2. Start a Worker

```bash
celery -A tasks worker --loglevel=INFO
```

### 3. Call a Task

```python
# In another Python process or shell
from tasks import add

result = add.delay(4, 4)
print(result.get(timeout=10))  # 8
```

## Broker Comparison

| Feature | RabbitMQ | Redis | Amazon SQS |
|---------|----------|-------|------------|
| Protocol | AMQP | Custom | HTTPS |
| Persistence | Disk + RAM | Optional AOF/RDB | Managed |
| Priority queues | Native | Approximate | FIFO support |
| Monitoring | Management UI | redis-cli | CloudWatch |
| Clustering | Built-in | Sentinel/Cluster | Managed |
| Best for | Production, complex routing | Simple setup, also result backend | AWS-native deployments |

## Result Backend Comparison

| Backend | Speed | Persistence | Best For |
|---------|-------|-------------|----------|
| Redis | Fast | Optional | Most use cases |
| SQLAlchemy | Moderate | Yes | When you already have a DB |
| Django ORM | Moderate | Yes | Django projects |
| Memcached | Fast | No | Ephemeral results |
| RPC (AMQP) | Fast | No | Direct result replies |

## Concurrency Models

| Pool | Mechanism | Best For |
|------|-----------|----------|
| `prefork` | Multiprocessing (default) | CPU-bound tasks |
| `eventlet` | Green threads | High I/O concurrency |
| `gevent` | Coroutines | High I/O concurrency |
| `threads` | OS threads | Moderate I/O tasks |
| `solo` | Single thread | Debugging, simple setups |

## Serialization Formats

| Format | Cross-language | Python Objects | Speed |
|--------|---------------|----------------|-------|
| JSON | Yes (default) | Limited types | Fast |
| pickle | Python only | All types | Fastest |
| msgpack | Yes | Limited types | Very fast |
| YAML | Yes | More types | Slow |

## Version Compatibility

| Celery | Python |
|--------|--------|
| 5.6.x | 3.9–3.13, PyPy 3.9+ |
| 5.5.x | 3.8–3.13 |
| 5.4.x | 3.8–3.12 |
| 5.2.x | 3.7–3.10 |
| 4.x | 2.7, 3.4–3.7 |

## Key Concepts

- **Task** — a Python function decorated with `@app.task` that can be sent to workers
- **Signature** — a serializable representation of a task call with arguments
- **Canvas** — primitives (chain, group, chord) for composing task workflows
- **Beat** — a scheduler that kicks off periodic tasks at configured intervals
- **Worker** — a process that consumes task messages and executes them
- **Broker** — the message transport (RabbitMQ, Redis, SQS)
- **Result backend** — stores task return values and metadata
- **ETA** — estimated time of arrival; delays task execution until a future time
