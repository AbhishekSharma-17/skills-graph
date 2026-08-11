# Validators

> Source: [Pydantic Validators](https://docs.pydantic.dev/latest/concepts/validators/)

## Table of Contents
- [Field Validators](#field-validators)
- [Validator Modes](#validator-modes)
- [Model Validators](#model-validators)
- [Annotated Validators](#annotated-validators)
- [Validation Info](#validation-info)
- [Validation Context](#validation-context)
- [Raising Errors](#raising-errors)
- [Validator Ordering](#validator-ordering)
- [Special Utilities](#special-utilities)

## Field Validators

Apply custom validation to individual fields using `@field_validator`:

```python
from pydantic import BaseModel, field_validator

class User(BaseModel):
    name: str
    age: int

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()

    @field_validator("age")
    @classmethod
    def age_must_be_positive(cls, v: int) -> int:
        if v < 0:
            raise ValueError("age must be non-negative")
        return v
```

Apply one validator to multiple fields:

```python
class Model(BaseModel):
    city: str
    country: str

    @field_validator("city", "country")
    @classmethod
    def must_be_title_case(cls, v: str) -> str:
        return v.title()
```

Use `"*"` wildcard to validate all fields:

```python
@field_validator("*", mode="before")
@classmethod
def strip_strings(cls, v):
    if isinstance(v, str):
        return v.strip()
    return v
```

## Validator Modes

### After (default)

Runs after Pydantic's built-in type validation. Receives the already-typed value:

```python
@field_validator("age", mode="after")
@classmethod
def check_age(cls, v: int) -> int:
    if v > 150:
        raise ValueError("unrealistic age")
    return v
```

### Before

Runs before type validation. Receives raw input (could be any type):

```python
from typing import Any

@field_validator("tags", mode="before")
@classmethod
def ensure_list(cls, v: Any) -> Any:
    if isinstance(v, str):
        return [v]
    return v
```

### Wrap

Most flexible — wraps Pydantic's validation. Can run code before and after, or bypass validation:

```python
from pydantic import BaseModel, field_validator, ValidationError
from pydantic import ValidatorFunctionWrapHandler

class Model(BaseModel):
    value: str

    @field_validator("value", mode="wrap")
    @classmethod
    def truncate_on_error(
        cls, v: Any, handler: ValidatorFunctionWrapHandler
    ) -> str:
        try:
            return handler(v)
        except ValidationError:
            return str(v)[:100]
```

### Plain

Replaces Pydantic's type validation entirely. No further validators run:

```python
from pydantic import BaseModel, PlainValidator
from typing import Annotated, Any

def custom_int(v: Any) -> int:
    if isinstance(v, str) and v.startswith("0x"):
        return int(v, 16)
    return int(v)

class Model(BaseModel):
    value: Annotated[int, PlainValidator(custom_int)]
```

## Model Validators

Validate the entire model, with access to all fields.

### After Model Validator

Runs after all field validation. Defined as instance method:

```python
from typing_extensions import Self
from pydantic import BaseModel, model_validator

class UserRegistration(BaseModel):
    password: str
    password_confirm: str

    @model_validator(mode="after")
    def passwords_match(self) -> Self:
        if self.password != self.password_confirm:
            raise ValueError("passwords do not match")
        return self
```

### Before Model Validator

Runs before any field validation. Receives raw input dict:

```python
from typing import Any
from pydantic import BaseModel, model_validator

class Event(BaseModel):
    name: str
    start_date: str

    @model_validator(mode="before")
    @classmethod
    def reject_sensitive_fields(cls, data: Any) -> Any:
        if isinstance(data, dict) and "ssn" in data:
            raise ValueError("SSN should not be included")
        return data
```

### Wrap Model Validator

Wraps the entire model validation process:

```python
from typing import Any
from typing_extensions import Self
from pydantic import (
    BaseModel, model_validator, ModelWrapValidatorHandler, ValidationError,
)
import logging

class SafeModel(BaseModel):
    name: str

    @model_validator(mode="wrap")
    @classmethod
    def log_failures(
        cls, data: Any, handler: ModelWrapValidatorHandler[Self]
    ) -> Self:
        try:
            return handler(data)
        except ValidationError:
            logging.error("Validation failed for: %s", data)
            raise
```

## Annotated Validators

Reusable validators via `Annotated` — composable across models:

```python
from typing import Annotated
from pydantic import AfterValidator, BeforeValidator, BaseModel

def strip_whitespace(v: str) -> str:
    return v.strip()

def to_lowercase(v: str) -> str:
    return v.lower()

def must_not_be_empty(v: str) -> str:
    if not v:
        raise ValueError("cannot be empty")
    return v

CleanStr = Annotated[str, BeforeValidator(strip_whitespace), AfterValidator(must_not_be_empty)]
Email = Annotated[str, BeforeValidator(strip_whitespace), AfterValidator(to_lowercase)]

class User(BaseModel):
    name: CleanStr
    email: Email
```

Annotated validators work inside containers:

```python
class Order(BaseModel):
    tags: list[CleanStr]  # each tag is stripped and checked
```

## Validation Info

Validators can accept a `ValidationInfo` parameter for context:

```python
from pydantic import BaseModel, field_validator, ValidationInfo

class PasswordChange(BaseModel):
    password: str
    password_confirm: str

    @field_validator("password_confirm")
    @classmethod
    def check_match(cls, v: str, info: ValidationInfo) -> str:
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("passwords do not match")
        return v
```

`ValidationInfo` provides:
- `info.data` — already-validated field values (field order matters)
- `info.context` — user-provided context dict
- `info.mode` — `"python"`, `"json"`, or `"strings"`
- `info.field_name` — current field name

## Validation Context

Pass runtime context to validators:

```python
from pydantic import BaseModel, field_validator, ValidationInfo

class Document(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def filter_text(cls, v: str, info: ValidationInfo) -> str:
        if info.context:
            stopwords = info.context.get("stopwords", set())
            words = [w for w in v.split() if w.lower() not in stopwords]
            return " ".join(words)
        return v

doc = Document.model_validate(
    {"text": "This is a sample text"},
    context={"stopwords": {"this", "is", "a"}},
)
print(doc.text)  # "sample text"
```

## Raising Errors

Three ways to signal validation failures:

### ValueError (most common)

```python
raise ValueError("name cannot be empty")
```

### AssertionError

```python
assert len(v) > 0, "cannot be empty"
```

Note: Skipped when Python runs with `-O` flag.

### PydanticCustomError (structured errors)

```python
from pydantic_core import PydanticCustomError

raise PydanticCustomError(
    "invalid_format",                      # error type code
    "Expected format '{expected}', got '{actual}'",  # message template
    {"expected": "YYYY-MM-DD", "actual": v},         # context
)
```

## Validator Ordering

With `Annotated`, execution order is:

1. **Before/Wrap validators**: right-to-left
2. **Pydantic internal validation**
3. **After validators**: left-to-right

```python
from typing import Annotated
from pydantic import AfterValidator, BeforeValidator, BaseModel

class Model(BaseModel):
    value: Annotated[
        str,
        AfterValidator(step_3),      # 3rd
        AfterValidator(step_4),      # 4th
        BeforeValidator(step_2),     # 2nd
        BeforeValidator(step_1),     # 1st (rightmost before)
    ]
```

With `@field_validator`, validators run in class definition order. Subclass validators run after parent validators.

## Special Utilities

### InstanceOf — Type checking without coercion

```python
from pydantic import BaseModel, InstanceOf

class Animal:
    pass

class Zoo(BaseModel):
    animals: list[InstanceOf[Animal]]
```

### SkipValidation — Bypass validation

```python
from pydantic import BaseModel, SkipValidation

class Cache(BaseModel):
    data: SkipValidation[dict]  # accepts anything, no validation
```

### PydanticUseDefault — Fall back to default

```python
from pydantic_core import PydanticUseDefault
from pydantic import BaseModel, BeforeValidator
from typing import Annotated, Any

def none_to_default(v: Any) -> Any:
    if v is None:
        raise PydanticUseDefault()
    return v

class Config(BaseModel):
    name: Annotated[str, BeforeValidator(none_to_default)] = "default"

print(Config(name=None).name)  # "default"
```

## Common Pitfalls

1. **Field validators must be `@classmethod`** with decorator `@field_validator`
2. **`info.data` only contains previously validated fields** — field order matters
3. **Don't mutate values then raise** — with unions, mutated values may leak to other attempts
4. **Default values are not validated** unless `validate_default=True`
5. **Before validators receive raw input** — always check the type before operating
6. **Model validators in base classes** also execute for subclasses
