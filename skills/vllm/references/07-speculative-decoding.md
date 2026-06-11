# Speculative Decoding

> Source: [docs.vllm.ai](https://docs.vllm.ai/) — v0.22.1

## Table of Contents
- [Overview](#overview)
- [Supported Methods](#supported-methods)
- [Configuration](#configuration)
- [Draft Model Method](#draft-model-method)
- [EAGLE Method](#eagle-method)
- [Multi-Token Prediction](#multi-token-prediction)
- [N-gram Method](#n-gram-method)
- [Suffix Decoding](#suffix-decoding)
- [Rejection Sampling](#rejection-sampling)
- [Performance Guidance](#performance-guidance)
- [Common Pitfalls](#common-pitfalls)

## Overview

Speculative decoding is an inference optimization that reduces inter-token latency by using a fast "proposer" to draft multiple tokens ahead, then verifying them in a single forward pass of the target model. Accepted tokens skip individual decoding steps, reducing wall-clock time.

It is most effective at low to medium query rates (QPS) where the GPU has idle cycles. At high QPS with full batches, the overhead of speculation can negate the gains.

## Supported Methods

| Method | Draft Model Required | Gains at Low QPS | Gains at High QPS | Complexity |
|--------|---------------------|-------------------|-------------------|------------|
| EAGLE | Yes (EAGLE head) | High | Medium-High | Medium |
| MTP | No (native support) | High | Medium-High | Low |
| Draft Model | Yes (separate model) | High | Medium | Medium |
| PARD | Yes (separate model) | High | Medium | Medium |
| MLP Speculator | Yes (MLP head) | Medium-High | Medium | Medium |
| N-gram | No | Low-Medium | Low | Very Low |
| Suffix Decoding | No | Low-Medium | Low | Very Low |

## Configuration

All speculative decoding is configured via `--speculative-config` with a JSON object:

```bash
vllm serve <target-model> \
    --speculative-config '{"method": "<method>", ...}'
```

### Universal Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `method` | string | Speculation method name |
| `model` | string | Draft/auxiliary model path (method-dependent) |
| `num_speculative_tokens` | int | Tokens to propose per step |
| `draft_tensor_parallel_size` | int | TP size for draft model (default: 1) |
| `rejection_sample_method` | string | strict, probabilistic, or synthetic |

## Draft Model Method

Uses a smaller, faster model from the same family to propose tokens.

```bash
vllm serve meta-llama/Llama-3.1-70B-Instruct \
    --speculative-config '{
        "method": "draft_model",
        "model": "meta-llama/Llama-3.1-8B-Instruct",
        "num_speculative_tokens": 5
    }'
```

**Requirements:**
- Draft model must share the same tokenizer as the target model
- Smaller model from the same family works best (e.g., 8B draft for 70B target)
- Draft model runs with its own tensor parallelism setting

**Tuning:**
- `num_speculative_tokens`: 3–7 typical; higher = more aggressive speculation
- `draft_tensor_parallel_size`: keep at 1 unless draft model is large

## EAGLE Method

EAGLE (Extrapolation Algorithm for Greater Language-model Efficiency) uses a trained autoregressive head that predicts hidden states of the target model.

```bash
vllm serve meta-llama/Llama-3.1-70B-Instruct \
    --speculative-config '{
        "method": "eagle",
        "model": "yuhuili/EAGLE3-LLaMA3.1-Instruct-70B",
        "num_speculative_tokens": 5
    }'
```

EAGLE is the strongest general-purpose model-based method. It achieves high acceptance rates because it directly models the target model's hidden state evolution rather than predicting output tokens.

**Finding EAGLE models:** Search HuggingFace for `EAGLE-<model-family>` or `EAGLE3-<model-family>`.

## Multi-Token Prediction

Uses the target model's native multi-token prediction heads (if available). No separate draft model needed.

```bash
vllm serve deepseek-ai/DeepSeek-V3 \
    --speculative-config '{
        "method": "mtp",
        "num_speculative_tokens": 1
    }'
```

MTP works best when the target model was trained with MTP objectives (e.g., DeepSeek-V3). For models without native MTP support, use EAGLE or draft models instead.

## N-gram Method

Lightweight method that proposes tokens by matching patterns from the prompt itself. No draft model or extra memory needed.

```bash
vllm serve model \
    --speculative-config '{
        "method": "ngram",
        "num_speculative_tokens": 5,
        "prompt_lookup_min": 1,
        "prompt_lookup_max": 5
    }'
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `prompt_lookup_min` | 1 | Minimum n-gram window size |
| `prompt_lookup_max` | varies | Maximum n-gram window size |

N-gram works best when the output is likely to repeat patterns from the input (e.g., summarization, code refactoring, translation with repeated terms).

## Suffix Decoding

Uses a suffix tree built from the prompt to propose matching token sequences. Dynamic speculation depth adapts to content.

```bash
vllm serve model \
    --speculative-config '{
        "method": "suffix_decoding",
        "num_speculative_tokens": 5,
        "suffix_decoding_max_tree_depth": 24,
        "suffix_decoding_min_token_prob": 0.1
    }'
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `suffix_decoding_max_tree_depth` | 24 | Maximum prefix-match depth |
| `suffix_decoding_min_token_prob` | 0.1 | Minimum probability threshold |

## Rejection Sampling

vLLM uses rejection sampling to ensure speculative decoding is theoretically lossless — the output distribution matches what the target model would produce without speculation.

### Methods

| Method | Description |
|--------|-------------|
| `strict` | Standard rejection sampling; maintains exact distribution |
| `probabilistic` | Relaxed sampling; may slightly alter distribution |
| `synthetic` | Synthetic token probabilities; experimental |

```bash
vllm serve model \
    --speculative-config '{
        "method": "draft_model",
        "model": "...",
        "num_speculative_tokens": 5,
        "rejection_sample_method": "strict"
    }'
```

### Lossless Guarantees

1. **Theoretically lossless** — speculative sampling preserves the target distribution up to hardware numerical precision
2. **Greedy equivalence** — verified that greedy decoding with and without speculation produces identical outputs
3. **Logprob caveat** — vLLM does not guarantee stable log probabilities across runs, so minor variations in reported logprobs are expected

## Performance Guidance

### When Speculative Decoding Helps

- Low to medium QPS (GPU not fully utilized)
- Interactive use cases where latency matters
- Long-form generation where per-token latency compounds
- Output overlaps significantly with input (for n-gram/suffix methods)

### When It Doesn't Help

- High QPS with full GPU utilization (speculation adds overhead)
- Very short generations (speculation setup cost dominates)
- Output is highly unpredictable (low acceptance rate)

### Method Selection Guide

```
Need maximum latency reduction?
  └─ EAGLE model available? → Use EAGLE
  └─ Model has native MTP? → Use MTP
  └─ Same-family small model available? → Use Draft Model
  └─ No extra models? → Use N-gram or Suffix Decoding

Need zero extra memory?
  └─ Use N-gram or Suffix Decoding

Output likely repeats input patterns?
  └─ N-gram or Suffix Decoding will be especially effective
```

### Benchmarking

Use vLLM's built-in benchmark to measure actual gains:

```bash
vllm bench serve --model model \
    --speculative-config '{...}' \
    --dataset-name <dataset>
```

Compare with and without speculation on your specific model, hardware, and traffic pattern.

## Common Pitfalls

1. **Pipeline parallelism incompatible** — speculative decoding does not work with `--pipeline-parallel-size > 1`
2. **Tokenizer mismatch** — draft model must use the same tokenizer as the target model
3. **Too many speculative tokens** — setting `num_speculative_tokens` too high wastes compute on tokens that get rejected; start with 3–5
4. **High QPS overhead** — at peak throughput, speculation slows things down; benchmark at your expected QPS
5. **Memory for draft model** — a separate draft model consumes additional GPU memory; factor this into capacity planning
6. **EAGLE version mismatch** — EAGLE heads are model-specific; use the correct version for your target model
