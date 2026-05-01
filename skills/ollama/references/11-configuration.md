# Ollama — Configuration & Environment Variables

> Source: [docs.ollama.com/faq](https://docs.ollama.com/faq) | Version: 0.22.x

## Table of Contents

- [Environment Variables Reference](#environment-variables-reference)
- [Server Configuration](#server-configuration)
- [Model Storage](#model-storage)
- [Networking & Access](#networking--access)
- [GPU & Hardware](#gpu--hardware)
- [Concurrency & Scheduling](#concurrency--scheduling)
- [Logging & Debug](#logging--debug)
- [Platform-Specific Configuration](#platform-specific-configuration)
- [Common Pitfalls](#common-pitfalls)

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `127.0.0.1:11434` | Server bind address |
| `OLLAMA_MODELS` | `~/.ollama/models` | Model storage directory |
| `OLLAMA_KEEP_ALIVE` | `5m` | How long to keep models loaded |
| `OLLAMA_NUM_PARALLEL` | auto (1-4) | Parallel requests per model |
| `OLLAMA_MAX_LOADED_MODELS` | `3 * num_gpus` | Max concurrent models |
| `OLLAMA_MAX_QUEUE` | `512` | Max queued requests |
| `OLLAMA_GPU_OVERHEAD` | `0` | Reserved VRAM (bytes) |
| `OLLAMA_DEBUG` | `0` | Enable debug logging |
| `OLLAMA_FLASH_ATTENTION` | `1` | Enable flash attention |
| `OLLAMA_NOPRUNE` | `0` | Disable automatic model pruning |
| `OLLAMA_ORIGINS` | `*` | Allowed CORS origins |
| `CUDA_VISIBLE_DEVICES` | all | GPU selection for NVIDIA |
| `HSA_OVERRIDE_GFX_VERSION` | — | AMD GPU compatibility override |

## Server Configuration

### Starting the Server

```bash
# Default: localhost:11434
ollama serve

# Custom host and port
OLLAMA_HOST=0.0.0.0:8080 ollama serve

# Custom host (IPv6)
OLLAMA_HOST=[::]:11434 ollama serve
```

### Systemd Service (Linux)

```bash
# Edit the service configuration
sudo systemctl edit ollama.service
```

Add environment variables:

```ini
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_MODELS=/mnt/models"
Environment="OLLAMA_NUM_PARALLEL=4"
```

```bash
# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

### macOS (launchd)

```bash
# Set environment variables for the Ollama app
launchctl setenv OLLAMA_HOST "0.0.0.0:11434"
launchctl setenv OLLAMA_MODELS "/Volumes/external/models"

# Restart the Ollama app for changes to take effect
```

## Model Storage

### Default Locations

| Platform | Default Path |
|----------|-------------|
| macOS | `~/.ollama/models` |
| Linux | `/usr/share/ollama/.ollama/models` (systemd) or `~/.ollama/models` |
| Windows | `%USERPROFILE%\.ollama\models` |
| Docker | `/root/.ollama` (inside container) |

### Custom Storage

```bash
# Move models to a larger drive
OLLAMA_MODELS=/mnt/large-drive/ollama/models ollama serve

# Docker: mount a volume
docker run -v /mnt/models:/root/.ollama -p 11434:11434 ollama/ollama
```

### Storage Structure

```
~/.ollama/
├── models/
│   ├── manifests/          # Model metadata and layer references
│   │   └── registry.ollama.ai/
│   │       └── library/
│   │           └── llama3.2/
│   │               └── latest   # Manifest file
│   └── blobs/              # Actual model weights (content-addressed)
│       ├── sha256-abc123...
│       └── sha256-def456...
├── id_ed25519              # SSH key for registry auth
└── id_ed25519.pub
```

Models use content-addressed storage — identical layers are shared between models.

## Networking & Access

### Expose to Network

By default, Ollama only listens on localhost. To allow network access:

```bash
# Bind to all interfaces
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

**Security warning:** This exposes the API without authentication. Use a reverse proxy with auth for production.

### CORS Configuration

```bash
# Allow specific origins
OLLAMA_ORIGINS="http://localhost:3000,https://myapp.com" ollama serve

# Allow all origins (default)
OLLAMA_ORIGINS="*" ollama serve
```

### Reverse Proxy (Nginx)

```nginx
server {
    listen 443 ssl;
    server_name ollama.example.com;

    ssl_certificate /etc/ssl/certs/ollama.crt;
    ssl_certificate_key /etc/ssl/private/ollama.key;

    location / {
        proxy_pass http://127.0.0.1:11434;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_buffering off;  # Required for streaming
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

### API Key Authentication

Ollama doesn't have built-in API key auth. Add it at the reverse proxy layer:

```nginx
location / {
    if ($http_authorization != "Bearer YOUR_SECRET_KEY") {
        return 401;
    }
    proxy_pass http://127.0.0.1:11434;
}
```

## GPU & Hardware

```bash
# Reserve VRAM for system operations (prevents OOM)
OLLAMA_GPU_OVERHEAD=512000000  # 512 MB

# Select specific NVIDIA GPUs
CUDA_VISIBLE_DEVICES=0,1 ollama serve

# AMD GPU compatibility (if auto-detection fails)
HSA_OVERRIDE_GFX_VERSION=11.0.0 ollama serve

# Enable/disable flash attention
OLLAMA_FLASH_ATTENTION=1 ollama serve
```

## Concurrency & Scheduling

```bash
# Parallel requests per model
OLLAMA_NUM_PARALLEL=4

# Maximum loaded models
OLLAMA_MAX_LOADED_MODELS=2

# Maximum queue depth
OLLAMA_MAX_QUEUE=100

# Keep models loaded longer
OLLAMA_KEEP_ALIVE=30m

# Keep models loaded indefinitely
OLLAMA_KEEP_ALIVE=-1
```

**Scheduler behavior:**
1. Request arrives → check if model is loaded
2. If loaded → process immediately (up to `NUM_PARALLEL` concurrent)
3. If not loaded → load model (may evict least-recently-used model)
4. If queue full → return 503 Service Unavailable
5. After `KEEP_ALIVE` with no requests → unload model

## Logging & Debug

```bash
# Enable debug logging
OLLAMA_DEBUG=1 ollama serve

# Log output locations:
# - macOS: ~/Library/Logs/Ollama/
# - Linux: journalctl -u ollama
# - Docker: docker logs ollama
```

Debug logging shows:
- GPU detection and layer allocation
- Model loading/unloading events
- Request routing and scheduling
- Memory allocation details
- Performance metrics

## Platform-Specific Configuration

### Linux (systemd)

```bash
# View service status
sudo systemctl status ollama

# View logs
journalctl -u ollama -f

# Enable auto-start
sudo systemctl enable ollama
```

### macOS

```bash
# Logs location
ls ~/Library/Logs/Ollama/

# The Ollama app runs as a launchd agent
# Restart by quitting and reopening the app
```

### Windows

```powershell
# Models directory
$env:OLLAMA_MODELS = "D:\ollama\models"

# Set via System > Environment Variables for persistence
```

### Docker

```bash
# Full configuration via environment variables
docker run -d \
  --name ollama \
  --gpus all \
  -v ollama-data:/root/.ollama \
  -p 11434:11434 \
  -e OLLAMA_HOST=0.0.0.0:11434 \
  -e OLLAMA_NUM_PARALLEL=4 \
  -e OLLAMA_KEEP_ALIVE=10m \
  -e OLLAMA_MAX_LOADED_MODELS=2 \
  ollama/ollama
```

## Common Pitfalls

1. **Settings not taking effect** — environment variables must be set before `ollama serve` starts. On Linux, edit the systemd service, not your shell profile
2. **Port already in use** — another Ollama instance or service on port 11434. Check with `lsof -i :11434`
3. **Models disappear after Docker restart** — forgot to mount a volume. Always use `-v ollama:/root/.ollama`
4. **CORS errors in browser** — set `OLLAMA_ORIGINS` to include your app's origin
5. **Remote access not working** — `OLLAMA_HOST=0.0.0.0` required. Also check firewall rules
6. **Slow after idle** — model was unloaded after `KEEP_ALIVE`. Increase timeout or set to `-1`
