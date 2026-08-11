# Unions & Discriminators

> Source: [Pydantic Unions](https://docs.pydantic.dev/latest/concepts/unions/)

## Table of Contents
- [Union Basics](#union-basics)
- [Smart Mode (Default)](#smart-mode-default)
- [Left-to-Right Mode](#left-to-right-mode)
- [Discriminated Unions](#discriminated-unions)
- [Callable Discriminators](#callable-discriminators)
- [Nested Discriminated Unions](#nested-discriminated-unions)
- [Tags for Error Messages](#tags-for-error-messages)

## Union Basics

Union types accept any one of their member types:

```python
from pydantic import BaseModel

class Item(BaseModel):
    id: int | str                    # int or str
    value: int | float | None = None # int, float, or None
```

The challenge: when multiple members could match, which one does Pydantic choose?

## Smart Mode (Default)

Pydantic v2's default `union_mode='smart'` picks the best match using two metrics:

1. **Valid fields count** — for models/dataclasses, the member with the most valid fields wins
2. **Exactness** — prefers exact type match > strict validation > lax validation

```python
from uuid import UUID
from pydantic import BaseModel

class Model(BaseModel):
    value: int | str | UUID

# Exact int match preferred
Model(value=42)            # value=42 (int, not str)

# Exact str match
Model(value="hello")       # value='hello' (str, not coerced to int)

# UUID parsed from string
Model(value="550e8400-e29b-41d4-a716-446655440000")  # UUID
```

For model unions, smart mode counts valid fields:

```python
from pydantic import BaseModel

class Cat(BaseModel):
    name: str
    meows: int

class Dog(BaseModel):
    name: str
    barks: float
    breed: str

class Pet(BaseModel):
    animal: Cat | Dog

# Dog has more matching fields
Pet(animal={"name": "Rex", "barks": 3.0, "breed": "Lab"})
# animal=Dog(...)
```

## Left-to-Right Mode

Try each union member in order; first match wins:

```python
from pydantic import BaseModel, Field

class Model(BaseModel):
    value: int | str = Field(union_mode="left_to_right")

# int is tried first, "42" coerced to 42
Model(value="42")   # value=42 (int!)

# Swap order to prefer str
class Model2(BaseModel):
    value: str | int = Field(union_mode="left_to_right")

Model2(value="42")  # value='42' (str, tried first)
```

Use left-to-right when you need deterministic ordering or specific coercion behavior.

## Discriminated Unions

The recommended approach. Uses a discriminator field to select the correct member without trying each one:

```python
from typing import Literal, Union
from pydantic import BaseModel, Field

class Cat(BaseModel):
    pet_type: Literal["cat"]
    name: str
    meows: int

class Dog(BaseModel):
    pet_type: Literal["dog"]
    name: str
    barks: float

class Fish(BaseModel):
    pet_type: Literal["fish"]
    name: str
    fins: int

class Pet(BaseModel):
    animal: Union[Cat, Dog, Fish] = Field(discriminator="pet_type")

pet = Pet.model_validate({"animal": {"pet_type": "dog", "name": "Rex", "barks": 3.0}})
print(type(pet.animal))  # <class 'Dog'>
```

Benefits over untagged unions:
- **Faster** — only one member is validated, not all
- **Better errors** — error says which discriminator value was wrong
- **Deterministic** — no ambiguity about which member matches

### Using Annotated Syntax

```python
from typing import Annotated, Literal, Union
from pydantic import BaseModel, Field

class Cat(BaseModel):
    kind: Literal["cat"]
    meows: int

class Dog(BaseModel):
    kind: Literal["dog"]
    barks: float

Animal = Annotated[Union[Cat, Dog], Field(discriminator="kind")]

class Zoo(BaseModel):
    animals: list[Animal]
```

## Callable Discriminators

When union members have differently-named discriminator fields, use a callable:

```python
from typing import Annotated, Any, Literal, Union
from pydantic import BaseModel, Discriminator, Tag

class ApplePie(BaseModel):
    fruit: Literal["apple"] = "apple"
    bake_time: int

class PumpkinPie(BaseModel):
    filling: Literal["pumpkin"] = "pumpkin"
    bake_time: int

class CherryCake(BaseModel):
    fruit: Literal["cherry"] = "cherry"
    layers: int

def get_dessert_type(v: Any) -> str:
    if isinstance(v, dict):
        if "filling" in v:
            return v["filling"]
        return v.get("fruit", "unknown")
    return getattr(v, "filling", getattr(v, "fruit", "unknown"))

Dessert = Annotated[
    Union[
        Annotated[ApplePie, Tag("apple")],
        Annotated[PumpkinPie, Tag("pumpkin")],
        Annotated[CherryCake, Tag("cherry")],
    ],
    Discriminator(get_dessert_type),
]

class Menu(BaseModel):
    desserts: list[Dessert]

menu = Menu.model_validate({
    "desserts": [
        {"fruit": "apple", "bake_time": 45},
        {"filling": "pumpkin", "bake_time": 60},
        {"fruit": "cherry", "layers": 3},
    ]
})
```

The callable discriminator must handle both `dict` inputs (validation) and model instances (serialization).

## Nested Discriminated Unions

Compose multiple levels of discriminators:

```python
from typing import Annotated, Literal, Union
from pydantic import BaseModel, Field

class BlackCat(BaseModel):
    pet_type: Literal["cat"]
    color: Literal["black"]
    name: str

class WhiteCat(BaseModel):
    pet_type: Literal["cat"]
    color: Literal["white"]
    name: str

# Inner union discriminated by color
Cat = Annotated[Union[BlackCat, WhiteCat], Field(discriminator="color")]

class Dog(BaseModel):
    pet_type: Literal["dog"]
    name: str
    breed: str

# Outer union discriminated by pet_type
Pet = Annotated[Union[Cat, Dog], Field(discriminator="pet_type")]

class Model(BaseModel):
    pet: Pet

m = Model.model_validate({
    "pet": {"pet_type": "cat", "color": "black", "name": "Salem"}
})
print(type(m.pet))  # <class 'BlackCat'>
```

## Tags for Error Messages

Use `Tag` to label union members for clearer error messages:

```python
from typing import Annotated, Union
from pydantic import Tag, TypeAdapter

DoubledList = Annotated[list[int], Tag("DoubledList")]
StringsMap = Annotated[dict[str, str], Tag("StringsMap")]

adapter = TypeAdapter(Union[DoubledList, StringsMap])

try:
    adapter.validate_python("invalid")
except Exception as e:
    print(e)  # error references "DoubledList" and "StringsMap" by name
```

### Custom Error Messages on Discriminator

```python
from pydantic import Discriminator

Discriminator(
    my_function,
    custom_error_type="invalid_discriminator",
    custom_error_message="Expected 'cat' or 'dog', got '{discriminator}'",
    custom_error_context={"discriminator": "..."},
)
```

## Patterns and Best Practices

### Event System Pattern

```python
from typing import Annotated, Literal, Union
from pydantic import BaseModel, Field

class UserCreated(BaseModel):
    event: Literal["user.created"]
    user_id: int
    email: str

class UserDeleted(BaseModel):
    event: Literal["user.deleted"]
    user_id: int

class OrderPlaced(BaseModel):
    event: Literal["order.placed"]
    order_id: int
    total: float

Event = Annotated[
    Union[UserCreated, UserDeleted, OrderPlaced],
    Field(discriminator="event"),
]

class WebhookPayload(BaseModel):
    events: list[Event]
```

### API Response Pattern

```python
from typing import Annotated, Literal, Union
from pydantic import BaseModel, Field

class SuccessResponse(BaseModel):
    status: Literal["success"]
    data: dict

class ErrorResponse(BaseModel):
    status: Literal["error"]
    message: str
    code: int

ApiResponse = Annotated[
    Union[SuccessResponse, ErrorResponse],
    Field(discriminator="status"),
]
```

## Common Pitfalls

1. **Use discriminated unions** whenever possible — they're faster and produce clearer errors
2. **Smart mode may surprise** — `"42"` could match `int` or `str` depending on exactness scoring
3. **Callable discriminators must handle both dict and model inputs**
4. **Avoid single-variant discriminated unions** — `Union[Cat]` is redundant
5. **Discriminator field must use `Literal`** type for string discriminators
6. **Nested models in unions** can conflict if they have similar field shapes
