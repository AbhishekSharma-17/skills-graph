# LangGraph — Multi-Agent Systems

> Source: [docs.langchain.com/oss/python/langgraph](https://docs.langchain.com/oss/python/langgraph/overview)

## Table of Contents

- [Multi-Agent Architecture Overview](#multi-agent-architecture-overview)
- [Supervisor Pattern](#supervisor-pattern)
- [Swarm Pattern](#swarm-pattern)
- [Handoff Mechanisms](#handoff-mechanisms)
- [Agent Communication](#agent-communication)
- [LangGraph Supervisor Library](#langgraph-supervisor-library)
- [Building Custom Multi-Agent Systems](#building-custom-multi-agent-systems)
- [Choosing a Pattern](#choosing-a-pattern)
- [Common Pitfalls](#common-pitfalls)

---

## Multi-Agent Architecture Overview

Multi-agent systems coordinate multiple specialized agents to solve complex tasks. LangGraph supports two primary patterns:

| Pattern | Description | Control Flow |
|---------|-------------|-------------|
| **Supervisor** | Central agent coordinates worker agents | Hub-and-spoke |
| **Swarm** | Agents hand off to each other directly | Peer-to-peer |

```
Supervisor:                    Swarm:
     Supervisor                Agent A ← → Agent B
    /    |    \                   ↕           ↕
Agent A Agent B Agent C       Agent C ← → Agent D
```

## Supervisor Pattern

A central supervisor agent decides which worker to invoke next:

```python
from typing import Literal
from langgraph.graph import StateGraph, START, END, MessagesState
from langchain_anthropic import ChatAnthropic

model = ChatAnthropic(model="claude-sonnet-4-20250514")

# Define worker agents as nodes
def researcher(state: MessagesState):
    response = model.invoke([
        {"role": "system", "content": "You are a research specialist. Search for information."},
        *state["messages"],
    ])
    return {"messages": [response]}

def writer(state: MessagesState):
    response = model.invoke([
        {"role": "system", "content": "You are a writing specialist. Draft polished content."},
        *state["messages"],
    ])
    return {"messages": [response]}

def reviewer(state: MessagesState):
    response = model.invoke([
        {"role": "system", "content": "You are a quality reviewer. Check for accuracy and clarity."},
        *state["messages"],
    ])
    return {"messages": [response]}

# Supervisor decides routing
def supervisor(state: MessagesState) -> Command[Literal["researcher", "writer", "reviewer", END]]:
    response = model.invoke([
        {"role": "system", "content": (
            "You are a supervisor managing a team of: researcher, writer, reviewer. "
            "Based on the conversation, decide which agent should act next. "
            "Respond with the agent name or 'FINISH' if the task is complete."
        )},
        *state["messages"],
    ])
    
    content = response.content.lower()
    if "finish" in content:
        return Command(goto=END, update={"messages": [response]})
    elif "researcher" in content:
        return Command(goto="researcher", update={"messages": [response]})
    elif "writer" in content:
        return Command(goto="writer", update={"messages": [response]})
    else:
        return Command(goto="reviewer", update={"messages": [response]})

# Build the graph
graph = StateGraph(MessagesState)
graph.add_node("supervisor", supervisor)
graph.add_node("researcher", researcher)
graph.add_node("writer", writer)
graph.add_node("reviewer", reviewer)

graph.add_edge(START, "supervisor")
graph.add_edge("researcher", "supervisor")
graph.add_edge("writer", "supervisor")
graph.add_edge("reviewer", "supervisor")
```

## Swarm Pattern

Agents hand off directly to each other without a central coordinator:

```python
from langgraph.types import Command

def triage_agent(state: MessagesState) -> Command[Literal["billing", "technical", "sales"]]:
    response = model.invoke([
        {"role": "system", "content": "You are a triage agent. Route to billing, technical, or sales."},
        *state["messages"],
    ])
    
    content = response.content.lower()
    if "billing" in content:
        return Command(goto="billing", update={"messages": [response]})
    elif "technical" in content:
        return Command(goto="technical", update={"messages": [response]})
    return Command(goto="sales", update={"messages": [response]})

def billing_agent(state: MessagesState) -> Command[Literal["technical", END]]:
    response = model.invoke([
        {"role": "system", "content": "You handle billing inquiries. If technical, hand off."},
        *state["messages"],
    ])
    
    if "technical" in response.content.lower():
        return Command(goto="technical", update={"messages": [response]})
    return Command(goto=END, update={"messages": [response]})

def technical_agent(state: MessagesState):
    response = model.invoke([
        {"role": "system", "content": "You handle technical support."},
        *state["messages"],
    ])
    return {"messages": [response]}

graph = StateGraph(MessagesState)
graph.add_node("triage", triage_agent)
graph.add_node("billing", billing_agent)
graph.add_node("technical", technical_agent)
graph.add_node("sales", sales_agent)

graph.add_edge(START, "triage")
graph.add_edge("technical", END)
graph.add_edge("sales", END)
```

## Handoff Mechanisms

### Using Command Objects

The primary way agents hand off to each other:

```python
def agent_a(state: State) -> Command[Literal["agent_b", "agent_c"]]:
    # Decide where to go
    return Command(
        update={"messages": [response], "context": "from_a"},
        goto="agent_b",
    )
```

### Using Handoff Tools

Create tools that agents can call to transfer control:

```python
from langchain_core.tools import tool

def create_handoff_tool(target_agent: str, description: str):
    @tool(name=f"transfer_to_{target_agent}")
    def handoff(reason: str) -> str:
        f"""Transfer to {target_agent}. {description}"""
        return f"Transferring to {target_agent}: {reason}"
    return handoff

transfer_to_billing = create_handoff_tool(
    "billing", "Use when the user has billing questions"
)
transfer_to_technical = create_handoff_tool(
    "technical", "Use when the user has technical issues"
)
```

### Subgraph Handoff

Navigate from a subgraph to a sibling in the parent graph:

```python
def subgraph_node(state: State) -> Command:
    return Command(
        goto="other_agent",
        graph=Command.PARENT,  # Navigate in parent graph
    )
```

## Agent Communication

### Shared State

All agents read from and write to the same state:

```python
class TeamState(TypedDict):
    messages: Annotated[list, add_messages]
    research_notes: Annotated[list[str], operator.add]
    draft: str
    feedback: str

def researcher(state: TeamState):
    notes = do_research(state["messages"][-1].content)
    return {"research_notes": [notes]}

def writer(state: TeamState):
    draft = write_from_notes(state["research_notes"])
    return {"draft": draft}
```

### Private Agent State via Subgraphs

Give each agent its own private message history:

```python
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

class ParentState(TypedDict):
    messages: Annotated[list, add_messages]
    current_task: str

# Agent has private conversation history
agent_graph = StateGraph(AgentState)
# ... build agent graph ...
agent_app = agent_graph.compile()

# Wrapper transforms state
def run_agent(state: ParentState):
    result = agent_app.invoke({
        "messages": [{"role": "user", "content": state["current_task"]}]
    })
    return {"messages": [result["messages"][-1]]}

parent = StateGraph(ParentState)
parent.add_node("agent", run_agent)
```

## LangGraph Supervisor Library

A pre-built supervisor implementation:

```python
# pip install langgraph-supervisor

from langgraph_supervisor import create_supervisor

supervisor = create_supervisor(
    model=model,
    agents=[researcher_agent, writer_agent, reviewer_agent],
    prompt="You manage a content creation team. Coordinate the agents to complete tasks.",
)

result = supervisor.invoke({
    "messages": [{"role": "user", "content": "Write an article about AI safety"}]
})
```

## Building Custom Multi-Agent Systems

### Hierarchical Teams

```python
# Research team (sub-supervisor)
research_team = StateGraph(MessagesState)
research_team.add_node("search_agent", search_agent)
research_team.add_node("analysis_agent", analysis_agent)
research_team.add_node("research_supervisor", research_supervisor)
# ... edges ...
research_app = research_team.compile()

# Writing team (sub-supervisor)
writing_team = StateGraph(MessagesState)
writing_team.add_node("draft_agent", draft_agent)
writing_team.add_node("edit_agent", edit_agent)
writing_team.add_node("writing_supervisor", writing_supervisor)
# ... edges ...
writing_app = writing_team.compile()

# Top-level supervisor
top = StateGraph(MessagesState)
top.add_node("research_team", research_app)
top.add_node("writing_team", writing_app)
top.add_node("director", director_agent)

top.add_edge(START, "director")
top.add_edge("research_team", "director")
top.add_edge("writing_team", "director")
```

### Sequential Pipeline

```python
graph = StateGraph(MessagesState)
graph.add_node("planner", planner_agent)
graph.add_node("executor", executor_agent)
graph.add_node("validator", validator_agent)

graph.add_edge(START, "planner")
graph.add_edge("planner", "executor")
graph.add_edge("executor", "validator")

def validate_or_retry(state):
    if state.get("valid"):
        return END
    return "planner"

graph.add_conditional_edges("validator", validate_or_retry)
```

## Choosing a Pattern

| Criterion | Supervisor | Swarm |
|-----------|-----------|-------|
| **Control** | Centralized, easier to reason about | Decentralized, agents self-organize |
| **Overhead** | Extra LLM call per routing decision | No intermediary, fewer LLM calls |
| **Scalability** | Supervisor becomes bottleneck at scale | Scales with agent count |
| **Debugging** | Clear routing decisions in one place | Harder to trace handoff chains |
| **Best for** | Task decomposition, quality control | Customer service routing, workflows |

## Common Pitfalls

1. **Infinite agent loops** — Agents handing off endlessly. Set `recursion_limit` and add exit conditions.
2. **State bloat** — All agents accumulate messages. Trim or summarize between handoffs.
3. **Unclear agent boundaries** — Each agent should have a distinct specialization. Overlap causes confusion.
4. **Missing exit conditions** — Every path must eventually reach `END`. Test all routing branches.
5. **Supervisor over-reliance** — Don't use supervisor for simple linear pipelines. Use direct edges.

---

> **Related:** [11-subgraphs.md](11-subgraphs.md) for subgraph composition, [09-prebuilt-agents.md](09-prebuilt-agents.md) for prebuilt agent components
