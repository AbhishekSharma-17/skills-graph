# Agno Context Management — Reference Router

Context engineering is the process of designing and controlling what information is sent to the language model. In Agno, agent context consists of four parts:

```
Agent Context
├── System Message (identity, instructions, additional context, expected output)
├── User Message (query + knowledge refs + dependencies)
├── Chat History (conversation turns, tool calls)
└── Additional Input (few-shot examples)
```

## Full Docs Hierarchy

```
Context
├── Overview (/context/overview)
├── Session Management          → See references/context.md
├── State Management            → See references/state.md
├── Context Management
│   ├── Overview (/context/agent/overview)
│   ├── Basic Instructions (/context/agent/instructions)
│   ├── Dynamic Instructions (/context/agent/dynamic-instructions)
│   ├── Instructions via Function (/context/agent/instructions-via-function)
│   ├── Few-Shot Learning (/context/agent/few-shot-learning)
│   ├── Providing Datetime (/context/agent/datetime-instructions)
│   ├── Providing Location (/context/agent/location-instructions)
│   └── Managing Tool Calls (/context/agent/filter-tool-calls-from-history)
├── Chat History
│   ├── Overview (/history/overview)
│   ├── For Agents
│   │   ├── Overview (/history/agent/overview)
│   │   └── Chat History (/history/agent/chat-history)
│   ├── For Teams
│   │   ├── Overview (/history/team/overview)
│   │   ├── Direct Response + History (/history/team/respond-directly-with-history)
│   │   ├── Team History (/history/team/team-history)
│   │   ├── Member History (/history/team/history-of-members)
│   │   └── Share Member Interactions (/history/team/share-member-interactions)
│   └── For Workflows
├── Context Compression BETA
│   ├── Overview (/compression/overview)
│   └── Token Counting (/compression/token-counting)
└── Dependency Injection
    ├── Overview (/dependencies/overview)
    ├── For Agents
    │   ├── Overview (/dependencies/agent/overview)
    │   ├── Add on Run (/dependencies/agent/add-dependencies-run)
    │   ├── Add to Context (/dependencies/agent/add-dependencies-to-context)
    │   └── Access in Tool (/dependencies/agent/access-dependencies-in-tool)
    └── For Teams
        ├── Overview (/dependencies/team/overview)
        ├── Reference Dependencies (/dependencies/team/reference-dependencies)
        ├── Access in Tool (/dependencies/team/access-dependencies-in-tool)
        └── Add on Run (/dependencies/team/add-dependencies-run)
```

## How Context Is Built

1. **System message** — Compiled from `description`, `role`, `instructions`, `additional_context`, `expected_output`, plus auto-injected metadata (datetime, memories, state, summaries)
2. **User message** — The user query, optionally enriched with knowledge base references and dependency data
3. **Chat history** — Previous conversation turns loaded from database, controlled by `num_history_runs` / `num_history_messages`
4. **Additional input** — Few-shot examples via `additional_input` parameter

Static content is placed first in the system message (for prompt caching), dynamic content appended after.

## Sub-References

Read only what the current task requires:

| Reference | File | Read When |
|-----------|------|-----------|
| **System Message** | `references/context-mgmt/system-message.md` | Building agent identity, instructions (basic/dynamic/via function), role, expected output, all `add_*_to_context` flags, system message override, datetime/location, debug mode |
| **Chat History** | `references/context-mgmt/chat-history.md` | Managing conversation history — 3 patterns (automatic/on-demand/programmatic), history size, tool call filtering, team history sharing, session summaries, cross-session search, token tracking |
| **Context Compression** | `references/context-mgmt/context-compression.md` | Compressing verbose tool results (BETA) — CompressionManager, count-based vs token-based triggers, token counting, combining with other controls |
| **Dependency Injection** | `references/context-mgmt/dependency-injection.md` | Injecting external data at runtime — static/callable deps, `add_dependencies_to_context`, accessing in tools via RunContext, agent deps, team deps, per-run deps |
| **Few-Shot & Caching** | `references/context-mgmt/few-shot-caching.md` | Few-shot learning with `additional_input` Message pairs, prompt caching strategies, context caching for cost savings, debug mode |

## Quick Example

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.db.sqlite import SqliteDb

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    # System message construction
    description="You are a famous short story writer asked to write for a magazine",
    instructions=["Always write 2 sentence stories."],
    expected_output="A creative 2-sentence story",
    markdown=True,
    # Context enrichment
    add_datetime_to_context=True,
    add_name_to_context=True,
    # Chat history
    db=SqliteDb(db_file="tmp/agent.db"),
    add_history_to_context=True,
    num_history_runs=3,
    # Debug
    debug_mode=True,  # View compiled system message in logs
)

agent.print_response("Tell me a horror story.", stream=True)
```

## Context-Related Agent Parameters

### System Message & Instructions

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `description` | `Optional[str]` | `None` | Agent identity — placed at the start of system message |
| `role` | `Optional[str]` | `None` | Agent role description |
| `instructions` | `Optional[Union[str, List[str], Callable]]` | `None` | Task-specific instructions (static, list, or dynamic function) |
| `additional_context` | `Optional[str]` | `None` | Extra context appended to system message |
| `expected_output` | `Optional[str]` | `None` | Description of expected output format |
| `system_message` | `Optional[str]` | `None` | Complete system message override (replaces all auto-construction) |

### Context Enrichment Flags

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `add_datetime_to_context` | `bool` | `False` | Include current date/time in system message |
| `add_name_to_context` | `bool` | `False` | Include agent name in system message |
| `add_state_to_context` | `bool` | `False` | Include session state in system message |
| `add_memories_to_context` | `bool` | `True` | Include stored user memories in system message |
| `add_history_to_context` | `bool` | `False` | Include chat history in context |
| `add_session_state_to_context` | `bool` | `False` | Show session state in system prompt |
| `add_dependencies_to_context` | `bool` | `False` | Include dependency data in system message |

### Chat History Controls

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `num_history_runs` | `Optional[int]` | `None` | Number of previous runs to include in history |
| `num_history_messages` | `Optional[int]` | `None` | Number of previous messages to include |
| `filter_tool_calls_from_history` | `bool` | `False` | Remove tool call messages from history |

### Dependency Injection

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dependencies` | `Optional[Dict[str, Any]]` | `None` | Static or callable dependencies injected at runtime |

## RunContext Attributes (Available in Tools)

| Attribute | Type | Description |
|-----------|------|-------------|
| `run_id` | `str` | Unique identifier for the current run |
| `session_id` | `Optional[str]` | Current session ID |
| `user_id` | `Optional[str]` | Current user ID |
| `dependencies` | `Optional[Dict]` | Runtime dependencies injected via `dependencies` parameter |
| `session_state` | `Dict` | Current session state (read/write) |
| `knowledge_filters` | `Optional[Dict]` | Filters for knowledge base queries |
| `metadata` | `Optional[Dict]` | Arbitrary metadata |

```python
from agno.run import RunContext

def my_tool(run_context: RunContext, query: str) -> str:
    """Access context in tools via run_context parameter."""
    user = run_context.user_id
    state = run_context.session_state
    deps = run_context.dependencies
    return f"User: {user}, State: {state}"
```

## Key Imports

```python
from agno.agent import Agent
from agno.team import Team
from agno.run import RunContext                        # Dependencies in tools
from agno.models.message import Message                # Few-shot examples
from agno.compression.manager import CompressionManager  # Context compression
```
