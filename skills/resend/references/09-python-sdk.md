# Python SDK

> Source: https://github.com/resend/resend-python | PyPI: https://pypi.org/project/resend/

## Table of Contents
- [Installation](#installation)
- [Initialization](#initialization)
- [Sending Emails](#sending-emails)
- [Async Support](#async-support)
- [Batch Emails](#batch-emails)
- [Domain Management](#domain-management)
- [Audiences & Contacts](#audiences--contacts)
- [Broadcasts](#broadcasts)
- [API Keys](#api-keys)
- [Error Handling](#error-handling)
- [Framework Integration](#framework-integration)
- [Common Pitfalls](#common-pitfalls)

## Installation

```bash
pip install resend
```

Requires Python 3.7+. Uses `httpx` under the hood for both sync and async operations.

## Initialization

```python
import resend

resend.api_key = "re_xxxxx"

# Or from environment variable
import os
resend.api_key = os.environ["RESEND_API_KEY"]
```

## Sending Emails

### Basic Send

```python
params: resend.Emails.SendParams = {
    "from": "App <noreply@yourdomain.com>",
    "to": ["user@example.com"],
    "subject": "Hello",
    "html": "<p>Hello world</p>",
}

email = resend.Emails.send(params)
print(email["id"])  # ae2014de-c168-4c61-8267-70d2662a1ce1
```

### With All Options

```python
params: resend.Emails.SendParams = {
    "from": "App <noreply@yourdomain.com>",
    "to": ["user@example.com"],
    "cc": ["cc@example.com"],
    "bcc": ["bcc@example.com"],
    "reply_to": "support@yourdomain.com",
    "subject": "Full Example",
    "html": "<p>Content</p>",
    "text": "Content (plain text)",
    "tags": [
        {"name": "type", "value": "transactional"},
        {"name": "user_id", "value": "usr_123"},
    ],
    "headers": {"X-Custom-Header": "value"},
    "scheduled_at": "in 1 hour",
}

email = resend.Emails.send(params)
```

### With Attachments

```python
import base64
from pathlib import Path

# From file path
pdf_content = Path("invoice.pdf").read_bytes()

params: resend.Emails.SendParams = {
    "from": "App <noreply@yourdomain.com>",
    "to": ["user@example.com"],
    "subject": "Your Invoice",
    "html": "<p>Invoice attached.</p>",
    "attachments": [
        {
            "filename": "invoice.pdf",
            "content": list(pdf_content),  # bytes as list of ints
        }
    ],
}

email = resend.Emails.send(params)
```

### With Idempotency Key

```python
email = resend.Emails.send(
    params,
    idempotency_key="order-confirm/order_1234",
)
```

### Get Email Status

```python
email = resend.Emails.get("ae2014de-c168-4c61-8267-70d2662a1ce1")
print(email["last_event"])  # 'delivered', 'bounced', etc.
```

## Async Support

All methods have async counterparts using `httpx.AsyncClient`:

```python
import asyncio
import resend

resend.api_key = "re_xxxxx"

async def send_email():
    params: resend.Emails.SendParams = {
        "from": "App <noreply@yourdomain.com>",
        "to": ["user@example.com"],
        "subject": "Async Hello",
        "html": "<p>Sent asynchronously!</p>",
    }
    email = await resend.Emails.send_async(params)
    return email["id"]

asyncio.run(send_email())
```

### Async in FastAPI

```python
from fastapi import FastAPI
import resend

app = FastAPI()
resend.api_key = os.environ["RESEND_API_KEY"]

@app.post("/api/send-welcome")
async def send_welcome(email: str, name: str):
    result = await resend.Emails.send_async({
        "from": "App <welcome@yourdomain.com>",
        "to": [email],
        "subject": f"Welcome, {name}!",
        "html": f"<h1>Hi {name}</h1><p>Welcome aboard!</p>",
    })
    return {"email_id": result["id"]}
```

## Batch Emails

```python
params = [
    {
        "from": "App <noreply@yourdomain.com>",
        "to": ["alice@example.com"],
        "subject": "Hello Alice",
        "html": "<p>Hi Alice</p>",
    },
    {
        "from": "App <noreply@yourdomain.com>",
        "to": ["bob@example.com"],
        "subject": "Hello Bob",
        "html": "<p>Hi Bob</p>",
    },
]

emails = resend.Batch.send(params)
# [{"id": "..."}, {"id": "..."}]

# Async batch
emails = await resend.Batch.send_async(params)
```

## Domain Management

```python
# Create
domain = resend.Domains.create({"name": "yourdomain.com"})

# List
domains = resend.Domains.list()

# Get (includes DNS records)
domain = resend.Domains.get("domain_id")

# Verify
resend.Domains.verify("domain_id")

# Delete
resend.Domains.remove("domain_id")
```

## Audiences & Contacts

### Audiences

```python
audience = resend.Audiences.create({"name": "Newsletter"})
audiences = resend.Audiences.list()
audience = resend.Audiences.get("audience_id")
resend.Audiences.remove("audience_id")
```

### Contacts

```python
# Create
contact = resend.Contacts.create({
    "audience_id": "aud_xxxxx",
    "email": "alice@example.com",
    "first_name": "Alice",
    "last_name": "Smith",
    "unsubscribed": False,
})

# List
contacts = resend.Contacts.list({"audience_id": "aud_xxxxx"})

# Get
contact = resend.Contacts.get({
    "audience_id": "aud_xxxxx",
    "id": "contact_id",
})

# Update
resend.Contacts.update({
    "audience_id": "aud_xxxxx",
    "id": "contact_id",
    "first_name": "Alicia",
})

# Remove by ID
resend.Contacts.remove({
    "audience_id": "aud_xxxxx",
    "id": "contact_id",
})

# Remove by email
resend.Contacts.remove({
    "audience_id": "aud_xxxxx",
    "email": "alice@example.com",
})

# Segment operations
resend.Contacts.Segments.add({
    "contact_id": "contact_id",
    "segment_id": "seg_xxxxx",
})
resend.Contacts.Segments.remove({
    "contact_id": "contact_id",
    "segment_id": "seg_xxxxx",
})
```

### Contact Properties

```python
resend.ContactProperties.create({
    "key": "company_name",
    "type": "string",
    "fallback_value": "your company",
})

props = resend.ContactProperties.list()
prop = resend.ContactProperties.get("prop_id")
resend.ContactProperties.update({"id": "prop_id", "fallback_value": "N/A"})
resend.ContactProperties.remove("prop_id")
```

## Broadcasts

```python
# Create and send
broadcast = resend.Broadcasts.create({
    "segment_id": "seg_xxxxx",
    "from": "News <news@yourdomain.com>",
    "subject": "Weekly Update",
    "html": "<h1>This Week</h1>",
    "send": True,
})

# Create draft
draft = resend.Broadcasts.create({
    "segment_id": "seg_xxxxx",
    "from": "News <news@yourdomain.com>",
    "subject": "Draft",
    "html": "<p>Draft content</p>",
})

# Send draft
resend.Broadcasts.send({"broadcast_id": draft["id"]})

# List / Get / Update / Delete
broadcasts = resend.Broadcasts.list()
broadcast = resend.Broadcasts.get("broadcast_id")
resend.Broadcasts.update({"id": "broadcast_id", "html": "<p>Updated</p>"})
resend.Broadcasts.remove("broadcast_id")
```

## API Keys

```python
key = resend.ApiKeys.create({
    "name": "Production Key",
    "permission": "full_access",  # or "sending_access"
})

keys = resend.ApiKeys.list()
resend.ApiKeys.remove("api_key_id")
```

## Error Handling

```python
try:
    email = resend.Emails.send(params)
except resend.exceptions.ValidationError as e:
    print(f"Validation error: {e.message}")
except resend.exceptions.ResendError as e:
    print(f"Resend error ({e.status_code}): {e.message}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

**Exception types:**
- `resend.exceptions.ValidationError` — 422 invalid params
- `resend.exceptions.ResendError` — base class for all Resend errors
- `resend.exceptions.RateLimitError` — 429 too many requests

## Framework Integration

### Django

```python
# settings.py
RESEND_API_KEY = os.environ["RESEND_API_KEY"]

# views.py
import resend
from django.conf import settings

resend.api_key = settings.RESEND_API_KEY

def send_notification(request):
    resend.Emails.send({
        "from": "App <noreply@yourdomain.com>",
        "to": [request.user.email],
        "subject": "Notification",
        "html": "<p>You have a new notification.</p>",
    })
```

### Flask

```python
from flask import Flask
import resend

app = Flask(__name__)
resend.api_key = os.environ["RESEND_API_KEY"]

@app.post("/send")
def send_email():
    email = resend.Emails.send({
        "from": "App <noreply@yourdomain.com>",
        "to": ["user@example.com"],
        "subject": "Hello from Flask",
        "html": "<p>Hello!</p>",
    })
    return {"id": email["id"]}
```

## Common Pitfalls

1. **Forgetting `resend.api_key`** — must be set before any API call. Use environment variables.
2. **Sync in async context** — use `send_async()` in FastAPI/async code to avoid blocking the event loop.
3. **Attachment format** — Python SDK expects `content` as a list of ints (byte values), not raw bytes.
4. **No `react` parameter** — Python SDK doesn't support React components. Use `html` only.
5. **Mutable default** — don't use mutable defaults for `tags` or `attachments` in function signatures.
6. **Not catching exceptions** — unlike Node SDK, Python SDK raises exceptions. Always wrap in try/except.
