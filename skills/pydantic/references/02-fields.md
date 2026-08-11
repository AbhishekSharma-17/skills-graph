# Fields

> Source: [Pydantic Fields](https://docs.pydantic.dev/latest/concepts/fields/)

## Table of Contents
- [Field Function](#field-function)
- [Default Values](#default-values)
- [Default Factory](#default-factory)
- [Constraints](#constraints)
- [The Annotated Pattern](#the-annotated-pattern)
- [Computed Fields](#computed-fields)
- [Frozen Fields](#frozen-fields)
- [Excluding Fields](#excluding-fields)
- [Deprecated Fields](#deprecated-fields)
- [Field Representation](#field-representation)
- [Discriminator Fields](#discriminator-fields)
- [JSON Schema Customization](#json-schema-customization)
- [Inspecting Fields](#inspecting-fields)

## Field Function

`Field()` customizes field behavior, constraints, and metadata:

```python
from pydantic import BaseModel, Field

class Product(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    price: float = Field(gt=0, description="Price in USD")
    quantity: int = Field(default=0, ge=0)
```

`Field()` assigned to an annotated attribute acts as metadata, not as a default value. A field with `Field()` but no `default` is still required.

## Default Values

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    name: str = "John Doe"              # inline default
    age: int = Field(default=25)        # Field default
    role: str | None = None             # nullable with None default
```

## Default Factory

Use `default_factory` for dynamic defaults:

```python
from uuid import uuid4
from datetime import datetime
from pydantic import BaseModel, Field

class Record(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    created_at: datetime = Field(default_factory=datetime.now)
    tags: list[str] = Field(default_factory=list)
```

Factories can accept already-validated data (field order matters):

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    email: str
    username: str = Field(
        default_factory=lambda data: data["email"].split("@")[0]
    )

u = User(email="alice@example.com")
print(u.username)  # "alice"
```

### Validate Default Values

```python
from pydantic import BaseModel, Field

class Config(BaseModel):
    retries: int = Field(default=3, ge=1, le=10, validate_default=True)
```

Pydantic deep-copies mutable defaults, so shared state bugs don't happen:

```python
class Model(BaseModel):
    items: list[int] = []

m1 = Model()
m1.items.append(1)
m2 = Model()
print(m2.items)  # [] — independent copy
```

## Constraints

### Numeric Constraints

```python
from pydantic import BaseModel, Field
from decimal import Decimal

class Payment(BaseModel):
    amount: float = Field(gt=0)              # > 0
    tax_rate: float = Field(ge=0, le=1)      # 0 <= x <= 1
    quantity: int = Field(gt=0, lt=1000)     # 0 < x < 1000
    price: Decimal = Field(
        max_digits=10, decimal_places=2      # Decimal precision
    )
    multiple: int = Field(multiple_of=5)     # must be multiple of 5
```

### String Constraints

```python
class Profile(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    slug: str = Field(pattern=r"^[a-z0-9-]+$")
    bio: str = Field(default="", max_length=500)
```

### Collection Constraints

```python
class Config(BaseModel):
    tags: list[str] = Field(min_length=1, max_length=10)
    scores: set[int] = Field(min_length=1)
```

## The Annotated Pattern

Using `Annotated` separates type from metadata, enabling reusable constrained types:

```python
from typing import Annotated
from pydantic import BaseModel, Field

PositiveInt = Annotated[int, Field(gt=0)]
ShortStr = Annotated[str, Field(max_length=100)]
Email = Annotated[str, Field(pattern=r"^[\w.-]+@[\w.-]+\.\w+$")]

class User(BaseModel):
    id: PositiveInt
    name: ShortStr
    email: Email
```

Annotated types can be nested in containers:

```python
class Order(BaseModel):
    quantities: list[PositiveInt]     # validates each item > 0
```

## Computed Fields

Properties included in serialization output via `@computed_field`:

```python
from pydantic import BaseModel, computed_field

class Rectangle(BaseModel):
    width: float
    height: float

    @computed_field
    @property
    def area(self) -> float:
        return self.width * self.height

r = Rectangle(width=3, height=4)
print(r.area)                # 12.0
print(r.model_dump())       # {'width': 3.0, 'height': 4.0, 'area': 12.0}
print(r.model_dump_json())  # includes area
```

Computed fields:
- Appear in `model_dump()` and `model_dump_json()`
- Appear in JSON Schema (serialization mode) as read-only
- Are NOT validated by Pydantic
- Can be marked `deprecated`
- Can use `repr=False` to hide from string representation

```python
from pydantic import BaseModel, computed_field

class User(BaseModel):
    first_name: str
    last_name: str

    @computed_field
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
```

## Frozen Fields

Prevent individual fields from being reassigned:

```python
from pydantic import BaseModel, Field

class Config(BaseModel):
    api_key: str = Field(frozen=True)
    debug: bool = False

c = Config(api_key="secret", debug=True)
c.debug = False       # OK
c.api_key = "new"     # raises ValidationError: Field is frozen
```

## Excluding Fields

Remove fields from serialization output:

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    name: str
    password: str = Field(exclude=True)
    internal_id: int = Field(exclude=True)

u = User(name="Alice", password="secret", internal_id=42)
print(u.model_dump())  # {'name': 'Alice'}
```

Conditional exclusion (v2.12+):

```python
class Config(BaseModel):
    name: str
    debug_info: str | None = Field(
        default=None,
        exclude_if=lambda v: v is None
    )
```

## Deprecated Fields

Mark fields as deprecated with warnings:

```python
from pydantic import BaseModel, Field

class Config(BaseModel):
    new_setting: str
    old_setting: str = Field(
        default="",
        deprecated="Use 'new_setting' instead"
    )

c = Config(new_setting="value", old_setting="old")
# Accessing c.old_setting triggers deprecation warning
```

## Field Representation

Control `repr()` output:

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    name: str = Field(repr=True)       # included in repr (default)
    password: str = Field(repr=False)  # hidden from repr

print(User(name="Alice", password="secret"))
# User(name='Alice')
```

## Discriminator Fields

For union type discrimination (see [Unions](09-unions.md)):

```python
from typing import Literal, Union
from pydantic import BaseModel, Field

class Cat(BaseModel):
    pet_type: Literal["cat"]
    meows: int

class Dog(BaseModel):
    pet_type: Literal["dog"]
    barks: float

class Pet(BaseModel):
    animal: Union[Cat, Dog] = Field(discriminator="pet_type")
```

## JSON Schema Customization

```python
from pydantic import BaseModel, Field

class Item(BaseModel):
    name: str = Field(
        title="Item Name",
        description="The name of the item",
        examples=["Widget", "Gadget"],
        json_schema_extra={"x-custom": "value"},
    )
```

## Inspecting Fields

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    name: str = Field(alias="username", gt=0)

info = User.model_fields["name"]
print(info.annotation)   # <class 'str'>
print(info.alias)         # 'username'
print(info.is_required()) # True
print(info.metadata)      # constraint metadata
```

## Common Pitfalls

1. **`Field()` is metadata, not a default** — `name: str = Field(min_length=1)` is still required
2. **`default_factory` data argument** relies on field definition order
3. **`exclude=True`** removes from `model_dump()` but the field is still accessible via attribute
4. **Computed fields are not validated** — Pydantic trusts the property return value
5. **`frozen=True` on Field** prevents reassignment but doesn't prevent mutation of mutable values
