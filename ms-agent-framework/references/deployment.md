# Deployment — Hosting Agents in Production

## Table of Contents
1. [Deployment Options](#deployment-options)
2. [FastAPI Deployment](#fastapi-deployment)
3. [Azure Functions](#azure-functions)
4. [Azure Container Apps](#azure-container-apps)
5. [Azure AI Foundry Agent Service](#azure-ai-foundry-agent-service)
6. [Agent-to-Agent (A2A)](#agent-to-agent-a2a)
7. [Production Checklist](#production-checklist)

---

## Deployment Options

| Option | Best For | Complexity | Cost |
|--------|----------|:----------:|:----:|
| **FastAPI/Flask** | Simple APIs, quick deployment | Low | Low |
| **Azure Functions** | Event-driven, serverless | Medium | Pay-per-use |
| **Azure Container Apps** | Containerized, auto-scaling | Medium | Medium |
| **Azure Kubernetes (AKS)** | Complex orchestration, GPU | High | Variable |
| **Azure AI Foundry** | Managed agents, enterprise | Low | Medium-High |

---

## FastAPI Deployment

The simplest production deployment — wrap agents in a REST API.

### Basic API

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import DefaultAzureCredential
import os

app = FastAPI(title="Agent API")

# Initialize once at startup
client = AzureOpenAIResponsesClient(
    project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
    deployment_name=os.environ["AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME"],
    credential=DefaultAzureCredential(),
)

agent = client.as_agent(
    name="APIAgent",
    instructions="You are a helpful assistant.",
    tools=[...],
)

# Session store (use Redis in production)
sessions = {}

class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    session_id: str

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # Get or create session
    if request.user_id not in sessions:
        sessions[request.user_id] = await agent.create_session()

    session = sessions[request.user_id]

    try:
        result = await agent.run(request.message, session=session)
        return ChatResponse(response=result, session_id=session.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

### Streaming API

```python
from fastapi.responses import StreamingResponse

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    session = sessions.get(request.user_id, await agent.create_session())
    sessions[request.user_id] = session

    async def generate():
        async for chunk in agent.run(request.message, session=session, stream=True):
            if chunk.text:
                yield f"data: {chunk.text}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t agent-api .
docker run -p 8000:8000 \
    -e AZURE_AI_PROJECT_ENDPOINT=... \
    -e AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME=gpt-4o \
    agent-api
```

---

## Azure Functions

Serverless deployment for event-driven agents.

### HTTP Trigger

```python
import azure.functions as func
import json
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import DefaultAzureCredential

app = func.FunctionApp()

@app.route(route="chat", methods=["POST"])
async def chat(req: func.HttpRequest) -> func.HttpResponse:
    body = req.get_json()
    message = body.get("message")

    client = AzureOpenAIResponsesClient(
        project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
        deployment_name=os.environ["AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME"],
        credential=DefaultAzureCredential(),
    )

    agent = client.as_agent(
        name="FunctionAgent",
        instructions="You are a helpful assistant.",
    )

    result = await agent.run(message)

    return func.HttpResponse(
        json.dumps({"response": result}),
        mimetype="application/json",
    )
```

### Durable Functions (Long-Running Workflows)

```python
from agent_framework.durabletask import DurableWorkflow

class DocumentPipeline(DurableWorkflow):
    """Long-running document processing with checkpoints"""

    async def run(self, input_data):
        # Each step is automatically checkpointed
        extracted = await self.call_activity("extract_text", input_data)
        analyzed = await self.call_activity("analyze_content", extracted)
        report = await self.call_activity("generate_report", analyzed)

        # Human approval gate
        approved = await self.wait_for_external_event("approval")

        if approved:
            await self.call_activity("publish_report", report)

        return {"status": "completed" if approved else "cancelled"}
```

---

## Azure Container Apps

Containerized deployment with auto-scaling.

### Deploy

```bash
# Create container app
az containerapp create \
    --name agent-api \
    --resource-group my-rg \
    --environment my-env \
    --image my-registry.azurecr.io/agent-api:latest \
    --target-port 8000 \
    --env-vars \
        AZURE_AI_PROJECT_ENDPOINT=... \
        AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME=gpt-4o \
    --min-replicas 1 \
    --max-replicas 10 \
    --scale-rule-name http-rule \
    --scale-rule-type http \
    --scale-rule-http-concurrency 10
```

### Managed Identity

```bash
# Enable managed identity
az containerapp identity assign \
    --name agent-api \
    --resource-group my-rg \
    --system-assigned

# Grant access to Azure OpenAI
az role assignment create \
    --assignee <identity-principal-id> \
    --role "Cognitive Services OpenAI User" \
    --scope <openai-resource-id>
```

Then use `DefaultAzureCredential()` — no API keys needed.

---

## Azure AI Foundry Agent Service

Fully managed agent hosting with built-in observability.

### Key Features
- Server-side agent persistence (no local state management)
- Built-in MCP hosting
- Multi-agent workflows (private preview)
- Compliance and governance
- Model routing across catalog

### Create Managed Agent

```python
from agent_framework.azure import AzureAIAgentClient

client = AzureAIAgentClient(
    project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential(),
)

# Agent is created and persisted in Foundry
agent = client.as_agent(
    name="ManagedAgent",
    instructions="You are an enterprise assistant.",
    tools=[...],
    mcp_servers=["web-search"],
)

# Sessions automatically persist server-side
session = await agent.create_session()
result = await agent.run("Help me analyze Q4 results", session=session)
```

---

## Agent-to-Agent (A2A)

Host agents as services that other agents can call.

### Host an Agent

```python
from agent_framework.a2a import HostedAgent, AgentServer

# Create agent
booking_agent = client.as_agent(
    name="BookingService",
    instructions="You handle flight and hotel bookings.",
    tools=[book_flight, book_hotel],
)

# Host as A2A service
server = AgentServer(
    agent=booking_agent,
    port=8001,
)
await server.start()
```

### Call Hosted Agent

```python
from agent_framework.a2a import RemoteAgent

# Connect to remote agent
booking_service = RemoteAgent(
    endpoint="https://booking-service.azurewebsites.net",
)

# Use in another agent as a tool
coordinator = client.as_agent(
    name="TravelCoordinator",
    instructions="Coordinate travel planning using the booking service.",
    tools=[booking_service.as_tool()],
)
```

---

## Production Checklist

### Security
- [ ] Use managed identity (not API keys)
- [ ] Enable content filtering
- [ ] Implement input validation middleware
- [ ] Set up rate limiting
- [ ] Enable audit logging
- [ ] Review data flow for compliance

### Reliability
- [ ] Implement retry middleware with backoff
- [ ] Set up health checks
- [ ] Configure auto-scaling
- [ ] Implement circuit breakers for external tools
- [ ] Test failure scenarios

### Observability
- [ ] Enable OpenTelemetry tracing
- [ ] Configure Azure Monitor / Application Insights
- [ ] Set up alerting on error rates
- [ ] Track token usage and costs
- [ ] Log all tool calls

### Performance
- [ ] Use streaming for user-facing responses
- [ ] Implement response caching where appropriate
- [ ] Choose right model (mini for speed, full for quality)
- [ ] Use connection pooling for database tools
- [ ] Set reasonable timeouts

### Deployment
- [ ] Use staging environment before production
- [ ] Implement canary deployments (5-10% traffic)
- [ ] Pin framework version in requirements.txt
- [ ] Set up CI/CD pipeline
- [ ] Document rollback procedures

### Cost Management
- [ ] Monitor token usage per agent
- [ ] Set budget alerts
- [ ] Use model routing for cost optimization
- [ ] Cache repeated queries
- [ ] Implement token limits in middleware
