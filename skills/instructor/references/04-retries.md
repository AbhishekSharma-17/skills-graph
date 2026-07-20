# Instructor — Retry Strategies

> Source: https://python.useinstructor.com/concepts/retrying | v1.15.4

## Table of Contents

- [How Retries Work](#how-retries-work)
- [Built-in Retries](#built-in-retries)
- [Tenacity Integration](#tenacity-integration)
- [Backoff Strategies](#backoff-strategies)
- [Error-Specific Retries](#error-specific-retries)
- [Result-Based Retries](#result-based-retries)
- [Logging and Monitoring](#logging-and-monitoring)
- [Failed Attempt Tracking](#failed-attempt-tracking)
- [Recommended Settings](#recommended-settings)

## How Retries Work

When validation fails, Instructor does not simply repeat the same request. It implements a "reask" pattern:

1. LLM returns a response
2. Pydantic validation fails with a specific error message
3. Instructor appends the error to the conversation as assistant + user messages
4. The LLM sees what went wrong and can self-correct
5. Process repeats until validation passes or retries exhaust

This makes retries intelligent — the LLM gets feedback about what was wrong.

```
Request → LLM Response → Validate
                            │
                     Pass? ─┤
                     Yes  → Return Model
                     No   → Append Error → Retry with context
```

## Built-in Retries

Set `max_retries` at client or call level:

```python
import instructor
from pydantic import BaseModel, Field

class User(BaseModel):
    name: str = Field(min_length=2)
    age: int = Field(ge=0, le=150)

# Client-level default
client = instructor.from_provider(
    "openai/gpt-4o-mini",
    max_retries=3,
    retry_delay=1,  # 1 second between retries
)

# Per-call override
user = client.create(
    response_model=User,
    messages=[{"role": "user", "content": "Extract: J, age -5"}],
    max_retries=5,  # Override for this call
)
```

### max_retries Behavior

| Value | Behavior |
|-------|----------|
| `0` | No retries — raise on first validation failure |
| `1` | One retry attempt after failure |
| `2-3` | Recommended for most validation scenarios |
| `5+` | Use only for complex schemas with many constraints |

## Tenacity Integration

For advanced retry logic, use the Tenacity library directly:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
)
def extract_user_info(text: str) -> User:
    return client.create(
        response_model=User,
        messages=[{"role": "user", "content": f"Extract: {text}"}],
    )

user = extract_user_info("Jason is 25 years old")
```

Tenacity decorates the entire function, retrying on any exception. This is useful when you want to:

- Apply custom backoff strategies
- Handle API errors alongside validation errors
- Add logging between attempts

## Backoff Strategies

### Fixed Delay

```python
from tenacity import retry, stop_after_attempt, wait_fixed

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def extract(text: str) -> User:
    return client.create(response_model=User, messages=[...])
```

### Exponential Backoff

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=60),
)
def extract(text: str) -> User:
    return client.create(response_model=User, messages=[...])
```

Delays: 1s → 2s → 4s → 8s → 16s (capped at 60s).

### Random Jitter

```python
from tenacity import retry, stop_after_attempt, wait_random

@retry(
    stop=stop_after_attempt(3),
    wait=wait_random(min=1, max=5),
)
def extract(text: str) -> User:
    return client.create(response_model=User, messages=[...])
```

## Error-Specific Retries

Target specific exception types:

```python
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from openai import RateLimitError, APIError

@retry(
    retry=retry_if_exception_type((RateLimitError, APIError)),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=1, max=60),
)
def extract_with_rate_limit_handling(text: str) -> User:
    return client.create(
        response_model=User,
        messages=[{"role": "user", "content": f"Extract: {text}"}],
    )
```

### Combining Error Types

```python
from pydantic import ValidationError

@retry(
    retry=retry_if_exception_type((RateLimitError, ValidationError)),
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=2, max=30),
)
def robust_extraction(text: str) -> User:
    return client.create(
        response_model=User,
        messages=[{"role": "user", "content": f"Extract: {text}"}],
    )
```

## Result-Based Retries

Retry based on the returned value, not exceptions:

```python
from tenacity import retry, retry_if_result, stop_after_attempt

def should_retry(result: User) -> bool:
    """Retry if the result doesn't meet quality criteria."""
    return result.age < 0 or result.age > 150 or not result.name.strip()

@retry(
    retry=retry_if_result(should_retry),
    stop=stop_after_attempt(3),
)
def extract_valid_user(text: str) -> User:
    return client.create(
        response_model=User,
        messages=[{"role": "user", "content": f"Extract: {text}"}],
    )
```

This is useful for criteria that Pydantic validators don't cover, like semantic quality checks.

## Logging and Monitoring

### With Tenacity Callbacks

```python
from tenacity import before_log, after_log, before_sleep_log
import logging

logger = logging.getLogger(__name__)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARNING),
    before_sleep=before_sleep_log(logger, logging.DEBUG),
)
def logged_extraction(text: str) -> User:
    return client.create(
        response_model=User,
        messages=[{"role": "user", "content": f"Extract: {text}"}],
    )
```

### Custom Callbacks

```python
from tenacity import retry, stop_after_attempt

def log_attempt(retry_state):
    print(f"Attempt {retry_state.attempt_number}")
    if retry_state.outcome.failed:
        print(f"  Error: {retry_state.outcome.exception()}")

@retry(
    stop=stop_after_attempt(3),
    after=log_attempt,
)
def extract(text: str) -> User:
    return client.create(response_model=User, messages=[...])
```

## Failed Attempt Tracking

When all retries exhaust, Instructor raises `InstructorRetryException` with full attempt history:

```python
from instructor.exceptions import InstructorRetryException

try:
    result = client.create(
        response_model=User,
        messages=[{"role": "user", "content": "..."}],
        max_retries=3,
    )
except InstructorRetryException as e:
    print(f"Failed after {e.n_attempts} attempts")
    for attempt in e.failed_attempts:
        print(f"Attempt {attempt.attempt_number}: {attempt.exception}")

    # Access total token usage across all attempts
    print(f"Total tokens: {e.total_usage}")
```

## Recommended Settings

| Scenario | max_retries | Wait Strategy | Timeout |
|----------|-------------|---------------|---------|
| Simple field validation | 2 | 1s fixed | — |
| Complex nested schemas | 3 | 1-10s exponential | 30s |
| Rate-limited API | 5 | 1-60s exponential | 120s |
| Network-flaky environment | 4 | 2-30s exponential | 60s |
| Ollama (local, slow) | 2 | 1s fixed | 30s per attempt |

### Critical Rules

1. **Always set stop conditions** — use `stop_after_attempt()` or `stop_after_delay()` to prevent infinite loops
2. **Match retry to error type** — use exponential backoff for rate limits, fixed delay for validation
3. **Log retries in production** — always know when and why retries happen
4. **Set Ollama timeouts explicitly** — local models can hang; use the `timeout` parameter
5. **Consider total cost** — each retry is another API call with token charges
