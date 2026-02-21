# Agno Teams


## Contents

- [What Are Teams?](#what-are-teams)
- [Team Modes](#team-modes)
- [Coordinate Mode (Default)](#coordinate-mode-default)
- [Route Mode](#route-mode)
- [Broadcast Mode](#broadcast-mode)
- [Tasks Mode](#tasks-mode)
- [Member Roles Matter](#member-roles-matter)
- [Nested Teams](#nested-teams)
- [Model Inheritance](#model-inheritance)
- [Running Teams](#running-teams)
- [Streaming Events](#streaming-events)
- [Delegation & Direct Response](#delegation-direct-response)
- [Storage, Memory & Knowledge](#storage-memory-knowledge)
- [Debugging](#debugging)
- [Constructor Quick Reference](#constructor-quick-reference)
- [Team Methods Reference](#team-methods-reference)
- [Full Example: Production Team](#full-example-production-team)

## What Are Teams?

Teams are groups of agents (or sub-teams) that collaborate on complex tasks. A team has a **leader** (orchestrator) and **members** (specialized agents). The leader delegates work based on the chosen **mode**.

**Use a team when:** task needs multiple specialized agents, single agent's context overflows, or you want parallel processing.

**Use a single agent when:** task fits one domain, you want minimal token cost, or you're still prototyping.

---

## Team Modes

| Mode | How It Works | Token Cost | Best For |
|------|-------------|-----------|----------|
| **Coordinate** | Leader selects members, crafts tasks, synthesizes results | High | Decomposition, synthesis, quality |
| **Route** | Leader picks ONE member, returns their response directly | Low | Routing, dispatch, low latency |
| **Broadcast** | Same task sent to ALL members, leader synthesizes | Medium | Multiple perspectives, parallel research |
| **Tasks** | Leader builds task list, iterates until goal complete | Very High | Multi-step pipelines with dependencies |

---

## Coordinate Mode (Default)

Leader decomposes → delegates to selected members → synthesizes results.

```python
from agno.team import Team
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.team.mode import TeamMode

researcher = Agent(
    name="Researcher",
    role="Research specialist who finds and summarizes information",
    model=OpenAIResponses(id="gpt-4o"),
    instructions=["Provide clear, factual summaries", "Cite limitations"],
)

writer = Agent(
    name="Writer",
    role="Content writer who crafts polished, engaging text",
    model=OpenAIResponses(id="gpt-4o"),
    instructions=["Transform raw info into readable text", "Use headers and clear prose"],
)

team = Team(
    name="Research & Writing Team",
    mode=TeamMode.coordinate,
    model=OpenAIResponses(id="gpt-4o"),
    members=[researcher, writer],
    instructions=[
        "For informational requests, ask Researcher to gather facts first,",
        "then ask Writer to polish findings into a final piece.",
    ],
    markdown=True,
    show_members_responses=True,
)

team.print_response("Write an overview of how LLMs are trained", stream=True)
```

---

## Route Mode

Leader picks the best single member → passes request → returns their response directly (no synthesis).

```python
from agno.team.mode import TeamMode

english_agent = Agent(
    name="English Agent",
    role="Responds only in English",
    instructions=["Always respond in English"],
)

spanish_agent = Agent(
    name="Spanish Agent",
    role="Responds only in Spanish",
    instructions=["Always respond in Spanish"],
)

team = Team(
    name="Language Router",
    mode=TeamMode.route,
    model=OpenAIResponses(id="gpt-4o"),
    members=[english_agent, spanish_agent],
    instructions=["Detect language and route to matching agent. Default to English."],
    markdown=True,
)

team.print_response("What is the capital of France?", stream=True)
team.print_response("Cual es la capital de Francia?", stream=True)
```

**Key parameter:** `determine_input_for_members=False` passes user input through unchanged (skips leader reformulation).

---

## Broadcast Mode

Same task → ALL members in parallel → leader synthesizes all perspectives.

```python
import asyncio
from agno.team.mode import TeamMode

optimist = Agent(
    name="Optimist",
    role="Focuses on opportunities and positive outcomes",
    instructions=["Emphasize upsides, growth potential, and positive trends"],
)

pessimist = Agent(
    name="Pessimist",
    role="Focuses on risks and potential downsides",
    instructions=["Identify what could go wrong and why caution is warranted"],
)

realist = Agent(
    name="Realist",
    role="Provides balanced, pragmatic analysis",
    instructions=["Weigh both opportunities and risks objectively"],
)

team = Team(
    name="Multi-Perspective Team",
    mode=TeamMode.broadcast,
    model=OpenAIResponses(id="gpt-4o"),
    members=[optimist, pessimist, realist],
    instructions=["Synthesize all viewpoints into a balanced summary"],
    markdown=True,
    show_members_responses=True,
)

# Use async for parallel execution — big latency win with broadcast
asyncio.run(team.aprint_response("Should a startup pivot from B2C to B2B?", stream=True))
```

---

## Tasks Mode

Leader decomposes goal into a task list → assigns to members → iterates until complete.

```python
from agno.team.mode import TeamMode

planner = Agent(
    name="Planner",
    role="Creates outlines and structures for content",
    instructions=["Create clear, logical outlines", "Break complex topics into sections"],
)

writer = Agent(
    name="Writer",
    role="Writes polished content based on outlines",
    instructions=["Write engaging content following the provided structure"],
)

editor = Agent(
    name="Editor",
    role="Reviews and improves content for clarity",
    instructions=["Review for clarity, grammar, flow", "Provide improved version directly"],
)

team = Team(
    name="Content Pipeline",
    mode=TeamMode.tasks,
    model=OpenAIResponses(id="gpt-4o"),
    members=[planner, writer, editor],
    instructions=[
        "1. Task Planner to outline the content",
        "2. Task Writer to draft based on outline",
        "3. Task Editor to polish the draft",
    ],
    max_iterations=10,
    markdown=True,
    show_members_responses=True,
)

team.print_response("Create a blog post: microservices vs monolith architecture")
```

---

## Member Roles Matter

The leader routes based on roles. Vague roles = wrong routing.

```python
# Bad — roles are vague
agent1 = Agent(name="Agent 1", role="Research things")
agent2 = Agent(name="Agent 2", role="Look stuff up")

# Good — roles are specific and distinct
news_agent = Agent(name="News Agent", role="Get tech news from HackerNews")
finance_agent = Agent(name="Finance Agent", role="Get stock prices from Yahoo Finance")
```

---

## Nested Teams

Teams can contain sub-teams. Top-level leader delegates to sub-team leaders.

```python
team = Team(
    name="Language Team",
    members=[
        Agent(name="English Agent", role="Answer in English"),
        Agent(name="Chinese Agent", role="Answer in Chinese"),
        Team(
            name="Germanic Team",
            role="Handle German and Dutch questions",
            members=[
                Agent(name="German Agent", role="Answer in German"),
                Agent(name="Dutch Agent", role="Answer in Dutch"),
            ],
        ),
    ],
)
```

---

## Model Inheritance

Members without a `model` inherit from their parent team:

```python
from agno.models.anthropic import Claude

# Uses its own model
claude_agent = Agent(name="Claude Agent", model=Claude(id="claude-sonnet-4-5"), role="Research")

# Inherits gpt-4o from team
inherited_agent = Agent(name="GPT Agent", role="Write content")

team = Team(
    model=OpenAIResponses(id="gpt-4o"),  # Default for team + members without model
    members=[claude_agent, inherited_agent],
)
```

---

## Running Teams

```python
# Sync
response = team.run("Your question")
print(response.content)

# Async (parallel member execution)
response = await team.arun("Your question")

# Streaming
team.print_response("Your question", stream=True)

# With session/user tracking
team.print_response("Hello!", session_id="s1", user_id="u1", stream=True)

# Access results
response = team.run("Your question")
response.content            # Final text
response.metrics            # Token usage, timing
response.member_responses   # Individual member responses
```

---

## Streaming Events

```python
from agno.team import TeamRunEvent

stream = team.run("Research AI trends", stream=True, stream_events=True)
for event in stream:
    if event.event == TeamRunEvent.run_content:
        print(event.content, end="", flush=True)
    elif event.event == TeamRunEvent.tool_call_started:
        print("Tool call started")
    elif event.event == TeamRunEvent.tool_call_completed:
        print("Tool call completed")
```

**Event types:** `TeamRunStarted`, `TeamRunContent`, `TeamRunContentCompleted`, `TeamRunCompleted`, `TeamRunError`, `TeamToolCallStarted`, `TeamToolCallCompleted`, `TeamReasoningStarted`, `TeamReasoningStep`, `TeamReasoningCompleted`, `TeamMemoryUpdateStarted`, `TeamMemoryUpdateCompleted`.

Control member events: `stream_member_events=False` on the Team to suppress.

---

## Delegation & Direct Response

### Default delegation flow
1. Team receives input → 2. Leader analyzes → 3. Leader selects members → 4. Leader formulates tasks → 5. Members execute → 6. Leader synthesizes

### Legacy flags (prefer `mode=` instead)
```python
# Legacy                              # Modern equivalent
respond_directly=True                 # mode=TeamMode.route
delegate_to_all_members=True          # mode=TeamMode.broadcast
determine_input_for_members=False     # Pass user input unchanged to member
```

### Structured input to members
```python
from pydantic import BaseModel

class ResearchRequest(BaseModel):
    topic: str
    num_sources: int = 5

team = Team(
    members=[research_agent],
    determine_input_for_members=False,  # Pass structured input directly
)
team.print_response(input=ResearchRequest(topic="AI Agents", num_sources=10))
```

---

## Storage, Memory & Knowledge

Teams support all the same persistence features as agents:

```python
from agno.db.sqlite import SqliteDb

team = Team(
    members=[...],
    model=OpenAIResponses(id="gpt-4o"),

    # Storage
    db=SqliteDb(db_file="team.db"),
    add_history_to_context=True,
    num_history_runs=3,

    # Memory
    enable_agentic_memory=True,
    add_memories_to_context=True,

    # Knowledge
    knowledge=knowledge_base,
    search_knowledge=True,

    # Context
    add_datetime_to_context=True,
)

# Session management
team.get_chat_history(session_id="s1")
memories = team.get_user_memories(user_id="u1")
```

---

## Debugging

### Enable debug mode
```python
# On the team (all runs)
team = Team(members=[...], debug_mode=True)

# Single run
team.print_response("Test", debug_mode=True, show_members_responses=True)

# Globally via env var
# AGNO_DEBUG=True
```

### Common issues and fixes

| Issue | Fix |
|-------|-----|
| Wrong member selected | Make roles more specific and distinct |
| Member fails silently | Use `show_members_responses=True` to inspect |
| Infinite delegation | Add instructions: "Do not delegate more than 3 times" |
| High token usage | Switch to `route` mode, limit history, check `response.metrics` |
| Slow execution | Use `await team.arun()` for parallel, or switch to `route` mode |

### Systematic debug steps
```python
# 1. Check roles
for m in team.members:
    print(f"{m.name}: {m.role}")

# 2. See leader decisions
team.print_response("Test", debug_mode=True)

# 3. Inspect member responses
team.print_response("Test", show_members_responses=True)

# 4. Monitor tokens
response = team.run("Test")
print(f"Tokens: {response.metrics.total_tokens}")
```

---

## Constructor Quick Reference

### Team Identity & Metadata

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `Optional[str]` | `None` | Team name — used for identification, logging, and tracing |
| `id` | `Optional[str]` | `None` | Team UUID — auto-generated if not set. Used for tracking and registry |
| `description` | `Optional[str]` | `None` | Description of the team added to the **start** of the system message. Sets the leader's persona |
| `role` | `Optional[str]` | `None` | Role of the team when used as a member inside a parent team (nested teams) |
| `metadata` | `Optional[Dict[str, Any]]` | `None` | Arbitrary metadata stored with the team — useful for tagging, filtering, and organization |

### Members & Hierarchy

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `members` | `List[Union[Agent, Team]]` | Required | List of agents or sub-teams that make up this team |
| `parent_team_id` | `Optional[str]` | `None` | ID of parent team — auto-set when this team is a member of another team |
| `workflow_id` | `Optional[str]` | `None` | Workflow ID — auto-set when the team is part of a workflow |

### Model

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `Optional[Union[Model, str]]` | `None` | LLM for the team leader. Accepts a Model object or model string (`"openai:gpt-4o"`). Members without a model **inherit** this |

### Team Mode & Delegation

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `mode` | `Optional[TeamMode]` | `None` | Team coordination mode: `TeamMode.coordinate`, `TeamMode.route`, `TeamMode.broadcast`, or `TeamMode.tasks`. Overrides legacy delegation flags |
| `determine_input_for_members` | `bool` | `True` | If True, the leader reformulates the user input into a task for each member. Set False to pass user input unchanged |
| `respond_directly` | `bool` | `False` | **Legacy** — If True, return member response directly without leader synthesis. Use `mode=TeamMode.route` instead |
| `delegate_to_all_members` | `bool` | `False` | **Legacy** — If True, delegate to all members. Use `mode=TeamMode.broadcast` instead. If both this and `respond_directly=True`, broadcast wins |
| `max_iterations` | `int` | `10` | Maximum iterations for `mode=TeamMode.tasks` autonomous loop before stopping |
| `member_timeout` | `Optional[float]` | `None` | Timeout in seconds for individual member delegations. Prevents hanging on slow members |

### System Message & Instructions

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `system_message` | `Optional[Union[str, Callable, Message]]` | `None` | Override the auto-built system message entirely. Can be a string, callable, or Message object |
| `system_message_role` | `str` | `"system"` | Role label for the system message (some models require `"developer"`) |
| `instructions` | `Optional[Union[str, List[str], Callable]]` | `None` | Behavioral guidelines for the team leader. List recommended. Supports `{state_var}` template variables |
| `use_instruction_tags` | `bool` | `False` | If True, wraps instructions in `<instructions>` XML tags in the system message |
| `introduction` | `Optional[str]` | `None` | Introduction message for the team — greeting or orientation shown at session start |
| `expected_output` | `Optional[str]` | `None` | Describe expected output format/content. Added to system message to guide the leader's final response |
| `additional_context` | `Optional[str]` | `None` | Extra context appended to the **end** of the system message |
| `markdown` | `bool` | `False` | If True, adds instructions to format output using markdown |

### Context Building

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `add_name_to_context` | `bool` | `False` | If True, adds the team name to the instructions |
| `add_datetime_to_context` | `bool` | `False` | If True, adds current datetime to instructions (gives the leader time awareness) |
| `add_location_to_context` | `bool` | `False` | If True, adds current location to instructions |
| `timezone_identifier` | `Optional[str]` | `None` | Custom timezone for datetime instructions, TZ Database format (e.g. `"America/New_York"`) |
| `add_member_tools_to_context` | `bool` | `False` | If True, adds a summary of tools available to each member into the leader's context (helps routing) |

### User Message & Input

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `input_schema` | `Optional[Type[BaseModel]]` | `None` | Pydantic model to validate input before processing |
| `additional_input` | `Optional[List[Union[str, Dict, BaseModel, Message]]]` | `None` | Extra messages added **after** system message and **before** user message |
| `send_media_to_model` | `bool` | `True` | If False, media (images, videos, audio, files) is only available to tools and **not** sent to the LLM |

### Tools

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tools` | `Optional[List[Union[Toolkit, Callable, Function, Dict]]]` | `None` | Tools available to the team leader (in addition to the delegation tool) |
| `tool_choice` | `Optional[Union[str, Dict[str, Any]]]` | `None` | Controls which tool the leader calls. `"auto"`, `"none"`, `"required"`, or force a specific tool |
| `tool_call_limit` | `Optional[int]` | `None` | Maximum tool calls per run. Prevents runaway delegation loops |
| `max_tool_calls_from_history` | `Optional[int]` | `None` | Max tool call messages to keep from history (trims old tool results) |
| `tool_hooks` | `Optional[List[Callable]]` | `None` | Functions executed between tool calls — useful for logging or validation mid-run |
| `get_member_information_tool` | `bool` | `False` | If True, adds a built-in tool that lets the leader query member capabilities |

### Knowledge & Retrieval

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `knowledge` | `Optional[Union[Knowledge, Callable]]` | `None` | Knowledge base for RAG — can be a Knowledge instance or a callable factory |
| `search_knowledge` | `bool` | `True` | Adds a built-in tool for the leader to search the knowledge base on demand (Agentic RAG) |
| `add_search_knowledge_instructions` | `bool` | `True` | If True, adds instructions about knowledge search to the system prompt |
| `update_knowledge` | `bool` | `False` | Adds a built-in tool for the leader to write to the knowledge base |
| `add_knowledge_to_context` | `bool` | `False` | Always inject knowledge references into the user prompt (Traditional RAG) |
| `knowledge_filters` | `Optional[Union[Dict[str, Any], List[FilterExpr]]]` | `None` | Static filters applied to every knowledge search |
| `enable_agentic_knowledge_filters` | `Optional[bool]` | `False` | Let the leader dynamically choose knowledge filters based on the query |
| `knowledge_retriever` | `Optional[Callable[..., Optional[List[Union[Dict, str]]]]]` | `None` | Custom retrieval function — replaces default knowledge search |
| `references_format` | `Literal["json", "yaml"]` | `"json"` | Format for knowledge references injected into context |

### Output & Parsing

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `output_schema` | `Optional[Union[Type[BaseModel], Dict[str, Any]]]` | `None` | Pydantic model or JSON schema for structured output from the team leader |
| `use_json_mode` | `bool` | `False` | If `output_schema` is set, forces the model to respond in JSON mode |
| `parse_response` | `bool` | `True` | If True, the response is automatically parsed into the `output_schema` |
| `parser_model` | `Optional[Union[Model, str]]` | `None` | Secondary model to parse/transform the leader's response into the output schema |
| `parser_model_prompt` | `Optional[str]` | `None` | Custom prompt for the parser model |
| `output_model` | `Optional[Union[Model, str]]` | `None` | Alternative model to structure/format the leader's response |
| `output_model_prompt` | `Optional[str]` | `None` | Custom prompt for the output model |

### Database & Storage

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db` | `Optional[Union[BaseDb, AsyncBaseDb]]` | `None` | Database backend for persistence — SqliteDb, PostgresDb, MongoDb, etc. Supports both sync and async backends |
| `store_media` | `bool` | `True` | If True, stores media content in the database alongside messages |
| `store_tool_messages` | `bool` | `True` | If True, stores tool call results in the database |
| `store_history_messages` | `bool` | `False` | If True, stores full chat history messages in the database |

### Session & User

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `session_id` | `Optional[str]` | `None` | Session identifier — auto-generated UUID if not set |
| `user_id` | `Optional[str]` | `None` | User identifier — used for memory isolation and multi-user scenarios |
| `session_state` | `Optional[Dict[str, Any]]` | `None` | Persistent state dict stored in the database. Survives across runs. Accessible via `{key}` in instructions |
| `add_session_state_to_context` | `bool` | `False` | If True, adds the full session_state dict to the context |
| `enable_agentic_state` | `bool` | `False` | Gives the team leader tools to update session_state dynamically during runs |
| `overwrite_db_session_state` | `bool` | `False` | If True, overwrites stored session_state instead of merging |
| `cache_session` | `bool` | `False` | If True, caches the current session in memory for faster access |

### History & Chat

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `add_history_to_context` | `bool` | `False` | Includes chat history of the current session in messages sent to the leader |
| `num_history_runs` | `Optional[int]` | `None` | Number of past runs to include in the leader's history |
| `num_history_messages` | `Optional[int]` | `None` | Number of individual history messages to include (finer control than `num_history_runs`) |
| `read_chat_history` | `bool` | `False` | Adds a built-in tool that lets the leader read the full chat history on demand |
| `search_session_history` | `Optional[bool]` | `False` | If True, allows searching through **previous** sessions (cross-session history) |
| `num_history_sessions` | `Optional[int]` | `None` | Number of past sessions to include in cross-session search |

### Member Interaction & History Sharing

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `add_team_history_to_members` | `bool` | `False` | If True, sends team-level conversation history to members when delegating (not agent-level history) |
| `num_team_history_runs` | `int` | `3` | Number of team historical runs to include when sharing history with members |
| `share_member_interactions` | `bool` | `False` | If True, sends all previous member interactions to each member when delegating a new task |

### Memory

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_agentic_memory` | `bool` | `False` | Gives the leader tools to create/update/delete user memories |
| `enable_user_memories` | `Optional[bool]` | `None` | **Deprecated** — use `update_memory_on_run` instead |
| `update_memory_on_run` | `bool` | `False` | If True, creates/updates user memories at the end of every run |
| `add_memories_to_context` | `Optional[bool]` | `None` | If True, injects stored user memories into the leader's context |
| `memory_manager` | `Optional[MemoryManager]` | `None` | Custom MemoryManager instance for advanced memory configuration |

### Session Summaries

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_session_summaries` | `bool` | `False` | Creates/updates a running summary at the end of each run |
| `add_session_summary_to_context` | `Optional[bool]` | `None` | If True, injects the session summary into the leader's context |
| `session_summary_manager` | `Optional[SessionSummaryManager]` | `None` | Custom SessionSummaryManager for advanced summary configuration |

### Learning

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `learning` | `Optional[Union[bool, LearningMachine]]` | `None` | Enable unified learning capabilities — LearningMachine manages user profiles, session context, entity memory, learned knowledge, and decision logs |
| `add_learnings_to_context` | `bool` | `True` | If True, adds learning context to the system prompt |

### Compression

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `compress_tool_results` | `bool` | `False` | If True, compresses tool call results to save context window space |
| `compression_manager` | `Optional[CompressionManager]` | `None` | Custom CompressionManager for controlling how tool results are compressed |

### Dependencies

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dependencies` | `Optional[Dict[str, Any]]` | `None` | Runtime dependencies available to tools and prompt functions via RunContext |
| `add_dependencies_to_context` | `bool` | `False` | If True, adds dependencies dict to the user prompt |

### Reasoning

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `reasoning` | `bool` | `False` | Enable step-by-step reasoning for the team leader before delegating |
| `reasoning_model` | `Optional[Union[Model, str]]` | `None` | Separate model for the reasoning phase |
| `reasoning_agent` | `Optional[Agent]` | `None` | Full Agent instance used for reasoning — allows tools and knowledge during the reasoning phase |
| `reasoning_min_steps` | `int` | `1` | Minimum reasoning steps before the leader can act |
| `reasoning_max_steps` | `int` | `10` | Maximum reasoning steps (prevents infinite reasoning) |

### Hooks & Guardrails

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `pre_hooks` | `Optional[List[Union[Callable, BaseGuardrail, BaseEval]]]` | `None` | Functions/guardrails/evals called **before** processing starts. Use for input validation, PII detection |
| `post_hooks` | `Optional[List[Union[Callable, BaseGuardrail, BaseEval]]]` | `None` | Functions/guardrails/evals called **after** the response is generated but **before** it's returned |

### Streaming & Events

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `stream` | `Optional[bool]` | `None` | Default streaming mode for this team. Can be overridden per-run |
| `stream_events` | `Optional[bool]` | `None` | Stream intermediate events (tool calls, delegation, reasoning) in addition to the final response |
| `stream_member_events` | `bool` | `True` | Stream events from member agents. Set False to suppress member-level events |
| `store_events` | `bool` | `False` | Persist events on the RunResponse object for later inspection |
| `events_to_skip` | `Optional[List[Union[RunEvent, TeamRunEvent]]]` | `None` | List of event types to exclude when storing events |
| `store_member_responses` | `bool` | `False` | Store full member RunResponse objects inside the team's RunOutput |

### Retry & Resilience

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `retries` | `int` | `0` | Number of retry attempts when a run fails |
| `delay_between_retries` | `int` | `1` | Delay in seconds between retry attempts |
| `exponential_backoff` | `bool` | `False` | If True, doubles the delay between each retry (1s → 2s → 4s → 8s...) |

### Debug & Telemetry

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `debug_mode` | `bool` | `False` | Enable detailed debug logging — shows leader decisions, member routing, delegation details |
| `debug_level` | `Literal[1, 2]` | `1` | Debug verbosity: `1` = standard, `2` = verbose (full message payloads) |
| `show_members_responses` | `bool` | `False` | Show individual member responses in output. Also enables debug_mode for the team and all members |
| `telemetry` | `bool` | `True` | Log minimal anonymous telemetry. Set False to opt out |

### Caching (Callable Factories)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cache_callables` | `bool` | `True` | Enable caching of callable factory results (for dynamic tools, knowledge, members) |
| `callable_tools_cache_key` | `Optional[Callable[..., Optional[str]]]` | `None` | Custom cache key function for tools callable factory |
| `callable_knowledge_cache_key` | `Optional[Callable[..., Optional[str]]]` | `None` | Custom cache key function for knowledge callable factory |
| `callable_members_cache_key` | `Optional[Callable[..., Optional[str]]]` | `None` | Custom cache key function for members callable factory |

---

## Team Mode Details

### Coordinate Mode
- **Flow:** Leader analyzes → selects members → formulates tasks → members execute → leader synthesizes
- **Token Cost:** High (decomposition + synthesis)
- **Latency:** Sequential (leader → members → leader)
- **Best For:** Quality output, multi-step decomposition, nuanced synthesis

### Route Mode
- **Flow:** Leader selects ONE member → passes request → returns their response directly
- **Token Cost:** Low (selection only, no synthesis)
- **Latency:** Fast (no synthesis step)
- **Best For:** Specialized routing, dispatch, low-latency responses
- **Tip:** Use `determine_input_for_members=False` to pass user input unchanged

### Broadcast Mode
- **Flow:** Leader sends same task to ALL members → collects results → synthesizes
- **Token Cost:** Medium (all members run, but synthesis is straightforward)
- **Latency:** Parallel member execution with `await team.arun()`, synthesis adds latency
- **Best For:** Multiple perspectives, parallel research, consensus building
- **Note:** If both `delegate_to_all_members=True` AND `respond_directly=True`, broadcast wins

### Tasks Mode
- **Flow:** Leader decomposes goal → creates task list → delegates → checks completion → iterates
- **Token Cost:** Very High (planning + iterative loop)
- **Latency:** Multiple cycles, up to `max_iterations`
- **Best For:** Multi-step pipelines with dependencies, autonomous task management
- **Key Parameter:** `max_iterations` controls loop limit (default 10)

---

## Team Methods Reference

### Running

| Method | Description |
|--------|-------------|
| `run(input, stream=None, ...)` | Run the team synchronously. Returns `RunResponse` |
| `arun(input, stream=None, ...)` | Run the team asynchronously (enables parallel member execution). Returns `RunResponse` |
| `print_response(input, stream=True, ...)` | Run and print the response to stdout |
| `aprint_response(input, stream=True, ...)` | Async run and print the response |
| `cli_app(...)` | Launch an interactive CLI chat interface |
| `acli_app(...)` | Async interactive CLI interface |

### Session & Memory

| Method | Description |
|--------|-------------|
| `get_chat_history(session_id)` | Get the chat history for a session |
| `get_user_memories(user_id)` | Retrieve all stored memories for a user |

---

## Full Example: Production Team

```python
from agno.team import Team
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.team.mode import TeamMode
from agno.db.sqlite import SqliteDb
from agno.tools.hackernews import HackerNewsTools
from agno.tools.yfinance import YFinanceTools

news_agent = Agent(
    name="News Agent",
    role="Get trending tech news from HackerNews",
    tools=[HackerNewsTools()],
    instructions=["Summarize top stories with links", "Focus on AI and tech"],
)

finance_agent = Agent(
    name="Finance Agent",
    role="Get stock prices and financial data from Yahoo Finance",
    tools=[YFinanceTools(stock_price=True, analyst_recommendations=True)],
    instructions=["Use tables for financial data", "Include analyst consensus"],
)

team = Team(
    name="Market Intelligence",
    mode=TeamMode.coordinate,
    model=OpenAIResponses(id="gpt-4o"),
    members=[news_agent, finance_agent],
    db=SqliteDb(db_file="team.db"),
    add_history_to_context=True,
    num_history_runs=3,
    enable_agentic_memory=True,
    add_memories_to_context=True,
    add_datetime_to_context=True,
    add_member_tools_to_context=True,
    instructions=[
        "Delegate to News Agent for trending stories and Finance Agent for stock data.",
        "Synthesize findings into a cohesive market intelligence brief.",
        "Remember user interests for future queries.",
    ],
    show_members_responses=True,
    markdown=True,
    retries=2,
    exponential_backoff=True,
    tool_call_limit=20,
    member_timeout=60,
)

team.print_response(
    "What's trending in AI and how are NVDA and MSFT doing?",
    stream=True,
    user_id="analyst_1",
)
```
