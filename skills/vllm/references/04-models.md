# Supported Models

> Source: [docs.vllm.ai](https://docs.vllm.ai/) — v0.22.1

## Table of Contents
- [Overview](#overview)
- [Model Categories](#model-categories)
- [Popular Model Families](#popular-model-families)
- [Loading Models](#loading-models)
- [Model Configuration](#model-configuration)
- [Hardware Requirements](#hardware-requirements)
- [Custom Models](#custom-models)
- [Common Pitfalls](#common-pitfalls)

## Overview

vLLM supports 200+ model architectures from HuggingFace, including decoder-only LLMs, encoder-decoder models, mixture-of-experts (MoE), multimodal models, embedding models, reward models, and classification models. If a model is on HuggingFace and uses a supported architecture, vLLM can likely serve it.

## Model Categories

### Decoder-Only Language Models
Standard autoregressive text generation models.

**Architectures**: LlamaForCausalLM, MistralForCausalLM, Qwen2ForCausalLM, GPT2LMHeadModel, GPTNeoXForCausalLM, PhiForCausalLM, Phi3ForCausalLM, GemmaForCausalLM, Gemma2ForCausalLM, CohereForCausalLM, StableLmForCausalLM, StarCoder2ForCausalLM, and many more.

### Mixture of Experts (MoE) Models
Models with sparse expert routing for efficient large-scale inference.

**Architectures**: MixtralForCausalLM, Qwen2MoeForCausalLM, DeepseekV2ForCausalLM, DeepseekV3ForCausalLM, ArcticForCausalLM, DbrxForCausalLM, JambaForCausalLM.

### Multimodal Models
Models that accept text with images, audio, or video.

**Vision-Language**: LlavaForConditionalGeneration, Qwen2VLForConditionalGeneration, Phi3VForCausalLM, InternVLChatModel, PaliGemmaForConditionalGeneration, MllamaForConditionalGeneration, Idefics3ForConditionalGeneration.

**Audio-Language**: WhisperForConditionalGeneration, Qwen2AudioForConditionalGeneration, GraniteSpeechModel.

**Video-Language**: Qwen2_5_VLForConditionalGeneration (supports video), LlavaNextVideoForCausalLM.

### Embedding Models
Models for generating vector representations of text.

**Architectures**: MistralModel (e5-mistral), LlamaModel, Qwen2Model, GemmaModel, BertModel, RobertaModel, XLMRobertaModel.

### Reward / Classification Models
Models that score or classify text.

**Architectures**: LlamaForSequenceClassification, Qwen2ForSequenceClassification, GPTNeoXForSequenceClassification.

## Popular Model Families

| Family | Example Models | Sizes | Notes |
|--------|---------------|-------|-------|
| Llama 3.x | Llama-3.1-8B-Instruct, Llama-3.1-70B, Llama-3.3-70B | 1B–405B | Meta's flagship; full vLLM support |
| Llama 4 | Llama-4-Scout-17B, Llama-4-Maverick-17B | 17B MoE | Latest generation with MoE |
| Qwen 2.5/3 | Qwen2.5-1.5B, Qwen2.5-72B, Qwen3-30B-A3B | 0.5B–72B | Alibaba; excellent multilingual |
| Mistral | Mistral-7B-v0.3, Mixtral-8x7B, Mistral-Small-24B | 7B–24B | Strong European models |
| DeepSeek | DeepSeek-V3, DeepSeek-R1 | 236B MoE | Reasoning-focused |
| Gemma 2 | gemma-2-2b, gemma-2-9b, gemma-2-27b | 2B–27B | Google's open models |
| Phi 3/4 | Phi-3-mini, Phi-3-medium, Phi-4 | 3.8B–14B | Microsoft; strong at small sizes |
| Command R | command-r, command-r-plus | 35B–104B | Cohere; tool calling + RAG |
| StarCoder 2 | starcoder2-3b, starcoder2-15b | 3B–15B | Code generation |

## Loading Models

### From HuggingFace Hub

```python
from vllm import LLM

# Public model
llm = LLM(model="meta-llama/Llama-3.1-8B-Instruct")

# Gated model (requires HF_TOKEN)
import os
os.environ["HF_TOKEN"] = "hf_..."
llm = LLM(model="meta-llama/Llama-3.1-70B-Instruct")

# Specific revision
llm = LLM(model="meta-llama/Llama-3.1-8B-Instruct", revision="main")
```

### From Local Path

```python
llm = LLM(model="/path/to/local/model")
```

### From ModelScope

```python
import os
os.environ["VLLM_USE_MODELSCOPE"] = "True"
llm = LLM(model="qwen/Qwen2.5-7B-Instruct")
```

### CLI Model Loading

```bash
# HuggingFace
vllm serve meta-llama/Llama-3.1-8B-Instruct

# With HuggingFace token
HF_TOKEN=hf_... vllm serve meta-llama/Llama-3.1-70B-Instruct

# Local path
vllm serve /data/models/llama-3.1-8b-instruct

# Custom download directory
vllm serve model --download-dir /data/hf_cache
```

## Model Configuration

### Data Type

```bash
# Auto-detect from model config (recommended)
vllm serve model --dtype auto

# Force float16
vllm serve model --dtype float16

# Force bfloat16 (recommended for newer GPUs: A100, H100)
vllm serve model --dtype bfloat16
```

### Context Length

```bash
# Use model's default max length
vllm serve model

# Override to shorter length (saves GPU memory)
vllm serve model --max-model-len 4096

# Override to longer with rope scaling
vllm serve model --max-model-len 32768
```

### Custom Model Code

Some models require custom code from their HuggingFace repository:

```bash
vllm serve model --trust-remote-code
```

```python
llm = LLM(model="model", trust_remote_code=True)
```

### Tokenizer Configuration

```bash
# Use a different tokenizer
vllm serve model --tokenizer another-model/tokenizer

# Custom chat template
vllm serve model --chat-template /path/to/template.jinja
```

## Hardware Requirements

### Memory Estimation

Rough VRAM requirements for FP16/BF16 models:

| Model Size | FP16 VRAM | Recommended GPU(s) |
|-----------|-----------|-------------------|
| 1B–3B | 2–6 GB | 1x RTX 3060/4060 |
| 7B–8B | 14–16 GB | 1x RTX 4090 / A10G |
| 13B | 26 GB | 1x A100-40GB |
| 30B–34B | 60–68 GB | 1x A100-80GB or 2x A10G |
| 70B | 140 GB | 2x A100-80GB |
| 405B | 810 GB | 8x H100-80GB |

Quantization significantly reduces these requirements (see `references/05-quantization.md`).

### GPU Memory Budget

vLLM allocates GPU memory for:
1. **Model weights** — fixed, determined by model size and dtype
2. **KV cache** — dynamic, controlled by `gpu_memory_utilization`
3. **Activation memory** — temporary, for forward pass computation

```bash
# Reserve 90% of GPU for vLLM (default)
vllm serve model --gpu-memory-utilization 0.9

# Conservative, leave headroom for other processes
vllm serve model --gpu-memory-utilization 0.8
```

## Custom Models

### Adding Custom Architecture Support

vLLM can serve models with custom architectures if they follow the HuggingFace pattern:

1. The model must be loadable by `transformers.AutoModelForCausalLM`
2. Enable with `--trust-remote-code`
3. The architecture must be compatible with vLLM's inference engine

### Out-of-Tree Models

Register custom model implementations without modifying vLLM source:

```python
from vllm import ModelRegistry

# Register before creating LLM instance
ModelRegistry.register_model("MyCustomModel", "path.to.module:MyModel")

llm = LLM(model="my-custom-model")
```

## Common Pitfalls

1. **Gated models need HF_TOKEN** — models like Llama require accepting the license on HuggingFace and setting `HF_TOKEN`
2. **trust_remote_code=False by default** — some models (InternLM, ChatGLM, etc.) need `--trust-remote-code` to load
3. **Wrong dtype for GPU** — use `bfloat16` on Ampere+ GPUs (A100, H100); older GPUs may need `float16`
4. **Context length vs memory** — doubling `max-model-len` roughly doubles KV cache memory; reduce it if OOM
5. **Base vs Instruct models** — base models have no chat template; use the completions API or provide a template
6. **Model too large for GPU** — use `--tensor-parallel-size` to split across GPUs, or quantization to reduce memory
