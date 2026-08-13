# Chroma — Deployment

> Source: [docs.trychroma.com/guides/deploy](https://docs.trychroma.com/guides/deploy)

## Table of Contents

- [Deployment Modes](#deployment-modes)
- [CLI Server](#cli-server)
- [Docker](#docker)
- [Docker Compose with Observability](#docker-compose-with-observability)
- [AWS Deployment](#aws-deployment)
- [Azure Deployment](#azure-deployment)
- [GCP Deployment](#gcp-deployment)
- [Thin Client for Serverless](#thin-client-for-serverless)
- [Environment Variables](#environment-variables)
- [Observability](#observability)
- [Common Pitfalls](#common-pitfalls)

## Deployment Modes

| Mode | Best For | Persistence | Multi-Process |
|------|----------|-------------|---------------|
| In-Memory | Tests, experiments | No | No |
| Persistent | Local dev, small apps | Yes (disk) | No |
| Client-Server (CLI) | Dev teams, staging | Yes (disk) | Yes |
| Docker | Production self-hosted | Yes (volumes) | Yes |
| Chroma Cloud | Production managed | Yes (managed) | Yes |

## CLI Server

Start a standalone Chroma server with the built-in CLI.

```bash
# Basic — data stored in ./my-data
chroma run --path ./my-data

# Custom host and port
chroma run --path ./my-data --host 0.0.0.0 --port 8080

# Default: localhost:8000
```

**Connect from Python:**

```python
import chromadb

client = chromadb.HttpClient(host="localhost", port=8000)
```

**Connect from TypeScript:**

```typescript
import { ChromaClient } from "chromadb";

const client = new ChromaClient({ host: "localhost", port: "8000" });
```

## Docker

### Basic Docker Run

```bash
docker run \
  -v ./chroma-data:/data \
  -p 8000:8000 \
  chromadb/chroma
```

### With Custom Configuration

Create a `config.yaml`:

```yaml
allow_reset: true
anonymized_telemetry: false
```

```bash
docker run \
  -v ./chroma-data:/data \
  -v ./config.yaml:/config.yaml \
  -p 8000:8000 \
  chromadb/chroma
```

### Docker Compose

```yaml
version: "3.9"

services:
  chroma:
    image: chromadb/chroma
    ports:
      - "8000:8000"
    volumes:
      - chroma_data:/data
    environment:
      - CHROMA_SERVER_AUTHN_PROVIDER=
      - ANONYMIZED_TELEMETRY=false
    restart: unless-stopped

volumes:
  chroma_data:
```

## Docker Compose with Observability

Full stack with OpenTelemetry and Zipkin for distributed tracing.

```yaml
version: "3.9"

services:
  chroma:
    image: chromadb/chroma
    ports:
      - "8000:8000"
    volumes:
      - chroma_data:/data
    environment:
      - CHROMA_OPEN_TELEMETRY__ENDPOINT=http://otel-collector:4317/
      - CHROMA_OPEN_TELEMETRY__SERVICE_NAME=chroma
    networks:
      - internal
    restart: unless-stopped

  otel-collector:
    image: otel/opentelemetry-collector-contrib
    command: ["--config=/etc/otel-config.yaml"]
    volumes:
      - ./otel-config.yaml:/etc/otel-config.yaml
    networks:
      - internal

  zipkin:
    image: openzipkin/zipkin
    ports:
      - "9411:9411"
    networks:
      - internal

networks:
  internal:

volumes:
  chroma_data:
```

Access Zipkin UI at `http://localhost:9411` to view traces.

## AWS Deployment

Chroma provides deployment guides for AWS using:
- EC2 instances with persistent EBS volumes
- ECS/Fargate for containerized deployment
- Load balancers for high availability

General pattern:

```bash
# On EC2 instance
pip install chromadb
chroma run --path /data/chroma --host 0.0.0.0 --port 8000
```

For production, use the Docker image behind an Application Load Balancer with an EBS volume for data persistence.

## Azure Deployment

Deploy on Azure Container Instances or Azure Kubernetes Service:

```bash
# Azure Container Instances
az container create \
  --resource-group myResourceGroup \
  --name chroma-server \
  --image chromadb/chroma \
  --ports 8000 \
  --azure-file-volume-share-name chromadata \
  --azure-file-volume-account-name mystorageaccount \
  --azure-file-volume-mount-path /data
```

## GCP Deployment

Deploy on Google Cloud Run or GKE:

```bash
# Cloud Run (note: ephemeral storage — use with CloudClient for persistence)
gcloud run deploy chroma \
  --image chromadb/chroma \
  --port 8000 \
  --allow-unauthenticated
```

For persistent storage on GCP, use GKE with Persistent Disks.

## Thin Client for Serverless

For serverless functions (AWS Lambda, Cloud Functions, Vercel), use the lightweight client package to avoid heavy dependencies.

```bash
pip install chromadb-client
```

```python
import chromadb

# Connects to a Chroma server or Chroma Cloud
client = chromadb.HttpClient(host="chroma.example.com", port=8000)
```

The thin client:
- Minimal dependency footprint (no ONNX, no sentence-transformers)
- HTTP-only communication
- Requires a running Chroma server for embedding generation
- Ideal for serverless and edge environments

## Environment Variables

Server-side configuration via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `CHROMA_SERVER_HOST` | Bind address | `0.0.0.0` |
| `CHROMA_SERVER_HTTP_PORT` | HTTP port | `8000` |
| `PERSIST_DIRECTORY` | Data storage path | `/data` |
| `ANONYMIZED_TELEMETRY` | Usage telemetry | `true` |
| `ALLOW_RESET` | Enable `client.reset()` | `false` |
| `CHROMA_SERVER_AUTHN_PROVIDER` | Auth provider class | — |
| `CHROMA_SERVER_AUTHN_CREDENTIALS` | Auth credentials | — |
| `CHROMA_OPEN_TELEMETRY__ENDPOINT` | OTEL collector endpoint | — |
| `CHROMA_OPEN_TELEMETRY__SERVICE_NAME` | OTEL service name | `chroma` |

## Observability

Chroma supports OpenTelemetry for distributed tracing and metrics.

### Enable OTEL Tracing

Set environment variables on the Chroma server:

```bash
export CHROMA_OPEN_TELEMETRY__ENDPOINT=http://localhost:4317/
export CHROMA_OPEN_TELEMETRY__SERVICE_NAME=chroma
```

Compatible collectors: Jaeger, Zipkin, Grafana Tempo, Datadog, New Relic.

## Common Pitfalls

1. **Docker volume permissions** — Ensure the `/data` directory inside the container is writable. Use named volumes or set correct permissions on bind mounts.

2. **Allow reset in production** — Keep `ALLOW_RESET=false` in production. A reset wipes all data irreversibly.

3. **Single-writer constraint** — Only one Chroma server process should write to a given data directory. For multiple instances, use Chroma Cloud.

4. **Cloud Run ephemeral storage** — GCP Cloud Run has ephemeral disk. Data is lost on container restart. Use Chroma Cloud or a persistent storage solution.

5. **Thin client limitations** — `chromadb-client` cannot run embedding functions locally. The server must have the embedding function configured, or you must provide pre-computed embeddings.

6. **No built-in auth** — The default Chroma server has no authentication. Use a reverse proxy (nginx, Caddy) or Chroma Cloud for production auth.
