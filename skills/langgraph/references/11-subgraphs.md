# LangGraph — Subgraphs & Composition

> Source: [docs.langchain.com/oss/python/langgraph/use-subgraphs](https://docs.langchain.com/oss/python/langgraph/use-subgraphs)

## Table of Contents

- [Overview](#overview)
- [Adding Subgraphs as Nodes](#adding-subgraphs-as-nodes)
- [Shared State Keys](#shared-state-keys)
- [Different State Schemas](#different-state-schemas)
- [State Transformation](#state-transformation)
- [Checkpointing in Subgraphs](#checkpointing-in-subgraphs)
- [Cross-Graph Navigation](#cross-graph-navigation)
- [Nested Subgraphs](#nested-subgraphs)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

Subgraphs let you compose complex systems from smaller, reusable graph modules. A compiled `StateGraph` implements `PregelProtocol` and can be passed directly as a node to another graph.

**Use subgraphs when:**
- Different parts of your system need independent state schemas
- You want to reuse graph modules across projects
- Each agent in a multi-agent system needs private state
- You want to encapsulate complexity behind a simple interface

## Adding Subgraphs as Nodes

A compiled graph can be used as a node in a parent graph:

```python
# Define a subgraph
sub_builder = StateGraph(SubState)
sub_builder.add_node("step_1", step_1_fn)
sub_builder.add_node("step_2", step_2_fn)
sub_builder.add_edge(START, "step_1")
sub_builder.add_edge("step_1", "step_2")
sub_builder.add_edge("step_2", END)
subgraph = sub_builder.compile()

# Add as a node in parent graph
parent_builder = StateGraph(ParentState)
parent_builder.add_node("subgraph", subgraph)  # Compiled graph as node
parent_builder.add_node("other_node", other_fn)
parent_builder.add_edge(START, "subgraph")
parent_builder.add_edge("subgraph", "other_node")
parent_builder.add_edge("other_node", END)
parent = parent_builder.compile(checkpointer=checkpointer)
```

## Shared State Keys

When parent and subgraph share state keys, the subgraph reads from and writes to the parent's state channels automatically:

```python
class ParentState(TypedDict):
    messages: Annotated[list, add_messages]
    context: str

class SubState(TypedDict):
    messages: Annotated[list, add_messages]  # Shared key
    internal_data: str                        # Subgraph-only key

# Subgraph reads `messages` from parent, writes back to `messages`
# `internal_data` is private to the subgraph
# `context` is not visible inside the subgraph
```

**How it works:**
1. Parent passes overlapping keys to the subgraph
2. Subgraph executes with its own state
3. Subgraph returns values from its `output_schema`
4. Overlapping keys are written back to parent using parent's reducers

## Different State Schemas

When schemas don't overlap, use a wrapper function to transform state:

```python
class ParentState(TypedDict):
    user_query: str
    final_answer: str

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

agent_builder = StateGraph(AgentState)
# ... build agent graph ...
agent = agent_builder.compile()

def run_agent(state: ParentState) -> dict:
    # Transform parent state → subgraph input
    result = agent.invoke({
        "messages": [{"role": "user", "content": state["user_query"]}]
    })
    # Transform subgraph output → parent state
    return {"final_answer": result["messages"][-1].content}

parent = StateGraph(ParentState)
parent.add_node("agent", run_agent)  # Wrapper function, not compiled graph
```

## State Transformation

### Input Transformation

```python
def prepare_for_subgraph(state: ParentState) -> dict:
    """Transform parent state to subgraph input."""
    return {
        "messages": [
            {"role": "system", "content": f"Context: {state['context']}"},
            {"role": "user", "content": state["query"]},
        ]
    }

def subgraph_node(state: ParentState) -> dict:
    sub_input = prepare_for_subgraph(state)
    result = subgraph.invoke(sub_input)
    return {"answer": result["messages"][-1].content}
```

### Output Filtering

```python
class SubOutput(TypedDict):
    summary: str  # Only return summary to parent

sub_builder = StateGraph(SubState, output=SubOutput)
# Only `summary` propagates back to parent
```

## Checkpointing in Subgraphs

When the parent has a checkpointer, subgraphs get their own checkpoint namespace:

```python
parent = parent_builder.compile(checkpointer=InMemorySaver())

# Each subgraph invocation gets a unique checkpoint_ns
# This enables:
# - Independent state history per subgraph execution
# - Interrupt/resume within subgraphs
# - Time-travel within subgraphs
```

**Inspecting subgraph state:**

```python
config = {"configurable": {"thread_id": "t1"}}
state = parent.get_state(config)

# Get subgraph states
for task in state.tasks:
    if hasattr(task, "state"):
        print(f"Subgraph state: {task.state}")
```

## Cross-Graph Navigation

Navigate from a subgraph to a node in the parent graph using `Command.PARENT`:

```python
from langgraph.types import Command

def subgraph_decision_node(state: SubState) -> Command:
    if state["needs_escalation"]:
        return Command(
            goto="escalation_handler",
            graph=Command.PARENT,  # Navigate in parent graph
            update={"reason": "Complex case detected"},
        )
    return Command(goto="next_sub_node")
```

**Multi-agent handoff via parent:**

```python
# Agent A (subgraph) hands off to Agent B (another subgraph in parent)
def agent_a_handoff(state: AgentAState) -> Command:
    return Command(
        goto="agent_b",  # Another node in parent graph
        graph=Command.PARENT,
        update={"handoff_context": state["findings"]},
    )
```

## Nested Subgraphs

Subgraphs can contain their own subgraphs:

```python
# Level 3: Inner subgraph
inner = StateGraph(InnerState)
# ... build ...
inner_app = inner.compile()

# Level 2: Middle subgraph containing inner
middle = StateGraph(MiddleState)
middle.add_node("inner", inner_app)
# ... build ...
middle_app = middle.compile()

# Level 1: Parent containing middle
parent = StateGraph(ParentState)
parent.add_node("middle", middle_app)
# ... build ...
parent_app = parent.compile(checkpointer=checkpointer)
```

**Streaming from nested subgraphs:**

```python
for chunk in parent_app.stream(inputs, config, subgraphs=True, version="v2"):
    ns = chunk["ns"]  # Tuple: () = parent, ("middle",) = level 2, ("middle", "inner") = level 3
    print(f"Level: {len(ns)}, Data: {chunk['data']}")
```

## Common Patterns

### Reusable Agent Module

```python
def create_specialist_agent(system_prompt: str, tools: list) -> CompiledStateGraph:
    """Factory for creating reusable specialist agents."""
    
    def agent_node(state: MessagesState):
        model_with_tools = model.bind_tools(tools)
        response = model_with_tools.invoke([
            {"role": "system", "content": system_prompt},
            *state["messages"],
        ])
        return {"messages": [response]}
    
    def should_continue(state: MessagesState) -> str:
        if state["messages"][-1].tool_calls:
            return "tools"
        return END
    
    builder = StateGraph(MessagesState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", should_continue)
    builder.add_edge("tools", "agent")
    
    return builder.compile()

# Create and compose
research_agent = create_specialist_agent("You are a researcher.", [search_tool])
writing_agent = create_specialist_agent("You are a writer.", [])

parent = StateGraph(MessagesState)
parent.add_node("research", research_agent)
parent.add_node("writing", writing_agent)
parent.add_edge(START, "research")
parent.add_edge("research", "writing")
parent.add_edge("writing", END)
```

### Conditional Subgraph Selection

```python
def route_to_subgraph(state: State) -> str:
    if state["task_type"] == "analysis":
        return "analysis_subgraph"
    elif state["task_type"] == "generation":
        return "generation_subgraph"
    return "simple_handler"

parent.add_conditional_edges("classifier", route_to_subgraph)
```

## Common Pitfalls

1. **Forgetting parent checkpointer** — Subgraph interrupts only work if the parent has a checkpointer.
2. **State key conflicts** — Shared keys use the parent's reducer. Ensure reducers are compatible.
3. **Deep nesting performance** — Each nesting level adds overhead. Keep it to 2-3 levels max.
4. **Assuming shared memory** — Subgraphs don't automatically share the parent's store. Pass it explicitly.
5. **Interrupt resume in subgraphs** — Both parent and subgraph nodes restart fully on resume.

---

> **Related:** [10-multi-agent.md](10-multi-agent.md) for multi-agent patterns, [01-graph-api.md](01-graph-api.md) for graph fundamentals
