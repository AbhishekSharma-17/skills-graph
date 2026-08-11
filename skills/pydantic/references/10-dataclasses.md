# Dataclasses & TypeAdapter

> Source: [Pydantic Dataclasses](https://docs.pydantic.dev/latest/concepts/dataclasses/) · [TypeAdapter](https://docs.pydantic.dev/latest/concepts/type_adapter/)

## Table of Contents
- [Pydantic Dataclasses](#pydantic-dataclasses)
- [Configuration](#configuration)
- [Validators in Dataclasses](#validators-in-dataclasses)
- [Stdlib Dataclass Integration](#stdlib-dataclass-integration)
- [BaseModel vs Dataclass](#basemodel-vs-dataclass)
- [TypeAdapter](#typeadapter)
- [TypeAdapter Methods](#typeadapter-methods)
- [TypeAdapter Patterns](#typeadapter-patterns)

## Pydantic Dataclasses

Pydantic's `@dataclass` decorator adds validation to standard Python dataclasses:

```python
from datetime import datetime
from pydantic.dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str
    signup_ts: datetime | None = None

user = User(id="42", name="Alice", signup_ts="2026-06-01T12:00:00")
print(user.id)        # 42 (int, coerced)
print(user.signup_ts) # 2026-06-01 12:00:00 (datetime, parsed)
```

Unlike `BaseModel`, Pydantic dataclasses:
- Don't have `model_dump()`, `model_validate()`, or other model methods
- Use `TypeAdapter` for serialization and schema generation
- Support `__post_init__()` lifecycle
- Are more compatible with stdlib dataclass tooling

## Configuration

```python
from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

# Via decorator parameter
@dataclass(config=ConfigDict(strict=True, frozen=True))
class StrictUser:
    name: str
    age: int

# Via class attribute
@dataclass
class FlexibleUser:
    __pydantic_config__ = ConfigDict(extra="allow", validate_assignment=True)
    name: str
    age: int
```

## Validators in Dataclasses

Field and model validators work the same as in `BaseModel`:

```python
from pydantic import field_validator, model_validator
from pydantic.dataclasses import dataclass
from typing_extensions import Self

@dataclass
class Order:
    product: str
    quantity: int
    unit_price: float

    @field_validator("quantity")
    @classmethod
    def must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("quantity must be positive")
        return v

    @model_validator(mode="after")
    def check_total(self) -> Self:
        if self.quantity * self.unit_price > 10000:
            raise ValueError("order total exceeds limit")
        return self
```

### __post_init__ Lifecycle

`__post_init__()` runs between before and after validators:

```python
from pydantic.dataclasses import dataclass

@dataclass
class Item:
    name: str
    slug: str = ""

    def __post_init__(self):
        if not self.slug:
            self.slug = self.name.lower().replace(" ", "-")

item = Item(name="Cool Widget")
print(item.slug)  # "cool-widget"
```

## Field Definitions

Combine Pydantic `Field()` with stdlib `field()`:

```python
import dataclasses
from pydantic import Field
from pydantic.dataclasses import dataclass

@dataclass
class Product:
    name: str = Field(min_length=1, max_length=100)
    tags: list[str] = dataclasses.field(default_factory=list)
    price: float = Field(gt=0, description="Price in USD")
```

### Init-only and Keyword-only Fields

```python
from pydantic import Field
from pydantic.dataclasses import dataclass

@dataclass
class Config:
    name: str
    verbose: bool = Field(init_var=True, default=False)  # init-only
    debug: bool = Field(kw_only=True, default=False)     # keyword-only
```

## Stdlib Dataclass Integration

Pydantic validates fields from inherited stdlib dataclasses:

```python
import dataclasses
import pydantic.dataclasses

@dataclasses.dataclass
class Base:
    x: int

@pydantic.dataclasses.dataclass
class Child(Base):
    y: str

child = Child(x="42", y="hello")
print(child.x)  # 42 (validated and coerced)
```

### Check Type

```python
from pydantic.dataclasses import is_pydantic_dataclass

@dataclass
class MyDC:
    x: int

print(is_pydantic_dataclass(MyDC))  # True
```

## BaseModel vs Dataclass

| Feature | BaseModel | Pydantic Dataclass |
|---------|-----------|-------------------|
| `model_dump()` | Yes | No (use TypeAdapter) |
| `model_validate()` | Yes | No (use TypeAdapter) |
| `model_json_schema()` | Yes | No (use TypeAdapter) |
| `model_copy()` | Yes | No |
| `model_construct()` | Yes | No |
| Validators | Yes | Yes |
| Configuration | Yes | Yes |
| `__post_init__` | No | Yes |
| stdlib compatibility | Limited | High |
| JSON Schema | Built-in | Via TypeAdapter |
| Extra fields in serialization | Yes | No |
| Generic support | Full | Limited |
| Hashable when frozen | Yes | Yes |

**Use BaseModel** for API schemas, complex validation, serialization-heavy code.

**Use dataclasses** for lightweight validated data containers, interop with existing dataclass code.

## TypeAdapter

`TypeAdapter` applies Pydantic validation to any type without creating a model:

```python
from pydantic import TypeAdapter

# Validate a list of ints
ta = TypeAdapter(list[int])
result = ta.validate_python(["1", "2", "3"])
print(result)  # [1, 2, 3]

# Validate a dict
ta = TypeAdapter(dict[str, int])
result = ta.validate_python({"a": "1", "b": "2"})
print(result)  # {'a': 1, 'b': 2}
```

### With TypedDict

```python
from typing_extensions import TypedDict
from pydantic import TypeAdapter

class UserDict(TypedDict):
    name: str
    age: int

ta = TypeAdapter(list[UserDict])
users = ta.validate_python([
    {"name": "Alice", "age": "30"},
    {"name": "Bob", "age": "25"},
])
print(users)  # [{'name': 'Alice', 'age': 30}, {'name': 'Bob', 'age': 25}]
```

### With Dataclasses

```python
from pydantic import TypeAdapter
from pydantic.dataclasses import dataclass

@dataclass
class Item:
    name: str
    price: float

ta = TypeAdapter(Item)
item = ta.validate_python({"name": "Widget", "price": "9.99"})
print(item)  # Item(name='Widget', price=9.99)

ta.dump_python(item)       # {'name': 'Widget', 'price': 9.99}
ta.dump_json(item)         # b'{"name":"Widget","price":9.99}'
print(ta.json_schema())   # JSON Schema dict
```

## TypeAdapter Methods

```python
from pydantic import TypeAdapter

ta = TypeAdapter(list[int])

# Validation
ta.validate_python([1, "2", 3])           # from Python objects
ta.validate_json(b'[1, 2, 3]')           # from JSON bytes/str
ta.validate_strings({"0": "1"})           # from string values

# Serialization
ta.dump_python([1, 2, 3])                 # to Python objects
ta.dump_json([1, 2, 3])                   # to JSON bytes (not str!)

# Schema
ta.json_schema()                          # JSON Schema dict
ta.json_schema(mode="serialization")      # serialization schema
```

Note: `dump_json()` returns `bytes`, not `str` (unlike `model_dump_json()`).

## TypeAdapter Patterns

### Reuse Instances (Performance)

```python
from pydantic import TypeAdapter

# Create once, reuse many times
int_list_adapter = TypeAdapter(list[int])

for raw_data in data_stream:
    validated = int_list_adapter.validate_python(raw_data)
```

Schema building has non-trivial overhead — don't create `TypeAdapter` instances in loops.

### Deferred Building

```python
from pydantic import ConfigDict, TypeAdapter

ta = TypeAdapter("MyType", config=ConfigDict(defer_build=True))

# Define the type later
MyType = int

# Explicitly rebuild
ta.rebuild()
result = ta.validate_python("42")  # 42
```

### Validate Function Arguments

```python
from pydantic import validate_call

@validate_call
def greet(name: str, age: int) -> str:
    return f"Hello {name}, age {age}"

greet("Alice", "30")  # age coerced to 30
greet("Alice", "abc") # ValidationError
```

`@validate_call` uses `TypeAdapter` internally for each argument.

## Common Pitfalls

1. **Pydantic dataclasses lack model methods** — use `TypeAdapter` for `dump_python/json` and `json_schema`
2. **Don't create TypeAdapter in loops** — schema building is expensive; create once and reuse
3. **`dump_json` returns bytes**, not str — call `.decode()` if you need a string
4. **TypeAdapter should not replace RootModel** for use as field annotations in other models
5. **Generic dataclasses** don't validate type parameters — wrap with TypeAdapter
6. **`__post_init__` runs between before and after validators** — order matters
