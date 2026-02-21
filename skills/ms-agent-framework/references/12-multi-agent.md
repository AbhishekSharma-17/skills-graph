# Multi-Agent Orchestration — Patterns & Examples

## Multi-Agent Patterns

| Pattern | Description | When to Use |
|---|---|---|
| **Sequential** | Agents run one after another in a chain | Linear pipelines, staged processing |
| **Concurrent** | Agents run in parallel | Independent analysis from multiple perspectives |
| **Handoff** | Agent dynamically routes to specialist | Customer support, triage |
| **Group Chat** | Multiple agents collaborate in turns | Brainstorming, review processes |
| **Supervisor** | One agent orchestrates others as tools | Complex coordination |

## Sequential — Pipeline

```python
import asyncio
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity.aio import AzureCliCredential

async def main():
    client = AzureOpenAIResponsesClient(
        project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
        deployment_name=os.environ["AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME"],
        credential=AzureCliCredential(),
    )

    # Agent 1: Research
    researcher = client.as_agent(
        name="Researcher",
        instructions="Research the given topic thoroughly. Output key findings.",
    )

    # Agent 2: Writer
    writer = client.as_agent(
        name="Writer",
        instructions="Write a polished article based on the research provided.",
    )

    # Agent 3: Editor
    editor = client.as_agent(
        name="Editor",
        instructions="Edit the article for clarity, grammar, and style.",
    )

    # Sequential execution
    topic = "The future of quantum computing"
    research = await researcher.run(f"Research: {topic}")
    draft = await writer.run(f"Write article based on this research:\n{research.text}")
    final = await editor.run(f"Edit this article:\n{draft.text}")

    print(final.text)
```

## Concurrent — Parallel Analysis

```python
async def parallel_analysis(query: str):
    # Three agents analyze simultaneously
    optimist = client.as_agent(
        name="Optimist",
        instructions="Analyze from an optimistic perspective.",
    )
    pessimist = client.as_agent(
        name="Pessimist",
        instructions="Analyze from a pessimistic, risk-focused perspective.",
    )
    realist = client.as_agent(
        name="Realist",
        instructions="Analyze from a balanced, realistic perspective.",
    )

    # Run all in parallel
    results = await asyncio.gather(
        optimist.run(query),
        pessimist.run(query),
        realist.run(query),
    )

    # Synthesize
    synthesizer = client.as_agent(
        name="Synthesizer",
        instructions="Synthesize these three analyses into a balanced summary.",
    )
    combined = "\n\n".join([
        f"Optimist: {results[0].text}",
        f"Pessimist: {results[1].text}",
        f"Realist: {results[2].text}",
    ])
    return await synthesizer.run(f"Synthesize:\n{combined}")
```

## Handoff — Dynamic Routing

One agent routes to specialists based on the request:

```python
from agent_framework import tool
from typing import Annotated

# Specialist agents
billing_agent = client.as_agent(
    name="BillingSpecialist",
    instructions="Handle billing questions. Be specific about charges and plans.",
)
tech_agent = client.as_agent(
    name="TechSupport",
    instructions="Handle technical issues. Provide step-by-step solutions.",
)
sales_agent = client.as_agent(
    name="Sales",
    instructions="Handle sales inquiries. Be persuasive but helpful.",
)

# Expose specialists as tools
@tool
async def route_to_billing(question: Annotated[str, "Billing question"]) -> str:
    """Route to billing specialist for billing-related questions."""
    result = await billing_agent.run(question)
    return result.text

@tool
async def route_to_tech(question: Annotated[str, "Technical question"]) -> str:
    """Route to tech support for technical issues."""
    result = await tech_agent.run(question)
    return result.text

@tool
async def route_to_sales(question: Annotated[str, "Sales question"]) -> str:
    """Route to sales for pricing and plan inquiries."""
    result = await sales_agent.run(question)
    return result.text

# Router agent
router = client.as_agent(
    name="Router",
    instructions="""You are a customer support router.
    Determine which specialist to route the customer to:
    - Billing: charges, payments, invoices, plans
    - Tech: bugs, errors, setup, configuration
    - Sales: pricing, upgrades, new features""",
    tools=[route_to_billing, route_to_tech, route_to_sales],
)

result = await router.run("My invoice seems wrong, I was charged twice")
```

## Supervisor — Orchestrator Pattern

One agent uses others as tools:

```python
# Define specialist agents
weather_agent = client.as_agent(name="Weather", ...)
travel_agent = client.as_agent(name="Travel", ...)
restaurant_agent = client.as_agent(name="Restaurant", ...)

# Wrap each as a tool
@tool
async def check_weather(query: Annotated[str, "Weather query"]) -> str:
    """Get weather information."""
    return (await weather_agent.run(query)).text

@tool
async def plan_travel(query: Annotated[str, "Travel planning query"]) -> str:
    """Plan travel arrangements."""
    return (await travel_agent.run(query)).text

@tool
async def find_restaurants(query: Annotated[str, "Restaurant query"]) -> str:
    """Find restaurant recommendations."""
    return (await restaurant_agent.run(query)).text

# Supervisor coordinates everything
supervisor = client.as_agent(
    name="TripPlanner",
    instructions="""You are a trip planning supervisor.
    Use your tools to coordinate:
    1. Check weather at destination
    2. Plan travel logistics
    3. Find restaurant recommendations
    Combine everything into a complete trip plan.""",
    tools=[check_weather, plan_travel, find_restaurants],
)

result = await supervisor.run("Plan a weekend trip to Portland")
```

## Group Chat — Collaborative

Multiple agents take turns in a shared conversation:

```python
async def group_chat(topic: str, agents: list, rounds: int = 3):
    """Run a group chat where agents take turns."""
    conversation = [f"Topic: {topic}"]

    for round_num in range(rounds):
        for agent in agents:
            context = "\n\n".join(conversation)
            response = await agent.run(
                f"Previous discussion:\n{context}\n\nAdd your perspective."
            )
            conversation.append(f"{agent.name}: {response.text}")

    return "\n\n".join(conversation)

# Create agents with different perspectives
agents = [
    client.as_agent(name="Engineer", instructions="Think about technical feasibility."),
    client.as_agent(name="Designer", instructions="Think about user experience."),
    client.as_agent(name="PM", instructions="Think about business value and timeline."),
]

result = await group_chat("Should we add AI search to our product?", agents)
```

## Multi-Agent with Workflows

For complex multi-agent orchestration, use workflows:

```python
from agent_framework.workflows import Workflow, Executor, handler, WorkflowContext

class AgentNode(Executor):
    def __init__(self, agent, id: str):
        super().__init__(id=id)
        self.agent = agent

    @handler
    async def run(self, input_text: str, ctx: WorkflowContext[str]) -> None:
        result = await self.agent.run(input_text)
        await ctx.send_message(result.text)

# Build multi-agent workflow
wf = Workflow()
wf.add_node("research", AgentNode(researcher, "research"))
wf.add_node("write", AgentNode(writer, "write"))
wf.add_node("review", AgentNode(reviewer, "review"))

wf.connect("research", "write")
wf.connect("write", "review")
wf.set_entry_node("research")
wf.set_exit_node("review")

events = await wf.run("Write an article about AI safety")
```

## Choosing a Pattern

| Requirement | Pattern |
|---|---|
| Steps must happen in order | Sequential |
| Steps are independent | Concurrent |
| Need dynamic routing | Handoff |
| Need discussion/debate | Group Chat |
| Need coordination + multiple tools | Supervisor |
| Complex graph with conditions | Workflow |
