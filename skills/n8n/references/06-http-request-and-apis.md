# HTTP Request and APIs

> Source: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/

## Table of Contents

- [HTTP Request Node](#http-request-node)
- [Request Configuration](#request-configuration)
- [Authentication](#authentication)
- [Request Body Types](#request-body-types)
- [Pagination](#pagination)
- [Response Handling](#response-handling)
- [cURL Import](#curl-import)
- [AI Tool Mode](#ai-tool-mode)
- [n8n REST API](#n8n-rest-api)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## HTTP Request Node

The HTTP Request node enables REST API calls to any endpoint. It supports all standard HTTP methods, multiple authentication types, pagination, and can function as an AI tool.

### Basic Configuration

```
URL: https://api.example.com/users
Method: GET
Authentication: None | Predefined Credential | Generic Credential
```

## Request Configuration

### HTTP Methods

| Method | Use Case |
|--------|----------|
| **GET** | Retrieve data |
| **POST** | Create resources |
| **PUT** | Replace resources |
| **PATCH** | Partial update |
| **DELETE** | Remove resources |
| **HEAD** | Check resource existence |
| **OPTIONS** | CORS preflight, capability discovery |

### Query Parameters

Add URL parameters as key-value pairs or JSON:

```
Key-Value mode:
  page = 1
  limit = 50
  sort = created_at

JSON mode:
  { "page": 1, "limit": 50, "sort": "created_at" }
```

With expressions:

```
page = {{ $json.nextPage }}
search = {{ $json.query }}
```

### Headers

```
Content-Type: application/json
Authorization: Bearer {{ $json.token }}
X-Custom-Header: my-value
```

## Authentication

### Predefined Credentials

Use n8n's built-in credential types that match known APIs:

```
Authentication: Predefined Credential Type
Credential Type: Notion API
→ Automatically handles auth headers and token management
```

### Generic Credential Types

| Type | Description |
|------|-------------|
| **Basic Auth** | Username + password in Authorization header |
| **Header Auth** | Custom header (e.g., X-API-Key) |
| **Digest Auth** | Challenge-response authentication |
| **OAuth1 API** | OAuth 1.0a flow |
| **OAuth2 API** | OAuth 2.0 with token refresh |
| **Query Auth** | API key in query parameter |
| **Custom Auth** | Fully custom authentication |

### OAuth2 Configuration

```
Authorization URL: https://provider.com/oauth/authorize
Access Token URL: https://provider.com/oauth/token
Client ID: your-client-id
Client Secret: your-client-secret
Scope: read write
Auth URI Query Parameters: (optional extras)
```

### Using Credentials with Expressions

```
Credential to use: {{ $json.credentialName }}
→ Dynamically select credentials at runtime
```

## Request Body Types

### JSON

```json
{
  "name": "{{ $json.name }}",
  "email": "{{ $json.email }}",
  "metadata": {
    "source": "n8n-workflow"
  }
}
```

### Form URL-Encoded

```
Content-Type: application/x-www-form-urlencoded

field1 = value1
field2 = {{ $json.dynamicValue }}
```

### Form-Data (Multipart)

For file uploads:

```
Content-Type: multipart/form-data

file = {{ $binary.data }}  (binary data from previous node)
name = document.pdf
description = Uploaded via n8n
```

### Raw Body

Send arbitrary content with custom MIME type:

```
Content Type: text/xml
Body:
<request>
  <id>{{ $json.id }}</id>
</request>
```

### Binary File

Send binary data from a previous node's output:

```
Input Data Field Name: data
→ Sends the binary content as the request body
```

## Pagination

Handle APIs that return data across multiple pages.

### Update Parameters Per Request

```
Pagination Mode: Update a Request Parameter
Parameter: query.page
Initial Value: 1
Update Expression: {{ $pageCount + 1 }}
Complete When: {{ $response.body.data.length === 0 }}
Limit Pages: 100
```

### Follow Next-Page URL

```
Pagination Mode: Response Contains a Next URL
Next URL Expression: {{ $response.body.next_page_url }}
Complete When: {{ !$response.body.next_page_url }}
```

### Pagination Variables

| Variable | Description |
|----------|-------------|
| `$pageCount` | Current page number (0-based) |
| `$request` | Current request configuration |
| `$response` | Previous response object |
| `$response.body` | Response body |
| `$response.headers` | Response headers |
| `$response.statusCode` | HTTP status code |

## Response Handling

### Response Format

| Format | Behavior |
|--------|----------|
| **Autodetect** | Parse based on Content-Type header |
| **JSON** | Parse as JSON object |
| **Text** | Return as plain text string |
| **File** | Save as binary data |

### Include Extra Data

```
Options:
  ✓ Include Response Headers and Status
  → $json.$response.headers
  → $json.$response.statusCode
```

### Never Error on HTTP Status

```
Options:
  ✓ Never Error
  → Node won't fail on 4xx/5xx responses
  → Check status code in downstream nodes
```

### Response Filtering

Specify which fields to include in the output to reduce data size:

```
Options:
  Response: Include only specified fields
  Fields: id, name, email
```

## cURL Import

Import API calls directly from documentation:

1. Copy a cURL command from API docs
2. In the HTTP Request node, click **Import cURL**
3. Paste the command
4. n8n populates URL, method, headers, body, and auth automatically

```bash
# Example cURL that n8n can import:
curl -X POST https://api.example.com/users \
  -H "Authorization: Bearer token123" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "email": "alice@example.com"}'
```

## AI Tool Mode

The HTTP Request node can function as a tool for AI agents:

```
Node attached to AI Agent as sub-node
→ Agent decides when to call the API
→ Uses $fromAI() function for dynamic parameters

Configuration:
  Description: "Fetch user data from the CRM API"
  URL: https://api.crm.com/users/{{ $fromAI('userId', 'The user ID to look up') }}
  Optimize Response: JSON, include only relevant fields
```

### $fromAI() Function

```javascript
// Let the AI agent provide parameter values
{{ $fromAI('paramName', 'Description for the AI', 'string') }}

// Examples:
URL: https://api.weather.com/forecast?city={{ $fromAI('city', 'City name for weather lookup') }}
Body: { "query": "{{ $fromAI('searchQuery', 'What to search for') }}" }
```

## n8n REST API

n8n exposes its own REST API for programmatic management:

### Authentication

```bash
# API key in header
curl -H "X-N8N-API-KEY: your-api-key" \
  https://your-n8n.com/api/v1/workflows
```

### Common Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/workflows` | GET | List all workflows |
| `/api/v1/workflows` | POST | Create a workflow |
| `/api/v1/workflows/:id` | GET | Get workflow details |
| `/api/v1/workflows/:id` | PATCH | Update a workflow |
| `/api/v1/workflows/:id/activate` | POST | Activate/publish |
| `/api/v1/executions` | GET | List executions |
| `/api/v1/executions/:id` | GET | Get execution details |
| `/api/v1/credentials` | GET | List credentials |
| `/api/v1/community-packages` | GET | List community packages |

## Common Patterns

### API Integration with Error Handling

```
HTTP Request (GET /api/data)
  → If ($json.$response.statusCode === 200)
    → True: Process data
    → False: If (statusCode === 429)
      → True: Wait (retry-after) → Loop back
      → False: Stop and Error
```

### Webhook-to-API Proxy

```
Webhook (POST /proxy/users)
  → HTTP Request (POST to external API)
  → Respond to Webhook (forward API response)
```

### Batch API Calls

```
Get list of IDs
  → Loop Over Items (batch size: 10)
  → HTTP Request (GET /api/items/{{ $json.id }})
  → Wait (1 second)
  → Loop back for next batch
  → Aggregate results
```

## Common Pitfalls

- **Self-signed certificates** — toggle off SSL verification in node options for dev environments; never in production
- **Rate limiting** — use Loop Over Items with a Wait node to respect API rate limits
- **Large responses** — n8n loads the full response into memory; use pagination for large datasets
- **Timeout** — default timeout varies; set explicitly in node options for slow APIs
- **OAuth token expiry** — n8n handles token refresh automatically for OAuth2 credentials
- **Binary vs JSON response** — set the correct response format; auto-detect can misidentify binary content

## Related Topics

- Triggers and Webhooks → `02-triggers-and-webhooks.md`
- Credentials → `07-credentials-and-security.md`
- AI Tools → `09-ai-agents-and-tools.md`
