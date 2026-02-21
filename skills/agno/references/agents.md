# Agno Agents


## Contents

- [The Agent Loop](#the-agent-loop)
- [Minimal Agent](#minimal-agent)
- [Agent with Tools](#agent-with-tools)
- [Structured Output](#structured-output)
- [Storage & Sessions](#storage-sessions)
- [Memory](#memory)
- [Knowledge (RAG)](#knowledge-rag)
- [Session State](#session-state)
- [Instructions & Context](#instructions-context)
- [Running & Streaming](#running-streaming)
- [Constructor Quick Reference](#constructor-quick-reference)
- [Full Example: Production Agent](#full-example-production-agent)

## The Agent Loop

An Agent is a stateful control loop around a stateless model:

1. Build context → system message + instructions + history + knowledge + memories
2. Send context + tool definitions to model
3. Model responds with text or tool call(s)
4. Tool calls → execute → return results → back to step 3
5. Text response → return to user

---

## Minimal Agent

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat

agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    description="You are a helpful assistant",
    instructions=["Be concise", "Use markdown"],
    markdown=True,
)
agent.print_response("Hello!", stream=True)
```

**Model options:** `OpenAIChat` (openai), `Claude` (anthropic), `Gemini` (google), `Groq`, `Mistral`, and 40+ more via `agno.models.*`.

---

## Agent with Tools

Tools let agents interact with external systems. Pass functions or Toolkit instances.

### Using built-in toolkits (120+ available)
```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.hackernews import HackerNewsTools
from agno.tools.yfinance import YFinanceTools

agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    tools=[
        HackerNewsTools(),
        YFinanceTools(stock_price=True, analyst_recommendations=True),
    ],
    instructions=["Use tables to display data"],
    show_tool_calls=True,
    markdown=True,
)
agent.print_response("Top AI stories on HackerNews?", stream=True)
```

### Custom tool functions
Agno auto-converts functions to JSON schema for the model. Use docstrings with Args for parameter descriptions.

```python
import random

def get_weather(city: str) -> str:
    """Get current weather for a city.

    Args:
        city (str): The city name.
    """
    conditions = ["sunny", "cloudy", "rainy", "snowy"]
    return f"Weather in {city}: {random.choice(conditions)}, 22°C"

agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    tools=[get_weather],
    show_tool_calls=True,
)
agent.print_response("What's the weather in Tokyo?")
```

### Custom toolkit class
```python
from agno.tools.toolkit import Toolkit

class OrderTools(Toolkit):
    def __init__(self):
        super().__init__(name="OrderTools")
        self.register(self.lookup_order)
        self.register(self.cancel_order)

    def lookup_order(self, order_id: str) -> str:
        """Look up an order by ID.

        Args:
            order_id (str): The order identifier.
        """
        return f"Order {order_id}: shipped, arriving tomorrow"

    def cancel_order(self, order_id: str) -> str:
        """Cancel an order.

        Args:
            order_id (str): The order identifier.
        """
        return f"Order {order_id} cancelled"

agent = Agent(model=OpenAIChat(id="gpt-4o"), tools=[OrderTools()])
```

### Concurrent tool execution
When using async, tools run in parallel automatically:
```python
async_agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    tools=[tool_a, tool_b, tool_c],
)
await async_agent.aprint_response("Run all three checks", stream=True)
```

---

## Structured Output

Use Pydantic models for validated, typed responses.

```python
from pydantic import BaseModel, Field
from typing import List

class MovieReview(BaseModel):
    title: str = Field(description="Movie title")
    rating: float = Field(ge=0, le=10, description="Rating out of 10")
    summary: str = Field(description="One sentence summary")
    pros: List[str] = Field(description="Strengths")
    cons: List[str] = Field(description="Weaknesses")

agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    output_schema=MovieReview,
)

response = agent.run("Review the movie Inception")
review: MovieReview = response.content
print(f"{review.title}: {review.rating}/10")
```

**Nested structures** work naturally — define Pydantic models that reference other models.

**JSON mode fallback** for models without native structured output:
```python
agent = Agent(model=OpenAIChat(id="gpt-4o"), output_schema=MovieReview, use_json_mode=True)
```

---

## Storage & Sessions

Storage gives agents persistence — chat history, session state, and continuity across restarts.

### SQLite (development)
```python
from agno.db.sqlite import SqliteDb

agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    db=SqliteDb(db_file="agent.db"),
    session_id="dev_session",
    add_history_to_context=True,
    num_history_runs=3,
)

agent.print_response("I'm building a Python API")
# Later — agent remembers context:
agent.print_response("What testing framework should I use?")
```

### PostgreSQL (production)
```python
from agno.db.postgres import PostgresDb

agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    db=PostgresDb(db_url="postgresql+psycopg://user:pass@localhost:5432/mydb"),
    add_history_to_context=True,
)
```

### Session summaries (for long conversations)
```python
agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    db=db,
    add_history_to_context=True,
    enable_session_summaries=True,
    add_session_summary_to_context=True,
)
```

---

## Memory

Memory stores learned user facts (preferences, habits) that persist across sessions. Different from chat history — memory is semantic, not chronological.

### Automatic memory (recommended)
Agno extracts and stores memories after each run:
```python
agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    db=SqliteDb(db_file="agent.db"),
    enable_user_memories=True,
    add_memories_to_context=True,
)

agent.print_response("I prefer Python and use VS Code", user_id="dev_user")
# Future sessions: agent recalls preferences automatically
agent.print_response("Suggest a project setup", user_id="dev_user")
```

### Agentic memory (agent decides what to remember)
Agent gets built-in tools to create/update/delete memories:
```python
agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    db=SqliteDb(db_file="agent.db"),
    enable_agentic_memory=True,  # Agent controls memory via tools
)
```

**Important:** Don't enable both `enable_user_memories` and `enable_agentic_memory` — they're mutually exclusive. Agentic takes precedence.

### Retrieving memories
```python
memories = agent.get_user_memories(user_id="dev_user")
```

---

## Knowledge (RAG)

Knowledge gives agents access to documents and domain expertise via vector search.

### Setup with LanceDB
```python
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.lancedb import LanceDb, SearchType
from agno.embedder.openai import OpenAIEmbedder

knowledge = Knowledge(
    vector_db=LanceDb(
        uri="tmp/lancedb",
        table_name="docs",
        search_type=SearchType.hybrid,
        embedder=OpenAIEmbedder(id="text-embedding-3-small", dimensions=1536),
    )
)

# Ingest content
knowledge.insert(url="https://docs.agno.com/introduction.md")
```

### Agent with knowledge
```python
agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    knowledge=knowledge,
    search_knowledge=True,
    instructions=["Search knowledge before answering", "Cite sources"],
)
agent.print_response("What is Agno?")
```

### Agentic RAG (default) vs Traditional RAG
- **Agentic RAG** (`search_knowledge=True`): Agent decides when to search — smarter, fewer unnecessary lookups
- **Traditional RAG**: Always inject context — simpler but less efficient

### Supported vector stores
LanceDB, ChromaDB, PgVector, Pinecone, Qdrant, Weaviate, Milvus, and 14+ more.

---

## Session State

Persistent state that tools can read and write, surviving across conversations.

```python
from agno.run import RunContext

def add_item(run_context: RunContext, item: str, price: float) -> str:
    """Add item to cart.

    Args:
        item (str): Item name.
        price (float): Item price.
    """
    run_context.session_state["cart"].append({"item": item, "price": price})
    run_context.session_state["total"] += price
    return f"Added {item}. Total: ${run_context.session_state['total']:.2f}"

agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    db=SqliteDb(db_file="agent.db"),
    session_state={"cart": [], "total": 0.0},
    tools=[add_item],
    instructions="Current cart: {cart}. Total: ${total}",
)
```

Template variables (`{cart}`, `{total}`) in instructions auto-resolve from session_state.

### Agentic state
Let the agent update state directly without custom tools:
```python
agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    db=SqliteDb(db_file="agent.db"),
    session_state={"preferences": {}},
    enable_agentic_state=True,
)
```

---

## Instructions & Context

### Instructions (list recommended)
```python
agent = Agent(
    instructions=[
        "You are a financial advisor",
        "Use tables to display data",
        "If asked about stocks, use YFinanceTools",
        "Keep answers under 3 sentences unless asked for detail",
    ]
)
```

### Context layers (in construction order)
1. System message (description + instructions)
2. DateTime (if `add_datetime_to_context=True`)
3. Session summary (if enabled)
4. User memories (if enabled)
5. Knowledge results (if relevant)
6. Chat history (if enabled)
7. User message

Static content first → maximizes prompt caching.

### Runtime dependencies
Inject data at call time without baking into instructions:
```python
response = agent.run(
    message="What's my order status?",
    dependencies={"order_id": "ORD-123", "status": "shipped"},
)
```

---

## Running & Streaming

```python
# Sync
response = agent.run("What's 2+2?")
print(response.content)

agent.print_response("Tell me a story", stream=True)

# Async
response = await agent.arun("What's 2+2?")
await agent.aprint_response("Tell me a story", stream=True)

# With session/user tracking
agent.print_response("Hello!", session_id="s1", user_id="u1", stream=True)
```

---

## Constructor Quick Reference

### Model & Identity

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `Optional[Union[Model, str]]` | `None` | LLM to use. Accepts a Model object (e.g. `OpenAIChat(id="gpt-4o")`) or a model string shorthand (`"openai:gpt-4o"`) |
| `name` | `Optional[str]` | `None` | Agent name — used for identification in teams, logging, and tracing |
| `id` | `Optional[str]` | `None` | Agent ID — auto-generated UUID if not set. Used for tracking and registry |
| `description` | `Optional[str]` | `None` | A description of the agent added to the **start** of the system message. Sets the agent's persona |
| `role` | `Optional[str]` | `None` | Role of the agent when used inside a Team (e.g. "researcher", "writer") |

### System Message & Instructions

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `system_message` | `Optional[Union[str, Callable, Message]]` | `None` | Override the auto-built system message entirely. Can be a string, a callable that returns a string, or a Message object |
| `system_message_role` | `str` | `"system"` | Role label for the system message (some models require `"developer"` instead of `"system"`) |
| `instructions` | `Optional[Union[str, List[str], Callable]]` | `None` | Behavioral guidelines appended to the system message. List recommended for clarity. Supports `{state_var}` template variables |
| `add_instruction_tags` | `bool` | `True` | If True, wraps instructions in `<instructions>` XML tags in the system message for better model adherence |
| `introduction` | `Optional[str]` | `None` | Introduction message for the Agent — a greeting or orientation message shown at session start |
| `expected_output` | `Optional[str]` | `None` | Describe the expected output format/content. Added to system message to guide the model's response structure |
| `additional_context` | `Optional[str]` | `None` | Extra context appended to the **end** of the system message. Useful for dynamic info that changes per run |
| `markdown` | `bool` | `False` | If True, adds instructions to format output using markdown |

### Context Building

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `build_context` | `bool` | `True` | Set to False to skip automatic context building entirely (you control the full prompt) |
| `add_name_to_context` | `bool` | `False` | If True, adds the agent's name to the instructions |
| `add_datetime_to_context` | `bool` | `False` | If True, adds current datetime to instructions (gives the agent a sense of time) |
| `add_location_to_context` | `bool` | `False` | If True, adds current location to instructions (gives the agent a sense of place) |
| `timezone_identifier` | `Optional[str]` | `None` | Custom timezone for datetime instructions, TZ Database format (e.g. `"America/New_York"`, `"Etc/UTC"`) |
| `resolve_in_context` | `bool` | `True` | If True, resolves `{session_state}`, `{dependencies}`, and `{metadata}` template variables in system/user messages |

### User Message & Input

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `user_message_role` | `str` | `"user"` | Role label for user messages |
| `build_user_context` | `bool` | `True` | Set to False to skip building user context (knowledge refs, etc. won't be injected into user message) |
| `input_schema` | `Optional[Type[BaseModel]]` | `None` | Pydantic model to **validate** the input before processing. Raises error if input doesn't match schema |
| `additional_input` | `Optional[List[Union[str, Dict, BaseModel, Message]]]` | `None` | Extra messages added **after** the system message and **before** the user message. Useful for few-shot examples |
| `send_media_to_model` | `bool` | `True` | If False, media (images, videos, audio, files) is only available to tools and **not** sent to the LLM |

### Tools & Execution

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tools` | `Optional[List[Union[Toolkit, Callable, Function, Dict]]]` | `None` | List of tools — can be Toolkit instances, plain functions, Function objects, or raw JSON schema dicts |
| `tool_call_limit` | `Optional[int]` | `None` | Maximum number of tool calls allowed in a single run. Prevents runaway loops |
| `tool_choice` | `Optional[Union[str, Dict[str, Any]]]` | `None` | Controls which tool the model calls. `"auto"` (default), `"none"`, `"required"`, or `{"type": "function", "function": {"name": "..."}}` to force a specific tool |
| `max_tool_calls_from_history` | `Optional[int]` | `None` | Max number of tool call messages to keep from chat history (trims old tool results to save context) |
| `tool_hooks` | `Optional[List[Callable]]` | `None` | Functions executed **between** tool calls — useful for logging, validation, or side effects mid-run |
| `read_tool_call_history` | `bool` | `False` | Adds a built-in tool that lets the model read its own tool call history |
| `show_tool_calls` | `bool` | `False` | Show tool calls in printed output (useful for debugging and transparency) |

### Knowledge & Retrieval

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `knowledge` | `Optional[Knowledge]` | `None` | Knowledge base for RAG — connect a vector DB with embedded documents |
| `search_knowledge` | `bool` | `True` | Adds a built-in tool that lets the agent **search** the knowledge base on demand (Agentic RAG) |
| `update_knowledge` | `bool` | `False` | Adds a built-in tool that lets the agent **write** to the knowledge base |
| `add_knowledge_to_context` | `bool` | `False` | Always inject knowledge references into the user prompt (Traditional RAG). Bypasses agent decision-making |
| `knowledge_filters` | `Optional[Dict[str, Any]]` | `None` | Static filters applied to every knowledge search (e.g. `{"category": "docs"}`) |
| `enable_agentic_knowledge_filters` | `Optional[bool]` | `None` | Let the agent dynamically choose knowledge filters based on the query |
| `knowledge_retriever` | `Optional[Callable[..., Optional[List[Union[Dict, str]]]]]` | `None` | Custom retrieval function — replaces the default knowledge search. Must return a list of dicts or strings |
| `references_format` | `Literal["json", "yaml"]` | `"json"` | Format for knowledge references injected into context |

### Output & Parsing

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `output_schema` | `Optional[Union[Type[BaseModel], Dict[str, Any]]]` | `None` | Pydantic model or JSON schema for structured output. Response is parsed and validated against this schema |
| `use_json_mode` | `bool` | `False` | If `output_schema` is set, forces the model to respond in JSON mode (fallback for models without native structured output) |
| `structured_outputs` | `Optional[bool]` | `None` | Use model-enforced structured outputs if supported (e.g. OpenAI's native structured outputs). More reliable than JSON mode |
| `parse_response` | `bool` | `True` | If True, the model response is automatically parsed into the `output_schema`. Set False to get raw text |
| `parser_model` | `Optional[Union[Model, str]]` | `None` | Secondary model used to parse/transform the response from the primary model into the output schema |
| `parser_model_prompt` | `Optional[str]` | `None` | Custom prompt sent to the parser model explaining how to parse the primary response |
| `output_model` | `Optional[Union[Model, str]]` | `None` | Alternative output model to structure/format the response from the main model |
| `output_model_prompt` | `Optional[str]` | `None` | Custom prompt for the output model |

### Database & Storage

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db` | `Optional[BaseDb]` | `None` | Database backend for persistence — SqliteDb, PostgresDb, MongoDb, RedisDb, DynamoDb, etc. |
| `store_media` | `bool` | `True` | If True, stores media content (images, files) in the database alongside messages |
| `store_tool_messages` | `bool` | `True` | If True, stores tool call results in the database |
| `store_history_messages` | `bool` | `True` | If True, stores full chat history messages in the database |
| `save_response_to_file` | `Optional[str]` | `None` | File path to save the response content to (e.g. `"output.md"`) |

### Session & User

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `session_id` | `Optional[str]` | `None` | Session identifier — auto-generated UUID if not set. Use to resume conversations |
| `user_id` | `Optional[str]` | `None` | User identifier — used for memory isolation, state separation, and multi-user scenarios |
| `session_state` | `Optional[Dict[str, Any]]` | `None` | Persistent state dict stored in the database. Survives across runs. Accessible via `{key}` in instructions |
| `add_session_state_to_context` | `bool` | `False` | If True, adds the full session_state dict to the context sent to the model |
| `enable_agentic_state` | `bool` | `False` | Gives the agent built-in tools to update session_state dynamically during runs |
| `overwrite_db_session_state` | `bool` | `False` | If True, overwrites the DB session state with the state provided in the run (instead of merging) |
| `cache_session` | `bool` | `False` | If True, caches the current session in memory for faster access (avoids DB reads on every run) |

### History & Chat

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `add_history_to_context` | `bool` | `False` | Includes chat history of the current session in messages sent to the model |
| `num_history_runs` | `Optional[int]` | `None` | Number of past runs to include in history (each run = one user message + one assistant response) |
| `num_history_messages` | `Optional[int]` | `None` | Number of individual history messages to include (finer control than `num_history_runs`) |
| `read_chat_history` | `bool` | `False` | Adds a built-in tool that lets the model read the full chat history on demand |
| `search_session_history` | `Optional[bool]` | `False` | If True, allows searching through **previous** sessions (cross-session history) |
| `num_history_sessions` | `Optional[int]` | `None` | Number of past sessions to include in cross-session search. Keep low (2-3 recommended) |

### Memory

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_user_memories` | `bool` | `False` | Enables automatic memory — Agno extracts user facts/preferences after each run and stores them |
| `enable_agentic_memory` | `bool` | `False` | Gives the agent tools to create/update/delete memories itself. **Mutually exclusive** with `enable_user_memories` |
| `add_memories_to_context` | `Optional[bool]` | `None` | If True, injects stored user memories into the context sent to the model |
| `update_memory_on_run` | `bool` | `False` | If True, memory is created/updated at the end of every run (vs. only when the agent decides) |
| `memory_manager` | `Optional[MemoryManager]` | `None` | Custom MemoryManager instance for advanced memory configuration (custom models, prompts, etc.) |

### Session Summaries

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_session_summaries` | `bool` | `False` | Creates/updates a running summary of the conversation at the end of each run |
| `add_session_summary_to_context` | `Optional[bool]` | `None` | If True, injects the session summary into context (useful for long conversations) |
| `session_summary_manager` | `Optional[SessionSummaryManager]` | `None` | Custom SessionSummaryManager for advanced summary configuration |

### Compression

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `compress_tool_results` | `bool` | `False` | If True, compresses tool call results to save context window space |
| `compression_manager` | `Optional[CompressionManager]` | `None` | Custom CompressionManager for controlling how tool results are compressed |

### Dependencies & Metadata

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dependencies` | `Optional[Dict[str, Any]]` | `None` | Runtime dependencies available to tools and prompt functions via `RunContext`. Injected at call time |
| `add_dependencies_to_context` | `bool` | `False` | If True, adds dependencies dict to the user prompt so the model can see them |
| `metadata` | `Optional[Dict[str, Any]]` | `None` | Arbitrary metadata stored with the agent — useful for tagging, filtering, and organization |

### Reasoning

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `reasoning` | `bool` | `False` | Enable step-by-step reasoning using ReasoningTools (think/analyze) before responding |
| `reasoning_model` | `Optional[Union[Model, str]]` | `None` | Separate model used for the reasoning phase (e.g. use a stronger model for reasoning, cheaper for response) |
| `reasoning_agent` | `Optional[Agent]` | `None` | A full Agent instance used for reasoning — allows tools, knowledge, etc. during the reasoning phase |
| `reasoning_min_steps` | `int` | `1` | Minimum number of reasoning steps before the agent can respond |
| `reasoning_max_steps` | `int` | `10` | Maximum number of reasoning steps (prevents infinite reasoning loops) |
| `show_full_reasoning` | `bool` | `False` | Show the full reasoning trace in printed output |

### Hooks & Guardrails

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `pre_hooks` | `Optional[List[Union[Callable, BaseGuardrail, BaseEval]]]` | `None` | Functions/guardrails/evals called **before** processing starts (after session loads). Use for input validation, PII detection, prompt injection defense |
| `post_hooks` | `Optional[List[Union[Callable, BaseGuardrail, BaseEval]]]` | `None` | Functions/guardrails/evals called **after** the response is generated but **before** it's returned. Use for output validation, content filtering |

### Retry & Resilience

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `retries` | `int` | `0` | Number of retry attempts when a run fails (e.g. model errors, parsing failures) |
| `delay_between_retries` | `int` | `1` | Delay in seconds between retry attempts |
| `exponential_backoff` | `bool` | `False` | If True, doubles the delay between each retry (1s → 2s → 4s → 8s...) |

### Streaming & Events

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `stream` | `Optional[bool]` | `None` | Default streaming mode for this agent. Can be overridden per-run |
| `stream_events` | `bool` | `False` | Stream intermediate events (tool calls, reasoning steps, etc.) in addition to the final response |
| `store_events` | `bool` | `False` | Persist events on the RunResponse object for later inspection |
| `events_to_skip` | `Optional[List[RunEvent]]` | `None` | List of RunEvent types to exclude when storing events (e.g. skip verbose tool results) |

### Debug & Telemetry

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `debug_mode` | `bool` | `False` | Enable detailed debug logging — shows prompt construction, tool calls, model responses |
| `debug_level` | `Literal[1, 2]` | `1` | Debug verbosity: `1` = standard, `2` = verbose (includes full message payloads) |
| `telemetry` | `bool` | `True` | Log minimal anonymous telemetry for framework analytics. Set False to opt out |

---

## Agent Methods Reference

### Running

| Method | Description |
|--------|-------------|
| `run(input, stream=None, ...)` | Run the agent synchronously. Returns `RunResponse` |
| `arun(input, stream=None, ...)` | Run the agent asynchronously. Returns `RunResponse` |
| `print_response(input, stream=True, ...)` | Run and print the response to stdout |
| `aprint_response(input, stream=True, ...)` | Async run and print the response |
| `continue_run(run_response, ...)` | Continue a paused/interrupted run (e.g. after human-in-the-loop) |
| `acontinue_run(run_response, ...)` | Async continue a paused run |
| `cli_app(...)` | Launch an interactive CLI chat interface |
| `acli_app(...)` | Async interactive CLI interface |

### Tool Management

| Method | Description |
|--------|-------------|
| `add_tool(tool)` | Add a single tool to the agent at runtime |
| `set_tools(tools)` | Replace all tools with a new list |

### Session Management

| Method | Description |
|--------|-------------|
| `get_session()` | Get the current session data |
| `update_session_state(state)` | Update the session state dict |
| `delete_session()` | Delete the current session from the database |

### Memory Management

| Method | Description |
|--------|-------------|
| `get_user_memories(user_id)` | Retrieve all stored memories for a user |

---

## Full Example: Production Agent

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.lancedb import LanceDb, SearchType
from agno.embedder.openai import OpenAIEmbedder
from agno.tools.hackernews import HackerNewsTools
from agno.run import RunContext

# Knowledge base
knowledge = Knowledge(
    vector_db=LanceDb(
        uri="tmp/lancedb",
        table_name="docs",
        search_type=SearchType.hybrid,
        embedder=OpenAIEmbedder(id="text-embedding-3-small", dimensions=1536),
    )
)

# Custom tool with state access
def save_note(run_context: RunContext, note: str) -> str:
    """Save a note.

    Args:
        note (str): The note to save.
    """
    run_context.session_state["notes"].append(note)
    return f"Saved. Total notes: {len(run_context.session_state['notes'])}"

# Full-featured agent
agent = Agent(
    name="Assistant",
    model=OpenAIChat(id="gpt-4o"),
    db=SqliteDb(db_file="assistant.db"),
    tools=[HackerNewsTools(), save_note],
    knowledge=knowledge,
    search_knowledge=True,
    session_state={"notes": []},
    enable_user_memories=True,
    add_memories_to_context=True,
    add_history_to_context=True,
    num_history_runs=5,
    enable_session_summaries=True,
    add_session_summary_to_context=True,
    add_datetime_to_context=True,
    instructions=[
        "Search knowledge for factual questions",
        "Remember user preferences",
        "Current notes: {notes}",
    ],
    show_tool_calls=True,
    markdown=True,
    retries=2,
    exponential_backoff=True,
    tool_call_limit=20,
)
```
