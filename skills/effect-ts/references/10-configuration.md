# Configuration

> Source: [effect.website/docs](https://effect.website/docs/configuration/) | Package: `effect` v3.21.x

## Table of Contents

- [Overview](#overview)
- [Config Primitives](#config-primitives)
- [Default Values and Optional Config](#default-values-and-optional-config)
- [Nested Configuration](#nested-configuration)
- [Validation and Transforms](#validation-and-transforms)
- [Secret Values](#secret-values)
- [ConfigProvider](#configprovider)
- [Config in Services and Layers](#config-in-services-and-layers)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## Overview

Effect provides a type-safe configuration system through the `Config` module. By default, configuration is loaded from environment variables, but you can swap the backend to read from files, maps, or custom sources.

```typescript
import { Effect, Config } from "effect"

const program = Effect.gen(function* () {
  const port = yield* Config.number("PORT")
  const host = yield* Config.string("HOST")
  const debug = yield* Config.boolean("DEBUG")

  yield* Effect.log(`Starting on ${host}:${port} (debug: ${debug})`)
})
// Reads PORT, HOST, DEBUG from environment variables
```

## Config Primitives

```typescript
import { Config } from "effect"

Config.string("KEY")            // string
Config.number("PORT")           // number (parsed from string)
Config.boolean("DEBUG")         // boolean ("true"/"false", "1"/"0", "yes"/"no")
Config.integer("MAX_RETRIES")   // integer (rejects floats)
Config.date("START_DATE")       // Date (parsed from ISO string)
Config.literal("ENV")("production", "staging", "development") // union
Config.logLevel("LOG_LEVEL")    // LogLevel
Config.duration("TIMEOUT")      // Duration (e.g., "5 seconds", "100 millis")

// Array from delimiter
Config.array(Config.string("ALLOWED_ORIGINS"), ",")
// ALLOWED_ORIGINS=a.com,b.com → ["a.com", "b.com"]
```

## Default Values and Optional Config

```typescript
// With default
const port = Config.number("PORT").pipe(Config.withDefault(3000))

// Optional (returns Option)
const debugMode = Config.option(Config.boolean("DEBUG"))
// Effect<Option<boolean>>

// Or else another config
const dbUrl = Config.orElse(
  Config.string("DATABASE_URL"),
  () => Config.string("DB_URL")
)
```

## Nested Configuration

Group related config with a prefix:

```typescript
// Reads DB_HOST, DB_PORT, DB_NAME, DB_PASSWORD
const dbConfig = Config.all({
  host: Config.string("HOST"),
  port: Config.number("PORT"),
  name: Config.string("NAME"),
  password: Config.redacted("PASSWORD")
}).pipe(Config.nested("DB"))

// Deeply nested: REDIS_CACHE_TTL, REDIS_CACHE_MAX_SIZE
const cacheConfig = Config.all({
  ttl: Config.number("TTL"),
  maxSize: Config.number("MAX_SIZE")
}).pipe(Config.nested("CACHE"), Config.nested("REDIS"))
```

### Config.all — Combine multiple configs

```typescript
const appConfig = Config.all({
  port: Config.number("PORT").pipe(Config.withDefault(3000)),
  host: Config.string("HOST").pipe(Config.withDefault("0.0.0.0")),
  db: Config.all({
    url: Config.string("URL"),
    pool: Config.number("POOL_SIZE").pipe(Config.withDefault(10))
  }).pipe(Config.nested("DB")),
  debug: Config.boolean("DEBUG").pipe(Config.withDefault(false))
})
// Effect<{ port: number; host: string; db: { url: string; pool: number }; debug: boolean }>
```

## Validation and Transforms

```typescript
// Validate with a predicate
const port = Config.number("PORT").pipe(
  Config.validate({
    message: "PORT must be between 1 and 65535",
    validation: (n) => n >= 1 && n <= 65535
  })
)

// Transform the value
const logLevel = Config.string("LOG_LEVEL").pipe(
  Config.map((s) => s.toUpperCase())
)

// Map with an effect
const parsedConfig = Config.string("JSON_CONFIG").pipe(
  Config.mapEffect((raw) =>
    Effect.try({
      try: () => JSON.parse(raw) as AppSettings,
      catch: (e) => new ConfigError({ key: "JSON_CONFIG", cause: e })
    })
  )
)
```

## Secret Values

Use `Config.redacted` for sensitive values. Redacted values are never logged or exposed in error messages:

```typescript
const secret = Config.redacted("API_KEY")
// Effect<Redacted<string>>

// Access the underlying value (explicit opt-in)
const program = Effect.gen(function* () {
  const apiKey = yield* Config.redacted("API_KEY")
  const raw = Redacted.value(apiKey) // string — use carefully
  // If you log `apiKey` directly: "<redacted>"
})
```

## ConfigProvider

The default `ConfigProvider` reads from `process.env`. You can replace it:

### From a Map

```typescript
import { ConfigProvider, Layer } from "effect"

const TestConfigProvider = ConfigProvider.fromMap(
  new Map([
    ["PORT", "8080"],
    ["HOST", "localhost"],
    ["DB_URL", "postgres://localhost/test"]
  ])
)

const program = myEffect.pipe(
  Effect.withConfigProvider(TestConfigProvider)
)
```

### From JSON

```typescript
const JsonConfigProvider = ConfigProvider.fromJson({
  port: 3000,
  host: "0.0.0.0",
  db: {
    url: "postgres://localhost/app",
    poolSize: 10
  }
})
```

### Layered Providers (Fallback Chain)

```typescript
// Try .env file first, fall back to environment variables
const provider = ConfigProvider.orElse(
  ConfigProvider.fromMap(dotEnvMap),
  () => ConfigProvider.fromEnv()
)
```

### As a Layer

```typescript
const TestConfig = Layer.setConfigProvider(
  ConfigProvider.fromMap(new Map([
    ["PORT", "3000"],
    ["DB_URL", "postgres://localhost/test"]
  ]))
)

const testProgram = myEffect.pipe(Effect.provide(TestConfig))
```

## Config in Services and Layers

The recommended pattern is to load config in a service layer:

```typescript
class AppConfig extends Effect.Service<AppConfig>()("app/Config", {
  effect: Effect.gen(function* () {
    const port = yield* Config.number("PORT").pipe(Config.withDefault(3000))
    const host = yield* Config.string("HOST").pipe(Config.withDefault("0.0.0.0"))
    const dbUrl = yield* Config.string("DATABASE_URL")
    const jwtSecret = yield* Config.redacted("JWT_SECRET")
    const env = yield* Config.literal("NODE_ENV")(
      "production", "staging", "development"
    ).pipe(Config.withDefault("development"))

    return { port, host, dbUrl, jwtSecret, env }
  })
}) {}

// Other services depend on AppConfig
class Database extends Effect.Service<Database>()("app/Database", {
  scoped: Effect.gen(function* () {
    const config = yield* AppConfig
    const pool = yield* Effect.acquireRelease(
      Effect.sync(() => createPool(config.dbUrl)),
      (p) => Effect.promise(() => p.end())
    )
    return { query: (sql: string) => Effect.tryPromise(() => pool.query(sql)) }
  }),
  dependencies: [AppConfig.Default]
}) {}
```

## Common Patterns

### Environment-Specific Layers

```typescript
const getLayer = () => {
  const env = process.env.NODE_ENV ?? "development"
  switch (env) {
    case "production":
      return Layer.mergeAll(ProdDatabaseLive, ProdCacheLive, ProdLoggerLive)
    case "test":
      return Layer.mergeAll(TestDatabaseLive, MockCacheLive, TestLoggerLive)
    default:
      return Layer.mergeAll(DevDatabaseLive, MemoryCacheLive, DevLoggerLive)
  }
}
```

### Feature Flags

```typescript
const features = Config.all({
  newDashboard: Config.boolean("FF_NEW_DASHBOARD").pipe(Config.withDefault(false)),
  betaApi: Config.boolean("FF_BETA_API").pipe(Config.withDefault(false)),
  maxUploadMb: Config.number("FF_MAX_UPLOAD_MB").pipe(Config.withDefault(10))
})
```

### Config Validation at Startup

```typescript
const validateConfig = Effect.gen(function* () {
  const config = yield* AppConfig
  if (config.env === "production" && !Redacted.value(config.jwtSecret)) {
    return yield* Effect.die(new Error("JWT_SECRET required in production"))
  }
  yield* Effect.log(`Config loaded: env=${config.env} port=${config.port}`)
})

const main = validateConfig.pipe(
  Effect.flatMap(() => startServer),
  Effect.provide(AppConfig.Default)
)
```

## Common Pitfalls

- **Config is evaluated lazily**: `Config.string("KEY")` doesn't read the env var until the effect is run. This is intentional — it lets you test with different providers.
- **Missing required config fails the effect**: If `PORT` is not set and there's no default, the effect fails with a `ConfigError`. Provide defaults for optional values.
- **Naming convention**: Environment variables use UPPER_SNAKE_CASE. `Config.nested("DB")` prepends `DB_` to all nested keys.
- **Don't read process.env directly**: Use `Config` for consistency, testability, and error handling. Direct env access bypasses the provider system.

## Related Topics

- Services and layers → `03-context-services.md` and `04-layers.md`
- Testing config → `11-testing.md`
- Schema validation for config → `05-schema.md`
