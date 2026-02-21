# Workflow State Management — Shared State, Isolation, Context Data

## Overview

Workflows maintain shared state across multiple executor invocations. State can be stored in the workflow context, executor instances, or message data, enabling stateful processing and data accumulation across pipeline stages.

## ctx.set_state() and ctx.get_state()

Store and retrieve key-value state in the workflow context:

```python
from agent_framework.workflows import WorkflowContext, Executor, handler

class StatefulExecutor(Executor):
    def __init__(self):
        super().__init__(id="state_example")

    @handler
    async def process(self, data: str, ctx: WorkflowContext[str]) -> None:
        # Store state
        await ctx.set_state("current_item", data)
        await ctx.set_state("processed_count", 1)

        # Retrieve state
        item = await ctx.get_state("current_item")
        count = await ctx.get_state("processed_count")

        await ctx.send_message(f"Item: {item}, Count: {count}")
```

### API Reference

| Method | Signature | Description |
|---|---|---|
| `set_state` | `await ctx.set_state(key, value)` | Store any Python object by key |
| `get_state` | `await ctx.get_state(key)` | Retrieve stored value; returns None if missing |

### Key Types

State can store any serializable Python type:

```python
# Strings
await ctx.set_state("name", "Alice")

# Numbers
await ctx.set_state("count", 42)

# Collections
await ctx.set_state("items", ["a", "b", "c"])
await ctx.set_state("config", {"debug": True})

# Pydantic models
from pydantic import BaseModel
class User(BaseModel):
    id: str
    name: str

user = User(id="123", name="Alice")
await ctx.set_state("user", user)
retrieved_user = await ctx.get_state("user")

# Custom classes
class FileContent:
    def __init__(self, path, content):
        self.path = path
        self.content = content

await ctx.set_state("file", FileContent("data.txt", "..."))
```

## Passing State Through Message Data

Share state by embedding it in messages:

```python
@handler
async def step1(self, input_data: str, ctx: WorkflowContext[dict]) -> None:
    # Process and attach state to outgoing message
    result = {"original": input_data, "processed": input_data.upper()}
    await ctx.send_message(result)

@handler
async def step2(self, message_with_state: dict, ctx: WorkflowContext[dict]) -> None:
    # Receive state in message
    original = message_with_state["original"]
    processed = message_with_state["processed"]

    # Add more state
    message_with_state["step2_result"] = f"{processed}_final"
    await ctx.send_message(message_with_state)
```

### Accumulator Pattern

```python
class Pipeline(Executor):
    """Passes accumulator dict through workflow stages."""

    def __init__(self):
        super().__init__(id="pipeline")

    @handler
    async def start(self, topic: str, ctx: WorkflowContext[dict]) -> None:
        # Create initial accumulator
        accumulator = {
            "topic": topic,
            "steps_completed": [],
            "results": {}
        }
        await ctx.send_message(accumulator)

class StepA(Executor):
    def __init__(self):
        super().__init__(id="step_a")

    @handler
    async def execute(self, accumulator: dict, ctx: WorkflowContext[dict]) -> None:
        # Read accumulated state
        topic = accumulator["topic"]

        # Process
        result_a = f"Analysis of {topic}"

        # Update accumulator
        accumulator["steps_completed"].append("step_a")
        accumulator["results"]["analysis"] = result_a

        await ctx.send_message(accumulator)

class StepB(Executor):
    def __init__(self):
        super().__init__(id="step_b")

    @handler
    async def execute(self, accumulator: dict, ctx: WorkflowContext[dict]) -> None:
        # Build on previous results
        analysis = accumulator["results"]["analysis"]
        result_b = f"Summary: {analysis}"

        accumulator["steps_completed"].append("step_b")
        accumulator["results"]["summary"] = result_b

        await ctx.send_message(accumulator)
```

## Executor Internal State

Executors can maintain mutable state across invocations (within a single workflow run):

```python
class Counter(Executor):
    """Executor with internal state."""

    def __init__(self):
        super().__init__(id="counter")
        self.count = 0  # Internal state
        self.history = []

    @handler
    async def increment(self, value: int, ctx: WorkflowContext[int]) -> None:
        self.count += value
        self.history.append(self.count)
        await ctx.send_message(self.count)

    @handler
    async def get_summary(self, _: str, ctx: WorkflowContext[dict]) -> None:
        await ctx.send_message({
            "current": self.count,
            "history": self.history
        })
```

### Important: State Isolation

Internal executor state is NOT automatically isolated between workflow runs. See "State Isolation" section below.

## WorkflowContext.data Dictionary

Access shared context data directly (in addition to set_state/get_state):

```python
@handler
async def process(self, input_data: str, ctx: WorkflowContext[str]) -> None:
    # Direct dictionary access (if supported by implementation)
    ctx.data["shared_key"] = "shared_value"
    value = ctx.data.get("shared_key")
```

This is lower-level access compared to `set_state`/`get_state`.

## State Isolation — Critical for Production

### Problem: Shared State Between Runs

Without proper isolation, executor state leaks between different workflow invocations:

```python
# WRONG - Shared state across runs
counter = Counter()  # Create once
workflow1 = WorkflowBuilder(start_executor=counter).build()

# Run 1
await workflow1.run("input1")
# counter.count == 1

# Run 2 - counter.count still exists!
await workflow1.run("input2")
# counter.count == 2 (leaked from run 1)
```

### Solution: Factory Pattern (Recommended)

Create fresh executor instances for each workflow:

```python
def create_workflow():
    """Factory function creates fresh instances each time."""
    # New executor instance for each call
    counter = Counter()
    workflow = WorkflowBuilder(start_executor=counter).build()
    return workflow

# Each call gets isolated executors
workflow1 = create_workflow()
await workflow1.run("input1")  # counter.count == 1

workflow2 = create_workflow()
await workflow2.run("input2")  # Different Counter, count == 1
```

### Builder Pattern for Complex Workflows

```python
class WorkflowFactory:
    """Factory for creating isolated workflows."""

    @staticmethod
    def create_analysis_workflow():
        # Create fresh instances
        parser = DataParser()
        analyzer = DataAnalyzer()
        reviewer = DataReviewer()

        return (
            WorkflowBuilder(start_executor=parser)
            .add_edge(parser, analyzer)
            .add_edge(analyzer, reviewer)
            .build()
        )

# Safe usage
for task in tasks:
    workflow = WorkflowFactory.create_analysis_workflow()
    await workflow.run(task)
```

## Sharing State Across Multiple Workflows

When you need data shared between separate workflow instances, use external storage:

```python
import json

class SharedStateStore:
    """Persistent state across workflows."""

    def __init__(self, storage_path: str):
        self.path = storage_path

    async def save(self, key: str, value):
        # Load existing
        data = {}
        try:
            with open(self.path) as f:
                data = json.load(f)
        except FileNotFoundError:
            pass

        # Update and save
        data[key] = value
        with open(self.path, 'w') as f:
            json.dump(data, f)

    async def load(self, key: str):
        try:
            with open(self.path) as f:
                data = json.load(f)
            return data.get(key)
        except FileNotFoundError:
            return None

# Use in workflows
store = SharedStateStore("/tmp/workflow_state.json")

class Workflow1:
    @handler
    async def produce(self, input_data: str, ctx: WorkflowContext[str]) -> None:
        result = input_data.upper()
        await store.save("result_from_wf1", result)
        await ctx.send_message(result)

class Workflow2:
    @handler
    async def consume(self, _: str, ctx: WorkflowContext[str]) -> None:
        result = await store.load("result_from_wf1")
        await ctx.send_message(f"Got: {result}")
```

## Custom Context Data via Workflow Kwargs

Pass custom context to all executors in a workflow:

```python
from agent_framework import WorkflowBuilder

# Build workflow with custom context
workflow = (
    WorkflowBuilder(
        start_executor=my_executor,
        # Custom kwargs passed to context
        workflow_context_data={
            "request_id": "req_12345",
            "user_id": "user_789",
            "tenant": "acme-corp"
        }
    )
    .build()
)

# Access in executors
class ContextAwareExecutor(Executor):
    @handler
    async def process(self, data: str, ctx: WorkflowContext[str]) -> None:
        # Access custom context
        request_id = ctx.data.get("request_id")
        user_id = ctx.data.get("user_id")

        await ctx.send_message(f"Processing for user {user_id} in request {request_id}")
```

## State Management Best Practices

### Pattern: Request-Scoped State

```python
class RequestScopedWorkflow:
    """Store request context for entire workflow."""

    @staticmethod
    def create_workflow_with_request(request_id: str, user_id: str):
        class FirstStep(Executor):
            @handler
            async def process(self, data: str, ctx: WorkflowContext[str]) -> None:
                # Store request context at start
                await ctx.set_state("request_id", request_id)
                await ctx.set_state("user_id", user_id)
                await ctx.send_message(data)

        class LastStep(Executor):
            @handler
            async def process(self, data: str, ctx: WorkflowContext[str]) -> None:
                # Retrieve context at end
                req = await ctx.get_state("request_id")
                user = await ctx.get_state("user_id")
                await ctx.send_message({
                    "result": data,
                    "request_id": req,
                    "user_id": user
                })

        return (
            WorkflowBuilder(start_executor=FirstStep())
            .add_edge(FirstStep(), LastStep())
            .build()
        )
```

### Pattern: Stateful Cache

```python
from datetime import datetime

class CacheManager(Executor):
    """Cache results during workflow execution."""

    def __init__(self):
        super().__init__(id="cache")
        self.cache = {}  # Executor-local cache
        self.access_count = {}

    @handler
    async def cache_set(self, item: dict, ctx: WorkflowContext[dict]) -> None:
        key = item.get("key")
        value = item.get("value")

        self.cache[key] = {
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
        self.access_count[key] = 0

        await ctx.send_message({"cached": key})

    @handler
    async def cache_get(self, key: str, ctx: WorkflowContext[dict]) -> None:
        if key in self.cache:
            self.access_count[key] += 1
            await ctx.send_message({
                "hit": True,
                "value": self.cache[key]["value"],
                "accesses": self.access_count[key]
            })
        else:
            await ctx.send_message({"hit": False, "key": key})

    @handler
    async def cache_summary(self, _: str, ctx: WorkflowContext[dict]) -> None:
        await ctx.send_message({
            "size": len(self.cache),
            "access_counts": self.access_count
        })
```

### Pattern: State Cleanup

```python
class StatefulWithCleanup(Executor):
    """Initialize and cleanup state."""

    def __init__(self):
        super().__init__(id="cleanup_example")
        self.resources = []

    @handler
    async def initialize(self, config: dict, ctx: WorkflowContext[str]) -> None:
        # Setup state
        await ctx.set_state("config", config)
        await ctx.set_state("initialized_at", datetime.now().isoformat())
        await ctx.send_message("initialized")

    @handler
    async def process(self, data: str, ctx: WorkflowContext[str]) -> None:
        config = await ctx.get_state("config")
        # Process using config
        await ctx.send_message(f"Processed {data}")

    @handler
    async def cleanup(self, _: str, ctx: WorkflowContext[str]) -> None:
        # Clear state
        await ctx.set_state("config", None)
        await ctx.set_state("initialized_at", None)
        await ctx.send_message("cleaned_up")
```

## Common Pitfalls

| Problem | Solution |
|---|---|
| Executor state shared across runs | Use factory pattern; create new instances |
| State not persisting across await points | Use ctx.set_state instead of instance variables for cross-executor data |
| Memory leaks from accumulating state | Implement cleanup; limit cache sizes |
| Race conditions in concurrent workflows | Use ctx.get_state/set_state (thread-safe) over shared objects |
| Lost state in nested workflows | Pass state explicitly as message data |
| Isolation failures in test mode | Create fresh workflow for each test via factory |
