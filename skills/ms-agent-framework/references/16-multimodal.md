# Multimodal Agents — Vision, Images, Data Content

## Content Types

The framework uses a unified `Content` class with factory methods:

| Factory Method | Creates | Use For |
|---|---|---|
| `Content.from_text("...")` | Text content | Regular text messages |
| `Content.from_data(data, media_type)` | Data content | Images, files, binary data |
| `Content.from_uri(uri)` | URI content | External resources by URL |

### All Content Types

| Type | Class | Description |
|---|---|---|
| Text | `TextContent` | Plain text |
| Data | `DataContent` | Binary data (images, files) with media type |
| URI | `URIContent` | External resource reference |
| FunctionCall | `FunctionCallContent` | LLM requesting a tool call |
| FunctionResult | `FunctionResultContent` | Tool call result |
| Error | `ErrorContent` | Error information |
| Usage | `UsageContent` | Token usage data |

## Sending Images to an Agent

### From Bytes

```python
from agent_framework import Message, Content

# Read image file
with open("photo.png", "rb") as f:
    image_data = f.read()

# Create multimodal message
message = Message(
    role="user",
    contents=[
        Content.from_text("What do you see in this image?"),
        Content.from_data(data=image_data, media_type="image/png"),
    ],
)

# Send to agent (use messages parameter)
response = await agent.run(messages=[message])
print(response.text)
```

### From URL

```python
message = Message(
    role="user",
    contents=[
        Content.from_text("Describe this image:"),
        Content.from_uri("https://example.com/photo.jpg"),
    ],
)

response = await agent.run(messages=[message])
```

### Supported Media Types

| Media Type | Extension |
|---|---|
| `image/png` | .png |
| `image/jpeg` | .jpg, .jpeg |
| `image/gif` | .gif |
| `image/webp` | .webp |

## Reading Response Content

```python
response = await agent.run("Analyze this data")

for message in response.messages:
    for content in message.contents:
        if content.type == "text":
            print(f"Text: {content.text}")
        elif content.type == "data":
            print(f"Data URI: {content.uri}")
            print(f"Media type: {content.media_type}")
        elif content.type == "uri":
            print(f"External URI: {content.uri}")
```

## Vision Agent Example

```python
import asyncio, os
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity.aio import AzureCliCredential
from agent_framework import Message, Content

async def main():
    client = AzureOpenAIResponsesClient(
        project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
        deployment_name="gpt-4o",  # Must be a vision-capable model
        credential=AzureCliCredential(),
    )

    agent = client.as_agent(
        name="VisionAgent",
        instructions="""You are an image analysis assistant.
        Describe images in detail, noting objects, colors, text, and composition.""",
    )

    # Analyze a local image
    with open("screenshot.png", "rb") as f:
        image_bytes = f.read()

    message = Message(
        role="user",
        contents=[
            Content.from_text("What's in this screenshot?"),
            Content.from_data(data=image_bytes, media_type="image/png"),
        ],
    )

    response = await agent.run(messages=[message])
    print(response.text)

asyncio.run(main())
```

## Multiple Images

```python
message = Message(
    role="user",
    contents=[
        Content.from_text("Compare these two images:"),
        Content.from_data(data=image1_bytes, media_type="image/png"),
        Content.from_data(data=image2_bytes, media_type="image/png"),
    ],
)
```

## Background Responses

Some providers support background (asynchronous) processing for long-running tasks:

| Provider | Background Support |
|---|:-:|
| Azure OpenAI Responses | ✅ |
| OpenAI Responses | ✅ |
| Azure AI Foundry | ✅ |
| Anthropic | ❌ |
| Ollama | ❌ |

## Provider Support for Vision

| Provider | Vision/Images |
|---|:-:|
| Azure OpenAI (gpt-4o, gpt-4o-mini) | ✅ |
| OpenAI (gpt-4o, gpt-4o-mini) | ✅ |
| Azure AI Foundry | ✅ |
| Anthropic Claude | ✅ |
| Ollama (llava, etc.) | ✅ (model-dependent) |
| GitHub Copilot | ❌ |

**Note:** The model must support vision. Use `gpt-4o`, `gpt-4o-mini`, Claude 3+, or Ollama vision models.
