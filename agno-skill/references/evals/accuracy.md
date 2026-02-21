# Accuracy Evals

Measure how well Agents and Teams perform against a gold-standard answer using LLM-as-a-judge methodology.

## How It Works

1. Provide `input` (prompt) and `expected_output` (gold answer)
2. Agent/Team runs with the input to produce actual output
3. An evaluator model scores how well the actual response matches expected output
4. Score returned on 1-10 scale; `avg_score` aggregated across iterations

## AccuracyEval Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `Optional[str]` | Name for this evaluation |
| `model` | `Model` | Evaluator model (scores the response) |
| `agent` | `Optional[Agent]` | Agent to evaluate |
| `team` | `Optional[Team]` | Team to evaluate (use instead of `agent`) |
| `input` | `str` | The prompt to send to the agent/team |
| `expected_output` | `str` | The gold-standard answer to compare against |
| `additional_guidelines` | `Optional[str]` | Extra guidelines for the evaluator |
| `num_iterations` | `int` | Number of times to run the eval (default: 1) |
| `evaluator_agent` | `Optional[Agent]` | Custom evaluator agent (LLM-as-a-judge) |
| `db` | `Optional[BaseDb]` | Database for persisting results |

## AccuracyResult

```python
result: Optional[AccuracyResult] = evaluation.run(print_results=True)
result.avg_score      # float — Average score across iterations (1-10)
result.results        # List of individual iteration results
```

## Basic Example

```python
from typing import Optional
from agno.agent import Agent
from agno.eval.accuracy import AccuracyEval, AccuracyResult
from agno.models.openai import OpenAIResponses
from agno.tools.calculator import CalculatorTools

evaluation = AccuracyEval(
    name="Calculator Evaluation",
    model=OpenAIResponses(id="gpt-5.2"),
    agent=Agent(
        model=OpenAIResponses(id="gpt-5.2"),
        tools=[CalculatorTools()],
    ),
    input="What is 10*5 then to the power of 2? do it step by step",
    expected_output="2500",
    additional_guidelines="Agent output should include the steps and the final answer.",
    num_iterations=3,
)

result: Optional[AccuracyResult] = evaluation.run(print_results=True)
assert result is not None and result.avg_score >= 8
```

## Custom Evaluator Agent (LLM-as-a-Judge)

Use a dedicated agent with custom instructions to evaluate responses:

```python
from agno.eval.accuracy import AccuracyAgentResponse, AccuracyEval

evaluator_agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    output_schema=AccuracyAgentResponse,  # Required schema for evaluator
    # instructions="Custom evaluator instructions here",
)

evaluation = AccuracyEval(
    model=OpenAIResponses(id="gpt-5.2"),
    agent=Agent(model=OpenAIResponses(id="gpt-5.2"), tools=[CalculatorTools()]),
    input="What is 10*5 then to the power of 2? do it step by step",
    expected_output="2500",
    evaluator_agent=evaluator_agent,
    additional_guidelines="Agent output should include the steps and the final answer.",
)

result: Optional[AccuracyResult] = evaluation.run(print_results=True)
```

**Key:** The evaluator agent must use `output_schema=AccuracyAgentResponse`.

## Accuracy with Given Output

Skip the agent run and evaluate a pre-existing output directly using `run_with_output()`:

```python
evaluation = AccuracyEval(
    name="Given Answer Evaluation",
    model=OpenAIResponses(id="gpt-5.2"),
    input="What is 10*5 then to the power of 2?",
    expected_output="2500",
)

result = evaluation.run_with_output(output="2500", print_results=True)
```

## Accuracy with Teams

Pass `team=` instead of `agent=`:

```python
from agno.team.team import Team

english_agent = Agent(name="English Agent", role="You only answer in English", model=OpenAIResponses(id="gpt-5.2"))
spanish_agent = Agent(name="Spanish Agent", role="You can only answer in Spanish", model=OpenAIResponses(id="gpt-5.2"))

multi_language_team = Team(
    name="Multi Language Team",
    model=OpenAIResponses(id="gpt-5.2"),
    members=[english_agent, spanish_agent],
    respond_directly=True,
    instructions=[
        "You are a language router that directs questions to the appropriate language agent.",
        "If the user asks in a language whose agent is not a team member, respond in English.",
    ],
)

evaluation = AccuracyEval(
    name="Multi Language Team",
    model=OpenAIResponses(id="gpt-5.2"),
    team=multi_language_team,
    input="Comment allez-vous?",
    expected_output="I can only answer in the following languages: English and Spanish.",
    num_iterations=1,
)

result: Optional[AccuracyResult] = evaluation.run(print_results=True)
```

## Async Support

```python
import asyncio

result: Optional[AccuracyResult] = asyncio.run(evaluation.arun(print_results=True))
```

## Methods

| Method | Description |
|--------|-------------|
| `run(print_results=False)` | Run evaluation synchronously |
| `arun(print_results=False)` | Run evaluation asynchronously |
| `run_with_output(output, print_results=False)` | Evaluate a given output without running the agent |

## Key Imports

```python
from agno.eval.accuracy import AccuracyEval, AccuracyResult, AccuracyAgentResponse
```
