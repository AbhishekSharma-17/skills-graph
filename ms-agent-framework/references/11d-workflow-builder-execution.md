# Workflow Builder & Execution — Construction, Running, Results

## WorkflowBuilder Class

The fluent API for constructing workflows. Provides methods to add executors, define edges, and build the final workflow.

### Constructor

```python
from agent_framework import WorkflowBuilder

# Create builder with entry executor
builder = WorkflowBuilder(start_executor="entry_executor_id")
```

**Parameters:**
- `start_executor` (str): ID of the executor that receives initial `workflow.run()` input

The start executor must be added with `add_executor()` before building.

### add_executor

Add an executor node to the workflow:

```python
builder.add_executor("step1", my_executor)
builder.add_executor("step2", another_executor)

# Can add both class-based and function-based executors
builder.add_executor("formatter", format_function)
```

**Signature:**
```python
def add_executor(self, id: str, executor: Executor | Callable) -> WorkflowBuilder
```

Returns self for method chaining.

### add_edge

Connect one executor to another:

```python
# Simple edge: step1 → step2
builder.add_edge(source="step1", target="step2")

# Conditional edge: only if condition true
builder.add_edge(
    source="router",
    target="urgent_handler",
    condition=lambda data: data.get("priority") == "high"
)
```

**Signature:**
```python
def add_edge(
    self,
    source: str,
    target: str,
    condition: Optional[Callable[[Any], bool]] = None
) -> WorkflowBuilder
```

**Parameters:**
- `source` (str): Source executor ID
- `target` (str): Target executor ID
- `condition` (optional): Function that returns bool to decide if edge activates

### add_fan_out_edges

Send to multiple executors, optionally filtering targets:

```python
# Simple fan-out: send to all three
builder.add_fan_out_edges(
    source="splitter",
    targets=["handler_a", "handler_b", "handler_c"]
)

# With selection function: send to subset
builder.add_fan_out_edges(
    source="splitter",
    targets=["handler_a", "handler_b", "handler_c"],
    selection_func=lambda data: [
        t for t in ["handler_a", "handler_b", "handler_c"]
        if should_send_to(t, data)
    ]
)
```

**Signature:**
```python
def add_fan_out_edges(
    self,
    source: str,
    targets: list[str],
    selection_func: Optional[Callable[[Any], list[str]]] = None
) -> WorkflowBuilder
```

**Parameters:**
- `source` (str): Source executor ID
- `targets` (list[str]): All possible target executor IDs
- `selection_func` (optional): Function receiving message, returns list of target IDs to receive it

If `selection_func` is None, all targets receive the message.

### add_fan_in_edge

Multiple sources to single target. Just use `add_edge()` multiple times:

```python
builder.add_edge("source_a", "merger")
builder.add_edge("source_b", "merger")
builder.add_edge("source_c", "merger")
```

**Note:** `add_fan_in_edge` is not typically exposed; use multiple `add_edge` calls instead.

### add_switch_case_edge_group

Declarative conditional routing with cases and default:

```python
from agent_framework import SwitchCaseEdgeGroup, Case

def is_error(data: dict) -> bool:
    return data.get("status") == "error"

def is_warning(data: dict) -> bool:
    return data.get("status") == "warning"

switch_group = SwitchCaseEdgeGroup(
    source="processor",
    cases=[
        Case(condition=is_error, target="error_handler"),
        Case(condition=is_warning, target="warning_handler"),
    ],
    default="success_handler"
)

builder.add_switch_case_edge_group(switch_group)
```

**Signature:**
```python
class SwitchCaseEdgeGroup:
    source: str
    cases: list[Case]
    default: str

class Case:
    condition: Callable[[Any], bool]
    target: str
```

Cases evaluated in order; first match wins. Default used if no case matches.

### add_multi_selection_edge_group

Send to multiple targets based on independent conditions:

```python
from agent_framework import MultiSelectionEdgeGroup

multi_group = MultiSelectionEdgeGroup(
    source="logger",
    selections=[
        ("file_logger", lambda d: True),  # Always log to file
        ("cloud_logger", lambda d: d.get("cloud_logging_enabled")),
        ("alerter", lambda d: d.get("severity") > 5),
    ]
)

builder.add_multi_selection_edge_group(multi_group)
```

**Signature:**
```python
class MultiSelectionEdgeGroup:
    source: str
    selections: list[tuple[str, Callable[[Any], bool]]]
```

All matching conditions send to their targets (unlike switch-case which stops at first match).

### add_chain

Quick method to chain executors sequentially:

```python
builder.add_chain([
    ("cleaner", text_cleaner),
    ("analyzer", text_analyzer),
    ("formatter", text_formatter),
])

# Equivalent to:
# builder.add_edge("cleaner", "analyzer")
# builder.add_edge("analyzer", "formatter")
```

**Signature:**
```python
def add_chain(self, chain: list[tuple[str, Executor | Callable]]) -> WorkflowBuilder
```

Each executor added and edges connected in sequence.

### with_checkpointing

Enable checkpointing for resumable execution:

```python
builder.with_checkpointing(
    checkpoint_dir="/tmp/checkpoints",
    save_interval=2  # Save every 2 supersteps
)
```

**Signature:**
```python
def with_checkpointing(
    self,
    checkpoint_dir: str,
    save_interval: int = 1
) -> WorkflowBuilder
```

**Parameters:**
- `checkpoint_dir` (str): Directory to save checkpoints
- `save_interval` (int): Save every N supersteps (default 1)

Checkpoints allow resuming workflow from interruption point.

### build

Construct the workflow. Validates graph and returns `Workflow` instance:

```python
workflow = builder.build()

# Can now run the workflow
result = await workflow.run(input_data)
```

**Validation:**
- All referenced executors exist
- No unreachable executors
- Entry executor exists
- Exit executor exists (unless single executor or all paths lead to output)
- No type mismatches (optional, depends on configuration)

Returns `Workflow` object ready for execution.

## Workflow Class

The executable workflow object. Created by `WorkflowBuilder.build()`.

### run (Non-Streaming)

Execute workflow synchronously and collect all results:

```python
# Simple execution
result = await workflow.run(input_data)

# Get outputs
outputs = result.get_outputs()
print(f"Results: {outputs}")

# Get final state
state = result.get_final_state()
```

**Signature:**
```python
async def run(self, input: Any) -> WorkflowEvents
```

**Returns:** `WorkflowEvents` object with results and state.

**Blocks until:**
- Workflow completes (exit executor yields output)
- Error occurs
- Timeout (if configured)

### run_stream (Streaming)

Execute workflow and stream events in real-time:

```python
async for event in workflow.run_stream(input_data):
    if event.type == "output":
        print(f"Output: {event.data}")

    elif isinstance(event, WorkflowOutputEvent):
        print(f"Final: {event.data}")
        break  # Workflow complete
```

**Signature:**
```python
async def run_stream(self, input: Any) -> AsyncIterator[WorkflowEvent]
```

**Yields:** `WorkflowEvent` objects in order of occurrence.

**Benefits:**
- Real-time visibility into execution
- Implement human-in-the-loop responses
- Monitor progress
- Handle errors gracefully
- Collect custom metrics

## WorkflowEvents Result Object

Returned by `workflow.run()`. Contains execution results and state.

```python
from agent_framework import WorkflowEvents

events = await workflow.run(input_data)
```

### get_outputs

Retrieve final output(s) from workflow:

```python
# Get outputs
outputs = events.get_outputs()

# If single output (most common)
if isinstance(outputs, list) and len(outputs) == 1:
    result = outputs[0]
else:
    result = outputs
```

**Returns:** Final output(s) from exit executor's `ctx.yield_output()`.

### get_final_state

Get workflow execution state after completion:

```python
state = events.get_final_state()

# State typically includes:
# - All executor outputs
# - Execution metadata
# - Timing information
```

**Returns:** State dict with execution results.

## Complete Workflow Construction Example

```python
import asyncio
from agent_framework import (
    WorkflowBuilder,
    Executor,
    handler,
    WorkflowContext,
    SwitchCaseEdgeGroup,
    Case,
)
from typing import Never

# Define executors
class RequestValidator(Executor):
    def __init__(self):
        super().__init__(id="validator")

    @handler
    async def validate(self, request: dict, ctx: WorkflowContext[dict]) -> None:
        # Basic validation
        is_valid = all(k in request for k in ["id", "action"])
        await ctx.send_message({
            "valid": is_valid,
            "request": request,
            "error": None if is_valid else "Missing required fields"
        })

class RequestProcessor(Executor):
    def __init__(self):
        super().__init__(id="processor")

    @handler
    async def process(self, data: dict, ctx: WorkflowContext[dict]) -> None:
        request = data["request"]
        result = {"action": request["action"], "result": "processed"}
        await ctx.send_message({"processed": True, "request": request, "result": result})

class ErrorHandler(Executor):
    def __init__(self):
        super().__init__(id="error_handler")

    @handler
    async def handle_error(self, data: dict, ctx: WorkflowContext) -> None:
        print(f"Error: {data['error']}")

class SuccessFormatter(Executor):
    def __init__(self):
        super().__init__(id="formatter")

    @handler
    async def format_success(self, data: dict, ctx: WorkflowContext[Never, str]) -> None:
        result = f"Success: {data['result']['result']} for {data['request']['action']}"
        await ctx.yield_output(result)

# Build workflow
async def build_workflow():
    validator = RequestValidator()
    processor = RequestProcessor()
    error_handler = ErrorHandler()
    formatter = SuccessFormatter()

    builder = WorkflowBuilder(start_executor="validator")

    # Add all executors
    builder.add_executor("validator", validator)
    builder.add_executor("processor", processor)
    builder.add_executor("error_handler", error_handler)
    builder.add_executor("formatter", formatter)

    # Connect with conditional routing
    builder.add_switch_case_edge_group(
        SwitchCaseEdgeGroup(
            source="validator",
            cases=[
                Case(
                    condition=lambda d: d["valid"],
                    target="processor"
                ),
                Case(
                    condition=lambda d: not d["valid"],
                    target="error_handler"
                )
            ],
            default="error_handler"
        )
    )

    # Connect processor to formatter
    builder.add_edge("processor", "formatter")

    # Enable checkpointing
    builder.with_checkpointing(
        checkpoint_dir="/tmp/workflow_checkpoints",
        save_interval=1
    )

    return builder.build()

# Execute workflow
async def main():
    workflow = await build_workflow()

    # Valid request
    valid_input = {
        "id": "req_123",
        "action": "create"
    }

    result = await workflow.run(valid_input)
    outputs = result.get_outputs()
    print(f"Output: {outputs}")

    # With streaming
    print("\nStreaming execution:")
    async for event in workflow.run_stream(valid_input):
        if event.type == "executor_completed":
            print(f"  {event.executor_id} completed")
        elif isinstance(event, WorkflowOutputEvent):
            print(f"  Result: {event.data}")

asyncio.run(main())
```

## Workflow Execution Rules

| Rule | Details | Consequence |
|---|---|---|
| Must have start executor | `WorkflowBuilder(start_executor=...)` | Build error if missing |
| Start executor ID must be added | Must call `add_executor(start_id, exec)` | Build error |
| All executors must be connected | No orphaned nodes | May fail if node unreachable |
| Type compatibility | Handler input type must match sender output type | Runtime error |
| Single entry point | Only start executor receives initial input | Other executors via edges only |
| Single exit (typically) | One executor calls `ctx.yield_output()` | Workflow complete at first output |
| No circular deadlocks | Cycles okay if data flows; infinite loops problematic | Potential hanging |
| Async handlers only | All handlers must be async | Type error |

## Builder Method Chaining

All builder methods return `self` for fluent chaining:

```python
workflow = (WorkflowBuilder(start_executor="step1")
    .add_executor("step1", executor1)
    .add_executor("step2", executor2)
    .add_executor("step3", executor3)
    .add_edge("step1", "step2")
    .add_edge("step2", "step3")
    .with_checkpointing("/tmp/ckpt")
    .build())
```

## Execution Model

Workflows execute in **supersteps** (Bulk Synchronous Parallel):

```
1. Entry executor receives input_data
   ↓
2. Superstep 1: Entry executes, sends messages
   ↓
3. Superstep 2: All message recipients execute concurrently
   ↓
4. Superstep 3: New message recipients execute
   ↓
... (repeat until no new messages)
   ↓
Final: Exit executor yields output
   ↓
Workflow completes, returns result
```

**Key behaviors:**
- All executors in a superstep run concurrently
- Messages not delivered until superstep completes
- Next superstep begins with message recipients
- Continues until no new messages generated or exit yields output

## Running with Checkpointing

Enable resumable execution:

```python
# Build with checkpointing
builder.with_checkpointing(
    checkpoint_dir="/var/checkpoints",
    save_interval=1  # Save after each superstep
)
workflow = builder.build()

# Run normally
result = await workflow.run(input_data)

# If interrupted, can resume from checkpoint
# (Implementation depends on framework version)
```

## Error Handling During Execution

```python
import asyncio

async def safe_workflow_run(workflow, input_data):
    try:
        result = await workflow.run(input_data)
        return {"success": True, "output": result.get_outputs()}

    except TimeoutError:
        return {"success": False, "error": "Workflow timed out"}

    except ValueError as e:
        return {"success": False, "error": f"Type error: {e}"}

    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {e}"}
```

## Running Nested Workflows

A workflow can be an executor in another workflow:

```python
from agent_framework import WorkflowExecutor

# Inner workflow
inner_wf = (WorkflowBuilder(start_executor="inner_step1")
    .add_executor("inner_step1", inner_exec1)
    .add_executor("inner_step2", inner_exec2)
    .add_edge("inner_step1", "inner_step2")
    .build())

# Use as executor in outer
nested_exec = WorkflowExecutor(
    id="nested",
    workflow=inner_wf
)

# Outer workflow
outer_wf = (WorkflowBuilder(start_executor="outer_step1")
    .add_executor("outer_step1", outer_exec)
    .add_executor("nested", nested_exec)
    .add_executor("outer_step2", outer_exec2)
    .add_edge("outer_step1", "nested")
    .add_edge("nested", "outer_step2")
    .build())

result = await outer_wf.run(input_data)
```

## Performance Optimization

```python
# Use function-based executors for simple operations
@executor(id="fast_processor")
async def quick_process(data: str, ctx: WorkflowContext[str]) -> None:
    await ctx.send_message(data.upper())

# Minimize async calls in handlers
class EfficientExecutor(Executor):
    @handler
    async def process(self, data: dict, ctx: WorkflowContext[dict]) -> None:
        # Do sync work here (multiple sync operations)
        result = process_sync_data(data)
        # Single async call
        await ctx.send_message(result)

# Use streaming for long-running workflows to free memory
async for event in workflow.run_stream(large_input):
    if isinstance(event, WorkflowOutputEvent):
        save_result(event.data)
        # Output processed and freed
```

## Summary Table

| Component | Purpose | Key Method |
|---|---|---|
| WorkflowBuilder | Construct workflow graph | `.build()` |
| add_executor | Add node | `builder.add_executor(id, exec)` |
| add_edge | Connect nodes | `builder.add_edge(src, tgt)` |
| add_fan_out_edges | One-to-many | `builder.add_fan_out_edges(src, [tgt1, tgt2, ...])` |
| add_switch_case | Conditional routing | `builder.add_switch_case_edge_group(group)` |
| with_checkpointing | Enable recovery | `builder.with_checkpointing(dir, interval)` |
| build | Finalize | `workflow = builder.build()` |
| Workflow.run | Execute (blocking) | `result = await workflow.run(input)` |
| Workflow.run_stream | Execute (streaming) | `async for event in workflow.run_stream(input)` |
| WorkflowEvents | Results container | `events.get_outputs()` |
