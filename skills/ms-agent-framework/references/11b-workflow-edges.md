# Workflow Edges — Connections, Routing, Fan-Out, Fan-In

Edges define how data flows between executors in a workflow. The WorkflowBuilder provides methods to create different edge patterns.

## Edge Types

### Simple Edge

Connect one executor directly to another:

```python
from agent_framework import WorkflowBuilder

builder = WorkflowBuilder(start_executor="step1")
builder.add_executor("step1", executor1)
builder.add_executor("step2", executor2)

# Simple edge: step1 → step2
builder.add_edge("step1", "step2")
```

When `step1` calls `ctx.send_message(data)`, it flows to `step2`.

### Conditional Edge (With Condition Function)

Route data conditionally based on content:

```python
def is_urgent(data: dict) -> bool:
    """Condition function: returns True if should follow edge."""
    return data.get("priority") == "high"

builder.add_edge(
    source="router",
    target="urgent_handler",
    condition=is_urgent  # Only if condition returns True
)

builder.add_edge(
    source="router",
    target="normal_handler",
    # No condition: default path
)
```

**Condition Function:**
- Takes message data as parameter
- Returns `bool`: True to allow edge, False to skip
- If condition is False, message does not flow to target
- Executors can have multiple outgoing conditional edges

### Targeted send_message

Send directly to specific executor by ID:

```python
@handler
async def selective_router(self, data: dict, ctx: WorkflowContext[dict]) -> None:
    """Send to different executors based on content."""
    if data.get("type") == "error":
        await ctx.send_message(data, target="error_handler")
    elif data.get("type") == "warning":
        await ctx.send_message(data, target="warning_handler")
    else:
        await ctx.send_message(data, target="normal_handler")

# Wire connections (all three targets must exist as edges)
builder.add_edge("router", "error_handler")
builder.add_edge("router", "warning_handler")
builder.add_edge("router", "normal_handler")
```

This provides runtime flexibility beyond static conditional edges.

## Fan-Out (One to Many)

One executor sends to multiple executors in parallel (superstep execution):

```python
# All executors receive the same data
builder.add_edge("splitter", "handler_a")
builder.add_edge("splitter", "handler_b")
builder.add_edge("splitter", "handler_c")
```

All three handlers execute concurrently (within the same superstep) when `splitter` calls `ctx.send_message()`.

### Fan-Out with Selection Function

Send to subset of connected executors based on selection criteria:

```python
def should_process_in_branch_a(data: dict) -> bool:
    return data.get("category") in ["type1", "type2"]

def should_process_in_branch_b(data: dict) -> bool:
    return data.get("category") in ["type2", "type3"]

builder.add_fan_out_edges(
    source="splitter",
    targets=["handler_a", "handler_b", "handler_c"],
    selection_func=lambda data: [
        target for target, condition in [
            ("handler_a", should_process_in_branch_a(data)),
            ("handler_b", should_process_in_branch_b(data)),
            ("handler_c", True),  # Always send to handler_c
        ] if condition
    ]
)
```

The selection function receives the message and returns list of target executor IDs to receive it.

## Fan-In (Many to One)

Multiple executors send to a single executor (merge):

```python
# Both branches feed into merge
builder.add_edge("handler_a", "merge")
builder.add_edge("handler_b", "merge")
builder.add_edge("handler_c", "merge")
```

The `merge` executor receives messages from all three sources.

### Fan-In with Aggregation

Collect outputs from multiple executors and process together:

```python
class AggregationExecutor(Executor):
    def __init__(self):
        super().__init__(id="aggregator")
        self.collected = []

    @handler
    async def aggregate(self, item: dict, ctx: WorkflowContext[dict]) -> None:
        """Collect items from multiple sources."""
        self.collected.append(item)
        # Forward aggregated result
        await ctx.send_message({"items": self.collected})

builder.add_edge("source_a", "aggregator")
builder.add_edge("source_b", "aggregator")
builder.add_edge("source_c", "aggregator")
builder.add_edge("aggregator", "final")
```

## Switch-Case Edges

Declarative conditional routing with multiple cases and default:

```python
from agent_framework import SwitchCaseEdgeGroup, Case

# Define condition functions
def is_error(data: dict) -> bool:
    return data.get("status") == "error"

def is_warning(data: dict) -> bool:
    return data.get("status") == "warning"

# Create switch-case group
switch_case = SwitchCaseEdgeGroup(
    source="processor",
    cases=[
        Case(condition=is_error, target="error_handler"),
        Case(condition=is_warning, target="warning_handler"),
    ],
    default="success_handler"  # Default if no case matches
)

builder.add_switch_case_edge_group(switch_case)
```

The framework evaluates cases in order and follows the first matching target.

## Multi-Selection Edges

Send to multiple targets based on independent conditions:

```python
from agent_framework import MultiSelectionEdgeGroup

def notify_admin(data: dict) -> bool:
    return data.get("severity") > 5

def log_event(data: dict) -> bool:
    return True  # Always log

multi_select = MultiSelectionEdgeGroup(
    source="processor",
    selections=[
        ("admin_notifier", notify_admin),
        ("logger", log_event),
        ("archiver", lambda d: d.get("archive", False)),
    ]
)

builder.add_multi_selection_edge_group(multi_select)
```

All selected targets that match conditions receive the message.

## Sequential Connection (add_chain)

Quick method to chain executors in sequence:

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

## Edge Validation Rules

The framework enforces constraints:

| Rule | Details | Violation Impact |
|---|---|---|
| All nodes must have outgoing edge(s) OR be exit node | Orphaned executors cause error | Workflow won't build |
| Entry node must not have incoming edges (sources) | Entry is the start | Can be work around with careful routing |
| Exit node must call `ctx.yield_output()` | Must produce final output | Workflow completes with no result |
| Target executor must exist | Referenced executor ID must be added | Build-time error |
| No circular references without careful state management | Infinite loops possible | Deadlock or infinite execution |
| Message types must be compatible | Sender type must match receiver's handler input type | Runtime type error |

## WorkflowBuilder Edge Methods

```python
from agent_framework import WorkflowBuilder

builder = WorkflowBuilder(start_executor="entry")

# Add simple edge
builder.add_edge(source="executor1", target="executor2")

# Add conditional edge
builder.add_edge(
    source="router",
    target="specific_handler",
    condition=lambda data: data.get("priority") == "high"
)

# Add fan-out edges with selection
builder.add_fan_out_edges(
    source="splitter",
    targets=["a", "b", "c"],
    selection_func=lambda data: ["a", "c"] if data.get("flag") else ["b"]
)

# Add fan-in edge (simple)
builder.add_edge(source="handler_a", target="merger")
builder.add_edge(source="handler_b", target="merger")

# Add switch-case group
builder.add_switch_case_edge_group(
    SwitchCaseEdgeGroup(
        source="processor",
        cases=[
            Case(condition=is_error, target="error"),
            Case(condition=is_warning, target="warning"),
        ],
        default="success"
    )
)

# Add multi-selection group
builder.add_multi_selection_edge_group(
    MultiSelectionEdgeGroup(
        source="logger",
        selections=[
            ("file_logger", always_true),
            ("cloud_logger", should_cloud_log),
        ]
    )
)

# Chain executors in sequence
builder.add_chain([
    ("step1", executor1),
    ("step2", executor2),
    ("step3", executor3),
])
```

## Complete Routing Example

```python
from agent_framework import (
    WorkflowBuilder,
    Executor,
    handler,
    WorkflowContext,
    SwitchCaseEdgeGroup,
    Case,
)

# Define executors
class RequestProcessor(Executor):
    @handler
    async def process(self, request: dict, ctx: WorkflowContext[dict]) -> None:
        processed = {"original": request, "processed": True}
        await ctx.send_message(processed)

class ValidatingExecutor(Executor):
    @handler
    async def validate(self, data: dict, ctx: WorkflowContext[dict]) -> None:
        is_valid = data.get("processed") is True
        await ctx.send_message({"valid": is_valid, **data})

def is_valid(data: dict) -> bool:
    return data.get("valid", False)

def is_invalid(data: dict) -> bool:
    return not data.get("valid", True)

class SuccessExecutor(Executor):
    @handler
    async def handle(self, data: dict, ctx: WorkflowContext[dict]) -> None:
        await ctx.send_message({"status": "success", **data})

class ErrorExecutor(Executor):
    @handler
    async def handle(self, data: dict, ctx: WorkflowContext) -> None:
        print(f"Error: {data}")

# Build workflow
processor = RequestProcessor(id="processor")
validator = ValidatingExecutor(id="validator")
success = SuccessExecutor(id="success")
error = ErrorExecutor(id="error")

builder = WorkflowBuilder(start_executor="processor")
builder.add_executor("processor", processor)
builder.add_executor("validator", validator)
builder.add_executor("success", success)
builder.add_executor("error", error)

# Chain first two
builder.add_edge("processor", "validator")

# Conditional routing
builder.add_switch_case_edge_group(
    SwitchCaseEdgeGroup(
        source="validator",
        cases=[
            Case(condition=is_valid, target="success"),
            Case(condition=is_invalid, target="error"),
        ],
        default="error"
    )
)

workflow = builder.build()
```

## Edge Type Comparison

| Pattern | Use Case | Concurrency | Complexity |
|---|---|---|---|
| Simple edge | Linear pipeline | Sequential | Low |
| Conditional edge | Route based on content | Sequential | Low |
| Targeted send_message | Runtime-decided routing | Sequential | Medium |
| Fan-out | Parallel processing | Concurrent (superstep) | Medium |
| Fan-out with selection | Filtered parallel | Concurrent (superstep) | High |
| Fan-in | Merge results | Sequential | Low |
| Switch-case | Multiple conditions | Sequential | Medium |
| Multi-selection | Independent routes | Concurrent | High |
| Chains | Sequential groups | Sequential | Low |

## Key Concepts

**Superstep Execution:** Edges define BSP (Bulk Synchronous Parallel) supersteps. All executors that receive messages in a superstep execute concurrently, then the next superstep begins.

**Condition Functions:** Return bool to decide if edge activates. Pure functions recommended (no side effects).

**Edge Resolution:** Framework resolves all edge destinations at build time, detecting invalid references early.

**Message Type Matching:** Executors must have handlers for message types received. Type mismatch causes runtime error.
