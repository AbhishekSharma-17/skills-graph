# Serialization

> Source: [Pydantic Serialization](https://docs.pydantic.dev/latest/concepts/serialization/)

## Table of Contents
- [model_dump](#model_dump)
- [model_dump_json](#model_dump_json)
- [Include and Exclude](#include-and-exclude)
- [Custom Field Serializers](#custom-field-serializers)
- [Custom Model Serializers](#custom-model-serializers)
- [Serialization Context](#serialization-context)
- [Polymorphic Serialization](#polymorphic-serialization)
- [SerializeAsAny](#serializeasany)

## model_dump

Convert a model to a Python dictionary:

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    name: str
    age: int
    email: str = Field(serialization_alias="email_address")

user = User(name="Alice", age=30, email="alice@example.com")

user.model_dump()
# {'name': 'Alice', 'age': 30, 'email': 'alice@example.com'}

user.model_dump(by_alias=True)
# {'name': 'Alice', 'age': 30, 'email_address': 'alice@example.com'}
```

### Filtering Options

```python
user.model_dump(exclude_none=True)      # skip None-valued fields
user.model_dump(exclude_unset=True)     # skip fields not explicitly provided
user.model_dump(exclude_defaults=True)  # skip fields matching their default
```

These are especially useful for PATCH APIs where you only want to update provided fields:

```python
class UserUpdate(BaseModel):
    name: str | None = None
    age: int | None = None
    email: str | None = None

update = UserUpdate(name="Bob")
update.model_dump(exclude_unset=True)
# {'name': 'Bob'} — only the field that was actually set
```

## model_dump_json

Serialize directly to a JSON string:

```python
from datetime import datetime
from pydantic import BaseModel

class Event(BaseModel):
    name: str
    timestamp: datetime
    tags: tuple[str, ...]

event = Event(
    name="deploy",
    timestamp=datetime(2026, 8, 11, 12, 0),
    tags=("prod", "v2"),
)

event.model_dump_json()
# '{"name":"deploy","timestamp":"2026-08-11T12:00:00","tags":["prod","v2"]}'

event.model_dump_json(indent=2)
# pretty-printed JSON
```

Key differences from `model_dump()`:
- Returns `str`, not `dict`
- Tuples become JSON arrays
- `datetime` becomes ISO 8601 string
- `bytes` becomes base64 string
- `Decimal` becomes string

## Include and Exclude

Fine-grained control over which fields appear:

```python
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    email: str
    password: str

user = User(id=1, name="Alice", email="a@b.com", password="secret")

# Exclude specific fields
user.model_dump(exclude={"password"})
# {'id': 1, 'name': 'Alice', 'email': 'a@b.com'}

# Include only specific fields
user.model_dump(include={"id", "name"})
# {'id': 1, 'name': 'Alice'}
```

### Nested Include/Exclude

```python
from pydantic import BaseModel

class Address(BaseModel):
    street: str
    city: str
    zip_code: str

class User(BaseModel):
    name: str
    address: Address

user = User(name="Alice", address=Address(street="123 Main", city="NYC", zip_code="10001"))

# Exclude nested fields
user.model_dump(exclude={"address": {"zip_code"}})
# {'name': 'Alice', 'address': {'street': '123 Main', 'city': 'NYC'}}

# Include nested fields
user.model_dump(include={"name": True, "address": {"city"}})
# {'name': 'Alice', 'address': {'city': 'NYC'}}
```

## Custom Field Serializers

### PlainSerializer

Replace default serialization for a field:

```python
from typing import Annotated
from pydantic import BaseModel, PlainSerializer

TimestampStr = Annotated[
    float,
    PlainSerializer(lambda x: f"{x:.2f}s", return_type=str),
]

class Metrics(BaseModel):
    latency: TimestampStr

m = Metrics(latency=0.12345)
print(m.model_dump())       # {'latency': '0.12s'}
```

### Decorator Syntax

```python
from pydantic import BaseModel, field_serializer

class User(BaseModel):
    name: str
    tags: list[str]

    @field_serializer("tags")
    def serialize_tags(self, tags: list[str]) -> str:
        return ",".join(tags)

u = User(name="Alice", tags=["admin", "user"])
print(u.model_dump())  # {'name': 'Alice', 'tags': 'admin,user'}
```

### WrapSerializer

Modify default serialization while keeping Pydantic's logic:

```python
from typing import Annotated
from pydantic import BaseModel, WrapSerializer, SerializerFunctionWrapHandler

def redact_long(v: str, handler: SerializerFunctionWrapHandler) -> str:
    result = handler(v)
    if len(result) > 50:
        return result[:47] + "..."
    return result

class Log(BaseModel):
    message: Annotated[str, WrapSerializer(redact_long)]
```

### JSON vs Python Mode

Serializers can behave differently for JSON vs dict output:

```python
from pydantic import BaseModel, field_serializer
from datetime import datetime

class Event(BaseModel):
    timestamp: datetime

    @field_serializer("timestamp")
    def serialize_ts(self, dt: datetime, _info) -> str | datetime:
        if _info.mode == "json":
            return dt.strftime("%Y-%m-%d")
        return dt
```

## Custom Model Serializers

### Plain Model Serializer

Replace the entire serialization:

```python
from pydantic import BaseModel, model_serializer

class Credentials(BaseModel):
    username: str
    password: str

    @model_serializer(mode="plain")
    def serialize(self) -> dict:
        return {"user": self.username}  # password excluded
```

### Wrap Model Serializer

Modify Pydantic's default output:

```python
from pydantic import BaseModel, model_serializer, SerializerFunctionWrapHandler

class Versioned(BaseModel):
    name: str
    value: int

    @model_serializer(mode="wrap")
    def add_version(self, handler: SerializerFunctionWrapHandler) -> dict:
        data = handler(self)
        data["_version"] = "1.0"
        return data

print(Versioned(name="x", value=1).model_dump())
# {'name': 'x', 'value': 1, '_version': '1.0'}
```

Only one serializer per model is allowed.

## Serialization Context

Pass runtime context to control serialization:

```python
from pydantic import BaseModel, field_serializer, FieldSerializationInfo

class Article(BaseModel):
    title: str
    body: str

    @field_serializer("body")
    def serialize_body(self, v: str, info: FieldSerializationInfo) -> str:
        if info.context and info.context.get("truncate"):
            max_len = info.context.get("max_length", 100)
            return v[:max_len] + "..." if len(v) > max_len else v
        return v

article = Article(title="Hello", body="A" * 500)

# Full body
article.model_dump()

# Truncated body
article.model_dump(context={"truncate": True, "max_length": 50})
```

## Polymorphic Serialization

By default, if a subclass instance is assigned to a base-class-typed field, only base class fields are serialized.

### Global Polymorphic Mode (v2.13+)

```python
from pydantic import BaseModel

class User(BaseModel):
    name: str

class Admin(User):
    permissions: list[str]

class Team(BaseModel):
    members: list[User]

admin = Admin(name="Alice", permissions=["read", "write"])
team = Team(members=[admin])

# Default — only User fields
team.model_dump()
# {'members': [{'name': 'Alice'}]}

# Polymorphic — includes subclass fields
team.model_dump(polymorphic_serialization=True)
# {'members': [{'name': 'Alice', 'permissions': ['read', 'write']}]}
```

## SerializeAsAny

Field-level annotation for duck-type serialization:

```python
from pydantic import BaseModel, SerializeAsAny

class User(BaseModel):
    name: str

class Admin(User):
    role: str

class Org(BaseModel):
    owner: SerializeAsAny[User]     # serializes all subclass fields
    viewer: User                     # serializes only User fields

admin = Admin(name="Alice", role="superadmin")
org = Org(owner=admin, viewer=admin)

print(org.model_dump())
# {'owner': {'name': 'Alice', 'role': 'superadmin'},
#  'viewer': {'name': 'Alice'}}
```

Runtime equivalent:

```python
org.model_dump(serialize_as_any=True)
```

## Common Pitfalls

1. **`model_dump()` returns dict**, `model_dump_json()` returns str — don't confuse them
2. **Only one `@model_serializer` per model** — defining two raises an error
3. **`by_alias=False` by default** for serialization — pass `by_alias=True` explicitly
4. **`exclude_unset` tracks what was passed** to the constructor, not what differs from defaults
5. **Subclass fields are dropped** by default when a parent type is annotated — use `SerializeAsAny` or `polymorphic_serialization=True`
6. **Circular references** can cause infinite recursion — use `model_dump()`'s `round_trip=True` carefully
