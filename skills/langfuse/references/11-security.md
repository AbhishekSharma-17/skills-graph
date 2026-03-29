# Security & Data Privacy

> Source: [langfuse.com/docs/security](https://langfuse.com/docs/security/overview)

## Table of Contents

- [Overview](#overview)
- [Data Masking & PII Redaction](#data-masking--pii-redaction)
- [Access Control](#access-control)
- [API Key Management](#api-key-management)
- [Encryption](#encryption)
- [Compliance](#compliance)
- [Input/Output Guardrails](#inputoutput-guardrails)
- [SDK Security Features](#sdk-security-features)
- [Self-Hosting for Data Sovereignty](#self-hosting-for-data-sovereignty)
- [Common Patterns](#common-patterns)

---

## Overview

Langfuse provides multiple layers of security for LLM observability data:

- **Data masking** — redact PII before it reaches Langfuse
- **Access control** — role-based project access
- **Encryption** — at rest and in transit
- **Self-hosting** — full data sovereignty
- **SDK controls** — selective capture, sampling

## Data Masking & PII Redaction

### Client-Side Masking (Recommended)

Redact sensitive data before sending to Langfuse:

```python
import re
from langfuse import observe

def mask_pii(text: str) -> str:
    """Mask common PII patterns."""
    # Email
    text = re.sub(r'[\w.-]+@[\w.-]+\.\w+', '[EMAIL]', text)
    # Phone
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
    # SSN
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)
    # Credit card
    text = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '[CC]', text)
    return text

@observe()
def process_query(query: str) -> str:
    masked_query = mask_pii(query)
    # Only masked data is sent to Langfuse
    langfuse.set_current_trace_io(input={"query": masked_query})
    result = call_llm(masked_query)
    return result
```

### Using Presidio (Microsoft)

```python
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

def anonymize_text(text: str) -> str:
    results = analyzer.analyze(text=text, language="en")
    anonymized = anonymizer.anonymize(text=text, analyzer_results=results)
    return anonymized.text

@observe(capture_input=False, capture_output=False)
def handle_sensitive_data(data: dict) -> dict:
    masked_input = {k: anonymize_text(str(v)) for k, v in data.items()}
    langfuse.set_current_trace_io(input=masked_input)
    # Process with original data, log masked version
    return process(data)
```

### Disable Capture Entirely

```python
# Per-function
@observe(capture_input=False, capture_output=False)
def sensitive_function(secret_data):
    pass

# Globally
# LANGFUSE_OBSERVE_DECORATOR_IO_CAPTURE_ENABLED=false
```

## Access Control

### Project-Level Roles

| Role | Permissions |
|------|------------|
| **Owner** | Full access, manage members, delete project |
| **Admin** | Manage settings, API keys, prompts |
| **Member** | View traces, create datasets, run experiments |
| **Viewer** | Read-only access to traces and dashboards |

### Organization Structure

```
Organization
├── Project A (production)
│   ├── Owner: Alice
│   ├── Admin: Bob
│   └── Member: Charlie
├── Project B (staging)
│   ├── Owner: Alice
│   └── Member: Dev Team
```

### API Key Scoping

API keys are scoped to a single project. A key for Project A cannot access Project B data.

## API Key Management

### Key Types

| Type | Format | Use |
|------|--------|-----|
| Public Key | `pk-lf-...` | Client-side identification |
| Secret Key | `sk-lf-...` | Server-side authentication |

### Best Practices

- Store keys in environment variables, never in code
- Rotate keys periodically (create new, update apps, delete old)
- Use separate keys per environment (dev, staging, prod)
- Revoke compromised keys immediately in the UI

```python
# Good: environment variables
import os
langfuse = Langfuse(
    public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
    secret_key=os.environ["LANGFUSE_SECRET_KEY"],
)
```

## Encryption

### In Transit

- All Langfuse Cloud endpoints enforce TLS 1.2+
- SDK communication is HTTPS-only
- Self-hosted: configure TLS via reverse proxy (nginx, Traefik)

### At Rest

- Langfuse Cloud: encryption at rest for all storage (Postgres, ClickHouse, S3)
- Self-hosted: configure encryption at the storage layer

## Compliance

### SOC 2

Langfuse Cloud is SOC 2 Type II certified.

### GDPR

- EU hosting available (default)
- Data processing agreement (DPA) available
- Right to deletion supported
- Self-hosting for full data control

### HIPAA

Self-hosting is recommended for HIPAA compliance. Langfuse Cloud does not sign BAAs.

### Data Residency

| Region | Langfuse Cloud URL |
|--------|-------------------|
| EU (Frankfurt) | `https://cloud.langfuse.com` |
| US (Virginia) | `https://us.cloud.langfuse.com` |
| Self-hosted | Your infrastructure |

## Input/Output Guardrails

Integrate security scanning into your traces:

### LLM Guard

```python
from llm_guard.input_scanners import PromptInjection, Toxicity
from llm_guard.output_scanners import NoRefusal, Bias

@observe()
def secure_pipeline(user_input: str) -> str:
    # Scan input
    sanitized, is_valid, risk_score = PromptInjection().scan(user_input)
    langfuse.score(name="injection-risk", value=risk_score)

    if not is_valid:
        return "I cannot process this request."

    response = call_llm(sanitized)

    # Scan output
    _, output_valid, _ = Bias().scan(user_input, response)
    langfuse.score(name="bias-detected", value=0 if output_valid else 1)

    return response
```

### NeMo Guardrails

```python
from nemoguardrails import RailsConfig, LLMRails

config = RailsConfig.from_path("./config")
rails = LLMRails(config)

@observe()
def guarded_chat(message: str) -> str:
    response = rails.generate(messages=[{"role": "user", "content": message}])
    return response["content"]
```

## SDK Security Features

### Sampling

Reduce data exposure by sampling traces:

```python
langfuse = Langfuse(sample_rate=0.1)  # Only trace 10% of requests
```

### Conditional Tracing

```python
@observe()
def handle_request(user_input: str, user_tier: str) -> str:
    if user_tier == "enterprise":
        # Disable tracing for enterprise users (data sensitivity)
        langfuse.update_current_trace(metadata={"tracing_disabled": True})
    return process(user_input)
```

## Self-Hosting for Data Sovereignty

Self-hosting ensures:
- Data never leaves your infrastructure
- Full control over retention policies
- Compliance with strict data residency requirements
- Air-gapped deployment possible (no internet needed)

See `10-self-hosting.md` for deployment guides.

## Common Patterns

### Audit Logging

```python
@observe()
def audited_action(user_id: str, action: str, data: dict):
    langfuse.update_current_trace(
        user_id=user_id,
        metadata={
            "action": action,
            "ip_address": "[MASKED]",  # Don't log real IPs
            "timestamp": datetime.now().isoformat(),
        },
    )
    return execute_action(action, data)
```

### Data Retention

Configure retention policies at the database level:
- ClickHouse TTL: automatically delete old trace data
- Postgres: smaller footprint, longer retention OK

```sql
-- ClickHouse TTL example
ALTER TABLE traces MODIFY TTL created_at + INTERVAL 90 DAY;
```
