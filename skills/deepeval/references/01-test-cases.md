# Test Cases

> Source: https://deepeval.com/docs/evaluation-test-cases

## Overview

Test cases are the atomic units of evaluation in DeepEval. An `LLMTestCase` represents a single interaction with your LLM application. A `ConversationalTestCase` represents a multi-turn dialogue. Test cases carry the data that metrics score against.

## LLMTestCase

The primary test case type for single-turn evaluation:

```python
from deepeval.test_case import LLMTestCase

test_case = LLMTestCase(
    input="What if these shoes don't fit?",
    actual_output="We offer a 30-day full refund at no extra cost.",
    expected_output="You're eligible for a 30 day refund at no extra cost.",
    context=["All customers are eligible for a 30 day full refund at no extra cost."],
    retrieval_context=["Only shoes can be refunded."]
)
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `input` | `str` | Yes | User's query or prompt to your LLM |
| `actual_output` | `str` | Yes | Your LLM application's response |
| `expected_output` | `str` | No | Ideal response (doesn't require exact match) |
| `context` | `list[str]` | No | Ground truth data for the given input |
| `retrieval_context` | `list[str]` | No | Chunks retrieved by your RAG pipeline |
| `tools_called` | `list[ToolCall]` | No | Tools invoked by your agent |
| `expected_tools` | `list[ToolCall]` | No | Tools that should have been called |
| `token_cost` | `float` | No | Cost of the interaction |
| `completion_time` | `float` | No | Duration in seconds |

### Context vs Retrieval Context

These are commonly confused but serve different purposes:

- **`context`** — Ideal/ground truth retrieval results. Comes from your evaluation dataset. Represents what *should* have been retrieved.
- **`retrieval_context`** — Actual retrieval results from your RAG pipeline at runtime. Represents what *was* retrieved.

Use `context` for reference-based metrics (ContextualRecall). Use `retrieval_context` for runtime metrics (Faithfulness, ContextualRelevancy).

## ToolCall

For agent evaluation, track tool invocations:

```python
from deepeval.test_case import ToolCall

test_case = LLMTestCase(
    input="What's 2 + 3?",
    actual_output="The answer is 5.",
    tools_called=[
        ToolCall(
            name="Calculator Tool",
            description="Calculates mathematical expressions.",
            input_parameters={"user_input": "2+3"},
            output=5,
            reasoning="User asked for arithmetic calculation."
        )
    ],
    expected_tools=[
        ToolCall(name="Calculator Tool")
    ]
)
```

### ToolCall Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `str` | Yes | Tool identifier |
| `description` | `str` | No | What the tool does |
| `reasoning` | `str` | No | Why the tool was selected |
| `output` | `Any` | No | Tool's return value |
| `input_parameters` | `dict[str, Any]` | No | Parameters passed to the tool |

## ConversationalTestCase

For multi-turn dialogue evaluation:

```python
from deepeval.test_case import ConversationalTestCase, Turn

test_case = ConversationalTestCase(
    turns=[
        Turn(role="user", content="Hello, how are you?"),
        Turn(role="assistant", content="I'm doing well, thank you!"),
        Turn(role="user", content="I'd like to buy a concert ticket."),
        Turn(role="assistant", content="I'd be happy to help! Which concert?"),
    ]
)
```

### Turn Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `role` | `str` | Yes | `"user"` or `"assistant"` |
| `content` | `str` | Yes | Message text |
| `retrieval_context` | `list[str]` | No | Retrieved chunks for this turn |
| `tools_called` | `list[ToolCall]` | No | Tools used in this turn |

## Multimodal Test Cases (MLLMImage)

DeepEval supports images in test cases:

```python
from deepeval.test_case import LLMTestCase, MLLMImage

shoes = MLLMImage(url='./shoes.png', local=True)
blue_shoes = MLLMImage(url='https://images.example.com/blue-shoes.png', local=False)

test_case = LLMTestCase(
    input=f"Change the color of these shoes to blue: {shoes}",
    actual_output=f"Here are the blue shoes: {blue_shoes}",
    expected_output=f"Blue version of the shoes"
)
```

### MLLMImage Fields

| Field | Type | Description |
|-------|------|-------------|
| `url` | `str` | Path or URL to the image |
| `local` | `bool` | `True` for local files, `False` for remote URLs |
| `dataBase64` | `str` | Base64-encoded image data |
| `mimeType` | `str` | Image MIME type |
| `filename` | `str` | Image filename |

## Labeling for Confident AI

Add metadata for cloud organization:

```python
test_case = LLMTestCase(
    name="refund-policy-check-001",
    tags=["refund", "customer-service"],
    input="What is your refund policy?",
    actual_output="We offer 30-day refunds."
)
```

## Creating Test Cases from Goldens

In evaluation loops, goldens convert to test cases by adding your LLM's actual output:

```python
from deepeval.dataset import EvaluationDataset, Golden

dataset = EvaluationDataset(goldens=[
    Golden(input="What is your name?"),
    Golden(input="How do I reset my password?"),
])

for golden in dataset.goldens:
    actual = my_llm_app(golden.input)
    test_case = LLMTestCase(
        input=golden.input,
        actual_output=actual,
        expected_output=golden.expected_output,
        context=golden.context
    )
    dataset.add_test_case(test_case)
```

## Which Parameters Does Each Metric Need?

Different metrics require different test case fields:

| Metric | Required Fields |
|--------|----------------|
| AnswerRelevancy | `input`, `actual_output` |
| Faithfulness | `input`, `actual_output`, `retrieval_context` |
| ContextualRelevancy | `input`, `retrieval_context` |
| ContextualPrecision | `input`, `retrieval_context`, `expected_output` |
| ContextualRecall | `input`, `retrieval_context`, `expected_output` |
| ToolCorrectness | `input`, `actual_output`, `tools_called`, `expected_tools` |
| TaskCompletion | `input`, `actual_output` |
| Bias | `input`, `actual_output` |
| Toxicity | `input`, `actual_output` |
| Hallucination | `input`, `actual_output`, `context` |

## Common Pitfalls

1. **Confusing `context` and `retrieval_context`** — Context is ground truth; retrieval_context is what your pipeline actually retrieved
2. **Missing `actual_output`** — Every `LLMTestCase` requires both `input` and `actual_output`
3. **Using LLMTestCase for multi-turn** — Use `ConversationalTestCase` with `Turn` objects instead
4. **Empty `retrieval_context`** — RAG metrics require non-empty retrieval_context lists
5. **ToolCall without `name`** — The `name` field is required on all ToolCall objects
