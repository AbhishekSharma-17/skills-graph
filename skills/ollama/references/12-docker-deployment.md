# Ollama — Docker & Production Deployment

> Source: [docs.ollama.com/docker](https://docs.ollama.com/docker) | Version: 0.22.x

## Table of Contents

- [Docker Quick Start](#docker-quick-start)
- [Docker Compose Setup](#docker-compose-setup)
- [GPU Configuration](#gpu-configuration)
- [Pre-Pulling Models](#pre-pulling-models)
- [Production Architecture](#production-architecture)
- [Nginx Reverse Proxy](#nginx-reverse-proxy)
- [Health Checks & Monitoring](#health-checks--monitoring)
- [Scaling & Load Balancing](#scaling--load-balancing)
- [Security Hardening](#security-hardening)
- [Backup & Recovery](#backup--recovery)
- [Common Pitfalls](#common-pitfalls)

---

## Docker Quick Start

```bash
# CPU only
docker run -d \
  --name ollama \
  -v ollama:/root/.ollama \
  -p 11434:11434 \
  ollama/ollama

# NVIDIA GPU
docker run -d \
  --name ollama \
  --gpus all \
  -v ollama:/root/.ollama \
  -p 11434:11434 \
  ollama/ollama

# AMD GPU (ROCm)
docker run -d \
  --name ollama \
  --device /dev/kfd \
  --device /dev/dri \
  -v ollama:/root/.ollama \
  -p 11434:11434 \
  ollama/ollama:rocm

# Pull and run a model
docker exec -it ollama ollama pull llama3.2
docker exec -it ollama ollama run llama3.2
```

**Pin the image tag** for production:

```bash
docker run -d --name ollama ollama/ollama:0.22.0
```

## Docker Compose Setup

### Basic Development Setup

```yaml
services:
  ollama:
    image: ollama/ollama:0.22.0
    container_name: ollama
    volumes:
      - ollama-data:/root/.ollama
    ports:
      - "11434:11434"
    environment:
      - OLLAMA_HOST=0.0.0.0:11434
      - OLLAMA_KEEP_ALIVE=10m
    restart: unless-stopped

volumes:
  ollama-data:
```

### Production Setup with GPU

```yaml
services:
  ollama:
    image: ollama/ollama:0.22.0
    container_name: ollama
    volumes:
      - ollama-data:/root/.ollama
    ports:
      - "11434:11434"
    environment:
      - OLLAMA_HOST=0.0.0.0:11434
      - OLLAMA_NUM_PARALLEL=4
      - OLLAMA_MAX_LOADED_MODELS=2
      - OLLAMA_KEEP_ALIVE=30m
      - OLLAMA_MAX_QUEUE=100
      - OLLAMA_GPU_OVERHEAD=512000000
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

volumes:
  ollama-data:
```

## GPU Configuration

### NVIDIA Container Toolkit

Prerequisites for GPU access in Docker:

```bash
# Install NVIDIA Container Toolkit
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
  sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### Selecting Specific GPUs

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          device_ids: ['0', '1']  # Use GPU 0 and 1 only
          capabilities: [gpu]
```

## Pre-Pulling Models

### Entrypoint Script

Create a custom entrypoint that pre-pulls models before accepting traffic:

```bash
#!/bin/bash
# entrypoint.sh
ollama serve &
sleep 5

echo "Pre-pulling models..."
ollama pull llama3.2
ollama pull nomic-embed-text
echo "Models ready."

wait
```

```yaml
services:
  ollama:
    image: ollama/ollama:0.22.0
    volumes:
      - ollama-data:/root/.ollama
      - ./entrypoint.sh:/entrypoint.sh
    entrypoint: ["/bin/bash", "/entrypoint.sh"]
```

### Init Container Pattern

```yaml
services:
  ollama:
    image: ollama/ollama:0.22.0
    volumes:
      - ollama-data:/root/.ollama
    ports:
      - "11434:11434"

  model-puller:
    image: ollama/ollama:0.22.0
    depends_on:
      ollama:
        condition: service_healthy
    entrypoint: >
      sh -c "
        ollama pull llama3.2 &&
        ollama pull nomic-embed-text &&
        echo 'All models pulled'
      "
    environment:
      - OLLAMA_HOST=ollama:11434
```

## Production Architecture

```
                    ┌──────────────┐
    Internet ──────▶│  Nginx/Caddy │ (TLS, auth, rate limiting)
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │ Load Balancer │ (least_conn)
                    └──┬───────┬───┘
                       │       │
              ┌────────▼──┐ ┌──▼────────┐
              │ Ollama #1 │ │ Ollama #2 │  (GPU instances)
              │ (GPU 0)   │ │ (GPU 1)   │
              └────────┬──┘ └──┬────────┘
                       │       │
                    ┌──▼───────▼──┐
                    │  Shared NFS  │ (model storage)
                    └─────────────┘
```

## Nginx Reverse Proxy

```nginx
upstream ollama {
    least_conn;
    server 127.0.0.1:11434;
    # server 127.0.0.1:11435;  # Add for multi-instance
}

server {
    listen 443 ssl http2;
    server_name llm.example.com;

    ssl_certificate     /etc/ssl/certs/llm.crt;
    ssl_certificate_key /etc/ssl/private/llm.key;

    # API key authentication
    set $api_key "YOUR_SECRET_API_KEY";
    if ($http_authorization != "Bearer $api_key") {
        return 401 '{"error": "unauthorized"}';
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=ollama:10m rate=10r/m;

    location / {
        limit_req zone=ollama burst=5 nodelay;

        proxy_pass http://ollama;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;

        # Required for streaming
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;

        # SSE headers
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
    }

    location /health {
        proxy_pass http://ollama/;
        access_log off;
    }
}
```

## Health Checks & Monitoring

### Health Check Endpoint

```bash
# Simple health check
curl -f http://localhost:11434/ || exit 1

# Check if model is loaded
curl -s http://localhost:11434/api/ps | jq '.models | length'
```

### Prometheus Metrics

Ollama doesn't expose Prometheus metrics natively. Use a sidecar:

```yaml
services:
  ollama-exporter:
    image: your-exporter:latest
    environment:
      - OLLAMA_URL=http://ollama:11434
    ports:
      - "9090:9090"
```

Monitor these key metrics:
- Request latency (total_duration from API responses)
- Tokens per second (eval_count / eval_duration)
- Active models (from /api/ps)
- Queue depth (OLLAMA_MAX_QUEUE usage)
- GPU utilization (via nvidia-smi)

### Alerting Rules

```yaml
# Alert if Ollama is down
- alert: OllamaDown
  expr: up{job="ollama"} == 0
  for: 1m

# Alert if generation is slow
- alert: OllamaSlowGeneration
  expr: ollama_tokens_per_second < 10
  for: 5m
```

## Scaling & Load Balancing

### Horizontal Scaling

Run multiple Ollama instances, each with its own GPU:

```yaml
services:
  ollama-0:
    image: ollama/ollama:0.22.0
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ['0']
              capabilities: [gpu]
    volumes:
      - shared-models:/root/.ollama
    ports:
      - "11434:11434"

  ollama-1:
    image: ollama/ollama:0.22.0
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ['1']
              capabilities: [gpu]
    volumes:
      - shared-models:/root/.ollama
    ports:
      - "11435:11434"

volumes:
  shared-models:
    driver: local
    driver_opts:
      type: nfs
      o: addr=nfs-server,rw
      device: ":/models"
```

### Capacity Planning

| GPU | VRAM | Recommended Model | Concurrent Users |
|-----|------|-------------------|-----------------|
| RTX 3060 | 12 GB | 7B Q4 | 2-4 |
| RTX 4090 | 24 GB | 13B Q4 or 7B Q8 | 4-8 |
| A100 | 40 GB | 34B Q4 or 13B Q8 | 8-16 |
| A100 | 80 GB | 70B Q4 | 8-16 |
| H100 | 80 GB | 70B Q8 | 16-32 |

## Security Hardening

1. **Never expose port 11434 directly** — always use a reverse proxy with TLS
2. **Add API key authentication** at the proxy layer
3. **Network segmentation** — run Ollama on an internal network
4. **Read-only model storage** — mount models as read-only in production
5. **Resource limits** — set Docker memory and CPU limits
6. **No shell access** — don't expose `docker exec` access

```yaml
services:
  ollama:
    image: ollama/ollama:0.22.0
    read_only: true
    tmpfs:
      - /tmp
    security_opt:
      - no-new-privileges:true
    deploy:
      resources:
        limits:
          memory: 32G
```

## Backup & Recovery

```bash
# Backup models
docker run --rm -v ollama-data:/data -v $(pwd):/backup \
  busybox tar czf /backup/ollama-models.tar.gz /data

# Restore models
docker run --rm -v ollama-data:/data -v $(pwd):/backup \
  busybox tar xzf /backup/ollama-models.tar.gz -C /

# Or simply re-pull models (if bandwidth allows)
docker exec ollama ollama pull llama3.2
```

## Common Pitfalls

1. **No volume mount** — models are stored inside the container and lost on restart. Always use `-v ollama:/root/.ollama`
2. **Wrong Docker image** — use `ollama/ollama:rocm` for AMD GPUs, not the default image
3. **Port not exposed** — `OLLAMA_HOST=0.0.0.0` is required inside the container, plus `-p 11434:11434`
4. **GPU not detected in Docker** — install NVIDIA Container Toolkit and use `--gpus all`
5. **Streaming broken behind proxy** — disable `proxy_buffering` in Nginx
6. **Models re-downloaded on restart** — volume not persisted or wrong mount point
