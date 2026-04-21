# tRPC — Subscriptions & Streaming

> Source: [trpc.io/docs/server/subscriptions](https://trpc.io/docs/server/subscriptions) | Version: 11.16.0

## Table of Contents

- [Subscriptions Overview](#subscriptions-overview)
- [SSE Subscriptions (Recommended)](#sse-subscriptions-recommended)
- [Generator-Based Subscriptions](#generator-based-subscriptions)
- [Observable-Based Subscriptions](#observable-based-subscriptions)
- [Client-Side Subscription Handling](#client-side-subscription-handling)
- [Streaming Queries and Mutations](#streaming-queries-and-mutations)
- [WebSocket Subscriptions (Legacy)](#websocket-subscriptions-legacy)
- [Production Patterns](#production-patterns)

## Subscriptions Overview

tRPC v11 supports real-time data through two mechanisms:

| Mechanism | Transport | Use Case |
|-----------|-----------|----------|
| **Subscriptions** | SSE or WebSocket | Push updates from server to client |
| **Streaming** | httpBatchStreamLink | Stream response data progressively |

SSE (Server-Sent Events) is the recommended transport for subscriptions in v11. It's simpler than WebSockets, works through proxies/load balancers, and supports automatic reconnection.

## SSE Subscriptions (Recommended)

### Server Setup

```typescript
// server/trpc.ts
import { initTRPC } from '@trpc/server';

const t = initTRPC.create();

export const router = t.router;
export const publicProcedure = t.procedure;
```

```typescript
// server/routers/chat.ts
import { z } from 'zod';
import { router, publicProcedure } from '../trpc';

export const chatRouter = router({
  onMessage: publicProcedure
    .input(z.object({ channelId: z.string() }))
    .subscription(async function* ({ input, signal }) {
      // signal is an AbortSignal — fires when the client disconnects
      const channel = await getChannel(input.channelId);

      for await (const message of channel.subscribe({ signal })) {
        yield message;
      }
    }),
});
```

### Client Setup with splitLink

```typescript
import {
  createTRPCClient,
  httpBatchLink,
  httpSubscriptionLink,
  splitLink,
} from '@trpc/client';
import type { AppRouter } from './server/router';

const trpc = createTRPCClient<AppRouter>({
  links: [
    splitLink({
      condition: (op) => op.type === 'subscription',
      true: httpSubscriptionLink({
        url: 'http://localhost:3000/api/trpc',
      }),
      false: httpBatchLink({
        url: 'http://localhost:3000/api/trpc',
      }),
    }),
  ],
});
```

## Generator-Based Subscriptions

v11's preferred approach uses async generators — clean, readable, with built-in cleanup:

### Basic Generator

```typescript
const appRouter = router({
  countdown: publicProcedure
    .input(z.object({ from: z.number().int().min(1).max(100) }))
    .subscription(async function* ({ input }) {
      for (let i = input.from; i >= 0; i--) {
        yield { remaining: i };
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }),
});
```

### With Cleanup (AbortSignal)

```typescript
const appRouter = router({
  liveMetrics: publicProcedure
    .subscription(async function* ({ signal }) {
      const interval = setInterval(() => {}, 0); // placeholder

      try {
        while (!signal.aborted) {
          const metrics = await collectMetrics();
          yield metrics;
          await new Promise((resolve, reject) => {
            const timeout = setTimeout(resolve, 5000);
            signal.addEventListener('abort', () => {
              clearTimeout(timeout);
              reject(new Error('Aborted'));
            }, { once: true });
          });
        }
      } finally {
        clearInterval(interval);
      }
    }),
});
```

### Event Emitter Pattern

```typescript
import { EventEmitter, on } from 'events';

const ee = new EventEmitter();

const appRouter = router({
  onNotification: publicProcedure
    .input(z.object({ userId: z.string() }))
    .subscription(async function* ({ input, signal }) {
      for await (const [data] of on(ee, `notification:${input.userId}`, {
        signal,
      })) {
        yield data;
      }
    }),
});

// Emit from anywhere in your server code
function sendNotification(userId: string, data: unknown) {
  ee.emit(`notification:${userId}`, data);
}
```

## Observable-Based Subscriptions

The older pattern using observables (still supported):

```typescript
import { observable } from '@trpc/server/observable';

const appRouter = router({
  onUpdate: publicProcedure
    .subscription(() => {
      return observable<{ timestamp: number }>((emit) => {
        const interval = setInterval(() => {
          emit.next({ timestamp: Date.now() });
        }, 1000);

        return () => {
          clearInterval(interval);
        };
      });
    }),
});
```

## Client-Side Subscription Handling

### Vanilla Client

```typescript
const subscription = trpc.chat.onMessage.subscribe(
  { channelId: 'general' },
  {
    onStarted() {
      console.log('Subscription started');
    },
    onData(message) {
      console.log('New message:', message);
      addMessageToUI(message);
    },
    onError(err) {
      console.error('Subscription error:', err);
    },
    onStopped() {
      console.log('Subscription ended');
    },
  },
);

// Unsubscribe when done
subscription.unsubscribe();
```

### React Component

```typescript
'use client';

import { useEffect, useState } from 'react';
import { useTRPC } from '@/trpc/client';

function ChatRoom({ channelId }: { channelId: string }) {
  const trpc = useTRPC();
  const [messages, setMessages] = useState<Message[]>([]);

  useEffect(() => {
    const sub = trpc.chat.onMessage.subscribe(
      { channelId },
      {
        onData(message) {
          setMessages(prev => [...prev, message]);
        },
        onError(err) {
          console.error('Chat error:', err);
        },
      },
    );

    return () => sub.unsubscribe();
  }, [channelId, trpc]);

  return (
    <div>
      {messages.map(msg => (
        <div key={msg.id}>{msg.text}</div>
      ))}
    </div>
  );
}
```

### With React Query (useSubscription)

```typescript
import { useSubscription } from '@trpc/tanstack-react-query';

function LiveMetrics() {
  const trpc = useTRPC();
  const [metrics, setMetrics] = useState<Metrics | null>(null);

  useSubscription(
    trpc.metrics.live.subscriptionOptions(undefined, {
      onData(data) {
        setMetrics(data);
      },
    })
  );

  return metrics ? <MetricsDisplay data={metrics} /> : <Spinner />;
}
```

## Streaming Queries and Mutations

v11 supports streaming responses from queries and mutations using `httpBatchStreamLink`:

### Streaming Query with Generator

```typescript
const appRouter = router({
  streamingSearch: publicProcedure
    .input(z.object({ query: z.string() }))
    .query(async function* ({ input }) {
      // Yield results as they arrive
      for await (const batch of searchWithPagination(input.query)) {
        yield batch;
      }
    }),
});
```

### Deferred Responses

```typescript
const appRouter = router({
  dashboardData: publicProcedure.query(async function* () {
    // Return fast data immediately
    yield {
      summary: await getSummary(), // Fast query
    };

    // Slow queries streamed later
    yield {
      detailedAnalytics: await getDetailedAnalytics(), // Slow query
    };
  }),
});
```

### Client with httpBatchStreamLink

```typescript
const trpc = createTRPCClient<AppRouter>({
  links: [
    httpBatchStreamLink({
      url: '/api/trpc',
    }),
  ],
});

// Streamed results arrive progressively
const result = await trpc.streamingSearch.query({ query: 'typescript' });
```

## WebSocket Subscriptions (Legacy)

Still supported but SSE is preferred in v11:

```typescript
// Server
import { applyWSSHandler } from '@trpc/server/adapters/ws';
import ws from 'ws';

const wss = new ws.Server({ port: 3001 });
applyWSSHandler({ wss, router: appRouter, createContext });

// Client
import { createWSClient, wsLink } from '@trpc/client';

const wsClient = createWSClient({ url: 'ws://localhost:3001' });

const trpc = createTRPCClient<AppRouter>({
  links: [
    splitLink({
      condition: (op) => op.type === 'subscription',
      true: wsLink({ client: wsClient }),
      false: httpBatchLink({ url: 'http://localhost:3000/api/trpc' }),
    }),
  ],
});
```

## Production Patterns

### Heartbeat / Keep-Alive

```typescript
const appRouter = router({
  onEvents: publicProcedure
    .subscription(async function* ({ signal }) {
      let lastEventTime = Date.now();

      while (!signal.aborted) {
        const events = await pollEvents({ since: lastEventTime, signal });

        if (events.length > 0) {
          for (const event of events) {
            yield event;
          }
          lastEventTime = events[events.length - 1].timestamp;
        }

        await sleep(1000, signal);
      }
    }),
});
```

### Reconnection Handling

SSE automatically reconnects. Configure on the client:

```typescript
httpSubscriptionLink({
  url: '/api/trpc',
  eventSourceOptions: () => ({
    withCredentials: true,
  }),
});
```

### Scaling with Redis Pub/Sub

```typescript
import Redis from 'ioredis';

const subscriber = new Redis();
const publisher = new Redis();

const appRouter = router({
  onMessage: publicProcedure
    .input(z.object({ channel: z.string() }))
    .subscription(async function* ({ input, signal }) {
      const sub = subscriber.duplicate();
      await sub.subscribe(input.channel);

      try {
        for await (const [channel, message] of sub.createStream({ signal })) {
          yield JSON.parse(message);
        }
      } finally {
        await sub.unsubscribe(input.channel);
        sub.disconnect();
      }
    }),
});

// Publish from anywhere
async function broadcast(channel: string, data: unknown) {
  await publisher.publish(channel, JSON.stringify(data));
}
```

## Common Pitfalls

1. **Always use `splitLink` for subscriptions** — subscriptions need their own terminating link (`httpSubscriptionLink` or `wsLink`), separate from query/mutation links.

2. **Handle the `signal` parameter** — generator subscriptions receive an `AbortSignal`. Check `signal.aborted` in loops and pass it to async operations for clean shutdown.

3. **SSE doesn't support binary data** — if you need to stream binary, use WebSockets or httpBatchStreamLink with Blob support.

4. **Don't forget cleanup in generators** — use `try/finally` blocks to clean up resources (timers, listeners, connections) when the subscription ends.
