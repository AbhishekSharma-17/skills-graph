# Evals

Measure the quality of your Agents and Teams across multiple dimensions.

## Docs Hierarchy

```
Evals
├── Overview                          ← this router
├── Accuracy
│   ├── Overview                      → accuracy.md
│   └── Usage
│       ├── Basic Accuracy
│       └── Accuracy with Teams
├── Performance
│   ├── Overview                      → performance.md
│   └── Usage
│       ├── Performance on Agent Response
│       └── Performance with Database Logging
├── Reliability
│   ├── Overview                      → reliability.md
│   └── Usage
│       ├── Reliability with Single Tool
│       └── Team Reliability with Stock Tools
└── Agent as Judge
    ├── Overview                      → agent-as-judge.md
    └── Usage
        ├── Basic Agent as Judge
        └── Agent as Judge as Post-Hook
```

## Evaluation Dimensions

| Dimension | What It Measures | Class | Import |
|-----------|-----------------|-------|--------|
| **Accuracy** | Correctness via LLM-as-a-judge | `AccuracyEval` | `agno.eval.accuracy` |
| **Performance** | Latency & memory footprint | `PerformanceEval` | `agno.eval.performance` |
| **Reliability** | Expected tool calls & error handling | `ReliabilityEval` | `agno.eval.reliability` |
| **Agent as Judge** | Custom quality criteria with scoring | `AgentAsJudgeEval` | `agno.eval.agent_as_judge` |

## Sub-References

| File | Read When |
|------|-----------|
| `evals/accuracy.md` | Accuracy evals, LLM-as-a-judge, expected output comparison, evaluator agents, teams |
| `evals/performance.md` | Latency benchmarks, memory profiling, instantiation perf, warmup, async perf |
| `evals/reliability.md` | Tool call verification, single/multiple tool calls, team reliability |
| `evals/agent-as-judge.md` | Custom criteria evaluation, numeric/binary scoring, post-hook evals, on_fail callbacks |

## Eval Constructor Parameters

### AccuracyEval

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `Optional[str]` | `None` | Name for this evaluation |
| `model` | `Model` | Required | Evaluator model (scores the response) |
| `agent` | `Optional[Agent]` | `None` | Agent to evaluate |
| `team` | `Optional[Team]` | `None` | Team to evaluate (use instead of `agent`) |
| `input` | `str` | Required | The prompt to send to the agent/team |
| `expected_output` | `str` | Required | The gold-standard answer to compare against |
| `additional_guidelines` | `Optional[str]` | `None` | Extra guidelines for the evaluator |
| `num_iterations` | `int` | `1` | Number of times to run the eval |
| `evaluator_agent` | `Optional[Agent]` | `None` | Custom evaluator agent (must use `output_schema=AccuracyAgentResponse`) |
| `db` | `Optional[BaseDb]` | `None` | Database for persisting results |

### PerformanceEval

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `Optional[str]` | `None` | Name for this evaluation |
| `func` | `Callable` | Required | Function to benchmark (must return something) |
| `num_iterations` | `int` | `1` | Number of times to run |
| `warmup_runs` | `int` | `0` | Warmup iterations before measuring |
| `measure_runtime` | `bool` | `True` | Measure execution time |
| `memory_growth_tracking` | `bool` | `False` | Track memory growth across iterations |
| `debug_mode` | `bool` | `False` | Enable detailed logging |
| `db` | `Optional[BaseDb]` | `None` | Database for persisting results |

### ReliabilityEval

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `Optional[str]` | `None` | Name for this evaluation |
| `agent_response` | `Optional[RunOutput]` | `None` | Agent response to evaluate |
| `team_response` | `Optional[TeamRunOutput]` | `None` | Team response to evaluate (use instead of `agent_response`) |
| `expected_tool_calls` | `List[str]` | Required | List of tool function names expected to have been called |
| `db` | `Optional[BaseDb]` | `None` | Database for persisting results |

### AgentAsJudgeEval

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
| `run_in_background` | `bool` | `False` | Run as non-blocking background task (useful as post-hook) |
| `db` | `Optional[BaseDb]` | `None` | Database for persisting results |
| `debug_mode` | `bool` | `False` | Enable detailed logging |

## Eval Methods

| Method | Applies To | Description |
|--------|-----------|-------------|
| `run(print_results=False)` | All evals | Run evaluation synchronously |
| `arun(print_results=False)` | All evals | Run evaluation asynchronously |
| `run_with_output(output, print_results=False)` | AccuracyEval | Evaluate a given output without running the agent |
| `result.assert_passed()` | ReliabilityEval | Assert the eval passed (raises `AssertionError` if failed) |

## Quick Start

```python
from agno.eval.accuracy import AccuracyEval, AccuracyResult
from agno.eval.performance import PerformanceEval
from agno.eval.reliability import ReliabilityEval, ReliabilityResult
from agno.eval.agent_as_judge import AgentAsJudgeEval
```

## Install

```bash
uv pip install -U agno             # Core (accuracy, reliability, agent-as-judge)
uv pip install -U memory_profiler  # Required for performance evals
```

## AgentOS Integration

All eval types support `db=` parameter to persist results to a database. View results at https://os.agno.com/evaluation or via API endpoints:

```
GET /eval-runs
GET /eval-runs/{id}
GET /eval-runs?agent_id={id}
GET /eval-runs/accuracy
GET /eval-runs/performance
GET /eval-runs/reliability
```

## Best Practices

- **Start simple** — begin with basic accuracy tests before complex performance/reliability evals
- **Multiple test cases** — build comprehensive suites covering edge cases
- **Track over time** — monitor metrics continuously as you iterate
- **Combine dimensions** — evaluate across all dimensions for holistic quality view
- **Use `num_iterations`** — run accuracy evals multiple times for statistical confidence
- **Warmup runs** — use `warmup_runs` for performance evals to eliminate cold-start noise
