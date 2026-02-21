# Deployment — Hosting Agents in Production

## Deployment Options

| Option | Best For | Complexity |
|---|---|:-:|
| **FastAPI** | REST APIs, quick deployment | Low |
| **Azure Functions** | Serverless, event-driven | Medium |
| **Azure Container Apps** | Containerized, auto-scaling | Medium |
| **Azure AI Foundry** | Managed agents, enterprise | Low |
| **Agent-to-Agent (A2A)** | Microservice agents | Medium |

## Azure Functions (Recommended for Serverless)

### Step 1: Create Agent

```python
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import AzureCliCredential

def _create_agent():
    return AzureOpenAIChatClient(
        credential=AzureCliCredential()
    ).as_agent(
        name="Joker",
        instructions="You are good at telling jokes.",
    )
```

### Step 2: Register with AgentFunctionApp

```python
from agent_framework.azure import AgentFunctionApp

app = AgentFunctionApp(
    agents=[_create_agent()],
    enable_health_check=True,
    max_poll_retries=50,
)
```

### Step 3: Run Locally

```bash
func start
```

### Step 4: Invoke

```bash
curl -X POST http://localhost:7071/api/agents/Joker/run \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me a joke"}'
```

## FastAPI Deployment

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import DefaultAzureCredential

app = FastAPI()

client = AzureOpenAIResponsesClient(
    project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
    deployment_name=os.environ["AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME"],
    credential=DefaultAzureCredential(),
)
agent = client.as_agent(name="API", instructions="You are helpful.")
sessions = {}

class ChatRequest(BaseModel):
    user_id: str
    message: str

@app.post("/chat")
async def chat(req: ChatRequest):
    if req.user_id not in sessions:
        sessions[req.user_id] = agent.create_session()
    result = await agent.run(req.message, session=sessions[req.user_id])
    return {"response": result.text}

@app.post("/chat/stream")
async def stream(req: ChatRequest):
    if req.user_id not in sessions:
        sessions[req.user_id] = agent.create_session()

    async def generate():
        async for chunk in agent.run(req.message, session=sessions[req.user_id], stream=True):
            if chunk.text:
                yield f"data: {chunk.text}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

## Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Agent-to-Agent (A2A)

Host agents as callable services:

```python
from agent_framework.a2a import AgentServer, RemoteAgent

# Host an agent
server = AgentServer(agent=booking_agent, port=8001)
await server.start()

# Call from another agent
remote = RemoteAgent(endpoint="https://booking.azurewebsites.net")
coordinator = client.as_agent(
    name="Coordinator",
    tools=[remote.as_tool()],
)
```

## Production Checklist

### Security
- [ ] Use `DefaultAzureCredential` (managed identity) — no API keys
- [ ] Enable content filtering
- [ ] Validate all inputs via middleware
- [ ] Set up rate limiting

### Reliability
- [ ] Retry middleware with exponential backoff
- [ ] Health check endpoints
- [ ] Auto-scaling configured
- [ ] Graceful error handling

### Observability
- [ ] OpenTelemetry tracing enabled
- [ ] Azure Monitor / Application Insights
- [ ] Token usage tracking
- [ ] All tool calls logged

### Cost
- [ ] Monitor token usage per agent
- [ ] Budget alerts configured
- [ ] Use appropriate model (mini for speed)
- [ ] Cache repeated queries
