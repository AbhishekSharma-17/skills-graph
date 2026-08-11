---
name: pydantic
description: "Python data validation and settings management using type hints. MANDATORY TRIGGERS: Pydantic, pydantic, BaseModel, model_validate, model_dump, Field(), field_validator, model_validator, ConfigDict, TypeAdapter, ValidationError. Also trigger when the user wants to validate data in Python, define typed data models, serialize/deserialize Python objects, generate JSON Schema from types, create settings from environment variables, use discriminated unions, or build type-safe APIs with FastAPI. When in doubt about whether to use this skill for Python data validation tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["python", "pydantic", "validation", "data-models", "serialization", "type-hints", "json-schema", "settings"]
---

# Pydantic — Data Validation Using Python Type Hints

> Source: [Pydantic v2.13.4 documentation](https://docs.pydantic.dev/) | PyPI: `pydantic`

## Reference Files

| # | File | Read When |
|---|------|-----------|
| 00 | [Overview](references/00-overview.md) | Understanding what Pydantic is, installation, quick start, core concepts |
| 01 | [Models](references/01-models.md) | Defining BaseModel, model methods, nested models, RootModel, generic models |
| 02 | [Fields](references/02-fields.md) | Field(), defaults, constraints, computed fields, Annotated pattern |
| 03 | [Validators](references/03-validators.md) | field_validator, model_validator, before/after/wrap/plain modes |
| 04 | [Types](references/04-types.md) | Built-in types, custom types, constrained types, network types |
| 05 | [Serialization](references/05-serialization.md) | model_dump, model_dump_json, custom serializers, include/exclude |
| 06 | [Aliases](references/06-aliases.md) | alias, validation_alias, serialization_alias, AliasPath, AliasGenerator |
| 07 | [Configuration](references/07-configuration.md) | ConfigDict, strict mode, extra fields, frozen models, string settings |
| 08 | [JSON Schema](references/08-json-schema.md) | Generating JSON Schema, customization, GenerateJsonSchema, OpenAPI |
| 09 | [Unions & Discriminators](references/09-unions.md) | Union types, discriminated unions, smart mode, tagged unions |
| 10 | [Dataclasses & TypeAdapter](references/10-dataclasses.md) | Pydantic dataclasses, TypeAdapter, when to use each |
| 11 | [Settings Management](references/11-settings.md) | BaseSettings, environment variables, .env files, secrets |
| 12 | [Error Handling](references/12-error-handling.md) | ValidationError, custom errors, error messages, error types |

## Installation

```bash
pip install pydantic                    # Core library
pip install pydantic[email]             # Email validation (EmailStr)
pip install pydantic-settings           # Settings management (BaseSettings)
```

## Quick Reference

- Docs: https://docs.pydantic.dev/
- GitHub: https://github.com/pydantic/pydantic
- PyPI: https://pypi.org/project/pydantic/
- Changelog: https://github.com/pydantic/pydantic/releases
