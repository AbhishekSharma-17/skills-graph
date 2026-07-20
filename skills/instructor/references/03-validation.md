# Instructor — Validation

> Source: https://python.useinstructor.com/concepts/validation | v1.15.4

## Table of Contents

- [Validation Flow](#validation-flow)
- [Field Constraints](#field-constraints)
- [Field Validators](#field-validators)
- [Model Validators](#model-validators)
- [Validation Context](#validation-context)
- [Pre-Validation Transforms](#pre-validation-transforms)
- [Semantic Validation with LLMs](#semantic-validation-with-llms)
- [Nested Model Validation](#nested-model-validation)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)

## Validation Flow

When the LLM returns a response, Instructor:

1. Parses the JSON from the LLM response
2. Constructs a Pydantic model instance (running all validators)
3. If validation passes → returns the typed model
4. If validation fails → appends the error to messages and retries (if `max_retries > 0`)

The retry mechanism feeds validation errors back to the LLM as context, allowing it to self-correct.

```python
import instructor
from pydantic import BaseModel, Field

class Product(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0)

client = instructor.from_provider("openai/gpt-4o-mini")
product = client.create(
    response_model=Product,
    messages=[{"role": "user", "content": "Extract: Widget costs -5 dollars"}],
    max_retries=3,  # Will retry when price <= 0
)
```

## Field Constraints

Use Pydantic's `Field()` for declarative constraints:

```python
from pydantic import BaseModel, Field

class UserProfile(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    age: int = Field(ge=0, le=150)
    email: str = Field(pattern=r"^[\w.+-]+@[\w-]+\.[\w.-]+$")
    score: float = Field(ge=0.0, le=1.0)
    tags: list[str] = Field(min_length=1, max_length=10)
```

### Common Field Constraints

| Constraint | Types | Description |
|-----------|-------|-------------|
| `min_length` / `max_length` | str, list | Length bounds |
| `ge`, `gt`, `le`, `lt` | int, float | Numeric bounds (>=, >, <=, <) |
| `pattern` | str | Regex pattern match |
| `multiple_of` | int, float | Must be divisible by value |
| `description` | any | Schema description sent to LLM |

## Field Validators

Use `@field_validator` for custom logic that field constraints can't express:

```python
from pydantic import BaseModel, field_validator

class Transaction(BaseModel):
    amount: float
    currency: str
    description: str

    @field_validator("currency")
    @classmethod
    def currency_must_be_valid(cls, v: str) -> str:
        valid = {"USD", "EUR", "GBP", "JPY", "CAD"}
        if v.upper() not in valid:
            raise ValueError(f"Currency must be one of {valid}, got {v}")
        return v.upper()

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Description cannot be empty or whitespace")
        return v.strip()
```

### Validator Modes

```python
# After-validation (default) — runs after type coercion
@field_validator("name")
@classmethod
def validate_name(cls, v: str) -> str:
    return v.title()

# Before-validation — runs on raw input before type coercion
@field_validator("username", mode="before")
@classmethod
def normalize_username(cls, v: str) -> str:
    return v.lower().strip()
```

## Model Validators

Validate across multiple fields using `@model_validator`:

```python
from pydantic import BaseModel, model_validator

class DateRange(BaseModel):
    start_date: str
    end_date: str

    @model_validator(mode="after")
    def end_after_start(self) -> "DateRange":
        if self.end_date < self.start_date:
            raise ValueError("end_date must be after start_date")
        return self
```

```python
class OrderItem(BaseModel):
    quantity: int
    unit_price: float
    total: float

    @model_validator(mode="after")
    def total_matches(self) -> "OrderItem":
        expected = self.quantity * self.unit_price
        if abs(self.total - expected) > 0.01:
            raise ValueError(
                f"Total {self.total} doesn't match "
                f"quantity * unit_price = {expected}"
            )
        return self
```

## Validation Context

Pass runtime data to validators via the `context` parameter:

```python
from pydantic import BaseModel, field_validator, ValidationInfo

class Citation(BaseModel):
    claim: str
    quote: str

    @field_validator("quote")
    @classmethod
    def quote_exists_in_source(cls, v: str, info: ValidationInfo) -> str:
        context = info.context
        if context:
            source_text = context.get("source_text", "")
            if v not in source_text:
                raise ValueError(
                    f"Quote '{v}' not found in source text. "
                    f"Must be an exact substring."
                )
        return v

client = instructor.from_provider("openai/gpt-4o-mini")
citation = client.create(
    response_model=Citation,
    messages=[{
        "role": "user",
        "content": "Find a key claim and supporting quote from this text: ...",
    }],
    context={"source_text": "The actual source text goes here..."},
    max_retries=3,
)
```

Context makes validators data-dependent without hardcoding values. On retry, the error message tells the LLM why the quote was rejected, helping it select a valid one.

## Pre-Validation Transforms

Transform raw data before validation with `mode="before"`:

```python
class NormalizedUser(BaseModel):
    username: str
    email: str

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, v: str) -> str:
        return v.lower().strip().replace(" ", "_")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()
```

## Semantic Validation with LLMs

Use `llm_validator` for subjective criteria that programmatic rules cannot handle:

```python
from instructor import llm_validator

class ContentReview(BaseModel):
    text: str
    summary: str

    @field_validator("summary")
    @classmethod
    def validate_summary(cls, v: str) -> str:
        # Use an LLM to check if the summary is accurate
        validator = llm_validator(
            "The summary must accurately reflect the main points "
            "without introducing new information.",
            model="gpt-4o-mini",
        )
        return validator(v)
```

Semantic validation is useful for content moderation, tone assessment, factual consistency, and coherence checks.

## Nested Model Validation

Validation cascades through nested models automatically:

```python
class Address(BaseModel):
    street: str = Field(min_length=5)
    city: str
    state: str = Field(min_length=2, max_length=2)
    zip_code: str = Field(pattern=r"^\d{5}(-\d{4})?$")

class Employee(BaseModel):
    name: str
    title: str
    address: Address  # Address validators run automatically

    @model_validator(mode="after")
    def title_not_empty(self) -> "Employee":
        if not self.title.strip():
            raise ValueError("Title cannot be empty")
        return self
```

## Error Handling

Catch extraction failures explicitly:

```python
from instructor.exceptions import InstructorRetryException

try:
    result = client.create(
        response_model=Product,
        messages=[{"role": "user", "content": "..."}],
        max_retries=3,
    )
except InstructorRetryException as e:
    print(f"Failed after {e.n_attempts} attempts")
    for attempt in e.failed_attempts:
        print(f"Attempt {attempt.attempt_number}: {attempt.exception}")
```

## Best Practices

1. **Start simple** — use `Field()` constraints before writing custom validators
2. **Always add descriptions** — `Field(description=...)` guides the LLM
3. **Use context for dynamic validation** — don't hardcode reference data
4. **Keep validators focused** — one concern per validator
5. **Set max_retries** — always set `max_retries=2-3` when using validators
6. **Prefer objective over semantic validation** — LLM validators are slower and less deterministic
7. **Test validators independently** — validate your Pydantic models with unit tests before using them with Instructor
