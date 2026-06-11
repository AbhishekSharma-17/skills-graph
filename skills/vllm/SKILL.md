---
name: vllm
description: "High-throughput LLM inference and serving engine with PagedAttention, continuous batching, and OpenAI-compatible API. MANDATORY TRIGGERS: vLLM, vllm, LLM serving, LLM inference engine, PagedAttention. Also trigger when the user wants to serve LLMs in production, deploy models with tensor parallelism, use speculative decoding, quantize models for inference, build OpenAI-compatible API servers, or optimize LLM throughput and latency. When in doubt about whether to use this skill for LLM serving tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["llm", "inference", "serving", "gpu", "quantization", "openai-api", "tensor-parallelism", "production"]
---

# vLLM

> Source: [docs.vllm.ai](https://docs.vllm.ai/) | Version tracked: 0.22.1 | `pip install vllm`

## Reference Files

| File | Read When |
|------|-----------|
| `references/00-overview.md` | Starting with vLLM, understanding architecture, installation, quick start |
| `references/01-offline-inference.md` | Batch inference with LLM class, SamplingParams, chat API, generate() |
| `references/02-serving.md` | OpenAI-compatible API server, endpoints, vllm serve, client setup |
| `references/03-sampling-params.md` | Generation parameters: temperature, top_p, top_k, penalties, stop tokens |
| `references/04-models.md` | Supported model architectures, loading models, HuggingFace, model config |
| `references/05-quantization.md` | FP8, GPTQ, AWQ, GGUF, BitsAndBytes, hardware compatibility matrix |
| `references/06-distributed-inference.md` | Tensor/pipeline/expert parallelism, multi-GPU, multi-node, Ray |
| `references/07-speculative-decoding.md` | Draft models, EAGLE, MTP, n-gram, --speculative-config |
| `references/08-structured-outputs.md` | JSON schema, regex, grammar constraints, guided decoding backends |
| `references/09-tool-calling.md` | Function calling, tool parsers, supported models, custom parsers |
| `references/10-multimodal.md` | Vision, audio, video inputs, embedding inputs, media handling |
| `references/11-lora-adapters.md` | LoRA serving, dynamic loading/unloading, multi-adapter, plugins |
| `references/12-production-deployment.md` | Docker, Kubernetes, Prometheus metrics, autoscaling, best practices |

## Installation

```bash
pip install vllm                    # NVIDIA CUDA (default)
uv pip install vllm --torch-backend=auto  # With uv (recommended)
pip install vllm-tpu                # Google TPU
```

## Quick Reference

- [Docs](https://docs.vllm.ai/) | [GitHub](https://github.com/vllm-project/vllm) | [PyPI](https://pypi.org/project/vllm/)
