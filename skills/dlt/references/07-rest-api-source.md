# dlt REST API Source

> Source: https://dlthub.com/docs/dlt-ecosystem/verified-sources/rest_api/basic | dlt v1.29.1

## Table of Contents
- [Overview](#overview)
- [Configuration Structure](#configuration-structure)
- [Client Configuration](#client-configuration)
- [Authentication Types](#authentication-types)
- [Pagination Types](#pagination-types)
- [Endpoint Configuration](#endpoint-configuration)
- [Resource Configuration](#resource-configuration)
- [Incremental Loading](#incremental-loading)
- [Resource Relationships](#resource-relationships)
- [Processing Steps](#processing-steps)
- [Complete Example](#complete-example)

## Overview

The REST API source provides a declarative way to extract data from REST APIs. Instead of writing HTTP request code, you define the API structure as configuration:

```python
import dlt
from dlt.sources.rest_api import rest_api_source

source = rest_api_source({
    "client": {"base_url": "https://api.example.com/v1/"},
    "resources": ["users", "posts", "comments"]
})

pipeline = dlt.pipeline("api_demo", destination="duckdb")
pipeline.run(source)
```

## Configuration Structure

```python
from dlt.sources.rest_api import RESTAPIConfig

config: RESTAPIConfig = {
    "client": {
        # Connection and authentication settings
    },
    "resource_defaults": {
        # Default parameters for all resources
    },
    "resources": [
        # List of resources to fetch
    ],
}
```

## Client Configuration

```python
"client": {
    "base_url": "https://api.example.com/v1/",
    "headers": {"Custom-Header": "value"},
    "auth": {...},
    "paginator": {...},
    "session": custom_requests_session  # Optional custom session
}
```

`base_url` is prepended to all endpoint paths. Fully qualified URLs (starting with `http:` or `https:`) are used as-is.

## Authentication Types

### Bearer Token
```python
"auth": {
    "type": "bearer",
    "token": dlt.secrets["your_api_token"]
}
# Shortcut syntax
"auth": {"token": dlt.secrets["your_api_token"]}
```

### HTTP Basic
```python
"auth": {
    "type": "http_basic",
    "username": "user",
    "password": dlt.secrets["password"]
}
```

### API Key
```python
"auth": {
    "type": "api_key",
    "name": "X-API-Key",
    "api_key": dlt.secrets["api_key"],
    "location": "header"  # or "query"
}
```

### OAuth 2.0 Client Credentials
```python
"auth": {
    "type": "oauth2_client_credentials",
    "access_token_url": "https://auth.example.com/token",
    "client_id": dlt.secrets["client_id"],
    "client_secret": dlt.secrets["client_secret"],
    "access_token_request_data": {},  # Optional extra data
    "default_token_expiration": 3600  # Seconds
}
```

### Custom auth class
```python
from dlt.sources.helpers.rest_client.auth import HttpBasicAuth
"auth": HttpBasicAuth("user", dlt.secrets["password"])
```

## Pagination Types

dlt can auto-detect pagination for compliant APIs. When auto-detection fails, specify explicitly:

### JSON Link (next URL in response body)
```python
"paginator": {
    "type": "json_link",
    "next_url_path": "pagination.next"
}
```

### Header Link (RFC 5988 Link header)
```python
"paginator": {
    "type": "header_link",
    "links_next_key": "next"
}
```

### Offset-based
```python
"paginator": {
    "type": "offset",
    "limit": 100,
    "offset": 0,
    "offset_param": "offset",
    "limit_param": "limit",
    "total_path": "total",
    "maximum_offset": 10000,
    "stop_after_empty_page": True
}
```

### Page Number
```python
"paginator": {
    "type": "page_number",
    "base_page": 0,
    "page_param": "page",
    "total_path": "total_pages",
    "maximum_page": 50,
    "stop_after_empty_page": True
}
```

### Cursor-based
```python
"paginator": {
    "type": "cursor",
    "cursor_path": "cursors.next",
    "cursor_param": "cursor"
}
```

### Header Cursor
```python
"paginator": {
    "type": "header_cursor",
    "cursor_key": "next",
    "cursor_param": "cursor"
}
```

### Single Page (no pagination)
```python
"paginator": {"type": "single_page"}
```

## Endpoint Configuration

```python
{
    "path": "issues",
    "method": "GET",                    # GET (default) or POST
    "headers": {"X-Custom": "value"},
    "params": {
        "sort": "updated",
        "per_page": 100,
    },
    "json": {"query": "data"},          # POST body (JSON)
    "data": "form-encoded-data",        # POST body (form)
    "paginator": {...},
    "data_selector": "results",         # JSONPath to data array
    "incremental": {...}
}
```

`data_selector` locates the data array in the response. For example, if the API returns `{"results": [...], "meta": {...}}`, use `data_selector: "results"`.

## Resource Configuration

```python
{
    "name": "issues",
    "endpoint": {...},
    "primary_key": "id",
    "write_disposition": "merge",
    "table_name": "custom_table",
    "max_table_nesting": 2,
    "selected": True,
    "parallelized": True,
    "include_from_parent": ["id", "title"],
    "processing_steps": [...],
    "auth": HttpBasicAuth("user", "pass")  # Per-resource auth override
}
```

### Resource defaults
Applied to all resources unless overridden:
```python
"resource_defaults": {
    "primary_key": "id",
    "write_disposition": "merge",
    "endpoint": {
        "params": {"per_page": 100}
    }
}
```

## Incremental Loading

### Via query parameters
```python
"params": {
    "since": {
        "type": "incremental",
        "cursor_path": "updated_at",
        "initial_value": "2024-01-25T11:21:28Z"
    }
}
```

### Via placeholders
```python
{
    "path": "posts",
    "params": {
        "created_since": "{incremental.start_value}"
    },
    "incremental": {
        "cursor_path": "created_at",
        "initial_value": "2024-01-25T00:00:00Z"
    }
}
```

Placeholder variants:
- `{incremental.start_value}` — current cursor or initial value
- `{incremental.initial_value}` — always uses initial value
- `{incremental.last_value}` — last tracked value
- `{incremental.end_value}` — end value if configured

### In POST body
```python
{
    "path": "posts/search",
    "method": "POST",
    "json": {
        "filters": {
            "fromDate": "{incremental.start_value}",
            "toDate": "2024-03-25"
        }
    },
    "incremental": {
        "cursor_path": "created_at",
        "initial_value": "2024-01-25T00:00:00Z"
    }
}
```

### Value conversion
```python
"incremental": {
    "start_param": "created_since",
    "cursor_path": "updated_at",
    "initial_value": "1704067200",
    "convert": lambda epoch: pendulum.from_timestamp(int(epoch)).to_date_string()
}
```

## Resource Relationships

### Via path parameters
```python
"resources": [
    {"name": "posts", "endpoint": {"path": "posts"}},
    {
        "name": "comments",
        "endpoint": {
            "path": "posts/{resources.posts.id}/comments"
        },
        "include_from_parent": ["id", "title"]
    }
]
```

### Via query parameters
```python
{
    "name": "post_comments",
    "endpoint": {
        "path": "comments",
        "params": {"post_id": "{resources.posts.id}"}
    }
}
```

### Via JSON body
```python
{
    "name": "post_details",
    "endpoint": {
        "path": "search",
        "method": "POST",
        "json": {"filters": {"id": "{resources.posts.id}"}}
    }
}
```

### Parallelized child resources
```python
{
    "name": "issue_comments",
    "parallelized": True,
    "endpoint": {
        "path": "issues/{resources.issues.number}/comments"
    }
}
```

## Processing Steps

Transform data before loading:

### Filter
```python
"processing_steps": [
    {"filter": lambda x: x["id"] < 10}
]
```

### Map
```python
def lower_title(record):
    record["title"] = record["title"].lower()
    return record

"processing_steps": [{"map": lower_title}]
```

### Yield Map (expand one item to many)
```python
def flatten_reactions(post):
    for reaction in post["reactions"]:
        yield {"reaction": reaction, "post_id": post["id"]}

"processing_steps": [{"yield_map": flatten_reactions}]
```

## Complete Example

```python
import dlt
from dlt.sources.rest_api import RESTAPIConfig, rest_api_resources

@dlt.source
def github_source(github_token=dlt.secrets.value):
    config: RESTAPIConfig = {
        "client": {
            "base_url": "https://api.github.com/repos/dlt-hub/dlt/",
            "auth": {"token": github_token}
        },
        "resource_defaults": {
            "primary_key": "id",
            "write_disposition": "merge",
            "endpoint": {"params": {"per_page": 100}}
        },
        "resources": [
            {
                "name": "issues",
                "endpoint": {
                    "path": "issues",
                    "params": {
                        "sort": "updated",
                        "direction": "desc",
                        "since": {
                            "type": "incremental",
                            "cursor_path": "updated_at",
                            "initial_value": "2024-01-25T11:21:28Z"
                        }
                    }
                }
            },
            {
                "name": "issue_comments",
                "endpoint": {
                    "path": "issues/{resources.issues.number}/comments"
                },
                "include_from_parent": ["id"]
            }
        ]
    }
    yield from rest_api_resources(config)

pipeline = dlt.pipeline(
    "rest_api_github",
    destination="duckdb",
    dataset_name="github_data"
)
load_info = pipeline.run(github_source())
print(load_info)
```
