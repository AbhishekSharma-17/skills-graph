# Distributed Inference

> Source: [docs.vllm.ai](https://docs.vllm.ai/) — v0.22.1

## Table of Contents
- [Overview](#overview)
- [Parallelism Strategies](#parallelism-strategies)
- [Single-Node Multi-GPU](#single-node-multi-gpu)
- [Multi-Node Deployment](#multi-node-deployment)
- [Expert Parallelism](#expert-parallelism)
- [Data Parallelism](#data-parallelism)
- [Context Parallelism](#context-parallelism)
- [Network Optimization](#network-optimization)
- [Decision Guide](#decision-guide)
- [Common Pitfalls](#common-pitfalls)

## Overview

When a model is too large for a single GPU, vLLM distributes it across multiple GPUs using parallelism strategies. The two primary strategies are tensor parallelism (split layers across GPUs) and pipeline parallelism (split model depth across GPUs).

## Parallelism Strategies

### Tensor Parallelism (TP)

Splits each transformer layer's weights across multiple GPUs. All GPUs work on every layer simultaneously, reducing latency (time-to-first-token). Best for single-node deployments.

```bash
# 4-GPU tensor parallelism
vllm serve meta-llama/Llama-3.1-70B-Instruct --tensor-parallel-size 4
```

```python
from vllm import LLM
llm = LLM(model="meta-llama/Llama-3.1-70B-Instruct", tensor_parallel_size=4)
```

**Requirements:**
- `tensor_parallel_size` must be a power of 2
- Must divide evenly into the model's attention head count
- GPUs should be on the same node with high-bandwidth interconnect (NVLink preferred)

### Pipeline Parallelism (PP)

Splits the model by depth — different groups of layers run on different GPUs/nodes. Each GPU processes a different stage. Better for multi-node setups and maximizing throughput.

```bash
# 2-node pipeline parallelism
vllm serve model --pipeline-parallel-size 2
```

### Combined TP + PP

For very large models across multiple nodes:

```bash
# 4 GPUs per node, 2 nodes
vllm serve model \
    --tensor-parallel-size 4 \
    --pipeline-parallel-size 2
```

Total GPUs = `tensor_parallel_size * pipeline_parallel_size` (= 8 in this example).

## Single-Node Multi-GPU

The most common multi-GPU scenario. vLLM uses Python multiprocessing by default (no Ray needed).

### Setup

```bash
# 2-GPU
vllm serve meta-llama/Llama-3.1-70B-Instruct --tensor-parallel-size 2

# 4-GPU (for 405B or large quantized models)
vllm serve meta-llama/Llama-3.1-70B-Instruct --tensor-parallel-size 4

# 8-GPU
vllm serve model --tensor-parallel-size 8
```

### Python API

```python
from vllm import LLM, SamplingParams

llm = LLM(
    model="meta-llama/Llama-3.1-70B-Instruct",
    tensor_parallel_size=2,
    gpu_memory_utilization=0.9,
)

outputs = llm.generate(["Hello!"], SamplingParams(max_tokens=100))
```

### Selecting Specific GPUs

```bash
# Use only GPUs 2 and 3
CUDA_VISIBLE_DEVICES=2,3 vllm serve model --tensor-parallel-size 2
```

### Verifying Setup

After starting, check the log for:

```
INFO: GPU KV cache size: X tokens
```

This indicates the total KV cache capacity across all GPUs.

## Multi-Node Deployment

For models that don't fit on a single machine.

### Using Ray (Recommended for Multi-Node)

Ray is the default distributed runtime for multi-node inference.

**Head Node:**
```bash
ray start --head

vllm serve model \
    --tensor-parallel-size 4 \
    --pipeline-parallel-size 2
```

**Worker Node(s):**
```bash
ray start --address=<head-node-ip>:6379
```

vLLM auto-discovers Ray workers and distributes model shards.

### Using Multiprocessing (No Ray)

For manual control over multi-node placement:

**Node 0 (Rank 0):**
```bash
vllm serve model \
    --tensor-parallel-size 4 \
    --pipeline-parallel-size 2 \
    --nnodes 2 \
    --node-rank 0 \
    --master-addr <node0-ip>
```

**Node 1 (Rank 1):**
```bash
vllm serve model \
    --tensor-parallel-size 4 \
    --pipeline-parallel-size 2 \
    --nnodes 2 \
    --node-rank 1 \
    --master-addr <node0-ip>
```

### Docker Multi-Node

```bash
# Head node
docker run --runtime nvidia --gpus all \
    --network=host \
    --ipc=host \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    vllm/vllm-openai:latest \
    --model model \
    --tensor-parallel-size 4 \
    --pipeline-parallel-size 2
```

Use `--ipc=host` for shared memory access between GPU processes.

## Expert Parallelism

For Mixture of Experts (MoE) models, vLLM supports expert parallelism — distributing expert layers across GPUs while keeping attention layers data-parallel.

```bash
vllm serve deepseek-ai/DeepSeek-V3 \
    --tensor-parallel-size 8 \
    --expert-parallel-size 4
```

This combines Data Parallel attention with Expert or Tensor Parallel MoE layers for better efficiency on large MoE models.

## Data Parallelism

Run multiple copies of the model (or model shards) to increase throughput:

```bash
# 2 replicas, each on 4 GPUs (8 GPUs total)
vllm serve model \
    --tensor-parallel-size 4 \
    --data-parallel-size 2
```

Data parallelism is useful when a single model instance can't saturate all available GPUs and you want higher aggregate throughput.

## Context Parallelism

For extremely long contexts, context parallelism splits the sequence across GPUs:

```bash
vllm serve model --context-parallel-size 2
```

This enables processing very long sequences (100K+ tokens) by distributing the KV cache across GPUs. Context parallelism requires specific attention backend support.

## Network Optimization

### InfiniBand and GPUDirect RDMA

For multi-node tensor parallelism, high-speed networking is critical:

```bash
# Docker: enable IPC and InfiniBand
docker run --runtime nvidia --gpus all \
    --ipc=host \
    --cap-add=IPC_LOCK \
    --device=/dev/infiniband \
    vllm/vllm-openai:latest \
    ...
```

### Verifying Network

Check NCCL logs for optimal communication:

```
[send] via NET/IB/GDRDMA    # Good: using InfiniBand with GPU Direct
[send] via NET/Socket        # Slow: falling back to TCP
```

### NCCL Environment Variables

```bash
# Force specific NCCL settings
export NCCL_IB_DISABLE=0          # Enable InfiniBand
export NCCL_NET_GDR_LEVEL=5       # Max GPUDirect RDMA level
export NCCL_SOCKET_IFNAME=eth0    # Network interface for fallback
```

## Decision Guide

```
Model fits on 1 GPU?
  └─ YES → No parallelism needed
  └─ NO → Model fits on 1 node?
           └─ YES → Use tensor parallelism
                     (--tensor-parallel-size = number of GPUs needed)
           └─ NO → Use TP + PP
                    (--tensor-parallel-size = GPUs per node)
                    (--pipeline-parallel-size = number of nodes)
```

### Sizing Guidelines

| Model Size (FP16) | Minimum GPUs (80GB) | Recommended Config |
|-------------------|--------------------|--------------------|
| 7B–8B | 1 | TP=1 |
| 13B | 1 | TP=1 |
| 30B–34B | 1 | TP=1 (tight) or TP=2 |
| 70B | 2 | TP=2 |
| 70B (quantized 4-bit) | 1 | TP=1 |
| 405B | 8 | TP=8 or TP=4,PP=2 |
| 405B (quantized FP8) | 4 | TP=4 |

### Performance Tradeoffs

| Strategy | Latency | Throughput | Communication |
|----------|---------|------------|---------------|
| TP (same node) | Lowest | Good | NVLink |
| TP (cross node) | Medium | Medium | InfiniBand (required) |
| PP | Medium | Highest | Lower bandwidth OK |
| TP + PP | Flexible | Flexible | Mix |

## Common Pitfalls

1. **TP size not power of 2** — `tensor_parallel_size` must be a power of 2 (1, 2, 4, 8)
2. **TP > attention heads** — TP size cannot exceed the number of attention heads; check model config
3. **Slow multi-node without InfiniBand** — tensor parallelism over TCP is orders of magnitude slower; use pipeline parallelism for slow networks
4. **KV cache reduced** — more GPUs for TP means more communication overhead and slightly less usable KV cache per GPU
5. **Ray version mismatch** — all nodes must run the same Ray and vLLM versions
6. **CUDA_VISIBLE_DEVICES with TP** — set it before launching; vLLM uses all visible GPUs up to `tensor_parallel_size`
7. **OOM with PP** — pipeline parallelism doesn't split individual layers; if one stage's layers exceed a single GPU, combine with TP
