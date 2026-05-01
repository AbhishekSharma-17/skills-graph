# Ollama — CLI Reference

> Source: [docs.ollama.com/cli](https://docs.ollama.com/cli) | CLI version: 0.22.x

## Table of Contents

- [Command Overview](#command-overview)
- [ollama run](#ollama-run)
- [ollama pull](#ollama-pull)
- [ollama push](#ollama-push)
- [ollama create](#ollama-create)
- [ollama list](#ollama-list)
- [ollama show](#ollama-show)
- [ollama cp](#ollama-cp)
- [ollama rm](#ollama-rm)
- [ollama serve](#ollama-serve)
- [ollama ps](#ollama-ps)
- [ollama stop](#ollama-stop)
- [Interactive Mode Commands](#interactive-mode-commands)
- [Common Patterns](#common-patterns)

---

## Command Overview

| Command | Description |
|---------|-------------|
| `ollama run` | Run a model (pulls if not present) |
| `ollama pull` | Download a model from the registry |
| `ollama push` | Upload a model to the registry |
| `ollama create` | Create a model from a Modelfile |
| `ollama list` | List downloaded models |
| `ollama show` | Show model information |
| `ollama cp` | Copy a model |
| `ollama rm` | Remove a model |
| `ollama serve` | Start the Ollama server |
| `ollama ps` | List running models |
| `ollama stop` | Stop a running model |

## ollama run

Run a model interactively or with a one-shot prompt.

```bash
# Interactive chat
ollama run llama3.2

# One-shot prompt
ollama run llama3.2 "What is Kubernetes?"

# With verbose output (shows timing stats)
ollama run llama3.2 --verbose "Hello"

# Pipe input
echo "Summarize this" | ollama run llama3.2

# Process a file
ollama run llama3.2 "Summarize:" < article.txt

# Vision model with image
ollama run llava "Describe this image:" < photo.jpg
```

**Behavior:**
- Auto-pulls the model if not downloaded
- Keeps the model loaded in memory after the session (configurable via `OLLAMA_KEEP_ALIVE`)
- Streams output token by token

## ollama pull

Download a model from the Ollama registry.

```bash
# Pull default tag
ollama pull qwen3

# Pull specific size
ollama pull qwen3:8b

# Pull specific quantization
ollama pull llama3.1:70b-q4_0

# Pull always gets the latest manifest
ollama pull llama3.2  # re-run to check for updates
```

## ollama push

Upload a custom model to the Ollama registry.

```bash
# Push to your namespace
ollama push myuser/mymodel:latest
```

Requires authentication via `ollama.com` account.

## ollama create

Create a new model from a Modelfile.

```bash
# Create from Modelfile in current directory
ollama create mymodel -f Modelfile

# Create with specific quantization
ollama create mymodel -f Modelfile --quantize q4_0

# Available quantization levels
# q4_0, q4_1, q5_0, q5_1, q8_0
```

**Quantization options:**
- `q4_0` — smallest, fastest, lowest quality
- `q4_1` — slightly better quality than q4_0
- `q5_0` — balanced size/quality
- `q5_1` — slightly better quality than q5_0
- `q8_0` — highest quality quantized, largest

## ollama list

List all downloaded models.

```bash
ollama list

# Output:
# NAME              ID            SIZE    MODIFIED
# llama3.2:latest   a80c4f17acd5  2.0 GB  2 days ago
# qwen3:8b          abc123def     4.9 GB  1 hour ago
# nomic-embed-text  274f441b2430  274 MB  3 days ago
```

## ollama show

Display detailed model metadata.

```bash
ollama show llama3.2

# Output includes:
# - Model architecture
# - Parameter count
# - Quantization level
# - Context length
# - Embedding length
# - License
# - System prompt
# - Modelfile template

# Show just the Modelfile
ollama show llama3.2 --modelfile

# Show just the template
ollama show llama3.2 --template

# Show just the license
ollama show llama3.2 --license

# Show just parameters
ollama show llama3.2 --parameters

# Show system prompt
ollama show llama3.2 --system
```

## ollama cp

Copy a model to a new name.

```bash
ollama cp llama3.2 my-llama3
```

Useful for creating a base to customize with `ollama create`.

## ollama rm

Remove a downloaded model.

```bash
ollama rm llama3.2
ollama rm myuser/mymodel:v1
```

## ollama serve

Start the Ollama API server.

```bash
# Start with defaults (localhost:11434)
ollama serve

# The server is typically auto-started:
# - macOS: launchd service
# - Linux: systemd service
# - Docker: container entrypoint
```

**Server configuration via environment variables:**

```bash
# Change bind address
OLLAMA_HOST=0.0.0.0:8080 ollama serve

# Custom model directory
OLLAMA_MODELS=/mnt/models ollama serve

# Enable debug logging
OLLAMA_DEBUG=1 ollama serve
```

## ollama ps

List currently loaded/running models.

```bash
ollama ps

# Output:
# NAME           ID            SIZE    PROCESSOR       UNTIL
# llama3.2:latest a80c4f17acd5 3.8 GB  100% GPU        4 minutes from now
# qwen3:8b       abc123def    6.2 GB  50% GPU / 50% CPU Forever
```

**Key columns:**
- `SIZE` — memory used (includes KV cache)
- `PROCESSOR` — GPU/CPU split for inference
- `UNTIL` — when the model will be unloaded (configurable via `OLLAMA_KEEP_ALIVE`)

## ollama stop

Stop a running model and free its memory.

```bash
ollama stop llama3.2
```

## Interactive Mode Commands

When running `ollama run <model>` interactively:

| Command | Description |
|---------|-------------|
| `/set system <msg>` | Set system message for the session |
| `/set temperature <val>` | Set temperature (0.0–2.0) |
| `/set seed <val>` | Set random seed for reproducibility |
| `/set num_ctx <val>` | Set context window size |
| `/show info` | Show model information |
| `/show modelfile` | Show the Modelfile |
| `/show template` | Show the prompt template |
| `/show system` | Show system message |
| `/show parameters` | Show model parameters |
| `/load <model>` | Load a different model |
| `/save <model>` | Save the current session as a model |
| `/clear` | Clear the chat context |
| `/bye` or `/exit` | Exit the session |
| `"""` | Begin/end multi-line input |

## Common Patterns

```bash
# Download multiple models
for model in llama3.2 qwen3:8b gemma3; do
  ollama pull "$model"
done

# Benchmark a model
ollama run llama3.2 --verbose "Write a haiku about coding" 2>&1 | grep -E "eval|total"

# Export a Modelfile from existing model
ollama show llama3.2 --modelfile > Modelfile

# Clean up unused models
ollama list | awk 'NR>1 {print $1}' | while read model; do
  echo "Keep $model? (y/n)"
  read -r answer
  [ "$answer" != "y" ] && ollama rm "$model"
done

# Check if server is running
curl -s http://localhost:11434/ && echo "Ollama is running"
```
