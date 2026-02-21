# Azure Functions — Serverless Agent Hosting

## Overview

Azure Functions provides a serverless compute platform ideal for hosting Microsoft Agent Framework agents. It offers:

- **Serverless Compute**: No server management required; Azure handles infrastructure, patching, and scaling
- **Auto-Scaling**: Automatic scaling based on demand; pay only for execution time (consumption-based pricing)
- **Multi-Language Support**: Python, Node.js, C#, Java, PowerShell, and more
- **Integrated Monitoring**: Built-in Application Insights integration for logging, tracing, and diagnostics
- **Durable Functions**: Stateful orchestration for complex multi-agent workflows
- **Trigger Flexibility**: HTTP, Event Hubs, Service Bus, Timer, Queue, and Blob triggers
- **Security**: Managed identity integration, RBAC, VNet support

### When to Use Azure Functions for Agents

**Azure Functions is ideal for:**
- Short-lived agent tasks (< 30 minutes duration)
- Unpredictable or bursty workloads
- Cost-sensitive deployments with infrequent usage
- Multi-step agent workflows requiring orchestration
- Event-driven agent activation
- Rapid prototyping and development

**Consider other options when:**
- Agents require persistent long-running processes
- Consistent high-volume throughput needed (consider Container Instances, App Service, or AKS)
- Agents need local state and caching between invocations
- Sub-100ms response latency is critical

---

## AgentFunctionApp Class

The `AgentFunctionApp` class is the primary interface for hosting agents in Azure Functions.

### Initialization

```python
from agent_framework.azure import AgentFunctionApp
from agent_framework.core import Agent

# Create your agents first
agent = Agent(
    name="customer_service_agent",
    instructions="You are a helpful customer service representative.",
    tools=[support_tool, lookup_tool]
)

# Initialize the function app
app = AgentFunctionApp(
    agents=[agent],                    # List of Agent instances
    enable_health_check=True,          # Enable /health endpoint (default: True)
    max_poll_retries=50,               # Max retries for polling long-running responses (default: 50)
    poll_interval=1.0,                 # Seconds between polls (default: 1.0)
    max_execution_time=3600,           # Max execution time in seconds (default: 3600)
    cors_origins=["*"],                # CORS allowed origins (default: ["*"])
    enable_streaming=True,             # Enable streaming responses (default: False)
    request_timeout=300,               # HTTP request timeout in seconds (default: 300)
    log_level="INFO",                  # Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
    enable_metrics=True,               # Enable Azure Monitor metrics (default: True)
    custom_decorators=None,            # List of custom function decorators (default: None)
)
```

### Key Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `agents` | List[Agent] | Required | List of Agent instances to host |
| `enable_health_check` | bool | True | Enable health check endpoint at `/health` |
| `max_poll_retries` | int | 50 | Maximum retry attempts for polling background tasks |
| `poll_interval` | float | 1.0 | Seconds between consecutive poll attempts |
| `max_execution_time` | int | 3600 | Maximum execution time per invocation in seconds |
| `cors_origins` | List[str] | ["*"] | CORS allowed origin domains |
| `enable_streaming` | bool | False | Enable SSE streaming for compatible clients |
| `request_timeout` | int | 300 | HTTP request timeout in seconds |
| `log_level` | str | "INFO" | Python logging level |
| `enable_metrics` | bool | True | Enable Application Insights metrics collection |
| `custom_decorators` | List[Callable] | None | Additional function decorators to apply |

---

## HTTP Endpoints (Auto-Generated)

AgentFunctionApp automatically generates REST endpoints for each agent. All endpoints follow RESTful conventions.

### Main Agent Invocation Endpoint

**Endpoint**: `POST /api/agents/{agent_name}/run`

**Description**: Invokes the agent with a user message and returns a response.

**URL Parameters**:
- `{agent_name}`: Name of the agent (from `agent.name`)

**Query Parameters**:
- `thread_id` (optional): Unique identifier for multi-turn conversation thread. If omitted, a new thread is created.
- `stream` (optional): Boolean (`true`/`false`). Enable streaming response (requires `enable_streaming=True`).
- `timeout` (optional): Integer. Override default request timeout in seconds.

**Request Body** (JSON):
```json
{
  "message": "What are your operating hours?",
  "metadata": {
    "user_id": "user_123",
    "session_id": "session_456",
    "client_version": "1.0"
  }
}
```

**Response Headers**:
- `x-ms-thread-id`: Thread ID for this conversation (returned in all responses)
- `x-ms-execution-time-ms`: Execution duration in milliseconds
- `x-ms-agent-version`: Agent version (if versioning enabled)
- `Content-Type`: `application/json` or `text/event-stream` (if streaming)

**Successful Response** (200 OK):
```json
{
  "thread_id": "thread_7a8f9e2b-1c3d-4e5f-9g8h-7i6j5k4l3m2n",
  "agent_name": "customer_service_agent",
  "response": "Our business hours are Monday-Friday, 9 AM - 6 PM EST.",
  "tool_calls": [
    {
      "tool_name": "business_hours_lookup",
      "status": "completed",
      "result": "9 AM - 6 PM EST"
    }
  ],
  "finish_reason": "end_turn",
  "execution_time_ms": 2847
}
```

**Error Response** (4xx/5xx):
```json
{
  "error": "Agent invocation failed",
  "error_code": "AGENT_EXECUTION_ERROR",
  "message": "Tool 'database_lookup' timed out after 30 seconds",
  "thread_id": "thread_7a8f9e2b-1c3d-4e5f-9g8h-7i6j5k4l3m2n",
  "request_id": "0HN4K6V8J0W2X:00000001"
}
```

### Health Check Endpoint

**Endpoint**: `GET /health`

**Description**: Returns service health status. Useful for load balancers and monitoring.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2024-02-16T10:30:45.123Z",
  "agents": [
    {
      "name": "customer_service_agent",
      "status": "ready",
      "model": "gpt-4",
      "version": "1.0.0"
    }
  ],
  "uptime_seconds": 3847,
  "azure_storage_connected": true,
  "application_insights_connected": true
}
```

### Thread Status Endpoint

**Endpoint**: `GET /api/agents/{agent_name}/threads/{thread_id}`

**Description**: Retrieves the status and history of a specific thread.

**Response** (200 OK):
```json
{
  "thread_id": "thread_7a8f9e2b-1c3d-4e5f-9g8h-7i6j5k4l3m2n",
  "agent_name": "customer_service_agent",
  "created_at": "2024-02-16T09:15:30.000Z",
  "last_message_at": "2024-02-16T10:30:45.123Z",
  "message_count": 12,
  "status": "active",
  "messages": [
    {
      "role": "user",
      "content": "What are your operating hours?",
      "timestamp": "2024-02-16T10:30:10.000Z"
    },
    {
      "role": "assistant",
      "content": "Our business hours are Monday-Friday, 9 AM - 6 PM EST.",
      "timestamp": "2024-02-16T10:30:45.123Z",
      "tool_calls": [...]
    }
  ]
}
```

### List Threads Endpoint

**Endpoint**: `GET /api/agents/{agent_name}/threads`

**Description**: Lists all active threads for an agent (paginated).

**Query Parameters**:
- `limit` (optional): Number of results (default: 50, max: 1000)
- `offset` (optional): Pagination offset (default: 0)
- `status` (optional): Filter by status: `active`, `completed`, `archived`

**Response** (200 OK):
```json
{
  "agent_name": "customer_service_agent",
  "total_count": 347,
  "limit": 50,
  "offset": 0,
  "threads": [
    {
      "thread_id": "thread_7a8f9e2b-1c3d-4e5f-9g8h-7i6j5k4l3m2n",
      "created_at": "2024-02-16T09:15:30.000Z",
      "last_message_at": "2024-02-16T10:30:45.123Z",
      "message_count": 12,
      "status": "active"
    }
  ]
}
```

---

## Stateful Agent Threads

Threads enable multi-turn conversations and maintain context across multiple function invocations. Each thread has its own message history and state.

### Thread Concepts

**Thread ID**: Unique identifier (UUID v4 format) for a conversation session
```
thread_7a8f9e2b-1c3d-4e5f-9g8h-7i6j5k4l3m2n
```

**Thread State**: Persisted in Azure Table Storage or Cosmos DB
- Message history (user and assistant messages)
- Tool invocation results
- Metadata (created_at, last_message_at, user_id, etc.)
- Custom context variables

### Creating a New Thread

When no `thread_id` is provided, Azure Functions automatically creates a new thread:

```bash
curl -X POST "http://localhost:7071/api/agents/customer_service_agent/run" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, can you help me with my account?"
  }'
```

Response includes new thread ID:
```json
{
  "thread_id": "thread_7a8f9e2b-1c3d-4e5f-9g8h-7i6j5k4l3m2n",
  "agent_name": "customer_service_agent",
  "response": "Hello! I'd be happy to help you with your account. What can I assist you with today?",
  "finish_reason": "end_turn"
}
```

### Continuing an Existing Thread

Pass the `thread_id` as a query parameter to continue a conversation:

```bash
curl -X POST "http://localhost:7071/api/agents/customer_service_agent/run?thread_id=thread_7a8f9e2b-1c3d-4e5f-9g8h-7i6j5k4l3m2n" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I need to reset my password"
  }'
```

The agent now has access to previous conversation history:
```json
{
  "thread_id": "thread_7a8f9e2b-1c3d-4e5f-9g8h-7i6j5k4l3m2n",
  "agent_name": "customer_service_agent",
  "response": "I can help you reset your password. For security purposes, I'll need to verify your identity first. Can you provide your account email?",
  "finish_reason": "end_turn"
}
```

### Thread Persistence Architecture

```python
# ThreadStore interface (implemented by AgentFunctionApp)
class ThreadStore:
    async def create_thread(self) -> str:
        """Create new thread ID"""

    async def get_thread(self, thread_id: str) -> Dict:
        """Retrieve thread state and message history"""

    async def append_message(
        self,
        thread_id: str,
        role: str,  # "user" or "assistant"
        content: str,
        metadata: Dict = None
    ) -> None:
        """Add message to thread"""

    async def update_thread_metadata(
        self,
        thread_id: str,
        metadata: Dict
    ) -> None:
        """Update custom thread metadata"""

    async def list_threads(
        self,
        agent_name: str,
        limit: int = 50,
        offset: int = 0,
        status: str = None
    ) -> List[Dict]:
        """List threads for an agent"""

    async def archive_thread(self, thread_id: str) -> None:
        """Archive a completed thread"""
```

### Thread Configuration

```python
# Configure thread persistence backend
app = AgentFunctionApp(
    agents=[agent],
    thread_store_config={
        "type": "azure_table",  # or "cosmos_db"
        "connection_string": "DefaultEndpointsProtocol=https;...",
        "table_name": "agent_threads",
        "ttl_days": 30,  # Auto-delete threads after 30 days
        "encryption_enabled": True,
    },
    thread_timeout_seconds=3600,  # Max active thread duration
)
```

### Practical Multi-Turn Example

```python
# Python client example
import requests
import json

agent_url = "http://localhost:7071/api/agents/customer_service_agent/run"

# Turn 1: New conversation
response = requests.post(
    agent_url,
    json={"message": "I want to upgrade my plan"}
)
thread_id = response.json()["thread_id"]
print(f"New thread: {thread_id}")

# Turn 2: Continue with existing thread
response = requests.post(
    f"{agent_url}?thread_id={thread_id}",
    json={"message": "What's included in the professional plan?"}
)
print(f"Agent response: {response.json()['response']}")

# Turn 3: Another turn in same conversation
response = requests.post(
    f"{agent_url}?thread_id={thread_id}",
    json={"message": "How much does it cost?"}
)
print(f"Agent response: {response.json()['response']}")

# Retrieve thread history
history_response = requests.get(
    f"http://localhost:7071/api/agents/customer_service_agent/threads/{thread_id}"
)
messages = history_response.json()["messages"]
print(f"Total turns: {len(messages)}")
```

---

## Durable Functions Orchestration

Durable Functions enable complex, stateful workflows orchestrating multiple agents and external services.

### Architecture Pattern: Worker-Client

**Client Function** (HTTP trigger): Accepts requests and starts orchestrations
**Orchestrator Function**: Defines workflow logic and coordinates activities
**Activity Functions**: Individual agent invocations and tool calls

### Sequential Orchestration

Chain multiple agents in sequence, passing results between them:

```python
import azure.functions as func
from azure.durable_functions import DurableOrchestrationClient, orchestrate, get_current_client

# Activity 1: Data extraction agent
@app.route("http_trigger_data_extraction", methods=["POST"])
async def activity_extract_data(context):
    return await app.agents["data_extraction_agent"].invoke(context["input"])

# Activity 2: Data validation agent
@app.route("http_trigger_validate_data", methods=["POST"])
async def activity_validate_data(context):
    extracted_data = context["extracted_data"]
    return await app.agents["data_validation_agent"].invoke({
        "message": f"Please validate this extracted data: {extracted_data}",
        "thread_id": context["thread_id"]
    })

# Activity 3: Data enrichment agent
@app.route("http_trigger_enrich_data", methods=["POST"])
async def activity_enrich_data(context):
    validated_data = context["validated_data"]
    return await app.agents["data_enrichment_agent"].invoke({
        "message": f"Enrich this data: {validated_data}",
        "thread_id": context["thread_id"]
    })

# Orchestrator function
@app.orchestration_trigger(input_name="input")
async def orchestrator(context):
    input_data = context.get_input()
    thread_id = input_data.get("thread_id") or str(uuid.uuid4())

    # Step 1: Extract data
    extraction_result = yield context.call_activity(
        "activity_extract_data",
        {
            "input": input_data["raw_text"],
            "thread_id": thread_id
        }
    )

    # Step 2: Validate extracted data
    validation_result = yield context.call_activity(
        "activity_validate_data",
        {
            "extracted_data": extraction_result["data"],
            "thread_id": thread_id
        }
    )

    # Step 3: Enrich validated data
    enrichment_result = yield context.call_activity(
        "activity_enrich_data",
        {
            "validated_data": validation_result["data"],
            "thread_id": thread_id
        }
    )

    return {
        "thread_id": thread_id,
        "raw_text": input_data["raw_text"],
        "extracted": extraction_result["data"],
        "validated": validation_result["data"],
        "enriched": enrichment_result["data"],
        "status": "completed"
    }

# Client HTTP trigger
@app.route("orchestrate_workflow", methods=["POST"])
async def start_orchestration(req: func.HttpRequest):
    client = DurableOrchestrationClient(req)

    data = req.get_json()
    instance_id = await client.start_new(
        "orchestrator",
        input_=data
    )

    return client.create_check_status_response(req, instance_id)
```

### Parallel Orchestration (Fan-Out/Fan-In)

Execute multiple agents concurrently and wait for all results:

```python
@app.orchestration_trigger(input_name="input")
async def parallel_orchestrator(context):
    input_data = context.get_input()
    thread_id = input_data.get("thread_id") or str(uuid.uuid4())

    # Define parallel tasks
    parallel_tasks = [
        # Sentiment analysis
        context.call_activity(
            "activity_sentiment_analysis",
            {
                "text": input_data["customer_feedback"],
                "thread_id": thread_id
            }
        ),
        # Entity extraction
        context.call_activity(
            "activity_extract_entities",
            {
                "text": input_data["customer_feedback"],
                "thread_id": thread_id
            }
        ),
        # Intent classification
        context.call_activity(
            "activity_classify_intent",
            {
                "text": input_data["customer_feedback"],
                "thread_id": thread_id
            }
        ),
    ]

    # Wait for all tasks to complete (fan-in)
    results = yield context.task_all(parallel_tasks)

    return {
        "thread_id": thread_id,
        "sentiment": results[0],
        "entities": results[1],
        "intent": results[2],
        "status": "completed"
    }
```

### Human-in-the-Loop with External Events

Orchestrator waits for external approval:

```python
@app.orchestration_trigger(input_name="input")
async def human_approval_orchestrator(context):
    input_data = context.get_input()

    # Step 1: Agent proposes action
    proposal = yield context.call_activity(
        "activity_propose_action",
        input_data
    )

    # Step 2: Wait for human approval (up to 1 hour timeout)
    approval_event = yield context.wait_for_external_event(
        "ApprovalReceived",
        timeout=timedelta(hours=1)
    )

    if approval_event is None:
        return {
            "status": "timeout",
            "proposal": proposal,
            "message": "Approval request timed out"
        }

    if not approval_event.get("approved"):
        return {
            "status": "rejected",
            "proposal": proposal,
            "rejection_reason": approval_event.get("reason")
        }

    # Step 3: Execute approved action
    result = yield context.call_activity(
        "activity_execute_action",
        proposal
    )

    return {
        "status": "completed",
        "proposal": proposal,
        "execution_result": result
    }

# Receive approval from external source (e.g., HTTP endpoint)
@app.route("approve_action", methods=["POST"])
async def approve_action(req: func.HttpRequest):
    client = DurableOrchestrationClient(req)
    instance_id = req.route_params.get("instanceId")

    data = req.get_json()

    await client.raise_event(
        instance_id,
        "ApprovalReceived",
        data={
            "approved": data.get("approved", False),
            "reason": data.get("reason", "")
        }
    )

    return func.HttpResponse("Event raised successfully")
```

### Timer Triggers for Scheduled Agents

Run agents on a schedule (e.g., daily reports, periodic checks):

```python
# Timer trigger runs on schedule (CRON syntax)
@app.timer_trigger(arg_name="myTimer", schedule="0 0 9 * * *")
async def scheduled_daily_report(myTimer: func.TimerRequest):
    """
    Runs daily at 9:00 AM UTC
    Schedule: "0 0 9 * * *" (CRON format)
    """

    if myTimer.is_past_due:
        logging.warning("Daily report is running behind schedule!")

    # Invoke reporting agent
    report = await app.agents["daily_report_agent"].invoke({
        "message": f"Generate daily report for {date.today()}"
    })

    # Store report
    table_client = app.get_table_client("daily_reports")
    await table_client.create_entity({
        "PartitionKey": str(date.today()),
        "RowKey": str(uuid.uuid4()),
        "report_content": report["response"],
        "timestamp": datetime.utcnow().isoformat()
    })

# More complex scheduled orchestration
@app.orchestration_trigger(input_name="input")
async def scheduled_sync_orchestrator(context):
    """Daily data synchronization orchestrator"""

    # Run multiple agents in parallel for different data sources
    tasks = [
        context.call_activity("sync_crm_data", {}),
        context.call_activity("sync_erp_data", {}),
        context.call_activity("sync_analytics_data", {}),
    ]

    results = yield context.task_all(tasks)

    # Generate summary report
    summary = yield context.call_activity(
        "generate_sync_summary",
        {"results": results}
    )

    return summary

@app.schedule_trigger(arg_name="mySchedule", schedule="0 0 0 * * *")
async def trigger_daily_sync(mySchedule: func.TimerRequest):
    """Trigger daily sync at midnight UTC"""

    client = DurableOrchestrationClient(None)
    await client.start_new("scheduled_sync_orchestrator", input_=None)
```

---

## Local Development Setup

### Prerequisites

```bash
# Install Azure Functions Core Tools
# macOS with Homebrew
brew tap azure/functions
brew install azure-functions-core-tools@4

# Linux (Ubuntu/Debian)
curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
sudo mv microsoft.gpg /etc/apt/trusted.gpg.d/microsoft.gpg
sudo sh -c 'echo "deb [arch=amd64,arm64] https://packages.microsoft.com/repos/azure-cli/ $(lsb_release -cs) main" > /etc/apt/sources.list.d/azure-cli.list'
sudo apt-get update
sudo apt-get install azure-functions-core-tools-4

# Windows (PowerShell)
choco install azure-functions-core-tools
```

### Docker Compose Setup (Recommended)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  azurite:
    image: mcr.microsoft.com/azure-storage/azurite:latest
    ports:
      - "10000:10000"  # Blob storage
      - "10001:10001"  # Queue storage
      - "10002:10002"  # Table storage
    environment:
      AZURITE_SILENT: "true"
      AZURITE_LOCATION: "/data"
    volumes:
      - azurite_data:/data

  durable-task-scheduler:
    image: mcr.microsoft.com/azure-functions/durable-task-scheduler:latest
    ports:
      - "7070:7070"
    environment:
      StorageAccount: "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUQtSyKbkFsz1UNEsPf2QQ==;BlobEndpoint=http://azurite:10000/devstoreaccount1;QueueEndpoint=http://azurite:10001/devstoreaccount1;TableEndpoint=http://azurite:10002/devstoreaccount1;"
    depends_on:
      - azurite

volumes:
  azurite_data:
```

Start the services:
```bash
docker-compose up -d
```

### Environment Configuration

Create `local.settings.json`:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUQtSyKbkFsz1UNEsPf2QQ==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;",
    "AZURE_OPENAI_ENDPOINT": "https://your-openai-instance.openai.azure.com/",
    "AZURE_OPENAI_API_KEY": "your-api-key",
    "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
    "AZURE_OPENAI_API_VERSION": "2024-08-01-preview",
    "AzureWebJobsDashboard": "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUQtSyKbkFsz1UNEsPf2QQ==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "FUNCTIONS_EXTENSION_VERSION": "~4",
    "ENABLE_INIT_FROM_CODE": "true",
    "AzureWebJobsFeatureFlags": "EnableWorkerTypeCheck"
  },
  "Host": {
    "LocalHttpPort": 7071,
    "CORS": {
      "AllowedOrigins": ["*"]
    }
  }
}
```

### Project Structure

```
azure-agent-function/
├── HttpTrigger/
│   ├── __init__.py
│   └── function_app.py
├── OrchestrationTrigger/
│   ├── __init__.py
│   └── function_app.py
├── ActivityTriggers/
│   ├── activity1/
│   │   ├── __init__.py
│   │   └── function_app.py
│   └── activity2/
│       ├── __init__.py
│       └── function_app.py
├── requirements.txt
├── local.settings.json
├── host.json
├── function_app.py
└── demo.http
```

### Starting the Local Runtime

```bash
# Install dependencies
pip install -r requirements.txt

# Start local Azure Functions runtime
func start

# Output:
# Azure Functions Core Tools
# Found Python Worker: /usr/local/Cellar/azure-functions-core-tools@4/4.0.5649/workers/python/3.9/bin/python3.9
#
# Azurite Blob Storage: http://127.0.0.1:10000
# Azurite Queue Storage: http://127.0.0.1:10001
# Azurite Table Storage: http://127.0.0.1:10002
#
# ...
#
# Listening on http://0.0.0.0:7071
# Application started. Press Ctrl+C to shut down.
```

### Testing with curl and demo.http

Create `demo.http`:

```http
### Variables
@baseUrl = http://localhost:7071
@agentName = customer_service_agent
@threadId = thread_7a8f9e2b-1c3d-4e5f-9g8h-7i6j5k4l3m2n

### Health Check
GET {{baseUrl}}/health

### Create New Thread
POST {{baseUrl}}/api/agents/{{agentName}}/run
Content-Type: application/json

{
  "message": "Hello, can you help me with my account?"
}

### Continue Existing Thread (save threadId from response above)
POST {{baseUrl}}/api/agents/{{agentName}}/run?thread_id={{threadId}}
Content-Type: application/json

{
  "message": "I need to reset my password"
}

### Get Thread Status
GET {{baseUrl}}/api/agents/{{agentName}}/threads/{{threadId}}

### List All Threads
GET {{baseUrl}}/api/agents/{{agentName}}/threads?limit=10

### Streaming Response
POST {{baseUrl}}/api/agents/{{agentName}}/run?stream=true
Content-Type: application/json

{
  "message": "Generate a detailed report on my account"
}

### Start Orchestration
POST {{baseUrl}}/api/orchestrate_workflow
Content-Type: application/json

{
  "raw_text": "Extract and validate customer information from: John Doe, john@example.com, Premium account"
}
```

Test with REST Client extension in VS Code or curl:

```bash
# Health check
curl http://localhost:7071/health

# Create new thread
curl -X POST "http://localhost:7071/api/agents/customer_service_agent/run" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, can you help me?"}'

# Continue thread
curl -X POST "http://localhost:7071/api/agents/customer_service_agent/run?thread_id=YOUR_THREAD_ID" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is your service level agreement?"}'

# Get thread history
curl "http://localhost:7071/api/agents/customer_service_agent/threads/YOUR_THREAD_ID"
```

---

## Deployment to Azure

### Prerequisites

```bash
# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Install Azure Developer CLI
curl -fsSL https://aka.ms/install-azd.sh | bash

# Login to Azure
az login
azd auth login
```

### Provision Infrastructure

Create `infra/main.bicep` (Bicep Infrastructure as Code):

```bicep
param location string = resourceGroup().location
param functionAppName string = 'agent-func-${uniqueString(resourceGroup().id)}'
param storageAccountName string = 'agentstor${uniqueString(resourceGroup().id)}'

// Storage Account
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  properties: {
    accessTier: 'Hot'
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
  }
}

// Application Insights
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${functionAppName}-insights'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    RetentionInDays: 30
  }
}

// App Service Plan (Flex Consumption)
resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: '${functionAppName}-plan'
  location: location
  sku: {
    name: 'FC1'
    tier: 'FlexConsumption'
  }
  properties: {}
}

// Function App
resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      appSettings: [
        {
          name: 'AzureWebJobsStorage'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=core.windows.net'
        }
        {
          name: 'WEBSITE_CONTENTAZUREFILECONNECTIONSTRING'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=core.windows.net'
        }
        {
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          value: appInsights.properties.InstrumentationKey
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsights.properties.ConnectionString
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'AZURE_OPENAI_ENDPOINT'
          value: 'https://your-openai-instance.openai.azure.com/'
        }
        {
          name: 'AZURE_OPENAI_DEPLOYMENT_NAME'
          value: 'gpt-4'
        }
      ]
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
    }
    httpsOnly: true
  }
}

output functionAppId string = functionApp.id
output functionAppName string = functionApp.name
output storageAccountId string = storageAccount.id
output appInsightsInstrumentationKey string = appInsights.properties.InstrumentationKey
```

Create `infra/azure.yaml`:

```yaml
metadata:
  template: Azure Agent Function Template
  description: Deploy Microsoft Agent Framework agents to Azure Functions

services:
  agents-function:
    project: .
    language: python
    module: function_app

variables:
  location: eastus
  functionAppName: agent-func-${RANDOM}
  environmentName: dev
```

Provision and deploy:

```bash
# Create new Azure resource group
az group create \
  --name agent-function-rg \
  --location eastus

# Provision infrastructure
azd provision --resource-group agent-function-rg

# Deploy application code
azd deploy
```

### Managed Identity Configuration

Enable managed identity for Azure OpenAI access:

```python
from azure.identity import ManagedIdentityCredential
from azure.openai import AzureOpenAI

# In function_app.py
managed_identity_credential = ManagedIdentityCredential()

client = AzureOpenAI(
    api_version="2024-08-01-preview",
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    azure_ad_token_provider=lambda: managed_identity_credential.get_token(
        "https://cognitiveservices.azure.com/.default"
    ).token,
)
```

Assign RBAC role:

```bash
# Get function app identity object ID
IDENTITY_ID=$(az functionapp identity show \
  --resource-group agent-function-rg \
  --name agent-func-XXXXX \
  --query principalId -o tsv)

# Assign Cognitive Services User role
az role assignment create \
  --role "Cognitive Services User" \
  --assignee-object-id $IDENTITY_ID \
  --scope /subscriptions/{subscriptionId}/resourceGroups/agent-function-rg/providers/Microsoft.CognitiveServices/accounts/your-openai-instance
```

### Plan Options

**Consumption Plan** (Pay-per-execution):
- $0.20 per 1M executions
- 180-second execution timeout
- Best for: Unpredictable, bursty workloads
- Pricing: Most cost-effective for low volume

**Flex Consumption Plan** (Newer, Recommended):
- Lower cold start latency
- Dynamic scaling
- Per-vCore-second billing
- Better for: Consistent baseline traffic with flexibility

**Premium Plan** (Dedicated):
- No cold starts (pre-warmed instances)
- Higher execution timeout (60 minutes)
- VNet integration
- Best for: Predictable, consistent high traffic

Configuration example for Flex Consumption:

```bicep
sku: {
  name: 'FC1'
  tier: 'FlexConsumption'
}
properties: {
  maximumInstances: 100
  minimumInstances: 1
  targetWorkerCount: 10
}
```

### Cold Start Mitigation

```python
# 1. Keep-alive timer to prevent scale-to-zero
@app.timer_trigger(arg_name="myTimer", schedule="0 */5 * * * *")
async def keepalive_trigger(myTimer: func.TimerRequest):
    """
    Runs every 5 minutes to keep function warm
    Schedule: "0 */5 * * * *" (CRON format)
    """
    logging.info("Keep-alive signal received")

# 2. Pre-warm common models
@app.function_app.on_startup()
async def startup(context):
    """Initialize models and connections at startup"""
    for agent in app.agents:
        # Pre-load model
        await agent._model.health_check()
        logging.info(f"Pre-loaded agent: {agent.name}")

# 3. Use function premium plan or keep-alive approach
# 4. Optimize package size (exclude unnecessary dependencies)
```

### Monitoring and Logging

```python
import logging
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace

# Configure Azure Monitor
configure_azure_monitor()
tracer = trace.get_tracer(__name__)

# Logging in functions
@app.route("log_example", methods=["POST"])
async def log_example(req: func.HttpRequest):
    logging.info("Processing request")

    with tracer.start_as_current_span("agent_invocation") as span:
        span.set_attribute("agent.name", agent.name)
        span.set_attribute("thread_id", thread_id)

        try:
            result = await agent.invoke(message)
            span.set_attribute("status", "success")
            logging.info(f"Agent invocation succeeded: {result}")
        except Exception as e:
            span.set_attribute("status", "error")
            logging.error(f"Agent invocation failed: {str(e)}", exc_info=True)
            raise
```

View logs in Azure Portal or via CLI:

```bash
# Stream logs in real-time
az functionapp logs tail \
  --resource-group agent-function-rg \
  --name agent-func-XXXXX \
  --provider Microsoft.Web/sites/slots

# Query Application Insights
az monitor app-insights query \
  --app agent-func-insights \
  --resource-group agent-function-rg \
  --query "SELECT COUNT(*) FROM requests WHERE success == false" \
  --interval PT5M
```

---

## Streaming Responses

Streaming enables real-time agent responses via Server-Sent Events (SSE).

### Enable Streaming in AgentFunctionApp

```python
app = AgentFunctionApp(
    agents=[agent],
    enable_streaming=True,
    stream_buffer_size=4096,  # Bytes per chunk
    stream_timeout=300,       # Seconds before timeout
)
```

### Streaming Endpoint

**Endpoint**: `POST /api/agents/{agent_name}/run?stream=true`

**Request Body**:
```json
{
  "message": "Generate a detailed analysis of customer satisfaction trends"
}
```

**Response**: Server-Sent Events (Content-Type: text/event-stream)

```
event: message_start
data: {"thread_id":"thread_...", "agent_name":"analysis_agent"}

event: content_delta
data: {"content":"The analysis reveals"}

event: content_delta
data: {"content":" several key trends in"}

event: content_delta
data: {"content":" customer satisfaction metrics."}

event: tool_call_start
data: {"tool_name":"fetch_metrics", "tool_id":"123"}

event: tool_call_result
data: {"tool_name":"fetch_metrics", "result":{"satisfaction_score":8.7}}

event: content_delta
data: {"content":" Customer satisfaction has increased to 8.7 out of 10."}

event: message_done
data: {"status":"completed", "finish_reason":"end_turn"}
```

### Client-Side Consumption

**Python Client**:
```python
import requests
import json

def stream_agent_response(message: str, agent_name: str = "analysis_agent"):
    """Stream agent response using SSE"""

    url = f"http://localhost:7071/api/agents/{agent_name}/run?stream=true"

    with requests.post(
        url,
        json={"message": message},
        stream=True
    ) as response:
        for line in response.iter_lines():
            if not line:
                continue

            if line.startswith(b"event: "):
                event_type = line[7:].decode('utf-8')
            elif line.startswith(b"data: "):
                data = json.loads(line[6:].decode('utf-8'))

                if event_type == "content_delta":
                    print(data["content"], end="", flush=True)
                elif event_type == "message_done":
                    print("\n[Agent finished]")
                elif event_type == "tool_call_result":
                    print(f"\n[Tool: {data['tool_name']}]")

stream_agent_response("Analyze customer feedback from Q1 2024")
```

**JavaScript Client**:
```javascript
async function streamAgentResponse(message, agentName = "analysis_agent") {
  const url = `http://localhost:7071/api/agents/${agentName}/run?stream=true`;

  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  let eventType = '';
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop();

    for (const line of lines) {
      if (line.startsWith('event: ')) {
        eventType = line.slice(7);
      } else if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));

        if (eventType === 'content_delta') {
          document.getElementById('response').appendChild(
            new Text(data.content)
          );
        }
      }
    }
  }
}

streamAgentResponse("What are the top 3 issues reported?");
```

---

## Scaling & Performance

### Auto-Scaling Configuration

```python
# Configure scaling behavior
app = AgentFunctionApp(
    agents=[agent],
    scaling_config={
        "enabled": True,
        "min_instances": 1,
        "max_instances": 100,
        "target_utilization": 0.7,  # Target 70% CPU
        "scale_up_threshold": 0.8,   # Scale up at 80%
        "scale_down_threshold": 0.3, # Scale down at 30%
    }
)
```

In Bicep for Flex Consumption:

```bicep
resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
  properties: {
    functionAppConfig: {
      runtime: 'python'
      runtimeVersion: '3.11'
      maximumInstances: 100
      minimumInstances: 1
      targetWorkerCount: 10
    }
  }
}
```

### Connection Pooling

```python
import asyncio
from aiohttp import TCPConnector, ClientSession

# Create reusable connection pool
connector = TCPConnector(
    limit=100,           # Max connections
    limit_per_host=30,   # Max per host
    ttl_dns_cache=300,   # DNS cache TTL
)
session = ClientSession(connector=connector)

# Use in agent tools
class APITool:
    def __init__(self, session: ClientSession):
        self.session = session

    async def call_api(self, url: str) -> str:
        async with self.session.get(url) as response:
            return await response.text()
```

Initialize at startup:

```python
@app.on_startup()
async def setup_connections():
    """Initialize connections at function startup"""
    connector = TCPConnector(limit=100, limit_per_host=30)
    app.http_session = ClientSession(connector=connector)

@app.on_shutdown()
async def cleanup_connections():
    """Close connections at shutdown"""
    if hasattr(app, 'http_session'):
        await app.http_session.close()
```

### Timeout Configuration

```python
app = AgentFunctionApp(
    agents=[agent],
    request_timeout=300,        # Total request timeout (seconds)
    tool_timeout=30,            # Per-tool timeout
    model_timeout=120,          # Model inference timeout
    polling_timeout=60,         # Long-polling timeout
)

# Override per-invocation
@app.route("agent_invoke_custom", methods=["POST"])
async def agent_invoke_with_timeout(req: func.HttpRequest):
    data = req.get_json()

    try:
        result = await asyncio.wait_for(
            agent.invoke(
                data["message"],
                thread_id=data.get("thread_id")
            ),
            timeout=data.get("timeout", 60)  # Custom timeout
        )
        return func.HttpResponse(json.dumps(result))
    except asyncio.TimeoutError:
        return func.HttpResponse(
            json.dumps({"error": "Agent invocation timed out"}),
            status_code=504
        )
```

### Cost Optimization

```python
# 1. Batch requests to reduce function invocations
@app.route("batch_invoke", methods=["POST"])
async def batch_invoke(req: func.HttpRequest):
    data = req.get_json()
    messages = data.get("messages", [])
    thread_id = data.get("thread_id")

    results = []
    for message in messages:
        result = await agent.invoke(message, thread_id=thread_id)
        results.append(result)

    return func.HttpResponse(json.dumps(results))

# 2. Use Durable Functions for long-running workflows
# (more efficient than polling)

# 3. Configure appropriate timeout to prevent long-running executions
app = AgentFunctionApp(
    agents=[agent],
    max_execution_time=300,  # Kill after 5 minutes
)

# 4. Monitor costs with Application Insights
# View cost analysis in Azure Portal → Cost Management
```

---

## Complete Working Example

Full end-to-end example with agent creation, function app setup, local testing, and deployment.

### Step 1: Create the Agent

File: `agents.py`

```python
from agent_framework.core import Agent, Tool
import json

# Define tools
class WeatherTool(Tool):
    name = "get_weather"
    description = "Get current weather for a location"

    def __init__(self):
        self.input_schema = {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name"
                }
            },
            "required": ["location"]
        }

    async def call(self, location: str) -> str:
        # Mock weather data
        weather_data = {
            "New York": "Cloudy, 62°F",
            "San Francisco": "Sunny, 58°F",
            "Seattle": "Rainy, 52°F",
        }
        return json.dumps(weather_data.get(location, "Location not found"))

class DatabaseLookupTool(Tool):
    name = "lookup_customer"
    description = "Look up customer information by ID"

    def __init__(self):
        self.input_schema = {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "Customer ID"
                }
            },
            "required": ["customer_id"]
        }

    async def call(self, customer_id: str) -> str:
        # Mock database
        customers = {
            "CUST001": {
                "name": "Alice Johnson",
                "email": "alice@example.com",
                "account_type": "Premium",
                "since": "2020-03-15"
            },
            "CUST002": {
                "name": "Bob Smith",
                "email": "bob@example.com",
                "account_type": "Standard",
                "since": "2021-06-20"
            }
        }
        customer = customers.get(customer_id)
        if customer:
            return json.dumps(customer)
        return json.dumps({"error": f"Customer {customer_id} not found"})

# Create agents
support_agent = Agent(
    name="customer_support",
    instructions="""You are a helpful customer support agent. You assist customers with
their inquiries about products, services, accounts, and general assistance.
Use the available tools to look up customer information and provide accurate answers.
Be empathetic, professional, and thorough in your responses.""",
    tools=[DatabaseLookupTool()],
    model="gpt-4",
)

weather_agent = Agent(
    name="weather_assistant",
    instructions="""You are a friendly weather assistant. Provide weather information
for requested locations. Be conversational and helpful.""",
    tools=[WeatherTool()],
    model="gpt-4",
)
```

### Step 2: Create Function App

File: `function_app.py`

```python
import azure.functions as func
import json
from agent_framework.azure import AgentFunctionApp
from agents import support_agent, weather_agent

# Initialize AgentFunctionApp
app_instance = AgentFunctionApp(
    agents=[support_agent, weather_agent],
    enable_health_check=True,
    enable_streaming=True,
    max_poll_retries=50,
    log_level="INFO",
    enable_metrics=True,
)

# Export for Azure Functions runtime
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# Register agent endpoints
# These are auto-generated by AgentFunctionApp but can be customized
@app.route("agents/{agent_name}/run", methods=["POST"])
async def agent_invoke(req: func.HttpRequest) -> func.HttpResponse:
    """Main agent invocation endpoint"""

    try:
        agent_name = req.route_params.get("agent_name")
        thread_id = req.params.get("thread_id")
        stream = req.params.get("stream", "false").lower() == "true"

        data = req.get_json()
        message = data.get("message")

        if not message:
            return func.HttpResponse(
                json.dumps({"error": "Missing 'message' field"}),
                status_code=400,
                mimetype="application/json"
            )

        # Invoke agent
        result = await app_instance.invoke_agent(
            agent_name=agent_name,
            message=message,
            thread_id=thread_id,
            stream=stream
        )

        return func.HttpResponse(
            json.dumps(result),
            status_code=200,
            mimetype="application/json",
            headers={
                "x-ms-thread-id": result.get("thread_id"),
                "x-ms-execution-time-ms": str(result.get("execution_time_ms", 0))
            }
        )

    except ValueError as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=400,
            mimetype="application/json"
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": "Internal server error", "details": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

@app.route("health", methods=["GET"])
async def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint"""

    health_status = {
        "status": "healthy",
        "agents": [
            {
                "name": agent.name,
                "status": "ready",
                "model": agent.model
            }
            for agent in app_instance.agents
        ]
    }

    return func.HttpResponse(
        json.dumps(health_status),
        status_code=200,
        mimetype="application/json"
    )

@app.route("agents/{agent_name}/threads/{thread_id}", methods=["GET"])
async def get_thread_history(req: func.HttpRequest) -> func.HttpResponse:
    """Retrieve thread history"""

    try:
        agent_name = req.route_params.get("agent_name")
        thread_id = req.route_params.get("thread_id")

        history = await app_instance.get_thread_history(
            agent_name=agent_name,
            thread_id=thread_id
        )

        return func.HttpResponse(
            json.dumps(history),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
```

### Step 3: Configuration Files

File: `requirements.txt`

```
azure-functions>=1.20.0
azure-functions-durable>=1.20.0
azure-storage-blob>=12.19.0
azure-storage-queue>=12.17.0
azure-storage-table>=12.18.0
azure-data-tables>=13.3.0
azure-identity>=1.15.0
azure-monitor-opentelemetry>=1.0.0
microsoft-agent-framework>=1.0.0
aiohttp>=3.9.0
pydantic>=2.5.0
python-dotenv>=1.0.0
```

File: `host.json`

```json
{
  "version": "2.0",
  "functionTimeout": "00:05:00",
  "logging": {
    "applicationInsights": {
      "samplingSettings": {
        "isEnabled": true,
        "maxTelemetryItemsPerSecond": 20,
        "evaluationInterval": "01:00:00",
        "initialSamplingPercentage": 100.0,
        "samplingPercentageIncreaseTimeout": "01:01:00",
        "samplingPercentageDecreaseTimeout": "01:05:00",
        "minSamplingPercentage": 0.1,
        "maxSamplingPercentage": 100.0,
        "movingAverageRatio": 0.25,
        "excludedTypes": "Request",
        "includedTypes": "Exception"
      }
    }
  },
  "extensionBundle": {
    "id": "Microsoft.Azure.Functions.ExtensionBundle",
    "version": "[4.*, 5.0.0)"
  }
}
```

### Step 4: Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Start Docker services
docker-compose up -d

# Start function runtime
func start

# In another terminal, test endpoints:

# Health check
curl http://localhost:7071/health

# Create new conversation
curl -X POST "http://localhost:7071/api/agents/customer_support/run" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hi, I need help with my account"}'

# Continue conversation
curl -X POST "http://localhost:7071/api/agents/customer_support/run?thread_id=THREAD_ID" \
  -H "Content-Type: application/json" \
  -d '{"message": "My customer ID is CUST001"}'

# Weather agent
curl -X POST "http://localhost:7071/api/agents/weather_assistant/run" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the weather in New York?"}'
```

### Step 5: Deployment

```bash
# Create resource group
az group create \
  --name agent-demo-rg \
  --location eastus

# Deploy with Azure Developer CLI
azd up

# Or deploy with Azure CLI + Bicep
az deployment group create \
  --resource-group agent-demo-rg \
  --template-file infra/main.bicep \
  --parameters location=eastus

# Deploy code
func azure functionapp publish agent-demo-XXXXX --python
```

### Step 6: Test Deployed Function

```bash
# Get function URL
FUNC_URL=$(az functionapp config appsettings list \
  --resource-group agent-demo-rg \
  --name agent-demo-XXXXX \
  --query "[?name=='WEBSITE_SLOT_SWAP_WARMUP_WAIT_TIME'].value" -o tsv)

# Test health endpoint
curl https://agent-demo-XXXXX.azurewebsites.net/api/health

# Test agent invocation
curl -X POST "https://agent-demo-XXXXX.azurewebsites.net/api/agents/customer_support/run" \
  -H "Content-Type: application/json" \
  -H "x-functions-key: YOUR_FUNCTION_KEY" \
  -d '{"message": "Hello, I need assistance"}'
```

---

## Configuration Reference Table

Complete reference of all AgentFunctionApp configuration parameters.

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `agents` | List[Agent] | N/A | Yes | List of Agent instances to host |
| `enable_health_check` | bool | True | No | Enable /health endpoint |
| `max_poll_retries` | int | 50 | No | Max retries for polling background tasks |
| `poll_interval` | float | 1.0 | No | Seconds between poll attempts |
| `max_execution_time` | int | 3600 | No | Max execution time per invocation (seconds) |
| `cors_origins` | List[str] | ["*"] | No | CORS allowed origin domains |
| `enable_streaming` | bool | False | No | Enable SSE streaming responses |
| `stream_buffer_size` | int | 4096 | No | Bytes per stream chunk |
| `stream_timeout` | int | 300 | No | Stream timeout in seconds |
| `request_timeout` | int | 300 | No | HTTP request timeout in seconds |
| `tool_timeout` | int | 30 | No | Per-tool execution timeout in seconds |
| `model_timeout` | int | 120 | No | Model inference timeout in seconds |
| `polling_timeout` | int | 60 | No | Long-polling timeout in seconds |
| `log_level` | str | "INFO" | No | Python logging level (DEBUG, INFO, WARNING, ERROR) |
| `enable_metrics` | bool | True | No | Enable Azure Monitor metrics collection |
| `custom_decorators` | List[Callable] | None | No | Additional function decorators |
| `thread_store_config` | Dict | None | No | Thread persistence backend configuration |
| `thread_timeout_seconds` | int | 3600 | No | Max active thread duration (seconds) |
| `scaling_config` | Dict | None | No | Auto-scaling configuration |
| `logging_config` | Dict | None | No | Advanced logging configuration |
| `monitoring_config` | Dict | None | No | Application Insights configuration |
| `security_config` | Dict | None | No | Security settings (authentication, encryption) |

---

## Troubleshooting Guide

### Common Issues and Solutions

**Issue: Function timeout (504 Gateway Timeout)**
- Increase `max_execution_time` for Consumption plan (max 600 seconds)
- Use Premium or Flex Consumption plan for longer operations
- Implement streaming for long-running responses
- Use Durable Functions for orchestration

**Issue: Cold start latency**
- Use Premium or Flex Consumption plan (pre-warmed instances)
- Implement keep-alive timer triggers
- Reduce package size (exclude unnecessary dependencies)
- Use lazy loading for models

**Issue: Storage connection errors**
- Verify Azurite is running (development): `docker-compose up -d`
- Check connection string in `local.settings.json`
- Verify Azure Storage account credentials for production

**Issue: Agent responses are slow**
- Profile with Application Insights
- Check tool execution times
- Consider parallel tool invocation
- Implement caching for frequent queries

**Issue: High memory usage**
- Monitor with Application Insights
- Use streaming for large responses
- Implement connection pooling
- Profile memory leaks in custom tools

---

## Best Practices

1. **Thread Management**: Always pass `thread_id` for multi-turn conversations
2. **Error Handling**: Implement comprehensive error handling in tools
3. **Timeouts**: Set appropriate timeouts for tools and models
4. **Streaming**: Use streaming for real-time feedback on long operations
5. **Monitoring**: Enable Application Insights for production deployments
6. **Security**: Use Managed Identity for Azure service authentication
7. **Scaling**: Use Durable Functions for complex orchestrations
8. **Testing**: Test locally before deploying to Azure
9. **Logging**: Implement structured logging for debugging
10. **Cost**: Monitor and optimize execution costs with Azure Cost Management
