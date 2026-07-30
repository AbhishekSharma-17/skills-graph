# dlt Sources

> Source: https://dlthub.com/docs/general-usage/source | dlt v1.29.1

## Table of Contents
- [Source Basics](#source-basics)
- [Creating Sources](#creating-sources)
- [Dynamic Resource Creation](#dynamic-resource-creation)
- [Resource Selection](#resource-selection)
- [Source Configuration](#source-configuration)
- [Nesting Control](#nesting-control)
- [Adding Resources Post-Creation](#adding-resources-post-creation)
- [Source Limiting](#source-limiting)
- [Source Decomposition](#source-decomposition)
- [Best Practices](#best-practices)

## Source Basics

A source is a function decorated with `@dlt.source` that returns or yields one or more resources:

```python
@dlt.source
def hubspot(api_key=dlt.secrets.value):
    return [companies(), deals(), products()]
```

Sources provide:
- Logical grouping of related resources
- Shared configuration and credentials
- Schema management across resources
- Resource selection and filtering

## Creating Sources

### Returning resource list
```python
@dlt.source
def my_database():
    return [users_resource(), orders_resource(), products_resource()]
```

### Yielding resources dynamically
```python
@dlt.source
def hubspot(api_key=dlt.secrets.value):
    endpoints = ["companies", "deals", "products"]
    def get_resource(endpoint):
        yield requests.get(f"{base_url}/{endpoint}").json()
    for endpoint in endpoints:
        yield dlt.resource(get_resource(endpoint), name=endpoint)
```

### Async sources
```python
@dlt.source
async def async_source(api_key=dlt.secrets.value):
    return [async_resource_a(), async_resource_b()]
```

## Dynamic Resource Creation

Create resources programmatically using `dlt.resource()` as a function call:

```python
@dlt.source
def api_source(base_url, endpoints):
    for endpoint in endpoints:
        @dlt.resource(name=endpoint, write_disposition="replace")
        def fetch(ep=endpoint):
            response = requests.get(f"{base_url}/{ep}")
            yield response.json()
        yield fetch
```

## Resource Selection

### Access and inspect resources
```python
source = hubspot()

# List all resource names
print(source.resources.keys())

# List selected resources
print(source.resources.selected.keys())

# Deselect a resource
source.deals.selected = False

# Select specific resources for loading
pipeline.run(source.with_resources("companies", "products"))
```

### Filter resource data
```python
source.deals.add_filter(
    lambda deal: deal["created_at"] > yesterday
)
```

### Transform resource data
```python
source.users.add_map(anonymize_user)
```

## Source Configuration

### Credential injection
```python
@dlt.source
def notion_source(
    database_ids=None,
    api_key: str = dlt.secrets.value
):
    # api_key is automatically injected from:
    # 1. sources.notion_source.api_key (env or TOML)
    # 2. sources.api_key
    # 3. api_key
    return [get_databases(database_ids, api_key)]
```

### Source cloning for multiple instances
```python
my_db = sql_database.clone(name="my_db", section="my_db")(
    table_names=["table_1"]
)
# Configuration uses: [sources.my_db.credentials]
```

### Custom section names
```python
@dlt.source(section="custom_section")
def my_source(api_key=dlt.secrets.value):
    # Looks for api_key in [sources.custom_section]
    return [my_resource()]
```

## Nesting Control

Control how deeply nested data creates child tables:

```python
@dlt.source(max_table_nesting=1)
def mongo_db():
    return [collection_a(), collection_b()]
```

### Post-instantiation override
```python
source = mongo_db()
source.max_table_nesting = 0  # Store all nested data as JSON
```

Nesting levels:
- `0` — No child tables; nested data stored as JSON columns
- `1` — One level of child tables (default for most use cases)
- `1000` — Maximum nesting (default)

## Adding Resources Post-Creation

```python
@dlt.transformer
def deal_scores(deal_item):
    score = model.predict(featurize(deal_item))
    yield {"deal_id": deal_item["id"], "score": score}

source = hubspot()
source.resources.add(source.deals | deal_scores)
```

## Source Limiting

Apply limits across all resources in a source:

```python
# Limit total yields per resource
pipeline.run(pipedrive_source().add_limit(10))

# Time-based limit
pipeline.run(pipedrive_source().add_limit(max_time=10))

# Combined
pipeline.run(pipedrive_source().add_limit(max_items=10, max_time=10))
```

## Source Decomposition

Split sources into independent components for parallel execution:

```python
components = source().decompose(strategy="scc")
# Returns list of strongly connected components
# Load serially in order, or in parallel with separate pipeline names

for component in components:
    pipeline.run(component)
```

This is useful when resources have no dependencies and can be loaded independently.

## Best Practices

1. **Defer data extraction to resources** — avoid long-running operations in the source function itself; the source function should only create and configure resources

2. **Use resource selection** — let users choose which resources to load rather than loading everything:
   ```python
   pipeline.run(source.with_resources("users", "orders"))
   ```

3. **Share credentials at source level** — pass API keys and connection strings to the source, not individual resources

4. **Use schema contracts** — apply contracts at the source level for consistent data quality:
   ```python
   @dlt.source(schema_contract={"columns": "freeze", "data_type": "freeze"})
   def strict_source():
       return [resource_a(), resource_b()]
   ```

5. **Keep sources focused** — one source per external system (one for HubSpot, one for Postgres, etc.)
