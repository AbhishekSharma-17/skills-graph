# Offline Batch Inference

> Source: [docs.vllm.ai](https://docs.vllm.ai/) — v0.22.1

## Table of Contents
- [Overview](#overview)
- [The LLM Class](#the-llm-class)
- [SamplingParams Basics](#samplingparams-basics)
- [Text Generation](#text-generation)
- [Chat API](#chat-api)
- [Batch Processing Patterns](#batch-processing-patterns)
- [Embedding and Pooling](#embedding-and-pooling)
- [Common Pitfalls](#common-pitfalls)

## Overview

Offline inference is the primary way to use vLLM for batch processing workloads — processing a dataset of prompts without running a persistent server. The `LLM` class handles model loading, memory management, and batched inference in a single process.

Use offline inference when:
- Processing a fixed dataset of prompts
- Running evaluation benchmarks
- Generating synthetic data
- One-off generation tasks in scripts or notebooks

## The LLM Class

The `LLM` class is the main entry point for offline inference.

### Constructor Parameters

```python
from vllm import LLM

llm = LLM(
    model="meta-llama/Llama-3.1-8B-Instruct",
    # Memory and performance
    tensor_parallel_size=1,          # Number of GPUs for tensor parallelism
    gpu_memory_utilization=0.9,      # Fraction of GPU memory to use (0.0-1.0)
    max_model_len=4096,              # Maximum sequence length
    dtype="auto",                    # Data type: auto, float16, bfloat16, float32
    # Quantization
    quantization=None,               # Quantization method: awq, gptq, fp8, etc.
    # KV cache
    kv_cache_dtype="auto",           # KV cache dtype: auto, fp8, fp8_e5m2, fp8_e4m3
    # Model loading
    trust_remote_code=False,         # Allow custom model code from HuggingFace
    download_dir=None,               # Custom model download directory
    # Features
    enable_lora=False,               # Enable LoRA adapter support
    enable_prefix_caching=True,      # Enable automatic prefix caching (default: True)
    seed=0,                          # Random seed for reproducibility
)
```

### Key Constructor Arguments

| Argument | Type | Default | Purpose |
|----------|------|---------|---------|
| `model` | str | required | HuggingFace model ID or local path |
| `tensor_parallel_size` | int | 1 | Number of GPUs to split the model across |
| `gpu_memory_utilization` | float | 0.9 | Fraction of GPU VRAM to allocate |
| `max_model_len` | int | auto | Maximum context length (tokens) |
| `dtype` | str | "auto" | Model weight dtype |
| `quantization` | str | None | Quantization method to apply |
| `enforce_eager` | bool | False | Disable CUDA graphs (useful for debugging) |
| `max_num_seqs` | int | 256 | Maximum concurrent sequences |
| `swap_space` | float | 4 | CPU swap space per GPU in GB |
| `seed` | int | 0 | Random seed |

## SamplingParams Basics

`SamplingParams` controls how tokens are sampled during generation.

```python
from vllm import SamplingParams

params = SamplingParams(
    temperature=0.8,       # Randomness (0.0 = greedy, higher = more random)
    top_p=0.95,            # Nucleus sampling threshold
    top_k=-1,              # Top-k filtering (-1 = disabled)
    max_tokens=256,        # Maximum tokens to generate
    stop=["\n\n"],         # Stop sequences
    presence_penalty=0.0,  # Penalize repeated tokens
    frequency_penalty=0.0, # Penalize frequent tokens
    repetition_penalty=1.0,# Repetition penalty multiplier
    min_p=0.0,             # Minimum probability threshold
    seed=None,             # Per-request random seed
)
```

See `references/03-sampling-params.md` for the full parameter reference.

## Text Generation

### Basic Generation

```python
from vllm import LLM, SamplingParams

llm = LLM(model="facebook/opt-125m")
params = SamplingParams(temperature=0.8, top_p=0.95, max_tokens=100)

prompts = [
    "The future of artificial intelligence is",
    "In a distant galaxy, there existed",
    "The recipe for a perfect chocolate cake starts with",
]

outputs = llm.generate(prompts, params)

for output in outputs:
    prompt = output.prompt
    generated = output.outputs[0].text
    print(f"Prompt: {prompt!r}")
    print(f"Output: {generated!r}\n")
```

### RequestOutput Structure

Each call to `generate()` returns a list of `RequestOutput` objects:

```python
output = outputs[0]

output.request_id      # Unique request identifier
output.prompt          # Input prompt text
output.prompt_token_ids # Tokenized prompt
output.outputs         # List of CompletionOutput objects
output.finished        # Whether generation is complete

# Each CompletionOutput contains:
completion = output.outputs[0]
completion.text             # Generated text
completion.token_ids        # Generated token IDs
completion.cumulative_logprob  # Sum of log probabilities
completion.logprobs         # Per-token log probabilities (if requested)
completion.finish_reason    # "stop", "length", or None
```

### Multiple Completions per Prompt

```python
params = SamplingParams(
    n=3,                  # Generate 3 completions per prompt
    temperature=1.0,
    max_tokens=50,
    best_of=5,            # Sample 5, return top 3 by log probability
)

outputs = llm.generate(["Tell me a joke about"], params)

for i, completion in enumerate(outputs[0].outputs):
    print(f"Completion {i}: {completion.text}")
```

### Greedy Decoding

```python
params = SamplingParams(temperature=0, max_tokens=100)
outputs = llm.generate(prompts, params)
```

## Chat API

For instruct/chat models, use `llm.chat()` which automatically applies the model's chat template.

```python
from vllm import LLM, SamplingParams

llm = LLM(model="meta-llama/Llama-3.1-8B-Instruct")
params = SamplingParams(temperature=0.7, max_tokens=256)

messages = [
    {"role": "system", "content": "You are a helpful coding assistant."},
    {"role": "user", "content": "Write a Python function to compute fibonacci numbers."},
]

outputs = llm.chat(messages=[messages], sampling_params=params)
print(outputs[0].outputs[0].text)
```

### Batch Chat

```python
conversations = [
    [
        {"role": "user", "content": "What is Python?"},
    ],
    [
        {"role": "user", "content": "What is Rust?"},
    ],
    [
        {"role": "system", "content": "You are a math tutor."},
        {"role": "user", "content": "Explain calculus simply."},
    ],
]

outputs = llm.chat(messages=conversations, sampling_params=params)

for conv, output in zip(conversations, outputs):
    question = conv[-1]["content"]
    answer = output.outputs[0].text
    print(f"Q: {question}\nA: {answer}\n")
```

### Using generate() with Chat Prompts

If you need more control, apply the chat template manually:

```python
from vllm import LLM, SamplingParams

llm = LLM(model="meta-llama/Llama-3.1-8B-Instruct")
tokenizer = llm.get_tokenizer()

messages = [
    {"role": "user", "content": "Hello!"},
]

prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
outputs = llm.generate([prompt], SamplingParams(max_tokens=100))
```

## Batch Processing Patterns

### Processing a Large Dataset

```python
from vllm import LLM, SamplingParams

llm = LLM(model="meta-llama/Llama-3.1-8B-Instruct", max_model_len=4096)
params = SamplingParams(temperature=0, max_tokens=512)

# Load prompts from file
with open("prompts.txt") as f:
    prompts = [line.strip() for line in f if line.strip()]

# vLLM handles batching internally — pass all prompts at once
outputs = llm.generate(prompts, params)

results = []
for output in outputs:
    results.append({
        "prompt": output.prompt,
        "response": output.outputs[0].text,
        "finish_reason": output.outputs[0].finish_reason,
    })
```

### With Prompt Token IDs

```python
from vllm import LLM, SamplingParams

llm = LLM(model="facebook/opt-125m")
tokenizer = llm.get_tokenizer()

prompts_text = ["Hello world", "How are you"]
token_ids = [tokenizer.encode(p) for p in prompts_text]

# Pass pre-tokenized inputs
outputs = llm.generate(prompt_token_ids=token_ids, sampling_params=SamplingParams())
```

## Embedding and Pooling

vLLM also supports embedding models for generating vector representations.

```python
from vllm import LLM

llm = LLM(model="intfloat/e5-mistral-7b-instruct", task="embed")

texts = [
    "What is machine learning?",
    "Deep learning is a subset of ML.",
]

outputs = llm.embed(texts)

for text, output in zip(texts, outputs):
    embedding = output.outputs.embedding
    print(f"Text: {text[:30]}... → dim={len(embedding)}")
```

### Classification / Reward Models

```python
from vllm import LLM

llm = LLM(model="jason9693/Qwen2.5-1.5B-apeach", task="classify")

outputs = llm.classify(["This movie was amazing!", "Terrible experience."])

for output in outputs:
    probs = output.outputs.probs
    print(f"Class probabilities: {probs}")
```

## Common Pitfalls

1. **generate() vs chat()** — `generate()` does NOT apply chat templates; use `chat()` for instruct models or apply the template manually via the tokenizer
2. **max_model_len too high** — if the model supports 128K context but you only need 4K, set `max_model_len=4096` to save GPU memory for the KV cache
3. **OOM on large models** — increase `tensor_parallel_size` to split across GPUs, or use quantization to reduce memory
4. **Slow first call** — the first `generate()` call compiles CUDA graphs; subsequent calls are much faster. Use `enforce_eager=True` to skip this for debugging
5. **Passing one conversation to chat()** — `llm.chat()` expects a list of conversations, not a single conversation; wrap in a list: `llm.chat(messages=[conversation])`
