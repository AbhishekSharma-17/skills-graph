# Multi-Agent Systems

> Source: [developers.llamaindex.ai — Multi-Agent](https://developers.llamaindex.ai/python/framework/understanding/agent/multi_agent/) | Version: 0.14.22

## Table of Contents
- [Overview](#overview)
- [AgentWorkflow (Handoff Pattern)](#agentworkflow-handoff-pattern)
- [Orchestrator Pattern](#orchestrator-pattern)
- [Custom Planner Pattern](#custom-planner-pattern)
- [Shared State](#shared-state)
- [Pattern Selection Guide](#pattern-selection-guide)
- [Common Patterns](#common-patterns)

## Overview

LlamaIndex provides three patterns for building multi-agent systems, each with different tradeoffs between simplicity and control:

1. **AgentWorkflow** — Agents hand off to each other in a swarm pattern
2. **Orchestrator** — A top-level agent treats sub-agents as callable tools
3. **Custom Planner** — Full DIY orchestration with explicit planning

## AgentWorkflow (Handoff Pattern)

The simplest multi-agent approach. You define agents with `can_handoff_to` declarations, and they transfer control to each other automatically.

```python
from llama_index.core.agent.workflow import AgentWorkflow, FunctionAgent
from llama_index.llms.openai import OpenAI

llm = OpenAI(model="gpt-4o")

# Define specialized agents
research_agent = FunctionAgent(
    name="researcher",
    description="Expert at finding and analyzing information.",
    system_prompt="You research topics thoroughly. Hand off to writer when done.",
    tools=[search_tool],
    llm=llm,
    can_handoff_to=["writer"],
)

writer_agent = FunctionAgent(
    name="writer",
    description="Expert at writing clear, engaging content.",
    system_prompt="You write content based on research notes. Hand off to reviewer.",
    tools=[],
    llm=llm,
    can_handoff_to=["reviewer"],
)

reviewer_agent = FunctionAgent(
    name="reviewer",
    description="Expert at reviewing and improving content quality.",
    system_prompt="You review content for accuracy and clarity.",
    tools=[],
    llm=llm,
    can_handoff_to=["writer"],
)

# Create the workflow
workflow = AgentWorkflow(
    agents=[research_agent, writer_agent, reviewer_agent],
    root_agent="researcher",
    initial_state={
        "research_notes": [],
        "draft": "",
        "feedback": [],
    },
)

import asyncio
response = asyncio.run(workflow.run(
    user_msg="Write an article about quantum computing"
))
```

Key concepts:
- `can_handoff_to` — Declares which agents this agent can transfer control to
- `root_agent` — The first agent to receive the user message
- `initial_state` — Shared state dictionary accessible by all agents
- Agents use a special `handoff` tool injected automatically

### How Handoffs Work

When an agent calls the `handoff` tool:
1. Current agent's conversation context is preserved
2. Control transfers to the target agent
3. Target agent receives the handoff message
4. Flow continues until an agent produces a final response

## Orchestrator Pattern

A central orchestrator agent treats specialist agents as callable tools. The orchestrator maintains full control over execution flow.

```python
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.workflow import Context

# Create specialist agents
research_agent = FunctionAgent(
    name="researcher",
    tools=[search_tool],
    llm=llm,
    system_prompt="You are a research specialist.",
)

writer_agent = FunctionAgent(
    name="writer",
    tools=[],
    llm=llm,
    system_prompt="You write content based on provided notes.",
)

# Wrap agents as tools for the orchestrator
async def call_researcher(ctx: Context, query: str) -> str:
    """Research a topic and return notes."""
    result = await research_agent.run(user_msg=f"Research: {query}")
    async with ctx.store.edit_state() as state:
        state["state"]["research_notes"].append(str(result))
    return str(result)

async def call_writer(ctx: Context, prompt: str) -> str:
    """Write content based on a prompt and available research notes."""
    state = await ctx.store.get_state()
    notes = state["state"].get("research_notes", [])
    full_prompt = f"Notes:\n{''.join(notes)}\n\nTask: {prompt}"
    result = await writer_agent.run(user_msg=full_prompt)
    return str(result)

# Create the orchestrator
orchestrator = FunctionAgent(
    name="orchestrator",
    system_prompt=(
        "You coordinate research and writing tasks. "
        "First research, then write based on findings."
    ),
    llm=OpenAI(model="gpt-4o"),
    tools=[call_researcher, call_writer],
    initial_state={"research_notes": [], "draft": ""},
)
```

Advantages over AgentWorkflow:
- Orchestrator sees all sub-agent results
- Central decision-making at every step
- Easier to inject custom logic between agent calls
- Sub-agents don't need to know about each other

## Custom Planner Pattern

Maximum flexibility through explicit plan generation and execution. The LLM outputs a structured plan (XML/JSON) that your code parses and executes.

```python
from llama_index.core.workflow import Workflow, step, Event, StartEvent, StopEvent

class PlanEvent(Event):
    plan: list[dict]

class ExecuteEvent(Event):
    results: list[str]

class PlannerWorkflow(Workflow):
    def __init__(self, agents: dict, llm, **kwargs):
        super().__init__(**kwargs)
        self.agents = agents
        self.llm = llm

    @step
    async def plan(self, ev: StartEvent) -> PlanEvent:
        """Generate a structured execution plan."""
        prompt = f"""Given the task: {ev.user_msg}
        
        Available agents: {list(self.agents.keys())}
        
        Output a plan as JSON:
        [{{"agent": "name", "task": "description"}}]
        """
        response = await self.llm.acomplete(prompt)
        import json
        plan = json.loads(str(response))
        return PlanEvent(plan=plan)

    @step
    async def execute(self, ev: PlanEvent) -> StopEvent:
        """Execute each step of the plan."""
        results = []
        for step_info in ev.plan:
            agent = self.agents[step_info["agent"]]
            result = await agent.run(user_msg=step_info["task"])
            results.append(str(result))
        return StopEvent(result="\n\n".join(results))

planner = PlannerWorkflow(
    agents={"researcher": research_agent, "writer": writer_agent},
    llm=llm,
    timeout=120,
)
result = asyncio.run(planner.run(user_msg="Write a report"))
```

Use the Custom Planner when:
- You need a very specific plan format
- Integration with external schedulers is required
- You want full control over agent execution order
- Earlier patterns can't express your required flow

## Shared State

All patterns support shared state via `Context`:

```python
# Reading state in tools
async def my_tool(ctx: Context, input: str) -> str:
    state = await ctx.store.get_state()
    notes = state["state"].get("notes", [])
    return f"Found {len(notes)} existing notes"

# Writing state in tools
async def save_tool(ctx: Context, data: str) -> str:
    async with ctx.store.edit_state() as state:
        state["state"]["notes"].append(data)
    return "Saved"
```

State is shared across all agents in a workflow, enabling collaboration without message passing.

## Pattern Selection Guide

| Aspect | AgentWorkflow | Orchestrator | Custom Planner |
|--------|---------------|-------------|----------------|
| Code complexity | Low | Medium | High |
| Flexibility | Medium | High | Maximum |
| Control | Agents decide | Central agent decides | Code decides |
| Built-in streaming | Yes | Yes | Manual |
| State sharing | Automatic | Via Context | Manual |
| Agent awareness | Know handoff targets | Isolated | Isolated |
| Best for | Prototypes, simple flows | Production, custom logic | Complex orchestration |

**Recommendation:** Start with `AgentWorkflow` for prototyping. Move to `Orchestrator` when you need more control. Use `Custom Planner` only when the other patterns can't express your flow.

## Common Patterns

### Research → Write → Review Pipeline

```python
workflow = AgentWorkflow(
    agents=[researcher, writer, reviewer],
    root_agent="researcher",
)
```

### Tool-Routing Multi-Agent

```python
sql_agent = FunctionAgent(name="sql", tools=[sql_tool], ...)
api_agent = FunctionAgent(name="api", tools=[api_tool], ...)
router_agent = FunctionAgent(
    name="router",
    can_handoff_to=["sql", "api"],
    system_prompt="Route to sql for database queries, api for external data.",
)
```

### Hierarchical Agents

```python
manager = FunctionAgent(
    name="manager",
    tools=[call_team_lead_a, call_team_lead_b],
    system_prompt="Coordinate between team leads.",
)
```
