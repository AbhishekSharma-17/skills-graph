# Workflows Advanced — Human-in-Loop, State, Checkpointing, Declarative, Observability

## Human-in-the-Loop

Workflows can pause for human approval or input using `request_info` events.

### Request Pattern

```python
from agent_framework.workflows import Executor, handler, WorkflowContext

class ApprovalGate(Executor):
    """Pauses workflow for human approval."""

    def __init__(self):
        super().__init__(id="approval")

    @handler
    async def request_approval(self, data: dict, ctx: WorkflowContext[dict]) -> None:
        # Send request for human input
        await ctx.request_info({
            "type": "approval",
            "message": f"Approve this action? Data: {data}",
            "options": ["approve", "reject", "modify"],
        })

        # After human responds, continue
        await ctx.send_message(data)
```

### Processing Human Input

```python
async for event in workflow.run_stream(input_data):
    if event.type == "request_info":
        # Show request to user
        print(f"Request: {event.data}")
        user_response = input("Your response: ")

        # Send response back
        responses = {event.request_id: user_response}
        # Continue workflow with responses
        async for next_event in workflow.run(responses=responses):
            process_event(next_event)

    elif event.type == "output":
        print(f"Output: {event.data}")
```

## State Management

### Executor State

Executors can maintain internal state across invocations:

```python
class StatefulCounter(Executor):
    def __init__(self):
        super().__init__(id="counter")
        self.count = 0

    @handler
    async def increment(self, data: str, ctx: WorkflowContext[str]) -> None:
        self.count += 1
        await ctx.send_message({"data": data, "count": self.count})
```

### Passing State Through Context

```python
class StateAwareExecutor(Executor):
    def __init__(self):
        super().__init__(id="state_aware")

    @handler
    async def process(self, data: dict, ctx: WorkflowContext[dict]) -> None:
        # Accumulate state in the data dict
        data["processed_by"] = data.get("processed_by", [])
        data["processed_by"].append(self.id)
        data["timestamp"] = datetime.utcnow().isoformat()
        await ctx.send_message(data)
```

## Checkpointing & Resuming

### Checkpoint Pattern

```python
class CheckpointedPipeline(Executor):
    def __init__(self, checkpoint_store):
        super().__init__(id="pipeline")
        self.store = checkpoint_store

    @handler
    async def process(self, data: dict, ctx: WorkflowContext[dict]) -> None:
        # Step 1
        result1 = await self.step1(data)
        await self.store.save("step1", result1)

        # Step 2 — can resume from here if step 1 already done
        result2 = await self.step2(result1)
        await self.store.save("step2", result2)

        await ctx.send_message(result2)

    async def resume_from(self, checkpoint: str, ctx: WorkflowContext[dict]) -> None:
        """Resume from a saved checkpoint."""
        saved_data = await self.store.load(checkpoint)
        if checkpoint == "step1":
            result2 = await self.step2(saved_data)
            await ctx.send_message(result2)
```

### Simple Checkpoint Store

```python
import json
from pathlib import Path

class FileCheckpointStore:
    def __init__(self, directory: str = "./checkpoints"):
        self.dir = Path(directory)
        self.dir.mkdir(exist_ok=True)

    async def save(self, name: str, data: dict):
        (self.dir / f"{name}.json").write_text(json.dumps(data))

    async def load(self, name: str) -> dict:
        return json.loads((self.dir / f"{name}.json").read_text())

    async def exists(self, name: str) -> bool:
        return (self.dir / f"{name}.json").exists()
```

## Declarative Workflows

Define workflows using configuration instead of code:

### YAML Definition

```yaml
# workflow.yaml
name: content_pipeline
entry: clean
exit: format

nodes:
  clean:
    executor: text_cleaner
    connects_to: [analyze]
  analyze:
    executor: text_analyzer
    connects_to: [format]
  format:
    executor: output_formatter
```

### Load from YAML

```python
import yaml
from agent_framework.workflows import Workflow

def load_workflow(config_path: str, executor_registry: dict) -> Workflow:
    """Load workflow from YAML config."""
    with open(config_path) as f:
        config = yaml.safe_load(f)

    wf = Workflow()

    # Add nodes
    for name, node_config in config["nodes"].items():
        executor = executor_registry[node_config["executor"]]
        wf.add_node(name, executor)

    # Connect edges
    for name, node_config in config["nodes"].items():
        for target in node_config.get("connects_to", []):
            wf.connect(name, target)

    wf.set_entry_node(config["entry"])
    wf.set_exit_node(config["exit"])

    return wf

# Usage
registry = {
    "text_cleaner": TextCleaner(),
    "text_analyzer": TextAnalyzer(),
    "output_formatter": OutputFormatter(),
}
workflow = load_workflow("workflow.yaml", registry)
```

## Observability in Workflows

### Logging Executor Wrapper

```python
import time
import logging

logger = logging.getLogger("workflow")

class ObservableExecutor(Executor):
    """Wrapper that adds logging/timing to any executor."""

    def __init__(self, wrapped: Executor):
        super().__init__(id=f"observable_{wrapped.id}")
        self.wrapped = wrapped

    @handler
    async def process(self, data, ctx: WorkflowContext) -> None:
        start = time.perf_counter()
        logger.info(f"[{self.wrapped.id}] Starting with input type: {type(data).__name__}")

        try:
            await self.wrapped.run(data, ctx)
            elapsed = time.perf_counter() - start
            logger.info(f"[{self.wrapped.id}] Completed in {elapsed:.2f}s")
        except Exception as e:
            elapsed = time.perf_counter() - start
            logger.error(f"[{self.wrapped.id}] Failed after {elapsed:.2f}s: {e}")
            raise
```

### Event-Based Monitoring

```python
async def run_with_monitoring(workflow, input_data):
    """Run workflow with full event monitoring."""
    events_log = []

    async for event in workflow.run_stream(input_data):
        events_log.append({
            "type": event.type,
            "executor": getattr(event, "executor_id", None),
            "timestamp": datetime.utcnow().isoformat(),
            "data_type": type(event.data).__name__,
        })

        if event.type == "output":
            print(f"[{event.executor_id}] Output: {event.data}")
        elif event.type == "error":
            print(f"[{event.executor_id}] ERROR: {event.data}")

    # Save execution log
    with open("workflow_execution.json", "w") as f:
        json.dump(events_log, f, indent=2)

    return events_log
```

## Workflow Visualization

Generate a visual representation of the workflow graph:

```python
def visualize_workflow(workflow) -> str:
    """Generate Mermaid diagram of workflow."""
    lines = ["graph LR"]
    for node_name in workflow.nodes:
        lines.append(f"    {node_name}[{node_name}]")
    for edge in workflow.edges:
        lines.append(f"    {edge.source} --> {edge.target}")
    # Mark entry/exit
    lines.append(f"    style {workflow.entry_node} fill:#4CAF50")
    lines.append(f"    style {workflow.exit_node} fill:#FF5722")
    return "\n".join(lines)

# Output:
# graph LR
#     clean[clean]
#     analyze[analyze]
#     format[format]
#     clean --> analyze
#     analyze --> format
#     style clean fill:#4CAF50
#     style format fill:#FF5722
```

## Error Handling in Workflows

```python
class ResilientExecutor(Executor):
    """Executor with retry logic."""

    def __init__(self, wrapped, max_retries=3):
        super().__init__(id=f"resilient_{wrapped.id}")
        self.wrapped = wrapped
        self.max_retries = max_retries

    @handler
    async def process(self, data, ctx: WorkflowContext) -> None:
        for attempt in range(self.max_retries):
            try:
                await self.wrapped.run(data, ctx)
                return
            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"Retry {attempt+1}: {e}")
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise
```

## Workflow Composition — Nested Workflows

```python
class SubWorkflowExecutor(Executor):
    """Run a sub-workflow as a single node in a parent workflow."""

    def __init__(self, sub_workflow, id: str):
        super().__init__(id=id)
        self.sub_workflow = sub_workflow

    @handler
    async def process(self, data, ctx: WorkflowContext) -> None:
        events = await self.sub_workflow.run(data)
        result = events.get_outputs()
        await ctx.send_message(result)

# Compose: parent workflow contains a sub-workflow as a node
parent = Workflow()
parent.add_node("preprocess", preprocessor)
parent.add_node("pipeline", SubWorkflowExecutor(child_workflow, "pipeline"))
parent.add_node("postprocess", postprocessor)
parent.connect("preprocess", "pipeline")
parent.connect("pipeline", "postprocess")
```
