# Streams

> Source: [effect.website/docs](https://effect.website/docs/stream/introduction/) | Package: `effect` v3.21.x

## Table of Contents

- [What Are Streams](#what-are-streams)
- [Creating Streams](#creating-streams)
- [Transforming Streams](#transforming-streams)
- [Consuming Streams](#consuming-streams)
- [Error Handling in Streams](#error-handling-in-streams)
- [Concurrency in Streams](#concurrency-in-streams)
- [Sinks](#sinks)
- [Channel — The Foundation](#channel--the-foundation)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## What Are Streams

A `Stream<A, E, R>` represents a lazy, potentially infinite sequence of values of type `A`, that may fail with `E` and requires services `R`. Streams are pull-based — values are produced on demand.

```typescript
import { Stream, Effect } from "effect"

// A stream of numbers 1-100
const numbers = Stream.range(1, 100)

// A stream from an array
const names = Stream.fromIterable(["Alice", "Bob", "Charlie"])

// An infinite stream
const ticks = Stream.repeatEffect(Effect.sync(() => Date.now()))
```

## Creating Streams

### From Values

```typescript
// Single value
Stream.succeed(42)

// Multiple values
Stream.fromIterable([1, 2, 3, 4, 5])

// From an effect (single value)
Stream.fromEffect(fetchUser(userId))

// Empty stream
Stream.empty

// Failed stream
Stream.fail(new Error("stream error"))

// Range
Stream.range(0, 99) // 0 through 99 inclusive
```

### From Effects

```typescript
// Repeat an effect forever
const heartbeat = Stream.repeatEffect(
  Effect.delay(Effect.succeed("ping"), Duration.seconds(1))
)

// Repeat with a schedule
const polling = Stream.repeatEffectWithSchedule(
  fetchStatus,
  Schedule.spaced(Duration.seconds(5))
)

// Unfold — generate from a seed
const fibonacci = Stream.unfold(
  [0, 1] as [number, number],
  ([a, b]) => Option.some([a, [b, a + b] as [number, number]])
)
```

### From External Sources

```typescript
// From an async callback/event system
const events = Stream.async<Event, Error>((emit) => {
  const handler = (event: Event) => {
    emit(Effect.succeed(Chunk.of(event)))
  }
  eventEmitter.on("data", handler)
  return Effect.sync(() => eventEmitter.off("data", handler))
})

// From a ReadableStream (Web API)
const webStream = Stream.fromReadableStream(
  () => response.body!,
  (error) => new StreamError({ cause: error })
)

// Paginated API
const allPages = Stream.paginateEffect(
  1, // initial page
  (page) =>
    fetchPage(page).pipe(
      Effect.map((result) => [
        result.items,
        result.hasMore ? Option.some(page + 1) : Option.none()
      ])
    )
)
```

## Transforming Streams

### Basic Transforms

```typescript
// Map
Stream.map(stream, (item) => item.toUpperCase())

// Filter
Stream.filter(stream, (item) => item.length > 3)

// FlatMap — each item produces a sub-stream
Stream.flatMap(userIds, (id) => Stream.fromEffect(fetchUser(id)))

// Take / Drop
Stream.take(stream, 10)     // first 10
Stream.drop(stream, 5)      // skip first 5
Stream.takeWhile(stream, (n) => n < 100)

// Distinct
Stream.changes(stream)       // remove consecutive duplicates

// Scan — running accumulation
Stream.scan(numbers, 0, (acc, n) => acc + n)
// 0, 1, 3, 6, 10, ...
```

### Chunked Operations

Streams internally operate on chunks (batches) for efficiency:

```typescript
// Process in chunks of 100
Stream.grouped(stream, 100)
// Stream<Chunk<A>> — each element is a chunk of up to 100 items

// Chunk by time window
Stream.groupedWithin(stream, 100, Duration.seconds(5))
// Emit chunk when either 100 items or 5 seconds, whichever comes first

// Map over chunks directly
Stream.mapChunks(stream, (chunk) => Chunk.map(chunk, transform))
```

### Effectful Transforms

```typescript
// Map with an effect
Stream.mapEffect(stream, (item) => enrichItem(item))

// Map with bounded concurrency
Stream.mapEffect(stream, (item) => enrichItem(item), { concurrency: 5 })

// Tap — side effect without changing the value
Stream.tap(stream, (item) => Effect.log(`Processing: ${item.id}`))
```

## Consuming Streams

### Run to Completion

```typescript
// Collect all into an array
const items = yield* Stream.runCollect(stream)
// Chunk<A>

// Run for side effects only
yield* Stream.runForEach(stream, (item) => processItem(item))

// Fold/reduce
const total = yield* Stream.runFold(stream, 0, (acc, n) => acc + n)

// Take the first element
const first = yield* Stream.runHead(stream) // Option<A>

// Take the last element
const last = yield* Stream.runLast(stream) // Option<A>

// Count elements
const count = yield* Stream.runCount(stream)

// Drain — run but discard values
yield* Stream.runDrain(stream)
```

### Run with Sink

```typescript
import { Stream, Sink } from "effect"

// Sum all numbers
const sum = yield* Stream.run(numbers, Sink.sum)

// Collect into an array
const arr = yield* Stream.run(stream, Sink.collectAll())

// Take first N
const firstTen = yield* Stream.run(stream, Sink.take(10))

// Fold with early termination
const result = yield* Stream.run(stream, Sink.foldUntil(0, 1000, (acc, n) => acc + n))
```

## Error Handling in Streams

```typescript
// Catch all errors
Stream.catchAll(stream, (error) =>
  Stream.succeed(defaultValue)
)

// Catch specific tagged errors
Stream.catchTag(stream, "NetworkError", (e) =>
  Stream.fromEffect(Effect.log(`Network error: ${e.url}`)).pipe(
    Stream.flatMap(() => Stream.empty)
  )
)

// Retry on failure
Stream.retry(stream, Schedule.exponential(Duration.seconds(1)))

// Handle errors per element
Stream.mapEffect(stream, (item) =>
  processItem(item).pipe(
    Effect.catchAll((e) => Effect.succeed({ item, error: e }))
  )
)

// orElse — switch to fallback stream on error
Stream.orElse(primaryStream, () => fallbackStream)
```

## Concurrency in Streams

### Merge — Interleave multiple streams

```typescript
// Merge two streams (interleaved, concurrent)
const merged = Stream.merge(stream1, stream2)

// Merge many streams
const merged = Stream.mergeAll(
  [stream1, stream2, stream3],
  { concurrency: 3 }
)
```

### Zip — Combine element-by-element

```typescript
// Zip two streams (pairs)
const pairs = Stream.zip(names, scores)
// Stream<[string, number]>

// Zip with a combining function
const labeled = Stream.zipWith(names, scores, (name, score) => ({ name, score }))
```

### Broadcast — Fan out to multiple consumers

```typescript
const program = Effect.gen(function* () {
  yield* Stream.fromIterable([1, 2, 3, 4, 5]).pipe(
    Stream.broadcast(2, 16), // 2 consumers, buffer size 16
    Effect.flatMap(([stream1, stream2]) =>
      Effect.all([
        Stream.runCollect(stream1.pipe(Stream.map(n => n * 2))),
        Stream.runCollect(stream2.pipe(Stream.map(n => n * 10)))
      ], { concurrency: "unbounded" })
    )
  )
})
```

## Sinks

Sinks are the dual of Streams — they consume values:

```typescript
import { Sink } from "effect"

// Built-in sinks
Sink.sum                        // Sum numbers
Sink.count                      // Count elements
Sink.collectAll()               // Collect to Chunk
Sink.head                       // First element
Sink.last                       // Last element
Sink.take(n)                    // First N elements
Sink.forEach(fn)                // Side effect per element
Sink.foldLeft(init, fn)         // Fold all elements

// Custom sink
const writeToDB = Sink.forEach((item: User) =>
  Effect.tryPromise(() => db.insert(item))
)

// Compose sinks
const pipeline = yield* Stream.run(
  userStream,
  Sink.forEach((user) =>
    Effect.gen(function* () {
      yield* validateUser(user)
      yield* saveUser(user)
      yield* notifyUser(user)
    })
  )
)
```

## Channel — The Foundation

Channels are the low-level primitive underlying both Streams and Sinks. Most users don't need them directly, but they're available for advanced use cases:

```typescript
import { Channel } from "effect"

// A Channel<Env, InErr, InElem, InDone, OutErr, OutElem, OutDone>
// represents a bidirectional communication pipeline
```

Channels support:
- Reading input elements
- Writing output elements
- Failure propagation
- Completion signaling
- Bidirectional communication

## Common Patterns

### ETL Pipeline

```typescript
const etl = Stream.fromEffect(fetchSourceData()).pipe(
  Stream.flatMap((batch) => Stream.fromIterable(batch.records)),
  Stream.filter((record) => record.isValid),
  Stream.mapEffect((record) => transformRecord(record), { concurrency: 10 }),
  Stream.grouped(100),
  Stream.mapEffect((batch) => writeBatch(batch)),
  Stream.runDrain
)
```

### Event Processing

```typescript
const eventProcessor = eventStream.pipe(
  Stream.filter((e) => e.type === "order.created"),
  Stream.mapEffect((e) => enrichOrder(e.data)),
  Stream.groupedWithin(50, Duration.seconds(10)),
  Stream.mapEffect((batch) => processBatch(batch)),
  Stream.tap((result) => Effect.log(`Processed ${result.count} orders`)),
  Stream.runDrain
)
```

### Polling with Backoff

```typescript
const poller = Stream.repeatEffectWithSchedule(
  fetchStatus.pipe(
    Effect.map((status) => status.items),
    Effect.catchAll(() => Effect.succeed([]))
  ),
  Schedule.exponential(Duration.seconds(1)).pipe(
    Schedule.union(Schedule.spaced(Duration.seconds(30)))
  )
).pipe(
  Stream.flatMap(Stream.fromIterable),
  Stream.changes
)
```

## Common Pitfalls

- **Streams are lazy**: Creating a stream doesn't execute anything. You must run it with `Stream.runCollect`, `Stream.runForEach`, etc.
- **Don't collect infinite streams**: `Stream.runCollect` on an infinite stream will never complete. Use `Stream.take` first or `Stream.runForEach`.
- **Backpressure matters**: When producers are faster than consumers, use bounded queues and `groupedWithin` to control flow.
- **flatMap ordering**: `Stream.flatMap` processes sub-streams sequentially by default. Use `{ concurrency: N }` for parallel sub-stream processing.

## Related Topics

- Concurrency primitives → `06-concurrency.md` and `07-concurrency-patterns.md`
- Resource management in streams → `09-resource-management.md`
