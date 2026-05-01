# Ollama — GPU & Performance Tuning

> Source: [docs.ollama.com/faq](https://docs.ollama.com/faq) | Version: 0.22.x

## Table of Contents

- [GPU Support Overview](#gpu-support-overview)
- [GPU Detection & Verification](#gpu-detection--verification)
- [GPU Layer Offloading](#gpu-layer-offloading)
- [Multi-GPU Setup](#multi-gpu-setup)
- [Memory Management](#memory-management)
- [Context Window Sizing](#context-window-sizing)
- [Concurrency Tuning](#concurrency-tuning)
- [Quantization & Model Size](#quantization--model-size)
- [Apple Silicon Optimization](#apple-silicon-optimization)
- [Performance Benchmarking](#performance-benchmarking)
- [Common Pitfalls](#common-pitfalls)

---

## GPU Support Overview

| Platform | GPU | Support | Notes |
|----------|-----|---------|-------|
| **NVIDIA** | CUDA (compute >=5.0) | Full | Best supported, recommended for production |
| **AMD** | ROCm | Full | Linux only, requires ROCm drivers |
| **Apple** | Metal | Full | M1/M2/M3/M4 unified memory, MLX runner for some models |
| **Intel** | — | CPU only | No GPU acceleration |

Ollama automatically detects available GPUs and offloads model layers.

## GPU Detection & Verification

```bash
# Check which GPU is being used
ollama ps

# Output shows GPU/CPU split:
# NAME           SIZE     PROCESSOR        UNTIL
# llama3.2       3.8 GB   100% GPU         4 minutes
# qwen3:32b      20 GB    60% GPU/40% CPU  Forever

# Enable debug logging for GPU details
OLLAMA_DEBUG=1 ollama serve
```

**Interpreting the PROCESSOR column:**
- `100% GPU` — all layers on GPU (fastest)
- `60% GPU/40% CPU` — model partially fits in VRAM, remaining layers on CPU
- `100% CPU` — no GPU acceleration (check drivers/support)

## GPU Layer Offloading

The `num_gpu` parameter controls how many model layers are offloaded to the GPU:

```bash
# In a Modelfile
PARAMETER num_gpu 35

# Via API options
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.2",
  "messages": [{"role": "user", "content": "Hello"}],
  "options": {"num_gpu": 999},
  "stream": false
}'
```

```python
from ollama import chat

response = chat(
    model="llama3.2",
    messages=[{"role": "user", "content": "Hello"}],
    options={"num_gpu": 0},  # Force CPU only
)
```

| Value | Behavior |
|-------|----------|
| `0` | CPU only — no GPU layers |
| `1-N` | Offload exactly N layers to GPU |
| `999` | Offload all possible layers to GPU |
| (default) | Auto-detect based on available VRAM |

## Multi-GPU Setup

Ollama can distribute model layers across multiple NVIDIA GPUs:

```bash
# Ollama auto-detects multiple GPUs
# Set num_gpu to a high value to use all GPUs
PARAMETER num_gpu 999

# To use specific GPUs only
CUDA_VISIBLE_DEVICES=0,1 ollama serve

# To exclude a GPU
CUDA_VISIBLE_DEVICES=1,2 ollama serve  # Skip GPU 0
```

**How multi-GPU works:**
- Ollama splits model layers across available GPUs
- Earlier layers go to GPU 0, later layers to GPU 1, etc.
- Inter-GPU communication adds some overhead
- Best for models too large for a single GPU

## Memory Management

### VRAM Estimation

Approximate VRAM requirements:

| Model Size | Q4_0 | Q5_1 | Q8_0 | FP16 |
|-----------|------|------|------|------|
| 3B | ~2 GB | ~2.5 GB | ~3.5 GB | ~6 GB |
| 7B | ~4 GB | ~5 GB | ~7.5 GB | ~14 GB |
| 13B | ~7 GB | ~9 GB | ~14 GB | ~26 GB |
| 34B | ~18 GB | ~23 GB | ~36 GB | ~68 GB |
| 70B | ~38 GB | ~48 GB | ~74 GB | ~140 GB |

Formula: `VRAM ≈ (params × bits_per_param / 8) + KV_cache + overhead`

### Key Environment Variables

```bash
# Reserve VRAM for system/other apps (prevents OOM)
OLLAMA_GPU_OVERHEAD=512000000  # 512 MB reserved

# Maximum models loaded simultaneously
OLLAMA_MAX_LOADED_MODELS=2  # default: 3 * num_GPUs

# Unload model after inactivity
OLLAMA_KEEP_ALIVE=5m  # default: 5 minutes
```

### Model Keep-Alive

```bash
# Per-request keep-alive
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.2",
  "messages": [{"role": "user", "content": "Hi"}],
  "keep_alive": "30m"
}'

# Keep model loaded indefinitely
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.2",
  "keep_alive": -1
}'

# Immediately unload
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.2",
  "keep_alive": 0
}'
```

## Context Window Sizing

Context window size directly impacts memory usage:

```
KV cache memory ≈ 2 × num_layers × num_heads × head_dim × num_ctx × bytes_per_param
```

| Model | num_ctx=2048 | num_ctx=8192 | num_ctx=32768 |
|-------|-------------|-------------|---------------|
| 7B Q4 | +0.5 GB | +2 GB | +8 GB |
| 13B Q4 | +1 GB | +4 GB | +16 GB |
| 70B Q4 | +2.5 GB | +10 GB | +40 GB |

```bash
# Set context window in Modelfile
PARAMETER num_ctx 8192

# Or per request
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.2",
  "options": {"num_ctx": 16384},
  "messages": [{"role": "user", "content": "..."}]
}'
```

**Rule of thumb:** doubling `num_ctx` roughly doubles the KV cache memory.

## Concurrency Tuning

```bash
# Parallel requests per model (default: auto, typically 1-4)
OLLAMA_NUM_PARALLEL=4

# Max queued requests before rejecting (default: 512)
OLLAMA_MAX_QUEUE=100

# Max concurrently loaded models
OLLAMA_MAX_LOADED_MODELS=2
```

**Memory impact of parallelism:**
- Each parallel slot allocates its own KV cache
- Total memory ≈ model_weights + (OLLAMA_NUM_PARALLEL × KV_cache_per_slot)
- With `num_ctx=4096` and `OLLAMA_NUM_PARALLEL=4`, you need 4x the KV cache memory

## Quantization & Model Size

Quantization reduces model size and VRAM usage at the cost of some quality:

| Quantization | Bits/Weight | Size vs FP16 | Quality Impact |
|-------------|-------------|-------------|----------------|
| Q4_0 | 4.0 | ~25% | Noticeable on complex reasoning |
| Q4_1 | 4.5 | ~28% | Slightly better than Q4_0 |
| Q5_0 | 5.0 | ~31% | Good balance |
| Q5_1 | 5.5 | ~34% | Very close to FP16 quality |
| Q8_0 | 8.0 | ~50% | Near-lossless |
| FP16 | 16.0 | 100% | Full precision |

```bash
# Create a quantized model
ollama create my-model -f Modelfile --quantize q4_0
```

**Guideline:** For most use cases, Q4_0 of a larger model outperforms Q8_0 of a smaller model. Prefer `llama3.1:70b-q4_0` over `llama3.1:8b-q8_0` if you have the VRAM.

## Apple Silicon Optimization

Apple Silicon (M1/M2/M3/M4) uses unified memory shared between CPU and GPU:

```bash
# Check Metal GPU usage
ollama ps
# Shows: 100% GPU (Metal)

# All system RAM is available as VRAM on Apple Silicon
# M1 Pro 32GB → ~28GB available for models
# M3 Max 128GB → ~120GB available for models
```

**Apple Silicon tips:**
- Unified memory means no CPU↔GPU transfer overhead
- Models up to ~75% of total RAM can run fully on GPU
- MLX runner (used for some models like Gemma 4) may be faster than llama.cpp on Apple Silicon
- M3/M4 Pro/Max chips offer the best local inference performance per dollar

## Performance Benchmarking

```bash
# Verbose mode shows timing statistics
ollama run llama3.2 --verbose "Write a haiku"

# Key metrics in verbose output:
# prompt eval rate:   125.45 tokens/s  ← prompt processing speed
# eval rate:          42.31 tokens/s   ← generation speed (tokens/sec)
# total duration:     1.234s
```

```python
from ollama import chat
import time

start = time.time()
response = chat(
    model="llama3.2",
    messages=[{"role": "user", "content": "Write a 100-word summary of Python"}],
)
elapsed = time.time() - start
tokens = response.eval_count
print(f"Generated {tokens} tokens in {elapsed:.2f}s ({tokens/elapsed:.1f} tok/s)")
```

## Common Pitfalls

1. **OOM crashes** — model + KV cache exceeds VRAM. Reduce `num_ctx`, use more aggressive quantization, or set `OLLAMA_GPU_OVERHEAD`
2. **Slow with GPU available** — check `ollama ps` PROCESSOR column. If showing CPU, verify GPU drivers are installed
3. **Multi-GPU imbalance** — uneven GPU memory (e.g., 24GB + 8GB) leads to suboptimal splits. Use `CUDA_VISIBLE_DEVICES` to select specific GPUs
4. **Context window too large** — setting `num_ctx=131072` on a 7B model may need 30GB+ just for KV cache
5. **Keep-alive memory leak** — models stay loaded for `OLLAMA_KEEP_ALIVE` duration. With many models, memory fills up. Use `ollama stop` or reduce keep-alive time
