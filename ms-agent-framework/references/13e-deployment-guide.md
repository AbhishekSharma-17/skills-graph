# Deployment Guide — Production Hosting Strategies

## Overview

The Microsoft Agent Framework supports multiple deployment options, each suited for different scale, cost, and complexity requirements. This guide covers decision-making, implementation patterns, and production best practices.

---

## Deployment Options Comparison

| Option | Best For | Scaling | Cold Start | Cost | Complexity |
|--------|----------|---------|-----------|------|-----------|
| **FastAPI** | Simple REST APIs, testing | Manual/Docker | <100ms | Low | Low |
| **Azure Functions** | Event-driven, serverless | Auto | 1-5s | Pay-per-execution | Low |
| **Container Apps** | Microservices, scalability | Auto | <1s | Pay-per-minute | Medium |
| **AKS** | Complex orchestration, GPU | Manual | Variable | Instance-based | High |
| **AI Foundry** | Built-in compliance, observability | Managed | None | Premium | Medium |
| **A2A (Agent-to-Agent)** | Multi-agent workflows | N/A | N/A | Varies | Medium |

---

## FastAPI Deployment

FastAPI provides a lightweight, production-ready REST API wrapper for agents with streaming support.

### Basic FastAPI Server

```python
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import json
from agent_framework import ChatAgent

app = FastAPI(title="Agent API", version="1.0.0")

# Initialize agent
agent = ChatAgent(
    name="APIAgent",
    chat_client=azure_openai_client
)

@app.post("/api/chat")
async def chat(request: Request):
    """Chat endpoint with streaming support."""
    body = await request.json()
    message = body.get("message")
    context = body.get("context", {})

    async def generate():
        """Stream agent response."""
        async for chunk in agent.invoke_stream(message, context=context):
            yield json.dumps({
                "type": "chunk",
                "content": chunk,
                "timestamp": datetime.utcnow().isoformat()
            }) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")

@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/ready")
async def readiness():
    """Readiness check endpoint."""
    # Verify agent is initialized and dependencies are available
    try:
        # Quick model check
        await agent.chat_client.get_model_info()
        return {"ready": True}
    except Exception as e:
        return {"ready": False, "error": str(e)}, 503
```

### Advanced FastAPI Configuration

```python
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZIPMiddleware
import logging
from slowapi import Limiter
from slowapi.util import get_remote_address

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

app = FastAPI()

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)
app.add_middleware(GZIPMiddleware, minimum_size=1000)

# Dependency injection
def get_agent():
    """Dependency: inject agent instance."""
    return agent

@app.post("/api/chat")
@limiter.limit("100/minute")
async def chat(
    request: Request,
    user_id: str = Header(None),
    correlation_id: str = Header(None)
):
    """Chat with rate limiting and request tracking."""
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id header required")

    body = await request.json()
    message = body.get("message")

    try:
        logger.info(
            f"Chat request",
            extra={
                "user_id": user_id,
                "correlation_id": correlation_id,
                "message_length": len(message)
            }
        )

        async def generate():
            async for chunk in agent.invoke_stream(
                message,
                context={"user_id": user_id, "correlation_id": correlation_id}
            ):
                yield json.dumps({"content": chunk}) + "\n"

        return StreamingResponse(generate(), media_type="application/x-ndjson")

    except Exception as e:
        logger.error(f"Chat error: {e}", extra={"correlation_id": correlation_id})
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=4)
```

### Docker for FastAPI

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  agent-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
      - OTEL_SERVICE_NAME=agent-api
    depends_on:
      - otel-collector
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  otel-collector:
    image: otel/opentelemetry-collector:latest
    ports:
      - "4317:4317"
    volumes:
      - ./otel-collector-config.yaml:/etc/otel-collector-config.yaml
    command: --config=/etc/otel-collector-config.yaml

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yaml:/etc/prometheus/prometheus.yaml
```

---

## Azure Container Apps Deployment

Container Apps provides managed Kubernetes-like experience with automatic scaling.

### Basic Deployment

```bash
# Create Container App from image
az containerapp create \
  --name agent-api \
  --resource-group myResourceGroup \
  --image myregistry.azurecr.io/agent-api:latest \
  --registry-server myregistry.azurecr.io \
  --registry-username $REGISTRY_USERNAME \
  --registry-password $REGISTRY_PASSWORD \
  --environment myEnvironment \
  --target-port 8000 \
  --ingress external \
  --min-replicas 2 \
  --max-replicas 10
```

### Advanced Configuration with Environment Variables

```bash
# Create container app with environment variables and resource limits
az containerapp create \
  --name agent-api \
  --resource-group myResourceGroup \
  --environment myEnvironment \
  --image myregistry.azurecr.io/agent-api:latest \
  --target-port 8000 \
  --ingress external \
  --min-replicas 2 \
  --max-replicas 20 \
  --cpu 1.0 \
  --memory 2Gi \
  --env-vars \
    OPENAI_API_KEY=secretref:openai-key \
    OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317 \
    OTEL_SERVICE_NAME=agent-api \
    LOG_LEVEL=INFO
```

### Managed Identity for Azure Resources

```bash
# Create container app with managed identity
az containerapp create \
  --name agent-api \
  --resource-group myResourceGroup \
  --environment myEnvironment \
  --image myregistry.azurecr.io/agent-api:latest \
  --system-assigned \
  --target-port 8000 \
  --ingress external

# Grant managed identity permission to Key Vault
az keyvault set-policy \
  --name myKeyVault \
  --object-id $(az containerapp identity show \
    --name agent-api \
    --resource-group myResourceGroup \
    --query principalId -o tsv) \
  --secret-permissions get list
```

### Auto-Scaling Configuration

```bash
# Update container app with custom scaling rules
az containerapp update \
  --name agent-api \
  --resource-group myResourceGroup \
  --min-replicas 2 \
  --max-replicas 50 \
  --scale-rule-name cpu-rule \
  --scale-rule-type cpu \
  --scale-rule-metadata \
    type=Utilization \
    value=70
```

### Terraform for Container Apps

```hcl
resource "azurerm_container_app" "agent_api" {
  name                         = "agent-api"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"

  template {
    container {
      name   = "agent-api"
      image  = "myregistry.azurecr.io/agent-api:latest"
      cpu    = 1.0
      memory = "2Gi"

      env {
        name        = "OPENAI_API_KEY"
        secret_name = "openai-key"
      }

      env {
        name  = "LOG_LEVEL"
        value = "INFO"
      }
    }

    min_replicas = 2
    max_replicas = 20

    http_scale_rule {
      concurrent_requests = 100
      name                = "http-scaling"
    }
  }

  ingress {
    allow_insecure_connections = false
    external_enabled           = true
    target_port                = 8000

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  identity {
    type = "SystemAssigned"
  }
}
```

---

## Azure AI Foundry Deployment

AI Foundry provides server-side agent persistence, built-in MCP hosting, and enterprise compliance.

### Deploying to AI Foundry

```python
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

# Initialize project client
project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str="<your-connection-string>"
)

# Deploy agent
agent_deployment = project_client.agents.create_deployment(
    name="my-agent-deployment",
    agent_config={
        "model": "gpt-4-turbo",
        "instructions": "You are a helpful assistant.",
        "tools": [
            {
                "type": "code_interpreter"
            },
            {
                "type": "file_search",
                "file_search": {
                    "max_num_results": 5
                }
            }
        ]
    },
    deployment_config={
        "min_replicas": 2,
        "max_replicas": 10,
        "environment_variables": {
            "LOG_LEVEL": "INFO"
        }
    }
)

print(f"Agent deployed: {agent_deployment.deployment_id}")
```

### MCP Server Hosting

```python
from azure.ai.projects import AIProjectClient

# Deploy custom MCP server
mcp_server = project_client.agents.deploy_mcp_server(
    name="my-custom-mcp",
    server_config={
        "type": "sse",  # Server-Sent Events
        "endpoint": "https://my-mcp-server.azurewebsites.net/mcp",
        "capabilities": ["tools", "resources", "prompts"]
    },
    deployment_config={
        "timeout_seconds": 30,
        "retry_policy": {
            "max_retries": 3,
            "backoff_multiplier": 2
        }
    }
)

# Link agent to MCP server
agent_client.agents.update(
    agent_id=agent_id,
    tools=[
        {
            "type": "mcp",
            "mcp_server_id": mcp_server.server_id
        }
    ]
)
```

### Built-in Compliance Features

```python
# AI Foundry provides automatic:
# - Content filtering
# - PII detection and redaction
# - Audit logging
# - Access control
# - Data encryption

# Configure compliance settings
agent_client.agents.create(
    model="gpt-4-turbo",
    compliance_config={
        "pii_detection": {
            "enabled": True,
            "redaction": True
        },
        "content_filtering": {
            "enabled": True,
            "categories": ["hate", "sexual", "violence", "self_harm"]
        },
        "audit_logging": {
            "enabled": True,
            "retention_days": 90
        }
    }
)
```

---

## Kubernetes (AKS) Deployment

For complex orchestration, GPU workloads, or custom requirements.

### Helm Chart for Agent

```yaml
# values.yaml
replicaCount: 3

image:
  repository: myregistry.azurecr.io/agent-api
  tag: latest
  pullPolicy: IfNotPresent

service:
  type: LoadBalancer
  port: 80
  targetPort: 8000

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: agent-api.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: agent-api-tls
      hosts:
        - agent-api.example.com

resources:
  limits:
    cpu: 1000m
    memory: 2Gi
  requests:
    cpu: 500m
    memory: 1Gi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

env:
  - name: OPENAI_API_KEY
    valueFrom:
      secretKeyRef:
        name: agent-secrets
        key: openai-api-key
  - name: OTEL_EXPORTER_OTLP_ENDPOINT
    value: http://otel-collector:4317

livenessProbe:
  httpGet:
    path: /api/health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /api/ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Deployment Commands

```bash
# Add Helm repo
helm repo add agent-framework https://charts.agentframework.dev
helm repo update

# Install agent
helm install my-agent agent-framework/agent-api \
  --namespace agents \
  --values values.yaml

# Upgrade agent
helm upgrade my-agent agent-framework/agent-api \
  --namespace agents \
  --values values.yaml

# View deployment
kubectl get pods -n agents
kubectl logs -f deployment/agent-api -n agents
```

### GPU Support for Local Models

```yaml
# pod-spec.yaml
apiVersion: v1
kind: Pod
metadata:
  name: agent-gpu
spec:
  containers:
  - name: agent
    image: agent-api:latest
    resources:
      limits:
        nvidia.com/gpu: 1  # Request 1 GPU
    env:
    - name: CUDA_VISIBLE_DEVICES
      value: "0"
    - name: MODEL_TYPE
      value: "llama-2-13b"  # Local model
```

---

## CI/CD Pipeline

### GitHub Actions Workflow

```yaml
name: Deploy Agent

on:
  push:
    branches: [main]
  workflow_dispatch:

env:
  REGISTRY: myregistry.azurecr.io
  IMAGE_NAME: agent-api

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Login to Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ secrets.REGISTRY_USERNAME }}
          password: ${{ secrets.REGISTRY_PASSWORD }}

      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

  test:
    runs-on: ubuntu-latest
    needs: build

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        run: pytest --cov=. --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  deploy-staging:
    runs-on: ubuntu-latest
    needs: [build, test]
    environment: staging

    steps:
      - name: Deploy to Container Apps (Staging)
        uses: azure/container-apps-deploy-action@v1
        with:
          appSourceUrl: ${{ github.server_url }}/${{ github.repository }}
          acrName: ${{ secrets.ACR_NAME }}
          acrUsername: ${{ secrets.REGISTRY_USERNAME }}
          acrPassword: ${{ secrets.REGISTRY_PASSWORD }}
          containerAppName: agent-api-staging
          resourceGroup: ${{ secrets.AZURE_RESOURCE_GROUP }}
          imageToDeploy: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}

  deploy-production:
    runs-on: ubuntu-latest
    needs: deploy-staging
    environment: production
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'

    steps:
      - name: Deploy to Container Apps (Production)
        uses: azure/container-apps-deploy-action@v1
        with:
          appSourceUrl: ${{ github.server_url }}/${{ github.repository }}
          acrName: ${{ secrets.ACR_NAME }}
          acrUsername: ${{ secrets.REGISTRY_USERNAME }}
          acrPassword: ${{ secrets.REGISTRY_PASSWORD }}
          containerAppName: agent-api-prod
          resourceGroup: ${{ secrets.AZURE_RESOURCE_GROUP }}
          imageToDeploy: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}

      - name: Smoke test
        run: |
          curl -f https://agent-api.example.com/api/health
          curl -f https://agent-api.example.com/api/ready
```

### Canary Deployments

```bash
# Deploy new version to 10% of traffic
az containerapp update \
  --name agent-api \
  --resource-group myResourceGroup \
  --yaml deployment-canary.yaml

# Monitor metrics (CPU, latency, errors)
az monitor metrics list \
  --resource agent-api \
  --resource-group myResourceGroup \
  --metric "Http4xxErrors" \
  --start-time 2024-01-01T00:00Z \
  --end-time 2024-01-01T01:00Z

# If successful, increase to 100%
az containerapp update \
  --name agent-api \
  --resource-group myResourceGroup \
  --yaml deployment-full.yaml
```

---

## Production Checklist

### Security

- [ ] Enable HTTPS/TLS for all endpoints
- [ ] Configure network security groups/firewall rules
- [ ] Enable authentication (API keys, OAuth, certificates)
- [ ] Use managed identities for Azure resources
- [ ] Encrypt secrets (API keys, connection strings) in Key Vault
- [ ] Enable audit logging for all operations
- [ ] Regular security scanning of container images
- [ ] Enable DDoS protection if public endpoint

### Reliability

- [ ] Multiple replicas for high availability (min 2)
- [ ] Health checks configured (liveness + readiness)
- [ ] Graceful shutdown handling (drain connections)
- [ ] Retry logic for transient failures
- [ ] Circuit breaker for downstream dependencies
- [ ] Database connection pooling
- [ ] Message queue for async operations

### Observability

- [ ] OpenTelemetry instrumentation enabled
- [ ] Centralized logging (Application Insights, Log Analytics)
- [ ] Distributed tracing configured
- [ ] Metrics collection and dashboards
- [ ] Alerting on critical metrics (latency, errors, tokens)
- [ ] SLO/SLI defined and monitored
- [ ] On-call runbooks for common issues

### Performance

- [ ] Response time <1s for 95th percentile
- [ ] Connection pooling to downstream services
- [ ] Caching strategy for frequently accessed data
- [ ] Database query optimization
- [ ] Content compression enabled
- [ ] Load testing with expected traffic volume
- [ ] Token budget monitoring and optimization
- [ ] Model selection appropriate for use case

### Cost

- [ ] Token usage monitoring and budgets
- [ ] Serverless options evaluated for variable load
- [ ] Caching to reduce API calls
- [ ] Model choice optimized for cost/performance
- [ ] Reserved capacity for steady-state load
- [ ] Cost alerts configured

---

## Scaling Strategies

### Horizontal Scaling

```python
# Configure autoscaling
autoscaling_config = {
    "min_replicas": 2,
    "max_replicas": 50,
    "scaling_rules": [
        {
            "name": "cpu",
            "type": "cpu",
            "metric": {
                "threshold": 70,
                "operation": "greater_than"
            }
        },
        {
            "name": "memory",
            "type": "memory",
            "metric": {
                "threshold": 80,
                "operation": "greater_than"
            }
        },
        {
            "name": "http_requests",
            "type": "http",
            "metric": {
                "concurrent_requests": 100
            }
        }
    ]
}
```

### Vertical Scaling

```bash
# Increase compute resources per instance
az containerapp update \
  --name agent-api \
  --cpu 2.0 \  # Increase from 1.0
  --memory 4Gi  # Increase from 2Gi
```

### Cold Start Mitigation

```python
# 1. Use container warm-up on startup
from fastapi import FastAPI

app = FastAPI()

@app.on_event("startup")
async def warmup():
    """Warm up LLM client on startup."""
    logger.info("Warming up LLM connection...")
    try:
        # Test model connectivity
        await chat_client.get_model_info()
        logger.info("LLM ready")
    except Exception as e:
        logger.error(f"Warmup failed: {e}")

# 2. Keep minimum replicas running
# 3. Use provisioned throughput for databases
# 4. Pre-load models in memory
```

### Connection Pooling

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

# Database connection pool
db_engine = create_engine(
    connection_string,
    poolclass=QueuePool,
    pool_size=20,           # Keep 20 connections in pool
    max_overflow=10,        # Allow 10 additional connections
    pool_pre_ping=True,     # Verify connections before use
    pool_recycle=3600,      # Recycle connections after 1 hour
)

# API client connection pooling (built-in for most async libraries)
import aiohttp
async_client = aiohttp.ClientSession(
    connector=aiohttp.TCPConnector(limit_per_host=50)
)
```

### Caching Patterns

```python
from functools import lru_cache
import redis
from datetime import timedelta

# In-memory caching for small datasets
@lru_cache(maxsize=1000)
def get_user_preferences(user_id: str):
    """Cache user preferences."""
    return db.get_user_preferences(user_id)

# Redis caching for shared state
redis_client = redis.Redis(host='localhost', port=6379)

def get_cached_response(key: str, ttl_seconds: int = 3600):
    """Get response from cache or compute."""
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)

    # Compute and cache
    result = expensive_operation()
    redis_client.setex(key, ttl_seconds, json.dumps(result))
    return result
```

---

## Cost Management

### Token Usage Monitoring

```python
from opentelemetry import metrics

meter = metrics.get_meter(__name__)
token_counter = meter.create_counter(
    "llm.tokens.usage",
    unit="tokens",
    description="Tokens used by LLM"
)

async def track_token_usage(agent_state):
    """Track token consumption."""
    input_tokens = agent_state.usage.input_tokens
    output_tokens = agent_state.usage.output_tokens

    token_counter.add(
        input_tokens,
        attributes={"type": "input", "model": agent_state.model}
    )
    token_counter.add(
        output_tokens,
        attributes={"type": "output", "model": agent_state.model}
    )

    # Calculate cost
    cost = calculate_token_cost(agent_state.model, input_tokens, output_tokens)
    logger.info(f"Request cost: ${cost:.4f}")
```

### Budget Alerts

```python
from azure.monitor.query import MetricsQueryClient

metrics_client = MetricsQueryClient(credential)

def check_token_budget():
    """Alert if token spending exceeds budget."""
    DAILY_BUDGET_DOLLARS = 100.00
    ALERT_THRESHOLD = 0.80  # Alert at 80% of budget

    # Query token usage from last 24 hours
    query = """
    customMetrics
    | where name == "llm.tokens.usage"
    | where timestamp > ago(24h)
    | extend cost = value * token_cost_per_unit
    | summarize TotalCost=sum(cost)
    """

    results = logs_client.query_workspace(
        workspace_id,
        query,
        timespan=timedelta(hours=24)
    )

    current_cost = results.tables[0].rows[0][0]
    spent_percent = current_cost / DAILY_BUDGET_DOLLARS

    if spent_percent > ALERT_THRESHOLD:
        logger.warning(
            f"Token budget alert: {spent_percent*100:.1f}% of daily budget spent"
        )

        # Send alert
        send_alert(
            severity="warning",
            message=f"Daily token budget at {spent_percent*100:.1f}%"
        )
```

### Model Routing for Cost Optimization

```python
from agent_framework import ChatAgent

def create_cost_optimized_agent():
    """Use cheaper model for simple tasks, expensive for complex."""

    class CostOptimizingRouter:
        async def select_model(self, message: str):
            """Select model based on complexity."""
            # Simple queries -> cheaper model
            if len(message) < 100 and not contains_complex_concepts(message):
                return "gpt-3.5-turbo"

            # Complex queries -> powerful model
            return "gpt-4-turbo"

    router = CostOptimizingRouter()

    agent = ChatAgent(
        name="CostOptimized",
        chat_client=MultiModelClient(router)
    )

    return agent
```

---

## Summary

Choose your deployment option based on:

- **FastAPI**: Simple API, quick iteration, learning
- **Azure Functions**: Serverless, event-driven, budget-conscious
- **Container Apps**: Production microservices, auto-scaling, managed
- **AKS**: Complex orchestration, GPU workloads, advanced needs
- **AI Foundry**: Enterprise compliance, built-in safety, governance
- **A2A**: Multi-agent collaboration, workflow orchestration

Every deployment needs:
1. Health checks and monitoring
2. Graceful scaling and shutdown
3. Security hardening and secrets management
4. Observability (traces, metrics, logs)
5. Cost monitoring and optimization
6. Backup and disaster recovery plan

Start simple (FastAPI), evolve to managed services as scale increases.
