# Agents in Workflows — Using Agents as Workflow Nodes

## Agent as Executor

Wrap any agent as a workflow executor node:

```python
from agent_framework.workflows import Executor, handler, WorkflowContext

class AgentExecutor(Executor):
    """Generic wrapper: runs an Agent as a workflow node."""

    def __init__(self, agent, id: str):
        super().__init__(id=id)
        self.agent = agent

    @handler
    async def process(self, input_text: str, ctx: WorkflowContext[str]) -> None:
        session = self.agent.create_session()
        result = await self.agent.run(input_text, session=session)
        await ctx.send_message(result.text)
```

### Usage

```python
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity.aio import AzureCliCredential
from agent_framework.workflows import Workflow

client = AzureOpenAIResponsesClient(
    project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
    deployment_name=os.environ["AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME"],
    credential=AzureCliCredential(),
)

# Create specialized agents
researcher = client.as_agent(
    name="Researcher",
    instructions="Research the topic. Output key findings as bullet points.",
)
writer = client.as_agent(
    name="Writer",
    instructions="Write a polished article from the provided research.",
)
editor = client.as_agent(
    name="Editor",
    instructions="Edit for clarity, grammar, and style. Output the final version.",
)

# Wrap as workflow executors
research_node = AgentExecutor(researcher, "research")
writer_node = AgentExecutor(writer, "write")
editor_node = AgentExecutor(editor, "edit")

# Build workflow
wf = Workflow()
wf.add_node("research", research_node)
wf.add_node("write", writer_node)
wf.add_node("edit", editor_node)
wf.connect("research", "write")
wf.connect("write", "edit")
wf.set_entry_node("research")
wf.set_exit_node("edit")  # Must use yield_output in exit node
```

## Agent Executor with yield_output (Exit Node)

For the final node, use `yield_output`:

```python
class AgentExitExecutor(Executor):
    """Agent executor that yields output (for exit nodes)."""

    def __init__(self, agent, id: str):
        super().__init__(id=id)
        self.agent = agent

    @handler
    async def process(self, input_text: str, ctx: WorkflowContext[str, str]) -> None:
        session = self.agent.create_session()
        result = await self.agent.run(input_text, session=session)
        await ctx.yield_output(result.text)  # Final output
```

## Streaming Agent in Workflow

```python
class StreamingAgentExecutor(Executor):
    def __init__(self, agent, id: str):
        super().__init__(id=id)
        self.agent = agent

    @handler
    async def process(self, input_text: str, ctx: WorkflowContext[str]) -> None:
        session = self.agent.create_session()
        stream = self.agent.run(input_text, session=session, stream=True)
        final = await stream.get_final_response()
        await ctx.send_message(final.text)
```

## Agent with Tools in Workflow

```python
from agent_framework import tool
from typing import Annotated

@tool
def search_web(query: Annotated[str, "Search query"]) -> str:
    """Search the web for information."""
    return f"Results for: {query}"

research_agent = client.as_agent(
    name="WebResearcher",
    instructions="Use web search to find information.",
    tools=[search_web],
)

# Wrap as node — tools are called automatically during agent.run()
research_node = AgentExecutor(research_agent, "research")
```

## Passing Structured Data Between Agent Nodes

```python
import json

class StructuredAgentExecutor(Executor):
    """Agent node that receives and emits structured data."""

    def __init__(self, agent, id: str):
        super().__init__(id=id)
        self.agent = agent

    @handler
    async def process(self, data: dict, ctx: WorkflowContext[dict]) -> None:
        # Convert dict to prompt
        prompt = f"Input data:\n{json.dumps(data, indent=2)}\n\nProcess this and respond with JSON."
        session = self.agent.create_session()
        result = await self.agent.run(prompt, session=session)

        # Parse agent's JSON response
        try:
            output = json.loads(result.text)
        except json.JSONDecodeError:
            output = {"raw_response": result.text}

        await ctx.send_message(output)
```

## Multi-Agent Pipeline (Full Example)

```python
import asyncio
from agent_framework.workflows import Workflow
from typing import Never

async def main():
    # Agents
    planner = client.as_agent(
        name="Planner",
        instructions="Create a detailed plan for the given task. Output steps.",
    )
    executor_agent = client.as_agent(
        name="Executor",
        instructions="Execute each step in the plan. Output results.",
        tools=[search_web, run_code],
    )
    reviewer = client.as_agent(
        name="Reviewer",
        instructions="Review the execution results. Output final assessment.",
    )

    # Nodes
    plan_node = AgentExecutor(planner, "plan")
    exec_node = AgentExecutor(executor_agent, "execute")
    review_node = AgentExitExecutor(reviewer, "review")  # Exit node

    # Workflow
    wf = Workflow()
    wf.add_node("plan", plan_node)
    wf.add_node("execute", exec_node)
    wf.add_node("review", review_node)
    wf.connect("plan", "execute")
    wf.connect("execute", "review")
    wf.set_entry_node("plan")
    wf.set_exit_node("review")

    # Run
    events = await wf.run("Build a REST API for a todo app")
    print(events.get_outputs())

asyncio.run(main())
```

## Workflow as Agent

Make an entire workflow callable like a single agent:

```python
class WorkflowAgent:
    """Wraps a workflow to behave like an agent."""

    def __init__(self, workflow, name: str):
        self.workflow = workflow
        self.name = name

    async def run(self, message: str):
        events = await self.workflow.run(message)
        return events.get_outputs()

# Use workflow as if it were a single agent
pipeline = WorkflowAgent(my_workflow, "ContentPipeline")
result = await pipeline.run("Write a blog post about AI")
```

## When to Use Agents in Workflows vs Orchestrations

| Scenario | Use |
|---|---|
| Simple linear agent pipeline | Workflow with AgentExecutor nodes |
| Dynamic agent selection | Orchestration (Handoff, Magentic) |
| Agent collaboration / discussion | Orchestration (Group Chat) |
| Fixed processing steps with agents | Workflow |
| Need conditional branching between agents | Workflow with Router executor |
| Parallel agent analysis | Orchestration (Concurrent) |
