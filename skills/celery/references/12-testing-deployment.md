# Testing & Deployment

> Source: [Testing with Celery](https://docs.celeryq.dev/en/stable/userguide/testing.html) · [Daemonization](https://docs.celeryq.dev/en/stable/userguide/daemonization.html)

## Table of Contents

- [Testing Philosophy](#testing-philosophy)
- [pytest Plugin](#pytest-plugin)
- [Eager Mode](#eager-mode)
- [Mocking Tasks](#mocking-tasks)
- [Testing Workflows](#testing-workflows)
- [Deployment Patterns](#deployment-patterns)
- [Systemd Configuration](#systemd-configuration)
- [Supervisor Configuration](#supervisor-configuration)
- [Docker Deployment](#docker-deployment)
- [Production Checklist](#production-checklist)

## Testing Philosophy

Celery tasks should separate concerns: the task handles serialization, message headers, and retries, while business logic lives in standalone functions.

```python
# tasks.py — thin wrapper
@app.task
def create_order(order_data):
    return _create_order(order_data)

# logic.py — testable without Celery
def _create_order(order_data):
    order = Order(**order_data)
    order.save()
    return order.id
```

Test the logic function directly. Test the Celery integration separately.

## pytest Plugin

### Installation

```bash
pip install "celery[pytest]"
```

### Enable the Plugin

```python
# conftest.py
pytest_plugins = ("celery.contrib.pytest",)
```

Or via environment: `PYTEST_PLUGINS=celery.contrib.pytest`

### Key Fixtures

```python
import pytest

@pytest.fixture(scope="session")
def celery_config():
    return {
        "broker_url": "memory://",
        "result_backend": "cache+memory://",
    }

@pytest.fixture(scope="session")
def celery_includes():
    return ["myapp.tasks"]

@pytest.fixture(scope="session")
def celery_worker_parameters():
    return {"perform_ping_check": False}
```

### Testing with Embedded Worker

```python
def test_add(celery_app, celery_worker):
    result = add.delay(4, 4)
    assert result.get(timeout=10) == 8
```

The `celery_worker` fixture starts an embedded worker in a separate thread with a 10-second shutdown timeout.

### Per-Test Configuration Override

```python
@pytest.mark.celery(task_always_eager=True)
def test_in_eager_mode():
    result = add.delay(4, 4)
    assert result.get() == 8

@pytest.mark.celery(result_backend="redis://localhost:6379/1")
class TestWithRedis:
    def test_with_redis_backend(self):
        ...
```

### Session-Scoped Worker (Faster Tests)

```python
@pytest.fixture(scope="session")
def celery_session_worker(celery_session_app, celery_session_worker):
    yield celery_session_worker
```

## Eager Mode

Execute tasks synchronously in the calling process (no broker or worker needed):

```python
app.conf.task_always_eager = True
app.conf.task_eager_propagates = True  # Re-raise exceptions
```

### Limitations

- Does not test serialization — args aren't serialized/deserialized
- Does not test concurrency — runs sequentially
- Does not test broker connectivity
- Does not write results to backend by default (enable with `task_store_eager_result=True`)

Use eager mode only for quick smoke tests, not as a substitute for integration tests.

## Mocking Tasks

### Mock External Dependencies

```python
from unittest.mock import patch

def test_send_order():
    with patch("myapp.tasks.payment_gateway") as mock_gateway:
        mock_gateway.charge.return_value = {"status": "ok"}
        result = process_payment("order-123", 99.99)
        mock_gateway.charge.assert_called_once_with("order-123", 99.99)
```

### Mock Task Delay

```python
def test_view_triggers_task():
    with patch("myapp.views.send_email.delay") as mock_delay:
        response = client.post("/register/", data={"email": "a@b.com"})
        mock_delay.assert_called_once_with("a@b.com")
```

### Test Retry Behavior

```python
from celery.exceptions import Retry

def test_task_retries_on_error():
    with patch("myapp.tasks.api_client.fetch") as mock_fetch:
        mock_fetch.side_effect = ConnectionError("timeout")
        with pytest.raises(Retry):
            fetch_data("http://example.com")
```

## Testing Workflows

### Test Chains

```python
def test_chain(celery_worker):
    from celery import chain
    result = chain(add.s(2, 2), mul.s(4))()
    assert result.get(timeout=10) == 16
```

### Test Groups

```python
def test_group(celery_worker):
    from celery import group
    result = group(add.s(i, i) for i in range(5))()
    assert result.get(timeout=10) == [0, 2, 4, 6, 8]
```

### Test Custom States

```python
def test_progress_tracking(celery_worker):
    result = upload_files.delay(["a.jpg", "b.jpg"])
    
    import time
    while not result.ready():
        if result.state == "PROGRESS":
            assert "current" in result.info
            assert "total" in result.info
        time.sleep(0.5)
    
    assert result.successful()
```

## Deployment Patterns

### Development

```bash
# Terminal 1: Worker
celery -A proj worker --loglevel=INFO

# Terminal 2: Beat (if using periodic tasks)
celery -A proj beat --loglevel=INFO

# Terminal 3: Flower (optional monitoring)
celery -A proj flower
```

### Production Layout

```
├── Worker(s)     — celery -A proj worker
├── Beat          — celery -A proj beat (single instance)
├── Flower        — celery -A proj flower (optional)
├── Broker        — Redis or RabbitMQ
└── Result Backend — Redis or PostgreSQL
```

## Systemd Configuration

### Worker Service

```ini
# /etc/systemd/system/celery.service
[Unit]
Description=Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=celery
Group=celery
WorkingDirectory=/opt/myapp
Environment="DJANGO_SETTINGS_MODULE=myproject.settings"
ExecStart=/opt/myapp/venv/bin/celery multi start worker1 \
    -A proj \
    --loglevel=INFO \
    --pidfile=/var/run/celery/%n.pid \
    --logfile=/var/log/celery/%n%I.log \
    --concurrency=4
ExecStop=/opt/myapp/venv/bin/celery multi stopwait worker1 \
    --pidfile=/var/run/celery/%n.pid
ExecReload=/opt/myapp/venv/bin/celery multi restart worker1 \
    -A proj \
    --pidfile=/var/run/celery/%n.pid \
    --logfile=/var/log/celery/%n%I.log
Restart=always

[Install]
WantedBy=multi-user.target
```

### Beat Service

```ini
# /etc/systemd/system/celerybeat.service
[Unit]
Description=Celery Beat Scheduler
After=network.target redis.service

[Service]
Type=simple
User=celery
Group=celery
WorkingDirectory=/opt/myapp
Environment="DJANGO_SETTINGS_MODULE=myproject.settings"
ExecStart=/opt/myapp/venv/bin/celery -A proj beat \
    --loglevel=INFO \
    --schedule=/var/run/celery/celerybeat-schedule \
    --pidfile=/var/run/celery/celerybeat.pid
Restart=always

[Install]
WantedBy=multi-user.target
```

## Supervisor Configuration

```ini
# /etc/supervisor/conf.d/celery.conf
[program:celery-worker]
command=/opt/myapp/venv/bin/celery -A proj worker --loglevel=INFO -c 4
directory=/opt/myapp
user=celery
autostart=true
autorestart=true
stdout_logfile=/var/log/celery/worker.log
stderr_logfile=/var/log/celery/worker_err.log
stopwaitsecs=600

[program:celery-beat]
command=/opt/myapp/venv/bin/celery -A proj beat --loglevel=INFO
directory=/opt/myapp
user=celery
autostart=true
autorestart=true
stdout_logfile=/var/log/celery/beat.log
stderr_logfile=/var/log/celery/beat_err.log
```

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Worker
CMD ["celery", "-A", "proj", "worker", "--loglevel=INFO", "-c", "4"]
```

### docker-compose.yml

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  worker:
    build: .
    command: celery -A proj worker --loglevel=INFO -c 4
    depends_on:
      - redis
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1

  beat:
    build: .
    command: celery -A proj beat --loglevel=INFO
    depends_on:
      - redis
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0

  flower:
    build: .
    command: celery -A proj flower --port=5555
    ports:
      - "5555:5555"
    depends_on:
      - redis
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
```

## Production Checklist

### Broker

- [ ] Use Redis or RabbitMQ (not SQLite)
- [ ] Enable persistence (Redis AOF or RabbitMQ disk)
- [ ] Configure connection pooling (`broker_pool_limit`)
- [ ] Set up broker monitoring and alerting
- [ ] Enable SSL/TLS for remote brokers

### Workers

- [ ] Set `worker_max_tasks_per_child` to prevent memory leaks
- [ ] Set `worker_max_memory_per_child` as a safety net
- [ ] Configure `time_limit` and `soft_time_limit`
- [ ] Use `--statedb` for persistent revoke state
- [ ] Set `worker_prefetch_multiplier=1` for long-running tasks
- [ ] Enable `worker_send_task_events` for monitoring

### Tasks

- [ ] Design tasks for idempotency
- [ ] Use `acks_late=True` for critical tasks
- [ ] Set appropriate `max_retries` and backoff
- [ ] Use `ignore_result=True` for fire-and-forget
- [ ] Pass IDs not objects as arguments
- [ ] Set `task_reject_on_worker_lost=True` for critical tasks

### Security

- [ ] Use JSON serializer (not pickle) unless in a trusted environment
- [ ] Restrict `accept_content` to expected formats
- [ ] Don't expose broker/backend to the public internet
- [ ] Use separate Redis databases for broker and backend

### Monitoring

- [ ] Deploy Flower or custom monitoring
- [ ] Set up alerting for failed tasks
- [ ] Monitor queue lengths
- [ ] Track task duration trends
- [ ] Log task arguments (redact sensitive data)

### Beat

- [ ] Run only ONE Beat instance
- [ ] Use `--scheduler django_celery_beat.schedulers:DatabaseScheduler` for dynamic schedules
- [ ] Set `expires` on periodic tasks to prevent queue buildup
