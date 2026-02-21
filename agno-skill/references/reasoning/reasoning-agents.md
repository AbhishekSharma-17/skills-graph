# Reasoning Agents

Framework-driven multi-step reasoning via `reasoning=True`. Transforms any model into a structured reasoning system using a 6-step framework.

## Agent Parameters

```python
from agno.agent import Agent

agent = Agent(
    model=model,
    reasoning=True,                      # Enable reasoning agent mode
    reasoning_model=None,                # Optional: separate model for reasoning
    reasoning_agent=None,                # Optional: custom reasoning agent instance
    reasoning_min_steps=1,               # Minimum reasoning steps (default 1)
    reasoning_max_steps=10,              # Maximum reasoning steps (default 10)
)
```

## The 6-Step Reasoning Framework

When `reasoning=True`, the agent follows this structured process on every request:

1. **Problem Analysis** — Restate the task, identify information and tools needed
2. **Decompose and Strategize** — Break into subtasks, develop approaches
3. **Intent Clarification and Planning** — Articulate intent, select strategy, create plan
4. **Execute the Action Plan** — Document each step, call tools, self-correct
5. **Validation (mandatory)** — Cross-verify with alternative approaches
6. **Final Answer** — Deliver thoroughly validated solution

## Basic Usage

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    reasoning=True,
    markdown=True,
)

agent.print_response(
    "Solve the trolley problem. Evaluate multiple ethical frameworks.",
    stream=True,
    show_full_reasoning=True,
)
```

## Separate Reasoning Model

Use a different (often cheaper/faster) model for the reasoning step:

```python
agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),           # Response model
    reasoning_model=OpenAIResponses(id="gpt-5-mini"),  # Reasoning model
    reasoning=True,
    reasoning_min_steps=2,
    reasoning_max_steps=5,
)
```

## Custom Reasoning Agent

Supply a fully configured agent instance for the reasoning step:

```python
custom_reasoner = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    instructions=[
        "Focus on mathematical rigor",
        "Always provide step-by-step proofs",
    ],
)

main_agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    reasoning=True,
    reasoning_agent=custom_reasoner,
)
```

## Extended Thinking (Claude)

```python
from agno.models.anthropic import Claude

agent = Agent(
    reasoning_model=Claude(
        id="claude-sonnet-4-5",
        thinking={"type": "enabled", "budget_tokens": 1024},
    ),
    reasoning=True,
    instructions="Think step by step about the problem.",
)
```

## Streaming Reasoning Events

Capture individual reasoning steps as they're generated:

```python
from agno.run.agent import RunEvent

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    reasoning=True,
)

for event in agent.run("What is 25 * 37?", stream=True, stream_events=True):
    if event.event == RunEvent.reasoning_started:
        print("Reasoning started...")
    elif event.event == RunEvent.reasoning_content_delta:
        print(event.reasoning_content, end="", flush=True)
    elif event.event == RunEvent.run_content:
        if event.content:
            print(event.content, end="", flush=True)
    elif event.event == RunEvent.run_completed:
        print("Done.")
```

### RunEvent Types

| Event | Description |
|-------|-------------|
| `RunEvent.run_started` | Run begins |
| `RunEvent.reasoning_started` | Reasoning process begins |
| `RunEvent.reasoning_content_delta` | Chunk of reasoning content (streams) |
| `RunEvent.run_content` | Final response content |
| `RunEvent.run_completed` | Run finishes |

## Data Structures

### ReasoningStep

```python
# from agno.reasoning

ReasoningStep(
    title: Optional[str] = None,         # Concise step title
    reasoning: Optional[str] = None,     # Detailed thought process
    action: Optional[str] = None,        # Action to take
    result: Optional[str] = None,        # Outcome of action
    next_action: NextAction = NextAction.CONTINUE,  # What to do next
    confidence: float = 0.8,             # 0.0 to 1.0
    metadata: Optional[Dict] = None,     # Additional metadata
)
```

### NextAction Enum

```python
class NextAction(Enum):
    CONTINUE = "continue"          # Continue reasoning
    VALIDATE = "validate"          # Validate before finalizing
    FINAL_ANSWER = "final_answer"  # Ready for final answer
    RESET = "reset"                # Reset and restart
```

### ReasoningSteps

```python
ReasoningSteps(
    reasoning_steps: List[ReasoningStep] = [],
    metadata: Optional[Dict] = None,
)
```

### Reasoning Events

```python
# Emitted during streaming
ReasoningStartedEvent(event="ReasoningStarted", run_id=..., agent_id=...)

ReasoningStepEvent(
    event="ReasoningStep",
    content=...,
    reasoning_content="...",
    step_number=1,
    run_id=...,
    agent_id=...,
)

ReasoningCompletedEvent(
    event="ReasoningCompleted",
    reasoning_steps=[...],
    reasoning_messages=[...],
    run_id=...,
    agent_id=...,
)
```
