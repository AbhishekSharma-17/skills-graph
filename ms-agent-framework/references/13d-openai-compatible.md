# OpenAI-Compatible Endpoints — Standard API Exposure

## Overview

**What:** Expose Agent Framework agents as OpenAI-compatible API endpoints that work with any OpenAI SDK client.

**Why:** Maximum compatibility with existing OpenAI libraries, tools, and workflows. Enables seamless integration with Ollama, LM Studio, vLLM, Azure AI Foundry, and any system expecting `/v1/chat/completions` or `/v1/responses` endpoints.

**Two protocols:**
1. **Chat Completions API** — Stateless per-request interface
2. **Responses API** — Stateful conversation management

---

## Chat Completions API

Standard OpenAI `/v1/chat/completions` endpoint format. Widely supported by clients and SDKs.

### Endpoint
```
POST /v1/chat/completions
```

### Request Format

```json
{
  "model": "gpt-4o-mini",
  "messages": [
    {
      "role": "user",
      "content": "What is the weather in San Francisco?"
    }
  ],
  "stream": false,
  "temperature": 0.7,
  "max_tokens": 1024,
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get current weather",
        "parameters": {
          "type": "object",
          "properties": {
            "location": {
              "type": "string",
              "description": "City name"
            }
          },
          "required": ["location"]
        }
      }
    }
  ]
}
```

### Response Format (Non-Streaming)

```json
{
  "id": "chatcmpl-8j9x5k",
  "object": "chat.completion",
  "created": 1699564800,
  "model": "gpt-4o-mini",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "The weather in San Francisco is sunny with 72°F temperature."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 45,
    "completion_tokens": 18,
    "total_tokens": 63
  }
}
```

### Streaming Response Format

Streaming uses Server-Sent Events (SSE) with `stream: true`:

```
data: {"id":"chatcmpl-8j9x5k","object":"chat.completion.chunk","created":1699564800,"model":"gpt-4o-mini","choices":[{"index":0,"delta":{"role":"assistant","content":"The"},"finish_reason":null}]}

data: {"id":"chatcmpl-8j9x5k","object":"chat.completion.chunk","created":1699564800,"model":"gpt-4o-mini","choices":[{"index":0,"delta":{"content":" weather"},"finish_reason":null}]}

data: {"id":"chatcmpl-8j9x5k","object":"chat.completion.chunk","created":1699564800,"model":"gpt-4o-mini","choices":[{"index":0,"delta":{"content":" in"},"finish_reason":null}]}

data: [DONE]
```

### Complete cURL Example

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-your-api-key" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful assistant."
      },
      {
        "role": "user",
        "content": "What is 2+2?"
      }
    ],
    "temperature": 0.7,
    "max_tokens": 100,
    "stream": false
  }'
```

### Request Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | string | required | Model identifier (e.g., "gpt-4o-mini") |
| `messages` | array | required | List of message objects with "role" and "content" |
| `stream` | boolean | false | Enable streaming responses |
| `temperature` | number | 0.7 | Sampling temperature (0.0-2.0) |
| `max_tokens` | integer | - | Maximum tokens in response |
| `top_p` | number | 1.0 | Nucleus sampling threshold (0.0-1.0) |
| `top_k` | integer | - | Top-k sampling parameter |
| `frequency_penalty` | number | 0.0 | Penalty for token frequency (-2.0 to 2.0) |
| `presence_penalty` | number | 0.0 | Penalty for token presence (-2.0 to 2.0) |
| `stop` | array | - | Stop sequences to terminate generation |
| `tools` | array | - | Tool definitions for function calling |
| `tool_choice` | string | "auto" | Tool selection strategy |

---

## Responses API

Stateful conversation management with explicit conversation IDs.

### Create Conversation

```
POST /v1/conversations
```

Request:
```json
{
  "system_prompt": "You are a helpful assistant.",
  "metadata": {
    "user_id": "user123",
    "session": "prod"
  }
}
```

Response:
```json
{
  "id": "conv-abc123xyz",
  "created_at": "2024-01-15T10:30:00Z",
  "status": "active"
}
```

### Send Message

```
POST /v1/conversations/{conversation_id}/messages
```

Request:
```json
{
  "role": "user",
  "content": "What is the weather in San Francisco?",
  "stream": false,
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get current weather for a location",
        "parameters": {
          "type": "object",
          "properties": {
            "location": {
              "type": "string"
            }
          },
          "required": ["location"]
        }
      }
    }
  ]
}
```

Response:
```json
{
  "id": "msg-xyz789",
  "conversation_id": "conv-abc123xyz",
  "role": "assistant",
  "content": "The weather in San Francisco is sunny with 72°F.",
  "created_at": "2024-01-15T10:31:00Z",
  "stop_reason": "end_turn",
  "usage": {
    "input_tokens": 42,
    "output_tokens": 15
  }
}
```

### Get Conversation History

```
GET /v1/conversations/{conversation_id}/messages
```

Response:
```json
{
  "messages": [
    {
      "id": "msg-abc123",
      "role": "user",
      "content": "What is the weather in San Francisco?",
      "created_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": "msg-xyz789",
      "role": "assistant",
      "content": "The weather in San Francisco is sunny with 72°F.",
      "created_at": "2024-01-15T10:31:00Z"
    }
  ],
  "conversation_id": "conv-abc123xyz"
}
```

### Delete Conversation

```
DELETE /v1/conversations/{conversation_id}
```

---

## Consuming from Python Client

### Chat Completions Client

For stateless, per-request interactions with Ollama, LM Studio, vLLM, or any `/v1/chat/completions` endpoint:

```python
from agent_framework.openai import OpenAIChatClient
from agent_framework import Tool

# Define tools
weather_tool = Tool(
    name="get_weather",
    description="Get current weather for a location",
    parameters={
        "location": {"type": "string", "description": "City name"}
    }
)

# Create client
client = OpenAIChatClient(
    base_url="http://localhost:11434/v1/",
    api_key="not-needed",
    model_id="llama3.2"
)

# Create agent
agent = client.as_agent(
    name="WeatherBot",
    instructions="You are a helpful weather assistant.",
    tools=[weather_tool]
)

# Simple non-streaming
response = agent.complete(
    messages=[
        {"role": "user", "content": "What's the weather in Paris?"}
    ],
    temperature=0.7
)
print(response.content)

# Streaming response
for chunk in agent.stream(
    messages=[
        {"role": "user", "content": "Explain climate change in detail."}
    ],
    max_tokens=500
):
    print(chunk.content, end="", flush=True)
```

### Responses Client

For stateful conversations with hosted .NET agents or OpenAI:

```python
from agent_framework.openai import OpenAIResponsesClient

# Create client
client = OpenAIResponsesClient(
    base_url="https://your-agent.openai.azure.com/",
    api_key="your-api-key",
    model_id="gpt-4o-mini"
)

# Create agent
agent = client.as_agent(
    name="ContextAwareBot",
    instructions="You are a helpful assistant with conversation memory."
)

# Create conversation
conversation = agent.create_conversation(
    system_prompt="You are a helpful customer service agent."
)

# Send messages (conversation state maintained)
response1 = agent.send_message(
    conversation_id=conversation.id,
    content="My name is Alice and I have an issue with my account."
)
print(response1.content)

# Agent remembers context
response2 = agent.send_message(
    conversation_id=conversation.id,
    content="Can you help me reset my password?"
)
# Agent responds with awareness of previous message

# Stream in conversation context
for chunk in agent.stream_message(
    conversation_id=conversation.id,
    content="Tell me about my account history."
):
    print(chunk.content, end="", flush=True)

# Retrieve conversation history
history = agent.get_history(conversation_id=conversation.id)
for msg in history.messages:
    print(f"{msg.role}: {msg.content}")

# Clean up
agent.delete_conversation(conversation_id=conversation.id)
```

### Handling Tool Calls

```python
from agent_framework.openai import OpenAIChatClient

client = OpenAIChatClient(
    base_url="http://localhost:11434/v1/",
    api_key="not-needed",
    model_id="llama3.2"
)

# Tools with implementation
weather_tool = Tool(
    name="get_weather",
    description="Get current weather",
    parameters={"location": {"type": "string"}},
    handler=lambda location: f"Sunny, 72°F in {location}"
)

agent = client.as_agent(
    name="Assistant",
    instructions="Help with weather queries.",
    tools=[weather_tool]
)

# Automatic tool invocation and continuation
response = agent.complete_with_tool_calls(
    messages=[
        {"role": "user", "content": "What's the weather in NYC?"}
    ]
)
# Agent automatically calls tool and includes result in response
print(response.content)
```

---

## Compatible Servers Table

| Server | Base URL Example | Protocol | Auth | Notes |
|--------|------------------|----------|------|-------|
| **Ollama** | `http://localhost:11434/v1/` | Chat Completions | Optional | Local inference, multiple model support |
| **LM Studio** | `http://localhost:1234/v1/` | Chat Completions | Optional | GUI-based local inference |
| **vLLM** | `http://localhost:8000/v1/` | Chat Completions | Optional | High-throughput inference engine |
| **Azure OpenAI** | `https://{resource}.openai.azure.com/v1/` | Both | API Key | Enterprise Azure deployment |
| **OpenAI** | `https://api.openai.com/v1/` | Both | API Key | Official OpenAI API |
| **Azure AI Foundry** | `https://{resource}.openai.azure.com/` | Both | Managed Identity | Serverless inference |
| **Hosted .NET Agent** | `https://your-agent.example.com/v1/` | Both | Bearer Token | Agent Framework hosting |
| **Hugging Face** | `https://api-inference.huggingface.co/models/` | Chat Completions | API Token | Model hub integration |

---

## Hosting Agents as OpenAI-Compatible Endpoints

### FastAPI Wrapper Pattern

Expose your Agent Framework agents as a `/v1/chat/completions` compatible server:

```python
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import json
from agent_framework import Agent, Tool

app = FastAPI(title="Agent Framework OpenAI Endpoint")

# Your agent definition
agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant.",
    tools=[
        Tool(
            name="calculate",
            description="Perform arithmetic calculation",
            parameters={"expression": {"type": "string"}},
            handler=lambda expression: str(eval(expression))
        )
    ]
)

# Request models matching OpenAI schema
class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False
    tools: Optional[List[dict]] = None

class Choice(BaseModel):
    index: int
    message: Message
    finish_reason: str

class ChatCompletionResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[Choice]
    usage: dict

# Non-streaming endpoint
@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    try:
        # Convert to agent format
        messages = [
            {"role": m.role, "content": m.content}
            for m in request.messages
        ]

        # Get response from agent
        response = agent.complete(
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )

        # Return OpenAI format
        return ChatCompletionResponse(
            id="chatcmpl-" + str(hash(str(messages)))[:16],
            object="chat.completion",
            created=int(__import__('time').time()),
            model=request.model,
            choices=[
                Choice(
                    index=0,
                    message=Message(role="assistant", content=response.content),
                    finish_reason="stop"
                )
            ],
            usage={
                "prompt_tokens": response.input_tokens or 0,
                "completion_tokens": response.output_tokens or 0,
                "total_tokens": (response.input_tokens or 0) + (response.output_tokens or 0)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Streaming endpoint
@app.post("/v1/chat/completions")
async def chat_completions_stream(request: ChatCompletionRequest):
    if not request.stream:
        return await chat_completions(request)

    async def generate():
        try:
            messages = [
                {"role": m.role, "content": m.content}
                for m in request.messages
            ]

            for chunk in agent.stream(
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            ):
                chunk_data = {
                    "id": "chatcmpl-stream",
                    "object": "chat.completion.chunk",
                    "created": int(__import__('time').time()),
                    "model": request.model,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"content": chunk.content},
                            "finish_reason": None
                        }
                    ]
                }
                yield f"data: {json.dumps(chunk_data)}\n\n"

            # Send [DONE] marker
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Running the Server

```bash
# Install dependencies
pip install fastapi uvicorn agent-framework

# Run server
python server.py

# Test with curl
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "local-agent",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": false
  }'

# Test with Python OpenAI client
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1/",
    api_key="not-needed"
)

response = client.chat.completions.create(
    model="local-agent",
    messages=[{"role": "user", "content": "Hello"}]
)
print(response.choices[0].message.content)
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY agent_server.py .
COPY agents/ ./agents/

EXPOSE 8000

CMD ["python", "agent_server.py"]
```

```bash
docker build -t agent-openai-endpoint .
docker run -p 8000:8000 agent-openai-endpoint
```

---

## When to Use Each Protocol

### Use Chat Completions API When:
- Per-request, stateless interactions
- Integrating with existing OpenAI SDK clients
- Running local inference (Ollama, vLLM)
- Simplicity is priority
- No persistent conversation state needed

### Use Responses API When:
- Multi-turn conversations with state
- Conversation history is important
- Separate conversation management needed
- Azure OpenAI or hosted agents
- Complex workflow with conversation lifecycle

### vs A2A Protocol:
- **OpenAI-Compatible:** Industry standard, broad client support
- **A2A:** Direct Agent Framework protocol, full feature access

### vs AG-UI Protocol:
- **OpenAI-Compatible:** API-first, programmatic consumption
- **AG-UI:** Web/dashboard UI, interactive testing

### vs Direct SDK Calls:
- **OpenAI-Compatible:** Language agnostic, HTTP-based
- **Direct SDK:** Full Agent Framework features, Python/C# only

---

## Security Considerations

- Always use HTTPS in production
- Implement API key validation
- Use managed identity for Azure endpoints
- Rate limit endpoints appropriately
- Log all API requests for audit trails
- Validate tool definitions before exposure
- Sanitize error messages in responses
- Use CORS appropriately for web clients
