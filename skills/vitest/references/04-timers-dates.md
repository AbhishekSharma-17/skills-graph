# Timers & Dates

> Source: [vitest.dev/api/vi](https://vitest.dev/api/vi.html) | Version: 4.x

## Table of Contents

- [Fake Timers](#fake-timers)
- [Advancing Timers](#advancing-timers)
- [Running Timers](#running-timers)
- [Timer Queries](#timer-queries)
- [System Time Mocking](#system-time-mocking)
- [Timer Tick Modes](#timer-tick-modes)
- [Practical Patterns](#practical-patterns)

---

## Fake Timers

Replace `setTimeout`, `setInterval`, `Date`, and related APIs with controllable fakes. Implementation based on `@sinonjs/fake-timers`.

### Enable Fake Timers

```typescript
import { vi, test, expect, beforeEach, afterEach } from 'vitest'

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})
```

### Configuration Options

```typescript
vi.useFakeTimers({
  shouldAdvanceTime: false,
  toFake: [
    'setTimeout', 'clearTimeout',
    'setInterval', 'clearInterval',
    'setImmediate', 'clearImmediate',
    'Date',
    'requestAnimationFrame', 'cancelAnimationFrame',
    'requestIdleCallback', 'cancelIdleCallback',
    'performance',
    'queueMicrotask',
  ],
  now: new Date(2026, 0, 1), // initial system time
  loopLimit: 10_000,
})
```

### Restore Real Timers

```typescript
vi.useRealTimers()
```

Discards all scheduled timers and restores original implementations.

### Check Timer State

```typescript
vi.isFakeTimers() // true if fake timers are active
```

## Advancing Timers

### By Time

```typescript
test('debounce fires after 300ms', () => {
  const fn = vi.fn()
  debounce(fn, 300)()

  vi.advanceTimersByTime(299)
  expect(fn).not.toHaveBeenCalled()

  vi.advanceTimersByTime(1)
  expect(fn).toHaveBeenCalledOnce()
})
```

### Async Variant

For timers that trigger async operations:

```typescript
test('async timer', async () => {
  const fn = vi.fn(async () => 'done')
  setTimeout(fn, 1000)

  await vi.advanceTimersByTimeAsync(1000)
  expect(fn).toHaveBeenCalled()
})
```

### To Next Timer

```typescript
test('advance one timer at a time', () => {
  const fn1 = vi.fn()
  const fn2 = vi.fn()

  setTimeout(fn1, 100)
  setTimeout(fn2, 200)

  vi.advanceTimersToNextTimer()
  expect(fn1).toHaveBeenCalled()
  expect(fn2).not.toHaveBeenCalled()

  vi.advanceTimersToNextTimer()
  expect(fn2).toHaveBeenCalled()
})
```

### To Next Frame

Advance to the next `requestAnimationFrame` callback:

```typescript
vi.advanceTimersToNextFrame()
```

## Running Timers

### Run All Timers

Execute all pending and subsequently created timers until the queue is empty:

```typescript
test('run all timers', () => {
  const fn = vi.fn()
  setTimeout(fn, 1000)
  setTimeout(fn, 2000)

  vi.runAllTimers()
  expect(fn).toHaveBeenCalledTimes(2)
})
```

Has a `loopLimit` safety valve (default: 10,000) to prevent infinite loops with recursive timers.

### Async Variant

```typescript
await vi.runAllTimersAsync()
```

### Run Only Pending Timers

Execute only timers that are currently queued, ignoring new timers created during execution:

```typescript
test('pending only', () => {
  const fn = vi.fn(() => {
    setTimeout(fn, 100) // this won't be run
  })
  setTimeout(fn, 100)

  vi.runOnlyPendingTimers()
  expect(fn).toHaveBeenCalledTimes(1)
})
```

### Run All Ticks

Execute all microtasks (process.nextTick callbacks):

```typescript
vi.runAllTicks()
```

### Clear All Timers

Remove all scheduled timers without executing them:

```typescript
vi.clearAllTimers()
```

## Timer Queries

```typescript
vi.getTimerCount() // number of pending timers
```

## System Time Mocking

### Set System Time

Control what `new Date()` and `Date.now()` return:

```typescript
test('mock date', () => {
  vi.setSystemTime(new Date(2026, 0, 15, 12, 0, 0))

  expect(new Date().getFullYear()).toBe(2026)
  expect(new Date().getMonth()).toBe(0)
  expect(Date.now()).toBe(new Date(2026, 0, 15, 12, 0, 0).getTime())
})
```

Accepts `Date`, number (timestamp), or string:

```typescript
vi.setSystemTime(new Date('2026-01-15'))
vi.setSystemTime(1737158400000)
vi.setSystemTime('2026-01-15T12:00:00Z')
```

**Important:** `setSystemTime` does NOT fire any timers — it only moves the clock.

### Get Mocked Time

```typescript
vi.getMockedSystemTime() // Date | null
```

Returns `null` if system time is not mocked.

### Get Real Time

```typescript
vi.getRealSystemTime() // number (ms since epoch)
```

Returns the actual system time even when fake timers are active.

## Timer Tick Modes

Control automatic timer advancement (v4.x):

```typescript
vi.setTimerTickMode('manual')           // default: timers only advance via vi.advanceTimers*
vi.setTimerTickMode('nextTimerAsync')   // auto-advance to next timer on await
vi.setTimerTickMode('interval', 20)     // auto-advance every N ms of real time
```

## Practical Patterns

### Testing Debounce

```typescript
import { vi, test, expect } from 'vitest'
import { debounce } from './utils'

test('debounce delays execution', () => {
  vi.useFakeTimers()
  const fn = vi.fn()
  const debounced = debounce(fn, 500)

  debounced()
  debounced()
  debounced()

  expect(fn).not.toHaveBeenCalled()
  vi.advanceTimersByTime(500)
  expect(fn).toHaveBeenCalledOnce()

  vi.useRealTimers()
})
```

### Testing setInterval

```typescript
test('polling stops after success', () => {
  vi.useFakeTimers()
  let attempts = 0
  const poll = vi.fn(() => {
    attempts++
    if (attempts >= 3) clearInterval(id)
  })
  const id = setInterval(poll, 1000)

  vi.advanceTimersByTime(3000)
  expect(poll).toHaveBeenCalledTimes(3)

  vi.advanceTimersByTime(5000)
  expect(poll).toHaveBeenCalledTimes(3) // stopped

  vi.useRealTimers()
})
```

### Testing Date-Dependent Logic

```typescript
test('subscription is expired', () => {
  vi.useFakeTimers()
  vi.setSystemTime(new Date('2026-06-01'))

  const subscription = {
    expiresAt: new Date('2026-05-01'),
    isExpired() { return new Date() > this.expiresAt },
  }

  expect(subscription.isExpired()).toBe(true)

  vi.setSystemTime(new Date('2026-04-01'))
  expect(subscription.isExpired()).toBe(false)

  vi.useRealTimers()
})
```

### Testing Retry with Backoff

```typescript
test('retries with exponential backoff', async () => {
  vi.useFakeTimers()
  const api = vi.fn()
    .mockRejectedValueOnce(new Error('fail'))
    .mockRejectedValueOnce(new Error('fail'))
    .mockResolvedValue('success')

  const promise = retryWithBackoff(api, { maxRetries: 3, baseDelay: 1000 })

  await vi.advanceTimersByTimeAsync(1000) // 1st retry delay
  await vi.advanceTimersByTimeAsync(2000) // 2nd retry delay

  const result = await promise
  expect(result).toBe('success')
  expect(api).toHaveBeenCalledTimes(3)

  vi.useRealTimers()
})
```

### Config-Level Fake Timers

```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    fakeTimers: {
      shouldAdvanceTime: true,
      now: new Date('2026-01-01'),
    },
  },
})
```

---

**Related:** [03-mocking.md](03-mocking.md) for general mocking, [01-writing-tests.md](01-writing-tests.md) for lifecycle hooks
