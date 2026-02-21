# Session Summaries

As conversations grow, including full chat history in context causes token costs to grow exponentially. Session summaries compress long conversations into a short summary, keeping costs linear.

## The Problem

Without summaries, token usage grows with every turn:

```
Run 1: 100 tokens
Run 2: 250 tokens  (100 history + 150 new)
Run 3: 450 tokens  (250 history + 200 new)
Run 4: 750 tokens  (450 history + 300 new)
... exponential growth
```

## The Solution

With summaries, a compressed representation replaces the full history:

```
Run 1: 100 tokens
Run 2: 250 tokens
[Summary created: ~50 tokens]
Run 3: 250 tokens  (50 summary + 200 new)
Run 4: 350 tokens  (50 summary + 300 new)
... linear growth
```

## Enable Session Summaries

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.db.postgres import PostgresDb

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=PostgresDb(db_url="postgresql+psycopg://ai:ai@localhost:5532/ai"),
    enable_session_summaries=True,
)

agent.print_response(
    "Hi my name is John and I live in New York",
    session_id="conversation_123",
)

# Retrieve the summary
summary = agent.get_session_summary(session_id="conversation_123")
if summary:
    print(summary.summary)  # "User's name is John, lives in New York"
    print(summary.topics)   # ["introduction", "location"]
```

## Summary in Context

When enabled, the summary is automatically injected into the system message:

```python
agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=db,
    enable_session_summaries=True,
    add_session_summary_to_context=True,  # Enabled by default when summaries are on
)
```

The model sees something like:

```
Here is a brief summary of your previous interactions:

<summary_of_previous_interactions>
The user asked about information about Digimon and Japan.
</summary_of_previous_interactions>

Note: this information is from previous interactions and may be outdated.
```

## Hybrid: Summary + Recent History

For the best of both worlds — long-term memory from summaries and short-term detail from recent messages:

```python
agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=db,
    enable_session_summaries=True,
    add_session_summary_to_context=True,   # Long-term memory
    add_history_to_context=True,           # Short-term detail
    num_history_runs=2,                    # Only last 2 turns for detail
)
```

This gives the model the summary for overall context plus the last 2 turns for immediate conversation detail.

## When to Use Summaries

**Use summaries for:**
- Long-running customer support conversations
- Multi-day or multi-week interactions
- Conversations with 10+ turns
- Production systems where token cost matters

**Consider alternatives for:**
- Short conversations (fewer than 5 turns) — full history is fine
- When full detail is critical (legal, medical) — summaries lose nuance
- Real-time chat needing only recent context — use `num_history_runs` alone

## Agent Parameters

```python
agent = Agent(
    enable_session_summaries=False,              # Create/update summaries
    add_session_summary_to_context=None,         # Include summary in system message
    session_summary_manager=None,                # Custom summary manager
)
```
