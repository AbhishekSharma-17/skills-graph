# Workflow Executors — Nodes, Handlers, Types, Lifecycle

Executors are the fundamental processing units of a workflow. Each executor is a node in the workflow graph that receives typed messages, performs operations, and produces output.

## Executor Base Class

All executors inherit from the `Executor` base class:

```python
from agent_framework import Executor, WorkflowContext, handler

class MyExecutor(Executor):
    def __init__(self, id: str):
        super().__init__(id=id)
```

**Constructor:**
- `id` (str): Unique identifier for the executor in the workflow (required)

## Class-Based Executors

Define executors as classes inheriting from `Executor`. Use the `@handler` decorator on methods to process messages.

### Basic Handler

```python
from agent_framework import Executor, handler, WorkflowContext

class UpperCase(Executor):
    def __init__(self, id: str = "upper_case"):
        super().__init__(id=id)

    @handler
    async def to_upper_case(self, text: str, ctx: WorkflowContext[str]) -> None:
        """Receive text and forward uppercase version to next node."""
        result = text.upper()
        await ctx.send_message(result)
```

### Multiple Handlers

A single executor can have multiple handlers to process different input types:

```python
class DataProcessor(Executor):
    def __init__(self):
        super().__init__(id="processor")

    @handler
    async def process_text(self, text: str, ctx: WorkflowContext[str]) -> None:
        """Handle string input."""
        await ctx.send_message(f"Text: {text.upper()}")

    @handler
    async def process_int(self, number: int, ctx: WorkflowContext[int]) -> None:
        """Handle int input."""
        await ctx.send_message(number * 2)

    @handler
    async def process_dict(self, data: dict, ctx: WorkflowContext[dict]) -> None:
        """Handle dict input."""
        await ctx.send_message({"processed": True, **data})
```

The framework dispatches messages to the appropriate handler based on input type.

### Executor with Custom Initialization

Executors can hold state and dependencies:

```python
class ContentCreator(Executor):
    def __init__(self, model_client, style: str = "formal"):
        super().__init__(id="content_creator")
        self.client = model_client
        self.style = style

    @handler
    async def create(self, topic: str, ctx: WorkflowContext[str]) -> None:
        prompt = f"Write about {topic} in a {self.style} style."
        response = await self.client.complete_async(prompt)
        await ctx.send_message(response.text)
```

## Function-Based Executors

Create executors from async functions using the `@executor` decorator:

```python
from agent_framework import executor, WorkflowContext

@executor(id="reverse_text")
async def reverse_text(text: str, ctx: WorkflowContext[str]) -> None:
    """Reverse input string and send to next node."""
    await ctx.send_message(text[::-1])
```

Function-based executors are more concise for simple operations. They automatically register as executors with the provided `id`.

## @handler Decorator

The `@handler` decorator marks a method as a message handler. Handler methods must be async.

### Type Annotations (Implicit Types)

Use type annotations for input and output:

```python
class ProcessingExecutor(Executor):
    @handler
    async def process(self, data: str, ctx: WorkflowContext[str]) -> None:
        """Type hints define input (str) and what ctx can forward (str)."""
        await ctx.send_message(data.upper())
```

**Context Type Parameters:**
- `WorkflowContext[InputType]` — receives InputType, forwards to next node
- `WorkflowContext[InputType, OutputType]` — receives InputType, yields OutputType (exit node)
- `WorkflowContext[Never, OutputType]` — no forwarding, only yields output (exit node)

### Explicit Type Parameters

Specify types via decorator arguments instead of type hints:

```python
class ExplicitTypesExecutor(Executor):
    @handler(input=str, output=str)
    async def to_upper(self, text, ctx) -> None:
        """Explicit: accepts str, forwards str."""
        await ctx.send_message(text.upper())

    @handler(input=str | int, output=str)
    async def handle_mixed(self, message, ctx) -> None:
        """Union types: accept str OR int."""
        await ctx.send_message(str(message).upper())

    @handler(input=dict, output=int, workflow_output=bool)
    async def complex_handler(self, data, ctx) -> None:
        """Can forward int AND yield bool as final output."""
        await ctx.send_message(len(data))
        await ctx.yield_output(True)
```

**Explicit Parameters:**
- `input` (required): Type or Union of types accepted
- `output` (optional): Type forwarded to next nodes
- `workflow_output` (optional): Type for `ctx.yield_output()`

**Important:** When using explicit parameters, specify **all** types — cannot mix type hints with explicit decorator parameters.

## WorkflowContext Methods

The context object passed to every handler controls data flow:

| Method | Signature | Purpose |
|---|---|---|
| `send_message(data)` | `async def send_message(data: T) -> None` | Forward message to connected executors |
| `send_message(data, target)` | `async def send_message(data: T, target: str) -> None` | Send to specific executor by ID |
| `yield_output(data)` | `async def yield_output(data: T) -> None` | Produce final workflow output (exit node) |
| `add_event(event)` | `async def add_event(event: WorkflowEvent) -> None` | Emit custom event to stream |

### send_message Examples

```python
@handler
async def forward_to_next(self, data: str, ctx: WorkflowContext[str]) -> None:
    """Default: send to all connected executors."""
    await ctx.send_message(data.upper())

@handler
async def selective_routing(self, data: dict, ctx: WorkflowContext[dict]) -> None:
    """Send to specific executor by ID."""
    if data.get("urgent"):
        await ctx.send_message(data, target="urgent_handler")
    else:
        await ctx.send_message(data, target="normal_handler")
```

### yield_output

Yield final workflow output. Only exit nodes call this:

```python
class ExitExecutor(Executor):
    @handler
    async def finalize(self, data: str, ctx: WorkflowContext[Never, str]) -> None:
        # Never = don't forward to next (this is exit node)
        final_result = f"Completed: {data}"
        await ctx.yield_output(final_result)
```

### add_event

Emit custom workflow events for monitoring:

```python
@handler
async def process_with_event(self, data: str, ctx: WorkflowContext) -> None:
    # Create and emit a custom event
    event = WorkflowEvent(
        type="custom_processing",
        executor_id=self.id,
        data={"stage": "processing", "input": data}
    )
    await ctx.add_event(event)
    # ... continue processing
```

## Handler Lifecycle

Handlers execute in order when messages arrive:

1. **Message received** — Framework matches input type to appropriate handler
2. **Handler invoked** — Async handler method executes with context
3. **send_message() called** — Message queued for connected executors
4. **yield_output() called** — Output collected for workflow result
5. **Handler completes** — Next executor in chain invoked (superstep execution)

## Nested Workflows (WorkflowExecutor)

Run a workflow as an executor node:

```python
from agent_framework import WorkflowExecutor

# Define inner workflow
inner_workflow = WorkflowBuilder(start_executor="step1")\
    .add_executor("step1", executor1)\
    .add_executor("step2", executor2)\
    .add_edge("step1", "step2")\
    .build()

# Use as executor in outer workflow
nested_exec = WorkflowExecutor(
    id="inner_workflow_node",
    workflow=inner_workflow
)

# Add to outer workflow like any executor
outer_workflow = WorkflowBuilder(start_executor="outer_step1")\
    .add_executor("outer_step1", some_executor)\
    .add_executor("nested_workflow", nested_exec)\
    .add_edge("outer_step1", "nested_workflow")\
    .build()
```

## Common Patterns

### Validation Executor

Validate data and conditionally route:

```python
class ValidatingExecutor(Executor):
    @handler
    async def validate(self, data: dict, ctx: WorkflowContext[dict]) -> None:
        if not data.get("required_field"):
            await ctx.send_message(
                {"error": "Missing required_field"},
                target="error_handler"
            )
        else:
            await ctx.send_message(data, target="processing_handler")
```

### Transformation Executor

Transform one type to another:

```python
class JSONTransformer(Executor):
    @handler(input=str, output=dict)
    async def parse_json(self, json_str, ctx) -> None:
        import json
        try:
            data = json.loads(json_str)
            await ctx.send_message(data)
        except json.JSONDecodeError as e:
            await ctx.send_message(
                {"error": str(e)},
                target="error_handler"
            )
```

### API Integration Executor

Call external API and forward response:

```python
class APIExecutor(Executor):
    def __init__(self, api_client):
        super().__init__(id="api_caller")
        self.client = api_client

    @handler
    async def call_api(self, request: dict, ctx: WorkflowContext[dict]) -> None:
        try:
            response = await self.client.post("/endpoint", json=request)
            await ctx.send_message(response.json())
        except Exception as e:
            await ctx.send_message(
                {"error": str(e)},
                target="error_handler"
            )
```

## Executor State & Checkpointing

Executors can save and restore state across checkpoints:

```python
class StatefulExecutor(Executor):
    def __init__(self):
        super().__init__(id="stateful")
        self.counter = 0

    @handler
    async def process(self, data: str, ctx: WorkflowContext[str]) -> None:
        self.counter += 1
        await ctx.send_message(f"{data} (count: {self.counter})")

    async def on_checkpoint_save(self) -> dict:
        """Called before checkpoint. Return state dict."""
        return {"counter": self.counter}

    async def on_checkpoint_restore(self, state: dict) -> None:
        """Called after checkpoint restore. Restore internal state."""
        self.counter = state.get("counter", 0)
```

**Checkpoint Methods:**
- `on_checkpoint_save() -> dict` — Serialize executor state before checkpoint
- `on_checkpoint_restore(state: dict) -> None` — Restore state after checkpoint resume

## Handler Signature Reference

```python
# Minimal handler (no forwarding)
@handler
async def my_handler(self, msg: str, ctx: WorkflowContext) -> None:
    print(msg)

# Forward to next executor
@handler
async def forward(self, msg: str, ctx: WorkflowContext[str]) -> None:
    await ctx.send_message(msg.upper())

# Exit handler (yield output)
@handler
async def exit_handler(self, msg: str, ctx: WorkflowContext[Never, str]) -> None:
    await ctx.yield_output(f"Result: {msg}")

# Both forward and yield
@handler
async def hybrid(self, msg: str, ctx: WorkflowContext[str, int]) -> None:
    await ctx.send_message(msg)
    await ctx.yield_output(len(msg))

# Explicit types
@handler(input=str | int, output=str)
async def explicit(self, msg, ctx) -> None:
    await ctx.send_message(str(msg))
```

## Summary Table

| Aspect | Details |
|---|---|
| **Definition** | Inherit `Executor`, decorate methods with `@handler` |
| **Function-based** | Use `@executor(id=...)` decorator on async function |
| **Handler dispatching** | Matches input type to appropriate handler method |
| **Data flow** | `ctx.send_message()` to forward, `ctx.yield_output()` to exit |
| **Multiple handlers** | Same executor can handle multiple input types |
| **Type specification** | Use type hints OR explicit decorator parameters, not both |
| **Selective routing** | Use `send_message(data, target="executor_id")` |
| **Custom events** | Use `ctx.add_event()` for observability |
| **State persistence** | Implement `on_checkpoint_save/restore` methods |
| **Nesting** | Use `WorkflowExecutor` to run workflows as nodes |
