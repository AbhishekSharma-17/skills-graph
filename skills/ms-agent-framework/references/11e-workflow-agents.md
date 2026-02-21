# Agents in Workflows — AgentExecutor, Streaming, Structured Data

## Built-in AgentExecutor Class

The framework provides a built-in `AgentExecutor` that wraps any agent as a workflow node. It handles message routing, streaming, and response collection automatically.

### AgentExecutor Constructor

```python
from agent_framework import AgentExecutor, AgentExecutorRequest, AgentExecutorResponse

executor = AgentExecutor(
    agent=my_agent,          # Agent instance from client.as_agent()
    id="agent_step"          # Unique executor ID
)
```

| Parameter | Type | Description |
|---|---|---|
| `agent` | Agent | The agent instance to wrap |
| `id` | str | Unique identifier for this executor in the workflow |

### AgentExecutorRequest Structure

Messages sent to an AgentExecutor must be wrapped in `AgentExecutorRequest`:

```python
from agent_framework import AgentExecutorRequest, Message

request = AgentExecutorRequest(
    messages=[
        Message("user", text="Research this topic"),
        Message("assistant", text="I found some info")  # Optional prior context
    ],
    should_respond=True,  # If False, treats as context only
)
```

| Field | Type | Description |
|---|---|---|
| `messages` | List[Message] | Chat messages for the agent |
| `should_respond` | bool | Whether agent should generate a response |

### AgentExecutorResponse Structure

The response from an agent contains both the final response and full conversation:

```python
response: AgentExecutorResponse
# response.executor_id: str              # ID of the executor
# response.agent_response: AgentResponse # Final response with .text
# response.full_conversation: List[Message]  # Complete message history
```

Access agent output:

```python
@handler
async def handle_agent_result(self, response: AgentExecutorResponse, ctx: WorkflowContext):
    final_text = response.agent_response.text
    full_history = response.full_conversation
    await ctx.send_message(final_text)
```

## Basic Agent Executor Pattern

### Simple Agent in Workflow

```python
from agent_framework.workflows import Executor, handler, WorkflowContext
from agent_framework import AgentExecutor, AgentExecutorRequest, AgentExecutorResponse

class AgentCoordinator(Executor):
    """Routes input to agent executor."""

    def __init__(self):
        super().__init__(id="coordinator")

    @handler
    async def invoke_agent(self, topic: str, ctx: WorkflowContext[AgentExecutorRequest]) -> None:
        request = AgentExecutorRequest(
            messages=[Message("user", text=f"Analyze: {topic}")],
            should_respond=True
        )
        await ctx.send_message(request)

# Create agent
researcher = client.as_agent(
    name="Researcher",
    instructions="Provide detailed research findings as bullet points."
)

# Create executor
agent_node = AgentExecutor(agent=researcher, id="research")

# Connect in workflow
wf = (
    WorkflowBuilder(start_executor=AgentCoordinator())
    .add_edge("coordinator", "research")
    .add_edge("research", "output")
    .build()
)
```

## Agent Message Types

AgentExecutor handles three input types automatically:

### String Input

```python
# Wraps automatically as Message("user", text=input)
await ctx.send_message("What is AI?")
```

### Message Input

```python
msg = Message("user", text="Explain machine learning")
await ctx.send_message(msg)
```

### Message List Input

```python
# Full conversation history
messages = [
    Message("user", text="What is deep learning?"),
    Message("assistant", text="Deep learning uses neural networks..."),
    Message("user", text="Give more details")
]
await ctx.send_message(messages)
```

Internal conversion:

```python
@handler
async def process(self, input_data, ctx: WorkflowContext):
    # All converted to AgentExecutorRequest internally
    if isinstance(input_data, str):
        request = AgentExecutorRequest(
            messages=[Message("user", text=input_data)],
            should_respond=True
        )
    elif isinstance(input_data, Message):
        request = AgentExecutorRequest(
            messages=[input_data],
            should_respond=True
        )
    elif isinstance(input_data, list):
        request = AgentExecutorRequest(
            messages=input_data,
            should_respond=True
        )
```

## Streaming Agent Executors

Stream real-time updates from agent execution using `stream=True` on the workflow:

### Streaming Pattern

```python
async for event in workflow.run_stream(input_data):
    if event.type == "output":
        if isinstance(event.data, AgentResponseUpdate):
            # Streaming text chunk from agent
            print(event.data.text, end="", flush=True)
        elif isinstance(event.data, AgentResponse):
            # Final non-streaming response
            print(event.data.text)
```

### Stream-Aware Agent Node

```python
from agent_framework.workflows import Executor, handler, WorkflowContext

class StreamingAnalyzer(Executor):
    def __init__(self):
        super().__init__(id="analyzer")

    @handler
    async def analyze(self, document: str, ctx: WorkflowContext[AgentExecutorRequest]) -> None:
        # Send request to streaming agent
        await ctx.send_message(AgentExecutorRequest(
            messages=[Message("user", text=f"Analyze:\n{document}")],
            should_respond=True
        ))

# Agents and executors stream automatically
agent = client.as_agent(
    name="Analyzer",
    instructions="Provide analysis in real-time.",
    stream=True
)

executor = AgentExecutor(agent=agent, id="analyzer")
```

### Collecting Streaming Updates

Accumulate streaming updates in a handler:

```python
class StreamAccumulator(Executor):
    def __init__(self):
        super().__init__(id="accumulator")
        self.accumulated_text = ""

    @handler
    async def receive_update(self, update: AgentResponseUpdate, ctx: WorkflowContext[str]) -> None:
        # Collect streaming text chunks
        self.accumulated_text += update.text

        # Or receive final response

    @handler
    async def receive_final(self, response: AgentResponse, ctx: WorkflowContext[str]) -> None:
        full_text = response.text
        await ctx.send_message(full_text)
```

## Passing Structured Data Between Agents

### Structured Data Pattern

Use Pydantic models for type-safe data exchange:

```python
from pydantic import BaseModel
from typing import List

class ResearchOutput(BaseModel):
    """Research findings from agent."""
    findings: List[str]
    sources: List[str]
    confidence: float

class Article(BaseModel):
    """Article written from research."""
    title: str
    content: str
    citations: List[str]
```

### Multi-Agent Pipeline with Structured Data

```python
class ResearchPhase(Executor):
    def __init__(self):
        super().__init__(id="research")
        self.researcher = client.as_agent(
            name="Researcher",
            instructions="Return JSON with 'findings', 'sources', 'confidence' fields"
        )

    @handler
    async def research(self, topic: str, ctx: WorkflowContext[AgentExecutorRequest]) -> None:
        await ctx.send_message(AgentExecutorRequest(
            messages=[Message("user", text=f"Research topic: {topic}")],
            should_respond=True
        ))

class WritePhase(Executor):
    def __init__(self):
        super().__init__(id="write")
        self.writer = client.as_agent(
            name="Writer",
            instructions="Write article JSON with 'title', 'content', 'citations' fields"
        )

    @handler
    async def write(self, research_response: AgentExecutorResponse, ctx: WorkflowContext[AgentExecutorRequest]) -> None:
        # Parse structured output from researcher
        research_json = research_response.agent_response.text
        research_data = ResearchOutput.model_validate_json(research_json)

        # Pass structured data to writer
        prompt = f"""
        Based on this research:
        - Findings: {', '.join(research_data.findings)}
        - Sources: {', '.join(research_data.sources)}
        - Confidence: {research_data.confidence}

        Write an article with JSON format: {{"title": "...", "content": "...", "citations": [...]}}
        """

        await ctx.send_message(AgentExecutorRequest(
            messages=[Message("user", text=prompt)],
            should_respond=True
        ))

class EditPhase(Executor):
    def __init__(self):
        super().__init__(id="edit")
        self.editor = client.as_agent(
            name="Editor",
            instructions="Review and improve the article."
        )

    @handler
    async def edit(self, article_response: AgentExecutorResponse, ctx: WorkflowContext[str]) -> None:
        article_json = article_response.agent_response.text
        article_data = Article.model_validate_json(article_json)

        await ctx.send_message(AgentExecutorRequest(
            messages=[Message("user", text=f"Edit this article:\n{article_data.content}")],
            should_respond=True
        ))
```

## Multi-Agent Pipeline (Full Example)

Complete example of 3-agent pipeline with structured handoff:

```python
import asyncio
from agent_framework.workflows import WorkflowBuilder
from agent_framework import Message, AgentExecutor, AgentExecutorRequest, AgentExecutorResponse

async def main():
    # Create three specialized agents
    planner = client.as_agent(
        name="Planner",
        instructions="Create a detailed step-by-step plan. Output JSON with 'steps' array."
    )

    executor_agent = client.as_agent(
        name="Executor",
        instructions="Execute each step and report results. Output JSON with 'results' array."
    )

    reviewer = client.as_agent(
        name="Reviewer",
        instructions="Review execution results and provide assessment."
    )

    # Wrap as executors
    planner_node = AgentExecutor(agent=planner, id="planner")
    executor_node = AgentExecutor(agent=executor_agent, id="executor")
    reviewer_node = AgentExecutor(agent=reviewer, id="reviewer")

    # Build workflow
    workflow = (
        WorkflowBuilder(start_executor=planner_node)
        .add_edge(planner_node, executor_node)
        .add_edge(executor_node, reviewer_node)
        .build()
    )

    # Run workflow
    input_request = AgentExecutorRequest(
        messages=[Message("user", text="Build a REST API for a todo app")],
        should_respond=True
    )

    async for event in workflow.run_stream(input_request):
        if event.type == "output":
            if isinstance(event.data, AgentResponseUpdate):
                print(event.data.text, end="", flush=True)
            elif isinstance(event.data, AgentResponse):
                print(f"\nFinal: {event.data.text}")

asyncio.run(main())
```

## Agent with Tools in Workflow

Agents use tools automatically during execution. Simply pass tools when creating the agent:

```python
from agent_framework import tool
from typing import Annotated

@tool
def search_web(query: Annotated[str, "Search query"]) -> str:
    """Search the web."""
    return f"Results for: {query}"

@tool
def code_executor(script: Annotated[str, "Python script"]) -> str:
    """Execute Python code."""
    return f"Executed: {script}"

# Create agent with tools
agent_with_tools = client.as_agent(
    name="Developer",
    instructions="Use search and code executor tools to solve problems.",
    tools=[search_web, code_executor]
)

# Tool calls happen automatically during agent.run()
node = AgentExecutor(agent=agent_with_tools, id="dev")

# In workflow, agent automatically calls tools and handles responses
wf = (
    WorkflowBuilder(start_executor=node)
    .build()
)
```

## Different Providers in Same Workflow

Combine agents from different LLM providers in one workflow:

```python
from agent_framework.azure import AzureOpenAIChatClient
from agent_framework.openai import OpenAIChatClient

# Azure agent
azure_agent = AzureOpenAIChatClient(
    project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
    credential=AzureCliCredential()
).as_agent(
    name="AzureAnalyzer",
    instructions="Analyze with Azure OpenAI"
)

# OpenAI agent
openai_agent = OpenAIChatClient(
    api_key=os.environ["OPENAI_API_KEY"]
).as_agent(
    name="OpenAIProcessor",
    instructions="Process with OpenAI"
)

# Use both in same workflow
analyzer = AgentExecutor(azure_agent, "azure_step")
processor = AgentExecutor(openai_agent, "openai_step")

wf = (
    WorkflowBuilder(start_executor=analyzer)
    .add_edge(analyzer, processor)
    .build()
)
```

## Common Patterns

| Pattern | Use Case |
|---|---|
| Simple pass-through | Single agent does all work |
| Sequential pipeline | Agent 1 → Agent 2 → Agent 3 (each refines) |
| Structured handoff | Pass Pydantic models between agents |
| Tool-using agent | Agent calls tools automatically during execution |
| Streaming monitoring | Subscribe to real-time token stream |
| Multi-provider | Mix different LLM endpoints in one flow |
| Approval gates | Insert human decision between agents |

## Best Practices

- Always wrap agents in `AgentExecutor` for workflow integration
- Use `AgentExecutorRequest` for explicit control over messages
- Parse structured output with Pydantic `.model_validate_json()` for safety
- Stream with `workflow.run_stream()` for real-time updates
- One executor instance per workflow to avoid state sharing
- Use consistent message format across agents for compatibility
- Set `should_respond=True` only when agent needs to generate output
