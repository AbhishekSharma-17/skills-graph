# Querying Traces & Spans

Database convenience functions for querying traces and spans from your tracing database.

## Trace Functions

### db.get_trace()

Get a single trace by ID or run ID:

```python
# Get by trace_id
trace = db.get_trace(trace_id="abc123...")

# Get by run_id (returns most recent match)
trace = db.get_trace(run_id=response.run_id)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `trace_id` | `Optional[str]` | Unique trace identifier |
| `run_id` | `Optional[str]` | Filter by run ID |

**Returns:** `Trace` or `None`

### db.get_traces()

Get multiple traces with filtering and pagination:

```python
# Get recent traces
traces, total_count = db.get_traces(limit=20)

# Filter by agent
traces, count = db.get_traces(agent_id=agent.id)

# Filter by team
traces, count = db.get_traces(team_id=team.id)

# Filter by workflow
traces, count = db.get_traces(workflow_id=workflow.id)

# Filter by time range
from datetime import datetime, timedelta, timezone

now = datetime.now(timezone.utc)
traces, count = db.get_traces(
    start_time=now - timedelta(hours=1),
    end_time=now,
    limit=100,
)

# Filter by status
traces, count = db.get_traces(status="ERROR")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `run_id` | `Optional[str]` | `None` | Filter by run ID |
| `session_id` | `Optional[str]` | `None` | Filter by session ID |
| `user_id` | `Optional[str]` | `None` | Filter by user ID |
| `agent_id` | `Optional[str]` | `None` | Filter by agent ID |
| `team_id` | `Optional[str]` | `None` | Filter by team ID |
| `workflow_id` | `Optional[str]` | `None` | Filter by workflow ID |
| `status` | `Optional[str]` | `None` | Filter by status: `"OK"`, `"ERROR"`, `"UNSET"` |
| `start_time` | `Optional[datetime]` | `None` | Filter traces after this time |
| `end_time` | `Optional[datetime]` | `None` | Filter traces before this time |
| `limit` | `Optional[int]` | `20` | Max traces to return |
| `page` | `Optional[int]` | `1` | Page number for pagination |

**Returns:** `tuple[List[Trace], int]` — (traces list, total count)

---

## Span Functions

### db.get_span()

Get a single span by ID:

```python
span = db.get_span(span_id="xyz789...")
if span:
    print(f"{span.name}: {span.duration_ms}ms")
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `span_id` | `str` | Unique span identifier |

**Returns:** `Span` or `None`

### db.get_spans()

Get multiple spans, filtered by trace or parent:

```python
# Get all spans in a trace
spans = db.get_spans(trace_id=trace.trace_id)

# Get child spans of a specific parent
children = db.get_spans(parent_span_id=root_span.span_id)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `trace_id` | `Optional[str]` | Filter by trace ID |
| `parent_span_id` | `Optional[str]` | Filter by parent span ID |

**Returns:** `List[Span]`

---

## Trace Object

Each `Trace` object contains:

| Attribute | Description |
|-----------|-------------|
| `trace_id` | Unique trace identifier |
| `name` | Operation name (e.g., `"Agent.run"`) |
| `status` | Status: `"OK"`, `"ERROR"`, `"UNSET"` |
| `duration_ms` | Execution duration in milliseconds |
| `start_time` | Start timestamp |
| `end_time` | End timestamp |

## Span Object

Each `Span` object contains:

| Attribute | Description |
|-----------|-------------|
| `span_id` | Unique span identifier |
| `trace_id` | Parent trace ID |
| `parent_span_id` | Parent span ID (null for root spans) |
| `name` | Operation name (e.g., `"agent.run"`, `"model.response"`, `"get_current_stock_price"`) |
| `duration_ms` | Execution duration in milliseconds |
| `start_time` | Start timestamp |

---

## Example: Analyzing a Run

```python
from agno.db.sqlite import SqliteDb

db = SqliteDb(db_file="tmp/traces.db")

# Get trace for a specific run
trace = db.get_trace(run_id=response.run_id)

if trace:
    print(f"Trace: {trace.name} ({trace.duration_ms}ms)")

    # Get all spans in this trace
    spans = db.get_spans(trace_id=trace.trace_id)

    # Print execution tree
    for span in sorted(spans, key=lambda s: s.start_time):
        indent = "  " if span.parent_span_id else ""
        print(f"{indent}- {span.name} ({span.duration_ms}ms)")
```

Example output:

```
Trace: Stock_Price_Agent.run (2450ms)
- Stock_Price_Agent.run (2450ms)
  - OpenAIChat.invoke (1200ms)
  - get_current_stock_price (300ms)
  - OpenAIChat.invoke (800ms)
```

## Example: Error Analysis

```python
# Find failed traces
error_traces, count = db.get_traces(status="ERROR", limit=50)
print(f"Found {count} failed traces")

for trace in error_traces:
    print(f"\n{trace.name} - {trace.duration_ms}ms")
    spans = db.get_spans(trace_id=trace.trace_id)
    for span in spans:
        if span.status == "ERROR":
            print(f"  FAILED: {span.name}")
```

## Example: Performance Monitoring

```python
from datetime import datetime, timedelta, timezone

now = datetime.now(timezone.utc)

# Get last hour's traces
traces, count = db.get_traces(
    agent_id=agent.id,
    start_time=now - timedelta(hours=1),
    end_time=now,
    limit=100,
)

# Calculate average latency
if traces:
    avg_ms = sum(t.duration_ms for t in traces) / len(traces)
    print(f"Average latency: {avg_ms:.0f}ms over {len(traces)} runs")
```
