# Custom Metrics

> Source: https://deepeval.com/docs/metrics-introduction | https://deepeval.com/docs/metrics-custom

## Overview

DeepEval's custom metrics let you define any evaluation criteria. GEval is the most common — it uses LLM-as-a-judge with natural language criteria. For deterministic scoring, use DAG. For full control, subclass `BaseMetric` directly.

## GEval — LLM-as-Judge Custom Metric

GEval evaluates subjective criteria like correctness, coherence, or tone using an LLM judge:

```python
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, SingleTurnParams

correctness_metric = GEval(
    name="Correctness",
    criteria="Determine if the 'actual output' is correct based on the 'expected output'.",
    evaluation_params=[
        SingleTurnParams.ACTUAL_OUTPUT,
        SingleTurnParams.EXPECTED_OUTPUT
    ],
    threshold=0.5
)

test_case = LLMTestCase(
    input="What is the capital of France?",
    actual_output="Paris is the capital of France.",
    expected_output="The capital of France is Paris."
)

correctness_metric.measure(test_case)
print(f"Score: {correctness_metric.score}")
print(f"Reason: {correctness_metric.reason}")
```

### SingleTurnParams

Available evaluation parameters for single-turn GEval:

| Parameter | Maps to |
|-----------|---------|
| `SingleTurnParams.INPUT` | `test_case.input` |
| `SingleTurnParams.ACTUAL_OUTPUT` | `test_case.actual_output` |
| `SingleTurnParams.EXPECTED_OUTPUT` | `test_case.expected_output` |
| `SingleTurnParams.CONTEXT` | `test_case.context` |
| `SingleTurnParams.RETRIEVAL_CONTEXT` | `test_case.retrieval_context` |

### GEval Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | Required | Display name for the metric |
| `criteria` | `str` | Required | Natural language evaluation criteria |
| `evaluation_params` | `list` | Required | Which test case fields to evaluate |
| `threshold` | `float` | `0.5` | Pass/fail threshold |
| `strict_mode` | `bool` | `False` | Binary scoring (0 or 1) |
| `model` | `str` | OpenAI default | LLM judge model |
| `verbose_mode` | `bool` | `False` | Print execution logs |

### Writing Effective Criteria

Good criteria are specific, measurable, and reference the evaluation parameters:

```python
# Good: specific and references parameters
GEval(
    name="Medical Accuracy",
    criteria="Determine if the 'actual output' provides medically accurate information "
             "that aligns with the 'expected output'. Penalize any unsupported medical claims "
             "or advice that contradicts established guidelines.",
    evaluation_params=[SingleTurnParams.ACTUAL_OUTPUT, SingleTurnParams.EXPECTED_OUTPUT],
)

# Bad: vague and generic
GEval(
    name="Quality",
    criteria="Is the output good?",
    evaluation_params=[SingleTurnParams.ACTUAL_OUTPUT],
)
```

## ConversationalGEval — Multi-Turn Custom Metric

For evaluating conversation-level properties:

```python
from deepeval.metrics import ConversationalGEval
from deepeval.test_case import ConversationalTestCase, Turn, MultiTurnParams

professionalism = ConversationalGEval(
    name="Professionalism",
    criteria="Determine whether the assistant maintained a professional tone "
             "throughout the conversation based on the content.",
    evaluation_params=[MultiTurnParams.CONTENT],
    threshold=0.5,
    strict_mode=True
)

test_case = ConversationalTestCase(
    turns=[
        Turn(role="user", content="Your product is terrible!"),
        Turn(role="assistant", content="I'm sorry to hear about your experience. "
             "Let me help resolve this issue for you."),
    ]
)

professionalism.measure(test_case)
```

### MultiTurnParams

| Parameter | Description |
|-----------|-------------|
| `MultiTurnParams.CONTENT` | Full conversation content |

## Building Custom BaseMetric Subclasses

For complete control over scoring logic, subclass `BaseMetric` directly:

### Non-LLM Metric Example (ROUGE)

```python
from deepeval.scorer import Scorer
from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

class RougeMetric(BaseMetric):
    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
        self.scorer = Scorer()
        self.score = None
        self.reason = None
        self.success = None
        self.error = None

    def measure(self, test_case: LLMTestCase) -> float:
        try:
            self.score = self.scorer.rouge_score(
                prediction=test_case.actual_output,
                target=test_case.expected_output,
                score_type="rouge1"
            )
            self.success = self.score >= self.threshold
            return self.score
        except Exception as e:
            self.error = str(e)
            raise

    async def a_measure(self, test_case: LLMTestCase) -> float:
        return self.measure(test_case)

    def is_successful(self) -> bool:
        if self.error:
            return False
        return self.success

    @property
    def __name__(self):
        return "ROUGE-1"
```

### Implementation Rules

1. **Inherit the right base class:**
   - `BaseMetric` for single-turn (accepts `LLMTestCase`)
   - `BaseConversationalMetric` for multi-turn (accepts `ConversationalTestCase`)

2. **Implement `__init__()`** with at least `threshold`

3. **Implement `measure()` and `a_measure()`** — both must:
   - Accept a test case argument
   - Set `self.score` and `self.success`
   - Optionally set `self.reason`
   - Handle exceptions by setting `self.error`

4. **Implement `is_successful()`** — compare score against threshold

5. **Define `__name__`** — return the metric's display name

### Composite Metric Example

Combine multiple metrics into one:

```python
from deepeval.metrics import BaseMetric, AnswerRelevancyMetric, FaithfulnessMetric

class RAGQualityMetric(BaseMetric):
    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
        self.relevancy = AnswerRelevancyMetric(threshold=threshold)
        self.faithfulness = FaithfulnessMetric(threshold=threshold)

    def measure(self, test_case):
        self.relevancy.measure(test_case)
        self.faithfulness.measure(test_case)
        self.score = min(self.relevancy.score, self.faithfulness.score)
        self.reason = (f"Relevancy: {self.relevancy.score:.2f}, "
                       f"Faithfulness: {self.faithfulness.score:.2f}")
        self.success = self.score >= self.threshold
        return self.score

    async def a_measure(self, test_case):
        import asyncio
        await asyncio.gather(
            self.relevancy.a_measure(test_case),
            self.faithfulness.a_measure(test_case)
        )
        self.score = min(self.relevancy.score, self.faithfulness.score)
        self.reason = (f"Relevancy: {self.relevancy.score:.2f}, "
                       f"Faithfulness: {self.faithfulness.score:.2f}")
        self.success = self.score >= self.threshold
        return self.score

    def is_successful(self):
        return self.success

    @property
    def __name__(self):
        return "RAG Quality"
```

## Custom Prompt Templates

Override default evaluation prompts for any built-in metric:

```python
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.metrics.answer_relevancy import AnswerRelevancyTemplate

class CustomTemplate(AnswerRelevancyTemplate):
    @staticmethod
    def generate_statements(actual_output: str):
        return f"""Break down the following text into individual statements.

Text: {actual_output}

Return as JSON array of strings."""

metric = AnswerRelevancyMetric(evaluation_template=CustomTemplate)
```

## Choosing the Right Approach

| Need | Use |
|------|-----|
| Subjective criteria (tone, quality) | `GEval` |
| Deterministic scoring tree | `DAG` |
| Algorithmic scoring (BLEU, ROUGE) | Custom `BaseMetric` |
| Combine existing metrics | Composite `BaseMetric` |
| Multi-turn criteria | `ConversationalGEval` |
| A/B comparison | `ArenaGEval` |

## Common Pitfalls

1. **Vague GEval criteria** — Be specific about what constitutes a good vs bad score
2. **Missing `a_measure`** — Always implement both sync and async; reuse sync if needed
3. **Not setting `self.error`** — Wrap measure logic in try/except for proper error reporting
4. **Forgetting `__name__`** — Required for display in reports and CI output
