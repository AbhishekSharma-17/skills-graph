# Agent Metrics

> Source: https://deepeval.com/docs/getting-started-agents

## Overview

Agent evaluation in DeepEval differs from standard LLM evaluation because agentic workflows are complex multi-component systems with tools, chained LLM calls, and RAG modules. DeepEval evaluates agents through tracing — the `@observe` decorator captures execution spans, and metrics attach at trace level (end-to-end) or span level (component-level).

## Agent Metric Types

### TaskCompletionMetric

Measures whether the agent achieved its intended goal:

```python
from deepeval.metrics import TaskCompletionMetric
from deepeval.test_case import LLMTestCase

metric = TaskCompletionMetric(threshold=0.7)

test_case = LLMTestCase(
    input="Book a flight from NYC to London for next Friday",
    actual_output="I've booked flight BA178 from JFK to Heathrow departing next Friday at 7:30 PM. Confirmation #BA2847."
)

metric.measure(test_case)
```

**Required fields:** `input`, `actual_output`

### ToolCorrectnessMetric

Verifies the agent called the right tools with correct parameters:

```python
from deepeval.metrics import ToolCorrectnessMetric
from deepeval.test_case import LLMTestCase, ToolCall

metric = ToolCorrectnessMetric(threshold=0.7)

test_case = LLMTestCase(
    input="What's the weather in San Francisco?",
    actual_output="It's 65°F and sunny in San Francisco.",
    tools_called=[
        ToolCall(
            name="WeatherAPI",
            input_parameters={"city": "San Francisco"},
            output={"temp": 65, "condition": "sunny"}
        )
    ],
    expected_tools=[
        ToolCall(name="WeatherAPI")
    ]
)

metric.measure(test_case)
```

**Required fields:** `input`, `actual_output`, `tools_called`, `expected_tools`

### ArgumentCorrectnessMetric

Evaluates whether the correct arguments were passed to tool calls:

```python
from deepeval.metrics import ArgumentCorrectnessMetric

metric = ArgumentCorrectnessMetric(threshold=0.7)
metric.measure(test_case)  # Uses same test_case with tools_called
```

**Required fields:** `input`, `actual_output`, `tools_called`

### StepEfficiencyMetric

Measures whether the agent took the optimal path to complete its task:

```python
from deepeval.metrics import StepEfficiencyMetric

metric = StepEfficiencyMetric(threshold=0.7)
metric.measure(test_case)
```

**Required fields:** `input`, `actual_output`

### PlanAdherenceMetric

Checks if the agent followed its stated plan:

```python
from deepeval.metrics import PlanAdherenceMetric

metric = PlanAdherenceMetric(threshold=0.7)
metric.measure(test_case)
```

### PlanQualityMetric

Evaluates the quality and completeness of the agent's plan:

```python
from deepeval.metrics import PlanQualityMetric

metric = PlanQualityMetric(threshold=0.7)
metric.measure(test_case)
```

## Agent Evaluation Architecture

Agent evaluation uses a three-step instrumentation process:

1. **Instrument the agent** — Wrap top-level functions with `@observe()` or use framework-specific handlers
2. **Automatic trace emission** — Every execution generates spans for each component
3. **Metric attachment** — Apply metrics at trace level or individual span level

```
Agent Call (Trace)
├── LLM Span: Initial reasoning
├── Tool Span: WeatherAPI call
├── LLM Span: Process results
├── Retriever Span: Knowledge lookup
└── LLM Span: Final response
```

## Complete Agent Evaluation Example

### Dataset Setup

```python
from deepeval.dataset import Golden, EvaluationDataset

goldens = [
    Golden(input="What is your name?"),
    Golden(input="Book a meeting with John for tomorrow at 2pm"),
    Golden(input="Search for restaurants near Times Square"),
]
dataset = EvaluationDataset(goldens=goldens)
```

### CI/CD Testing with Pytest

```python
import pytest
from deepeval import assert_test
from deepeval.metrics import TaskCompletionMetric

@pytest.mark.parametrize("golden", dataset.goldens)
def test_agent(golden: Golden):
    agent.invoke(golden.input)  # Traced via @observe or callback
    assert_test(golden=golden, metrics=[TaskCompletionMetric()])
```

### Development Iteration with evals_iterator

```python
from deepeval.metrics import TaskCompletionMetric
from deepeval.dataset import AsyncConfig

for golden in dataset.evals_iterator(
    metrics=[TaskCompletionMetric()],
    async_config=AsyncConfig(run_async=False),
):
    agent.run_sync(golden.input)
```

## Framework-Specific Integration

### LangChain / LangGraph

```python
from deepeval.integrations.langchain import CallbackHandler

result = agent.invoke(
    {"input": golden.input},
    config={"callbacks": [CallbackHandler()]}
)
```

### OpenAI (Drop-in Replacement)

```python
from deepeval.openai import OpenAI

client = OpenAI()  # Automatically traced
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)
```

### Anthropic (Drop-in Replacement)

```python
from deepeval.anthropic import Anthropic

client = Anthropic()  # Automatically traced
```

### Manual Instrumentation

```python
from deepeval.tracing import observe, update_current_trace

@observe()
def my_agent(query: str) -> str:
    plan = plan_step(query)
    result = execute_step(plan)
    update_current_trace(input=query, output=result)
    return result

@observe(type="tool")
def search_tool(query: str) -> str:
    return search_api.search(query)

@observe(type="llm")
def reasoning_step(context: str) -> str:
    return llm.generate(context)
```

## Sub-Agent Evaluation

For multi-agent systems, attach metrics to specific sub-agent spans:

```python
@observe(type="agent", metrics=[TaskCompletionMetric()])
def research_agent(query: str) -> str:
    results = web_search(query)
    summary = summarize(results)
    return summary

@observe(type="agent", metrics=[TaskCompletionMetric()])
def writing_agent(topic: str, research: str) -> str:
    draft = generate_draft(topic, research)
    return draft

@observe()
def orchestrator(query: str) -> str:
    research = research_agent(query)
    article = writing_agent(query, research)
    update_current_trace(input=query, output=article)
    return article
```

Each sub-agent gets its own score, independent of the overall trace evaluation.

## Agent Metric Selection Guide

| Goal | Primary Metric | Secondary |
|------|---------------|-----------|
| Did the task succeed? | TaskCompletion | StepEfficiency |
| Correct tool usage? | ToolCorrectness | ArgumentCorrectness |
| Optimal execution? | StepEfficiency | PlanAdherence |
| Planning quality? | PlanQuality | PlanAdherence |
| Full agent audit | TaskCompletion + ToolCorrectness | StepEfficiency |

## Common Pitfalls

1. **Not using tracing** — Agent metrics work best with `@observe` traces that capture tool calls and reasoning steps
2. **Missing `tools_called`** — ToolCorrectness needs actual tool invocation data
3. **Evaluating only end-to-end** — Sub-agent failures hide behind passing trace-level scores
4. **No expected_tools baseline** — ToolCorrectness needs both `tools_called` and `expected_tools`
5. **Ignoring step efficiency** — An agent that reaches the right answer via 20 steps when 3 would suffice is wasting tokens
