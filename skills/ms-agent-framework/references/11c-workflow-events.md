# Workflow Events — Streaming, Monitoring, Event Types

Workflow events provide real-time visibility into execution. Stream events during workflow execution to monitor progress, handle outputs, and implement human-in-the-loop interactions.

## WorkflowEvent Class

Base class for all workflow events:

```python
from agent_framework import WorkflowEvent

class WorkflowEvent:
    type: str  # Event type identifier
    executor_id: str  # Which executor emitted this
    data: Any  # Event payload
    timestamp: datetime  # When event occurred
    superstep: int  # Which superstep (0-indexed)
```

All events provide core execution context information.

## Event Types

### started

Workflow execution started:

```python
{
    "type": "started",
    "executor_id": "workflow",
    "data": {
        "input": "user input data",
        "workflow_id": "main_workflow"
    },
    "superstep": 0
}
```

**When:** Emitted once at workflow start, before entry executor runs.

### executor_invoked

Executor handler about to execute:

```python
{
    "type": "executor_invoked",
    "executor_id": "processor",
    "data": {
        "handler_name": "process",
        "input": "input message",
        "input_type": "str"
    },
    "superstep": 1
}
```

**When:** Right before handler method invoked.

### output

Data sent via `ctx.send_message()`:

```python
{
    "type": "output",
    "executor_id": "processor",
    "data": {
        "message": "processed data",
        "target": None  # None if broadcast, specific ID if targeted
    },
    "superstep": 1
}
```

**When:** Executor calls `ctx.send_message()` or returns value from handler.

### executor_completed

Executor handler finished successfully:

```python
{
    "type": "executor_completed",
    "executor_id": "processor",
    "data": {
        "handler_name": "process",
        "duration_ms": 125,
        "status": "success"
    },
    "superstep": 1
}
```

**When:** Handler completes without error.

### executor_failed

Executor handler raised exception:

```python
{
    "type": "executor_failed",
    "executor_id": "processor",
    "data": {
        "handler_name": "process",
        "error": "ValueError: invalid input",
        "traceback": "...",
        "duration_ms": 50
    },
    "superstep": 1
}
```

**When:** Unhandled exception in handler. Workflow halts by default.

### error

Workflow-level error (different from executor_failed):

```python
{
    "type": "error",
    "executor_id": "workflow",
    "data": {
        "error": "No handler found for type int in executor xyz",
        "phase": "message_routing"
    },
    "superstep": None
}
```

**When:** Framework error (type mismatch, missing executor, etc.).

### warning

Non-fatal warning:

```python
{
    "type": "warning",
    "executor_id": "processor",
    "data": {
        "message": "Slow execution",
        "duration_ms": 5000
    },
    "superstep": 1
}
```

**When:** Framework detects conditions needing attention.

### request_info

Executor requests external information (human-in-the-loop):

```python
{
    "type": "request_info",
    "executor_id": "validator",
    "data": {
        "question": "Approve this transaction?",
        "request_id": "req_12345",
        "context": {"amount": 1000, "recipient": "user@example.com"}
    },
    "superstep": 3
}
```

**When:** Executor calls context method to request user input.

**Pattern:** Listener collects request, sends response back via workflow context method.

### superstep_started

Superstep begins (Pregel-style BSP):

```python
{
    "type": "superstep_started",
    "executor_id": "workflow",
    "data": {
        "superstep": 1,
        "executors_to_run": ["processor", "validator", "logger"]
    },
    "superstep": 1
}
```

**When:** Framework prepares to invoke next batch of executors.

### superstep_completed

Superstep finished, all executors in batch complete:

```python
{
    "type": "superstep_completed",
    "executor_id": "workflow",
    "data": {
        "superstep": 1,
        "executed": ["processor", "validator", "logger"],
        "messages_produced": 3,
        "duration_ms": 250
    },
    "superstep": 1
}
```

**When:** All executors in current superstep complete (or timeout).

## WorkflowOutputEvent

Special event for final workflow outputs:

```python
from agent_framework import WorkflowOutputEvent

class WorkflowOutputEvent(WorkflowEvent):
    type: str = "workflow_output"
    data: Any  # Final output from ctx.yield_output()
```

**When:** Exit executor calls `ctx.yield_output()`.

**Accessing outputs:**
```python
async for event in workflow.run_stream(input_data):
    if isinstance(event, WorkflowOutputEvent):
        final_result = event.data
        print(f"Final output: {final_result}")
```

## Streaming with run_stream

Execute workflow and stream events in real-time:

```python
async for event in workflow.run_stream("input data"):
    if event.type == "started":
        print("Workflow started")

    elif event.type == "executor_invoked":
        print(f"{event.executor_id} is processing...")

    elif event.type == "output":
        target = event.data.get("target", "next")
        print(f"{event.executor_id} sent: {event.data['message']} -> {target}")

    elif event.type == "executor_completed":
        print(f"{event.executor_id} done in {event.data['duration_ms']}ms")

    elif event.type == "executor_failed":
        print(f"ERROR: {event.executor_id} failed: {event.data['error']}")

    elif event.type == "request_info":
        print(f"Human input needed: {event.data['question']}")

    elif isinstance(event, WorkflowOutputEvent):
        print(f"Final result: {event.data}")
```

## Monitoring with Custom Events

Executors can emit custom events:

```python
from agent_framework import WorkflowEvent

class ProcessingExecutor(Executor):
    @handler
    async def process(self, data: dict, ctx: WorkflowContext) -> None:
        # Standard processing
        result = expensive_operation(data)

        # Emit custom event for monitoring
        custom_event = WorkflowEvent(
            type="processing_milestone",
            executor_id=self.id,
            data={
                "milestone": "transformation_complete",
                "input_size": len(str(data)),
                "output_size": len(str(result))
            }
        )
        await ctx.add_event(custom_event)

        await ctx.send_message(result)

# Listen for custom events
async for event in workflow.run_stream(input_data):
    if event.type == "processing_milestone":
        print(f"Milestone: {event.data['milestone']}")
        print(f"Size change: {event.data['input_size']} -> {event.data['output_size']}")
```

## Event Processing Patterns

### Pattern 1: Simple Output Collection

Get final output(s):

```python
events = await workflow.run(input_data)
outputs = events.get_outputs()
print(f"Results: {outputs}")
```

### Pattern 2: Real-Time Monitoring

Stream and log all events:

```python
import asyncio
import json
from datetime import datetime

async def monitor_workflow(workflow, input_data):
    execution_log = []

    async for event in workflow.run_stream(input_data):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": event.type,
            "executor_id": event.executor_id,
            "superstep": event.superstep,
            "data": event.data
        }
        execution_log.append(log_entry)

        # Print progress
        if event.type in ["executor_invoked", "executor_completed", "error"]:
            print(json.dumps(log_entry, indent=2))

    return execution_log
```

### Pattern 3: Human-in-the-Loop

Pause for user approval:

```python
async def workflow_with_approval(workflow, input_data):
    async for event in workflow.run_stream(input_data):
        if event.type == "request_info":
            # Display request to user
            print(f"Request: {event.data['question']}")
            print(f"Context: {event.data['context']}")

            # Get user response
            response = input("Enter your response: ")

            # Send back to workflow
            await workflow.send_response(
                request_id=event.data['request_id'],
                response=response
            )

        elif isinstance(event, WorkflowOutputEvent):
            print(f"Approved. Final result: {event.data}")

# Run with approval loop
await workflow_with_approval(workflow, input_data)
```

### Pattern 4: Error Handling

Catch and handle executor failures:

```python
async def workflow_with_error_handling(workflow, input_data):
    errors_encountered = []
    final_output = None

    async for event in workflow.run_stream(input_data):
        if event.type == "executor_failed":
            error_info = {
                "executor": event.executor_id,
                "error": event.data['error'],
                "handler": event.data['handler_name'],
                "superstep": event.superstep
            }
            errors_encountered.append(error_info)
            print(f"Captured error: {event.data['error']}")
            # Workflow stops on error by default
            # Could implement recovery logic here

        elif isinstance(event, WorkflowOutputEvent):
            final_output = event.data

    return {
        "success": len(errors_encountered) == 0,
        "errors": errors_encountered,
        "output": final_output
    }
```

### Pattern 5: Performance Analysis

Track execution metrics:

```python
async def analyze_performance(workflow, input_data):
    metrics = {
        "executor_times": {},
        "superstep_times": {},
        "total_duration": 0
    }

    superstep_start = None

    async for event in workflow.run_stream(input_data):
        if event.type == "superstep_started":
            superstep_start = event.timestamp

        elif event.type == "superstep_completed":
            duration = (event.timestamp - superstep_start).total_seconds() * 1000
            metrics["superstep_times"][event.superstep] = {
                "duration_ms": duration,
                "executors": event.data['executed']
            }

        elif event.type == "executor_completed":
            executor_id = event.executor_id
            duration = event.data['duration_ms']
            if executor_id not in metrics["executor_times"]:
                metrics["executor_times"][executor_id] = []
            metrics["executor_times"][executor_id].append(duration)

    # Calculate averages
    for executor_id, times in metrics["executor_times"].items():
        metrics["executor_times"][executor_id] = {
            "avg_ms": sum(times) / len(times),
            "min_ms": min(times),
            "max_ms": max(times),
            "count": len(times)
        }

    return metrics
```

## Superstep Execution Model (Pregel BSP)

Workflow uses Bulk Synchronous Parallel (BSP) superstep model:

```
Superstep 0:
  ├─ Entry executor processes input
  └─ Sends messages to next batch

Superstep 1:
  ├─ All receiving executors run concurrently
  ├─ Each can send messages to next batch
  └─ All must complete before next superstep

Superstep 2:
  ├─ New batch of executors (those that received messages)
  └─ Repeat until no more messages

Final:
  ├─ Exit executor yields output
  └─ Workflow completes
```

**Events per superstep:**
1. `superstep_started` — Batch beginning
2. `executor_invoked` (multiple, parallel) — Executors starting
3. `output` (multiple) — Messages between executors
4. `executor_completed` (multiple) — Executors finishing
5. `superstep_completed` — Batch done

## Event Stream Filtering

Filter events by type:

```python
async def get_only_errors(workflow, input_data):
    errors = []
    async for event in workflow.run_stream(input_data):
        if event.type in ["error", "executor_failed", "warning"]:
            errors.append({
                "type": event.type,
                "executor": event.executor_id,
                "detail": event.data
            })
    return errors

async def track_output_messages(workflow, input_data):
    messages = []
    async for event in workflow.run_stream(input_data):
        if event.type == "output":
            messages.append({
                "from": event.executor_id,
                "message": event.data['message'],
                "superstep": event.superstep
            })
    return messages
```

## Event Timing

Use event timestamps for performance analysis:

```python
import time

async def timeline(workflow, input_data):
    timeline_events = []

    async for event in workflow.run_stream(input_data):
        timeline_events.append({
            "time": event.timestamp,
            "elapsed_ms": (event.timestamp - start_time).total_seconds() * 1000,
            "type": event.type,
            "executor": event.executor_id,
            "superstep": event.superstep
        })

    # Print timeline
    for entry in timeline_events:
        print(f"{entry['elapsed_ms']:7.1f}ms | {entry['type']:20s} | {entry['executor']}")
```

## Summary Table

| Event Type | When | Use Case |
|---|---|---|
| `started` | Workflow begins | Setup/logging |
| `executor_invoked` | Handler about to run | Tracing |
| `output` | Message sent | Data flow visibility |
| `executor_completed` | Handler finished | Performance metrics |
| `executor_failed` | Handler error | Error handling |
| `error` | Framework error | Debugging |
| `warning` | Warning condition | Alerting |
| `request_info` | Input requested | Human-in-the-loop |
| `superstep_started` | Batch begins | BSP tracing |
| `superstep_completed` | Batch done | Performance analysis |
| `workflow_output` | Final output | Result collection |

## Complete Streaming Example

```python
async def full_example():
    workflow = build_my_workflow()

    async for event in workflow.run_stream("process this"):
        match event.type:
            case "started":
                print("Starting workflow...")

            case "executor_invoked":
                print(f"  {event.executor_id} running...")

            case "output":
                target = event.data.get("target", "→ next")
                print(f"    {event.executor_id} → {target}")

            case "executor_completed":
                print(f"  {event.executor_id} ✓ ({event.data['duration_ms']}ms)")

            case "executor_failed":
                print(f"  {event.executor_id} ✗ Error: {event.data['error']}")
                break

            case "request_info":
                response = await get_user_input(event.data['question'])
                await workflow.send_response(event.data['request_id'], response)

            case "error":
                print(f"  Workflow error: {event.data['error']}")
                break

            case _ if isinstance(event, WorkflowOutputEvent):
                print(f"Final result: {event.data}")
```
