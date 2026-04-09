# React & Client Integration

> Source: [docs.convex.dev/client/react](https://docs.convex.dev/client/react) | convex v1.34.x

## Table of Contents

- [Setup](#setup)
- [ConvexProvider](#convexprovider)
- [useQuery](#usequery)
- [useMutation](#usemutation)
- [useAction](#useaction)
- [usePaginatedQuery](#usepaginatedquery)
- [Conditional Queries](#conditional-queries)
- [Loading States](#loading-states)
- [Optimistic Updates](#optimistic-updates)
- [Next.js Integration](#nextjs-integration)
- [Other Frameworks](#other-frameworks)

## Setup

```bash
npm install convex
npx convex dev  # Generates types and starts sync
```

## ConvexProvider

Wrap your app with `ConvexProvider` to enable all Convex hooks:

```tsx
// src/main.tsx
import { ConvexProvider, ConvexReactClient } from "convex/react";

const convex = new ConvexReactClient(import.meta.env.VITE_CONVEX_URL);

function App() {
  return (
    <ConvexProvider client={convex}>
      <YourApp />
    </ConvexProvider>
  );
}
```

The `VITE_CONVEX_URL` (or `NEXT_PUBLIC_CONVEX_URL`) is set automatically by `npx convex dev`.

## useQuery

Subscribe to a query — automatically re-renders when data changes:

```tsx
import { useQuery } from "convex/react";
import { api } from "../convex/_generated/api";

function MessageList() {
  const messages = useQuery(api.messages.list);

  if (messages === undefined) {
    return <Loading />;  // Initial load
  }

  return (
    <ul>
      {messages.map((msg) => (
        <li key={msg._id}>{msg.body}</li>
      ))}
    </ul>
  );
}
```

### With Arguments

```tsx
function ChannelMessages({ channelId }: { channelId: Id<"channels"> }) {
  const messages = useQuery(api.messages.listByChannel, { channelId });
  // ...
}
```

### Return Values

- `undefined` — Query is still loading (initial fetch)
- Actual data — Query has resolved
- The hook **never returns an error** — errors are thrown and caught by error boundaries

## useMutation

Call a mutation function:

```tsx
import { useMutation } from "convex/react";

function SendButton() {
  const sendMessage = useMutation(api.messages.send);

  const handleClick = async () => {
    await sendMessage({ body: "Hello!", author: "Alice" });
  };

  return <button onClick={handleClick}>Send</button>;
}
```

### With Optimistic Updates

```tsx
const sendMessage = useMutation(api.messages.send).withOptimisticUpdate(
  (localStore, args) => {
    const currentMessages = localStore.getQuery(api.messages.list, {});
    if (currentMessages !== undefined) {
      const optimisticMessage = {
        _id: crypto.randomUUID() as Id<"messages">,
        _creationTime: Date.now(),
        body: args.body,
        author: args.author,
      };
      localStore.setQuery(api.messages.list, {}, [
        ...currentMessages,
        optimisticMessage,
      ]);
    }
  },
);
```

## useAction

Call an action function:

```tsx
import { useAction } from "convex/react";

function PayButton({ orderId }: { orderId: Id<"orders"> }) {
  const processPayment = useAction(api.payments.process);
  const [loading, setLoading] = useState(false);

  const handlePay = async () => {
    setLoading(true);
    try {
      const result = await processPayment({ orderId });
      // Handle success
    } catch (error) {
      // Handle error
    } finally {
      setLoading(false);
    }
  };

  return (
    <button onClick={handlePay} disabled={loading}>
      {loading ? "Processing..." : "Pay Now"}
    </button>
  );
}
```

**Reminder:** Prefer mutations over direct action calls from the client. The pattern is: mutation writes intent to DB, then schedules the action.

## usePaginatedQuery

Load data in pages with infinite scroll or "Load More":

```tsx
import { usePaginatedQuery } from "convex/react";

function InfiniteMessages({ channelId }: { channelId: Id<"channels"> }) {
  const { results, status, loadMore } = usePaginatedQuery(
    api.messages.listByChannel,
    { channelId },
    { initialNumItems: 25 },
  );

  return (
    <div>
      {results.map((msg) => (
        <Message key={msg._id} message={msg} />
      ))}

      {status === "CanLoadMore" && (
        <button onClick={() => loadMore(25)}>Load More</button>
      )}
      {status === "LoadingMore" && <Spinner />}
      {status === "Exhausted" && <p>No more messages</p>}
    </div>
  );
}
```

### Status Values

| Status | Meaning |
|--------|---------|
| `"LoadingFirstPage"` | Initial page is loading |
| `"CanLoadMore"` | More pages available |
| `"LoadingMore"` | Next page is loading |
| `"Exhausted"` | All data loaded |

## Conditional Queries

Skip a query when arguments aren't ready:

```tsx
function UserProfile({ userId }: { userId?: Id<"users"> }) {
  // Pass "skip" to disable the query
  const user = useQuery(
    api.users.get,
    userId ? { userId } : "skip",
  );

  if (!userId) return <p>Select a user</p>;
  if (user === undefined) return <Loading />;
  return <p>{user.name}</p>;
}
```

## Loading States

```tsx
function DataView() {
  const data = useQuery(api.data.list);

  // Pattern 1: Simple loading check
  if (data === undefined) return <Skeleton />;

  // Pattern 2: Suspense (experimental)
  // Wrap with <Suspense fallback={<Loading />}>
}
```

### Error Handling

Convex throws errors as exceptions. Use React error boundaries:

```tsx
import { ErrorBoundary } from "react-error-boundary";

function App() {
  return (
    <ErrorBoundary fallback={<ErrorPage />}>
      <ConvexProvider client={convex}>
        <YourApp />
      </ConvexProvider>
    </ErrorBoundary>
  );
}
```

## Optimistic Updates

Show changes instantly before the server confirms:

```tsx
const deleteTask = useMutation(api.tasks.remove).withOptimisticUpdate(
  (localStore, { taskId }) => {
    const tasks = localStore.getQuery(api.tasks.list, {});
    if (tasks !== undefined) {
      localStore.setQuery(
        api.tasks.list,
        {},
        tasks.filter((t) => t._id !== taskId),
      );
    }
  },
);
```

### OptimisticLocalStore API

```typescript
localStore.getQuery(queryRef, args)     // Get cached query result
localStore.setQuery(queryRef, args, value)  // Set optimistic value
```

- Optimistic updates are **temporary** — replaced by server response
- If the mutation fails, the optimistic update is rolled back
- Keep optimistic logic simple — it runs synchronously

## Next.js Integration

### App Router (Server Components)

```tsx
// app/layout.tsx
import { ConvexClientProvider } from "./ConvexClientProvider";

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <ConvexClientProvider>{children}</ConvexClientProvider>
      </body>
    </html>
  );
}
```

```tsx
// app/ConvexClientProvider.tsx
"use client";
import { ConvexProvider, ConvexReactClient } from "convex/react";

const convex = new ConvexReactClient(process.env.NEXT_PUBLIC_CONVEX_URL!);

export function ConvexClientProvider({ children }: { children: React.ReactNode }) {
  return <ConvexProvider client={convex}>{children}</ConvexProvider>;
}
```

### Server-Side Preloading

```tsx
// app/page.tsx
import { preloadQuery } from "convex/nextjs";
import { api } from "../convex/_generated/api";
import { ClientComponent } from "./ClientComponent";

export default async function Page() {
  const preloaded = await preloadQuery(api.messages.list);
  return <ClientComponent preloadedMessages={preloaded} />;
}
```

```tsx
// app/ClientComponent.tsx
"use client";
import { usePreloadedQuery } from "convex/nextjs";
import { Preloaded } from "convex/nextjs";

export function ClientComponent({
  preloadedMessages,
}: {
  preloadedMessages: Preloaded<typeof api.messages.list>;
}) {
  const messages = usePreloadedQuery(preloadedMessages);
  // messages is immediately available (no loading state)
  return <MessageList messages={messages} />;
}
```

### Environment Variables

```env
# .env.local
NEXT_PUBLIC_CONVEX_URL=https://your-deployment.convex.cloud
```

## Other Frameworks

### Vue

```typescript
import { useConvexQuery, useConvexMutation } from "@convex-vue/core";
const messages = useConvexQuery(api.messages.list, {});
const send = useConvexMutation(api.messages.send);
```

### Svelte

```svelte
<script>
  import { useQuery, useMutation } from "convex/svelte";
  const messages = useQuery(api.messages.list, {});
  const send = useMutation(api.messages.send);
</script>
```

### Plain JavaScript/Node.js

```typescript
import { ConvexClient } from "convex/browser";

const client = new ConvexClient(CONVEX_URL);

// One-off query
const messages = await client.query(api.messages.list);

// Subscribe to updates
const unsubscribe = client.onUpdate(api.messages.list, {}, (messages) => {
  console.log("Updated:", messages);
});
```

## Related References

- Queries and mutations: `01-functions-queries-mutations.md`
- Authentication (provider wrapping): `05-authentication.md`
- Pagination: `04-indexes-performance.md`
