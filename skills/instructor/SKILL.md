---
name: instructor
description: "Structured LLM output extraction with Pydantic validation, automatic retries, streaming, and multi-provider support. MANDATORY TRIGGERS: instructor, structured output LLM, Pydantic LLM extraction, response_model, from_provider instructor, instructor-ai. Also trigger when the user wants to extract typed data from LLMs, needs validated JSON from language models, asks about LLM output parsing with Pydantic, or discusses structured extraction with retries. When in doubt about whether to use this skill for LLM structured output tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["python", "llm", "pydantic", "structured-output", "ai", "extraction"]
---

# Instructor

> v1.15.4 | https://python.useinstructor.com | https://github.com/567-labs/instructor

## Reference Files

| File | Read When |
|------|-----------|
| [00-overview.md](references/00-overview.md) | Starting with Instructor, understanding core value proposition, installation |
| [01-core-usage.md](references/01-core-usage.md) | Creating clients, from_provider, response_model, basic extraction patterns |
| [02-modes.md](references/02-modes.md) | Choosing extraction modes: TOOLS, JSON, MD_JSON, TOOLS_STRICT, PARALLEL_TOOLS |
| [03-validation.md](references/03-validation.md) | Pydantic validators, field constraints, semantic validation, validation context |
| [04-retries.md](references/04-retries.md) | Retry strategies, tenacity integration, backoff patterns, error handling |
| [05-streaming.md](references/05-streaming.md) | Partial streaming, iterable responses, async streaming, real-time UI updates |
| [06-providers.md](references/06-providers.md) | OpenAI, Anthropic, Ollama, Google, Mistral — provider-specific setup and modes |
| [07-multimodal.md](references/07-multimodal.md) | Image, audio, PDF extraction — unified multimodal API across providers |
| [08-hooks.md](references/08-hooks.md) | Event hooks for logging, monitoring, error classification, testing |
| [09-classification.md](references/09-classification.md) | Enums, Literals, union types for classification and labeling tasks |
| [10-batch-processing.md](references/10-batch-processing.md) | BatchProcessor, bulk extraction, cost savings, result handling |
| [11-async-patterns.md](references/11-async-patterns.md) | Async clients, concurrency with gather/as_completed, rate limiting |
| [12-advanced-patterns.md](references/12-advanced-patterns.md) | Templating, nested models, complex schemas, production best practices |

## Installation

```bash
pip install instructor
# With provider extras:
pip install "instructor[anthropic]"
pip install "instructor[google-generativeai]"
pip install "instructor[litellm]"
```

## Quick Reference

- [Official Docs](https://python.useinstructor.com)
- [GitHub Repository](https://github.com/567-labs/instructor)
- [PyPI Package](https://pypi.org/project/instructor/)
