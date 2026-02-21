# Reliability Evals

Measure how well Agents and Teams handle tool calls and error scenarios.

## What Makes an Agent Reliable?

- Does it make the **expected tool calls**?
- Does it handle **errors gracefully**?
- Does it respect **rate limits** of the model API?

## How It Works

1. Run the agent/team first to get a `RunOutput` / `TeamRunOutput`
2. Pass the response + expected tool call names to `ReliabilityEval`
3. The eval checks if all expected tools were actually called
4. Returns pass/fail result

**Key difference from AccuracyEval:** ReliabilityEval takes a pre-existing response (`agent_response` / `team_response`), not an agent to run.

## ReliabilityEval Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `Optional[str]` | Name for this evaluation |
| `agent_response` | `Optional[RunOutput]` | Agent response to evaluate |
| `team_response` | `Optional[TeamRunOutput]` | Team response to evaluate (use instead of `agent_response`) |
| `expected_tool_calls` | `List[str]` | List of tool function names expected to have been called |
| `db` | `Optional[BaseDb]` | Database for persisting results |

## ReliabilityResult

```python
result: Optional[ReliabilityResult] = evaluation.run(print_results=True)
result.assert_passed()  # Raises AssertionError if failed
```

## Basic — Single Tool Call

```python
from typing import Optional
from agno.agent import Agent
from agno.eval.reliability import ReliabilityEval, ReliabilityResult
from agno.models.openai import OpenAIResponses
from agno.run.agent import RunOutput
from agno.tools.calculator import CalculatorTools

def factorial():
    agent = Agent(
        model=OpenAIResponses(id="gpt-5.2"),
        tools=[CalculatorTools()],
    )
    response: RunOutput = agent.run("What is 10!?")

    evaluation = ReliabilityEval(
        name="Tool Call Reliability",
        agent_response=response,
        expected_tool_calls=["factorial"],
    )
    result: Optional[ReliabilityResult] = evaluation.run(print_results=True)
    result.assert_passed()
```

## Multiple Tool Calls

Verify the agent makes multiple expected tool calls in sequence:

```python
def multiply_and_exponentiate():
    agent = Agent(
        model=OpenAIResponses(id="gpt-5.2"),
        tools=[CalculatorTools()],
    )
    response: RunOutput = agent.run(
        "What is 10*5 then to the power of 2? do it step by step"
    )

    evaluation = ReliabilityEval(
        name="Tool Calls Reliability",
        agent_response=response,
        expected_tool_calls=["multiply", "exponentiate"],
    )
    result: Optional[ReliabilityResult] = evaluation.run(print_results=True)
    if result:
        result.assert_passed()
```

## Team Reliability

Test team tool delegation with `team_response=`:

```python
from agno.run.team import TeamRunOutput
from agno.team.team import Team
from agno.tools.yfinance import YFinanceTools

team_member = Agent(
    name="Stock Searcher",
    model=OpenAIResponses("gpt-5.2"),
    role="Searches the web for information on a stock.",
    tools=[YFinanceTools(stock_price=True)],
)

team = Team(
    name="Stock Research Team",
    model=OpenAIResponses("gpt-5.2"),
    members=[team_member],
    markdown=True,
    show_members_responses=True,
)

expected_tool_calls = [
    "delegate_task_to_member",  # Team delegation tool
    "get_current_stock_price",  # Member's tool
]

def evaluate_team_reliability():
    response: TeamRunOutput = team.run("What is the current stock price of NVDA?")

    evaluation = ReliabilityEval(
        name="Team Reliability Evaluation",
        team_response=response,
        expected_tool_calls=expected_tool_calls,
    )
    result: Optional[ReliabilityResult] = evaluation.run(print_results=True)
    if result:
        result.assert_passed()
```

**Note:** For teams, include `"delegate_task_to_member"` in expected tool calls — this is the internal tool used to delegate tasks to team members.

## Methods

| Method | Description |
|--------|-------------|
| `run(print_results=False)` | Run evaluation synchronously |
| `result.assert_passed()` | Assert the eval passed (raises `AssertionError` if failed) |

## Key Imports

```python
from agno.eval.reliability import ReliabilityEval, ReliabilityResult
from agno.run.agent import RunOutput
from agno.run.team import TeamRunOutput
```
