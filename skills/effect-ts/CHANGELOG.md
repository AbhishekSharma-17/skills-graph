## [1.0.0] — 2026-05-30

**Source version tracked:** `effect` v3.21.x

### Added

- **Overview & Setup** — What Effect is, when to use it, installation, ecosystem packages
- **The Effect Type** — Effect<A, E, R>, creating effects, Effect.gen, pipe/flow, running effects
- **Error Handling** — Typed errors, tagged errors, catchTag, retry policies, Cause, defects vs failures
- **Context & Services** — Dependency injection, Effect.Service, Context.Tag, accessor patterns
- **Layers** — Layer composition, providing services, scoped layers, application wiring
- **Schema** — Bidirectional validation, decode/encode, branded types, Schema.Class, transforms
- **Concurrency** — Fibers, structured concurrency, forking, interruption, racing, timeouts
- **Concurrency Patterns** — Ref, Deferred, Queue, Semaphore, PubSub, Latch, circuit breaker
- **Streams** — Stream creation, transforms, consumption, Sink, Channel, ETL patterns
- **Resource Management** — Scope, acquireRelease, finalizers, transaction wrapper, graceful shutdown
- **Configuration** — Config module, ConfigProvider, nested config, secrets, feature flags
- **Testing** — @effect/vitest, TestClock, layer testing, mocking services, property testing
- **Platform** — HTTP client/server, HttpApi declarative APIs, filesystem, runtime backends

### Stats

- Routing entries: 13
- Reference files: 13
- Total lines: ~4,600
