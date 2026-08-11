# Types

> Source: [Pydantic Types](https://docs.pydantic.dev/latest/concepts/types/)

## Table of Contents
- [Standard Library Types](#standard-library-types)
- [Pydantic-Specific Types](#pydantic-specific-types)
- [Network Types](#network-types)
- [Constrained Types](#constrained-types)
- [Custom Types with Annotated](#custom-types-with-annotated)
- [Named Type Aliases](#named-type-aliases)
- [Custom Types with Core Schema](#custom-types-with-core-schema)
- [Third-Party Type Integration](#third-party-type-integration)

## Standard Library Types

Pydantic validates all common Python types:

```python
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from enum import Enum
from pathlib import Path
from uuid import UUID
from typing import Any
from pydantic import BaseModel

class Everything(BaseModel):
    # Primitives
    name: str
    count: int
    price: float
    active: bool
    raw: bytes

    # Date/time
    created: datetime
    birthday: date
    alarm: time
    duration: timedelta

    # Others
    amount: Decimal
    unique_id: UUID
    config_path: Path
    anything: Any
```

### Collections

```python
from pydantic import BaseModel

class Collections(BaseModel):
    tags: list[str]
    scores: set[int]
    metadata: dict[str, Any]
    coordinates: tuple[float, float]
    frozen_tags: frozenset[str]
    pair: tuple[str, int]           # fixed-length tuple
    variadic: tuple[int, ...]       # variable-length tuple
```

### Enums and Literals

```python
from enum import Enum
from typing import Literal
from pydantic import BaseModel

class Color(str, Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"

class Config(BaseModel):
    color: Color
    mode: Literal["fast", "slow", "auto"]
    level: Literal[1, 2, 3]
```

## Pydantic-Specific Types

```python
from pydantic import (
    BaseModel,
    StrictInt, StrictFloat, StrictStr, StrictBool, StrictBytes,
    PositiveInt, NegativeInt, NonNegativeInt, NonPositiveInt,
    PositiveFloat, NegativeFloat, NonNegativeFloat, NonPositiveFloat,
    FiniteFloat,
    conint, confloat, constr, conlist, conset,
    SecretStr, SecretBytes,
    Json,
    ImportString,
)

class Example(BaseModel):
    # Strict types — no coercion
    strict_id: StrictInt          # "42" rejected
    strict_name: StrictStr        # 42 rejected

    # Constrained numeric types
    age: PositiveInt              # > 0
    offset: NonNegativeInt        # >= 0
    temperature: FiniteFloat      # no inf/nan

    # Secret types — hidden in repr and logs
    api_key: SecretStr
    token: SecretBytes

    # JSON — validates a JSON string, then parses contents
    payload: Json[dict[str, int]]

    # Import path — imports and returns the object
    handler: ImportString
```

### SecretStr Usage

```python
from pydantic import BaseModel, SecretStr

class Config(BaseModel):
    api_key: SecretStr

c = Config(api_key="sk-abc123")
print(c.api_key)                    # SecretStr('**********')
print(c.api_key.get_secret_value()) # sk-abc123
print(c.model_dump())               # {'api_key': SecretStr('**********')}
print(c.model_dump_json())          # {"api_key":"**********"}
```

### Json Type

```python
from pydantic import BaseModel, Json

class Request(BaseModel):
    payload: Json[list[int]]

r = Request(payload='[1, 2, 3]')
print(r.payload)       # [1, 2, 3] (parsed list)
print(type(r.payload)) # <class 'list'>
```

## Network Types

Install `pydantic[email]` for email validation:

```python
from pydantic import (
    BaseModel,
    AnyUrl, AnyHttpUrl, HttpUrl, AnyWebsocketUrl,
    FileUrl, FtpUrl, PostgresDsn, RedisDsn,
    MongoDsn, KafkaDsn, AmqpDsn,
    EmailStr, NameEmail,
    IPvAnyAddress, IPvAnyInterface, IPvAnyNetwork,
)

class Service(BaseModel):
    url: HttpUrl
    ws: AnyWebsocketUrl
    db: PostgresDsn
    cache: RedisDsn
    email: EmailStr
    ip: IPvAnyAddress

s = Service(
    url="https://example.com/api",
    ws="wss://example.com/ws",
    db="postgresql://user:pass@localhost/db",
    cache="redis://localhost:6379/0",
    email="user@example.com",
    ip="192.168.1.1",
)
```

## Constrained Types

Create constrained types using factory functions:

```python
from pydantic import BaseModel, conint, confloat, constr, conlist

class Constrained(BaseModel):
    age: conint(gt=0, lt=150)
    rate: confloat(ge=0, le=1)
    slug: constr(pattern=r"^[a-z0-9-]+$", min_length=1, max_length=50)
    tags: conlist(str, min_length=1, max_length=10)
```

Prefer `Annotated` + `Field()` over `con*()` functions in modern code:

```python
from typing import Annotated
from pydantic import BaseModel, Field

Age = Annotated[int, Field(gt=0, lt=150)]
Rate = Annotated[float, Field(ge=0, le=1)]
Slug = Annotated[str, Field(pattern=r"^[a-z0-9-]+$", min_length=1)]

class Modern(BaseModel):
    age: Age
    rate: Rate
    slug: Slug
```

## Custom Types with Annotated

The recommended way to create reusable validated types:

```python
from typing import Annotated
from pydantic import AfterValidator, PlainSerializer, WithJsonSchema, BaseModel

def must_be_positive(v: float) -> float:
    if v <= 0:
        raise ValueError("must be positive")
    return v

def round_to_cents(v: float) -> float:
    return round(v, 2)

USD = Annotated[
    float,
    AfterValidator(must_be_positive),
    AfterValidator(round_to_cents),
    PlainSerializer(lambda x: f"${x:.2f}", return_type=str),
    WithJsonSchema({"type": "number", "exclusiveMinimum": 0}),
]

class Invoice(BaseModel):
    amount: USD
    tax: USD

inv = Invoice(amount=42.567, tax=3.141)
print(inv.amount)              # 42.57
print(inv.model_dump_json())   # {"amount":"$42.57","tax":"$3.14"}
```

### Generic Annotated Types

```python
from typing import Annotated, TypeVar
from annotated_types import Len

T = TypeVar("T")
ShortList = Annotated[list[T], Len(max_length=5)]

class Model(BaseModel):
    items: ShortList[int]

Model(items=[1, 2, 3])          # OK
Model(items=list(range(100)))   # ValidationError
```

## Named Type Aliases

Create types that appear as `$defs` in JSON Schema (v2.11+):

```python
from typing import Annotated
from typing_extensions import TypeAliasType
from annotated_types import Gt
from pydantic import BaseModel

PositiveIntList = TypeAliasType(
    "PositiveIntList",
    list[Annotated[int, Gt(0)]],
)

class Model(BaseModel):
    x: PositiveIntList
    y: PositiveIntList

# JSON Schema will reference PositiveIntList as a $def
```

Python 3.12+ `type` statement:

```python
type PositiveIntList = list[Annotated[int, Gt(0)]]
```

## Custom Types with Core Schema

For advanced customization, implement `__get_pydantic_core_schema__`:

```python
from typing import Any
from pydantic_core import CoreSchema, core_schema
from pydantic import BaseModel, GetCoreSchemaHandler

class Username(str):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls._validate,
            core_schema.str_schema(min_length=3, max_length=50),
        )

    @classmethod
    def _validate(cls, value: str) -> "Username":
        if not value.isalnum():
            raise ValueError("username must be alphanumeric")
        return cls(value.lower())

class User(BaseModel):
    username: Username
```

## Third-Party Type Integration

Wrap external types with an annotation marker:

```python
from typing import Annotated, Any
from pydantic_core import core_schema
from pydantic import BaseModel, GetCoreSchemaHandler, GetPydanticSchema

class ExternalThing:
    def __init__(self, value: int):
        self.value = value

class Model(BaseModel):
    thing: Annotated[
        ExternalThing,
        GetPydanticSchema(
            lambda tp, handler: core_schema.no_info_after_validator_function(
                lambda v: ExternalThing(v),
                core_schema.int_schema(),
                serialization=core_schema.plain_serializer_function_ser_schema(
                    lambda x: x.value
                ),
            )
        ),
    ]

m = Model(thing=42)
print(m.thing.value)       # 42
print(m.model_dump())      # {'thing': 42}
```

## Common Pitfalls

1. **Type coercion happens by default** — `"42"` becomes `42` for `int` fields; use `StrictInt` or strict mode to prevent
2. **`Optional[X]` means `X | None`**, not "field is optional" — add a default to make it optional
3. **`SecretStr` hides values in repr/JSON** but stores the actual value in memory
4. **`Json[T]` expects a JSON string** and parses it, not a pre-parsed value
5. **`ImportString` actually imports** the module — be careful with untrusted input
6. **Network types return `Url` objects**, not plain strings — call `str()` if needed
