# Inngest — Python SDK

> Source: [inngest.com/docs/getting-started/python-quick-start](https://www.inngest.com/docs/getting-started/python-quick-start)

## Table of Contents

- [Installation](#installation)
- [Client Setup](#client-setup)
- [Creating Functions](#creating-functions)
- [Framework Integration](#framework-integration)
- [Step Primitives](#step-primitives)
- [Parallel Execution](#parallel-execution)
- [Error Handling](#error-handling)
- [Sending Events](#sending-events)
- [Type Hints](#type-hints)
- [Testing](#testing)
- [Common Patterns](#common-patterns)

---

## Installation

```bash
# Requires Python 3.10+
pip install inngest

# With your web framework
pip install inngest fastapi uvicorn   # FastAPI
pip install inngest flask             # Flask
pip install inngest django            # Django
```

## Client Setup

```python
import logging
import inngest

inngest_client = inngest.Inngest(
    app_id="my-python-app",
    logger=logging.getLogger("uvicorn"),
    # Event key and signing key are read from env vars by default:
    # INNGEST_EVENT_KEY, INNGEST_SIGNING_KEY
)
```

### Client options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `app_id` | `str` | required | Unique application identifier |
| `logger` | `Logger` | None | Python logger instance |
| `event_key` | `str` | env var | API key for sending events |
| `signing_key` | `str` | env var | Key for verifying requests |
| `is_production` | `bool` | auto | Force production mode |

## Creating Functions

### Basic function

```python
@inngest_client.create_function(
    fn_id="send-welcome-email",
    trigger=inngest.TriggerEvent(event="user/signup.completed"),
)
async def send_welcome_email(ctx: inngest.Context) -> str:
    user_id = ctx.event.data["userId"]

    user = await ctx.step.run("get-user", lambda: get_user(user_id))

    await ctx.step.run(
        "send-email",
        lambda: send_email(user["email"], "Welcome!"),
    )

    return "done"
```

### Function with retries

```python
@inngest_client.create_function(
    fn_id="process-payment",
    trigger=inngest.TriggerEvent(event="payment/created"),
    retries=10,
)
async def process_payment(ctx: inngest.Context) -> dict:
    payment_id = ctx.event.data["paymentId"]
    result = await ctx.step.run(
        "charge",
        lambda: stripe.PaymentIntent.capture(payment_id),
    )
    return {"status": "captured", "id": result["id"]}
```

### Cron function

```python
@inngest_client.create_function(
    fn_id="daily-cleanup",
    trigger=inngest.TriggerCron(cron="0 2 * * *"),
)
async def daily_cleanup(ctx: inngest.Context) -> str:
    deleted = await ctx.step.run("cleanup", cleanup_expired_sessions)
    ctx.logger.info(f"Cleaned up {deleted} sessions")
    return f"Deleted {deleted} sessions"
```

### Function with concurrency

```python
@inngest_client.create_function(
    fn_id="ai-generate",
    trigger=inngest.TriggerEvent(event="ai/generate"),
    concurrency=[
        inngest.Concurrency(limit=10, scope="fn"),
    ],
)
async def ai_generate(ctx: inngest.Context) -> dict:
    result = await ctx.step.run(
        "generate",
        lambda: openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": ctx.event.data["prompt"]}],
        ),
    )
    return {"response": result.choices[0].message.content}
```

## Framework Integration

### FastAPI

```python
import inngest.fast_api
from fastapi import FastAPI

app = FastAPI()

# Register all Inngest functions with FastAPI
inngest.fast_api.serve(
    app,
    inngest_client,
    [send_welcome_email, process_payment, daily_cleanup],
)

# Start: INNGEST_DEV=1 uvicorn main:app --reload
```

### Flask

```python
import inngest.flask
from flask import Flask

app = Flask(__name__)

inngest.flask.serve(
    app,
    inngest_client,
    [send_welcome_email, process_payment],
)

# Start: INNGEST_DEV=1 flask run
```

### Django

```python
# urls.py
import inngest.django
from django.urls import path

urlpatterns = [
    path(
        "api/inngest",
        inngest.django.serve(
            inngest_client,
            [send_welcome_email, process_payment],
        ),
    ),
]
```

## Step Primitives

### step.run

```python
result = await ctx.step.run("step-name", handler_function)

# With lambda
user = await ctx.step.run("get-user", lambda: db.get_user(user_id))

# With async function
async def fetch_data():
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://api.example.com/data")
        return resp.json()

data = await ctx.step.run("fetch-data", fetch_data)
```

### step.sleep

```python
await ctx.step.sleep("wait-1h", datetime.timedelta(hours=1))

# String duration format
await ctx.step.sleep("wait-5m", "5m")
await ctx.step.sleep("wait-1d", "1d")
```

### step.sleep_until

```python
from datetime import datetime

await ctx.step.sleep_until(
    "wait-for-deadline",
    datetime.fromisoformat(ctx.event.data["deadline"]),
)
```

### step.wait_for_event

```python
result = await ctx.step.wait_for_event(
    "wait-verification",
    event="user/email.verified",
    timeout="24h",
    if_exp=f'event.data.userId == "{ctx.event.data["userId"]}"',
)

if result is None:
    # Timeout — no matching event received
    await ctx.step.run("send-reminder", lambda: send_reminder(user_id))
else:
    # Event received
    await ctx.step.run("activate", lambda: activate_user(user_id))
```

### step.invoke

```python
result = await ctx.step.invoke(
    "generate-report",
    function=generate_report_fn,
    data={"reportId": ctx.event.data["reportId"]},
    timeout="5m",
)
```

### step.send_event

```python
await ctx.step.send_event(
    "notify-downstream",
    [
        inngest.Event(
            name="processing/complete",
            data={"resultId": result["id"]},
        ),
    ],
)
```

## Parallel Execution

```python
@inngest_client.create_function(
    fn_id="process-dashboard",
    trigger=inngest.TriggerEvent(event="dashboard/refresh"),
)
async def process_dashboard(ctx: inngest.Context) -> dict:
    # Run steps in parallel
    results = await ctx.group.parallel(
        lambda: ctx.step.run("fetch-analytics", fetch_analytics),
        lambda: ctx.step.run("fetch-notifications", fetch_notifications),
        lambda: ctx.step.run("fetch-preferences", fetch_preferences),
    )

    analytics, notifications, preferences = results
    return {
        "analytics": analytics,
        "notifications": notifications,
        "preferences": preferences,
    }
```

### Dynamic parallel

```python
async def process_batch(ctx: inngest.Context) -> dict:
    items = ctx.event.data["items"]

    results = await ctx.group.parallel(
        *[
            lambda item=item: ctx.step.run(
                f"process-{item['id']}",
                lambda i=item: process_item(i),
            )
            for item in items
        ]
    )

    return {"processed": len(results)}
```

## Error Handling

### NonRetriableError

```python
@inngest_client.create_function(
    fn_id="validate-data",
    trigger=inngest.TriggerEvent(event="data/validate"),
)
async def validate_data(ctx: inngest.Context) -> str:
    data = ctx.event.data

    if "email" not in data:
        raise inngest.NonRetriableError("Missing email field")

    if not is_valid_email(data["email"]):
        raise inngest.NonRetriableError(f"Invalid email: {data['email']}")

    return "valid"
```

### Try/catch with steps

```python
async def resilient_function(ctx: inngest.Context) -> dict:
    try:
        result = await ctx.step.run("primary-api", call_primary_api)
    except Exception:
        result = await ctx.step.run("fallback-api", call_fallback_api)

    return {"result": result}
```

## Sending Events

```python
# Send from anywhere in your app
await inngest_client.send(
    inngest.Event(
        name="user/signup.completed",
        data={"userId": "usr_123", "email": "user@example.com"},
    )
)

# Send multiple events
await inngest_client.send(
    [
        inngest.Event(name="order/item.shipped", data={"itemId": "a"}),
        inngest.Event(name="order/item.shipped", data={"itemId": "b"}),
    ]
)
```

## Type Hints

```python
from typing import TypedDict

class UserCreatedData(TypedDict):
    userId: str
    email: str
    plan: str

@inngest_client.create_function(
    fn_id="handle-signup",
    trigger=inngest.TriggerEvent(event="user/created"),
)
async def handle_signup(ctx: inngest.Context) -> dict:
    data: UserCreatedData = ctx.event.data  # type: ignore[assignment]
    user_id = data["userId"]
    # ...
    return {"processed": True}
```

## Testing

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_send_welcome_email():
    """Test the welcome email function with a mock context."""
    mock_ctx = AsyncMock(spec=inngest.Context)
    mock_ctx.event = inngest.Event(
        name="user/signup.completed",
        data={"userId": "usr_test", "email": "test@example.com"},
    )
    mock_ctx.step.run = AsyncMock(side_effect=[
        {"id": "usr_test", "email": "test@example.com"},  # get-user
        {"messageId": "msg_123"},                            # send-email
    ])

    result = await send_welcome_email(mock_ctx)
    assert result == "done"
    assert mock_ctx.step.run.call_count == 2
```

## Common Patterns

### Data pipeline

```python
@inngest_client.create_function(
    fn_id="etl-pipeline",
    trigger=inngest.TriggerEvent(event="pipeline/run"),
    retries=3,
)
async def etl_pipeline(ctx: inngest.Context) -> dict:
    # Extract
    raw_data = await ctx.step.run("extract", lambda: extract_from_source(
        ctx.event.data["source"]
    ))

    # Transform
    transformed = await ctx.step.run("transform", lambda: transform_data(raw_data))

    # Load
    result = await ctx.step.run("load", lambda: load_to_warehouse(transformed))

    return {"rows_loaded": result["count"]}
```

### Scheduled report

```python
@inngest_client.create_function(
    fn_id="weekly-report",
    trigger=inngest.TriggerCron(cron="0 9 * * 1"),  # Mondays 9 AM
)
async def weekly_report(ctx: inngest.Context) -> str:
    metrics = await ctx.step.run("gather-metrics", gather_weekly_metrics)
    report = await ctx.step.run("generate-report", lambda: build_report(metrics))
    await ctx.step.run("send-report", lambda: email_report(report))
    return "sent"
```
