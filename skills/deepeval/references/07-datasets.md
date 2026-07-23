# Datasets

> Source: https://deepeval.com/docs/evaluation-datasets

## Overview

An evaluation dataset in DeepEval comprises **goldens** — precursors to test cases. During evaluation, goldens convert into test cases by adding your LLM's actual output. Datasets can be single-turn (using `Golden`) or multi-turn (using `ConversationalGolden`).

## Golden vs Test Case

| Aspect | Golden | Test Case |
|--------|--------|-----------|
| Purpose | Template with expected data | Fully formed for scoring |
| Required fields | `input` (single-turn) or `scenario` (multi-turn) | `input` + `actual_output` |
| Contains | Expected outputs, context | Expected + actual outputs |
| When created | Before evaluation | During evaluation |
| Reusable | Yes — across model versions | No — tied to specific run |

## Creating Datasets

### Single-Turn Dataset

```python
from deepeval.dataset import EvaluationDataset, Golden

dataset = EvaluationDataset(goldens=[
    Golden(input="What is your return policy?"),
    Golden(
        input="How do I reset my password?",
        expected_output="Go to Settings > Security > Reset Password.",
        context=["Password reset is available under Settings > Security."]
    ),
    Golden(
        input="What payment methods do you accept?",
        expected_output="We accept Visa, Mastercard, and PayPal."
    ),
])
```

### Multi-Turn Dataset

```python
from deepeval.dataset import EvaluationDataset, ConversationalGolden

dataset = EvaluationDataset(goldens=[
    ConversationalGolden(
        scenario="Frustrated user asking for a refund.",
        expected_outcome="Redirected to a human agent.",
        user_description="An upset customer who received a damaged product."
    ),
    ConversationalGolden(
        scenario="User wants to purchase a VIP concert ticket.",
        expected_outcome="Successful ticket purchase.",
        user_description="Andy Byron, CEO of a tech company."
    ),
])
```

### Adding Goldens After Initialization

```python
dataset = EvaluationDataset()

# Single-turn
dataset.add_golden(Golden(input="New question"))

# Multi-turn
dataset.add_golden(ConversationalGolden(
    scenario="User needs technical support.",
    expected_outcome="Issue resolved."
))
```

## Golden Data Models

### Single-Turn Golden

```python
class Golden(BaseModel):
    input: str
    expected_output: str | None = None
    context: list[str] | None = None
    expected_tools: list[ToolCall] | None = None
    additional_metadata: dict | None = None
    comments: str | None = None
    actual_output: str | None = None          # Pre-filled for static datasets
    retrieval_context: list[str] | None = None
    tools_called: list[ToolCall] | None = None
```

### Multi-Turn Golden (ConversationalGolden)

```python
class ConversationalGolden(BaseModel):
    scenario: str
    expected_outcome: str | None = None
    user_description: str | None = None
    context: list[str] | None = None
    additional_metadata: dict | None = None
    comments: str | None = None
    turns: list[Turn] | None = None  # Pre-filled for static conversations
```

## Loading Datasets

### From JSON File

```python
dataset = EvaluationDataset()
dataset.add_goldens_from_json_file(file_path="goldens.json")
```

Expected JSON format:

```json
[
  {"input": "What is DeepEval?", "expected_output": "An LLM evaluation framework."},
  {"input": "How do I install it?", "expected_output": "pip install deepeval"}
]
```

### From JSONL File

```python
dataset = EvaluationDataset()
dataset.add_goldens_from_jsonl_file(file_path="goldens.jsonl")
```

Each line is one golden:

```json
{"input": "What is DeepEval?", "expected_output": "An LLM evaluation framework."}
{"input": "How do I install it?", "expected_output": "pip install deepeval"}
```

### From CSV File

```python
dataset = EvaluationDataset()
dataset.add_goldens_from_csv_file(file_path="goldens.csv")
```

### From JSON as Test Cases (Custom Column Names)

```python
dataset = EvaluationDataset()
dataset.add_test_cases_from_json_file(
    file_path="data.json",
    input_key_name="query",
    actual_output_key_name="response",
    expected_output_key_name="ideal_response",
    context_key_name="ground_truth",
    retrieval_context_key_name="retrieved_chunks"
)
```

### From CSV as Test Cases

```python
dataset.add_test_cases_from_csv_file(
    file_path="data.csv",
    input_col_name="query",
    actual_output_col_name="response",
    context_col_name="ground_truth",
    context_col_delimiter=";"
)
```

### From Confident AI

```python
dataset = EvaluationDataset()
dataset.pull(alias="My Dataset")
print(dataset.goldens)
```

## Saving Datasets

### To Confident AI

```python
dataset.push(alias="Production Eval Dataset")
dataset.push(alias="Draft Dataset", finalized=False)
```

### To Local Files

```python
# JSON
dataset.save_as(file_type="json", directory="./eval-data")

# CSV
dataset.save_as(file_type="csv", directory="./eval-data")

# Include test cases (not just goldens)
dataset.save_as(
    file_type="json",
    directory="./eval-data",
    include_test_cases=True
)
```

## Running Evaluations

### Single-Turn with Pytest

```python
import pytest
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase

for golden in dataset.goldens:
    test_case = LLMTestCase(
        input=golden.input,
        actual_output=my_llm_app(golden.input)
    )
    dataset.add_test_case(test_case)

@pytest.mark.parametrize("test_case", dataset.test_cases)
def test_llm_app(test_case: LLMTestCase):
    assert_test(test_case, [AnswerRelevancyMetric()])
```

### Single-Turn with evaluate()

```python
from deepeval import evaluate

for golden in dataset.goldens:
    test_case = LLMTestCase(
        input=golden.input,
        actual_output=my_llm_app(golden.input)
    )
    dataset.add_test_case(test_case)

evaluate(test_cases=dataset.test_cases, metrics=[AnswerRelevancyMetric()])
```

### Multi-Turn with ConversationSimulator

```python
from deepeval.simulator import ConversationSimulator

async def model_callback(input: str, turns, thread_id: str):
    response = await my_chatbot(input, turns, thread_id)
    return Turn(role="assistant", content=response)

simulator = ConversationSimulator(model_callback=model_callback)
test_cases = simulator.simulate(
    conversational_goldens=dataset.goldens,
    max_user_simulations=10,
)

evaluate(test_cases=test_cases, metrics=[ConversationCompletenessMetric()])
```

### With evals_iterator (Recommended)

```python
for golden in dataset.evals_iterator(metrics=[AnswerRelevancyMetric()]):
    my_traced_app(golden.input)
```

## Key Constraints

- Once `_multi_turn` is set during initialization, it cannot be changed
- A dataset cannot mix single-turn and multi-turn goldens
- JSONL files cannot mix `Golden` and `ConversationalGolden` rows
- `save_as()` saves only goldens by default — set `include_test_cases=True` for both

## Common Pitfalls

1. **Mixing golden types** — A single dataset must be all single-turn OR all multi-turn
2. **Forgetting to add test cases** — Goldens need `actual_output` added before evaluation
3. **Using test cases as goldens** — Test cases with actual_output aren't reusable templates
4. **Small datasets** — Include diverse inputs, varying complexity, and edge cases
5. **No expected_output for reference metrics** — ContextualRecall and ContextualPrecision need it
