# Error Handling

> Source: [Pydantic Error Handling](https://docs.pydantic.dev/latest/concepts/error_handling/)

## Table of Contents
- [ValidationError](#validationerror)
- [Error Structure](#error-structure)
- [Common Error Types](#common-error-types)
- [Custom Errors](#custom-errors)
- [Error Messages](#error-messages)
- [Error Formatting](#error-formatting)
- [Handling Errors in Practice](#handling-errors-in-practice)

## ValidationError

`ValidationError` is raised when data fails validation:

```python
from pydantic import BaseModel, ValidationError

class User(BaseModel):
    name: str
    age: int
    email: str

try:
    User(name="", age="not-a-number", email=123)
except ValidationError as e:
    print(e.error_count())  # number of errors
    print(e.errors())       # list of error dicts
    print(e.json())         # errors as JSON string
    print(str(e))           # human-readable error message
```

Output of `str(e)`:

```
2 validation errors for User
age
  Input should be a valid integer, unable to parse string as an integer
    [type=int_parsing, input_value='not-a-number', input_type=str]
email
  Input should be a valid string
    [type=string_type, input_value=123, input_type=int]
```

## Error Structure

Each error in `e.errors()` is a dict with these keys:

```python
{
    "type": "int_parsing",            # error type code
    "loc": ("age",),                  # field location (tuple of keys/indices)
    "msg": "Input should be a valid integer, unable to parse string as an integer",
    "input": "not-a-number",          # the invalid input value
    "url": "https://errors.pydantic.dev/2.13/v/int_parsing",  # docs link
    "ctx": {"error": "..."},          # additional context (optional)
}
```

### Nested Error Locations

```python
from pydantic import BaseModel, ValidationError

class Address(BaseModel):
    city: str
    zip_code: int

class User(BaseModel):
    name: str
    address: Address

try:
    User(name="Alice", address={"city": "NYC", "zip_code": "bad"})
except ValidationError as e:
    for err in e.errors():
        print(err["loc"])  # ('address', 'zip_code')
```

### List Item Errors

```python
from pydantic import BaseModel, ValidationError

class Model(BaseModel):
    items: list[int]

try:
    Model(items=[1, "two", 3, "four"])
except ValidationError as e:
    for err in e.errors():
        print(err["loc"])
    # ('items', 1)  — index 1 failed
    # ('items', 3)  — index 3 failed
```

## Common Error Types

| Error Type | Description | Example |
|-----------|-------------|---------|
| `missing` | Required field not provided | `User()` missing `name` |
| `string_type` | Expected string | `name=123` |
| `int_type` | Expected integer (strict) | `age="30"` in strict mode |
| `int_parsing` | Cannot parse as integer | `age="abc"` |
| `float_type` | Expected float | `price="abc"` |
| `bool_type` | Expected boolean | `active="maybe"` |
| `value_error` | Custom `ValueError` from validator | `raise ValueError(...)` |
| `assertion_error` | `assert` statement failed | `assert x > 0` |
| `string_too_short` | String below `min_length` | `Field(min_length=5)` |
| `string_too_long` | String above `max_length` | `Field(max_length=10)` |
| `string_pattern_mismatch` | Regex pattern doesn't match | `Field(pattern=...)` |
| `greater_than` | Value not greater than limit | `Field(gt=0)` |
| `less_than` | Value not less than limit | `Field(lt=100)` |
| `extra_forbidden` | Extra field with `extra="forbid"` | Unrecognized field |
| `frozen_field` | Assignment to frozen field | `frozen=True` |
| `frozen_instance` | Assignment to frozen model | `ConfigDict(frozen=True)` |
| `union_tag_invalid` | Invalid discriminator value | Wrong `pet_type` |
| `json_invalid` | Invalid JSON string | `Json[...]` field |

## Custom Errors

### ValueError in Validators

```python
from pydantic import BaseModel, field_validator

class Product(BaseModel):
    price: float

    @field_validator("price")
    @classmethod
    def must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("price must be positive")
        return v
```

Error output:
```python
{
    "type": "value_error",
    "loc": ("price",),
    "msg": "Value error, price must be positive",
    "input": -5.0,
}
```

### PydanticCustomError (Structured)

For custom error types with template messages:

```python
from pydantic import BaseModel, field_validator
from pydantic_core import PydanticCustomError

class User(BaseModel):
    username: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if len(v) < 3:
            raise PydanticCustomError(
                "username_too_short",
                "Username must be at least {min_length} characters",
                {"min_length": 3},
            )
        if not v.isalnum():
            raise PydanticCustomError(
                "username_invalid_chars",
                "Username must be alphanumeric, got '{username}'",
                {"username": v},
            )
        return v
```

Error output:
```python
{
    "type": "username_too_short",
    "loc": ("username",),
    "msg": "Username must be at least 3 characters",
    "ctx": {"min_length": 3},
}
```

### Multiple Errors from One Validator

Use `model_validator` with manual error collection:

```python
from pydantic import BaseModel, model_validator, ValidationError
from pydantic_core import InitErrorDetails, PydanticCustomError

class Registration(BaseModel):
    username: str
    password: str
    password_confirm: str

    @model_validator(mode="before")
    @classmethod
    def validate_all(cls, data):
        errors = []
        if isinstance(data, dict):
            if len(data.get("password", "")) < 8:
                errors.append(
                    InitErrorDetails(
                        type=PydanticCustomError(
                            "password_too_short",
                            "Password must be at least 8 characters",
                        ),
                        loc=("password",),
                        input=data.get("password"),
                    )
                )
            if data.get("password") != data.get("password_confirm"):
                errors.append(
                    InitErrorDetails(
                        type=PydanticCustomError(
                            "passwords_mismatch",
                            "Passwords do not match",
                        ),
                        loc=("password_confirm",),
                        input=data.get("password_confirm"),
                    )
                )
        if errors:
            raise ValidationError.from_exception_data(
                title="Registration", line_errors=errors
            )
        return data
```

## Error Messages

### Custom Error Messages via Annotations

```python
from typing import Annotated
from pydantic import BaseModel, AfterValidator

def positive_check(v: int) -> int:
    if v <= 0:
        raise ValueError("must be a positive number")
    return v

PositiveInt = Annotated[int, AfterValidator(positive_check)]

class Order(BaseModel):
    quantity: PositiveInt
```

### Internationalization

Access error details programmatically for translation:

```python
from pydantic import BaseModel, ValidationError

class User(BaseModel):
    age: int

try:
    User(age="abc")
except ValidationError as e:
    for error in e.errors():
        error_type = error["type"]     # "int_parsing"
        error_loc = error["loc"]       # ("age",)
        error_input = error["input"]   # "abc"
        # Map error_type to translated message
```

## Error Formatting

### JSON Output

```python
try:
    User(name=123, age="bad")
except ValidationError as e:
    print(e.json(indent=2))
```

### Filtering Errors

```python
try:
    User(name=123, age="bad")
except ValidationError as e:
    # Only field-level errors
    field_errors = [
        err for err in e.errors()
        if len(err["loc"]) == 1
    ]

    # Errors for a specific field
    age_errors = [
        err for err in e.errors()
        if err["loc"] == ("age",)
    ]
```

## Handling Errors in Practice

### FastAPI Error Responses

FastAPI automatically converts `ValidationError` to 422 responses. For custom formatting:

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

app = FastAPI()

@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": [
                {
                    "field": ".".join(str(loc) for loc in err["loc"]),
                    "message": err["msg"],
                    "type": err["type"],
                }
                for err in exc.errors()
            ]
        },
    )
```

### Try-Parse Pattern

```python
from pydantic import BaseModel, ValidationError

class Config(BaseModel):
    host: str
    port: int

def parse_config(data: dict) -> Config | None:
    try:
        return Config.model_validate(data)
    except ValidationError as e:
        for error in e.errors():
            print(f"Config error at {error['loc']}: {error['msg']}")
        return None
```

### Collecting All Errors

Pydantic collects all errors rather than failing on the first one:

```python
from pydantic import BaseModel, ValidationError

class Form(BaseModel):
    name: str
    email: str
    age: int

try:
    Form(name=123, email=456, age="bad")
except ValidationError as e:
    print(e.error_count())  # 3 — all errors collected
```

## Common Pitfalls

1. **`ValidationError` is from `pydantic`**, not `pydantic_core` — import from `pydantic`
2. **Errors are collected, not short-circuited** — all field errors are reported at once
3. **`loc` is a tuple**, not a string — use `".".join(str(x) for x in loc)` for dotted paths
4. **`input` in error dict** may contain sensitive data — redact before logging
5. **Model validators can still raise** even if all field validators pass
6. **`PydanticCustomError` context values** must be JSON-serializable (strings, numbers, bools)
