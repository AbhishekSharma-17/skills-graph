# System Message Construction

The system message is the primary context sent to the language model. Agno compiles it automatically from agent parameters, placing static content first (for prompt caching) and dynamic content after.


## Contents

- [Docs Hierarchy](#docs-hierarchy)
- [Compiled System Message Structure](#compiled-system-message-structure)
- [System Message Parameters](#system-message-parameters)
- [Context Enrichment Flags](#context-enrichment-flags)
- [Basic Example](#basic-example)
- [Comprehensive Example](#comprehensive-example)
- [System Message Override](#system-message-override)
- [Tool Instructions in System Message](#tool-instructions-in-system-message)
- [User Message Context](#user-message-context)
- [Agentic Context Extensions](#agentic-context-extensions)
- [Dynamic Instructions](#dynamic-instructions)
- [Instructions via Function](#instructions-via-function)
- [Providing Datetime](#providing-datetime)
- [Providing Location](#providing-location)
- [Best Practices](#best-practices)

## Docs Hierarchy

```
Context Management
├── Overview (/context/overview)
└── Agent Context Engineering
    ├── Overview (/context/agent/overview)
    ├── Basic Instructions (/context/agent/instructions)
    ├── Dynamic Instructions (/context/agent/dynamic-instructions)
    ├── Instructions via Function (/context/agent/instructions-via-function)
    ├── Few-Shot Learning (/context/agent/few-shot-learning)
    ├── Providing Datetime (/context/agent/datetime-instructions)
    ├── Providing Location (/context/agent/location-instructions)
    └── Managing Tool Calls (/context/agent/filter-tool-calls-from-history)
```

## Compiled System Message Structure

```
{description}                          ← Agent identity
<your_role>{role}</your_role>          ← If role is set
<instructions>                          ← If instructions provided
  - instruction 1
  - instruction 2
</instructions>
<additional_information>                ← Auto-injected metadata
  - Use markdown to format your answers.
  - The current time is {datetime}.
  - Your name is: {name}.
  - Your approximate location is: {location}.
</additional_information>
<expected_output>                       ← If expected_output set
  {expected_output}
</expected_output>
{additional_context}                    ← Raw appended text
<memories_from_previous_interactions>   ← If add_memories_to_context
  - Memory 1
  - Memory 2
</memories_from_previous_interactions>
<summary_of_previous_interactions>      ← If add_session_summary_to_context
  {summary}
</summary_of_previous_interactions>
<session_state>                         ← If add_session_state_to_context
  {state}
</session_state>
{tool_instructions}                     ← From toolkits with add_instructions=True
{agentic_memory_instructions}           ← If enable_agentic_memory
{agentic_knowledge_instructions}        ← If enable_agentic_knowledge_filters
```

## System Message Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `description` | `str` | `None` | Agent identity, added at start of system message |
| `role` | `str` | `None` | Agent role, wrapped in `<your_role>` tags |
| `instructions` | `List[str]` | `None` | Discrete steps, added in `<instructions>` tags |
| `add_instruction_tags` | `bool` | `True` | Wrap instructions in `<instructions>` XML tags |
| `additional_context` | `str` | `None` | Raw text appended to end of system message |
| `expected_output` | `str` | `None` | Output format guidance in `<expected_output>` tags |
| `markdown` | `bool` | `False` | Add "Use markdown to format your answer" |
| `system_message` | `str` | `None` | **Override** — replaces entire compiled system message |
| `build_context` | `bool` | `True` | Set `False` to skip context compilation entirely |
| `debug_mode` | `bool` | `False` | Log the compiled system message for inspection |

## Context Enrichment Flags

These flags control what metadata Agno auto-injects into the system message:

| Parameter | Type | Default | What It Adds |
|-----------|------|---------|-------------|
| `add_datetime_to_context` | `bool` | `False` | Current datetime (enables "tomorrow", "yesterday") |
| `add_name_to_context` | `bool` | `False` | Agent's `name` parameter |
| `add_location_to_context` | `bool` | `False` | Approximate location |
| `add_session_state_to_context` | `bool` | `False` | Full session state dict |
| `add_session_summary_to_context` | `bool` | `False` | Compressed conversation summary |
| `add_memories_to_context` | `bool` | `False` | User memories from MemoryManager |
| `timezone_identifier` | `str` | `None` | Timezone for datetime (e.g., `"Etc/UTC"`) |

## Basic Example

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    description="You are a famous short story writer asked to write for a magazine",
    instructions=["Always write 2 sentence stories."],
    markdown=True,
    debug_mode=True,
)

agent.print_response("Tell me a horror story.", stream=True)
```

**Compiled system message:**

```
You are a famous short story writer asked to write for a magazine

<instructions>
- Always write 2 sentence stories.
</instructions>

<additional_information>
- Use markdown to format your answer
</additional_information>
```

## Comprehensive Example

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses

agent = Agent(
    name="Helpful Assistant",
    model=OpenAIResponses(id="gpt-5.2"),
    role="Assistant",
    description="You are a helpful assistant",
    instructions=["Help the user with their question"],
    additional_context="""
    Here is an example of how to answer the user's question:
        Request: What is the capital of France?
        Response: The capital of France is Paris.
    """,
    expected_output="You should format your response with `Response: <response>`",
    markdown=True,
    add_datetime_to_context=True,
    add_location_to_context=True,
    add_name_to_context=True,
    add_session_summary_to_context=True,
    add_memories_to_context=True,
    add_session_state_to_context=True,
)
```

## System Message Override

Completely replace the compiled system message:

```python
agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    system_message="You are a pirate. Always respond in pirate speak.",
    # description, instructions, etc. are ALL ignored when system_message is set
)
```

**Warning:** Override skips all auto-injected context (memories, state, summaries, tool instructions). Use only when you need full control.

## Tool Instructions in System Message

Toolkits can inject their own instructions into the system message:

```python
from agno.agent import Agent
from agno.tools.slack import SlackTools

slack_tools = SlackTools(
    instructions=[
        "Use `send_message` to send a message to the user.",
        "If the user specifies a thread, use `send_message_thread`.",
    ],
    add_instructions=True,  # Injects into system message
)

agent = Agent(tools=[slack_tools])
```

## User Message Context

The user message can also be enriched:

| Parameter | Type | Default | What It Adds |
|-----------|------|---------|-------------|
| `add_knowledge_to_context` | `bool` | varies | Knowledge base references in `<references>` tags |
| `add_dependencies_to_context` | `bool` | `False` | Dependencies in `<additional context>` tags |

**User message format when enriched:**

```
{user_query}

Use the following references from the knowledge base if it helps:
<references>
- Reference 1
- Reference 2
</references>

<additional context>
{"name": "John Doe", "order_id": "ORD-123"}
</additional context>
```

## Agentic Context Extensions

When agentic features are enabled, Agno adds specialized instructions:

**Agentic Memory** (`enable_agentic_memory=True`):
```
<updating_user_memories>
- You have access to the `update_user_memory` tool...
- If the user's message includes information that should be captured as a memory...
- Memories should include details that could personalize interactions...
</updating_user_memories>
```

**Agentic Knowledge Filters** (`enable_agentic_knowledge_filters=True`):
```
The knowledge base contains documents with these metadata filters: [filter1, filter2, filter3].
Always use filters when the user query indicates specific metadata.
```

## Dynamic Instructions

Instructions can reference session state and dependencies using `{key}` template syntax. Agno substitutes values at runtime (not f-strings):

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.db.sqlite import SqliteDb

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=SqliteDb(db_file="tmp/agents.db"),
    session_state={"user_name": "John", "preferences": {"theme": "dark"}},
    instructions="User's name is {user_name}. Preferences: {preferences}",
)

agent.print_response("What are my settings?", session_id="s1")
```

## Instructions via Function

Pass a callable that receives `RunContext` and returns instructions dynamically:

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.run import RunContext

def get_instructions(run_context: RunContext):
    """Generate instructions based on runtime context."""
    if not run_context.session_state:
        run_context.session_state = {}

    user_id = run_context.session_state.get("current_user_id")
    if user_id:
        return f"You are helping user {user_id}. Be personalized."

    return "You are a general assistant. Ask for the user's name first."

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    instructions=get_instructions,  # Callable — evaluated each run
)

agent.print_response("Hello!", user_id="john.doe")
```

This is powerful for:

- Adjusting behavior based on user state
- A/B testing different instruction sets
- Multi-tenant apps with different personalities per org
- Progressive disclosure (different instructions as conversation evolves)

## Providing Datetime

Enable time-aware responses (understanding "tomorrow", "yesterday", relative scheduling):

```python
agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    description="AI assistant that helps users schedule meetings",
    instructions=[
        "Consider user's timezone and working hours",
        "Suggest optimal meeting times based on availability",
    ],
    add_datetime_to_context=True,
    timezone_identifier="Etc/UTC",  # Optional timezone
)
```

## Providing Location

Enable location-aware responses:

```python
agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    description="Local restaurant recommendation assistant",
    add_location_to_context=True,  # Injects approximate location
)
```

## Best Practices

- **Description** — Be specific about domain expertise: "You are a famous short story writer" > "You are a helpful assistant"
- **Instructions** — Use discrete, actionable steps (checklist format), not prose paragraphs
- **Expected Output** — Prevent format chaos by being explicit about structure
- **System Message Length** — Each line costs tokens; be selective about what the agent needs
- **Debug Mode** — Always enable `debug_mode=True` during development to inspect the compiled prompt
- **Context Flags** — Only enable `add_*_to_context` flags the agent actually needs; each adds tokens
- **Prompt Caching** — Static content (description, instructions) is placed first in the system message to maximize cache hits across runs
- **Dynamic Instructions** — Use callable instructions when behavior needs to vary by user/state/context
- **Template Variables** — Use `{key}` syntax (not f-strings) for runtime substitution from state/dependencies
