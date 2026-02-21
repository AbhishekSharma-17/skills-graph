# Agent as Judge Evals

Evaluate custom quality criteria for Agents and Teams using LLM-as-a-judge methodology with flexible scoring.

## How It Works

1. Run your agent to produce output
2. Define custom `criteria` (e.g. "professional tone", "factual accuracy")
3. `AgentAsJudgeEval` uses an LLM to score the output against your criteria
4. Returns score + reason + pass/fail status

## Key Difference from AccuracyEval

| AccuracyEval | AgentAsJudgeEval |
|-------------|-----------------|
| Compares output to expected answer | Evaluates against custom criteria |
| Runs the agent internally | Takes pre-generated output |
| Always numeric (1-10) | Numeric (1-10) or binary (pass/fail) |
| Single criteria (correctness) | Any custom criteria |

## AgentAsJudgeEval Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `criteria` | `str` | `""` | Evaluation criteria — what makes a good response (required) |
| `scoring_strategy` | `Literal["numeric", "binary"]` | `"binary"` | `"numeric"` (1-10) or `"binary"` (pass/fail) |
| `threshold` | `int` | `7` | Minimum score to pass (numeric strategy only) |
| `on_fail` | `Optional[Callable]` | `None` | Callback when evaluation fails |
| `additional_guidelines` | `Optional[Union[str, List[str]]]` | `None` | Extra evaluation guidelines |
| `name` | `Optional[str]` | `None` | Evaluation name |
| `model` | `Optional[Model]` | `None` | Evaluator model (defaults to gpt-5-mini) |
| `evaluator_agent` | `Optional[Agent]` | `None` | Custom evaluator agent |
| `run_in_background` | `bool` | `False` | Run as non-blocking background task |
| `db` | `Optional[BaseDb]` | `None` | Database for persisting results |
| `debug_mode` | `bool` | `False` | Enable detailed logging |

## run() / arun() Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `input` | `Optional[str]` | `None` | Input text (for single evaluation) |
| `output` | `Optional[str]` | `None` | Output text (for single evaluation) |
| `cases` | `Optional[List[Dict[str, str]]]` | `None` | Batch evaluation — list of `{"input": ..., "output": ...}` |
| `print_summary` | `bool` | `False` | Print summary |
| `print_results` | `bool` | `False` | Print detailed results |

Provide either (`input`, `output`) **or** `cases`, not both.

## Basic Example — Numeric Scoring

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.eval.agent_as_judge import AgentAsJudgeEval
from agno.models.openai import OpenAIResponses

db = SqliteDb(db_file="tmp/agent_as_judge_basic.db")

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    instructions="You are a technical writer. Explain concepts clearly and concisely.",
    db=db,
)

response = agent.run("Explain what an API is")

evaluation = AgentAsJudgeEval(
    name="Explanation Quality",
    criteria="Explanation should be clear, beginner-friendly, and use simple language",
    scoring_strategy="numeric",  # Score 1-10
    threshold=7,                 # Pass if score >= 7
    db=db,
)

result = evaluation.run(
    input="Explain what an API is",
    output=str(response.content),
    print_results=True,
)
```

## on_fail Callback

Trigger custom logic when evaluation fails:

```python
from agno.eval.agent_as_judge import AgentAsJudgeEval, AgentAsJudgeEvaluation

def on_evaluation_failure(evaluation: AgentAsJudgeEvaluation):
    """Callback triggered when evaluation fails (score < threshold)."""
    print(f"Evaluation failed - Score: {evaluation.score}/10")
    print(f"Reason: {evaluation.reason[:100]}...")

evaluation = AgentAsJudgeEval(
    name="Explanation Quality",
    criteria="Explanation should be clear, beginner-friendly",
    scoring_strategy="numeric",
    threshold=9,  # Strict threshold
    on_fail=on_evaluation_failure,
    db=db,
)
```

## Custom Evaluator Agent

Use a custom agent with specific instructions as the judge:

```python
custom_evaluator = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    description="Strict technical evaluator",
    instructions="You are a strict evaluator. Only pass exceptionally clear and accurate explanations.",
)

evaluation = AgentAsJudgeEval(
    name="Technical Accuracy",
    criteria="Explanation must be technically accurate and comprehensive",
    evaluator_agent=custom_evaluator,
)

result = evaluation.run(
    input="Explain what an API is",
    output=str(response.content),
    print_results=True,
    print_summary=True,
)
```

## As a Post-Hook (Automatic Evaluation)

Run evaluation automatically after every agent run:

```python
agent_as_judge_eval = AgentAsJudgeEval(
    name="Response Quality Check",
    model=OpenAIResponses(id="gpt-5.2"),
    criteria="Response should be professional, well-structured, and provide balanced perspectives",
    scoring_strategy="numeric",
    threshold=7,
    db=db,
)

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    instructions="Provide professional and well-reasoned answers.",
    post_hooks=[agent_as_judge_eval],  # Runs after every agent.run()
    db=db,
)

response = agent.run("What are the benefits of renewable energy?")

# Query stored results
eval_runs = db.get_eval_runs()
if eval_runs:
    latest = eval_runs[-1]
    if latest.eval_data and "results" in latest.eval_data:
        result = latest.eval_data["results"][0]
        print(f"Score: {result.get('score', 'N/A')}/10")
        print(f"Status: {'PASSED' if result.get('passed') else 'FAILED'}")
```

## Database Persistence

Store and query eval results:

```python
db = SqliteDb(db_file="tmp/agent_as_judge.db")

evaluation = AgentAsJudgeEval(
    name="Quality Check",
    criteria="Response should be helpful",
    db=db,
)

# After running...
eval_runs = db.get_eval_runs()
print(f"Total evaluations stored: {len(eval_runs)}")
if eval_runs:
    latest = eval_runs[-1]
    print(f"Eval ID: {latest.run_id}")
    print(f"Name: {latest.name}")
```

## Key Imports

```python
from agno.eval.agent_as_judge import AgentAsJudgeEval, AgentAsJudgeEvaluation
```
