# Production Deployment

> Source: [docs.vllm.ai](https://docs.vllm.ai/) — v0.22.1

## Table of Contents
- [Overview](#overview)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Prometheus Metrics](#prometheus-metrics)
- [Health Checks](#health-checks)
- [Performance Tuning](#performance-tuning)
- [Autoscaling](#autoscaling)
- [Security Hardening](#security-hardening)
- [Graceful Shutdown](#graceful-shutdown)
- [Common Pitfalls](#common-pitfalls)

## Overview

Deploying vLLM in production requires attention to container configuration, GPU access, monitoring, health checks, autoscaling, and security. vLLM provides official Docker images, Prometheus metrics, and health endpoints to support production-grade deployments.

## Docker Deployment

### Official Images

| Image | Platform | Tag Pattern |
|-------|----------|-------------|
| `vllm/vllm-openai` | NVIDIA CUDA | `latest`, `v0.22.1`, `nightly` |
| `vllm/vllm-openai-rocm` | AMD ROCm | `latest`, `nightly` |
| `intel/vllm` | Intel XPU | `latest` |

### NVIDIA GPU

```bash
docker run --runtime nvidia --gpus all \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    --env "HF_TOKEN=$HF_TOKEN" \
    -p 8000:8000 \
    --ipc=host \
    vllm/vllm-openai:latest \
    --model meta-llama/Llama-3.1-8B-Instruct
```

### AMD ROCm GPU

```bash
docker run --rm \
    --group-add=video \
    --cap-add=SYS_PTRACE \
    --security-opt seccomp=unconfined \
    --device /dev/kfd \
    --device /dev/dri \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    --env "HF_TOKEN=$HF_TOKEN" \
    -p 8000:8000 \
    --ipc=host \
    vllm/vllm-openai-rocm:latest \
    --model Qwen/Qwen2.5-7B-Instruct
```

### Docker Compose

```yaml
services:
  vllm:
    image: vllm/vllm-openai:latest
    runtime: nvidia
    environment:
      - HF_TOKEN=${HF_TOKEN}
      - NVIDIA_VISIBLE_DEVICES=all
    ports:
      - "8000:8000"
    ipc: host
    volumes:
      - hf_cache:/root/.cache/huggingface
    command: >
      --model meta-llama/Llama-3.1-8B-Instruct
      --max-model-len 4096
      --gpu-memory-utilization 0.9
      --api-key ${VLLM_API_KEY}
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 120s

volumes:
  hf_cache:
```

### Non-Root User

```bash
docker run --rm --gpus all \
    --user 2000:0 \
    -v ~/.cache/huggingface:/home/vllm/.cache/huggingface \
    -p 8000:8000 \
    vllm/vllm-openai:latest \
    --model meta-llama/Llama-3.1-8B-Instruct
```

### Building Custom Images

```dockerfile
FROM vllm/vllm-openai:v0.22.1

# Install optional dependencies
RUN uv pip install --system vllm[audio]==0.22.1

# Or add custom packages
RUN uv pip install --system my-custom-package
```

## Kubernetes Deployment

### Basic Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vllm-server
spec:
  replicas: 1
  selector:
    matchLabels:
      app: vllm
  template:
    metadata:
      labels:
        app: vllm
    spec:
      terminationGracePeriodSeconds: 120
      containers:
        - name: vllm
          image: vllm/vllm-openai:latest
          args:
            - "--model"
            - "meta-llama/Llama-3.1-8B-Instruct"
            - "--max-model-len"
            - "4096"
            - "--gpu-memory-utilization"
            - "0.9"
            - "--api-key"
            - "$(VLLM_API_KEY)"
          env:
            - name: HF_TOKEN
              valueFrom:
                secretKeyRef:
                  name: hf-secret
                  key: token
            - name: VLLM_API_KEY
              valueFrom:
                secretKeyRef:
                  name: vllm-secret
                  key: api-key
          ports:
            - containerPort: 8000
              name: http
          resources:
            limits:
              nvidia.com/gpu: 1
            requests:
              nvidia.com/gpu: 1
              memory: "32Gi"
              cpu: "4"
          startupProbe:
            httpGet:
              path: /health
              port: 8000
            failureThreshold: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            periodSeconds: 30
            failureThreshold: 3
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: kubernetes.io/hostname
          whenUnsatisfiable: DoNotSchedule
          labelSelector:
            matchLabels:
              app: vllm
---
apiVersion: v1
kind: Service
metadata:
  name: vllm-service
spec:
  selector:
    app: vllm
  ports:
    - port: 8000
      targetPort: 8000
  type: ClusterIP
```

### Multi-GPU Deployment

```yaml
resources:
  limits:
    nvidia.com/gpu: 4
  requests:
    nvidia.com/gpu: 4
    memory: "128Gi"
    cpu: "16"
```

Add `--tensor-parallel-size 4` to the args.

### GPU Scheduling with InfiniBand

```yaml
securityContext:
  capabilities:
    add: ["IPC_LOCK"]
```

## Prometheus Metrics

vLLM exposes metrics at the `/metrics` endpoint with the `vllm:` prefix.

### Key Metrics

**Server-Level (Gauges):**

| Metric | Type | Description |
|--------|------|-------------|
| `vllm:num_requests_running` | Gauge | Currently processing requests |
| `vllm:num_requests_waiting` | Gauge | Queued requests waiting for processing |
| `vllm:gpu_cache_usage_perc` | Gauge | GPU KV cache utilization (0.0–1.0) |
| `vllm:cpu_cache_usage_perc` | Gauge | CPU swap cache utilization |
| `vllm:num_preemptions_total` | Counter | Total request preemptions |

**Request-Level (Histograms):**

| Metric | Type | Description |
|--------|------|-------------|
| `vllm:time_to_first_token_seconds` | Histogram | Time to first token (TTFT) |
| `vllm:time_per_output_token_seconds` | Histogram | Inter-token latency (TPOT) |
| `vllm:e2e_request_latency_seconds` | Histogram | End-to-end request latency |
| `vllm:request_prompt_tokens` | Histogram | Prompt token counts |
| `vllm:request_generation_tokens` | Histogram | Generated token counts |

### Prometheus Scrape Config

```yaml
scrape_configs:
  - job_name: "vllm"
    scrape_interval: 15s
    static_configs:
      - targets: ["vllm-service:8000"]
    metrics_path: /metrics
```

### Key SLO Metrics

Monitor these for production health:
- **TTFT p99** < target latency — user experience for first response
- **KV cache usage** < 90% — indicates capacity headroom
- **Queue depth** (`num_requests_waiting`) — signals need for scaling
- **Preemptions** — high preemption rate means the KV cache is too small

### Grafana Dashboard

Track these panels:
1. Request latency (TTFT p50/p95/p99)
2. Token throughput (tokens/sec)
3. KV cache utilization
4. Queue depth over time
5. Active requests
6. GPU utilization (from nvidia-smi exporter)

## Health Checks

```bash
# Basic health check
curl http://localhost:8000/health

# Returns 200 when ready, 503 when loading
```

Use the health endpoint for:
- Docker HEALTHCHECK
- Kubernetes readiness/liveness probes
- Load balancer health checks

## Performance Tuning

### GPU Memory Utilization

```bash
# Aggressive (maximize KV cache)
vllm serve model --gpu-memory-utilization 0.95

# Conservative (leave headroom)
vllm serve model --gpu-memory-utilization 0.85
```

Load test between 0.85 and 0.95 to find the sweet spot.

### Max Model Length

```bash
# Only allocate KV cache for 4K context
vllm serve model --max-model-len 4096
```

Reducing `max-model-len` frees GPU memory for more concurrent requests.

### Max Concurrent Sequences

```bash
# Limit concurrent requests
vllm serve model --max-num-seqs 128
```

### Prefix Caching

Enabled by default. Benefits workloads with shared system prompts:

```bash
vllm serve model --enable-prefix-caching  # default: True
```

### Attention Backend

```bash
# Force FlashAttention for NVIDIA
vllm serve model --attention-backend FLASH_ATTN

# Force FlashInfer
vllm serve model --attention-backend FLASHINFER
```

Let vLLM auto-select unless benchmarking shows a specific backend is faster.

## Autoscaling

### Horizontal Pod Autoscaler (Kubernetes)

Scale based on Prometheus metrics using KEDA:

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: vllm-scaler
spec:
  scaleTargetRef:
    name: vllm-server
  minReplicaCount: 1
  maxReplicaCount: 8
  triggers:
    - type: prometheus
      metadata:
        serverAddress: http://prometheus:9090
        metricName: vllm_queue_depth
        query: avg(vllm:num_requests_waiting{job="vllm"})
        threshold: "5"
```

### Scaling Signals

| Signal | Scale Up When | Scale Down When |
|--------|--------------|-----------------|
| Queue depth | > 5 requests waiting | 0 for 5+ minutes |
| KV cache usage | > 85% sustained | < 50% sustained |
| TTFT p99 | > latency SLO | < 50% of SLO |

## Security Hardening

### API Authentication

```bash
vllm serve model --api-key $VLLM_API_KEY
```

### Network Security

- Run behind a reverse proxy (nginx, Envoy, Istio)
- Use TLS termination at the proxy
- Restrict `/metrics` to internal networks
- Use Kubernetes NetworkPolicy to limit pod-to-pod traffic

### Media Security

```bash
# Restrict media fetching domains
vllm serve model --allowed-media-domains "cdn.example.com,storage.googleapis.com"

# Disable URL redirects
VLLM_MEDIA_URL_ALLOW_REDIRECTS=0 vllm serve model
```

### Runtime LoRA Safety

Never expose `VLLM_ALLOW_RUNTIME_LORA_UPDATING=True` to untrusted users.

## Graceful Shutdown

Configure `terminationGracePeriodSeconds` in Kubernetes (60–120 seconds) to allow in-flight requests to complete:

```yaml
terminationGracePeriodSeconds: 120
```

vLLM handles SIGTERM by:
1. Stopping acceptance of new requests
2. Completing in-flight requests
3. Shutting down cleanly

## Common Pitfalls

1. **Missing --ipc=host** — required for shared memory between GPU processes; without it, multi-GPU setups fail
2. **No health check start period** — model loading can take minutes; set `start_period` (Docker) or `failureThreshold * periodSeconds` (K8s) high enough
3. **HF_TOKEN not set** — gated models fail silently at startup without the token
4. **Metrics not scraped** — verify `/metrics` returns data and Prometheus can reach the endpoint
5. **Over-provisioned memory** — `gpu_memory_utilization=0.99` leaves no headroom for spikes; 0.90 is a safe default
6. **No request timeout** — add client-side timeouts to prevent hung connections from consuming resources indefinitely
7. **GPU scheduling** — in Kubernetes, GPU resources are whole integers; you cannot share a GPU between vLLM pods without MIG/MPS
