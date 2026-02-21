# Context Engineering

Context engineering controls what information the model sees at each turn. Agno builds a structured system message from multiple components, and you control each one.

## Context Components

An agent's context consists of:

1. **System message** — the main instruction context
2. **User message** — the input for this run
3. **Chat history** — past conversation turns (see `history.md`)
4. **Additional input** — few-shot examples or extra messages

## System Message Structure

Agno builds the system message from these parameters, in order:

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    # 1. Description — opens the system message
    description="You are a famous short story writer asked to write for a magazine",
    # 2. Role — wrapped in <your_role> tags
    role="Creative Writer",
    # 3. Instructions — wrapped in <instructions> tags
    instructions=["Always write 2 sentence stories.", "Use vivid imagery."],
    # 4. Additional information block
    markdown=True,                      # "Use markdown to format your answers."
    add_datetime_to_context=True,       # "The current time is 2025-09-30 12:00:00."
    add_location_to_context=True,       # "Your approximate location is: New York, NY."
    add_name_to_context=True,           # "Your name is: Creative Writer."
    # 5. Expected output
    expected_output="A two-sentence story with a twist ending",
    # 6. Additional context (appended at end)
    additional_context="The magazine focuses on sci-fi themes.",
    # Debug: print the compiled system message
    debug_mode=True,
)
agent.print_response("Tell me a horror story.", stream=True)
```

The compiled system message looks like:

```
You are a famous short story writer asked to write for a magazine
<your_role>
Creative Writer
</your_role>

<instructions>
  Always write 2 sentence stories.
  Use vivid imagery.
</instructions>

<additional_information>
Use markdown to format your answers.
The current time is 2025-09-30 12:00:00.
Your approximate location is: New York, NY, USA.
Your name is: Creative Writer.
</additional_information>

<expected_output>
  A two-sentence story with a twist ending
</expected_output>

The magazine focuses on sci-fi themes.

[+ memories, summary, session state if enabled]
```

## System Message Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `description` | `str` | `None` | Agent description at start of system message |
| `role` | `str` | `None` | Agent role in `<your_role>` tags |
| `instructions` | `List[str]` | `None` | Instructions in `<instructions>` tags |
| `add_instruction_tags` | `bool` | `True` | Wrap instructions in XML tags |
| `additional_context` | `str` | `None` | Extra context appended at end |
| `expected_output` | `str` | `None` | Output format expectations |
| `markdown` | `bool` | `False` | Add markdown formatting instruction |
| `add_datetime_to_context` | `bool` | `False` | Include current datetime |
| `add_name_to_context` | `bool` | `False` | Include agent name |
| `add_location_to_context` | `bool` | `False` | Include approximate location |
| `timezone_identifier` | `str` | `None` | Custom timezone |
| `add_session_summary_to_context` | `bool` | `False` | Include session summary |
| `add_memories_to_context` | `bool` | `False` | Include user memories |
| `add_session_state_to_context` | `bool` | `False` | Include session state |
| `enable_agentic_knowledge_filters` | `bool` | `False` | Let agent choose knowledge filters |
| `system_message` | `str` | `None` | Override entire system message |
| `build_context` | `bool` | `True` | Enable/disable context building |

## Override System Message

Skip all the automatic building and set a raw system message:

```python
agent = Agent(
    system_message="You are a pirate. Always respond in pirate speak.",
)
agent.print_response("What's the weather like?")
```

When `system_message` is set, all other context parameters (`description`, `instructions`, etc.) are ignored.

## Additional Context

Inject dynamic information (database schemas, API docs, etc.) into the system message:

```python
from textwrap import dedent
from agno.agent import Agent
from agno.tools.duckdb import DuckDbTools

duckdb_tools = DuckDbTools(
    create_tables=False, export_tables=False, summarize_tables=False,
)
duckdb_tools.create_table_from_path(
    path="https://phidata-public.s3.amazonaws.com/demo_data/IMDB-Movie-Data.csv",
    table="movies",
)

agent = Agent(
    tools=[duckdb_tools],
    markdown=True,
    additional_context=dedent("""\
    You have access to the following tables:
    - movies: contains information about movies from IMDB.
    """),
)
agent.print_response("What is the average rating of movies?", stream=True)
```

## User Message Context

The input to `agent.run()` or `agent.print_response()` becomes the user message. You can enrich it with dependencies and knowledge:

```python
agent = Agent(
    add_knowledge_to_context=True,       # Inject knowledge base results
    add_dependencies_to_context=True,    # Inject dependencies dict
)

agent.print_response(
    "What is the capital of France?",
    dependencies={"user_name": "John Doe"},
)
```

This produces a user message like:

```
What is the capital of France?

<additional context>
{"user_name": "John Doe"}
</additional context>
```

## Few-Shot Learning

Provide example interactions with `additional_input`:

```python
from agno.agent import Agent
from agno.models.message import Message
from agno.models.openai import OpenAIResponses

support_examples = [
    Message(role="user", content="I forgot my password and can't log in"),
    Message(
        role="assistant",
        content=(
            "I'll help you reset your password.\n\n"
            "**Steps:**\n"
            "1. Go to login page, click 'Forgot Password'\n"
            "2. Enter your email\n"
            "3. Check email for reset link\n"
            "4. Create a new strong password"
        ),
    ),
    Message(role="user", content="I've been charged twice for the same order!"),
    Message(
        role="assistant",
        content=(
            "I sincerely apologize for the billing error.\n\n"
            "**Action Plan:**\n"
            "1. Investigate your account for the duplicate charge\n"
            "2. Process a full refund\n"
            "3. Provide confirmation number\n\n"
            "Refund takes 3-5 business days."
        ),
    ),
]

agent = Agent(
    name="Customer Support Specialist",
    model=OpenAIResponses(id="gpt-5.2"),
    additional_input=support_examples,    # Few-shot examples
    instructions=[
        "Be empathetic, professional, and solution-oriented.",
        "Provide clear, actionable steps.",
    ],
    markdown=True,
)
agent.print_response("My order hasn't arrived yet")
```

The examples are prepended to the conversation, teaching the model the desired response style.

## Context Caching

Agno places static content at the beginning of the system message for optimal prompt caching with supported providers (OpenAI, Anthropic, OpenRouter). This means the `description`, `instructions`, and tool definitions are cached, and only the dynamic parts (history, state, user message) change per run.

## Debug Mode

Use `debug_mode=True` to print the full compiled system message and see exactly what the model receives:

```python
agent = Agent(
    description="A helpful assistant",
    instructions=["Be concise"],
    debug_mode=True,
)
agent.print_response("Hello")
# Prints the full system message to console
```
