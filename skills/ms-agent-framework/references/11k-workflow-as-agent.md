# Workflows as Agents — Composability, Wrapping, Reuse

## Overview

Workflows can be wrapped to behave like agents, enabling composition, reuse, and integration with orchestration systems. A workflow becomes an agent by wrapping it in an agent interface that maintains conversation state and handles tool binding.

## WorkflowAgent Wrapper Pattern

### Basic Pattern

```python
from agent_framework import Agent
from agent_framework.workflows import Workflow, WorkflowExecutor

# Define workflow
workflow = Workflow()
workflow.add_node("step1", executor1)
workflow.add_node("step2", executor2)
workflow.connect("step1", "step2")
workflow.set_entry_node("step1")
workflow.set_exit_node("step2")

# Wrap as agent
class WorkflowAgent(Agent):
    """Wraps a workflow to behave like an agent."""

    def __init__(self, workflow: Workflow, client, **kwargs):
        self.workflow = workflow
        self.client = client
        # Initialize agent properties
        super().__init__(name="WorkflowAgent", instructions="Execute workflow", **kwargs)

    async def run(self, input_data: str, **kwargs):
        """Run workflow as agent."""
        result = await self.workflow.run(input_data)
        return result.get_outputs()

# Usage
agent = WorkflowAgent(workflow, client)
response = await agent.run("Process this data")
```

## workflow.as_agent() Built-In Method

Simple helper to convert workflow to agent:

```python
from agent_framework.workflows import Workflow

# Build workflow
workflow = Workflow()
workflow.add_node("process", processor)
workflow.add_node("format", formatter)
workflow.connect("process", "format")
workflow.set_entry_node("process")
workflow.set_exit_node("format")

# Convert to agent
agent = workflow.as_agent(
    name="DataProcessor",
    instructions="Process and format data",
    client=client,
)

# Use as normal agent
result = await agent.run("input data")

# Can be used in orchestrations
from agent_framework import Orchestration

orchestrator = Orchestration()
orchestrator.add_agent("workflow_agent", agent)
await orchestrator.run("route to workflow_agent with input")
```

### API Signature

```python
def as_agent(
    self,
    name: str,
    instructions: str,
    client,
    tools: List = None,
    options: Dict = None,
    **kwargs
) -> Agent:
    """
    Convert workflow to agent.

    Args:
        name: Agent name
        instructions: Agent system prompt/instructions
        client: LLM client
        tools: Optional list of tools to bind
        options: LLM options (temperature, max_tokens, etc.)
        **kwargs: Additional agent configuration

    Returns:
        Agent instance wrapping this workflow
    """
```

## Using Workflow-Agent in Orchestrations

Integrate workflow agents into multi-agent systems:

```python
from agent_framework import Orchestration, Agent
from agent_framework.workflows import Workflow

# Create workflows
research_workflow = create_research_workflow()
review_workflow = create_review_workflow()

# Convert to agents
researcher = research_workflow.as_agent(
    name="Researcher",
    instructions="Conduct thorough research on topics",
    client=client,
)

reviewer = review_workflow.as_agent(
    name="Reviewer",
    instructions="Review and critique research",
    client=client,
)

# Create orchestration
orchestration = Orchestration()
orchestration.add_agent("researcher", researcher)
orchestration.add_agent("reviewer", reviewer)

# Define routing
async def route_request(message: str, agents: dict):
    """Route to appropriate workflow-agent."""
    if "review" in message.lower():
        return await agents["reviewer"].run(message)
    else:
        return await agents["researcher"].run(message)

# Use in handoff pattern
response = await route_request("Please research AI trends", {
    "researcher": researcher,
    "reviewer": reviewer,
})
```

## Workflow-Agent with Sessions for Conversation History

Maintain conversation state in workflow agents:

```python
from agent_framework import Session, Agent
from agent_framework.workflows import Workflow

# Create workflow
workflow = Workflow()
# ... add nodes ...

# Create agent from workflow
agent = workflow.as_agent(
    name="Assistant",
    instructions="Help users with questions",
    client=client,
)

# Create session for conversation history
session = Session(agent_id="assistant")

# Multiple turns in conversation
response1 = await agent.run("What is AI?", session=session)
response2 = await agent.run("Explain neural networks", session=session)
# Session maintains context from previous messages

# Access conversation history
history = await session.get_messages()
for msg in history:
    print(f"{msg.role}: {msg.content}")
```

### Persistent Session with State

```python
from agent_framework import Session

class PersistentWorkflowAgent:
    """Workflow agent with persistent conversation state."""

    def __init__(self, workflow: Workflow, client, session_id: str):
        self.agent = workflow.as_agent(
            name="PersistentAgent",
            instructions="Maintain conversation state",
            client=client,
        )
        self.session = Session(agent_id=session_id)

    async def process_message(self, message: str) -> str:
        """Process message in session context."""
        response = await self.agent.run(message, session=self.session)
        return response

    async def get_history(self):
        """Get conversation history."""
        return await self.session.get_messages()

    async def clear_history(self):
        """Clear session state."""
        await self.session.clear()

# Usage
persistent_agent = PersistentWorkflowAgent(workflow, client, "user_123")
await persistent_agent.process_message("What's the weather?")
await persistent_agent.process_message("What about tomorrow?")  # Remembers context
```

## Workflow-Agent with Human-in-Loop

Pause workflow agents for human approval:

```python
from agent_framework.workflows import handler, WorkflowContext

class HumanApprovalExecutor(Executor):
    """Request human approval in workflow."""

    def __init__(self):
        super().__init__(id="approval")

    @handler
    async def request_approval(self, data: dict, ctx: WorkflowContext[dict]) -> None:
        # Request human input
        await ctx.request_info({
            "type": "approval",
            "message": f"Approve action: {data}",
            "options": ["approve", "reject", "modify"],
        })

        # Continue after response
        await ctx.send_message(data)

# Build workflow with approval
workflow = Workflow()
workflow.add_node("process", processor)
workflow.add_node("approval", HumanApprovalExecutor())
workflow.add_node("execute", executor)
workflow.connect("process", "approval")
workflow.connect("approval", "execute")

# Convert to agent
agent = workflow.as_agent(
    name="ApprovalAgent",
    instructions="Execute with human approval",
    client=client,
)

# Use with human-in-loop
async def run_with_approval(agent, input_data):
    """Run agent with human approval handling."""
    async for event in agent.run_stream(input_data):
        if event.type == "request_info":
            print(f"Approval needed: {event.data}")
            user_response = input("Your response: ")
            # Continue with response
            async for result_event in agent.run(responses={event.request_id: user_response}):
                print(result_event.data)
        elif event.type == "output":
            print(f"Result: {event.data}")
```

## Workflow-Agent with Checkpointing

Resume workflow agents from checkpoints:

```python
from agent_framework.workflows import Workflow
import json
from pathlib import Path

class CheckpointedWorkflowAgent:
    """Workflow agent with checkpoint/resume capability."""

    def __init__(self, workflow: Workflow, client, checkpoint_dir: str = "./checkpoints"):
        self.agent = workflow.as_agent(
            name="CheckpointedAgent",
            instructions="Support checkpointing",
            client=client,
        )
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)

    async def run_with_checkpoint(self, session_id: str, input_data: str):
        """Run agent with checkpoint saving."""
        checkpoint_file = self.checkpoint_dir / f"{session_id}.json"

        # Check for existing checkpoint
        if checkpoint_file.exists():
            with open(checkpoint_file) as f:
                checkpoint = json.load(f)
                # Resume from checkpoint
                result = await self._resume_from_checkpoint(checkpoint, input_data)
        else:
            # Start fresh
            result = await self.agent.run(input_data)
            # Save checkpoint
            await self._save_checkpoint(session_id, result)

        return result

    async def _save_checkpoint(self, session_id: str, state: dict):
        """Save execution state as checkpoint."""
        checkpoint_file = self.checkpoint_dir / f"{session_id}.json"
        with open(checkpoint_file, "w") as f:
            json.dump({"state": state, "timestamp": datetime.utcnow().isoformat()}, f)

    async def _resume_from_checkpoint(self, checkpoint: dict, new_input: str):
        """Resume from saved checkpoint."""
        # Reconstruct state and continue
        return await self.agent.run(new_input)

# Usage
checkpointed_agent = CheckpointedWorkflowAgent(workflow, client)
result = await checkpointed_agent.run_with_checkpoint("session_123", "process data")
```

## Workflow-Agent with kwargs for Custom Context

Pass custom context to workflow agents:

```python
from agent_framework.workflows import Workflow, WorkflowContext

class ContextAwareExecutor(Executor):
    """Executor that uses workflow context."""

    def __init__(self):
        super().__init__(id="context_aware")

    @handler
    async def process(self, data: str, ctx: WorkflowContext[str]) -> None:
        # Access custom context
        user_id = getattr(ctx, "user_id", None)
        auth_level = getattr(ctx, "auth_level", None)

        result = f"User {user_id} ({auth_level}): {data}"
        await ctx.send_message(result)

# Create workflow
workflow = Workflow()
workflow.add_node("context_node", ContextAwareExecutor())

# Convert to agent with custom kwargs
agent = workflow.as_agent(
    name="ContextAgent",
    instructions="Use provided context",
    client=client,
    user_id="user_123",  # Custom context
    auth_level="admin",
)

# Run with kwargs
result = await agent.run(
    "process request",
    user_id="user_456",  # Override at runtime
    auth_level="user",
)
```

### Custom Context Passing

```python
from typing import Dict, Any

class CustomContextWorkflowAgent:
    """Workflow agent with custom context support."""

    def __init__(self, workflow: Workflow, client):
        self.workflow = workflow
        self.agent = workflow.as_agent(
            name="CustomContextAgent",
            instructions="Accept custom context",
            client=client,
        )

    async def run_with_context(self, input_data: str, context: Dict[str, Any]) -> Any:
        """Run with custom context."""
        # Inject context into workflow
        return await self.workflow.run(
            input_data,
            context=context,  # Pass to executors
        )

# Usage
agent = CustomContextWorkflowAgent(workflow, client)
result = await agent.run_with_context(
    "process data",
    context={
        "user_id": "user_123",
        "organization_id": "org_456",
        "permissions": ["read", "write"],
        "metadata": {"source": "api"},
    }
)
```

## Reflection Pattern: Agent → Critic → Agent Loop as Workflow Exposed as Agent

Create self-improving agent with reflection:

```python
from agent_framework import Agent
from agent_framework.workflows import Workflow, Executor, handler, WorkflowContext

# Agent that generates content
class GeneratorExecutor(Executor):
    """Generate initial response."""

    def __init__(self, client):
        super().__init__(id="generator")
        self.client = client

    @handler
    async def generate(self, prompt: str, ctx: WorkflowContext[str]) -> None:
        response = await self.client.complete_async(
            f"Generate response for: {prompt}"
        )
        await ctx.send_message({"content": response.text, "iteration": 1})

# Critic that evaluates
class CriticExecutor(Executor):
    """Evaluate and critique response."""

    def __init__(self, client):
        super().__init__(id="critic")
        self.client = client

    @handler
    async def critique(self, data: dict, ctx: WorkflowContext[dict]) -> None:
        critique = await self.client.complete_async(
            f"Critique this: {data['content']}"
        )

        data["critique"] = critique.text

        # Route based on quality
        if "needs improvement" in critique.text.lower():
            await ctx.send_message(data, target="generator_v2")
        else:
            await ctx.send_message(data, target="finalizer")

# Improved generator
class ImprovedGeneratorExecutor(Executor):
    """Generate improved response based on critique."""

    def __init__(self, client):
        super().__init__(id="generator_v2")
        self.client = client

    @handler
    async def generate_improved(self, data: dict, ctx: WorkflowContext[dict]) -> None:
        if data["iteration"] >= 3:
            # Max iterations reached
            await ctx.send_message(data, target="finalizer")
            return

        improved = await self.client.complete_async(
            f"Improve: {data['content']}\nFeedback: {data['critique']}"
        )

        data["content"] = improved.text
        data["iteration"] += 1
        await ctx.send_message(data, target="critic")

# Finalizer
@executor(id="finalizer")
async def finalize(data: dict, ctx: WorkflowContext[Never, str]) -> None:
    await ctx.yield_output(data["content"])

# Build reflection workflow
reflection_workflow = Workflow()
reflection_workflow.add_node("generator", GeneratorExecutor(client))
reflection_workflow.add_node("critic", CriticExecutor(client))
reflection_workflow.add_node("generator_v2", ImprovedGeneratorExecutor(client))
reflection_workflow.add_node("finalizer", finalize)

reflection_workflow.connect("generator", "critic")
reflection_workflow.connect("critic", "generator_v2")
reflection_workflow.connect("critic", "finalizer")
reflection_workflow.connect("generator_v2", "critic")

reflection_workflow.set_entry_node("generator")
reflection_workflow.set_exit_node("finalizer")

# Expose as agent
reflection_agent = reflection_workflow.as_agent(
    name="ReflectionAgent",
    instructions="Generate and improve responses through self-reflection",
    client=client,
)

# Use
result = await reflection_agent.run("Write a poem about AI")
```

## Nested Workflows as Sub-Executors with WorkflowExecutor

Compose workflows by embedding one in another:

```python
from agent_framework.workflows import Workflow, WorkflowExecutor

# Child workflow
def create_child_workflow():
    wf = Workflow()
    wf.add_node("step_a", executor_a)
    wf.add_node("step_b", executor_b)
    wf.connect("step_a", "step_b")
    wf.set_entry_node("step_a")
    wf.set_exit_node("step_b")
    return wf

# Parent workflow with child as node
parent = Workflow()

# Create child workflow and wrap as executor
child_wf = create_child_workflow()
child_executor = WorkflowExecutor(child_wf, id="child_pipeline")

# Add child to parent
parent.add_node("preprocess", preprocessor)
parent.add_node("child", child_executor)  # Embedded workflow
parent.add_node("postprocess", postprocessor)

parent.connect("preprocess", "child")
parent.connect("child", "postprocess")
parent.set_entry_node("preprocess")
parent.set_exit_node("postprocess")

# Parent can be exposed as agent
parent_agent = parent.as_agent(
    name="ParentPipeline",
    instructions="Execute nested pipelines",
    client=client,
)

# Usage
result = await parent_agent.run("input data")
```

### Multiple Levels of Nesting

```python
def create_hierarchical_workflows():
    """Create multi-level nested workflows."""

    # Level 3: Leaf workflows
    leaf1 = create_workflow([executor1, executor2])
    leaf2 = create_workflow([executor3, executor4])

    # Level 2: Mid-level workflows
    mid = Workflow()
    mid.add_node("leaf1", WorkflowExecutor(leaf1, "leaf1"))
    mid.add_node("leaf2", WorkflowExecutor(leaf2, "leaf2"))
    mid.add_node("merger", merge_executor)
    mid.connect("leaf1", "merger")
    mid.connect("leaf2", "merger")

    # Level 1: Root workflow
    root = Workflow()
    root.add_node("pre", preprocessor)
    root.add_node("mid", WorkflowExecutor(mid, "mid"))
    root.add_node("post", postprocessor)
    root.connect("pre", "mid")
    root.connect("mid", "post")

    return root

# Expose complex hierarchy as single agent
root_workflow = create_hierarchical_workflows()
hierarchical_agent = root_workflow.as_agent(
    name="HierarchicalProcessor",
    instructions="Process data through multi-level pipeline",
    client=client,
)
```

## WorkflowExecutor Wrapper

The wrapper class for embedding workflows:

```python
from agent_framework.workflows import Executor, handler, WorkflowContext

class WorkflowExecutor(Executor):
    """Run a workflow as an executor node."""

    def __init__(self, workflow: Workflow, id: str = None):
        super().__init__(id=id or f"workflow_{workflow.id}")
        self.workflow = workflow

    @handler
    async def execute(self, data, ctx: WorkflowContext) -> None:
        """Execute embedded workflow."""
        events = await self.workflow.run(data)
        outputs = events.get_outputs()
        await ctx.send_message(outputs)
```

## When to Use Workflow-as-Agent

| Use Case | Suitable |
|---|:-:|
| Reusing workflows across systems | ✅ |
| Composing workflows in orchestrations | ✅ |
| Adding conversation memory to workflows | ✅ |
| Exposing workflows as API endpoints | ✅ |
| Workflow debugging via agent interface | ✅ |
| Workflow versioning and deployment | ✅ |
| Nested workflow composition | ✅ |
| Complex state management across steps | ✅ |
| Simple single-step operations | ❌ |
| Pure data processing (no agents) | ❌ |

## Best Practices

1. **Keep workflows focused** — Single responsibility
2. **Use clear naming** — Agent name reflects purpose
3. **Document instructions** — Clear system prompts
4. **Handle state properly** — Use sessions for memory
5. **Test in isolation** — Test workflow before wrapping as agent
6. **Version control** — Track workflow changes
7. **Monitor performance** — Check execution times
8. **Handle errors** — Include error handling in workflows
