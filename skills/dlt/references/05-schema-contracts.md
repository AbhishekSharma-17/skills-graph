# dlt Schema Contracts

> Source: https://dlthub.com/docs/general-usage/schema-contracts | dlt v1.29.1

## Table of Contents
- [Overview](#overview)
- [Contract Modes](#contract-modes)
- [Schema Entities](#schema-entities)
- [Applying Contracts](#applying-contracts)
- [Specification Formats](#specification-formats)
- [Pydantic Model Integration](#pydantic-model-integration)
- [DataFrames and Arrow Tables](#dataframes-and-arrow-tables)
- [Exception Handling](#exception-handling)
- [Common Patterns](#common-patterns)

## Overview

Schema contracts control how dlt handles data that doesn't match the existing schema. They prevent unexpected schema changes from breaking downstream consumers and enforce data quality at the pipeline level.

Contracts govern three aspects of schema evolution:
- **tables** — can new tables be created?
- **columns** — can new columns be added to existing tables?
- **data_type** — can column types change?

## Contract Modes

| Mode | Behavior |
|------|----------|
| `evolve` | No constraints — new tables, columns, and type changes allowed (default) |
| `freeze` | Raises exception if data doesn't fit existing schema; no data loaded |
| `discard_row` | Drops entire rows that don't adhere to schema |
| `discard_value` | Drops non-conforming values from rows; row still loaded without that data |

## Schema Entities

| Entity | What it controls |
|--------|-----------------|
| `tables` | Creation of new tables not in current schema |
| `columns` | Creation of new columns on existing tables |
| `data_type` | Changes to column properties (data_type, nullable, precision, scale, timezone) |

## Applying Contracts

### Source level
```python
@dlt.source(schema_contract={"columns": "freeze", "data_type": "freeze"})
def frozen_source():
    return [items(), other_items()]
```

### Resource level
```python
@dlt.resource(schema_contract={"tables": "evolve", "columns": "freeze"})
def items():
    yield from get_items()
```

### Pipeline run level (overrides all)
```python
pipeline.run(my_source(), schema_contract="freeze")
```

### Precedence hierarchy
Pipeline run > resource > source. More specific settings override broader ones.

```python
@dlt.resource(schema_contract={"columns": "evolve"})
def items():
    yield from get_items()

@dlt.source(schema_contract={"columns": "freeze", "data_type": "freeze"})
def frozen_source():
    return [items(), other_items()]

# Override everything at run time
pipeline.run(frozen_source(), schema_contract="freeze")
```

## Specification Formats

### Full format (explicit per entity)
```python
schema_contract = {
    "tables": "evolve",
    "columns": "freeze",
    "data_type": "freeze"
}
```

### Shorthand format (same mode for all entities)
```python
schema_contract = "freeze"
# Expands to: {"tables": "freeze", "columns": "freeze", "data_type": "freeze"}
```

## Pydantic Model Integration

When using Pydantic models for schema definition, contracts map to Pydantic's `extra` config:

| Contract mode | Pydantic extra |
|--------------|----------------|
| `evolve` | `extra="allow"` |
| `freeze` | `extra="forbid"` |
| `discard_value` | `extra="ignore"` |
| `discard_row` | `extra="forbid"` (with additional handling) |

Default contract with Pydantic models:
```python
{"tables": "evolve", "columns": "discard_value", "data_type": "freeze"}
```

### Authoritative models
Bypass column and data_type enforcement:

```python
from typing import ClassVar
from pydantic import BaseModel
from dlt.common.libs.pydantic import DltConfig

class MyModel(BaseModel):
    dlt_config: ClassVar[DltConfig] = {"is_authoritative_model": True}
    class Config:
        extra = "forbid"
    id: int
    name: str
```

### Event stream validation with discriminated unions
```python
from typing import ClassVar, Literal, Union
from typing_extensions import Annotated
from pydantic import BaseModel, Field, RootModel
from dlt.common.libs.pydantic import DltConfig

class ClickEvent(BaseModel):
    kind: Literal["click"]
    element_id: str

class PurchaseEvent(BaseModel):
    kind: Literal["purchase"]
    amount: float

EventUnion = Annotated[
    Union[ClickEvent, PurchaseEvent],
    Field(discriminator="kind")
]

class Event(RootModel[EventUnion]):
    dlt_config: ClassVar[DltConfig] = {"is_authoritative_model": True}
```

Dispatch to separate tables:
```python
TABLE_MAP = {"click": "click_events", "purchase": "purchase_events"}

@dlt.resource(
    name="events",
    columns=Event,
    schema_contract={"data_type": "discard_row"},
)
def event_stream():
    for item in items:
        yield dlt.mark.with_table_name(item, TABLE_MAP[item["kind"]])
```

## DataFrames and Arrow Tables

Contracts apply identically to Pandas, Polars, and Arrow DataFrames:

| Mode | New column behavior |
|------|-------------------|
| `evolve` | Column allowed; table may be reordered |
| `discard_value` | Column deleted from DataFrame |
| `discard_row` | Rows with problematic column deleted, then column removed |
| `freeze` | Exception raised |

## Exception Handling

Capture validation errors in `freeze` mode:

```python
from dlt.common.schema.exceptions import DataValidationError

try:
    pipeline.run(source())
except PipelineStepFailed as pip_ex:
    if pip_ex.step == "normalize":
        if isinstance(pip_ex.__context__.__context__, DataValidationError):
            err = pip_ex.__context__.__context__
            print(f"Table: {err.table_name}")
            print(f"Column: {err.column_name}")
            print(f"Entity: {err.schema_entity}")
            print(f"Contract: {err.contract_mode}")
```

`DataValidationError` attributes: `schema_name`, `table_name`, `column_name`, `schema_entity`, `contract_mode`, `table_schema`, `schema_contract`, `data_item`.

## Common Patterns

### Production data quality guard
```python
@dlt.source(schema_contract={
    "tables": "freeze",      # No surprise tables
    "columns": "discard_value",  # Drop unknown columns silently
    "data_type": "freeze"    # Type changes are errors
})
def production_source():
    return [users(), orders(), products()]
```

### Flexible development, strict production
```python
contract = "evolve" if dev_mode else {
    "tables": "freeze",
    "columns": "freeze",
    "data_type": "freeze"
}
pipeline.run(source(), schema_contract=contract)
```

### Allow new tables but freeze existing
```python
@dlt.resource(schema_contract={
    "tables": "evolve",       # New tables OK
    "columns": "freeze",      # No new columns on existing tables
    "data_type": "freeze"     # No type changes
})
def dynamic_events():
    yield from get_events()
```

### Discard bad rows, keep good ones
```python
@dlt.resource(schema_contract={
    "tables": "discard_row",
    "columns": "discard_row",
    "data_type": "discard_row"
})
def tolerant_resource():
    yield from get_messy_data()
```

Key behaviors:
- Contracts apply after table/column name normalization
- Resource contracts apply to all root and nested tables within that resource
- `discard_row` operates at table level; nested table violations don't affect parent rows
- New tables allow initial column creation, then revert to specified contract
- Manually pre-created destination tables/columns bypass initial creation checks
