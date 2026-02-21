# Human-in-the-Loop — Approval Gates, Interactive Input, Request Handlers

## Overview

Human-in-the-loop workflows pause execution to request information from a user, wait for a response, and then resume based on that feedback. This enables approval gates, interactive guidance, and human-driven decision-making within automated workflows.

## ctx.request_info() Method

Request information from the user and pause the workflow:

```python
from agent_framework.workflows import WorkflowContext

@handler
async def request_approval(self, data: dict, ctx: WorkflowContext[dict]) -> None:
    await ctx.request_info(
        request_data={
            "type": "approval",
            "message": f"Approve: {data}?",
            "options": ["approve", "reject", "modify"]
        },
        response_type=str  # Expected response type
    )
```

### request_info Parameters

| Parameter | Type | Description |
|---|---|---|
| `request_data` | Any | Payload sent to the user (can be dict, Pydantic model, string) |
| `response_type` | Type | Python type of expected response (str, dict, BaseModel, etc.) |

### Event Structure

When `request_info` is called, the workflow emits a `request_info` event:

```python
{
    "type": "request_info",
    "request_id": "req_12345",  # Unique ID for this request
    "executor_id": "approval_gate",
    "data": {
        "type": "approval",
        "message": "Approve this action?",
        "options": ["approve", "reject"]
    }
}
```

## @response_handler Decorator

Process the user's response after `ctx.request_info()`. The handler receives the original request data and the response:

```python
from agent_framework import response_handler

class ApprovalExecutor(Executor):
    def __init__(self):
        super().__init__(id="approval")

    @handler
    async def request_approval(self, data: dict, ctx: WorkflowContext[dict]) -> None:
        # Send request
        await ctx.request_info(
            request_data={"message": f"Approve {data}?"},
            response_type=str
        )

    @response_handler
    async def on_approval_response(
        self,
        original_request: dict,      # The request_data from ctx.request_info
        response: str,               # The user's response
        ctx: WorkflowContext[dict]   # Workflow context
    ) -> None:
        if response.lower() == "approve":
            await ctx.send_message({"status": "approved", "data": original_request})
        else:
            await ctx.send_message({"status": "rejected", "data": original_request})
```

### Key Rules

- `@response_handler` receives original `request_data` as first parameter
- Response type matches the `response_type` from `ctx.request_info()`
- Only one `@response_handler` per executor (for single request type)
- Handler must match the request/response pairing

## Processing Request Events in run_stream

Handle request_info events and send responses back to the workflow:

### Basic Pattern

```python
async def main():
    workflow = build_workflow()

    # Start workflow
    stream = workflow.run(input_data, stream=True)
    pending_responses = {}

    async for event in stream:
        if event.type == "request_info":
            # Capture request
            request_id = event.request_id
            request_data = event.data
            print(f"Workflow requests: {request_data}")

            # Get user input
            user_response = input("Your response: ")
            pending_responses[request_id] = user_response

        elif event.type == "output":
            print(f"Output: {event.data}")

    # Resume with responses
    if pending_responses:
        async for event in workflow.run(stream=True, responses=pending_responses):
            if event.type == "output":
                print(f"Final: {event.data}")
```

### Multi-Step Human-in-Loop Loop

```python
async def process_with_human_guidance(workflow, initial_input):
    """Run workflow with multiple human feedback points."""
    stream = workflow.run(initial_input, stream=True)
    pending_responses = None

    while True:
        pending_responses = await collect_responses(stream)

        if pending_responses is None:
            # Workflow completed
            break

        # Resume with responses
        stream = workflow.run(stream=True, responses=pending_responses)

async def collect_responses(stream):
    """Collect all pending requests from a workflow event stream."""
    responses = {}

    async for event in stream:
        if event.type == "request_info":
            request_id = event.request_id
            request_data = event.data

            # Format and show request
            if isinstance(request_data, dict):
                prompt = request_data.get("prompt", str(request_data))
            else:
                prompt = str(request_data)

            print(f"\nRequest: {prompt}")
            answer = input("> ").strip()
            responses[request_id] = answer

        elif event.type == "output":
            print(f"Output: {event.data}")

    return responses if responses else None
```

## Approval Gate Executor Pattern

Simple executor that pauses for human approval:

```python
from agent_framework.workflows import Executor, handler, WorkflowContext
from dataclasses import dataclass

@dataclass
class ApprovalRequest:
    """Request sent to human for approval."""
    action: str
    details: str
    requires_approval: bool = True

class ApprovalGate(Executor):
    """Pauses workflow for human approval."""

    def __init__(self, id: str = "approval"):
        super().__init__(id=id)

    @handler
    async def check_approval(self, action_data: dict, ctx: WorkflowContext[dict]) -> None:
        if action_data.get("high_risk", False):
            # Request approval for high-risk actions
            await ctx.request_info(
                request_data=ApprovalRequest(
                    action=action_data.get("action", "Unknown"),
                    details=action_data.get("details", "")
                ),
                response_type=str
            )
        else:
            # Auto-approve low-risk actions
            await ctx.send_message(action_data)

    @response_handler
    async def on_approval(
        self,
        request: ApprovalRequest,
        decision: str,
        ctx: WorkflowContext[dict]
    ) -> None:
        if decision.lower() in ["approve", "yes", "y"]:
            await ctx.send_message({"approved": True, "action": request.action})
        else:
            await ctx.send_message({"approved": False, "action": request.action, "reason": decision})
```

## Interactive Input Executor

Request structured input from user:

```python
from pydantic import BaseModel

class UserInput(BaseModel):
    """Structured user input."""
    field1: str
    field2: int
    field3: bool

class InteractiveStep(Executor):
    """Requests structured input from user."""

    def __init__(self):
        super().__init__(id="input_step")

    @handler
    async def ask_user(self, prompt: str, ctx: WorkflowContext[UserInput]) -> None:
        await ctx.request_info(
            request_data={"prompt": prompt, "schema": "field1: str, field2: int, field3: bool"},
            response_type=UserInput
        )

    @response_handler
    async def process_input(
        self,
        request: dict,
        user_input: UserInput,
        ctx: WorkflowContext[dict]
    ) -> None:
        # Process the structured input
        result = {
            "received": user_input.dict(),
            "processed": True
        }
        await ctx.send_message(result)
```

## Tool Approval Pattern

Request user approval before executing a tool:

```python
from pydantic import BaseModel

class ToolCallApproval(BaseModel):
    """Request approval for tool execution."""
    tool_name: str
    parameters: dict
    description: str

class ApprovalTools(Executor):
    """Requests approval before executing sensitive tools."""

    def __init__(self):
        super().__init__(id="tool_approval")

    @handler
    async def check_tool(self, tool_call: dict, ctx: WorkflowContext[dict]) -> None:
        if self.is_sensitive_tool(tool_call["tool"]):
            # Request approval for sensitive operations
            await ctx.request_info(
                request_data=ToolCallApproval(
                    tool_name=tool_call["tool"],
                    parameters=tool_call["params"],
                    description=f"Execute {tool_call['tool']} with params: {tool_call['params']}"
                ),
                response_type=str
            )
        else:
            # Auto-approve non-sensitive tools
            await ctx.send_message({"approved": True, "tool": tool_call["tool"]})

    @response_handler
    async def on_tool_approval(
        self,
        request: ToolCallApproval,
        decision: str,
        ctx: WorkflowContext[dict]
    ) -> None:
        if decision.lower() == "approve":
            await ctx.send_message({"execute": True, "tool": request.tool_name})
        else:
            await ctx.send_message({"execute": False, "tool": request.tool_name})

    @staticmethod
    def is_sensitive_tool(tool_name: str) -> bool:
        return tool_name in ["delete_file", "execute_code", "send_email"]
```

## Combining Human-in-Loop with Checkpointing

Save workflow state when pausing for human input, resume from checkpoint:

```python
from agent_framework import InMemoryCheckpointStorage, WorkflowBuilder

async def main():
    checkpoint_storage = InMemoryCheckpointStorage()

    # Build workflow with checkpointing
    workflow = (
        WorkflowBuilder(start_executor=my_executor, checkpoint_storage=checkpoint_storage)
        .add_edge(my_executor, approval_gate)
        .build()
    )

    # Initial run
    stream = workflow.run(input_data, stream=True)
    pending_responses = await collect_responses_with_checkpoints(stream, checkpoint_storage)

    if pending_responses is None:
        return  # Workflow completed

    # Checkpoint is automatically saved at pause point
    # Later, can resume from checkpoint
    saved_checkpoint = (await checkpoint_storage.list_checkpoints())[0]

    # Resume with responses
    stream = workflow.run(
        stream=True,
        responses=pending_responses,
        checkpoint_id=saved_checkpoint.checkpoint_id
    )
    await process_stream(stream)

async def collect_responses_with_checkpoints(stream, storage):
    """Collect responses and save checkpoints."""
    responses = {}

    async for event in stream:
        if event.type == "request_info":
            request_id = event.request_id
            prompt = event.data.get("prompt", str(event.data))
            answer = input(f"{prompt}\n> ")
            responses[request_id] = answer

            # List available checkpoints
            checkpoints = await storage.list_checkpoints()
            print(f"Checkpoints available: {len(checkpoints)}")

    return responses if responses else None
```

## Declaration-Only Tools for Client-Side Execution

Define tools that client executes rather than the agent:

```python
from agent_framework import tool
from typing import Annotated

@tool(declaration_only=True)  # Client will execute this
def fetch_user_data(user_id: Annotated[str, "User ID"]) -> str:
    """Fetch user data from database."""
    # This function is declared but not executed by agent
    # Client captures the tool call and executes it
    pass

class ClientSideToolExecutor(Executor):
    def __init__(self):
        super().__init__(id="tool_executor")

    @handler
    async def execute_tool(self, tool_call: dict, ctx: WorkflowContext[dict]) -> None:
        tool_name = tool_call.get("tool")

        if tool_name == "fetch_user_data":
            # Request client to execute
            await ctx.request_info(
                request_data={
                    "type": "tool_execution",
                    "tool": tool_name,
                    "params": tool_call.get("params")
                },
                response_type=dict
            )

    @response_handler
    async def on_tool_result(
        self,
        request: dict,
        result: dict,
        ctx: WorkflowContext[dict]
    ) -> None:
        # Receive result from client-executed tool
        await ctx.send_message(result)
```

## Complex Example: Multi-Step Approval Workflow

```python
from pydantic import BaseModel

class DocumentRequest(BaseModel):
    document_id: str
    title: str
    content: str

class ReviewNotes(BaseModel):
    reviewer_name: str
    feedback: str
    approved: bool

class MultiStepApprovalWorkflow:
    """Workflow: Create → Review → Approve → Publish"""

    @staticmethod
    async def build_workflow(client):
        class CreateExecutor(Executor):
            def __init__(self):
                super().__init__(id="create")

            @handler
            async def create(self, topic: str, ctx: WorkflowContext[DocumentRequest]) -> None:
                # Agent creates document
                doc = DocumentRequest(
                    document_id="doc_123",
                    title=topic,
                    content=f"Content for {topic}"
                )
                await ctx.send_message(doc)

        class ReviewExecutor(Executor):
            def __init__(self):
                super().__init__(id="review")

            @handler
            async def request_review(self, doc: DocumentRequest, ctx: WorkflowContext[DocumentRequest]) -> None:
                await ctx.request_info(
                    request_data={
                        "type": "review",
                        "document": doc.dict(),
                        "prompt": f"Review '{doc.title}' and provide feedback"
                    },
                    response_type=ReviewNotes
                )

            @response_handler
            async def on_review(self, request: dict, notes: ReviewNotes, ctx: WorkflowContext[dict]) -> None:
                await ctx.send_message({
                    "document_id": request["document"]["document_id"],
                    "review": notes.dict()
                })

        class ApproveExecutor(Executor):
            def __init__(self):
                super().__init__(id="approve")

            @handler
            async def request_approval(self, review_result: dict, ctx: WorkflowContext[dict]) -> None:
                if not review_result["review"]["approved"]:
                    # Request changes
                    await ctx.request_info(
                        request_data={
                            "type": "revise",
                            "message": f"Changes needed: {review_result['review']['feedback']}"
                        },
                        response_type=str
                    )
                else:
                    # Approve for publishing
                    await ctx.send_message({"action": "publish", "doc_id": review_result["document_id"]})

            @response_handler
            async def on_approval(self, request: dict, response: str, ctx: WorkflowContext[dict]) -> None:
                await ctx.send_message({"action": "republish", "changes": response})

        create = CreateExecutor()
        review = ReviewExecutor()
        approve = ApproveExecutor()

        return (
            WorkflowBuilder(start_executor=create)
            .add_edge(create, review)
            .add_edge(review, approve)
            .build()
        )
```

## Best Practices

| Practice | Benefit |
|---|---|
| Use Pydantic for request/response types | Type safety and validation |
| Store request context in original_request param | Easier response handling |
| Name @response_handler descriptively | Clarity on purpose |
| Combine with checkpointing | Resume from pause points |
| Validate user input in handler | Prevent invalid workflows |
| Use declaration_only tools for client execution | Secure sensitive operations |
| Collect all requests before resuming | Batch human interactions |
| Provide clear prompts to users | Better decisions |
