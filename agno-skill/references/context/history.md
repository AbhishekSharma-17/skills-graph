# Chat History

Chat history gives agents memory of past conversation turns. Agno provides three patterns for managing history, from simple automatic inclusion to programmatic access.

## Pattern 1: Automatic History (Most Common)

Previous messages are automatically included in the model's context:

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.db.sqlite import SqliteDb

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=SqliteDb(db_file="tmp/data.db"),
    add_history_to_context=True,   # Include past messages
    num_history_runs=3,            # Last 3 conversation turns
)

agent.print_response("I'm working on a Python API", session_id="dev")
# Agent now remembers:
agent.print_response("What testing framework should I use?", session_id="dev")
```

## Pattern 2: On-Demand History (Model Decides)

The agent gets a `get_chat_history()` tool and decides when to look up past messages:

```python
agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=SqliteDb(db_file="tmp/data.db"),
    read_chat_history=True,  # Model can call get_chat_history() tool
)
```

This is more efficient for agents that rarely need history — it only loads when the model decides it's relevant.

## Pattern 3: Programmatic Access

Read history in your application code, outside of agent runs:

```python
# All messages excluding those marked as from_history
chat_history = agent.get_chat_history(session_id="session_123")

# User-assistant message pairs from each run
messages = agent.get_session_messages(session_id="session_123")

# Last run output with metrics and tool calls
last_run = agent.get_last_run_output()
```

## Controlling History Size

Fine-tune how much history the model sees:

```python
agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=SqliteDb(db_file="agent.db"),
    add_history_to_context=True,
    num_history_runs=5,               # Include last 5 turns
    num_history_messages=20,          # Cap at 20 messages total
    max_tool_calls_from_history=3,    # Limit tool call results in history
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `add_history_to_context` | `bool` | `False` | Include chat history in context |
| `num_history_runs` | `int` | `None` | Number of past runs to include |
| `num_history_messages` | `int` | `None` | Max total messages to include |
| `max_tool_calls_from_history` | `int` | `None` | Limit tool call results (reduces tokens) |
| `read_chat_history` | `bool` | `False` | Give agent tool to read history on-demand |
| `read_tool_call_history` | `bool` | `False` | Give agent tool to read past tool calls |

## Cross-Session History Search

Allow an agent to search across previous sessions (useful for recall across separate conversations):

```python
agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=SqliteDb(db_file="agent.db"),
    search_session_history=True,
    num_history_sessions=2,  # Keep low (2-3) to manage token cost
)
```

This searches recent sessions for the same `agent_id` and `user_id`.

## Choosing a Pattern

| Use Case | Configuration |
|----------|---------------|
| Short chats (< 10 turns) | `add_history_to_context=True`, `num_history_runs=3` |
| Long-lived threads | Limited history + session summaries (see `summaries.md`) |
| Tool-heavy agents | Add `max_tool_calls_from_history=3` to reduce tokens |
| Audit / debug flows | `read_chat_history=True` (on-demand) |
| Cross-session recall | `search_session_history=True`, `num_history_sessions=2` |
| Minimal memory use | Use session summaries instead of full history |

## Full Example with History

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.db.sqlite import SqliteDb

db = SqliteDb(db_file="tmp/agent.db")

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=db,
    session_id="chat_history_demo",
    instructions="You are a helpful assistant that answers questions about space and oceans.",
    add_history_to_context=True,
    num_history_runs=2,
)

agent.print_response("Where is the Sea of Tranquility?", stream=True)
# Answer: On the Moon...

agent.print_response("What was my first question?", stream=True)
# Answer: You asked about the Sea of Tranquility...
```
