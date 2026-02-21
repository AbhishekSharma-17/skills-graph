# Agno Input / Output

Agno agents accept multiple input formats (strings, dicts, Pydantic models, message lists, multimodal media) and can produce text, structured Pydantic objects, audio, or streamed events.

## Sub-References

| Sub-Reference | File | Read When |
|---------------|------|-----------|
| **Structured I/O** | `input-output/structured-io.md` | Input formats (string, dict, Pydantic, messages), structured input validation, structured output (Pydantic), output model refinement, parser model, expected output, classification/extraction patterns |
| **Multimodal** | `input-output/multimodal.md` | Image/audio/video/file input, audio output, image generation (DALL-E), media classes (Image, Audio, Video, File), multimodal compatibility matrix |
| **Streaming & Reference** | `input-output/streaming-reference.md` | Sync/async streaming, stream events, agent I/O parameters reference table, run() signature, RunOutput object, teams structured I/O, full multimodal+structured example |

## Quick Start

```python
from pydantic import BaseModel
from agno.agent import Agent
from agno.models.openai import OpenAIResponses

class MovieScript(BaseModel):
    setting: str
    genre: str
    storyline: str

agent = Agent(model=OpenAIResponses(id="gpt-4o"), output_schema=MovieScript)
response = agent.run("Write a movie script about a heist in Tokyo")
print(response.content.setting)  # "Tokyo, Japan"
```
