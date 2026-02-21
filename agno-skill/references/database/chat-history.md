# Agno Chat History

## Contents
- [Enable History](#enable-history)
- [Control History Size](#control-history-size)
- [On-Demand History](#on-demand-history)
- [Cross-Session History](#cross-session-history)
- [Programmatic Access](#programmatic-access)
- [Team History](#team-history)
- [Workflow History](#workflow-history)

---

Chat history gives agents context from previous turns in the same session.

## Enable History

```python
agent = Agent(
    db=SqliteDb(db_file="agent.db"),
    add_history_to_context=True,   # Inject history into context
    num_history_runs=3,            # Include last 3 turns
)
```

## Control History Size

```python
agent = Agent(
    db=db,
    add_history_to_context=True,
    num_history_runs=5,                # Number of previous runs to include
    num_history_messages=20,           # Max total messages
    max_tool_calls_from_history=10,    # Limit tool calls in history
)
```

## On-Demand History

Agent decides when to look up history:

```python
agent = Agent(
    db=db,
    read_chat_history=True,  # Agent gets a get_chat_history() tool
)
```

## Cross-Session History

```python
agent = Agent(
    db=db,
    search_session_history=True,
    num_history_sessions=2,  # Search across last 2 sessions
)
```

## Programmatic Access

```python
# Get user-assistant pairs
chat_history = agent.get_chat_history(session_id="chat_1")

# Get all messages
messages = agent.get_session_messages(session_id="chat_1")

# Get last run output with metrics
last_run = agent.get_last_run_output()
```

## Team History

```python
team = Team(
    db=db,
    add_history_to_context=True,
    num_history_runs=3,
    add_team_history_to_members=True,  # Share history with members
)
```

## Workflow History

```python
workflow = Workflow(
    db=db,
    add_workflow_history_to_steps=True,
    num_history_runs=5,
)
```
