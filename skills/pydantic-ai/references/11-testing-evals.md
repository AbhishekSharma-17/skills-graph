# Testing and Evals

> Source: [pydantic.dev/docs/ai/testing](https://pydantic.dev/docs/ai/testing/) | [pydantic.dev/docs/ai/evals](https://pydantic.dev/docs/ai/evals/)

## Table of Contents

- [Overview](#overview)
- [TestModel](#testmodel)
- [FunctionModel](#functionmodel)
- [Agent Override](#agent-override)
- [Blocking Real Model Requests](#blocking-real-model-requests)
- [Capturing Messages](#capturing-messages)
- [Pytest Patterns](#pytest-patterns)
- [Pydantic Evals](#pydantic-evals)
- [Online Evaluation](#online-evaluation)
- [Common Pitfalls](#common-pitfalls)

## Overview

Pydantic AI provides two testing strategies:

1. **Unit testing** — use `TestModel` or `FunctionModel` to exercise application code without real LLM calls
2. **Evaluation** — use Pydantic Evals to systematically test and benchmark agents with datasets and scoring

## TestModel

`TestModel` is the simplest way to test agents. By default, it calls all tools, then returns plain text or structured output based on the agent's output type:

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-5.2')

@agent.tool_plain
def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f'{city}: sunny, 22°C'

# Test with TestModel
result = agent.run_sync('What is the weather?', model='test')
print(result.output)
# TestModel generates a valid response, calling all tools
```

### TestModel With Structured Output

```python
from pydantic import BaseModel

class CityInfo(BaseModel):
    city: str
    country: str

agent = Agent('openai:gpt-5.2', output_type=CityInfo)

result = agent.run_sync('Tell me about Paris', model='test')
print(result.output)
# CityInfo(city='a', country='a')  — TestModel generates valid but minimal data
```

### Custom TestModel Data

```python
from pydantic_ai.models.test import TestModel

model = TestModel(custom_output_text='Hello from test!')
result = agent.run_sync('Hi', model=model)
print(result.output)  # 'Hello from test!'
```

## FunctionModel

`FunctionModel` gives full control over the model's behavior — essential for testing specific tool call sequences:

```python
from pydantic_ai import Agent
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.messages import (
    ModelResponse,
    TextPart,
    ToolCallPart,
)

def my_model(messages, info):
    # On first call, call a tool
    if info.function_tools and not any(
        isinstance(m, ModelResponse) for m in messages
    ):
        return ModelResponse(parts=[
            ToolCallPart(
                tool_name='get_weather',
                args={'city': 'London'},
            )
        ])
    # On second call, return text
    return ModelResponse(parts=[TextPart('The weather is great!')])

agent = Agent('openai:gpt-5.2')

@agent.tool_plain
def get_weather(city: str) -> str:
    return f'{city}: sunny'

result = agent.run_sync('Weather?', model=FunctionModel(my_model))
print(result.output)  # 'The weather is great!'
```

## Agent Override

`agent.override()` replaces model, deps, or toolsets within a context manager — ideal for testing application code that internally creates agents:

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-5.2', deps_type=str)

# Application code
async def get_answer(question: str) -> str:
    result = await agent.run(question, deps='real-api-key')
    return result.output

# Test code
async def test_get_answer():
    with agent.override(model='test', deps='test-key'):
        answer = await get_answer('What is 2+2?')
    assert answer  # TestModel output
```

### Override With Custom Model

```python
with agent.override(model=FunctionModel(my_model)):
    result = agent.run_sync('Hello')
```

### Override Scope

Overrides apply only within the `with` block. Multiple overrides can nest:

```python
with agent.override(model='test'):
    # Uses TestModel
    result1 = agent.run_sync('Hello')

    with agent.override(deps='special-deps'):
        # Uses TestModel AND special deps
        result2 = agent.run_sync('Hello')
```

## Blocking Real Model Requests

Prevent accidental real API calls in tests:

```python
import pytest
from pydantic_ai import ALLOW_MODEL_REQUESTS

@pytest.fixture(autouse=True)
def block_model_requests():
    with ALLOW_MODEL_REQUESTS.override(False):
        yield
    # Any real model request raises an error
```

## Capturing Messages

Inspect the full message exchange for assertions:

```python
from pydantic_ai import capture_run_messages

with capture_run_messages() as messages:
    result = agent.run_sync('Hello', model='test')

# Inspect messages
for msg in messages:
    print(type(msg).__name__, msg)
```

### Asserting Tool Calls

```python
from pydantic_ai.messages import ToolCallPart

with capture_run_messages() as messages:
    result = agent.run_sync('Get weather', model='test')

tool_calls = [
    part
    for msg in messages
    if hasattr(msg, 'parts')
    for part in msg.parts
    if isinstance(part, ToolCallPart)
]
assert any(tc.tool_name == 'get_weather' for tc in tool_calls)
```

## Pytest Patterns

### Fixture for Model Override

```python
import pytest
from pydantic_ai import ALLOW_MODEL_REQUESTS

@pytest.fixture(autouse=True)
def no_real_requests():
    with ALLOW_MODEL_REQUESTS.override(False):
        yield

@pytest.fixture
def test_agent():
    with agent.override(model='test'):
        yield agent

async def test_my_feature(test_agent):
    result = await test_agent.run('Hello')
    assert result.output
```

### Parametrized Tests

```python
@pytest.mark.parametrize('question,expected_tool', [
    ('What is the weather?', 'get_weather'),
    ('Calculate 2+2', 'calculate'),
])
async def test_tool_routing(question, expected_tool):
    with capture_run_messages() as messages:
        with agent.override(model='test'):
            await agent.run(question)

    tool_names = [
        p.tool_name for m in messages
        for p in getattr(m, 'parts', [])
        if isinstance(p, ToolCallPart)
    ]
    assert expected_tool in tool_names
```

## Pydantic Evals

Systematic evaluation framework for testing AI systems with datasets, evaluators, and scoring.

### Core Concepts

| Concept | Purpose |
|---------|---------|
| **Dataset** | Collection of test cases with evaluators |
| **Case** | Single test scenario with inputs and expected outputs |
| **Evaluator** | Scoring/validation logic (deterministic or LLM-based) |
| **Experiment** | Running a task function against all cases |

### Basic Evaluation

```python
from pydantic_evals import Dataset, Case
from pydantic_evals.evaluators import Evaluator, EvaluatorContext

class OutputNotEmpty(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return bool(ctx.output)

dataset = Dataset(
    cases=[
        Case(inputs='What is Python?', expected_output='programming language'),
        Case(inputs='What is 2+2?', expected_output='4'),
    ],
    evaluators=[OutputNotEmpty()],
)

async def my_task(inputs: str) -> str:
    result = await agent.run(inputs)
    return result.output

report = await dataset.evaluate(my_task)
report.print()
```

### LLM Judge Evaluator

```python
from pydantic_evals.evaluators import LLMJudge

dataset = Dataset(
    cases=[Case(inputs='Explain quantum computing')],
    evaluators=[
        LLMJudge(
            rubric='Is the explanation accurate and accessible to beginners?',
            model='openai:gpt-5.2',
        ),
    ],
)
```

## Online Evaluation

Attach evaluators to production functions for continuous quality monitoring:

```python
from pydantic_evals.evaluators import Evaluator, EvaluatorContext
from pydantic_evals.online import OnlineEvaluator, evaluate

class IsHelpful(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return len(str(ctx.output)) > 20

@evaluate(OnlineEvaluator(evaluator=IsHelpful(), sample_rate=0.1))
async def handle_query(query: str) -> str:
    result = await agent.run(query)
    return result.output
```

### Agent Integration

```python
from pydantic_ai import Agent
from pydantic_evals.online_capability import OnlineEvaluation

agent = Agent(
    'openai:gpt-5.2',
    name='support-agent',
    capabilities=[OnlineEvaluation(evaluators=[IsHelpful()])],
)
```

## Common Pitfalls

- **TestModel limitations** — `TestModel` calls all tools with generated data; it doesn't test intelligent tool selection
- **FunctionModel complexity** — for complex tool sequences, `FunctionModel` requires careful message construction
- **ALLOW_MODEL_REQUESTS scope** — set it in a fixture to avoid accidentally blocking requests in production code
- **Eval costs** — LLM-based evaluators (like `LLMJudge`) consume tokens; use `sample_rate` to control costs
- **Override nesting** — overrides don't stack cumulatively; each `override()` replaces the full context

## Related

- `01-agents.md` — Agent run methods
- `02-dependencies.md` — Override deps for testing
- `12-logfire-observability.md` — Monitoring and debugging
