# Checkpoints & Resuming — Persistence, Recovery, Durable Workflows

## Overview

Checkpoints capture the complete state of a workflow at superstep boundaries (when all executors in a stage complete). This enables resuming workflows from saved points, implementing recovery logic, and creating durable workflows that persist across system failures.

## When Checkpoints Are Created

Checkpoints are automatically created at the end of each superstep after all executors in that stage complete execution. A checkpoint captures:

- Current state of all executors
- All pending messages for the next superstep
- Pending requests and responses (human-in-loop)
- All shared workflow state (set_state values)

```
Initial Input
    ↓
┌─────────────────┐
│   Superstep 1   │ ← Checkpoint 1 created here
│  Executor A, B  │
└────────┬────────┘
         ↓
┌─────────────────┐
│   Superstep 2   │ ← Checkpoint 2 created here
│   Executor C    │
└────────┬────────┘
         ↓
┌─────────────────┐
│   Superstep 3   │ ← Checkpoint 3 created here
│  Executor D, E  │
└─────────────────┘
```

## InMemoryCheckpointStorage

Manage checkpoints in memory (loses checkpoints if process exits):

```python
from agent_framework import InMemoryCheckpointStorage, WorkflowBuilder

# Create storage
checkpoint_storage = InMemoryCheckpointStorage()

# Build workflow with checkpointing enabled
executor_a = MyExecutor("a")
executor_b = MyExecutor("b")

workflow = (
    WorkflowBuilder(
        start_executor=executor_a,
        checkpoint_storage=checkpoint_storage  # Enable checkpointing
    )
    .add_edge(executor_a, executor_b)
    .build()
)

# Run workflow
async for event in workflow.run_stream(input_data):
    # Handle events
    if event.type == "output":
        print(event.data)

# Access saved checkpoints
checkpoints = await checkpoint_storage.list_checkpoints()
print(f"Checkpoints: {len(checkpoints)}")
for checkpoint in checkpoints:
    print(f"  - {checkpoint.checkpoint_id}")
```

### Checkpoint Info Structure

```python
checkpoint: CheckpointInfo
# checkpoint.checkpoint_id      # str - Unique identifier
# checkpoint.superstep_id       # int - Which superstep this checkpoint is from
# checkpoint.created_at         # datetime - When checkpoint was saved
# checkpoint.workflow_state     # dict - Serialized workflow state
```

## FileCheckpointStore (Durable)

Store checkpoints to disk for durability across process restarts:

```python
from agent_framework import FileCheckpointStore, WorkflowBuilder
import os

# Create file-based storage
checkpoint_dir = "/tmp/workflow_checkpoints"
os.makedirs(checkpoint_dir, exist_ok=True)

checkpoint_storage = FileCheckpointStore(checkpoint_dir)

# Build workflow
workflow = (
    WorkflowBuilder(
        start_executor=executor_a,
        checkpoint_storage=checkpoint_storage
    )
    .add_edge(executor_a, executor_b)
    .build()
)

# Run - checkpoints are persisted to disk
async for event in workflow.run_stream(input_data):
    if event.type == "output":
        print(event.data)

# Checkpoints survive process restart
checkpoints = await checkpoint_storage.list_checkpoints()
```

## Building Workflows with Checkpointing

Pass `checkpoint_storage` to WorkflowBuilder:

```python
from agent_framework import WorkflowBuilder, InMemoryCheckpointStorage

# Option 1: In-memory checkpoints
storage = InMemoryCheckpointStorage()
workflow = (
    WorkflowBuilder(
        start_executor=start,
        checkpoint_storage=storage
    )
    .add_edge(start, middle)
    .add_edge(middle, end)
    .build()
)

# Option 2: File-based checkpoints
from agent_framework import FileCheckpointStore
storage = FileCheckpointStore("/var/checkpoints")
workflow = (
    WorkflowBuilder(
        start_executor=start,
        checkpoint_storage=storage
    )
    .add_edge(start, middle)
    .build()
)
```

## Listing Checkpoints

Retrieve all checkpoints from storage:

```python
checkpoints = await checkpoint_storage.list_checkpoints()

for checkpoint in checkpoints:
    print(f"ID: {checkpoint.checkpoint_id}")
    print(f"  Superstep: {checkpoint.superstep_id}")
    print(f"  Created: {checkpoint.created_at}")
    print(f"  State keys: {list(checkpoint.workflow_state.keys())}")
```

## Resuming from Checkpoint (Same Run Instance)

Resume a workflow from a saved checkpoint on the same workflow instance:

```python
# Initial run
async for event in workflow.run_stream(input_data):
    if event.type == "output":
        print(event.data)

# Get checkpoints
checkpoints = await checkpoint_storage.list_checkpoints()

# Resume from checkpoint 2
if len(checkpoints) >= 2:
    saved_checkpoint = checkpoints[1]

    # Resume on same workflow instance
    async for event in workflow.run_stream(checkpoint_id=saved_checkpoint.checkpoint_id):
        if event.type == "output":
            print(f"Resumed: {event.data}")
```

## Rehydrating into New Workflow Instance

Load a checkpoint into a different workflow instance:

```python
# Original workflow
workflow1 = (
    WorkflowBuilder(start_executor=executor_a)
    .add_edge(executor_a, executor_b)
    .build()
)

# Run and get checkpoints
async for event in workflow1.run_stream(input_data):
    pass

checkpoints = await checkpoint_storage.list_checkpoints()

# Create new workflow (doesn't need checkpointing enabled)
workflow2 = (
    WorkflowBuilder(start_executor=executor_a)
    .add_edge(executor_a, executor_b)
    .build()
)

# Rehydrate from checkpoint
if checkpoints:
    saved_checkpoint = checkpoints[0]

    async for event in workflow2.run_stream(
        checkpoint_id=saved_checkpoint.checkpoint_id,
        checkpoint_storage=checkpoint_storage
    ):
        if event.type == "output":
            print(f"Rehydrated: {event.data}")
```

## Combining Checkpoints with Human-in-Loop

Checkpoints are captured at pause points in human-in-loop workflows:

```python
from agent_framework import InMemoryCheckpointStorage, WorkflowBuilder

class ApprovalGate(Executor):
    def __init__(self):
        super().__init__(id="approval")

    @handler
    async def request_approval(self, data: dict, ctx: WorkflowContext[dict]) -> None:
        # This request causes workflow to pause
        await ctx.request_info(
            request_data={"message": f"Approve {data}?"},
            response_type=str
        )

    @response_handler
    async def on_approval(self, request: dict, response: str, ctx: WorkflowContext[dict]) -> None:
        if response.lower() == "approve":
            await ctx.send_message({"status": "approved"})
        else:
            await ctx.send_message({"status": "rejected"})

# Workflow with checkpointing
checkpoint_storage = InMemoryCheckpointStorage()
workflow = (
    WorkflowBuilder(start_executor=step1, checkpoint_storage=checkpoint_storage)
    .add_edge(step1, ApprovalGate())
    .build()
)

# Process with human-in-loop
stream = workflow.run(input_data, stream=True)
pending_responses = {}

async for event in stream:
    if event.type == "request_info":
        # Checkpoint automatically created at pause point
        request_id = event.request_id
        user_response = input(f"{event.data['message']}\n> ")
        pending_responses[request_id] = user_response

    elif event.type == "output":
        print(event.data)

# Checkpoint saved at pause point; can later resume
if pending_responses:
    # Get checkpoint from before approval step
    checkpoints = await checkpoint_storage.list_checkpoints()
    if checkpoints:
        print(f"Can resume from: {checkpoints[-1].checkpoint_id}")

    # Resume with responses
    stream = workflow.run(stream=True, responses=pending_responses)
    async for event in stream:
        if event.type == "output":
            print(event.data)
```

## Executor Lifecycle Hooks for Checkpointing

Executors can hook into checkpoint events for custom behavior:

```python
from agent_framework.workflows import Executor, handler, WorkflowContext

class CheckpointAwareExecutor(Executor):
    def __init__(self):
        super().__init__(id="checkpoint_aware")
        self.state = {}

    @handler
    async def process(self, data: str, ctx: WorkflowContext[str]) -> None:
        # Custom state
        self.state["last_input"] = data
        await ctx.send_message(data)

    async def on_checkpoint_save(self):
        """Called when checkpoint is being saved."""
        print(f"Saving checkpoint with state: {self.state}")
        # Can perform cleanup or finalization
        return self.state

    async def on_checkpoint_restore(self, state):
        """Called when resuming from checkpoint."""
        print(f"Restoring checkpoint state: {state}")
        self.state = state
```

## Sub-Workflow Checkpointing

Nested workflows also checkpoint at their supersteps:

```python
class SubWorkflowExecutor(Executor):
    def __init__(self, sub_workflow):
        super().__init__(id="subwf")
        self.sub_workflow = sub_workflow

    @handler
    async def execute(self, data: str, ctx: WorkflowContext[str]) -> None:
        # Sub-workflow checkpoints are independent
        results = []
        async for event in self.sub_workflow.run_stream(data):
            if event.type == "output":
                results.append(event.data)

        await ctx.send_message(results)

# Create sub-workflow with own checkpointing
sub_checkpoint_storage = InMemoryCheckpointStorage()
sub_workflow = (
    WorkflowBuilder(start_executor=executor_x, checkpoint_storage=sub_checkpoint_storage)
    .add_edge(executor_x, executor_y)
    .build()
)

# Main workflow also has checkpointing
main_checkpoint_storage = InMemoryCheckpointStorage()
main_workflow = (
    WorkflowBuilder(
        start_executor=SubWorkflowExecutor(sub_workflow),
        checkpoint_storage=main_checkpoint_storage
    )
    .build()
)

# Both workflows checkpoint independently
async for event in main_workflow.run_stream(input_data):
    pass

main_checkpoints = await main_checkpoint_storage.list_checkpoints()
sub_checkpoints = await sub_checkpoint_storage.list_checkpoints()
```

## Recovery Pattern: Automatic Retry from Checkpoint

```python
from typing import Optional

class ResilientWorkflowRunner:
    """Automatically retry workflows from last checkpoint on failure."""

    def __init__(self, workflow, checkpoint_storage):
        self.workflow = workflow
        self.checkpoint_storage = checkpoint_storage
        self.max_retries = 3

    async def run_with_recovery(self, input_data):
        """Run workflow with automatic checkpoint recovery."""
        attempt = 0

        while attempt < self.max_retries:
            try:
                print(f"Run attempt {attempt + 1}")
                async for event in self.workflow.run_stream(input_data):
                    if event.type == "output":
                        yield event

                # Success
                return

            except Exception as e:
                attempt += 1
                print(f"Error on attempt {attempt}: {e}")

                if attempt < self.max_retries:
                    # Get last checkpoint and resume
                    checkpoints = await self.checkpoint_storage.list_checkpoints()
                    if checkpoints:
                        last_checkpoint = checkpoints[-1]
                        print(f"Resuming from checkpoint {last_checkpoint.checkpoint_id}")

                        # Resume from checkpoint
                        async for event in self.workflow.run_stream(
                            checkpoint_id=last_checkpoint.checkpoint_id
                        ):
                            if event.type == "output":
                                yield event
                        return

                    else:
                        # No checkpoint, retry from start
                        print("No checkpoint, retrying from start")
                        continue

                else:
                    raise Exception(f"Failed after {self.max_retries} attempts") from e

# Usage
checkpoint_storage = InMemoryCheckpointStorage()
workflow = build_workflow(checkpoint_storage)
runner = ResilientWorkflowRunner(workflow, checkpoint_storage)

async for event in runner.run_with_recovery(input_data):
    print(event)
```

## Durable Workflows with Azure Storage

Store checkpoints in Azure Blob Storage for enterprise durability:

```python
from azure.storage.blob.aio import BlobClient
import json

class AzureCheckpointStore:
    """Store checkpoints in Azure Blob Storage."""

    def __init__(self, connection_string: str, container_name: str):
        self.connection_string = connection_string
        self.container_name = container_name

    async def save_checkpoint(self, checkpoint_id: str, state: dict):
        blob = BlobClient.from_connection_string(
            self.connection_string,
            container_name=self.container_name,
            blob_name=f"checkpoints/{checkpoint_id}.json"
        )
        async with blob:
            await blob.upload_blob(json.dumps(state), overwrite=True)

    async def load_checkpoint(self, checkpoint_id: str) -> Optional[dict]:
        blob = BlobClient.from_connection_string(
            self.connection_string,
            container_name=self.container_name,
            blob_name=f"checkpoints/{checkpoint_id}.json"
        )
        async with blob:
            try:
                data = await blob.download_blob()
                return json.loads(await data.readall())
            except Exception:
                return None

    async def list_checkpoints(self):
        """List all checkpoint IDs."""
        container = ContainerClient.from_connection_string(
            self.connection_string,
            container_name=self.container_name
        )
        checkpoints = []
        async with container:
            async for blob in container.list_blobs(name_starts_with="checkpoints/"):
                checkpoint_id = blob.name.replace("checkpoints/", "").replace(".json", "")
                checkpoints.append(checkpoint_id)
        return checkpoints

# Usage
from agent_framework import WorkflowBuilder

azure_store = AzureCheckpointStore(
    connection_string=os.environ["AZURE_STORAGE_CONNECTION_STRING"],
    container_name="workflow-checkpoints"
)

# Wrap in CheckpointStorage interface for compatibility
workflow = (
    WorkflowBuilder(start_executor=executor_a)
    # Note: FileCheckpointStore is built-in; custom stores require adapter
    .build()
)

# Manual checkpoint management
async for event in workflow.run_stream(input_data):
    pass

# Save final state
checkpoints = await storage.list_checkpoints()
if checkpoints:
    final = checkpoints[-1]
    await azure_store.save_checkpoint(final.checkpoint_id, final.workflow_state)
```

## Checkpoint Inspection

Access checkpoint data for analysis:

```python
async def inspect_checkpoints(checkpoint_storage):
    """Inspect all checkpoints for debugging."""
    checkpoints = await checkpoint_storage.list_checkpoints()

    for i, checkpoint in enumerate(checkpoints):
        print(f"\n=== Checkpoint {i + 1} ===")
        print(f"ID: {checkpoint.checkpoint_id}")
        print(f"Superstep: {checkpoint.superstep_id}")
        print(f"Created: {checkpoint.created_at}")
        print(f"State keys: {list(checkpoint.workflow_state.keys())}")

        # Inspect executor states
        for key, value in checkpoint.workflow_state.items():
            if key.startswith("executor_"):
                print(f"  {key}: {value}")

        # Inspect pending messages
        if "pending_messages" in checkpoint.workflow_state:
            msgs = checkpoint.workflow_state["pending_messages"]
            print(f"  Pending messages: {len(msgs)}")

        # Inspect human-in-loop requests
        if "pending_requests" in checkpoint.workflow_state:
            reqs = checkpoint.workflow_state["pending_requests"]
            print(f"  Pending requests: {len(reqs)}")
```

## Best Practices

| Practice | Benefit |
|---|---|
| Use FileCheckpointStore in production | Survives process failures |
| Checkpoint at human-in-loop points | Easy resume after user approval |
| Combine with retry logic | Automatic recovery from transient errors |
| Limit checkpoint history | Prevent unbounded disk usage |
| Version checkpoint format | Handle upgrades cleanly |
| Test checkpoint resume path | Ensure recovery actually works |
| Monitor checkpoint size | Detect state explosion |
| Store metadata separately | Track checkpoint provenance |

## Common Issues

| Problem | Solution |
|---|---|
| Checkpoint size grows unbounded | Implement state cleanup in executors |
| Resume doesn't continue from where paused | Ensure responses dict matches request_ids |
| Lost checkpoints on process crash | Use FileCheckpointStore, not InMemory |
| Executor state not in checkpoint | Use ctx.set_state, not self.var |
| Can't resume different workflow | Use rehydrate pattern with same executor instances |
