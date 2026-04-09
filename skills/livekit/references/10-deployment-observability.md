# Deployment & Observability

> Source: [docs.livekit.io/deploy](https://docs.livekit.io/deploy/) — Cloud, self-hosted, monitoring

## Table of Contents

- [Deployment Options](#deployment-options)
- [LiveKit Cloud Deployment](#livekit-cloud-deployment)
- [Self-Hosted Deployment](#self-hosted-deployment)
- [Environment Variables](#environment-variables)
- [Secrets Management](#secrets-management)
- [Scaling](#scaling)
- [Observability](#observability)
- [Data Hooks](#data-hooks)
- [Monitoring Best Practices](#monitoring-best-practices)

---

## Deployment Options

| Option | Best For | Effort |
|--------|----------|--------|
| LiveKit Cloud | Most teams, fastest time to prod | Low |
| Self-hosted + Cloud agents | Custom infra with managed agents | Medium |
| Fully self-hosted | Full control, compliance requirements | High |

## LiveKit Cloud Deployment

### First Deployment

```bash
# Install CLI
brew install livekit-cli

# Authenticate
lk cloud auth

# Initialize project
lk agent init my-agent --template agent-starter-python
cd my-agent

# Register agent with Cloud
lk agent create

# Deploy
lk agent deploy
```

### Deployment Commands

```bash
# Deploy current code
lk agent deploy

# Deploy with a specific version tag
lk agent deploy --version v1.2.0

# View deployment status
lk agent status

# View logs
lk agent logs

# Rollback to previous version
lk agent rollback

# List deployments
lk agent deployments
```

### Dashboard Capabilities

- Monitor active sessions and agent status in realtime
- View session transcripts and audio recordings
- Identify and diagnose errors
- Track usage, billing, and system limits

### Cold Starts

When no agent instances are warm, the first request may have a cold start delay. LiveKit Cloud manages scaling, but be aware of:
- Initial deployment spinup time
- Auto-scaling response time
- Minimum instance configuration

## Self-Hosted Deployment

### Docker Compose (Development)

```yaml
# docker-compose.yml
version: '3.8'
services:
  livekit:
    image: livekit/livekit-server:latest
    ports:
      - "7880:7880"   # HTTP
      - "7881:7881"   # WebRTC (TCP)
      - "7882:7882/udp"  # WebRTC (UDP)
    environment:
      - LIVEKIT_KEYS=devkey:secret
    volumes:
      - ./livekit.yaml:/etc/livekit.yaml
    command: --config /etc/livekit.yaml

  agent:
    build: .
    environment:
      - LIVEKIT_URL=ws://livekit:7880
      - LIVEKIT_API_KEY=devkey
      - LIVEKIT_API_SECRET=secret
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DEEPGRAM_API_KEY=${DEEPGRAM_API_KEY}
      - CARTESIA_API_KEY=${CARTESIA_API_KEY}
    depends_on:
      - livekit
```

### Kubernetes (Production)

```yaml
# agent-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: voice-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: voice-agent
  template:
    metadata:
      labels:
        app: voice-agent
    spec:
      containers:
        - name: agent
          image: your-registry/voice-agent:latest
          env:
            - name: LIVEKIT_URL
              value: "wss://livekit.internal"
            - name: LIVEKIT_API_KEY
              valueFrom:
                secretKeyRef:
                  name: livekit-secrets
                  key: api-key
            - name: LIVEKIT_API_SECRET
              valueFrom:
                secretKeyRef:
                  name: livekit-secrets
                  key: api-secret
          resources:
            requests:
              memory: "512Mi"
              cpu: "500m"
            limits:
              memory: "1Gi"
              cpu: "1000m"
```

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml .
RUN pip install uv && uv sync

COPY src/ src/

# Download model files at build time
RUN uv run src/agent.py download-files

CMD ["uv", "run", "src/agent.py", "start"]
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `LIVEKIT_URL` | Yes | WebSocket URL (`wss://...` or `ws://localhost:7880`) |
| `LIVEKIT_API_KEY` | Yes | API key from project settings |
| `LIVEKIT_API_SECRET` | Yes | API secret from project settings |
| `OPENAI_API_KEY` | If using OpenAI | OpenAI API key |
| `DEEPGRAM_API_KEY` | If using Deepgram | Deepgram API key |
| `CARTESIA_API_KEY` | If using Cartesia | Cartesia API key |
| `ELEVENLABS_API_KEY` | If using ElevenLabs | ElevenLabs API key |
| `ANTHROPIC_API_KEY` | If using Anthropic | Anthropic API key |
| `GOOGLE_API_KEY` | If using Google | Google AI API key |
| `ASSEMBLYAI_API_KEY` | If using AssemblyAI | AssemblyAI API key |

## Secrets Management

### LiveKit Cloud

```bash
# Set a secret
lk agent secret set OPENAI_API_KEY sk-...

# List secrets
lk agent secret list

# Delete a secret
lk agent secret delete OPENAI_API_KEY
```

Secrets are encrypted and injected at runtime — never stored in code or config files.

### Self-hosted

Use your platform's secrets management:
- Kubernetes Secrets
- Docker Secrets
- AWS Secrets Manager / Parameter Store
- HashiCorp Vault

## Scaling

### LiveKit Cloud (Automatic)

- Auto-scales agent instances based on demand
- Load balances across available instances
- Scales to plan limits automatically

### Self-Hosted

**Horizontal scaling:**
- Run multiple agent server instances
- LiveKit server distributes jobs across registered agents
- Use Kubernetes HPA for auto-scaling

**Resource considerations:**
- Each agent job is a subprocess (~100-200MB RAM)
- CPU usage depends on audio processing
- Network bandwidth for WebRTC media streams

```yaml
# Kubernetes HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: voice-agent-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: voice-agent
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

## Observability

### LiveKit Cloud Insights

Built-in observability stack providing:
- **Transcripts** — Full conversation transcripts per session
- **Traces** — Detailed pipeline execution traces
- **Logs** — Agent runtime logs
- **Audio recordings** — Session audio for quality review
- **Unified timeline** — Correlate events across the session

### Accessing Insights

```bash
# View agent logs
lk agent logs

# View specific session
lk agent session <session-id>
```

## Data Hooks

Collect custom data from agent sessions for external observability:

```python
from livekit.agents import AgentSession

@session.on("conversation_item_added")
def log_conversation(item):
    # Send to your observability stack
    send_to_datadog({
        "event": "conversation_item",
        "role": item.role,
        "content": item.content,
        "timestamp": item.timestamp,
    })

@session.on("agent_state_changed")
def log_state(state):
    send_to_datadog({
        "event": "agent_state",
        "state": state,
    })
```

**Exportable data:**
- Session recordings
- Conversation transcripts
- Pipeline metrics (STT/LLM/TTS latency)
- Custom events

## Monitoring Best Practices

1. **Track end-to-end latency** — Measure time from user speech end to agent speech start
2. **Monitor STT accuracy** — Log transcripts and flag low-confidence results
3. **Alert on error rates** — Tool failures, LLM timeouts, connection drops
4. **Track session duration** — Unusually long or short sessions may indicate issues
5. **Monitor resource usage** — CPU, memory, network per agent instance
6. **Log tool invocations** — Track which tools are called and their success rates
7. **Review transcripts** — Periodically audit conversation quality
8. **Set up health checks** — Ensure agent servers are responsive

```python
# Custom metrics collection
import time

@session.on("user_input_transcribed")
def track_stt_latency(transcript):
    metrics.histogram("stt.latency", time.time() - speech_end_time)

@session.on("agent_state_changed")
def track_response_time(state):
    if state == "speaking":
        metrics.histogram("response.latency", time.time() - thinking_start_time)
```
