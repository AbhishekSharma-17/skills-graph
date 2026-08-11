# Aliases

> Source: [Pydantic Aliases](https://docs.pydantic.dev/latest/concepts/alias/)

## Table of Contents
- [Alias Types](#alias-types)
- [AliasPath](#aliaspath)
- [AliasChoices](#aliaschoices)
- [AliasGenerator](#aliasgenerator)
- [Alias Precedence](#alias-precedence)
- [Configuration Defaults](#configuration-defaults)

## Alias Types

Pydantic provides three alias types for mapping between external data names and Python field names.

### alias — Validation and Serialization

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    name: str = Field(alias="userName")

user = User.model_validate({"userName": "Alice"})
print(user.name)                          # Alice
print(user.model_dump(by_alias=True))     # {'userName': 'Alice'}
print(user.model_dump())                  # {'name': 'Alice'}
```

### validation_alias — Validation Only

Accepts `str`, `AliasPath`, or `AliasChoices`:

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    name: str = Field(validation_alias="user_name")

user = User.model_validate({"user_name": "Alice"})
print(user.model_dump())                  # {'name': 'Alice'}
print(user.model_dump(by_alias=True))     # {'name': 'Alice'} — no serialization alias
```

### serialization_alias — Serialization Only

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    name: str = Field(serialization_alias="userName")

user = User(name="Alice")
print(user.model_dump())                  # {'name': 'Alice'}
print(user.model_dump(by_alias=True))     # {'userName': 'Alice'}
```

### Combined Usage

```python
from pydantic import BaseModel, Field

class ApiUser(BaseModel):
    name: str = Field(
        validation_alias="user_name",       # accept snake_case input
        serialization_alias="userName",     # output camelCase
    )

user = ApiUser.model_validate({"user_name": "Alice"})
print(user.model_dump(by_alias=True))     # {'userName': 'Alice'}
```

## AliasPath

Access nested or indexed data during validation:

```python
from pydantic import BaseModel, Field, AliasPath

class User(BaseModel):
    first_name: str = Field(validation_alias=AliasPath("names", 0))
    last_name: str = Field(validation_alias=AliasPath("names", 1))
    city: str = Field(validation_alias=AliasPath("address", "city"))

user = User.model_validate({
    "names": ["Alice", "Smith"],
    "address": {"city": "New York"},
})
print(user.first_name)  # Alice
print(user.city)         # New York
```

Deeply nested paths:

```python
class Config(BaseModel):
    db_host: str = Field(
        validation_alias=AliasPath("database", "connection", "host")
    )

Config.model_validate({
    "database": {"connection": {"host": "localhost"}}
})
```

## AliasChoices

Accept multiple alternative field names with priority ordering:

```python
from pydantic import BaseModel, Field, AliasChoices

class User(BaseModel):
    name: str = Field(
        validation_alias=AliasChoices("name", "full_name", "display_name")
    )

# Any of these work:
User.model_validate({"name": "Alice"})
User.model_validate({"full_name": "Alice"})
User.model_validate({"display_name": "Alice"})
```

Combine with `AliasPath`:

```python
from pydantic import BaseModel, Field, AliasChoices, AliasPath

class User(BaseModel):
    email: str = Field(
        validation_alias=AliasChoices(
            "email",
            "email_address",
            AliasPath("contact", "email"),
        )
    )

User.model_validate({"email": "a@b.com"})
User.model_validate({"contact": {"email": "a@b.com"}})
```

## AliasGenerator

Automatically generate aliases for all fields from a function or `AliasGenerator`:

### Simple Function

```python
from pydantic import BaseModel, ConfigDict

class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=lambda field_name: "".join(
            word.capitalize() if i else word
            for i, word in enumerate(field_name.split("_"))
        )
    )
    user_name: str
    email_address: str

# Accepts camelCase input:
CamelModel.model_validate({"userName": "Alice", "emailAddress": "a@b.com"})
```

### AliasGenerator with Separate Validation/Serialization

```python
from pydantic import AliasGenerator, BaseModel, ConfigDict

class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=lambda name: name.upper(),
            serialization_alias=lambda name: name.title().replace("_", ""),
        )
    )
    user_name: str
    age: int

m = ApiModel.model_validate({"USER_NAME": "Alice", "AGE": 30})
print(m.model_dump(by_alias=True))  # {'UserName': 'Alice', 'Age': 30}
```

### Built-in Converters

```python
from pydantic.alias_generators import to_camel, to_pascal, to_snake

class MyModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel)
    user_name: str     # accepts "userName"
    created_at: str    # accepts "createdAt"
```

## Alias Precedence

When both `alias` on a field and `alias_generator` on the model exist:

- **Default**: Field-level `alias` takes precedence over generator
- **`alias_priority=1`**: Generator overrides the field alias
- **`alias_priority=2`**: Field alias is protected from generator (explicit)

```python
from pydantic import BaseModel, ConfigDict, Field

class Model(BaseModel):
    model_config = ConfigDict(alias_generator=lambda x: x.title())

    # Field alias wins (default behavior)
    name: str = Field(alias="username")

    # Generator wins
    email: str = Field(alias="mail", alias_priority=1)

# name uses "username", email uses "Email" (from generator)
```

## Configuration Defaults

### Validation Settings

```python
from pydantic import BaseModel, ConfigDict, Field

class Model(BaseModel):
    model_config = ConfigDict(
        validate_by_alias=True,   # accept alias names (default True)
        validate_by_name=False,   # accept field names (default False)
    )
    name: str = Field(alias="userName")

# With defaults: accepts {"userName": "Alice"} but NOT {"name": "Alice"}
```

Enable both field name and alias:

```python
model_config = ConfigDict(
    validate_by_alias=True,
    validate_by_name=True,    # now both work
)
```

### Serialization Settings

```python
class Model(BaseModel):
    model_config = ConfigDict(
        serialize_by_alias=False,  # default: field names in output
    )
    name: str = Field(serialization_alias="userName")

# model_dump() returns {'name': '...'} by default
# model_dump(by_alias=True) returns {'userName': '...'}
```

Set `serialize_by_alias=True` to always output aliases:

```python
class ApiModel(BaseModel):
    model_config = ConfigDict(serialize_by_alias=True)
    user_name: str = Field(serialization_alias="userName")

m = ApiModel(user_name="Alice")
print(m.model_dump())  # {'userName': 'Alice'} — alias by default
```

### populate_by_name

Legacy option — replaced by `validate_by_name` in v2.12+:

```python
class Model(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    name: str = Field(alias="userName")

# Both work:
Model(userName="Alice")
Model(name="Alice")
```

## Common Pitfalls

1. **`by_alias=False` by default** for `model_dump()` — aliases only appear when explicitly requested
2. **`validation_alias` overrides `alias`** for validation; `serialization_alias` overrides for serialization
3. **`validate_by_name=False` by default** — with an alias set, the Python field name is rejected in input
4. **`AliasPath` uses list indices** starting at 0, not 1
5. **Cannot set both `validate_by_alias=False` and `validate_by_name=False`** — at least one must be True
6. **`alias` must be a string**; only `validation_alias` supports `AliasPath`/`AliasChoices`
