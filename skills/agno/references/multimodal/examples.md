# Multimodal — Complete Examples

## 1. Image Analysis with Tools

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

## 2. Image Generation with DALL-E

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.tools.dalle import DalleTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[DalleTools()],
)

agent.run("Generate an image of a sunset over mountains")
images = agent.get_images()
for image in images:
    print(image.url)
```

## 3. Gemini Native Image Generation

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
            PILImage.open(BytesIO(img.content)).show()
```

## 4. Audio Transcription (Gemini + Speaker ID)

```python
import requests
from agno.agent import Agent
from agno.media import Audio
from agno.models.google import Gemini

agent = Agent(model=Gemini(id="gemini-3-flash-preview"), markdown=True)

url = "https://agno-public.s3.us-east-1.amazonaws.com/demo_data/QA-01.mp3"
audio_content = requests.get(url).content

agent.print_response(
    "Give a transcript. Use speaker A, speaker B to identify speakers.",
    audio=[Audio(content=audio_content)],
    stream=True,
)
```

## 5. Audio I/O Agent (Listen + Speak)

```python
import requests
from agno.agent import Agent
from agno.media import Audio
from agno.models.openai import OpenAIChat
from agno.utils.audio import write_audio_to_file

url = "https://openaiassets.blob.core.windows.net/$web/API/docs/audio/alloy.wav"
wav_data = requests.get(url).content

agent = Agent(
    model=OpenAIChat(
        id="gpt-4o-audio-preview",
        modalities=["text", "audio"],
        audio={"voice": "sage", "format": "wav"},
    ),
    markdown=True,
)

response = agent.run("What's in this recording?", audio=[Audio(content=wav_data, format="wav")])

if response.response_audio:
    print(response.content)
    write_audio_to_file(response.response_audio.content, "tmp/result.wav")
```

## 6. Cross-Modal: Image → Text → Audio

Pipeline that analyzes an image, writes a story, then narrates it:

```python
from pathlib import Path
from agno.agent import Agent, RunOutput
from agno.media import Image
from agno.models.openai import OpenAIChat
from agno.utils.audio import write_audio_to_file

# Step 1: Image → Text
image_agent = Agent(model=OpenAIChat(id="gpt-4o"))
image_path = Path(__file__).parent / "sample.jpg"

image_story: RunOutput = image_agent.run(
    "Write a 3 sentence fiction story about the image",
    images=[Image(filepath=image_path)],
)

# Step 2: Text → Audio
audio_agent = Agent(
    model=OpenAIChat(
        id="gpt-4o-audio-preview",
        modalities=["text", "audio"],
        audio={"voice": "sage", "format": "wav"},
    ),
)

audio_story: RunOutput = audio_agent.run(
    f"Narrate the story with flair: {image_story.content}"
)

if audio_story.response_audio:
    write_audio_to_file(audio_story.response_audio.content, "tmp/sample_story.wav")
```

## 7. Video Analysis (Gemini)

```python
from agno.agent import Agent
from agno.media import Video
from agno.models.google import Gemini

agent = Agent(model=Gemini(id="gemini-2.0-flash-exp"), markdown=True)

agent.print_response(
    "Describe what happens in this video. Include timestamps.",
    videos=[Video(filepath="./clip.mp4")],
    stream=True,
)
```

## 8. PDF / File Input

```python
from agno.agent import Agent
from agno.media import File
from agno.models.anthropic import Claude

agent = Agent(model=Claude(id="claude-sonnet-4-5"), markdown=True)

# From URL
agent.print_response(
    "Summarize this document",
    files=[File(url="https://example.com/report.pdf")],
)

# From local file
agent.print_response(
    "What are the key points?",
    files=[File(filepath="./report.pdf")],
)
```

## 9. Multiple Media Types in One Request

```python
from agno.agent import Agent
from agno.media import Image, File
from agno.models.openai import OpenAIResponses

agent = Agent(model=OpenAIResponses(id="gpt-5.2"), markdown=True)

agent.print_response(
    "Compare the chart in the image with the data in the PDF",
    images=[Image(filepath="./chart.png")],
    files=[File(filepath="./data.pdf")],
)
```

## 10. Image Analysis in Tools (Auto-Injected)

Tools can receive images from user input via auto-injected parameters:

```python
from typing import Optional, List
from agno.media import Image
from agno.tools.function import ToolResult

def analyze_images(images: Optional[List[Image]] = None) -> ToolResult:
    """Analyze uploaded images."""
    if not images:
        return ToolResult(content="No images provided")
    return ToolResult(content=f"Received {len(images)} images for analysis")

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[analyze_images],
)
```

## Import Reference

```python
# Media classes
from agno.media import Image, Audio, Video, File

# Agent and response
from agno.agent import Agent, RunOutput

# Models
from agno.models.openai import OpenAIResponses, OpenAIChat
from agno.models.google import Gemini
from agno.models.anthropic import Claude

# Tools
from agno.tools.dalle import DalleTools

# Utilities
from agno.utils.audio import write_audio_to_file
```
