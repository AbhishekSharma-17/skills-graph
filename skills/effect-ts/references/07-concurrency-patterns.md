# Concurrency Patterns

> Source: [effect.website/docs](https://effect.website/docs/concurrency/) | Package: `effect` v3.21.x

## Table of Contents

- [Ref — Mutable References](#ref--mutable-references)
- [Deferred — One-Shot Async Signals](#deferred--one-shot-async-signals)
- [Queue — Producer/Consumer Communication](#queue--producerconsumer-communication)
- [Semaphore — Concurrency Limiting](#semaphore--concurrency-limiting)
- [PubSub — Publish/Subscribe](#pubsub--publishsubscribe)
- [Latch — Synchronization Barriers](#latch--synchronization-barriers)
- [Practical Patterns](#practical-patterns)
- [Common Pitfalls](#common-pitfalls)

## Ref — Mutable References

Safe mutable state that can be shared across concurrent fibers:

```typescript
import { Effect, Ref } from "effect"

const counter = Effect.gen(function* () {
  const ref = yield* Ref.make(0)

  // Concurrent updates are safe
  yield* Effect.all(
    Array.from({ length: 100 }, () =>
      Ref.update(ref, (n) => n + 1)
    ),
    { concurrency: "unbounded" }
  )

  const count = yield* Ref.get(ref)
  return count // 100 — no race conditions
})
```

### Ref Operations

```typescript
Ref.make(initial)                    // Create a ref
Ref.get(ref)                         // Read current value
Ref.set(ref, value)                  // Set value
Ref.update(ref, (current) => next)   // Update with function
Ref.modify(ref, (current) => [returnValue, nextState]) // Update and return
Ref.getAndUpdate(ref, fn)            // Get old value, set new
Ref.updateAndGet(ref, fn)            // Set new value, get it
```

### SynchronizedRef — Effectful Updates

When updates themselves need to run effects:

```typescript
import { SynchronizedRef } from "effect"

const cache = Effect.gen(function* () {
  const ref = yield* SynchronizedRef.make<Map<string, User>>(new Map())

  yield* SynchronizedRef.updateEffect(ref, (cache) =>
    Effect.gen(function* () {
      const freshData = yield* fetchAllUsers()
      return new Map(freshData.map(u => [u.id, u]))
    })
  )
})
```

## Deferred — One-Shot Async Signals

A Deferred is a promise-like value that can be completed exactly once. Multiple fibers can wait on it:

```typescript
import { Effect, Deferred } from "effect"

const coordinatedWork = Effect.gen(function* () {
  const signal = yield* Deferred.make<string, Error>()

  // Consumer — waits for the signal
  const consumer = yield* Effect.fork(
    Effect.gen(function* () {
      yield* Effect.log("Waiting for data...")
      const data = yield* Deferred.await(signal)
      yield* Effect.log(`Received: ${data}`)
      return data
    })
  )

  // Producer — completes the signal
  yield* Effect.sleep(Duration.seconds(1))
  yield* Deferred.succeed(signal, "Hello from producer!")

  return yield* Fiber.join(consumer)
})
```

### Deferred Operations

```typescript
Deferred.make<A, E>()                // Create
Deferred.await(deferred)             // Wait for completion
Deferred.succeed(deferred, value)    // Complete with success
Deferred.fail(deferred, error)       // Complete with failure
Deferred.complete(deferred, effect)  // Complete with an effect's result
Deferred.isDone(deferred)            // Check if completed (sync)
```

## Queue — Producer/Consumer Communication

Bounded or unbounded queues for inter-fiber communication with backpressure:

```typescript
import { Effect, Queue } from "effect"

const pipeline = Effect.gen(function* () {
  // Bounded queue — producers block when full
  const queue = yield* Queue.bounded<WorkItem>(100)

  // Producer
  const producer = yield* Effect.fork(
    Effect.forEach(
      items,
      (item) => Queue.offer(queue, item),
      { concurrency: 1 }
    )
  )

  // Consumer
  const consumer = yield* Effect.fork(
    Effect.forever(
      Effect.gen(function* () {
        const item = yield* Queue.take(queue)
        yield* processItem(item)
      })
    )
  )

  yield* Fiber.join(producer)
  yield* Queue.shutdown(queue) // Signal no more items
})
```

### Queue Types

```typescript
Queue.bounded<A>(capacity)    // Back-pressures when full
Queue.unbounded<A>()          // No limit (use carefully)
Queue.dropping<A>(capacity)   // Drops new items when full
Queue.sliding<A>(capacity)    // Drops oldest items when full
```

### Queue Operations

```typescript
Queue.offer(queue, item)      // Enqueue (may block for bounded)
Queue.offerAll(queue, items)  // Enqueue multiple
Queue.take(queue)             // Dequeue (blocks when empty)
Queue.takeAll(queue)          // Take all currently available
Queue.takeBetween(queue, min, max) // Take between min and max items
Queue.poll(queue)             // Take if available (Option)
Queue.size(queue)             // Current size
Queue.shutdown(queue)         // Signal completion
Queue.awaitShutdown(queue)    // Wait for shutdown signal
```

### Multiple Consumers

```typescript
const workerPool = Effect.gen(function* () {
  const queue = yield* Queue.bounded<Task>(1000)

  // 5 concurrent workers reading from the same queue
  const workers = yield* Effect.all(
    Array.from({ length: 5 }, (_, i) =>
      Effect.fork(
        Effect.gen(function* () {
          while (true) {
            const task = yield* Queue.take(queue)
            yield* processTask(task)
          }
        }).pipe(Effect.catchAll(() => Effect.void))
      )
    ),
    { concurrency: "unbounded" }
  )

  return { queue, workers }
})
```

## Semaphore — Concurrency Limiting

Limit the number of concurrent operations:

```typescript
import { Effect } from "effect"

const rateLimited = Effect.gen(function* () {
  // Allow at most 5 concurrent operations
  const semaphore = yield* Effect.makeSemaphore(5)

  const results = yield* Effect.forEach(
    urls,
    (url) => semaphore.withPermits(1)(fetchUrl(url)),
    { concurrency: "unbounded" }
  )
  return results
})
```

### Semaphore for Resource Pools

```typescript
const connectionPool = Effect.gen(function* () {
  const semaphore = yield* Effect.makeSemaphore(10) // max 10 connections

  return {
    withConnection: <A, E, R>(effect: Effect.Effect<A, E, R>) =>
      semaphore.withPermits(1)(effect)
  }
})
```

### Multiple Permits

```typescript
// Heavy operation takes 3 permits (limits to ~3 concurrent heavy ops)
const heavyOp = semaphore.withPermits(3)(expensiveComputation)

// Light operation takes 1 permit
const lightOp = semaphore.withPermits(1)(quickCheck)
```

## PubSub — Publish/Subscribe

One-to-many message distribution:

```typescript
import { Effect, PubSub, Queue } from "effect"

const messageBus = Effect.gen(function* () {
  const pubsub = yield* PubSub.bounded<Event>(256)

  // Subscriber 1 — gets its own queue
  const sub1 = yield* PubSub.subscribe(pubsub)

  // Subscriber 2 — independent queue
  const sub2 = yield* PubSub.subscribe(pubsub)

  // Publisher — message goes to ALL subscribers
  yield* PubSub.publish(pubsub, { type: "user.created", userId: "123" })

  // Each subscriber receives the message independently
  const msg1 = yield* Queue.take(sub1)
  const msg2 = yield* Queue.take(sub2)
})
```

### PubSub Types

```typescript
PubSub.bounded<A>(capacity)    // Back-pressure on publish when full
PubSub.unbounded<A>()          // No limits
PubSub.dropping<A>(capacity)   // Drop messages when subscriber queue full
PubSub.sliding<A>(capacity)    // Drop oldest when subscriber queue full
```

## Latch — Synchronization Barriers

Coordinate multiple fibers to wait for a signal before proceeding:

```typescript
import { Effect } from "effect"

const barrier = Effect.gen(function* () {
  const latch = yield* Effect.makeLatch(false) // starts closed

  // Multiple fibers wait at the latch
  const workers = yield* Effect.forEach(
    Array.from({ length: 10 }),
    () => Effect.fork(
      Effect.gen(function* () {
        yield* latch.await  // blocks until latch opens
        yield* doWork()
      })
    ),
    { concurrency: "unbounded" }
  )

  // Setup phase
  yield* performSetup()

  // Open the latch — all workers proceed
  yield* latch.open
})
```

## Practical Patterns

### Rate Limiter

```typescript
const makeRateLimiter = (maxPerSecond: number) =>
  Effect.gen(function* () {
    const semaphore = yield* Effect.makeSemaphore(maxPerSecond)

    return <A, E, R>(effect: Effect.Effect<A, E, R>) =>
      semaphore.withPermits(1)(
        effect.pipe(
          Effect.tap(() => Effect.sleep(Duration.seconds(1)).pipe(
            Effect.fork,
            Effect.flatMap((f) => Effect.void) // don't wait
          ))
        )
      )
  })
```

### Debounce

```typescript
const debounce = <A, E, R>(
  effect: Effect.Effect<A, E, R>,
  duration: Duration.DurationInput
) =>
  Effect.gen(function* () {
    const ref = yield* Ref.make<Fiber.RuntimeFiber<A, E> | null>(null)
    return Effect.gen(function* () {
      const prev = yield* Ref.get(ref)
      if (prev) yield* Fiber.interrupt(prev)
      const fiber = yield* Effect.fork(
        Effect.delay(effect, duration)
      )
      yield* Ref.set(ref, fiber)
      return yield* Fiber.join(fiber)
    })
  })
```

### Circuit Breaker

```typescript
const makeCircuitBreaker = (threshold: number, resetAfter: Duration.DurationInput) =>
  Effect.gen(function* () {
    const failures = yield* Ref.make(0)
    const state = yield* Ref.make<"closed" | "open" | "half-open">("closed")

    return <A, E, R>(effect: Effect.Effect<A, E, R>) =>
      Effect.gen(function* () {
        const current = yield* Ref.get(state)
        if (current === "open") {
          return yield* Effect.fail(new CircuitBreakerOpen())
        }

        return yield* effect.pipe(
          Effect.tap(() => Ref.set(failures, 0)),
          Effect.tapError(() =>
            Ref.updateAndGet(failures, (n) => n + 1).pipe(
              Effect.flatMap((n) =>
                n >= threshold
                  ? Ref.set(state, "open" as const).pipe(
                      Effect.tap(() =>
                        Effect.sleep(resetAfter).pipe(
                          Effect.tap(() => Ref.set(state, "half-open" as const)),
                          Effect.fork
                        )
                      )
                    )
                  : Effect.void
              )
            )
          )
        )
      })
  })
```

## Common Pitfalls

- **Unbounded queues can leak memory**: Prefer `Queue.bounded` in production. Use `Queue.unbounded` only when you control the producer rate.
- **Deferred can only be completed once**: Subsequent calls to `Deferred.succeed` or `Deferred.fail` are silently ignored.
- **Ref updates are atomic but not transactional**: Each `Ref.update` is atomic, but combining multiple ref updates isn't. Use `SynchronizedRef` or STM for multi-ref transactions.
- **Semaphore permits must be released**: `withPermits` handles this automatically. Don't manually acquire/release unless you understand the cleanup implications.

## Related Topics

- Fiber basics → `06-concurrency.md`
- Streams (async data flows) → `08-streams.md`
- Resource management → `09-resource-management.md`
