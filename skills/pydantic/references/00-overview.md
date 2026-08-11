# Pydantic — Overview

> Source: [Pydantic Documentation](https://docs.pydantic.dev/) · Version 2.13.4

## What Is Pydantic

Pydantic is the most widely-used Python library for data validation. It uses Python type hints to define data schemas and provides automatic validation, serialization, and JSON Schema generation. With 27K+ GitHub stars and 10 billion+ downloads, Pydantic is used by every major Python framework including FastAPI, LangChain, and Django REST Framework.

Pydantic v2 is built on `pydantic-core`, a Rust-based validation engine that is 5-50x faster than v1.

## When to Use Pydantic

- **API request/response validation** — Define typed models for FastAPI, Flask, Django endpoints
- **Configuration management** — Load settings from env vars, `.env` files, secrets
- **Data transformation** — Parse, coerce, and normalize messy input data
- **JSON Schema generation** — Auto-generate schemas for OpenAPI, LLM tool definitions
- **Database ORM integration** — Validate data from SQLAlchemy, Django, or Tortoise ORM
- **Serialization** — Convert models to dicts, JSON, or custom formats

## Installation

```bash
pip install pydantic                     # Core library
pip install pydantic[email]              # Email validation support
pip install pydantic-settings            # Settings management
pip install pydantic[timezone]           # Timezone support
```

Requires Python 3.9+. Python 3.12+ recommended for native type parameter syntax.

## Quick Start

```python
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ValidationError

class User(BaseModel):
    id: int
    name: str = Field(min_length=1, max_length=100)
    email: str
    signup_ts: datetime | None = None
    tags: list[str] = []

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("invalid email format")
        return v.lower()

user = User(
    id="42",              # coerced to int
    name="Jane Doe",
    email="Jane@Example.COM",
    signup_ts="2026-06-01T12:00:00",
    tags=["admin", "staff"],
)

print(user.id)           # 42 (int, not str)
print(user.email)        # jane@example.com (lowered by validator)
print(user.signup_ts)    # 2026-06-01 12:00:00 (parsed datetime)

# Serialization
user.model_dump()        # dict
user.model_dump_json()   # JSON string

# JSON Schema
User.model_json_schema() # JSON Schema dict

# Validation errors
try:
    User(id="not-a-number", name="", email="bad")
except ValidationError as e:
    print(e.error_count())  # 3 errors
    print(e.errors())       # list of error dicts
```

## Core Concepts

### Models
Classes inheriting from `BaseModel` that define fields as annotated attributes.

### Fields
Field declarations with constraints (`Field(gt=0, max_length=100)`) and metadata.

### Validators
Custom validation logic via `@field_validator` and `@model_validator` decorators.

### Serialization
Convert models to dicts (`model_dump()`) or JSON (`model_dump_json()`).

### Type Coercion
Pydantic converts compatible types by default — `"42"` becomes `42` for `int` fields. Use strict mode to disable coercion.

### Configuration
`ConfigDict` controls model behavior: extra fields, immutability, string handling, ORM mode.

## Pydantic v2 vs v1 Migration Highlights

| v1 | v2 |
|----|-----|
| `.dict()` | `.model_dump()` |
| `.json()` | `.model_dump_json()` |
| `.parse_obj()` | `.model_validate()` |
| `.parse_raw()` | `.model_validate_json()` |
| `.schema()` | `.model_json_schema()` |
| `.copy()` | `.model_copy()` |
| `@validator` | `@field_validator` |
| `@root_validator` | `@model_validator` |
| `class Config:` | `model_config = ConfigDict(...)` |
| `orm_mode = True` | `from_attributes = True` |
| `Optional[X]` | `X \| None` |

## Ecosystem

| Package | Purpose |
|---------|---------|
| `pydantic` | Core data validation library |
| `pydantic-settings` | Settings management from env vars / files |
| `pydantic-extra-types` | Phone numbers, colors, countries, etc. |
| `pydantic-ai` | AI agent framework built on Pydantic |
| `logfire` | Observability platform by Pydantic team |

## Performance Notes

- Pydantic v2 uses Rust-based `pydantic-core` for validation
- Schema building happens once at class creation time (not per validation)
- Use `TypeAdapter` for non-model types to avoid BaseModel overhead
- `model_construct()` skips validation entirely for trusted data
- Reuse `TypeAdapter` instances — schema building has non-trivial cost
