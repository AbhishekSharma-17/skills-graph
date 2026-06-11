# Sampling Parameters

> Source: [docs.vllm.ai](https://docs.vllm.ai/) — v0.22.1

## Table of Contents
- [Overview](#overview)
- [SamplingParams Reference](#samplingparams-reference)
- [Temperature and Randomness](#temperature-and-randomness)
- [Token Filtering](#token-filtering)
- [Penalties](#penalties)
- [Output Control](#output-control)
- [Log Probabilities](#log-probabilities)
- [Structured Output Integration](#structured-output-integration)
- [Recommended Presets](#recommended-presets)
- [Common Pitfalls](#common-pitfalls)

## Overview

`SamplingParams` controls how vLLM selects tokens during generation. These parameters apply to both offline inference (`LLM.generate()`) and the online serving API. The API parameters map directly to OpenAI-compatible fields.

## SamplingParams Reference

```python
from vllm import SamplingParams

params = SamplingParams(
    # Randomness
    temperature=1.0,           # float, default 1.0
    top_p=1.0,                 # float, default 1.0
    top_k=-1,                  # int, default -1 (disabled)
    min_p=0.0,                 # float, default 0.0
    seed=None,                 # int | None, default None

    # Penalties
    presence_penalty=0.0,      # float, default 0.0
    frequency_penalty=0.0,     # float, default 0.0
    repetition_penalty=1.0,    # float, default 1.0

    # Output control
    max_tokens=16,             # int, default 16
    min_tokens=0,              # int, default 0
    n=1,                       # int, default 1
    best_of=None,              # int | None, default None
    stop=None,                 # str | list[str] | None
    stop_token_ids=None,       # list[int] | None
    include_stop_str_in_output=False,  # bool

    # Log probabilities
    logprobs=None,             # int | None
    prompt_logprobs=None,      # int | None

    # Advanced
    skip_special_tokens=True,  # bool
    spaces_between_special_tokens=True,  # bool
    truncate_prompt_tokens=None,  # int | None

    # Structured output
    structured_outputs=None,   # StructuredOutputsParams | None
)
```

## Temperature and Randomness

### temperature (float, default: 1.0)

Controls randomness in token selection. Applied before top_p and top_k filtering.

| Value | Behavior |
|-------|----------|
| 0.0 | Greedy decoding — always picks the most likely token |
| 0.1–0.3 | Low randomness — focused, deterministic output |
| 0.7–0.9 | Moderate randomness — balanced creativity |
| 1.0 | Standard sampling — uses raw model probabilities |
| 1.5–2.0 | High randomness — very creative, may lose coherence |

```python
# Greedy (deterministic)
SamplingParams(temperature=0)

# Creative writing
SamplingParams(temperature=0.9)
```

### top_p (float, default: 1.0)

Nucleus sampling: considers only the smallest set of tokens whose cumulative probability exceeds `top_p`. Applied after temperature scaling.

```python
# Only consider tokens making up 90% of the probability mass
SamplingParams(temperature=0.8, top_p=0.9)
```

- `1.0` = disabled (consider all tokens)
- `0.9` = standard nucleus sampling
- `0.5` = aggressive filtering, more focused output

### top_k (int, default: -1)

Considers only the top `k` most probable tokens. Applied after temperature, before top_p.

```python
# Only consider top 50 tokens
SamplingParams(temperature=0.8, top_k=50)
```

- `-1` = disabled (consider all tokens)
- `1` = equivalent to greedy decoding
- `50` = common default for top-k sampling

### min_p (float, default: 0.0)

Filters out tokens with probability below `min_p * max_probability`. Dynamic alternative to top_k that adapts to the probability distribution.

```python
# Filter tokens with probability < 10% of the most likely token
SamplingParams(temperature=0.8, min_p=0.1)
```

- `0.0` = disabled
- `0.05–0.1` = mild filtering
- `0.2+` = aggressive filtering

### seed (int | None, default: None)

Sets the random seed for reproducible generation. When set, identical inputs produce identical outputs.

```python
# Reproducible output
SamplingParams(temperature=0.8, seed=42)
```

## Penalties

### presence_penalty (float, default: 0.0)

Adds a constant penalty to tokens that have appeared in the output. Encourages the model to talk about new topics.

- Range: -2.0 to 2.0
- `0.0` = no penalty
- Positive = penalize repetition
- Negative = encourage repetition

### frequency_penalty (float, default: 0.0)

Adds a penalty proportional to how many times a token has appeared. Stronger than presence_penalty for highly repeated tokens.

- Range: -2.0 to 2.0
- `0.0` = no penalty

### repetition_penalty (float, default: 1.0)

Multiplicative penalty applied to the logits of tokens that appear in the input prompt or previous output.

- `1.0` = no penalty
- `1.1–1.3` = mild anti-repetition
- `> 1.5` = strong, may degrade quality

```python
# Reduce repetition in long generations
SamplingParams(
    temperature=0.7,
    repetition_penalty=1.15,
    frequency_penalty=0.3,
)
```

## Output Control

### max_tokens (int, default: 16)

Maximum number of tokens to generate per completion. The actual output may be shorter if a stop condition is met.

```python
SamplingParams(max_tokens=512)
```

### min_tokens (int, default: 0)

Minimum number of tokens to generate before allowing stop conditions. Forces the model to produce at least this many tokens.

```python
# Force at least 50 tokens before stopping
SamplingParams(max_tokens=200, min_tokens=50)
```

### n (int, default: 1)

Number of independent completions to generate for each prompt. Each uses independent sampling.

```python
# Generate 3 alternatives
SamplingParams(n=3, temperature=0.9)
```

### best_of (int | None, default: None)

Generate `best_of` completions server-side and return the top `n` by log probability. Must be >= `n`.

```python
# Generate 5, return the 2 best
SamplingParams(n=2, best_of=5, temperature=1.0)
```

### stop (str | list[str] | None)

Stop generation when any of these strings appear in the output.

```python
SamplingParams(stop=["\n\n", "END", "```"])
```

### stop_token_ids (list[int] | None)

Stop generation when any of these token IDs are generated.

```python
SamplingParams(stop_token_ids=[128009])  # Llama 3 EOS
```

### include_stop_str_in_output (bool, default: False)

Whether to include the stop string in the generated output.

## Log Probabilities

### logprobs (int | None, default: None)

Number of top log probabilities to return per generated token.

```python
params = SamplingParams(logprobs=5)
outputs = llm.generate(["Hello"], params)

for token_logprob in outputs[0].outputs[0].logprobs:
    for token_id, logprob_info in token_logprob.items():
        print(f"Token: {logprob_info.decoded_token}, LogProb: {logprob_info.logprob:.4f}")
```

### prompt_logprobs (int | None, default: None)

Number of top log probabilities to return per prompt token. Useful for scoring/perplexity calculations.

```python
params = SamplingParams(prompt_logprobs=1, max_tokens=0)
outputs = llm.generate(["The cat sat on the"], params)
```

## Structured Output Integration

Pass structured output constraints via the `structured_outputs` field:

```python
from vllm.sampling_params import StructuredOutputsParams

params = SamplingParams(
    temperature=0,
    max_tokens=200,
    structured_outputs=StructuredOutputsParams(
        json_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
            "required": ["name", "age"],
        }
    ),
)
```

See `references/08-structured-outputs.md` for full structured output options.

## Recommended Presets

### Code Generation
```python
SamplingParams(temperature=0, max_tokens=1024)
```

### Creative Writing
```python
SamplingParams(temperature=0.9, top_p=0.95, max_tokens=2048, repetition_penalty=1.1)
```

### Factual Q&A
```python
SamplingParams(temperature=0.1, top_p=0.9, max_tokens=256)
```

### Classification / Structured
```python
SamplingParams(temperature=0, max_tokens=50)
```

### Diverse Generation (Multiple Options)
```python
SamplingParams(n=5, temperature=1.0, top_p=0.95, max_tokens=100)
```

## Common Pitfalls

1. **Default max_tokens is 16** — this is very short; always set it explicitly for real workloads
2. **temperature=0 ignores top_p/top_k** — greedy decoding bypasses all sampling filters
3. **best_of with low temperature** — `best_of` only makes sense with randomness; at `temperature=0` all candidates are identical
4. **Mixing repetition_penalty with frequency_penalty** — both fight repetition; using both may over-penalize and produce incoherent text
5. **stop strings in chat templates** — stop tokens from the chat template are usually handled automatically; adding them to `stop` may cause double-stopping
