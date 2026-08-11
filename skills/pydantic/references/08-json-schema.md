# JSON Schema

> Source: [Pydantic JSON Schema](https://docs.pydantic.dev/latest/concepts/json_schema/)

## Table of Contents
- [Generating Schemas](#generating-schemas)
- [Schema Modes](#schema-modes)
- [Field-Level Customization](#field-level-customization)
- [Model-Level Customization](#model-level-customization)
- [WithJsonSchema](#withjsonschema)
- [GenerateJsonSchema Class](#generatejsonschema-class)
- [Multi-Model Schemas](#multi-model-schemas)
- [Ref Template Customization](#ref-template-customization)
- [Type Mapping Reference](#type-mapping-reference)

## Generating Schemas

### From a Model

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    id: int
    name: str = Field(min_length=1, max_length=100)
    email: str | None = None

schema = User.model_json_schema()
# {
#   'properties': {
#     'id': {'title': 'Id', 'type': 'integer'},
#     'name': {'maxLength': 100, 'minLength': 1, 'title': 'Name', 'type': 'string'},
#     'email': {'anyOf': [{'type': 'string'}, {'type': 'null'}],
#               'default': None, 'title': 'Email'}
#   },
#   'required': ['id', 'name'],
#   'title': 'User',
#   'type': 'object'
# }
```

### From TypeAdapter

```python
from pydantic import TypeAdapter

ta = TypeAdapter(list[int])
print(ta.json_schema())
# {'items': {'type': 'integer'}, 'type': 'array'}
```

## Schema Modes

Control whether the schema describes input validation or output serialization:

```python
from decimal import Decimal
from pydantic import BaseModel

class Price(BaseModel):
    amount: Decimal

# Validation schema — accepts numbers or numeric strings
Price.model_json_schema(mode="validation")

# Serialization schema — outputs strings
Price.model_json_schema(mode="serialization")
```

This matters for types like `Decimal` (validated as number, serialized as string) and computed fields (only in serialization schema).

## Field-Level Customization

```python
from pydantic import BaseModel, Field

class Product(BaseModel):
    name: str = Field(
        title="Product Name",
        description="The display name of the product",
        examples=["Widget Pro", "Gadget X"],
        json_schema_extra={"x-custom-field": "value"},
    )
    price: float = Field(
        gt=0,
        description="Price in USD",
        examples=[9.99, 29.99],
    )
    sku: str = Field(
        pattern=r"^[A-Z]{3}-\d{4}$",
        description="Stock keeping unit",
    )
```

### Programmatic Title Generation

```python
from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo

def screaming_title(name: str, info: FieldInfo) -> str:
    return name.upper().replace("_", " ")

class Model(BaseModel):
    user_name: str = Field(field_title_generator=screaming_title)
    # JSON Schema title: "USER NAME"
```

## Model-Level Customization

```python
from pydantic import BaseModel, ConfigDict

class ApiResponse(BaseModel):
    model_config = ConfigDict(
        title="API Response",
        json_schema_extra={
            "examples": [{"data": "hello", "status": 200}],
            "x-api-version": "2.0",
        },
    )
    data: str
    status: int
```

### Using a Callable

```python
from pydantic import BaseModel, ConfigDict

def add_description(schema: dict) -> None:
    schema["description"] = "Auto-generated API schema"

class Model(BaseModel):
    model_config = ConfigDict(json_schema_extra=add_description)
    value: int
```

### json_schema_extra Merging (v2.9+)

When using `Annotated`, dict-valued `json_schema_extra` merges additively:

```python
from typing import Annotated
from pydantic import Field, TypeAdapter

MyType = Annotated[int, Field(json_schema_extra={"key1": "val1"})]
ta = TypeAdapter(Annotated[MyType, Field(json_schema_extra={"key2": "val2"})])
print(ta.json_schema())
# {'key1': 'val1', 'key2': 'val2', 'type': 'integer'}
```

## WithJsonSchema

Override the entire JSON Schema for a type:

```python
from typing import Annotated
from pydantic import BaseModel, WithJsonSchema

CustomId = Annotated[
    int,
    WithJsonSchema(
        {"type": "integer", "minimum": 1, "examples": [1, 42, 100]}
    ),
]

class Item(BaseModel):
    id: CustomId
```

Mode-specific overrides:

```python
from pydantic import WithJsonSchema

MyField = Annotated[
    complex_type,
    WithJsonSchema(
        {"type": "object"},                  # validation schema
        mode="serialization",
    ),
]
```

### SkipJsonSchema

Exclude a field or type from generated schemas:

```python
from pydantic import BaseModel
from pydantic.json_schema import SkipJsonSchema

class Internal(BaseModel):
    public: str
    private: SkipJsonSchema[str] = "hidden"
```

## GenerateJsonSchema Class

Subclass for global schema generation control:

```python
from pydantic import BaseModel
from pydantic.json_schema import GenerateJsonSchema

class CustomSchemaGenerator(GenerateJsonSchema):
    def generate(self, schema, mode="validation"):
        json_schema = super().generate(schema, mode=mode)
        json_schema["$schema"] = self.schema_dialect
        json_schema["x-generated-by"] = "pydantic"
        return json_schema

class User(BaseModel):
    name: str

schema = User.model_json_schema(schema_generator=CustomSchemaGenerator)
```

### Preserve Field Order

```python
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaValue
from typing import Optional

class OrderPreservingSchema(GenerateJsonSchema):
    def sort(self, value: JsonSchemaValue, parent_key: Optional[str] = None) -> JsonSchemaValue:
        return value  # no sorting — preserve definition order

schema = Model.model_json_schema(schema_generator=OrderPreservingSchema)
```

### Handle Invalid Types

```python
from pydantic_core import PydanticOmit, core_schema
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaValue

class LenientSchema(GenerateJsonSchema):
    def handle_invalid_for_json_schema(
        self, schema: core_schema.CoreSchema, error_info: str
    ) -> JsonSchemaValue:
        raise PydanticOmit  # silently omit un-serializable fields
```

## Multi-Model Schemas

Generate a combined schema with shared `$defs`:

```python
from pydantic import BaseModel
from pydantic.json_schema import models_json_schema

class User(BaseModel):
    name: str

class Product(BaseModel):
    title: str
    price: float

class Order(BaseModel):
    user: User
    items: list[Product]

_, top_schema = models_json_schema(
    [(User, "validation"), (Product, "validation"), (Order, "validation")],
    title="My API Schema",
)
```

## Ref Template Customization

Control `$ref` format for OpenAPI compatibility:

```python
from pydantic import BaseModel, TypeAdapter

class Address(BaseModel):
    city: str

class User(BaseModel):
    address: Address

ta = TypeAdapter(User)
schema = ta.json_schema(ref_template="#/components/schemas/{model}")
# References become: "$ref": "#/components/schemas/Address"
```

## Type Mapping Reference

| Python Type | JSON Schema |
|-------------|-------------|
| `None` | `{"type": "null"}` |
| `bool` | `{"type": "boolean"}` |
| `int` | `{"type": "integer"}` |
| `float` | `{"type": "number"}` |
| `str` | `{"type": "string"}` |
| `bytes` | `{"type": "string", "format": "base64"}` |
| `list[T]` | `{"type": "array", "items": ...}` |
| `set[T]` | `{"type": "array", "items": ..., "uniqueItems": true}` |
| `dict[K, V]` | `{"type": "object"}` |
| `tuple[A, B]` | `{"type": "array", "prefixItems": [...]}` |
| `datetime` | `{"type": "string", "format": "date-time"}` |
| `date` | `{"type": "string", "format": "date"}` |
| `UUID` | `{"type": "string", "format": "uuid"}` |
| `Decimal` | `{"type": "number"}` (validation) / `{"type": "string"}` (serialization) |
| `EmailStr` | `{"type": "string", "format": "email"}` |
| `HttpUrl` | `{"type": "string", "format": "uri"}` |
| `SecretStr` | `{"type": "string", "writeOnly": true}` |
| `Enum` | `{"enum": [...]}` |
| `Literal["a", "b"]` | `{"enum": ["a", "b"]}` |
| `Union[A, B]` | `{"anyOf": [...]}` |
| `X \| None` | `{"anyOf": [..., {"type": "null"}]}` |

## Specification Compliance

Generated schemas conform to:
- JSON Schema Draft 2020-12
- OpenAPI Specification v3.1.0

## Common Pitfalls

1. **Validation vs serialization schemas differ** for `Decimal`, `SecretStr`, computed fields
2. **`json_schema_extra` callable** receives the schema dict and should mutate it in place
3. **`ref_template`** only affects `$ref` format, not the schema structure
4. **Nested models generate `$defs`** — don't flatten them manually
5. **`SkipJsonSchema` hides the field** from schema but it's still validated and serialized
