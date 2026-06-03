# Haystack Generators

> Source: [docs.haystack.deepset.ai/docs/generators](https://docs.haystack.deepset.ai/docs/generators) | haystack-ai 2.30.0

## Table of Contents

- [What Are Generators](#what-are-generators)
- [Chat Generators vs Text Generators](#chat-generators-vs-text-generators)
- [Supported Providers](#supported-providers)
- [OpenAI Generator](#openai-generator)
- [Anthropic Generator](#anthropic-generator)
- [Hugging Face Generators](#hugging-face-generators)
- [Ollama Generator](#ollama-generator)
- [Generation Parameters](#generation-parameters)
- [Streaming](#streaming)
- [Tool Support](#tool-support)
- [Common Pitfalls](#common-pitfalls)

## What Are Generators

Generators are components that produce text using LLMs. They accept prompts or chat messages and return generated text. Every RAG pipeline and agent needs a generator as its core reasoning engine.

Two categories:
- **Chat Generators** — conversational, message-based (most common)
- **Text Generators** — single-prompt completion (legacy, less common)

## Chat Generators vs Text Generators

| Feature | ChatGenerator | Generator |
|---------|--------------|-----------|
| Input | `list[ChatMessage]` | `str` prompt |
| Output | `list[ChatMessage]` replies | `list[str]` replies |
| System prompt | Via `ChatMessage.from_system()` | Embedded in prompt |
| Tool calling | Supported | Not supported |
| Use with Agent | Yes | No |
| Recommended | Yes | Only for simple completion |

## Supported Providers

### Cloud Providers

| Provider | Package | ChatGenerator |
|----------|---------|---------------|
| OpenAI | `haystack-ai` (built-in) | `OpenAIChatGenerator` |
| Azure OpenAI | `haystack-ai` (built-in) | `AzureOpenAIChatGenerator` |
| Anthropic | `anthropic-haystack` | `AnthropicChatGenerator` |
| Google GenAI | `google-genai-haystack` | `GoogleGenAIChatGenerator` |
| Amazon Bedrock | `amazon-bedrock-haystack` | `AmazonBedrockChatGenerator` |
| Cohere | `cohere-haystack` | `CohereChatGenerator` |
| Mistral | `mistral-haystack` | `MistralChatGenerator` |
| NVIDIA | `nvidia-haystack` | `NvidiaChatGenerator` |
| Together AI | `together-haystack` | `TogetherAIChatGenerator` |

### Local / Self-Hosted

| Provider | Package | ChatGenerator |
|----------|---------|---------------|
| Hugging Face Local | `haystack-ai` (built-in) | `HuggingFaceLocalChatGenerator` |
| Ollama | `ollama-haystack` | `OllamaChatGenerator` |
| vLLM | `vllm-haystack` | `VLLMChatGenerator` |
| Llama.cpp | `llama-cpp-haystack` | `LlamaCppChatGenerator` |

### Image Generation

| Provider | Package | Generator |
|----------|---------|-----------|
| DALL-E | `haystack-ai` (built-in) | `DALLEImageGenerator` |
| Vertex AI | `google-vertex-haystack` | Vertex image generator |

## OpenAI Generator

Built-in, no extra package needed:

```python
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.dataclasses import ChatMessage

generator = OpenAIChatGenerator(model="gpt-4o-mini")

result = generator.run(
    messages=[
        ChatMessage.from_system("You are a helpful assistant."),
        ChatMessage.from_user("What is Haystack?"),
    ]
)
print(result["replies"][0].text)
```

### With Custom Parameters

```python
generator = OpenAIChatGenerator(
    model="gpt-4o",
    generation_kwargs={
        "temperature": 0.7,
        "max_tokens": 500,
        "top_p": 0.9,
    },
)
```

### OpenAI Responses API

For advanced features like built-in web search:

```python
from haystack.components.generators.chat import OpenAIResponsesChatGenerator

generator = OpenAIResponsesChatGenerator(model="gpt-4o")
```

## Anthropic Generator

```bash
pip install anthropic-haystack
```

```python
from haystack_integrations.components.generators.anthropic import AnthropicChatGenerator
from haystack.dataclasses import ChatMessage

generator = AnthropicChatGenerator(model="claude-sonnet-4-20250514")

result = generator.run(
    messages=[
        ChatMessage.from_system("Be concise."),
        ChatMessage.from_user("Explain RAG in one sentence."),
    ]
)
```

## Hugging Face Generators

### Local (Transformers)

```python
from haystack.components.generators.chat import HuggingFaceLocalChatGenerator

generator = HuggingFaceLocalChatGenerator(
    model="HuggingFaceTB/SmolLM-135M-Instruct",
    generation_kwargs={"max_new_tokens": 256},
)
generator.warm_up()  # Load model into memory

result = generator.run(
    messages=[ChatMessage.from_user("Hello!")]
)
```

### API (Inference Endpoints)

```python
from haystack.components.generators.chat import HuggingFaceAPIChatGenerator
from haystack.utils import Secret

generator = HuggingFaceAPIChatGenerator(
    api_type="serverless_inference_api",
    api_params={"model": "meta-llama/Llama-3.1-8B-Instruct"},
    token=Secret.from_env_var("HF_TOKEN"),
)
```

## Ollama Generator

```bash
pip install ollama-haystack
```

```python
from haystack_integrations.components.generators.ollama import OllamaChatGenerator

generator = OllamaChatGenerator(
    model="llama3.1",
    url="http://localhost:11434",
)

result = generator.run(
    messages=[ChatMessage.from_user("What is Haystack?")]
)
```

## Generation Parameters

Common parameters across providers:

| Parameter | Type | Description |
|-----------|------|-------------|
| `temperature` | float | Randomness (0.0 = deterministic, 2.0 = very random) |
| `max_tokens` | int | Maximum tokens in the response |
| `top_p` | float | Nucleus sampling threshold |
| `stop` | list[str] | Stop sequences |
| `frequency_penalty` | float | Penalize repeated tokens |
| `presence_penalty` | float | Penalize tokens already present |

Set at init or override at runtime:

```python
# At initialization
generator = OpenAIChatGenerator(
    generation_kwargs={"temperature": 0.3}
)

# At runtime (overrides init)
result = generator.run(
    messages=messages,
    generation_kwargs={"temperature": 0.9, "max_tokens": 200},
)
```

## Streaming

Most chat generators support token-by-token streaming:

```python
from haystack.components.generators.utils import print_streaming_chunk

generator = OpenAIChatGenerator(
    model="gpt-4o-mini",
    streaming_callback=print_streaming_chunk,
)

result = generator.run(
    messages=[ChatMessage.from_user("Tell me a story")]
)
```

Custom streaming callback:

```python
collected_tokens = []

def collect_tokens(chunk):
    if chunk.content:
        collected_tokens.append(chunk.content)

generator = OpenAIChatGenerator(
    streaming_callback=collect_tokens,
)
```

## Tool Support

Pass tools to generators for function calling:

```python
from haystack.tools import tool

@tool
def lookup(query: str) -> str:
    """Look up information."""
    return f"Info about: {query}"

generator = OpenAIChatGenerator(
    model="gpt-4o-mini",
    tools=[lookup],
)

result = generator.run(
    messages=[ChatMessage.from_user("Look up Python")]
)

# Check if the LLM wants to call a tool
reply = result["replies"][0]
if reply.tool_calls:
    print(reply.tool_calls[0].tool_name)  # "lookup"
    print(reply.tool_calls[0].arguments)  # {"query": "Python"}
```

Not all generators support tools. Check the streaming/tools compatibility table in the docs.

## Common Pitfalls

**Wrong package for the provider**: OpenAI and HuggingFace generators are built-in. All others need separate packages (e.g., `anthropic-haystack`).

**Forgetting warm_up() for local models**: `HuggingFaceLocalChatGenerator` and `LlamaCppChatGenerator` need `warm_up()` to load models. In pipelines this happens automatically, but standalone usage requires explicit calls.

**Mixing ChatGenerator and Generator**: Agents and `ChatPromptBuilder` require chat generators. Don't use text-only generators with them.

**Deprecated generators**: `GoogleAIGeminiChatGenerator` is deprecated — use `GoogleGenAIChatGenerator` instead.

## Related Topics

- Agents → `03-agents.md`
- Tool calling → `04-tools.md`
- Prompt building → `10-prompt-building.md`
