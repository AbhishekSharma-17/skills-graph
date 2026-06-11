# vLLM Overview

> Source: [docs.vllm.ai](https://docs.vllm.ai/) — v0.22.1

## What is vLLM?

vLLM is a high-throughput and memory-efficient inference and serving engine for large language models. It implements PagedAttention for efficient KV cache management, continuous batching for maximizing GPU utilization, and an OpenAI-compatible API server for drop-in replacement of commercial LLM APIs.

Originally developed at UC Berkeley, vLLM has grown into one of the most active open-source AI projects with 2000+ contributors and support for 200+ model architectures from HuggingFace.

## When to Use vLLM

- **Production LLM serving** — serve open-weight models behind an OpenAI-compatible API
- **Batch inference** — process large prompt datasets offline with maximum throughput
- **Multi-GPU deployment** — serve models too large for a single GPU via tensor/pipeline parallelism
- **Cost optimization** — run quantized models (FP8, GPTQ, AWQ, GGUF) to reduce GPU memory
- **Multi-model serving** — serve LoRA adapters on-demand without reloading the base model
- **Multimodal inference** — process images, audio, and video alongside text

## When NOT to Use vLLM

- **Training or fine-tuning** — vLLM is inference-only; use Axolotl, TRL, or DeepSpeed for training
- **Edge/mobile deployment** — use llama.cpp, MLC-LLM, or ONNX Runtime for small devices
- **Single-request latency-critical** — for one-off requests, the overhead of the engine may not pay off

## Core Architecture

### PagedAttention
vLLM's key innovation. Instead of allocating contiguous memory for each sequence's KV cache, PagedAttention manages memory in fixed-size blocks (pages), similar to OS virtual memory. This eliminates memory fragmentation and enables near-optimal GPU memory utilization.

### Continuous Batching
Rather than waiting for all sequences in a batch to complete, vLLM dynamically adds new requests and removes finished ones at each decoding step. This keeps the GPU saturated and dramatically improves throughput compared to static batching.

### Optimized Kernels
vLLM includes highly optimized CUDA/ROCm kernels:
- **Attention**: FlashAttention, FlashInfer, TRTLLM-GEN, FlashMLA, Triton
- **GEMM/MoE**: CUTLASS, TRTLLM-GEN, CuTeDSL for various precisions
- **CUDA Graphs**: Pre-compiled execution graphs to eliminate kernel launch overhead

## Installation

### Prerequisites
- **OS**: Linux (primary), macOS Apple Silicon (via vLLM-Metal)
- **Python**: 3.10–3.13
- **GPU**: NVIDIA CUDA, AMD ROCm, Google TPU, Intel Gaudi, or Apple Silicon

### NVIDIA CUDA (Recommended)

```bash
# Using uv (recommended)
uv venv --python 3.12 --seed
source .venv/bin/activate
uv pip install vllm --torch-backend=auto

# Or direct invocation without venv
uv run --with vllm vllm --help

# Using conda + pip
conda create -n vllm python=3.12 -y
conda activate vllm
pip install --upgrade uv
uv pip install vllm --torch-backend=auto
```

### AMD ROCm

```bash
uv venv --python 3.12 --seed
source .venv/bin/activate
uv pip install vllm --extra-index-url https://wheels.vllm.ai/rocm/
```

Requires Python 3.12, ROCm 7.0, and glibc >= 2.35.

### Google TPU

```bash
uv pip install vllm-tpu
```

### Apple Silicon

Use [vLLM-Metal](https://github.com/vllm-project/vllm-metal) with the MLX backend and mlx-community models.

## Quick Start

### Offline Batch Inference

```python
from vllm import LLM, SamplingParams

prompts = [
    "Hello, my name is",
    "The capital of France is",
    "The future of AI is",
]
sampling_params = SamplingParams(temperature=0.8, top_p=0.95)

llm = LLM(model="facebook/opt-125m")
outputs = llm.generate(prompts, sampling_params)

for output in outputs:
    print(f"Prompt: {output.prompt!r}")
    print(f"Generated: {output.outputs[0].text!r}\n")
```

### Online Serving

```bash
# Start the server
vllm serve Qwen/Qwen2.5-1.5B-Instruct

# Query with curl
curl http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "Qwen/Qwen2.5-1.5B-Instruct",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"}
        ]
    }'
```

```python
from openai import OpenAI

client = OpenAI(api_key="EMPTY", base_url="http://localhost:8000/v1")
response = client.chat.completions.create(
    model="Qwen/Qwen2.5-1.5B-Instruct",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.choices[0].message.content)
```

## Hardware Support

| Platform | Status | Notes |
|----------|--------|-------|
| NVIDIA CUDA | Full support | Primary target, all features |
| AMD ROCm | Full support | ROCm 7.0+, most features |
| Google TPU | Supported | Via vllm-tpu package |
| Intel Gaudi | Supported | Via plugin ecosystem |
| Intel XPU | Supported | Via intel/vllm Docker image |
| Apple Silicon | Experimental | Via vLLM-Metal with MLX |
| CPU-only | Supported | Via vllm-cpu package |

## Key Environment Variables

| Variable | Purpose |
|----------|---------|
| `VLLM_API_KEY` | API key for the server |
| `HF_TOKEN` | HuggingFace token for gated models |
| `VLLM_USE_MODELSCOPE=True` | Use ModelScope instead of HuggingFace |
| `CUDA_VISIBLE_DEVICES` | Restrict visible GPUs |
| `VLLM_ENABLE_CUDA_COMPATIBILITY=1` | Enable older CUDA driver support |

## Common Pitfalls

1. **Out of memory** — reduce `--max-model-len` or increase `--tensor-parallel-size`
2. **Slow first request** — CUDA graph compilation and model loading happen on first use; subsequent requests are fast
3. **Chat template missing** — instruct/chat models need a chat template; pass `--chat-template` if not built into the model
4. **Wrong attention backend** — let vLLM auto-select unless you have a specific reason to override with `--attention-backend`
