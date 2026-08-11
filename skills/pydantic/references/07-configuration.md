# Configuration

> Source: [Pydantic Configuration](https://docs.pydantic.dev/latest/concepts/config/)

## Table of Contents
- [ConfigDict Usage](#configdict-usage)
- [Validation Behavior](#validation-behavior)
- [Serialization Behavior](#serialization-behavior)
- [String Handling](#string-handling)
- [Extra Fields](#extra-fields)
- [Strict Mode](#strict-mode)
- [ORM / Attribute Mode](#orm--attribute-mode)
- [JSON Schema Options](#json-schema-options)
- [All ConfigDict Options](#all-configdict-options)

## ConfigDict Usage

Configure model behavior using `ConfigDict`:

```python
from pydantic import BaseModel, ConfigDict

class User(BaseModel):
    model_config = ConfigDict(
        strict=True,
        frozen=True,
        extra="forbid",
    )
    name: str
    age: int
```

Configuration can also be set via class keyword arguments:

```python
class User(BaseModel, frozen=True, extra="forbid"):
    name: str
```

Or on dataclasses:

```python
from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

@dataclass(config=ConfigDict(strict=True))
class User:
    name: str
```

### Inheritance

Child models inherit parent configuration and can override it:

```python
class BaseUser(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)
    name: str

class MutableUser(BaseUser):
    model_config = ConfigDict(frozen=False)  # override frozen
    # strict=True is inherited
```

## Validation Behavior

```python
model_config = ConfigDict(
    # Revalidate on assignment (default: False)
    validate_assignment=True,

    # Validate default values (default: False)
    validate_default=True,

    # Revalidate instances passed as model fields (default: "never")
    revalidate_instances="always",  # "never" | "always" | "subclass-instances"

    # Allow arbitrary types that Pydantic can't validate (default: False)
    arbitrary_types_allowed=True,

    # Use enum values instead of enum members (default: False)
    use_enum_values=True,

    # Coerce numbers to strings (default: False)
    coerce_numbers_to_str=True,
)
```

### validate_assignment

```python
from pydantic import BaseModel, ConfigDict

class User(BaseModel):
    model_config = ConfigDict(validate_assignment=True)
    name: str
    age: int

user = User(name="Alice", age=30)
user.age = "not a number"  # raises ValidationError
user.age = 31              # OK, validated
```

### use_enum_values

```python
from enum import Enum
from pydantic import BaseModel, ConfigDict

class Color(str, Enum):
    RED = "red"
    BLUE = "blue"

class Item(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    color: Color

item = Item(color=Color.RED)
print(item.color)       # "red" (str), not Color.RED
print(type(item.color)) # <class 'str'>
```

## Serialization Behavior

```python
model_config = ConfigDict(
    # Use aliases by default in serialization (default: False)
    serialize_by_alias=True,

    # Accept field names during validation (default: False)
    validate_by_name=True,
)
```

## String Handling

```python
model_config = ConfigDict(
    str_strip_whitespace=True,   # strip leading/trailing whitespace
    str_to_lower=True,           # convert to lowercase
    str_to_upper=False,          # convert to uppercase
    str_min_length=0,            # minimum string length for all str fields
    str_max_length=255,          # maximum string length for all str fields
)
```

Example:

```python
from pydantic import BaseModel, ConfigDict

class CleanModel(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        str_to_lower=True,
        str_max_length=100,
    )
    name: str
    email: str

m = CleanModel(name="  Alice  ", email="  Alice@Example.COM  ")
print(m.name)   # "alice"
print(m.email)  # "alice@example.com"
```

## Extra Fields

Control handling of unrecognized fields:

```python
model_config = ConfigDict(
    extra="ignore",   # silently drop extra fields (default)
    # extra="forbid",  # raise ValidationError on extra fields
    # extra="allow",   # accept and store extra fields
)
```

```python
from pydantic import BaseModel, ConfigDict

class StrictApi(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str

StrictApi(name="Alice", role="admin")  # ValidationError: Extra inputs are not permitted
```

## Strict Mode

Disable type coercion — values must match the declared type exactly:

```python
from pydantic import BaseModel, ConfigDict

class StrictModel(BaseModel):
    model_config = ConfigDict(strict=True)
    count: int
    name: str
    active: bool

# OK
StrictModel(count=42, name="hello", active=True)

# Fails — no coercion
StrictModel(count="42", name="hello", active=True)  # str -> int rejected
StrictModel(count=42, name="hello", active=1)        # int -> bool rejected
```

### Per-Field Strict Mode

```python
from pydantic import BaseModel, Field

class MixedModel(BaseModel):
    strict_id: int = Field(strict=True)    # no coercion
    flexible_name: str                      # coercion allowed
```

### Strict Mode Conversion Table

| From \ To | `int` | `float` | `str` | `bool` | `bytes` |
|-----------|-------|---------|-------|--------|---------|
| `int` | Yes | Lax only | Lax only | Lax only | No |
| `float` | Lax only | Yes | Lax only | No | No |
| `str` | Lax only | Lax only | Yes | No | Lax only |
| `bool` | Lax only | Lax only | No | Yes | No |

"Lax only" means the conversion works in default (lax) mode but fails in strict mode.

### Per-Call Strict Mode

```python
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str

# Strict validation for this call only
User.model_validate({"id": 42, "name": "Alice"}, strict=True)
```

## ORM / Attribute Mode

Validate from object attributes (SQLAlchemy, Django ORM, dataclasses):

```python
from pydantic import BaseModel, ConfigDict

class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: str

# SQLAlchemy model
class UserORM:
    def __init__(self, id, name, email):
        self.id = id
        self.name = name
        self.email = email

orm_user = UserORM(id=1, name="Alice", email="alice@example.com")
user = UserSchema.model_validate(orm_user)
print(user.model_dump())  # {'id': 1, 'name': 'Alice', 'email': 'alice@example.com'}
```

## JSON Schema Options

```python
model_config = ConfigDict(
    title="User Model",
    json_schema_extra={"examples": [{"name": "Alice", "age": 30}]},
    json_schema_mode_override="serialization",
    field_title_generator=lambda name, info: name.replace("_", " ").title(),
    model_title_generator=lambda cls: f"Schema_{cls.__name__}",
)
```

## All ConfigDict Options

| Option | Default | Description |
|--------|---------|-------------|
| `strict` | `False` | Disable type coercion |
| `frozen` | `False` | Immutable instances (hashable) |
| `extra` | `"ignore"` | `"ignore"`, `"forbid"`, or `"allow"` |
| `from_attributes` | `False` | Validate from object attributes |
| `validate_assignment` | `False` | Validate on attribute assignment |
| `validate_default` | `False` | Validate default values |
| `validate_by_name` | `False` | Accept field names when alias is set |
| `validate_by_alias` | `True` | Accept alias names |
| `serialize_by_alias` | `False` | Use aliases in `model_dump()` by default |
| `populate_by_name` | `False` | Legacy; use `validate_by_name` |
| `use_enum_values` | `True` | Store enum values instead of members |
| `arbitrary_types_allowed` | `False` | Allow types without Pydantic support |
| `revalidate_instances` | `"never"` | `"never"`, `"always"`, `"subclass-instances"` |
| `coerce_numbers_to_str` | `False` | Convert numbers to strings |
| `str_strip_whitespace` | `False` | Strip whitespace from strings |
| `str_to_lower` | `False` | Lowercase all strings |
| `str_to_upper` | `False` | Uppercase all strings |
| `str_min_length` | `0` | Minimum string length |
| `str_max_length` | `None` | Maximum string length |
| `regex_engine` | `"rust-regex"` | Regex engine: `"rust-regex"` or `"python-re"` |
| `title` | `None` | Model title in JSON Schema |
| `json_schema_extra` | `None` | Extra JSON Schema properties |
| `defer_build` | `False` | Defer schema building until first use |

## Common Pitfalls

1. **`strict=True` on ConfigDict** applies to ALL fields — use `Field(strict=True)` for per-field control
2. **`use_enum_values=True`** means you lose the enum type — fields become plain strings/ints
3. **`validate_assignment=True`** adds overhead on every attribute set
4. **`from_attributes=True`** tries `getattr()` on non-dict inputs, which can raise unexpected errors
5. **`extra="allow"`** stores extras in `__pydantic_extra__` — they're included in `model_dump()` but not in type hints
6. **`frozen=True`** makes instances hashable but doesn't prevent mutation of nested mutable objects
