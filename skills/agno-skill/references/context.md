# Agno Context & Sessions — Reference Router

> **See Also:** For detailed context engineering (system message construction, chat history controls, compression, dependency injection, few-shot, caching), read `references/context-mgmt.md` (the dedicated Context Management module).

Sessions and context are how Agno agents remember, persist, and reason across multiple interactions. A **session** is a multi-turn conversation identified by `session_id`, containing runs, chat history, state, and summaries. **Context engineering** controls what information the model sees at each turn.

## Hierarchy

```
Session (multi-turn conversation)
├── Runs (individual interactions within a session)
│   ├── Messages (user/assistant)
│   ├── Tool calls & results
│   └── Metrics
├── Session State (persistent key-value data across runs)
├── Chat History (conversation memory)
├── Session Summary (compressed long-term memory)
└── Metadata
```

## Sub-References

Read only what the current task requires:

| Reference | File | Read When |
|-----------|------|-----------|
| **Sessions** | `references/context/sessions.md` | Core session lifecycle — session IDs, runs, multi-user sessions, session caching, naming (manual + auto), accessing messages/runs |
| **Session State** | `references/context/state.md` | Persistent data across runs — RunContext access, agentic state, state in instructions, overwrite vs merge, multi-user state |
| **Chat History** | `references/context/history.md` | Three history patterns (automatic, on-demand, programmatic), controlling history size, cross-session search, tool call limits |
| **Session Summaries** | `references/context/summaries.md` | Token cost reduction for long conversations, enabling summaries, summary + history hybrid, when to use |
| **Context Engineering** | `references/context/context-engineering.md` | Building the system message, user message context, additional context, few-shot learning, context caching, debug mode |
| **Workflow Sessions** | `references/context/workflow-sessions.md` | Workflow-specific sessions (vs agent/team), execution history, step history, workflow session naming |
| **Persistence** | `references/context/persistence.md` | Database backends (Postgres, SQLite, Mongo, DynamoDB, etc.), async support, session table customization, schema |

## Quick Start

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.db.sqlite import SqliteDb

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=SqliteDb(db_file="agent.db"),          # Enable persistence
    add_history_to_context=True,              # Agent remembers conversation
    num_history_runs=3,                       # Last 3 turns
)

# Same session_id = same conversation thread
agent.print_response("I'm building a Python API", session_id="dev_session")
agent.print_response("What testing framework should I use?", session_id="dev_session")
```
