# Images — Input, Analysis & Generation

## Image Input (Vision)

Pass images to any vision-capable model for analysis:

```python
from agno.agent import Agent
from agno.media import Image
from agno.models.openai import OpenAIResponses

agent = Agent(model=OpenAIResponses(id="gpt-5.2"), markdown=True)

# From URL
agent.print_response(
    "Describe this image",
    images=[Image(url="https://example.com/photo.jpg")],
    stream=True,
)

# From local file
from pathlib import Path
image_path = Path(__file__).parent / "sample.jpg"
agent.print_response(
    "Write a 3 sentence fiction story about the image",
    images=[Image(filepath=image_path)],
)

# From bytes
agent.print_response(
    "What's in this image?",
    images=[Image(content=image_bytes)],
)

# Multiple images
agent.print_response(
    "Compare these two images",
    images=[Image(url="https://...1.jpg"), Image(url="https://...2.jpg")],
)
```

## Image Input with Tools

Vision + tool calling — the agent sees the image AND can call tools:

```python
from agno.agent import Agent
from agno.media import Image
from agno.models.openai import OpenAIResponses
from agno.tools.hackernews import HackerNewsTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[HackerNewsTools()],
    markdown=True,
)

agent.print_response(
    "Tell me about this image and give me the latest news about it.",
    images=[Image(url="https://upload.wikimedia.org/wikipedia/commons/0/0c/GoldenGateBridge-001.jpg")],
    stream=True,
)
```

## Image Generation — DALL-E

Use DalleTools to generate images via DALL-E:

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.tools.dalle import DalleTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[DalleTools()],
)

agent.run("Generate an image of a sunset over mountains")

# Access generated images
images = agent.get_images()
for image in images:
    print(image.url)
```

## Image Generation — Gemini (Native)

Gemini can generate images natively via `response_modalities`:

```python
from io import BytesIO
from agno.agent import Agent, RunOutput
from agno.models.google import Gemini
from PIL import Image as PILImage

agent = Agent(
    model=Gemini(
        id="gemini-2.0-flash-exp-image-generation",
        response_modalities=["Text", "Image"],
    )
)

response = agent.run("Make me an image of a cat in a tree.")

if response and isinstance(response, RunOutput) and response.images:
    for img in response.images:
        if img.content:
            pil_image = PILImage.open(BytesIO(img.content))
            pil_image.show()
```

## Image Class Reference

```python
from agno.media import Image

Image(
    url: str = None,           # Image URL (https://...)
    filepath: str = None,      # Local file path
    content: bytes = None,     # Raw image bytes
)
```

Pick one of `url`, `filepath`, or `content`. The agent handles encoding automatically.

## Supported Models for Image Input

- **OpenAI**: GPT-4o, GPT-4o-mini, GPT-5.2, o1, o3-mini (via OpenAIResponses or OpenAIChat)
- **Google**: All Gemini models (gemini-2.0-flash, gemini-3-flash-preview, etc.)
- **Anthropic**: Claude 3+, Claude 3.5+, Claude Sonnet 4.5
- **Other**: Any model with vision capability

## Supported Models for Image Generation

- **OpenAI**: Via `DalleTools()` (DALL-E 3)
- **Google**: `gemini-2.0-flash-exp-image-generation` with `response_modalities=["Text", "Image"]`
