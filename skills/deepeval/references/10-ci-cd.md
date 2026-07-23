# CI/CD Integration

> Source: https://deepeval.com/docs/evaluation-unit-testing-in-ci-cd

## Overview

DeepEval integrates LLM evaluations into CI/CD pipelines through pytest. The framework uses `assert_test()` for gating deployments and `deepeval test run` as the execution command. It plugs into any CI provider that runs shell steps — GitHub Actions, GitLab CI, CircleCI, Jenkins.

## Three-Step Integration

1. **Load datasets** from Confident AI, CSV, JSON, or inline code
2. **Construct test cases** using parametrized pytest tests with `assert_test()`
3. **Execute** with `deepeval test run` instead of plain pytest

## Why deepeval test run Over pytest

`deepeval test run` wraps pytest with additional capabilities:

- Async evaluation behavior
- Error handling and skip-on-missing
- Test run caching
- Run identification and baselining
- Parallel metric execution
- Automatic Confident AI reporting
- Post-run inspection prompt

## Test File Structure

```python
# tests/test_llm_app.py
import pytest
from deepeval import assert_test
from deepeval.dataset import Golden, EvaluationDataset
from deepeval.test_case import LLMTestCase
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric

# Load or create dataset
dataset = EvaluationDataset(goldens=[
    Golden(input="What is your return policy?"),
    Golden(input="How do I contact support?"),
    Golden(input="What payment methods do you accept?"),
])

@pytest.mark.parametrize("golden", dataset.goldens)
def test_rag_quality(golden: Golden):
    answer, retrieved = rag_pipeline(golden.input)
    test_case = LLMTestCase(
        input=golden.input,
        actual_output=answer,
        retrieval_context=retrieved,
    )
    assert_test(test_case, [
        AnswerRelevancyMetric(threshold=0.7),
        FaithfulnessMetric(threshold=0.7),
    ])
```

## Running Tests

### Basic Execution

```bash
deepeval test run tests/test_llm_app.py
```

### With Flags

```bash
# Parallel execution with 4 processes
deepeval test run tests/ -n 4

# Stop on first failure
deepeval test run tests/ -x

# Use cached results
deepeval test run tests/ -c

# Label the run
deepeval test run tests/ -id "v2.1-release"

# Mark as official baseline
deepeval test run tests/ -o

# Verbose output
deepeval test run tests/ -v

# Skip tests with missing parameters
deepeval test run tests/ -s

# Repeat tests 3 times
deepeval test run tests/ -r 3
```

### Command Reference

| Flag | Short | Type | Description |
|------|-------|------|-------------|
| `--verbose` | `-v` | bool | Detailed output |
| `--exit-on-first-failure` | `-x` | bool | Stop on first failure |
| `--num-processes` | `-n` | int | Parallel test execution |
| `--use-cache` | `-c` | bool | Cache metric results |
| `--repeat` | `-r` | int | Rerun tests N times |
| `--identifier` | `-id` | str | Label the test run |
| `--official` | `-o` | bool | Mark as baseline run |
| `--skip-on-missing-params` | `-s` | bool | Skip instead of error |
| `--show-warnings` | `-w` | bool | Display warnings |
| `--ignore-errors` | `-i` | bool | Continue despite errors |
| `--mark` | `-m` | str | Filter by pytest markers |
| `--display` | `-d` | str | Result presentation format |

## GitHub Actions Workflow

```yaml
name: LLM Evaluation Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.10"

      - name: Install Dependencies
        run: |
          pip install -r requirements.txt
          pip install deepeval

      - name: Run LLM Evaluations
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          CONFIDENT_API_KEY: ${{ secrets.CONFIDENT_API_KEY }}
        run: deepeval test run tests/test_llm_app.py
```

### With Poetry

```yaml
      - name: Install Poetry
        run: |
          curl -sSL https://install.python-poetry.org | python3 -
          echo "$HOME/.local/bin" >> $GITHUB_PATH

      - name: Install Dependencies
        run: poetry install --no-root

      - name: Run Evaluations
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: poetry run deepeval test run tests/
```

## Loading Datasets in CI

### From Local Files

```python
dataset = EvaluationDataset()
dataset.add_goldens_from_json_file("tests/fixtures/goldens.json")
```

### From Confident AI

```python
dataset = EvaluationDataset()
dataset.pull(alias="Production Eval Dataset")
```

### Inline

```python
dataset = EvaluationDataset(goldens=[
    Golden(input="Question 1"),
    Golden(input="Question 2"),
])
```

## With Tracing (Instrumented Apps)

When your app uses `@observe`:

```python
@pytest.mark.parametrize("golden", dataset.goldens)
def test_agent(golden: Golden):
    my_traced_agent(golden.input)  # @observe'd function
    assert_test(golden=golden, metrics=[TaskCompletionMetric()])
```

Metrics attached to spans via `@observe(metrics=[...])` run automatically — you only need to pass end-to-end metrics to `assert_test()`.

## Caching for Speed

Enable caching to skip unchanged metric evaluations:

```bash
deepeval test run tests/ -c
```

Cached results are stored locally and reused when the same test case + metric combination is encountered.

## Official Baseline Runs

Mark a run as the official baseline for regression tracking:

```bash
deepeval test run tests/ -o -id "v2.0-baseline"
```

Or programmatically:

```python
evaluate(test_cases=[...], metrics=[...], official=True)
```

Subsequent runs are compared against the latest official run on Confident AI.

## Viewing Results

### Terminal Inspection

```bash
deepeval inspect
```

Opens a TUI showing per-test scores, reasons, and pass/fail status.

### Confident AI Dashboard

```bash
deepeval view
```

Opens the latest run in the browser on Confident AI (requires login).

### Local JSON Storage

```bash
export DEEPEVAL_RESULTS_FOLDER="./eval-results"
deepeval test run tests/
```

Results saved as JSON to the specified folder.

## Common Pitfalls

1. **Missing API keys in CI** — Set `OPENAI_API_KEY` as a secret; `CONFIDENT_API_KEY` optional
2. **Using `pytest` instead of `deepeval test run`** — Loses DeepEval features
3. **No caching in CI** — Use `-c` flag to speed up iterative runs
4. **Threshold too low** — Production pipelines should use 0.7+ thresholds
5. **No official baseline** — Use `--official` to establish regression reference points
6. **Giant datasets in CI** — Start with 10-20 representative goldens; expand later
