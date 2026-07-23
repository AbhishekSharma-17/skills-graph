# Synthesizer & Synthetic Data Generation

> Source: https://deepeval.com/docs/synthesizer-generate-from-scratch | https://deepeval.com/docs/evaluation-datasets

## Overview

DeepEval's Synthesizer generates high-quality synthetic test data from your knowledge base or from scratch. It chunks documents, builds contexts, generates input-output pairs, and evolves them into harder edge cases — producing thousands of test cases in minutes. The `deepeval generate` CLI command and the `Synthesizer` Python class provide both programmatic and terminal interfaces.

## Synthesizer Methods

### generate_goldens_from_docs

Creates goldens from knowledge base documents. The most grounded method — test cases are rooted in actual documentation:

```python
from deepeval.synthesizer import Synthesizer
from deepeval.dataset import EvaluationDataset

synthesizer = Synthesizer()

goldens = synthesizer.generate_goldens_from_docs(
    document_paths=['knowledge_base.txt', 'faq.docx', 'guide.pdf']
)

dataset = EvaluationDataset(goldens=goldens)
print(f"Generated {len(goldens)} goldens")
```

### generate_goldens_from_contexts

Creates goldens from prepared context chunks:

```python
contexts = [
    ["Our return policy allows 30-day returns.", "Free shipping on orders over $50."],
    ["Password must be 8+ characters.", "Two-factor authentication is available."],
]

goldens = synthesizer.generate_goldens_from_contexts(contexts=contexts)
```

### generate_goldens_from_scratch

Creates goldens without any source documents. Useful for testing beyond your knowledge base:

```python
from deepeval.synthesizer import Synthesizer
from deepeval.synthesizer.config import StylingConfig

styling_config = StylingConfig(
    input_format="Questions in English that ask for data in a database.",
    expected_output_format="SQL query based on the given input.",
    task="Answering text-to-SQL-related queries by querying a database.",
    scenario="Non-technical users trying to query a database using plain English."
)

synthesizer = Synthesizer(styling_config=styling_config)
goldens = synthesizer.generate_goldens_from_scratch(num_goldens=25)
```

**Note:** Because no documents or contexts are provided, goldens aren't grounded in a knowledge base — this is the least grounded generation method.

### generate_goldens_from_goldens

Augments existing goldens with variations:

```python
existing_goldens = dataset.goldens
augmented = synthesizer.generate_goldens_from_goldens(goldens=existing_goldens)
```

## Multi-Turn Synthesis

### ConversationalStylingConfig

For generating multi-turn conversation test data:

```python
from deepeval.synthesizer.config import ConversationalStylingConfig

conv_config = ConversationalStylingConfig(
    scenario="Customer service for an e-commerce platform.",
    user_persona="Impatient customer who wants quick answers.",
    expected_outcome="Issue resolved with customer satisfaction."
)

synthesizer = Synthesizer(styling_config=conv_config)
conv_goldens = synthesizer.generate_conversational_goldens_from_scratch(
    num_goldens=10
)
```

## ConversationSimulator

For generating multi-turn test cases by simulating user interactions with your chatbot:

```python
from deepeval.simulator import ConversationSimulator
from deepeval.test_case import Turn
from typing import List, Dict

async def model_callback(
    input: str,
    conversation_history: List[Dict[str, str]]
) -> str:
    return await my_chatbot(input, conversation_history)

simulator = ConversationSimulator(
    user_intentions={"Opening a bank account": 1},
    user_profile_items=[
        "full name",
        "current address",
        "date of birth",
        "phone number",
    ]
)

conversational_test_cases = simulator.simulate(
    model_callback=model_callback,
    stopping_criteria="Stop when the user's banking request has been fully resolved."
)
```

### ConversationSimulator Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_intentions` | `dict[str, int]` | Intent → weight mapping |
| `user_profile_items` | `list[str]` | User attributes the simulator uses |
| `model_callback` | `async callable` | Your chatbot's response function |

### simulate() Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `model_callback` | `callable` | Chatbot response function |
| `stopping_criteria` | `str` | When to end the conversation |
| `max_user_simulations` | `int` | Max simulated conversations |
| `max_turns` | `int` | Max turns per conversation |
| `conversational_goldens` | `list` | Goldens to drive simulation |

## CLI: deepeval generate

Generate synthetic test data from the terminal without writing Python:

```bash
deepeval generate --method docs --variation single-turn
```

### Required Arguments

| Flag | Values | Description |
|------|--------|-------------|
| `--method` | `docs`, `contexts`, `scratch`, `goldens` | Source of test data |
| `--variation` | `single-turn`, `multi-turn` | Output type |

### Common Options

| Flag | Default | Description |
|------|---------|-------------|
| `--output-dir` | `./synthetic_data` | Output directory |
| `--file-type` | `json` | `json`, `csv`, or `jsonl` |
| `--file-name` | auto | Custom filename |
| `--model` | default | LLM model for generation |
| `--async-mode` | enabled | Async generation |
| `--max-concurrent` | auto | Max parallel generations |
| `--include-expected` | yes | Include expected_output |
| `--cost-tracking` | off | Track token costs |

### Examples

```bash
# From documentation files
deepeval generate --method docs --variation single-turn \
  --output-dir ./eval-data --file-type jsonl

# From scratch with styling
deepeval generate --method scratch --variation single-turn

# Multi-turn from goldens
deepeval generate --method goldens --variation multi-turn
```

## Vibe Coding Integration

DeepEval supports a tight feedback loop with coding agents:

1. **Dataset setup** — Agent runs `deepeval generate` to create test data
2. **Suite construction** — Framework provides pytest templates
3. **Execution** — `deepeval test run` returns per-test scores and reasoning
4. **Failure localization** — `@observe` traces pinpoint which component failed
5. **Targeted patching** — Agent modifies the minimal component and reruns

Effective agent directives:

```
Run `deepeval test run tests/evals/` and fix the lowest-scoring metric.
Don't change thresholds. Re-run to confirm.
```

```
Run 5 rounds of the iteration loop. Each round: run evals, pick one
failing metric, edit the smallest thing that could fix it, re-run,
summarize what changed.
```

## Best Practices

1. **Start with docs** — `generate_goldens_from_docs` produces the most grounded test data
2. **Mix methods** — Combine doc-based and from-scratch goldens for broader coverage
3. **Include edge cases** — Use styling config to specify challenging scenarios
4. **Version your datasets** — Push to Confident AI or save locally for reproducibility
5. **Curate after generation** — Review and edit synthetic goldens before using in CI/CD

## Common Pitfalls

1. **Too many synthetic goldens** — Start with 20-50 and refine; quality beats quantity
2. **Ungrounded from-scratch data** — May not reflect real usage patterns
3. **No human review** — Always review synthetic data before using as evaluation baseline
4. **Static datasets** — Regenerate periodically as your knowledge base evolves
5. **Missing styling config** — From-scratch generation needs clear task/scenario descriptions
