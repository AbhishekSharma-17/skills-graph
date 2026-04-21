# tRPC — Client & Links

> Source: [trpc.io/docs/client/links](https://trpc.io/docs/client/links) | Version: 11.16.0

## Table of Contents

- [Vanilla Client](#vanilla-client)
- [Links Overview](#links-overview)
- [httpBatchLink](#httpbatchlink)
- [httpLink](#httplink)
- [httpBatchStreamLink](#httpbatchstreamlink)
- [splitLink](#splitlink)
- [loggerLink](#loggerlink)
- [httpSubscriptionLink](#httpsubscriptionlink)
- [wsLink](#wslink)
- [Custom Links](#custom-links)
- [Headers and Authorization](#headers-and-authorization)

## Vanilla Client

The vanilla client works in any TypeScript environment (Node.js, browser, edge):

```typescript
import { createTRPCClient, httpBatchLink } from '@trpc/client';
import type { AppRouter } from './server/router';

const trpc = createTRPCClient<AppRouter>({
  links: [
    httpBatchLink({
      url: 'http://localhost:3000/api/trpc',
    }),
  ],
});

// Queries
const user = await trpc.user.getById.query({ id: '1' });

// Mutations
const newPost = await trpc.post.create.mutate({
  title: 'Hello',
  content: 'World',
});

// Subscriptions (with httpSubscriptionLink in splitLink)
const subscription = trpc.chat.onMessage.subscribe(
  { channelId: 'general' },
  {
    onData(message) { console.log(message); },
    onError(err) { console.error(err); },
  },
);
```

## Links Overview

Links form a chain that processes each tRPC operation. They're similar to middleware on the client side:

```
Client call → Link 1 → Link 2 → ... → Terminating Link → HTTP → Server
```

Rules:
- The chain **must** end with exactly one **terminating link** (httpBatchLink, httpLink, wsLink, etc.)
- Non-terminating links (loggerLink, splitLink) can be placed before
- Links execute in order for requests, and in reverse for responses

## httpBatchLink

The default and most common link. Batches multiple tRPC calls made in the same tick into a single HTTP request:

```typescript
import { httpBatchLink } from '@trpc/client';

const trpc = createTRPCClient<AppRouter>({
  links: [
    httpBatchLink({
      url: 'http://localhost:3000/api/trpc',
      maxURLLength: 2083, // Switch to POST for long URLs
    }),
  ],
});
```

Batching behavior:
- Multiple calls in the same event loop tick are combined
- Queries use GET (cacheable by CDN/browser), mutations use POST
- If the combined URL exceeds `maxURLLength`, it switches to POST

### Configuration Options

```typescript
httpBatchLink({
  url: 'http://localhost:3000/api/trpc',
  maxURLLength: 2083,

  // Custom headers per request
  headers() {
    return {
      Authorization: `Bearer ${getToken()}`,
    };
  },

  // Custom fetch implementation
  fetch(url, options) {
    return fetch(url, { ...options, credentials: 'include' });
  },

  // Transformer for Date, Map, Set, BigInt, etc.
  transformer: superjson,
});
```

## httpLink

Non-batching link — one HTTP request per tRPC call. Use when batching causes issues (e.g., debugging, specific caching needs):

```typescript
import { httpLink } from '@trpc/client';

const trpc = createTRPCClient<AppRouter>({
  links: [
    httpLink({
      url: 'http://localhost:3000/api/trpc',
    }),
  ],
});
```

## httpBatchStreamLink

Like `httpBatchLink`, but streams responses as they become available instead of waiting for all to complete:

```typescript
import { httpBatchStreamLink } from '@trpc/client';

const trpc = createTRPCClient<AppRouter>({
  links: [
    httpBatchStreamLink({
      url: 'http://localhost:3000/api/trpc',
    }),
  ],
});
```

Benefits:
- Fast queries return immediately without waiting for slow ones
- Supports streaming generators from procedures
- Better perceived performance for batch requests

Limitations:
- Cannot set response headers after stream starts (no cookies)
- Requires server adapter support

## splitLink

Conditionally routes operations to different link chains:

```typescript
import { splitLink, httpBatchLink, httpSubscriptionLink } from '@trpc/client';

const trpc = createTRPCClient<AppRouter>({
  links: [
    splitLink({
      condition(op) {
        return op.type === 'subscription';
      },
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

### Multi-Way Splitting

```typescript
const trpc = createTRPCClient<AppRouter>({
  links: [
    splitLink({
      condition: (op) => op.type === 'subscription',
      true: httpSubscriptionLink({ url: '/api/trpc' }),
      false: splitLink({
        condition: (op) => op.path.startsWith('streaming.'),
        true: httpBatchStreamLink({ url: '/api/trpc' }),
        false: httpBatchLink({ url: '/api/trpc' }),
      }),
    }),
  ],
});
```

## loggerLink

Logs all operations for debugging:

```typescript
import { loggerLink } from '@trpc/client';

const trpc = createTRPCClient<AppRouter>({
  links: [
    loggerLink({
      enabled: (opts) =>
        process.env.NODE_ENV === 'development' ||
        (opts.direction === 'down' && opts.result instanceof Error),
    }),
    httpBatchLink({
      url: 'http://localhost:3000/api/trpc',
    }),
  ],
});
```

Output example:
```
▲ query user.getById { id: '1' }
▼ query user.getById — 23ms { id: '1', name: 'Alice' }
```

### Custom Logger

```typescript
loggerLink({
  logger(opts) {
    if (opts.direction === 'up') {
      console.log(`→ ${opts.type} ${opts.path}`, opts.input);
    } else {
      const duration = opts.elapsedMs;
      if (opts.result instanceof Error) {
        console.error(`← ${opts.type} ${opts.path} ERROR [${duration}ms]`, opts.result);
      } else {
        console.log(`← ${opts.type} ${opts.path} OK [${duration}ms]`);
      }
    }
  },
});
```

## httpSubscriptionLink

Terminating link for SSE-based subscriptions:

```typescript
import { httpSubscriptionLink } from '@trpc/client';

// Used with splitLink (subscriptions only)
httpSubscriptionLink({
  url: 'http://localhost:3000/api/trpc',

  // Reconnection settings
  eventSourceOptions() {
    return {
      withCredentials: true,
    };
  },
});
```

See `08-subscriptions-streaming.md` for full subscription details.

## wsLink

WebSocket-based link for subscriptions (legacy approach — SSE is recommended in v11):

```typescript
import { createWSClient, wsLink } from '@trpc/client';

const wsClient = createWSClient({
  url: 'ws://localhost:3001',
});

// Used with splitLink (subscriptions only)
wsLink({ client: wsClient });
```

## Custom Links

Create links for cross-cutting concerns:

```typescript
import { type TRPCLink } from '@trpc/client';
import { observable } from '@trpc/server/observable';
import type { AppRouter } from './server/router';

const retryLink: TRPCLink<AppRouter> = () => {
  return ({ next, op }) => {
    return observable((observer) => {
      let attempts = 0;
      const maxRetries = 3;

      const execute = () => {
        attempts++;
        const subscription = next(op).subscribe({
          next(value) {
            observer.next(value);
          },
          error(err) {
            if (attempts < maxRetries && err.data?.httpStatus === 503) {
              setTimeout(execute, 1000 * attempts);
            } else {
              observer.error(err);
            }
          },
          complete() {
            observer.complete();
          },
        });
      };

      execute();
    });
  };
};
```

## Headers and Authorization

### Static Headers

```typescript
httpBatchLink({
  url: '/api/trpc',
  headers: {
    'x-api-key': 'my-api-key',
  },
});
```

### Dynamic Headers (Bearer Token)

```typescript
httpBatchLink({
  url: '/api/trpc',
  async headers() {
    const token = await getAccessToken();
    return {
      Authorization: token ? `Bearer ${token}` : undefined,
    };
  },
});
```

### Per-Operation Headers

```typescript
httpBatchLink({
  url: '/api/trpc',
  headers({ opList }) {
    // opList contains all operations in the batch
    const needsAuth = opList.some(op => op.path.startsWith('protected.'));
    return needsAuth
      ? { Authorization: `Bearer ${getToken()}` }
      : {};
  },
});
```

## Common Pitfalls

1. **Links array must end with a terminating link** — `httpBatchLink`, `httpLink`, `wsLink`, or `httpSubscriptionLink`. Forgetting this causes a runtime error.

2. **`splitLink` branches must also end with terminating links** — each branch is its own complete link chain.

3. **`loggerLink` goes before terminating links** — it's a pass-through link that needs to wrap the terminating link to see both request and response.

4. **Don't use `httpBatchStreamLink` if you need to set cookies** — response headers can't be modified once streaming starts. Use `httpBatchLink` for cookie-setting procedures.
