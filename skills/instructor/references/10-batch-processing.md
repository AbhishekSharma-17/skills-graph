# Instructor — Batch Processing

> Source: https://python.useinstructor.com/concepts/batch | v1.15.4

## Overview

Batch processing sends multiple extraction requests in a single operation, offering up to 50% cost savings compared to individual API calls. Instructor supports batch processing across OpenAI, Anthropic, and Google GenAI.

## BatchProcessor Class

The `BatchProcessor` class manages batch lifecycle:

```python
from instructor.batch import BatchProcessor
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int
    role: str

processor = BatchProcessor("openai/gpt-4o-mini", User)
```

### Constructor Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | `str` | Provider/model string |
| `response_model` | `type[BaseModel]` | Expected output schema |

## Creating Batches

### File-Based (Large Jobs)

Write requests to a JSONL file for audit trails and large datasets:

```python
messages_list = [
    [{"role": "user", "content": "Extract: Jason is 25, engineer"}],
    [{"role": "user", "content": "Extract: Sarah is 30, designer"}],
    [{"role": "user", "content": "Extract: Mike is 28, manager"}],
]

processor.create_batch_from_messages(
    file_path="batch_requests.jsonl",
    messages_list=messages_list,
    max_tokens=200,
    temperature=0.1,
)
```

### In-Memory (Serverless)

Skip file I/O for ephemeral workloads:

```python
buffer = processor.create_batch_from_messages(
    messages_list=messages_list,
    file_path=None,  # Returns BytesIO buffer
    max_tokens=150,
)
```

## Batch Workflow

### Submit

```python
batch_id = processor.submit_batch(file_or_buffer)
print(f"Submitted batch: {batch_id}")
```

### Monitor

```python
status = processor.get_batch_status(batch_id)
print(f"Status: {status.status}")
print(f"Completed: {status.completed_count}/{status.total_count}")
```

### Retrieve Results

```python
all_results = processor.retrieve_results(batch_id)
```

## Result Handling

Instructor provides type-safe result filtering:

```python
from instructor.batch import filter_successful, filter_errors, extract_results

# Get only successful extractions
successful = filter_successful(all_results)

# Get only failures
errors = filter_errors(all_results)

# Extract just the Pydantic objects
users: list[User] = extract_results(all_results)

print(f"Succeeded: {len(successful)}")
print(f"Failed: {len(errors)}")

for user in users:
    print(f"{user.name}: {user.age}, {user.role}")
```

## Complete Example

```python
import instructor
from instructor.batch import BatchProcessor, filter_successful, extract_results
from pydantic import BaseModel, Field

class ProductReview(BaseModel):
    product: str
    sentiment: str = Field(description="positive, negative, or neutral")
    key_points: list[str]
    rating: float = Field(ge=1.0, le=5.0)

# Prepare messages
reviews = [
    "The laptop is amazing, fast performance and great display.",
    "Terrible customer service, product broke after 2 days.",
    "It's okay. Nothing special but does the job.",
]

messages_list = [
    [{"role": "user", "content": f"Analyze this review: {review}"}]
    for review in reviews
]

# Create and submit batch
processor = BatchProcessor("openai/gpt-4o-mini", ProductReview)
buffer = processor.create_batch_from_messages(
    messages_list=messages_list,
    file_path=None,
    max_tokens=300,
)
batch_id = processor.submit_batch(buffer)

# Wait and retrieve (batch execution takes time)
import time
while True:
    status = processor.get_batch_status(batch_id)
    if status.status in ("completed", "failed", "expired"):
        break
    time.sleep(30)

# Process results
results = processor.retrieve_results(batch_id)
analyzed = extract_results(filter_successful(results))

for review in analyzed:
    print(f"{review.product}: {review.sentiment} ({review.rating}/5)")
```

## Provider-Specific Notes

### OpenAI

- Maximum batch execution time: 24 hours
- Batch requests go through the same models and rate limits
- 50% cost savings on input and output tokens

### Anthropic

- Batch API available for Claude models
- Check Anthropic docs for current batch limits

### Google GenAI

- Batch execution limit: 24 hours
- Uses the Gemini batch prediction API

## Best Practices

1. **Minimum batch size** — aim for 25,000+ requests per job for optimal efficiency
2. **File vs in-memory** — use file-based for audit requirements; in-memory for ephemeral/serverless
3. **Error handling** — always check `filter_errors()` and handle failures
4. **Idempotency** — batch IDs are unique; track them for recovery
5. **Cost monitoring** — batch processing saves ~50% but monitor total spend
6. **Timeouts** — batch jobs can take hours; implement polling with backoff
7. **Schema complexity** — simpler schemas have higher batch success rates

## When Not to Use Batch

- Real-time extraction where latency matters
- Interactive applications (chatbots, live dashboards)
- Small volumes (< 100 requests) — overhead isn't worth it
- When you need individual retry control per request
