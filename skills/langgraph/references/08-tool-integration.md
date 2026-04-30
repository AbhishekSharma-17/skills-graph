# LangGraph — Tool Integration

> Source: [docs.langchain.com/oss/python/langgraph](https://docs.langchain.com/oss/python/langgraph/overview)

## Table of Contents

- [Tool Basics](#tool-basics)
- [Defining Tools](#defining-tools)
- [Binding Tools to LLMs](#binding-tools-to-llms)
- [ToolNode](#toolnode)
- [Tool Routing](#tool-routing)
- [Tool Error Handling](#tool-error-handling)
- [Structured Tool Output](#structured-tool-output)
- [Dynamic Tool Selection](#dynamic-tool-selection)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

---

## Tool Basics

LangGraph agents call tools via the LLM's tool-calling API. The flow is:
1. LLM receives state (messages + tool definitions)
2. LLM decides to call a tool (returns `tool_calls` in the response)
3. Graph routes to tool execution node
4. Tool results are added to messages
5. LLM sees results and decides next action

```
User → Agent (LLM) → [tool_calls?] → ToolNode → Agent → ... → Response
                   → [no tools]    → END
```

## Defining Tools

### Using @tool Decorator

```python
from langchain_core.tools import tool

@tool
def search_web(query: str) -> str:
    """Search the web for current information."""
    return web_search_api(query)

@tool
def calculate(expression: str) -> float:
    """Evaluate a mathematical expression."""
    return eval(expression)  # Use a safe evaluator in production

@tool
def get_weather(city: str, unit: str = "celsius") -> dict:
    """Get current weather for a city.
    
    Args:
        city: The city name to look up.
        unit: Temperature unit, either 'celsius' or 'fahrenheit'.
    """
    return {"city": city, "temp": 22, "unit": unit}
```

### Using Pydantic Input Schema

```python
from pydantic import BaseModel, Field

class SearchInput(BaseModel):
    query: str = Field(description="The search query")
    max_results: int = Field(default=5, description="Maximum results to return")

@tool(args_schema=SearchInput)
def search(query: str, max_results: int = 5) -> list[dict]:
    """Search a knowledge base."""
    return perform_search(query, max_results)
```

### Using StructuredTool

```python
from langchain_core.tools import StructuredTool

def _multiply(a: int, b: int) -> int:
    return a * b

multiply_tool = StructuredTool.from_function(
    func=_multiply,
    name="multiply",
    description="Multiply two numbers together",
)
```

### Async Tools

```python
@tool
async def fetch_data(url: str) -> dict:
    """Fetch data from a URL."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
```

## Binding Tools to LLMs

LLMs need to know about available tools:

```python
from langchain_anthropic import ChatAnthropic

model = ChatAnthropic(model="claude-sonnet-4-20250514")
tools = [search_web, calculate, get_weather]

# Bind tools to model
model_with_tools = model.bind_tools(tools)

# Use in a node
def agent(state: State):
    response = model_with_tools.invoke(state["messages"])
    return {"messages": [response]}
```

### With Tool Choice

```python
# Force a specific tool
model_with_tools = model.bind_tools(tools, tool_choice="search_web")

# Let LLM decide (default)
model_with_tools = model.bind_tools(tools, tool_choice="auto")

# Force at least one tool call
model_with_tools = model.bind_tools(tools, tool_choice="any")
```

## ToolNode

`ToolNode` is a prebuilt node that executes tool calls from LLM messages:

```python
from langgraph.prebuilt import ToolNode

tools = [search_web, calculate, get_weather]
tool_node = ToolNode(tools)

graph = StateGraph(MessagesState)
graph.add_node("agent", agent)
graph.add_node("tools", tool_node)

graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", should_continue)
graph.add_edge("tools", "agent")
```

**ToolNode behavior:**
- Reads the last message's `tool_calls`
- Executes each tool call
- Returns `ToolMessage` objects with results
- Handles multiple tool calls in parallel

### Custom Tool Executor

```python
def custom_tool_node(state: State):
    messages = state["messages"]
    last_message = messages[-1]
    
    tool_results = []
    for tool_call in last_message.tool_calls:
        tool = tool_map[tool_call["name"]]
        result = tool.invoke(tool_call["args"])
        tool_results.append(
            ToolMessage(
                content=str(result),
                tool_call_id=tool_call["id"],
            )
        )
    
    return {"messages": tool_results}
```

## Tool Routing

Route based on whether the LLM wants to call tools:

```python
from langgraph.graph import END

def should_continue(state: State) -> str:
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END

graph.add_conditional_edges("agent", should_continue)
```

### Route to Specific Tools

```python
def route_tools(state: State) -> str:
    last_message = state["messages"][-1]
    if not last_message.tool_calls:
        return END
    
    tool_name = last_message.tool_calls[0]["name"]
    if tool_name == "dangerous_action":
        return "approval_node"
    return "tools"

graph.add_conditional_edges("agent", route_tools)
```

## Tool Error Handling

### ToolNode Built-in Handling

```python
tool_node = ToolNode(tools, handle_tool_errors=True)
# Returns error message as ToolMessage instead of raising
```

### Custom Error Handling

```python
@tool
def risky_operation(data: str) -> str:
    """Perform an operation that might fail."""
    try:
        return process(data)
    except ValueError as e:
        return f"Error: {e}. Please try with different input."
```

### Retry Pattern

```python
def tool_node_with_retry(state: State):
    last_message = state["messages"][-1]
    results = []
    
    for tool_call in last_message.tool_calls:
        tool = tool_map[tool_call["name"]]
        try:
            result = tool.invoke(tool_call["args"])
        except Exception as e:
            result = f"Tool failed: {e}. The agent should try a different approach."
        
        results.append(ToolMessage(
            content=str(result),
            tool_call_id=tool_call["id"],
        ))
    
    return {"messages": results}
```

## Structured Tool Output

### Return Complex Objects

```python
@tool
def search_documents(query: str) -> list[dict]:
    """Search internal documents.
    
    Returns a list of matching documents with title, content, and score.
    """
    results = vector_store.search(query, k=5)
    return [
        {"title": r.title, "content": r.content, "score": r.score}
        for r in results
    ]
```

### With Artifact Support

```python
from langchain_core.tools import tool

@tool(response_format="content_and_artifact")
def generate_chart(data: list[dict], chart_type: str) -> tuple[str, dict]:
    """Generate a chart from data."""
    chart = create_chart(data, chart_type)
    return (
        f"Generated {chart_type} chart with {len(data)} data points",
        {"chart_data": chart, "type": chart_type},
    )
```

## Dynamic Tool Selection

### Context-Dependent Tools

```python
def agent_with_dynamic_tools(state: State):
    # Select tools based on current state
    available_tools = [search_web]
    
    if state.get("authenticated"):
        available_tools.append(write_database)
    if state.get("admin"):
        available_tools.append(delete_records)
    
    model_with_tools = model.bind_tools(available_tools)
    response = model_with_tools.invoke(state["messages"])
    return {"messages": [response]}
```

### Per-Turn Tool Filtering

```python
def agent(state: State):
    # Don't offer tools if we already have a good answer
    if state.get("confidence", 0) > 0.95:
        response = model.invoke(state["messages"])  # No tools
    else:
        response = model_with_tools.invoke(state["messages"])
    return {"messages": [response]}
```

## Common Patterns

### Tool Call with Confirmation

```python
def agent_node(state: State):
    response = model_with_tools.invoke(state["messages"])
    return {"messages": [response]}

def confirm_node(state: State):
    last_msg = state["messages"][-1]
    tool_call = last_msg.tool_calls[0]
    
    approved = interrupt({
        "tool": tool_call["name"],
        "args": tool_call["args"],
        "question": f"Approve {tool_call['name']}?",
    })
    
    if approved:
        return {}  # Continue to tools
    return {"messages": [AIMessage(content="Action cancelled by user.")]}
```

### Tool Result Summarization

```python
def summarize_tools(state: State):
    tool_messages = [m for m in state["messages"] if isinstance(m, ToolMessage)]
    if len(tool_messages) > 5:
        summary = model.invoke(
            f"Summarize these tool results: {[m.content for m in tool_messages[-5:]]}"
        )
        return {"tool_summary": summary.content}
    return {}
```

## Common Pitfalls

1. **Tool not in bind_tools** — LLM can only call tools it knows about. Always `model.bind_tools(tools)`.
2. **Missing tool_call_id** — `ToolMessage` must include the `tool_call_id` from the original call.
3. **Non-string tool results** — Convert results to strings for `ToolMessage.content`.
4. **Tools without docstrings** — The docstring is sent to the LLM as the tool description. Always include one.
5. **Forgetting tool routing** — After the agent node, add conditional edges to check for `tool_calls`.

---

> **Related:** [09-prebuilt-agents.md](09-prebuilt-agents.md) for pre-made tool-calling agents, [07-human-in-the-loop.md](07-human-in-the-loop.md) for tool approval gates
