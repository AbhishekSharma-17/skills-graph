# Models

> Source: [Pydantic Models](https://docs.pydantic.dev/latest/concepts/models/)

## Table of Contents
- [Defining Models](#defining-models)
- [Required vs Optional Fields](#required-vs-optional-fields)
- [Model Methods](#model-methods)
- [Model Configuration](#model-configuration)
- [Nested Models](#nested-models)
- [Generic Models](#generic-models)
- [Dynamic Model Creation](#dynamic-model-creation)
- [RootModel](#rootmodel)
- [Private Attributes](#private-attributes)
- [Abstract Models](#abstract-models)
- [Model Immutability](#model-immutability)
- [Extra Fields](#extra-fields)

## Defining Models

Models inherit from `BaseModel` and define fields as annotated class attributes:

```python
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str = "Jane Doe"
    email: str
```

Fields without defaults are required. Fields with defaults are optional.

## Required vs Optional Fields

```python
from pydantic import BaseModel

class Item(BaseModel):
    name: str                    # required
    description: str = ""        # optional with default
    price: float | None = None   # optional, can be None
    quantity: int                 # required
```

Use `X | None` (Python 3.10+) or `Optional[X]` for nullable fields. A field typed `str | None` without a default is still required — you must pass `None` explicitly.

## Model Methods

### Validation

```python
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str

# From dict
user = User.model_validate({"id": 1, "name": "Alice"})

# From JSON string or bytes
user = User.model_validate_json('{"id": 1, "name": "Alice"}')

# From dict with string values (e.g., query params)
user = User.model_validate_strings({"id": "1", "name": "Alice"})
```

### Serialization

```python
user = User(id=1, name="Alice")

user.model_dump()                     # {'id': 1, 'name': 'Alice'}
user.model_dump(exclude={"name"})     # {'id': 1}
user.model_dump(include={"id"})       # {'id': 1}
user.model_dump(exclude_none=True)    # skip None values
user.model_dump(exclude_unset=True)   # skip fields not explicitly set
user.model_dump(exclude_defaults=True)# skip fields matching defaults
user.model_dump(by_alias=True)        # use alias names

user.model_dump_json()                # '{"id":1,"name":"Alice"}'
user.model_dump_json(indent=2)        # pretty-printed JSON
```

### Schema and Metadata

```python
User.model_json_schema()     # JSON Schema dict
User.model_fields             # dict of field name -> FieldInfo
user.model_fields_set         # set of fields explicitly provided
User.model_rebuild()          # rebuild schema for forward references
```

### Copy and Construct

```python
# Copy with updates
new_user = user.model_copy(update={"name": "Bob"})
deep_copy = user.model_copy(deep=True)

# Create without validation (trusted data only)
user = User.model_construct(id=1, name="Alice")
```

## Model Configuration

Use `ConfigDict` to configure model behavior:

```python
from pydantic import BaseModel, ConfigDict

class StrictUser(BaseModel):
    model_config = ConfigDict(
        strict=True,
        frozen=True,
        extra="forbid",
        from_attributes=True,
        str_strip_whitespace=True,
        str_max_length=255,
    )

    id: int
    name: str
```

See [Configuration](07-configuration.md) for all options.

## Nested Models

```python
from pydantic import BaseModel

class Address(BaseModel):
    street: str
    city: str
    country: str = "US"

class Company(BaseModel):
    name: str
    address: Address

class Employee(BaseModel):
    name: str
    company: Company

emp = Employee.model_validate({
    "name": "Alice",
    "company": {
        "name": "Acme",
        "address": {"street": "123 Main", "city": "NYC"},
    },
})
print(emp.company.address.city)  # NYC
```

## Generic Models

Create reusable model structures with type parameters:

```python
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class Response(BaseModel, Generic[T]):
    data: T
    error: str | None = None

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int

# Usage
int_resp = Response[int](data=42)
user_page = PaginatedResponse[User](items=[user], total=1, page=1)
```

Python 3.12+ syntax:

```python
from pydantic import BaseModel

class Response[T](BaseModel):
    data: T
    error: str | None = None
```

## Dynamic Model Creation

Build models at runtime with `create_model()`:

```python
from pydantic import create_model

DynamicUser = create_model(
    "DynamicUser",
    name=(str, ...),           # required str
    age=(int, 25),             # int with default 25
    email=(str, "a@b.com"),    # str with default
)

user = DynamicUser(name="Alice")
print(user.model_dump())  # {'name': 'Alice', 'age': 25, 'email': 'a@b.com'}
```

With validators:

```python
from pydantic import create_model, field_validator

def name_must_not_be_empty(cls, v):
    if not v.strip():
        raise ValueError("name cannot be empty")
    return v

DynamicUser = create_model(
    "DynamicUser",
    name=(str, ...),
    __validators__={"name_check": field_validator("name")(name_must_not_be_empty)},
)
```

## RootModel

Define models with a custom root type instead of named fields:

```python
from pydantic import RootModel

Pets = RootModel[list[str]]
pets = Pets.model_validate(["dog", "cat", "bird"])
print(pets.root)    # ['dog', 'cat', 'bird']
print(pets[0])      # 'dog' (supports __getitem__)

Tags = RootModel[dict[str, int]]
tags = Tags({"python": 10, "pydantic": 5})
print(tags.model_dump())  # {'python': 10, 'pydantic': 5}
```

RootModel supports iteration, length, and indexing for sequence types.

## Private Attributes

Attributes excluded from validation and serialization:

```python
from datetime import datetime
from pydantic import BaseModel, PrivateAttr

class Model(BaseModel):
    public_field: str
    _created_at: datetime = PrivateAttr(default_factory=datetime.now)
    _internal: str = PrivateAttr(default="secret")

m = Model(public_field="hello")
print(m._created_at)        # works
print(m.model_dump())       # {'public_field': 'hello'} — no private attrs
```

## Abstract Models

Combine with Python's `abc`:

```python
import abc
from pydantic import BaseModel

class Animal(BaseModel, abc.ABC):
    name: str

    @abc.abstractmethod
    def speak(self) -> str: ...

class Dog(Animal):
    breed: str

    def speak(self) -> str:
        return "Woof!"
```

## Model Immutability

```python
from pydantic import BaseModel, ConfigDict

class FrozenUser(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str
    age: int

user = FrozenUser(name="Alice", age=30)
user.name = "Bob"  # raises ValidationError: Instance is frozen

# Frozen models are hashable
users = {user}
```

Note: Nested mutable objects (lists, dicts) can still be modified in place.

## Extra Fields

Control handling of fields not declared in the model:

```python
from pydantic import BaseModel, ConfigDict

# Ignore extra fields (default)
class Strict(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str

# Forbid extra fields — raises ValidationError
class VeryStrict(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str

# Allow extra fields — stored in __pydantic_extra__
class Flexible(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str

m = Flexible(name="Alice", role="admin")
print(m.model_dump())           # {'name': 'Alice', 'role': 'admin'}
print(m.__pydantic_extra__)     # {'role': 'admin'}
```

## Common Pitfalls

1. **Mutable defaults are safe** — Pydantic deep-copies non-hashable defaults per instance
2. **`model_construct()` skips all validation** — only use with fully trusted data
3. **`model_fields_set` tracks explicit assignment**, not non-default values
4. **Generic models must be parameterized** before use as field types in other models
5. **Forward references** require `model_rebuild()` after all referenced types are defined
