# Platform

> Source: [effect.website/docs](https://effect.website/docs/platform/introduction/) | Package: `@effect/platform` v0.x | `effect` v3.21.x

## Table of Contents

- [Overview](#overview)
- [HTTP Client](#http-client)
- [HTTP Server](#http-server)
- [HttpApi — Declarative API Definition](#httpapi--declarative-api-definition)
- [Filesystem](#filesystem)
- [Runtime Backends](#runtime-backends)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## Overview

`@effect/platform` provides platform-independent abstractions for HTTP, filesystem, workers, and more. You write code against the abstract interfaces and then provide a runtime-specific backend:

```bash
npm install @effect/platform           # abstract interfaces
npm install @effect/platform-node      # Node.js backend
npm install @effect/platform-bun       # Bun backend
npm install @effect/platform-browser   # Browser backend
```

## HTTP Client

### Basic Requests

```typescript
import { HttpClient, HttpClientRequest, HttpClientResponse } from "@effect/platform"
import { NodeHttpClient } from "@effect/platform-node"
import { Effect } from "effect"

const fetchUser = (id: string) =>
  Effect.gen(function* () {
    const client = yield* HttpClient.HttpClient
    const response = yield* client.get(`https://api.example.com/users/${id}`)
    const user = yield* HttpClientResponse.json(response)
    return user
  })

// Provide the Node.js HTTP client
const program = fetchUser("123").pipe(
  Effect.provide(NodeHttpClient.layer)
)
```

### Request Building

```typescript
const request = HttpClientRequest.post("https://api.example.com/users").pipe(
  HttpClientRequest.jsonBody({ name: "Alice", email: "alice@test.com" }),
  HttpClientRequest.setHeaders({
    Authorization: "Bearer token123",
    "Content-Type": "application/json"
  })
)

const response = yield* client.execute(request)
```

### Response Handling with Schema

```typescript
import { Schema } from "effect"

const UserResponse = Schema.Struct({
  id: Schema.Number,
  name: Schema.String,
  email: Schema.String
})

const fetchUser = (id: string) =>
  Effect.gen(function* () {
    const client = yield* HttpClient.HttpClient
    const response = yield* client.get(`/api/users/${id}`)
    return yield* HttpClientResponse.schemaBodyJson(UserResponse)(response)
  })
// Effect<{ id: number; name: string; email: string }, HttpClientError | ParseError, HttpClient>
```

### Middleware

```typescript
const clientWithAuth = HttpClient.mapRequest(
  client,
  HttpClientRequest.setHeader("Authorization", `Bearer ${token}`)
)

const clientWithRetry = HttpClient.retry(client, {
  schedule: Schedule.exponential(Duration.seconds(1)),
  times: 3
})

const clientWithLogging = HttpClient.tapRequest(client, (req) =>
  Effect.log(`${req.method} ${req.url}`)
)
```

## HTTP Server

### Basic Server

```typescript
import { HttpRouter, HttpServer, HttpServerResponse } from "@effect/platform"
import { NodeHttpServer } from "@effect/platform-node"
import { Effect, Layer } from "effect"

const router = HttpRouter.empty.pipe(
  HttpRouter.get("/health", HttpServerResponse.json({ status: "ok" })),
  HttpRouter.get("/users/:id",
    Effect.gen(function* () {
      const params = yield* HttpRouter.params
      const user = yield* fetchUser(params.id)
      return HttpServerResponse.json(user)
    })
  ),
  HttpRouter.post("/users",
    Effect.gen(function* () {
      const body = yield* HttpServerRequest.json
      const user = yield* createUser(body)
      return HttpServerResponse.json(user, { status: 201 })
    })
  )
)

const ServerLive = NodeHttpServer.layer(router, { port: 3000 })

Effect.runPromise(
  Layer.launch(ServerLive)
)
```

### Middleware for Server

```typescript
const withCors = HttpMiddleware.cors({
  allowedOrigins: ["https://app.example.com"],
  allowedMethods: ["GET", "POST", "PUT", "DELETE"]
})

const withLogging = HttpMiddleware.logger

const app = router.pipe(
  HttpRouter.use(withCors),
  HttpRouter.use(withLogging)
)
```

## HttpApi — Declarative API Definition

The `HttpApi*` modules provide a fully declarative, schema-first API definition:

### Define Endpoints

```typescript
import { HttpApi, HttpApiEndpoint, HttpApiGroup } from "@effect/platform"
import { Schema } from "effect"

class User extends Schema.Class<User>("User")({
  id: Schema.Number,
  name: Schema.String,
  email: Schema.String
}) {}

class CreateUser extends Schema.Class<CreateUser>("CreateUser")({
  name: Schema.NonEmptyString,
  email: Schema.String
}) {}

class NotFoundError extends Schema.TaggedError<NotFoundError>()(
  "NotFoundError",
  { message: Schema.String }
) {}

// Define endpoints
const usersApi = HttpApiGroup.make("users").pipe(
  HttpApiGroup.add(
    HttpApiEndpoint.get("getUser", "/users/:id").pipe(
      HttpApiEndpoint.setPath(Schema.Struct({ id: Schema.NumberFromString })),
      HttpApiEndpoint.setSuccess(User),
      HttpApiEndpoint.addError(NotFoundError, { status: 404 })
    )
  ),
  HttpApiGroup.add(
    HttpApiEndpoint.post("createUser", "/users").pipe(
      HttpApiEndpoint.setPayload(CreateUser),
      HttpApiEndpoint.setSuccess(User, { status: 201 })
    )
  )
)

// Compose into a full API
const api = HttpApi.make("myApp").pipe(
  HttpApi.addGroup(usersApi)
)
```

### Implement Handlers

```typescript
import { HttpApiBuilder } from "@effect/platform"

const usersHandlers = HttpApiBuilder.group(api, "users", (handlers) =>
  handlers.pipe(
    HttpApiBuilder.handle("getUser", ({ path }) =>
      Effect.gen(function* () {
        const repo = yield* UserRepo
        return yield* repo.findById(String(path.id))
      })
    ),
    HttpApiBuilder.handle("createUser", ({ payload }) =>
      Effect.gen(function* () {
        const repo = yield* UserRepo
        return yield* repo.create(payload)
      })
    )
  )
)

const app = HttpApiBuilder.api(api).pipe(
  Layer.provide(usersHandlers),
  Layer.provide(UserRepo.Default)
)
```

### Auto-Generated Client

```typescript
import { HttpApiClient } from "@effect/platform"

const client = yield* HttpApiClient.make(api, {
  baseUrl: "http://localhost:3000"
})

const user = yield* client.users.getUser({ path: { id: 1 } })
const newUser = yield* client.users.createUser({
  payload: { name: "Alice", email: "alice@test.com" }
})
```

### Auto-Generated OpenAPI Docs

```typescript
import { HttpApiSwagger } from "@effect/platform"

const app = HttpApiBuilder.api(api).pipe(
  Layer.provide(usersHandlers),
  Layer.provide(HttpApiSwagger.layer()) // serves at /docs
)
```

## Filesystem

```typescript
import { FileSystem } from "@effect/platform"
import { NodeFileSystem } from "@effect/platform-node"

const program = Effect.gen(function* () {
  const fs = yield* FileSystem.FileSystem

  // Read a file
  const content = yield* fs.readFileString("config.json")

  // Write a file
  yield* fs.writeFileString("output.txt", "Hello, Effect!")

  // Check existence
  const exists = yield* fs.exists("data.csv")

  // List directory
  const files = yield* fs.readDirectory("src/")

  // Create directory
  yield* fs.makeDirectory("dist/", { recursive: true })

  // Remove file
  yield* fs.remove("temp.txt")
})

const main = program.pipe(Effect.provide(NodeFileSystem.layer))
```

## Runtime Backends

Choose the backend that matches your runtime:

```typescript
// Node.js
import { NodeHttpClient } from "@effect/platform-node"
import { NodeFileSystem } from "@effect/platform-node"
import { NodeHttpServer } from "@effect/platform-node"

const NodeLayer = Layer.mergeAll(
  NodeHttpClient.layer,
  NodeFileSystem.layer
)

// Bun
import { BunHttpClient } from "@effect/platform-bun"
import { BunFileSystem } from "@effect/platform-bun"

const BunLayer = Layer.mergeAll(
  BunHttpClient.layer,
  BunFileSystem.layer
)

// Browser
import { BrowserHttpClient } from "@effect/platform-browser"

const BrowserLayer = BrowserHttpClient.layer
```

## Common Patterns

### API Client Service

```typescript
class ApiClient extends Effect.Service<ApiClient>()("app/ApiClient", {
  effect: Effect.gen(function* () {
    const http = yield* HttpClient.HttpClient
    const config = yield* AppConfig
    const baseClient = http.pipe(
      HttpClient.mapRequest(
        HttpClientRequest.prependUrl(config.apiBaseUrl)
      ),
      HttpClient.mapRequest(
        HttpClientRequest.setHeader("Authorization", `Bearer ${Redacted.value(config.apiKey)}`)
      )
    )

    return {
      get: <A>(path: string, schema: Schema.Schema<A>) =>
        baseClient.get(path).pipe(
          Effect.flatMap(HttpClientResponse.schemaBodyJson(schema))
        ),
      post: <A>(path: string, body: unknown, schema: Schema.Schema<A>) =>
        baseClient.execute(
          HttpClientRequest.post(path).pipe(HttpClientRequest.jsonBody(body))
        ).pipe(
          Effect.flatMap(HttpClientResponse.schemaBodyJson(schema))
        )
    }
  }),
  dependencies: [NodeHttpClient.layer, AppConfig.Default]
}) {}
```

### File-Based Processing Pipeline

```typescript
const processFiles = Effect.gen(function* () {
  const fs = yield* FileSystem.FileSystem
  const files = yield* fs.readDirectory("input/")

  yield* Effect.forEach(
    files.filter(f => f.endsWith(".json")),
    (file) => Effect.gen(function* () {
      const content = yield* fs.readFileString(`input/${file}`)
      const data = JSON.parse(content)
      const processed = transform(data)
      yield* fs.writeFileString(`output/${file}`, JSON.stringify(processed))
    }),
    { concurrency: 5 }
  )
})
```

## Common Pitfalls

- **Always provide a runtime backend**: `@effect/platform` interfaces require a backend. Without `NodeHttpClient.layer` or equivalent, effects fail with a missing service error.
- **HttpApi schemas are validated bidirectionally**: Request payloads are decoded, response bodies are encoded. Make sure your Schema handles both directions.
- **Don't mix platform backends**: Use one backend consistently. Mixing `NodeHttpClient` and `BunHttpClient` in the same app causes conflicts.
- **Response bodies must be consumed**: HTTP responses are streams. If you don't read the body, the connection may leak. Always call `HttpClientResponse.json`, `schemaBodyJson`, or `text`.

## Related Topics

- Schema for request/response validation → `05-schema.md`
- Services and layers → `03-context-services.md` and `04-layers.md`
- Error handling in HTTP → `02-error-handling.md`
- Testing HTTP services → `11-testing.md`
