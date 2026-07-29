# Fastify — Validation & Serialization

> Source: [fastify.dev/docs/latest/Reference/Validation-and-Serialization](https://fastify.dev/docs/latest/Reference/Validation-and-Serialization/)

## Table of Contents

- [Overview](#overview)
- [Request Validation](#request-validation)
- [Response Serialization](#response-serialization)
- [Shared Schemas](#shared-schemas)
- [Custom Validators](#custom-validators)
- [Custom Serializers](#custom-serializers)
- [Security Considerations](#security-considerations)
- [Common Pitfalls](#common-pitfalls)

## Overview

Fastify uses a schema-based approach for both validation and serialization:

- **Validation** — Ajv v8 validates incoming requests (body, querystring, params, headers)
- **Serialization** — fast-json-stringify serializes outgoing responses (2-3x faster than `JSON.stringify`)

Both are compiled ahead of time when routes are registered, so the runtime cost per request is minimal.

## Request Validation

### Schema Locations

```javascript
fastify.post('/users', {
  schema: {
    body: {
      type: 'object',
      required: ['name', 'email'],
      properties: {
        name: { type: 'string', minLength: 1 },
        email: { type: 'string', format: 'email' },
        age: { type: 'integer', minimum: 0 }
      }
    },
    querystring: {
      type: 'object',
      properties: {
        include: { type: 'string', enum: ['profile', 'posts'] }
      }
    },
    params: {
      type: 'object',
      properties: {
        orgId: { type: 'string', pattern: '^[a-z0-9-]+$' }
      }
    },
    headers: {
      type: 'object',
      properties: {
        'x-api-key': { type: 'string' }
      },
      required: ['x-api-key']
    }
  }
}, async (request) => {
  return createUser(request.body)
})
```

### v5 Requirement

Fastify v5 requires full JSON Schema with the `type` property. The `jsonShorthand` option was removed:

```javascript
// WRONG in v5
schema: { body: { name: { type: 'string' } } }

// CORRECT in v5
schema: {
  body: {
    type: 'object',
    properties: { name: { type: 'string' } }
  }
}
```

### Default Ajv Configuration

```javascript
{
  coerceTypes: 'array',     // auto-convert types (string → number, etc.)
  useDefaults: true,         // populate missing fields with schema defaults
  removeAdditional: true,    // strip properties not in schema
  allErrors: false           // stop on first error (DoS protection)
}
```

### Type Coercion

Ajv's `coerceTypes: 'array'` means query params like `?tags=foo` automatically coerce to `['foo']` when the schema says `type: 'array'`.

### Validation Error Response

Invalid requests return a 400 with details:

```json
{
  "statusCode": 400,
  "code": "FST_ERR_VALIDATION",
  "error": "Bad Request",
  "message": "body/email must match format \"email\""
}
```

### Attaching Validation Errors

Instead of an automatic 400 response, store errors on the request for manual handling:

```javascript
fastify.post('/users', {
  attachValidation: true,
  schema: { body: { /* ... */ } }
}, async (request, reply) => {
  if (request.validationError) {
    reply.code(422)
    return {
      errors: request.validationError.validation.map(e => ({
        field: e.instancePath,
        message: e.message
      }))
    }
  }
  return createUser(request.body)
})
```

### Custom Error Formatting

```javascript
const fastify = Fastify({
  schemaErrorFormatter: (errors, dataVar) => {
    const messages = errors.map(e =>
      `${dataVar}${e.instancePath} ${e.message}`
    ).join('; ')
    return new Error(messages)
  }
})
```

## Response Serialization

### Schema-Based Serialization

Define response schemas by HTTP status code to enable fast-json-stringify:

```javascript
fastify.get('/users/:id', {
  schema: {
    response: {
      200: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          name: { type: 'string' },
          email: { type: 'string' }
        }
      },
      404: {
        type: 'object',
        properties: {
          error: { type: 'string' }
        }
      }
    }
  }
}, async (request) => {
  const user = await getUser(request.params.id)
  if (!user) {
    return { error: 'User not found', statusCode: 404 }
  }
  return user
})
```

### Benefits of Response Schemas

1. **Performance** — fast-json-stringify is 2-3x faster than `JSON.stringify`
2. **Security** — properties not in the schema are stripped, preventing accidental data leakage (e.g., password hashes)
3. **Documentation** — feeds into Swagger/OpenAPI generation

### Status Code Patterns

```javascript
response: {
  200: { /* exact match */ },
  '2xx': { /* all 2xx codes without a specific schema */ },
  '4xx': { /* all 4xx codes */ },
  default: { /* fallback for any unmatched status */ }
}
```

### Content-Type Specific Schemas

```javascript
response: {
  200: {
    content: {
      'application/json': {
        schema: {
          type: 'object',
          properties: { data: { type: 'string' } }
        }
      },
      'text/csv': {
        schema: { type: 'string' }
      }
    }
  }
}
```

## Shared Schemas

Register reusable schemas with `addSchema()` and reference them via `$ref`:

```javascript
// Register shared schemas
fastify.addSchema({
  $id: 'User',
  type: 'object',
  properties: {
    id: { type: 'string', format: 'uuid' },
    name: { type: 'string' },
    email: { type: 'string', format: 'email' },
    createdAt: { type: 'string', format: 'date-time' }
  }
})

fastify.addSchema({
  $id: 'PaginationQuery',
  type: 'object',
  properties: {
    page: { type: 'integer', minimum: 1, default: 1 },
    limit: { type: 'integer', minimum: 1, maximum: 100, default: 20 }
  }
})

// Use in routes
fastify.get('/users', {
  schema: {
    querystring: { $ref: 'PaginationQuery' },
    response: {
      200: {
        type: 'object',
        properties: {
          users: {
            type: 'array',
            items: { $ref: 'User' }
          },
          total: { type: 'integer' }
        }
      }
    }
  }
}, handler)
```

### $ref Patterns

```javascript
{ $ref: 'User' }                    // reference by $id
{ $ref: 'User#/properties/email' }  // reference a sub-path
{ $ref: '#foo' }                    // internal schema reference
```

### Schema Scope

Schemas registered via `addSchema()` are encapsulated — they're visible in the current scope and child scopes but not in parent or sibling scopes. Use `getSchemas()` to list available schemas.

## Custom Validators

Replace Ajv with another validation library:

```javascript
const Joi = require('joi')

fastify.setValidatorCompiler(({ schema }) => {
  const joiSchema = Joi.object(schema)
  return (data) => {
    const { error, value } = joiSchema.validate(data)
    if (error) {
      return { error }
    }
    return { value }
  }
})
```

The compiler must return `{ value }` on success or `{ error }` on failure. Never throw from a validator.

## Custom Serializers

```javascript
fastify.setSerializerCompiler(({ schema }) => {
  return (data) => JSON.stringify(data)
})
```

## Content-Type Specific Validation

```javascript
fastify.post('/upload', {
  schema: {
    body: {
      content: {
        'application/json': {
          schema: {
            type: 'object',
            properties: { data: { type: 'string' } }
          }
        },
        'text/plain': {
          schema: { type: 'string' }
        }
      }
    }
  }
}, handler)
```

Content type matching uses the exact MIME type essence — custom parsers accepting multiple types via regex need corresponding `content` map entries.

## Security Considerations

1. **Treat schemas as application code** — validation and serialization use `new Function()` internally, which is unsafe with user-provided schemas
2. **Don't use `$async` Ajv** — accessing databases during validation opens DoS vectors
3. **Keep `allErrors: false`** — setting it to `true` makes the validator process the entire input even after finding errors, which can be exploited for DoS
4. **Response schemas strip extra fields** — this is a feature, not a bug; it prevents accidental data leaks

## Common Pitfalls

1. **Missing `type` in schemas** — Fastify v5 requires explicit `type` on all schemas; omitting it causes an error at startup
2. **`removeAdditional: true` surprises** — extra properties in the body are silently removed; if you need them, set `removeAdditional: false` in Ajv config
3. **Coercion side effects** — `coerceTypes: 'array'` can transform unexpected values; be explicit with types
4. **Shared schema scope** — schemas added in a plugin aren't visible in parent plugins; register common schemas at the root level
