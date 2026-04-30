# LangGraph — Deployment & Production

> Source: [docs.langchain.com/langsmith/deployment](https://docs.langchain.com/langsmith/deployment)

## Table of Contents

- [Deployment Options Overview](#deployment-options-overview)
- [LangGraph Platform](#langgraph-platform)
- [Self-Hosted Deployment](#self-hosted-deployment)
- [LangSmith Integration](#langsmith-integration)
- [Production Checkpointing](#production-checkpointing)
- [Testing Strategies](#testing-strategies)
- [Error Handling](#error-handling)
- [Performance Optimization](#performance-optimization)
- [Monitoring and Observability](#monitoring-and-observability)
- [Common Pitfalls](#common-pitfalls)

---

## Deployment Options Overview

| Option | Description | Best For |
|--------|-------------|----------|
| **LangGraph Cloud (SaaS)** | Fully managed by LangChain | Quick deployment, small teams |
| **BYOC (Bring Your Own Cloud)** | Run in your VPC, managed by LangChain | Data sovereignty with managed service |
| **Self-Hosted** | Full control, your infrastructure | Enterprise, strict compliance |
| **Custom** | Roll your own server | Maximum flexibility |

## LangGraph Platform

LangGraph Platform (now part of LangSmith Deployment) provides production infrastructure for agents:

**Key features:**
- Horizontally scalable task queues for handling bursts
- Long-running agent support with persistent connections
- Built-in streaming endpoints
- Agent versioning and A/B testing
- Human-in-the-loop API endpoints
- LangSmith Studio for visual debugging

### Cloud Deployment

```bash
# Install CLI
pip install langgraph-cli

# Deploy from local directory
langgraph deploy --app ./my_agent

# Or deploy from git repo via LangSmith UI
```

### Configuration File

```yaml
# langgraph.json
{
  "dependencies": ["."],
  "graphs": {
    "my_agent": "./agent.py:graph"
  },
  "env": ".env",
  "python_version": "3.12"
}
```

### BYOC Deployment

Run in your AWS/GCP/Azure VPC:
- Data stays in your environment
- LangChain handles provisioning and updates
- Control plane managed externally, data plane internal

## Self-Hosted Deployment

### FastAPI Integration

```python
from fastapi import FastAPI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from contextlib import asynccontextmanager

app_graph = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global app_graph
    async with await AsyncPostgresSaver.from_conn_string(
        "postgresql://user:pass@localhost:5432/db"
    ) as checkpointer:
        await checkpointer.setup()
        app_graph = graph.compile(checkpointer=checkpointer, store=store)
        yield

app = FastAPI(lifespan=lifespan)

@app.post("/chat")
async def chat(thread_id: str, message: str):
    config = {"configurable": {"thread_id": thread_id}}
    result = await app_graph.ainvoke(
        {"messages": [{"role": "user", "content": message}]},
        config,
    )
    return {"response": result["messages"][-1].content}

@app.post("/chat/stream")
async def chat_stream(thread_id: str, message: str):
    from fastapi.responses import StreamingResponse
    
    config = {"configurable": {"thread_id": thread_id}}
    
    async def generate():
        async for chunk in app_graph.astream(
            {"messages": [{"role": "user", "content": message}]},
            config,
            stream_mode="messages",
        ):
            msg, metadata = chunk
            if msg.content:
                yield f"data: {msg.content}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

### Docker Deployment

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## LangSmith Integration

### Tracing

LangSmith automatically traces LangGraph executions:

```bash
export LANGSMITH_API_KEY="your-key"
export LANGSMITH_PROJECT="my-agent"
export LANGSMITH_TRACING=true
```

All graph executions, node transitions, LLM calls, and tool invocations are traced.

### Evaluation

```python
from langsmith import evaluate

def predict(inputs: dict) -> dict:
    result = agent.invoke({"messages": [{"role": "user", "content": inputs["question"]}]})
    return {"answer": result["messages"][-1].content}

results = evaluate(
    predict,
    data="my-eval-dataset",
    evaluators=[correctness_evaluator, helpfulness_evaluator],
)
```

### LangSmith Studio

Visual debugging environment for LangGraph:
- See graph structure and execution flow
- Set breakpoints visually
- Inspect state at each step
- Replay and time-travel debug
- Test different inputs interactively

## Production Checkpointing

### PostgreSQL Setup

```python
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

pool = AsyncConnectionPool(
    conninfo="postgresql://user:pass@host:5432/db",
    min_size=5,
    max_size=20,
    kwargs={"autocommit": True, "row_factory": dict_row},
)

checkpointer = AsyncPostgresSaver(pool)
await checkpointer.setup()
```

### Connection Management

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_graph():
    async with await AsyncPostgresSaver.from_conn_string(DB_URL) as cp:
        await cp.setup()
        yield graph.compile(checkpointer=cp)
```

## Testing Strategies

### Unit Testing Nodes

```python
import pytest

def test_routing_node():
    state = {"messages": [AIMessage(content="", tool_calls=[{"name": "search"}])]}
    result = should_continue(state)
    assert result == "tools"

def test_routing_no_tools():
    state = {"messages": [AIMessage(content="Hello!")]}
    result = should_continue(state)
    assert result == END
```

### Integration Testing the Graph

```python
@pytest.mark.asyncio
async def test_agent_end_to_end():
    app = graph.compile(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "test-1"}}
    
    result = await app.ainvoke(
        {"messages": [{"role": "user", "content": "What is 2+2?"}]},
        config,
    )
    
    assert "4" in result["messages"][-1].content

@pytest.mark.asyncio
async def test_multi_turn():
    app = graph.compile(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "test-2"}}
    
    await app.ainvoke(
        {"messages": [{"role": "user", "content": "My name is Alice"}]}, config
    )
    result = await app.ainvoke(
        {"messages": [{"role": "user", "content": "What is my name?"}]}, config
    )
    
    assert "alice" in result["messages"][-1].content.lower()
```

### Testing Interrupts

```python
@pytest.mark.asyncio
async def test_interrupt_resume():
    app = graph.compile(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "test-3"}}
    
    result = await app.ainvoke({"input": "data"}, config)
    assert "__interrupt__" in result  # Verify interrupt occurred
    
    # Resume
    result = await app.ainvoke(Command(resume="approved"), config)
    assert result["status"] == "completed"
```

## Error Handling

### Retry Configuration

```python
from langchain_core.runnables import RunnableConfig

config = RunnableConfig(
    max_retries=3,
    retry_delay=1.0,
    configurable={"thread_id": "t1"},
)
```

### Graceful Degradation

```python
def resilient_node(state: State) -> dict:
    try:
        result = external_api_call(state["query"])
        return {"result": result, "error": None}
    except Exception as e:
        return {"result": None, "error": str(e)}

def fallback_router(state: State) -> str:
    if state.get("error"):
        return "fallback_node"
    return "next_node"
```

### Error in Tools

```python
from langgraph.prebuilt import ToolNode

tool_node = ToolNode(tools, handle_tool_errors=True)
# Tool errors become ToolMessage with error content
# Agent sees the error and can retry or adjust
```

## Performance Optimization

- **State size** — Keep state minimal. Store large data externally, reference by ID
- **Parallel nodes** — Use parallel edges for independent operations
- **Node caching** — Cache expensive computations with `CachePolicy`
- **Connection pooling** — Use `psycopg_pool` for database connections
- **Async everywhere** — Use `ainvoke`/`astream` in async applications
- **Recursion limits** — Set appropriate limits to prevent runaway agents
- **Message trimming** — Trim conversation history to fit LLM context windows

## Monitoring and Observability

### Key Metrics

- **Latency per node** — Track via LangSmith traces
- **Tool call success rate** — Monitor tool errors
- **Recursion depth** — Track how many loops agents take
- **Checkpoint storage** — Monitor database size growth
- **Token usage** — Track LLM token consumption per run

### Structured Logging

```python
import structlog

logger = structlog.get_logger()

def monitored_node(state: State) -> dict:
    logger.info("node_executing", node="agent", message_count=len(state["messages"]))
    result = process(state)
    logger.info("node_completed", node="agent", tokens_used=result.get("tokens"))
    return result
```

## Common Pitfalls

1. **InMemorySaver in production** — Always use PostgresSaver or equivalent.
2. **Missing connection pooling** — Single connections don't scale. Use `psycopg_pool`.
3. **No monitoring** — Enable LangSmith tracing for production visibility.
4. **Unbounded state growth** — Implement message trimming and checkpoint cleanup.
5. **Missing error handling** — Production agents must handle LLM failures, tool errors, and timeouts.
6. **No integration tests** — Test the full graph flow, not just individual nodes.

---

> **Related:** [04-persistence-checkpointing.md](04-persistence-checkpointing.md) for checkpointer details, [06-streaming.md](06-streaming.md) for production streaming
