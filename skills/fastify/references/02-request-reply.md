# Fastify — Request & Reply Objects

> Source: [fastify.dev/docs/latest/Reference/Request](https://fastify.dev/docs/latest/Reference/Request/) and [fastify.dev/docs/latest/Reference/Reply](https://fastify.dev/docs/latest/Reference/Reply/)

## Table of Contents

- [Request Object](#request-object)
- [Reply Object](#reply-object)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## Request Object

The Request object is the first parameter of every handler function. It wraps the Node.js `http.IncomingMessage` with additional properties.

### Core Properties

| Property | Type | Description |
|----------|------|-------------|
| `request.body` | any | Parsed request payload |
| `request.query` | object | Parsed querystring |
| `request.params` | object | URL parameter values |
| `request.headers` | object | Request headers (getter/setter) |
| `request.raw` | IncomingMessage | Underlying Node.js request |
| `request.server` | FastifyInstance | Scoped Fastify instance |
| `request.id` | string | Unique request identifier |
| `request.log` | Logger | Pino child logger for this request |
| `request.ip` | string | Client IP (or X-Forwarded-For with trustProxy) |
| `request.ips` | string[] | IP chain from X-Forwarded-For |
| `request.host` | string | Host header value |
| `request.hostname` | string | Hostname without port |
| `request.port` | number | Port from host header |
| `request.protocol` | string | `'http'` or `'https'` |
| `request.method` | string | HTTP method |
| `request.url` | string | Request URL |
| `request.originalUrl` | string | URL before internal re-routing |
| `request.mediaType` | string | Content-Type media type |
| `request.is404` | boolean | True if in 404 handler |
| `request.socket` | Socket | Underlying connection |
| `request.signal` | AbortSignal | Aborted on timeout or disconnect |
| `request.routeOptions` | object | Route config, schema, method, url |

### Usage Example

```javascript
fastify.post('/users/:id', async (request, reply) => {
  console.log(request.params.id)       // URL parameter
  console.log(request.body)            // parsed body
  console.log(request.query.filter)    // querystring
  console.log(request.headers['x-api-key'])
  console.log(request.ip)             // client IP
  console.log(request.method)         // 'POST'
  request.log.info('processing user request')
  return { ok: true }
})
```

### Security Note

`request.ip`, `request.ips`, `request.host`, `request.hostname`, `request.port`, and `request.protocol` come from request metadata and should be treated as untrusted input unless your proxy chain is explicitly trusted via the `trustProxy` option.

### Validation Methods

```javascript
// Get compiled validator for a schema part
const validate = request.getValidationFunction('body')
const isValid = validate(someData)

// Compile and cache a custom schema
const validateCustom = request.compileValidationSchema({
  type: 'object',
  properties: { name: { type: 'string' } },
  required: ['name']
})

// Validate arbitrary data
const result = request.validateInput(data, 'body')
```

## Reply Object

The Reply object is the second parameter of handler functions. It manages HTTP response construction and sending.

### Status Codes

```javascript
reply.code(201)           // set status code (chainable)
reply.statusCode = 404    // property setter alternative
reply.statusCode          // read current status code
```

Default status code is 200 if not explicitly set.

### Headers

```javascript
// Set individual header
reply.header('x-request-id', '12345')
reply.header('cache-control', 'no-cache')

// Set multiple headers at once
reply.headers({
  'x-custom': 'value',
  'x-another': 'other'
})

// Read a set header
const val = reply.getHeader('x-custom')

// Get all headers
const all = reply.getHeaders()

// Check existence
reply.hasHeader('x-custom')  // true

// Remove a header
reply.removeHeader('x-custom')
```

#### Multiple Set-Cookie Headers

```javascript
reply.header('set-cookie', 'session=abc; Path=/')
reply.header('set-cookie', 'theme=dark; Path=/')
// Both cookies are sent
```

To reset, call `reply.removeHeader('set-cookie')` first.

### Content Type

```javascript
reply.type('application/json')         // shorthand for content-type
reply.type('text/html; charset=utf-8')
```

JSON subtypes automatically include UTF-8 charset.

### Sending Responses

#### Objects (JSON)

```javascript
reply.send({ hello: 'world' })
// Serialized via fast-json-stringify if response schema exists,
// otherwise JSON.stringify
```

#### Strings

```javascript
reply.send('plain text')
// Default: text/plain; charset=utf-8
// If content-type already set, sent as-is
```

#### Streams

```javascript
import { createReadStream } from 'fs'
reply.send(createReadStream('./file.txt'))
// Default: application/octet-stream
```

#### Buffers

```javascript
reply.send(Buffer.from('binary data'))
// Default: application/octet-stream
```

#### Errors

```javascript
reply.send(new Error('Something went wrong'))
// Automatically formatted: { statusCode, error, message }
// Status codes < 400 are elevated to 500
```

#### Async Return vs reply.send()

```javascript
// Preferred: return value
fastify.get('/a', async () => {
  return { data: 'value' }
})

// With reply.send — must return reply
fastify.get('/b', async (request, reply) => {
  reply.code(201).send({ created: true })
  return reply
})
```

### Redirect

```javascript
reply.redirect('/new-location')        // 302 by default
reply.redirect('/new-location', 301)   // permanent redirect
reply.code(303).redirect('/other')     // set code first
```

URLs must be properly encoded. Use `encodeURI()` for user-provided paths.

### Not Found

```javascript
reply.callNotFound()
// Invokes the custom not found handler
```

### Hijacking

Take full control of the response, bypassing Fastify's send logic:

```javascript
fastify.get('/sse', async (request, reply) => {
  reply.hijack()
  const raw = reply.raw
  raw.writeHead(200, { 'content-type': 'text/event-stream' })
  raw.write('data: hello\n\n')
  // You own the socket now
})
```

### Response Timing

```javascript
fastify.addHook('onResponse', (request, reply, done) => {
  console.log(`Response time: ${reply.elapsedTime}ms`)
  done()
})
```

### HTTP Trailers

```javascript
reply.trailer('x-checksum', async (reply, payload) => {
  return computeChecksum(payload)
})
// Requires chunked transfer encoding (added automatically)
```

### Early Hints (HTTP 103)

```javascript
reply.writeEarlyHints({
  link: '</styles.css>; rel=preload; as=style'
})
```

### Serialization Control

```javascript
// Custom serializer for this reply
reply.serializer((payload) => {
  return customSerialize(payload)
})

// Compile a serialization function from schema
const serialize = reply.compileSerializationSchema({
  type: 'object',
  properties: { foo: { type: 'string' } }
})

// Serialize data with a specific schema
const json = reply.serializeInput({ foo: 'bar' }, 200)
```

### Promise Support

Reply objects are thenable — you can await them:

```javascript
fastify.get('/stream', async (request, reply) => {
  reply.send(someStream)
  await reply  // waits until response is fully sent
  console.log('response complete')
})
```

### Raw Access

```javascript
reply.raw  // Node.js http.ServerResponse
reply.sent // boolean: has reply.send() been called?
```

## Common Patterns

### Conditional Response

```javascript
fastify.get('/data', async (request, reply) => {
  const data = await fetchData(request.query.id)
  if (!data) {
    reply.code(404)
    return { error: 'Not found' }
  }
  return data
})
```

### Setting Headers Before Send

```javascript
fastify.get('/download', async (request, reply) => {
  reply
    .code(200)
    .header('content-disposition', 'attachment; filename="report.csv"')
    .type('text/csv')
    .send(csvStream)
  return reply
})
```

## Common Pitfalls

1. **Double send** — calling both `return value` and `reply.send()` in an async handler causes a warning; pick one approach
2. **Returning undefined** — async handlers that return nothing produce an error; always return a value or call `reply.send()`
3. **reply.raw bypasses Fastify** — writing directly to `reply.raw` skips hooks, serialization, and logging
4. **Headers after send** — setting headers after `reply.send()` has no effect
5. **Error status codes** — errors sent with status codes < 400 are automatically elevated to 500
