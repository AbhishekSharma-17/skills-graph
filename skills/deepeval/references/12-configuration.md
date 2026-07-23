# Configuration & CLI

> Source: https://deepeval.com/docs/command-line-interface

## Overview

DeepEval provides a comprehensive CLI for test execution, model provider configuration, synthetic data generation, and result inspection. Configuration follows a precedence chain: process environment → `.env.local` → `.env` → JSON keystore → defaults.

## Core CLI Commands

### deepeval test run

Execute evaluation tests via pytest:

```bash
deepeval test run test_file.py
deepeval test run tests/
deepeval test run tests/test_rag.py::test_specific_function
```

### deepeval login / logout

Authenticate with Confident AI:

```bash
# Browser-based authentication
deepeval login

# CI/headless environments
deepeval login --api-key "confident_us..."

# Save to dotenv
deepeval login --save=dotenv:.env.local

# Log out
deepeval logout
```

### deepeval generate

Generate synthetic test data:

```bash
deepeval generate --method docs --variation single-turn
deepeval generate --method scratch --variation multi-turn --output-dir ./data
```

### deepeval inspect

Open saved test runs in terminal UI:

```bash
deepeval inspect
deepeval inspect --folder ./experiments

# Requires: pip install "deepeval[inspect]"
```

Resolution order: `--folder` → `DEEPEVAL_RESULTS_FOLDER` → `.deepeval/.latest_run_full.json` → `./experiments`

### deepeval view

Open latest test run in Confident AI browser:

```bash
deepeval view
```

### deepeval diagnose

Report environment configuration:

```bash
deepeval diagnose
deepeval diagnose --json  # Machine-readable output
```

### deepeval settings

List and manage settings:

```bash
deepeval settings -l           # List all settings
deepeval settings -l "model"   # Filter settings
deepeval settings --set KEY=VALUE
```

## Model Provider Configuration

### LLM Providers

Configure the LLM judge used by metrics:

```bash
# OpenAI (default)
export OPENAI_API_KEY="sk-..."

# Azure OpenAI
deepeval set-azure-openai \
    --base-url="https://your-resource.openai.azure.com/" \
    --model="gpt-4" \
    --deployment-name="gpt-4-deployment" \
    --api-version="2024-02-15-preview"

# Ollama (local models)
deepeval set-ollama --model=deepseek-r1:1.5b \
    --base-url="http://localhost:11434"

# Gemini
deepeval set-gemini --model="gemini-2.0-flash-001"

# Anthropic
deepeval set-anthropic --model="claude-sonnet-4-20250514"

# AWS Bedrock
deepeval set-bedrock --model="anthropic.claude-3-sonnet" \
    --region="us-east-1"

# DeepSeek
deepeval set-deepseek --model="deepseek-chat"

# Grok
deepeval set-grok --model="grok-2"

# LiteLLM (multi-provider proxy)
deepeval set-litellm --model="gpt-4"

# Local model
deepeval set-local-model --model="llama3" \
    --base-url="http://localhost:8000"

# Portkey
deepeval set-portkey --model="gpt-4"
```

### Unset Providers

```bash
deepeval unset-azure-openai
deepeval unset-ollama
deepeval unset-gemini
# etc.
```

### Common set-* Flags

| Flag | Description |
|------|-------------|
| `-m` | Model name |
| `-i` | Input token cost |
| `-o` | Output token cost |
| `--save=dotenv[:path]` | Save to dotenv file |
| `--quiet`, `-q` | Suppress output |

### Embedding Provider Configuration

```bash
deepeval set-azure-openai-embedding \
    --model="text-embedding-ada-002" \
    --deployment-name="embedding-deployment"

deepeval set-ollama-embeddings --model="nomic-embed-text"

deepeval set-local-embeddings --model="sentence-transformers/all-MiniLM-L6-v2" \
    --base-url="http://localhost:8001"
```

## Custom LLM in Python

For programmatic provider configuration:

```python
from deepeval.models.base_model import DeepEvalBaseLLM

class CustomLLM(DeepEvalBaseLLM):
    def __init__(self, model):
        self.model = model

    def load_model(self):
        return self.model

    def generate(self, prompt: str) -> str:
        return self.model.invoke(prompt).content

    async def a_generate(self, prompt: str) -> str:
        res = await self.model.ainvoke(prompt)
        return res.content

    def get_model_name(self) -> str:
        return "Custom Model"

# Usage with any metric
from deepeval.metrics import AnswerRelevancyMetric

custom_llm = CustomLLM(model=my_llm_instance)
metric = AnswerRelevancyMetric(model=custom_llm)
```

### Per-Metric Model Override

```python
from deepeval.metrics import GEval

metric = GEval(
    name="Correctness",
    criteria="...",
    evaluation_params=[...],
    model="o1"  # Override for this metric only
)
```

## Environment Variables

### Core Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key (default LLM judge) |
| `CONFIDENT_API_KEY` | Confident AI platform key |
| `DEEPEVAL_RESULTS_FOLDER` | Local results storage path |
| `DEEPEVAL_DISABLE_DOTENV` | Set to `1` to skip .env loading |
| `DEEPEVAL_NO_INSPECT_PROMPT` | Set to `1` to disable post-run TUI prompt |
| `DEEPEVAL_DEFAULT_SAVE` | Default persistence target |
| `ENV_DIR_PATH` | Custom settings directory |

### Trace Configuration

| Variable | Description |
|----------|-------------|
| `CONFIDENT_TRACE_VERBOSE` | Set to `0` to disable trace console output |
| `CONFIDENT_TRACE_FLUSH` | Set to `0` to disable trace flush logging |

### Debug Configuration

```bash
deepeval set-debug --log-level DEBUG
deepeval set-debug --debug-async
deepeval unset-debug
```

| Debug Flag | Description |
|------------|-------------|
| `--log-level` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `--debug-async` | Debug async operations |
| `--trace-verbose` | Verbose trace output |
| `--trace-env` | Trace environment detection |

## Confident AI Integration

### What It Provides

- Cloud-hosted test run reports
- Regression tracking across runs
- Production monitoring with online evaluation
- Team collaboration on evaluation results
- Dataset management and version control

### Setup

```bash
# Login (saves key locally)
deepeval login

# Or set env var directly
export CONFIDENT_API_KEY="confident_us..."
```

### Is It Required?

No. DeepEval runs fully locally. Confident AI is optional for:
- Shared reports → use local JSON instead
- Regression tracking → compare runs manually
- Production monitoring → add your own logging

## Retry Behavior

DeepEval retries transient errors automatically:

- **Network timeouts, 5xx errors:** Retried up to 2 times
- **Rate limit (429) errors:** Retried unless marked non-retryable
- **Backoff strategy:** Exponential with initial 1s delay, base 2, jitter 2s, 5s cap

## .env File Precedence

```
Process environment variables (highest priority)
  → .env.local
    → .env.<APP_ENV>
      → .env
        → JSON keystore
          → defaults (lowest priority)
```

## Common Pitfalls

1. **No OPENAI_API_KEY** — Most metrics need an LLM judge; set this first
2. **Confusing CONFIDENT_API_KEY with OPENAI_API_KEY** — They serve different purposes
3. **Not using `--save=dotenv`** — CLI settings may not persist across sessions without this
4. **Wrong model for Ollama** — Ensure the model is pulled locally before setting
5. **Missing `[inspect]` extra** — `deepeval inspect` requires `pip install "deepeval[inspect]"`
