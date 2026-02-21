# Agno Reasoning System

Agno provides three complementary approaches to add reasoning capabilities to agents:

1. **Reasoning Models** — Use models with native reasoning (GPT-5-mini, DeepSeek-R1, Claude 3.7+ with extended thinking). The model handles reasoning internally.
2. **Reasoning Tools** — Give agents explicit `think()` and `analyze()` tools for structured chain-of-thought. Works with any model.
3. **Reasoning Agents** — Enable framework-driven multi-step reasoning via `reasoning=True`. Works with any model.

## Quick Start

### Reasoning Agent (simplest)

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    reasoning=True,
    markdown=True,
)

agent.print_response(
    "A bat and ball cost $1.10 total. The bat costs $1.00 more than the ball. How much does the ball cost?",
    stream=True,
    show_full_reasoning=True,
)
```

### Reasoning Tools

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.tools.reasoning import ReasoningTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[ReasoningTools(add_instructions=True)],
)

agent.print_response("Which is bigger: 9.11 or 9.9?", stream=True)
```

### Reasoning + Response Model (split reasoning and response across models)

```python
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.models.groq import Groq

agent = Agent(
    model=Claude(id="claude-sonnet-4-5"),
    reasoning_model=Groq(
        id="deepseek-r1-distill-llama-70b",
        temperature=0.6, max_tokens=1024, top_p=0.95,
    ),
)
agent.print_response("9.11 and 9.9 -- which is bigger?", stream=True, show_full_reasoning=True)
```

## Agent Reasoning Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `reasoning` | `bool` | `False` | Enable step-by-step reasoning using ReasoningTools (think/analyze) before responding |
| `reasoning_model` | `Optional[Union[Model, str]]` | `None` | Separate model for the reasoning phase (e.g. use a stronger model for reasoning, cheaper for response) |
| `reasoning_agent` | `Optional[Agent]` | `None` | Full Agent instance for reasoning — allows tools, knowledge, etc. during the reasoning phase |
| `reasoning_min_steps` | `int` | `1` | Minimum number of reasoning steps before the agent can respond |
| `reasoning_max_steps` | `int` | `10` | Maximum number of reasoning steps (prevents infinite reasoning loops) |

### ReasoningTools Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `add_instructions` | `bool` | `False` | If True, adds reasoning instructions to the agent's system message |

```python
from agno.tools.reasoning import ReasoningTools

agent = Agent(
    model=model,
    tools=[ReasoningTools(add_instructions=True)],
)

# Or use framework-driven reasoning
agent = Agent(
    model=model,
    reasoning=True,
    reasoning_model="openai:gpt-4o",
    reasoning_min_steps=2,
    reasoning_max_steps=5,
)

# Display options
agent.print_response("...", show_full_reasoning=True, stream=True)
agent.run("...", stream=True, stream_events=True)  # For capturing events
```

## Comparison

| Aspect | Reasoning Models | Reasoning Tools | Reasoning Agents |
|--------|------------------|-----------------|------------------|
| Activation | Automatic (model layer) | Agent-driven (explicit calls) | Automatic (every request) |
| Control | Model-level | Tool-level | Framework-level |
| Best For | Single-shot problems | Research/analysis tasks | Multi-step tool use |
| Model Requirement | Reasoning-capable models only | Any model | Any model |

## Sub-References

Read only what the task requires:

| Reference | File | Read When |
|-----------|------|-----------|
| **Reasoning Tools** | `references/reasoning/reasoning-tools.md` | Using ReasoningTools, KnowledgeTools, MemoryTools, WorkflowTools — constructors, methods, parameters, combining toolkits |
| **Reasoning Agents** | `references/reasoning/reasoning-agents.md` | Framework-driven reasoning, custom reasoning agents, streaming events, the 6-step reasoning framework, data structures |
| **Examples** | `references/reasoning/examples.md` | Complete examples — basic, split models, DeepSeek+Claude, extended thinking, tools+knowledge, combined approaches |
