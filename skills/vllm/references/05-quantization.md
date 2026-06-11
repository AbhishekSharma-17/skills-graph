# Quantization

> Source: [docs.vllm.ai](https://docs.vllm.ai/) — v0.22.1

## Table of Contents
- [Overview](#overview)
- [Quantization Methods](#quantization-methods)
- [Hardware Compatibility Matrix](#hardware-compatibility-matrix)
- [Using Pre-Quantized Models](#using-pre-quantized-models)
- [Online Quantization](#online-quantization)
- [GPTQ Models](#gptq-models)
- [AWQ Models](#awq-models)
- [FP8 Quantization](#fp8-quantization)
- [GGUF Models](#gguf-models)
- [BitsAndBytes](#bitsandbytes)
- [Quantized KV Cache](#quantized-kv-cache)
- [Custom Quantization Plugins](#custom-quantization-plugins)
- [Common Pitfalls](#common-pitfalls)

## Overview

Quantization reduces model memory footprint by representing weights (and optionally activations) in lower precision. This lets you serve larger models on fewer GPUs, or fit more concurrent requests in memory at the cost of minor quality degradation.

vLLM supports loading pre-quantized models from HuggingFace and performing online (runtime) quantization for some methods.

## Quantization Methods

| Method | Bits | Type | Pre-quantized | Online | Notes |
|--------|------|------|---------------|--------|-------|
| FP8 (W8A8) | 8-bit | Weight + Activation | Yes | Yes | Best for Hopper/Ada GPUs |
| GPTQ | 4/8-bit | Weight-only | Yes | No | Most popular, wide support |
| AWQ | 4-bit | Weight-only | Yes | No | Activation-aware, fast |
| Marlin | 4-bit | Weight-only | Yes | No | Optimized GPTQ kernel |
| GGUF | 2–8-bit | Weight-only | Yes | No | llama.cpp format |
| BitsAndBytes | 4/8-bit | Weight-only | Yes | Yes | Easy to use, NF4 support |
| INT8 (W8A8) | 8-bit | Weight + Activation | Yes | No | Via llm-compressor |
| INT4 (W4A16) | 4-bit | Weight-only | Yes | No | Via llm-compressor |
| TorchAO | Various | Various | Yes | Yes | PyTorch native |
| NVIDIA ModelOpt | Various | Various | Yes | No | GPU-specific optimization |

## Hardware Compatibility Matrix

| Method | Volta (V100) | Turing (T4) | Ampere (A100) | Ada (L40/4090) | Hopper (H100) | AMD | CPU |
|--------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| AWQ | - | Yes | Yes | Yes | Yes | - | Yes |
| GPTQ | Yes | Yes | Yes | Yes | Yes | - | Yes |
| Marlin | - | Yes* | Yes | Yes | Yes | - | - |
| FP8 (W8A8) | - | - | - | Yes | Yes | Yes | - |
| INT8 (W8A8) | - | Yes | Yes | Yes | Yes | - | Yes |
| BitsAndBytes | Yes | Yes | Yes | Yes | Yes | - | - |
| GGUF | Yes | Yes | Yes | Yes | Yes | Yes | - |

*Turing: Marlin supported but not MXFP4.

## Using Pre-Quantized Models

The simplest approach — download and serve a model that's already quantized on HuggingFace:

```python
from vllm import LLM

# GPTQ model
llm = LLM(model="TheBloke/Llama-2-13B-Chat-GPTQ", quantization="gptq")

# AWQ model
llm = LLM(model="TheBloke/Llama-2-7B-Chat-AWQ", quantization="awq")

# FP8 model
llm = LLM(model="neuralmagic/Meta-Llama-3.1-8B-Instruct-FP8", quantization="fp8")
```

```bash
# CLI
vllm serve TheBloke/Llama-2-13B-Chat-GPTQ --quantization gptq
vllm serve TheBloke/Llama-2-7B-Chat-AWQ --quantization awq
```

Many pre-quantized models auto-detect the quantization method from their config. You can often omit `--quantization`:

```bash
vllm serve TheBloke/Llama-2-7B-Chat-AWQ  # auto-detected
```

## Online Quantization

Apply quantization at load time to any FP16/BF16 model. No separate quantization step needed.

### FP8 Online Quantization

Available on Ada (L40, RTX 4090) and Hopper (H100) GPUs:

```bash
vllm serve meta-llama/Llama-3.1-8B-Instruct --quantization fp8
```

```python
llm = LLM(model="meta-llama/Llama-3.1-8B-Instruct", quantization="fp8")
```

### BitsAndBytes Online Quantization

```python
from vllm import LLM

# 4-bit NF4 quantization
llm = LLM(
    model="meta-llama/Llama-3.1-8B-Instruct",
    quantization="bitsandbytes",
    load_format="bitsandbytes",
)
```

## GPTQ Models

GPTQ uses calibration data to find optimal weight quantization. Models must be pre-quantized using tools like AutoGPTQ or GPTQModel.

```bash
# Serve a 4-bit GPTQ model
vllm serve TheBloke/Llama-2-70B-Chat-GPTQ \
    --quantization gptq \
    --tensor-parallel-size 2

# Marlin kernel (faster GPTQ inference on supported hardware)
vllm serve TheBloke/Llama-2-7B-Chat-GPTQ --quantization marlin
```

### Memory Savings

| Model | FP16 | GPTQ-4bit | Savings |
|-------|------|-----------|---------|
| 7B | 14 GB | ~4 GB | ~71% |
| 13B | 26 GB | ~7 GB | ~73% |
| 70B | 140 GB | ~35 GB | ~75% |

### Marlin Kernel

Marlin is an optimized kernel for GPTQ models that provides faster inference on Turing+ GPUs:

```bash
vllm serve model --quantization marlin
```

Automatically used when the hardware supports it and the model format is compatible.

## AWQ Models

AWQ (Activation-Aware Weight Quantization) preserves salient weights at higher precision. Often slightly better quality than GPTQ at the same bit width.

```bash
vllm serve TheBloke/Llama-2-7B-Chat-AWQ --quantization awq

# With Marlin kernel for faster inference
vllm serve TheBloke/Llama-2-7B-Chat-AWQ --quantization awq_marlin
```

## FP8 Quantization

FP8 provides near-lossless quantization for weights and activations, with minimal quality degradation. Best option for Hopper (H100) and Ada (L40, RTX 4090) GPUs.

```bash
# Online FP8 (quantize at load time)
vllm serve meta-llama/Llama-3.1-70B-Instruct \
    --quantization fp8 \
    --tensor-parallel-size 4

# Pre-quantized FP8 model
vllm serve neuralmagic/Meta-Llama-3.1-70B-Instruct-FP8
```

### Quantizing with llm-compressor

```python
from llmcompressor.modifiers.quantization import QuantizationModifier
from llmcompressor import oneshot

recipe = QuantizationModifier(
    targets="Linear",
    scheme="FP8_DYNAMIC",
)

oneshot(
    model="meta-llama/Llama-3.1-8B-Instruct",
    recipe=recipe,
    output_dir="./Llama-3.1-8B-Instruct-FP8",
)
```

## GGUF Models

GGUF is the format used by llama.cpp, supporting various quantization levels (Q2_K through Q8_0).

```bash
vllm serve TheBloke/Llama-2-7B-Chat-GGUF --quantization gguf
```

```python
llm = LLM(model="TheBloke/Llama-2-7B-Chat-GGUF", quantization="gguf")
```

GGUF supports the widest range of hardware, including AMD GPUs.

## BitsAndBytes

Simple 4-bit and 8-bit quantization using HuggingFace's bitsandbytes library. Good for quick experimentation.

```python
llm = LLM(
    model="meta-llama/Llama-3.1-8B-Instruct",
    quantization="bitsandbytes",
    load_format="bitsandbytes",
)
```

Only supported on NVIDIA GPUs (Volta and newer).

## Quantized KV Cache

Independently of weight quantization, you can quantize the KV cache to save memory and serve more concurrent requests:

```bash
# FP8 KV cache
vllm serve model --kv-cache-dtype fp8_e5m2

# FP8 E4M3 format (better precision)
vllm serve model --kv-cache-dtype fp8_e4m3
```

This reduces KV cache memory by ~50% with minimal quality impact. Can be combined with weight quantization.

## Custom Quantization Plugins

vLLM supports out-of-tree quantization implementations:

```python
from vllm.model_executor.layers.quantization import register_quantization_config
from vllm.model_executor.layers.quantization.base_config import QuantizationConfig

@register_quantization_config("my_quant")
class MyQuantConfig(QuantizationConfig):
    def get_name(self) -> str:
        return "my_quant"

    def get_supported_act_dtypes(self):
        return [torch.float16]

    def get_min_capability(self) -> int:
        return 70  # Minimum compute capability

    @classmethod
    def get_config_filenames(cls):
        return ["quantize_config.json"]

    @classmethod
    def from_config(cls, config):
        return cls()

    def get_quant_method(self, layer, prefix):
        # Return quantization method for this layer type
        ...
```

Use: `LLM(model="...", quantization="my_quant")`

## Common Pitfalls

1. **GPU doesn't support the method** — FP8 requires Ada/Hopper; check the hardware compatibility matrix
2. **Quantization + tensor parallelism** — most quantized models support tensor parallelism, but `tensor_parallel_size` must divide the model's attention heads evenly
3. **Quality degradation** — FP8 is nearly lossless; GPTQ/AWQ 4-bit may show noticeable quality loss on reasoning tasks; benchmark on your use case
4. **Marlin auto-upgrade** — vLLM may automatically upgrade GPTQ/AWQ to use Marlin kernels if hardware supports it
5. **Mixed quantization** — you cannot mix different quantization methods for different layers through the standard CLI; use custom plugins for that
6. **GGUF + tensor parallelism** — GGUF models may have limited tensor parallelism support; check model-specific documentation
