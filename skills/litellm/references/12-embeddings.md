# Embeddings & Other APIs

> Source: https://docs.litellm.ai/docs/embedding/supported_embedding • Written for litellm v1.52.x

LiteLLM isn't just chat completions. It exposes embeddings, image generation, audio transcription, text-to-speech, and moderation under the same unified interface.

## Embeddings

```python
from litellm import embedding

resp = embedding(
    model="text-embedding-3-small",
    input=["Hello world", "Goodbye world"],
)

vectors = [item["embedding"] for item in resp.data]
print(len(vectors), len(vectors[0]))   # 2 1536
```

Switch providers by changing the model:
```python
embedding(model="cohere/embed-english-v3.0", input=["..."])
embedding(model="vertex_ai/text-embedding-004", input=["..."])
embedding(model="bedrock/amazon.titan-embed-text-v2:0", input=["..."])
embedding(model="huggingface/BAAI/bge-large-en-v1.5", input=["..."])
embedding(model="ollama/nomic-embed-text", input=["..."], api_base="http://localhost:11434")
```

### Async embedding

```python
from litellm import aembedding

resp = await aembedding(model="text-embedding-3-small", input=texts)
```

### Dimensions

For models that support reduced dimensions (e.g. OpenAI v3):
```python
embedding(model="text-embedding-3-small", input=["..."], dimensions=512)
```

### Response shape

```python
EmbeddingResponse(
    object="list",
    data=[
        {"index": 0, "object": "embedding", "embedding": [0.123, ...]},
        {"index": 1, "object": "embedding", "embedding": [0.456, ...]},
    ],
    model="text-embedding-3-small",
    usage=Usage(prompt_tokens=4, total_tokens=4),
)
```

## Image generation

```python
from litellm import image_generation

resp = image_generation(
    model="dall-e-3",
    prompt="A serene mountain landscape at dawn",
    size="1024x1024",
    n=1,
)
url = resp.data[0]["url"]
```

Other providers:
```python
image_generation(model="bedrock/stability.stable-diffusion-xl-v1", prompt="...")
image_generation(model="vertex_ai/imagen-3.0-generate-001", prompt="...")
```

## Audio transcription (speech-to-text)

```python
from litellm import transcription

with open("audio.mp3", "rb") as f:
    resp = transcription(
        model="whisper-1",
        file=f,
        language="en",
    )
print(resp.text)
```

Bedrock / Azure equivalents work the same way:
```python
transcription(model="azure/whisper-deployment", file=f)
```

## Text-to-speech

```python
from litellm import speech

resp = speech(
    model="tts-1",
    voice="alloy",
    input="Hello world",
)

with open("out.mp3", "wb") as f:
    f.write(resp.content)
```

## Moderation

```python
from litellm import moderation

resp = moderation(
    model="text-moderation-latest",
    input="I want to hurt someone.",
)
print(resp.results[0].flagged)         # True/False
print(resp.results[0].categories)      # per-category booleans
```

## Reranking

LiteLLM supports rerankers (Cohere, Voyage, Jina):

```python
from litellm import rerank

resp = rerank(
    model="cohere/rerank-english-v3.0",
    query="What is the capital of France?",
    documents=[
        "Paris is the capital of France.",
        "Berlin is the capital of Germany.",
        "London is the capital of the UK.",
    ],
    top_n=2,
)

for r in resp.results:
    print(r.index, r.relevance_score, r.document)
```

## Batching helpers

`batch_completion` exists for chat, but for embeddings you typically just pass a list:

```python
embedding(model="text-embedding-3-small", input=texts_list)  # one API call, many vectors
```

Most providers cap at ~2048 inputs per call. Chunk larger workloads.

## Proxy support

All of these endpoints work through the proxy under their OpenAI paths:
- `/v1/embeddings`
- `/v1/images/generations`
- `/v1/audio/transcriptions`
- `/v1/audio/speech`
- `/v1/moderations`
- `/v1/rerank`

Add them to `model_list` in `config.yaml`:
```yaml
model_list:
  - model_name: text-embedding-3-small
    litellm_params:
      model: openai/text-embedding-3-small
      api_key: os.environ/OPENAI_API_KEY

  - model_name: rerank-en
    litellm_params:
      model: cohere/rerank-english-v3.0
      api_key: os.environ/COHERE_API_KEY
```

## Common pitfalls

- **Mixing embedding dimensions** — Different models produce different vector sizes; you can't store them in the same index.
- **Provider rerank score scales differ** — Cohere returns 0–1, Voyage may return logits. Don't compare across providers.
- **Whisper file size limit** — OpenAI Whisper API caps files at 25 MB. Chunk longer audio first.
- **Image generation latency** — Slow models (DALL·E 3, Imagen) may exceed default timeouts; bump `timeout`.
- **Embedding rate limits** — Embeddings have separate quotas from chat. Token-per-minute rate limits hit fast on big corpora.

## Related
- Caching embeddings → `08-caching.md`
- Cost per embedding call → `10-cost-tracking.md`
