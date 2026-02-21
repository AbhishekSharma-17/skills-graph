# Chat History

Chat history provides conversation continuity by loading previous turns into agent context. Agno supports three access patterns (automatic, on-demand, programmatic), fine-grained controls over size and tool call filtering, session summaries for long-term memory, and team-level history sharing.


## Contents

- [Docs Hierarchy](#docs-hierarchy)
- [How Chat History Works](#how-chat-history-works)
- [Agent Chat History Parameters](#agent-chat-history-parameters)
- [Pattern 1: Automatic History (For Agents)](#pattern-1-automatic-history-for-agents)
- [Pattern 2: On-Demand History (Agent Tools)](#pattern-2-on-demand-history-agent-tools)
- [Pattern 3: Programmatic Access](#pattern-3-programmatic-access)
- [Cross-Session Search](#cross-session-search)
- [Managing Tool Calls from History](#managing-tool-calls-from-history)
- [Team Chat History](#team-chat-history)
- [Session Summaries (Long-Term Memory)](#session-summaries-long-term-memory)
- [Token Growth Without History Control](#token-growth-without-history-control)
- [Token Tracking](#token-tracking)
- [Choosing History Strategy](#choosing-history-strategy)

## Docs Hierarchy

```
Chat History
├── Overview (/history/overview)
├── For Agents
│   ├── Overview (/history/agent/overview)
│   └── Chat History (/history/agent/chat-history)
├── For Teams
│   ├── Overview (/history/team/overview)
│   ├── Direct Response + History (/history/team/respond-directly-with-history)
│   ├── Team History (/history/team/team-history)
│   ├── Member History (/history/team/history-of-members)
│   └── Share Member Interactions (/history/team/share-member-interactions)
└── For Workflows
```

## How Chat History Works

1. Agent receives a message and a `session_id`
2. Agno loads previous runs from the database for that session
3. History is added to context (controlled by `num_history_runs` or `num_history_messages`)
4. Agent responds with full conversation awareness
5. New run is saved to database

---

## Agent Chat History Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `add_history_to_context` | `bool` | `False` | Automatically include previous messages in every request |
| `num_history_runs` | `int` | `3` | Number of previous runs (turns) to include |
| `num_history_messages` | `int` | `None` | Max messages to include across all runs (alternative to runs) |
| `max_tool_calls_from_history` | `int` | `None` | Limit tool call messages kept in history |
| `read_chat_history` | `bool` | `False` | Give agent a `get_chat_history()` tool (on-demand access) |
| `read_tool_call_history` | `bool` | `False` | Give agent a `get_tool_call_history()` tool |
| `search_session_history` | `bool` | `False` | Allow searching through previous sessions |
| `num_history_sessions` | `int` | `None` | Number of past sessions to search |
| `db` | `AgnoDb` | `None` | Database for storing/loading history |
| `session_id` | `str` | `None` | Session identifier for history continuity |

---

## Pattern 1: Automatic History (For Agents)

History is automatically loaded and included in every request:

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIResponses

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=SqliteDb(db_file="tmp/agent.db"),
    session_id="chat_history",
    instructions="You are a helpful assistant.",
    add_history_to_context=True,
    num_history_runs=3,  # Last 3 turns
)

agent.print_response("My name is Sarah", stream=True)
agent.print_response("What's my name?", stream=True)
# Agent knows: "Sarah" — because history is automatically included
```

## Pattern 2: On-Demand History (Agent Tools)

Agent decides when to check history by calling a tool:

```python
agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=SqliteDb(db_file="tmp/agent.db"),
    read_chat_history=True,       # Agent gets get_chat_history() tool
    read_tool_call_history=True,  # Agent gets get_tool_call_history() tool
)

# Agent can call get_chat_history() when it needs to recall past conversations
# Agent can call get_tool_call_history() to review what tools were called
```

## Pattern 3: Programmatic Access

Access history directly in code:

```python
# Get user-assistant message pairs
chat_history = agent.get_chat_history(session_id="chat_123")

# Get all messages from the session (including system, tool calls)
messages = agent.get_session_messages(session_id="chat_123")

# Get the last run output with metrics
last_run = agent.get_last_run_output()
```

## Cross-Session Search

Search across previous sessions for relevant context:

```python
agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=SqliteDb(db_file="tmp/agent.db"),
    search_session_history=True,  # Enable cross-session search
    num_history_sessions=2,       # Search last 2 sessions
)
```

---

## Managing Tool Calls from History

Tool calls can be verbose and consume significant tokens. Use `max_tool_calls_from_history` to keep only recent tool results:

```python
import random

def get_weather_for_city(city: str) -> str:
    """Get weather for a city."""
    conditions = ["Sunny", "Cloudy", "Rainy", "Snowy", "Foggy", "Windy"]
    temperature = random.randint(-10, 35)
    condition = random.choice(conditions)
    return f"{city}: {temperature}°C, {condition}"

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[get_weather_for_city],
    db=SqliteDb(db_file="tmp/agent.db"),
    add_history_to_context=True,
    max_tool_calls_from_history=3,  # Keep only last 3 tool calls
)

agent.print_response("What's the weather in Tokyo?")    # Sees: [Tokyo]
agent.print_response("What's the weather in Paris?")    # Sees: [Tokyo, Paris]
agent.print_response("What's the weather in London?")   # Sees: [Tokyo, Paris, London]
agent.print_response("What's the weather in Berlin?")   # Sees: [Paris, London, Berlin] — Tokyo filtered
agent.print_response("What's the weather in Mumbai?")   # Sees: [London, Berlin, Mumbai] — filtered
```

**Important:** `max_tool_calls_from_history` filters tool calls from runs loaded by `num_history_runs`. The database always retains complete history.

---

## Team Chat History

Teams have additional history parameters for sharing context across members:

### Team History Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `add_history_to_context` | `bool` | `False` | Include team-level history |
| `num_history_runs` | `int` | `3` | Team-level runs to include |
| `add_team_history_to_members` | `bool` | `False` | Share team history with member agents |
| `num_team_history_runs` | `int` | `3` | Number of team-level runs to share with members |
| `share_member_interactions` | `bool` | `False` | Members can see each other's interactions |

### Team with Shared History

```python
from agno.team import Team
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIResponses

researcher = Agent(name="Researcher", model=OpenAIResponses(id="gpt-5.2"))
writer = Agent(name="Writer", model=OpenAIResponses(id="gpt-5.2"))

team = Team(
    name="ContentTeam",
    model=OpenAIResponses(id="gpt-5.2"),
    members=[researcher, writer],
    db=SqliteDb(db_file="tmp/team.db"),
    add_history_to_context=True,
    num_history_runs=3,
    add_team_history_to_members=True,  # Members see team-level history
)
```

### Direct Response with History

When a team uses `respond_directly=True`, team-level history ensures continuity:

```python
team = Team(
    name="SupportTeam",
    model=OpenAIResponses(id="gpt-5.2"),
    members=[billing_agent, tech_agent],
    db=SqliteDb(db_file="tmp/team.db"),
    respond_directly=True,
    add_history_to_context=True,
    num_history_runs=5,
)
```

### Share Member Interactions

Members can see what other members have done in the current run:

```python
team = Team(
    name="CollabTeam",
    model=OpenAIResponses(id="gpt-5.2"),
    members=[agent_a, agent_b],
    share_member_interactions=True,  # Agent B sees what Agent A did
)
```

---

## Session Summaries (Long-Term Memory)

For long conversations, combine limited history with session summaries:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_session_summaries` | `bool` | `False` | Generate rolling summary after each run |
| `add_session_summary_to_context` | `bool` | `False` | Inject summary into system message |

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.sqlite import SqliteDb

agent = Agent(
    name="efficient_support",
    model=OpenAIChat(id="gpt-5-mini"),
    db=SqliteDb(db_file="tmp/agent.db"),
    add_history_to_context=True,
    num_history_runs=3,
    enable_session_summaries=True,
    add_session_summary_to_context=True,
    instructions=[
        "Focus on current query",
        "Reference history only when directly relevant",
        "Avoid repeating previously stated information",
    ],
)
```

**Combined effect:**

- **Summary** → Long-term memory (condensed overview of entire conversation)
- **Last N runs** → Short-term memory (full messages for immediate context)
- **Result** → Full awareness at a fraction of the token cost

The summary is stored in the `summary` field of the session record in `agno_sessions` table.

---

## Token Growth Without History Control

| Component | Cumulative Tokens | Notes |
|-----------|-------------------|-------|
| System Prompt | 1,200 | Static |
| + User Message | 2,500 | |
| + LLM Response | 4,000 | |
| + Run 2 (full history) | 8,000 | Doubles |
| + Run 3 (full history) | 16,000 | Doubles again |
| + Run 10 | 100,000+ | Unsustainable |

**With `num_history_runs=3` + summaries:** Stays under 10,000 tokens consistently.

## Token Tracking

Monitor token usage per run and per session:

```python
# Per-run metrics
response = agent.run("What is AI?", session_id="s1")
print(f"Input:  {response.metrics.input_tokens}")
print(f"Output: {response.metrics.output_tokens}")
print(f"Total:  {response.metrics.total_tokens}")
print(f"Cache write: {response.metrics.cache_write_tokens}")
print(f"Cache read:  {response.metrics.cache_read_tokens}")

# Per-session metrics (cumulative across all runs)
session_metrics = agent.get_session_metrics(session_id="s1")
if session_metrics:
    print(f"Session total: {session_metrics.total_tokens}")
```

---

## Choosing History Strategy

| Scenario | Strategy |
|----------|----------|
| Short conversations (<10 turns) | `add_history_to_context=True`, no limits |
| Medium conversations (10-50 turns) | `num_history_runs=5` |
| Long conversations (50+ turns) | `num_history_runs=3` + `enable_session_summaries=True` |
| Tool-heavy agents | Add `max_tool_calls_from_history=3` to any strategy |
| Agent needs to decide when to recall | Use `read_chat_history=True` (on-demand) |
| Cross-session context needed | Add `search_session_history=True` + `num_history_sessions=2` |
| Teams with shared context | Add `add_team_history_to_members=True` |
| Cost-sensitive production | `num_history_runs=2` + summaries + `get_session_metrics` |
