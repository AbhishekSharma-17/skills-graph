# Instructor — Hooks System

> Source: https://python.useinstructor.com/concepts/hooks | v1.15.4

## Overview

Instructor's hooks system provides event callbacks for intercepting API interactions. Use hooks for logging, monitoring, error classification, testing, and debugging without modifying extraction logic.

## Event Types

| Event | Fires When | Callback Signature |
|-------|-----------|-------------------|
| `completion:kwargs` | Before sending to LLM | `handler(*args, **kwargs)` |
| `completion:response` | After receiving response | `handler(response)` |
| `completion:error` | On error during retry | `handler(error, *, attempt_number, max_attempts, is_last_attempt)` |
| `parse:error` | Pydantic validation fails | `handler(error)` |
| `completion:last_attempt` | Final retry exhausted | `handler(error)` |

## Registering Hooks

### Basic Registration

```python
import instructor

client = instructor.from_provider("openai/gpt-4o-mini")

def log_kwargs(*args, **kwargs):
    print(f"Sending request with model: {kwargs.get('model')}")
    print(f"Messages: {len(kwargs.get('messages', []))}")

def log_response(response):
    print(f"Received response: {response.id}")
    if hasattr(response, "usage"):
        print(f"Tokens: {response.usage.total_tokens}")

client.on("completion:kwargs", log_kwargs)
client.on("completion:response", log_response)
```

### Enum-Based Registration

```python
from instructor import HookName

client.on(HookName.COMPLETION_KWARGS, log_kwargs)
client.on(HookName.COMPLETION_RESPONSE, log_response)
client.on(HookName.COMPLETION_ERROR, log_error)
client.on(HookName.PARSE_ERROR, log_parse_error)
```

## Removing Hooks

```python
# Remove specific handler
client.off("completion:kwargs", log_kwargs)

# Clear all handlers for an event
client.clear("completion:kwargs")

# Clear all hooks entirely
client.clear()
```

## Error Handling Hooks

### Retry Error Hook

```python
def on_error(error, *, attempt_number, max_attempts, is_last_attempt):
    print(f"Attempt {attempt_number}/{max_attempts}")
    print(f"Error: {error}")
    if is_last_attempt:
        print("Final attempt failed — will raise exception")

client.on("completion:error", on_error)
```

### Parse Error Hook

```python
from pydantic import ValidationError

def on_parse_error(error):
    if isinstance(error, ValidationError):
        for err in error.errors():
            print(f"Validation failed: {err['loc']} — {err['msg']}")
    else:
        print(f"Parse error: {error}")

client.on("parse:error", on_parse_error)
```

### Last Attempt Hook

```python
def on_last_attempt(error):
    # Log to monitoring system, send alert, etc.
    print(f"All retries exhausted: {error}")

client.on("completion:last_attempt", on_last_attempt)
```

## Error Classification

Classify errors by type for targeted handling:

```python
from instructor.exceptions import InstructorRetryException
from pydantic import ValidationError

def classify_error(error, *, attempt_number, max_attempts, is_last_attempt):
    if isinstance(error, ValidationError):
        print(f"[VALIDATION] Attempt {attempt_number}: Schema mismatch")
    elif "rate_limit" in str(error).lower():
        print(f"[RATE_LIMIT] Attempt {attempt_number}: Backing off")
    elif "timeout" in str(error).lower():
        print(f"[TIMEOUT] Attempt {attempt_number}: Slow response")
    else:
        print(f"[UNKNOWN] Attempt {attempt_number}: {type(error).__name__}")

client.on("completion:error", classify_error)
```

## Hook Composition

Combine multiple hook sets with the `+` operator:

```python
def logging_hooks(client):
    client.on("completion:kwargs", log_kwargs)
    client.on("completion:response", log_response)

def monitoring_hooks(client):
    client.on("completion:error", on_error)
    client.on("completion:last_attempt", on_last_attempt)

# Apply both
logging_hooks(client)
monitoring_hooks(client)
```

## Use Cases

### Token Tracking

```python
total_tokens = {"prompt": 0, "completion": 0}

def track_tokens(response):
    if hasattr(response, "usage") and response.usage:
        total_tokens["prompt"] += response.usage.prompt_tokens
        total_tokens["completion"] += response.usage.completion_tokens

client.on("completion:response", track_tokens)

# After multiple calls:
print(f"Total prompt tokens: {total_tokens['prompt']}")
print(f"Total completion tokens: {total_tokens['completion']}")
```

### Request Logging for Debugging

```python
import json

def debug_request(*args, **kwargs):
    messages = kwargs.get("messages", [])
    tools = kwargs.get("tools", [])
    print(f"--- Request ---")
    print(f"Model: {kwargs.get('model')}")
    print(f"Messages: {json.dumps(messages, indent=2)}")
    if tools:
        print(f"Tools: {len(tools)} defined")
    print(f"--- End ---")

client.on("completion:kwargs", debug_request)
```

### Testing with Hooks

```python
import pytest

def test_extraction_makes_api_call():
    calls = []

    def capture_call(*args, **kwargs):
        calls.append(kwargs)

    client = instructor.from_provider("openai/gpt-4o-mini")
    client.on("completion:kwargs", capture_call)

    user = client.create(
        response_model=User,
        messages=[{"role": "user", "content": "Extract: Jason is 25"}],
    )

    assert len(calls) == 1
    assert calls[0]["model"] == "gpt-4o-mini"
```

### Latency Monitoring

```python
import time

request_times = {}

def start_timer(*args, **kwargs):
    request_times["start"] = time.time()

def end_timer(response):
    elapsed = time.time() - request_times.get("start", time.time())
    print(f"Request took {elapsed:.2f}s")

client.on("completion:kwargs", start_timer)
client.on("completion:response", end_timer)
```

## Backward Compatibility

Old-style handlers accepting only `(error)` still work for `completion:error`:

```python
# Old style (still works)
def simple_error_handler(error):
    print(f"Error: {error}")

# New style (recommended)
def detailed_error_handler(error, *, attempt_number, max_attempts, is_last_attempt):
    print(f"Error on attempt {attempt_number}: {error}")
```
