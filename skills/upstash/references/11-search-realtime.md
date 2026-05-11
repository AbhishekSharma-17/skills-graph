# Upstash Search & Realtime

## Table of Contents

- [Overview](#overview)
- [Upstash Search](#upstash-search)
- [Upstash Realtime](#upstash-realtime)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

- **Upstash Search**: Lightweight, AI-powered search built on Upstash Vector. Provides full-text and semantic search with filtering, aggregations, and field-level queries — all serverless and pay-per-request.
- **Upstash Realtime**: Channel-based pub/sub messaging over HTTP. No WebSocket server required — uses Server-Sent Events (SSE) for fully serverless real-time communication.

---

## Upstash Search

### What is Upstash Search

Upstash Search delivers full-text and semantic search powered by Upstash Vector. It combines vector embeddings with metadata filtering to provide relevant results without managing infrastructure.

Key capabilities:

- Full-text and semantic search powered by Upstash Vector
- Supports aggregations, query operators, and field-level search
- Metadata filtering with boolean, range, and wildcard operators
- Ideal for blog search, e-commerce product search, user directories, and knowledge bases

### Setup

1. Create a Search index in the Upstash console (or reuse an existing Vector index)
2. Install the SDK:

```bash
npm install @upstash/vector
```

3. Configure environment variables:

```bash
UPSTASH_VECTOR_REST_URL=https://your-index.upstash.io
UPSTASH_VECTOR_REST_TOKEN=your-token
```

4. Initialize the client:

```typescript
import { Index } from "@upstash/vector";

const index = Index.fromEnv();
```

### Query Operators

Supported operators for metadata filtering:

| Operator | Syntax | Example |
|----------|--------|---------|
| Equals | `field = 'value'` | `category = 'tutorial'` |
| Not equals | `field != 'value'` | `status != 'draft'` |
| Greater than | `field > value` | `price > 50` |
| Less than | `field < value` | `price < 100` |
| Greater or equal | `field >= value` | `rating >= 4.0` |
| Less or equal | `field <= value` | `stock <= 10` |
| AND | `expr AND expr` | `category = 'books' AND price < 20` |
| OR | `expr OR expr` | `color = 'red' OR color = 'blue'` |
| IN | `field IN [values]` | `status IN ['active', 'pending']` |
| GLOB | `field GLOB 'pattern'` | `name GLOB 'Pro*'` |
| HAS FIELD | `HAS FIELD field` | `HAS FIELD discount` |
| HAS NOT FIELD | `HAS NOT FIELD field` | `HAS NOT FIELD legacy_id` |

### Aggregation Operators

#### Bucket Aggregations

- **Terms**: Group results by field values (e.g., count products per category)
- **Date histogram**: Group results by time intervals (e.g., posts per month)
- **Range**: Group results by numeric ranges (e.g., price brackets)

#### Metric Aggregations

- **Count**: Total number of matching documents
- **Sum**: Sum of a numeric field across results
- **Avg**: Average value of a numeric field
- **Min**: Minimum value of a numeric field
- **Max**: Maximum value of a numeric field

### Search Recipes

#### Blog Search

```typescript
import { Index } from "@upstash/vector";

const index = Index.fromEnv();

// Index blog posts
await index.upsert([
  {
    id: "post-1",
    data: "Getting started with serverless Redis",
    metadata: {
      title: "Serverless Redis Guide",
      author: "Alice",
      category: "tutorial",
      publishedAt: "2026-01-15",
      tags: ["redis", "serverless"],
    },
  },
  {
    id: "post-2",
    data: "Building real-time dashboards with Upstash",
    metadata: {
      title: "Real-time Dashboards",
      author: "Bob",
      category: "guide",
      publishedAt: "2026-02-10",
      tags: ["realtime", "dashboard"],
    },
  },
]);

// Search with semantic query and metadata filter
const results = await index.query({
  data: "how to use Redis in serverless",
  topK: 10,
  includeMetadata: true,
  filter: "category = 'tutorial'",
});

console.log(results[0].metadata?.title);
// => "Serverless Redis Guide"
```

#### E-commerce Product Search

```typescript
// Index products
await index.upsert([
  {
    id: "product-1",
    data: "Wireless Bluetooth Headphones with Noise Cancellation",
    metadata: {
      name: "ProSound X500",
      price: 79.99,
      category: "electronics",
      brand: "ProSound",
      inStock: true,
      rating: 4.5,
    },
  },
  {
    id: "product-2",
    data: "Over-ear Studio Monitor Headphones for Music Production",
    metadata: {
      name: "AudioPro M200",
      price: 149.99,
      category: "electronics",
      brand: "AudioPro",
      inStock: true,
      rating: 4.8,
    },
  },
]);

// Search with price and availability filters
const results = await index.query({
  data: "wireless headphones",
  topK: 20,
  includeMetadata: true,
  filter: "category = 'electronics' AND price < 100 AND inStock = true",
});
```

#### User Directory Search

```typescript
await index.upsert([
  {
    id: "user-1",
    data: "Alice Johnson — Senior Software Engineer specializing in distributed systems",
    metadata: {
      name: "Alice Johnson",
      role: "Senior Software Engineer",
      department: "Engineering",
      location: "San Francisco",
    },
  },
  {
    id: "user-2",
    data: "Bob Martinez — Data Scientist focused on NLP and recommendation systems",
    metadata: {
      name: "Bob Martinez",
      role: "Data Scientist",
      department: "Engineering",
      location: "New York",
    },
  },
]);

const results = await index.query({
  data: "distributed systems engineer",
  topK: 5,
  includeMetadata: true,
  filter: "department = 'Engineering'",
});
```

---

## Upstash Realtime

### What is Upstash Realtime

Upstash Realtime provides channel-based real-time messaging over HTTP:

- No WebSocket server needed — fully serverless
- Supports server-to-client and client-to-client messaging
- Built on Server-Sent Events (SSE) for broad browser compatibility
- Uses Upstash Redis pub/sub under the hood
- Pay-per-message pricing with no idle costs

### Installation

```bash
npm install @upstash/redis
```

### Server-Side: Publishing Messages

```typescript
import { Redis } from "@upstash/redis";

const redis = Redis.fromEnv();

// Publish a JSON message to a channel
await redis.publish("chat:room-1", JSON.stringify({
  userId: "user-123",
  message: "Hello everyone!",
  timestamp: Date.now(),
}));

// Publish to multiple channels
await Promise.all([
  redis.publish("notifications:user-123", JSON.stringify({ type: "mention" })),
  redis.publish("notifications:user-456", JSON.stringify({ type: "reply" })),
]);
```

### Client-Side: Subscribing to Channels

```typescript
import { Realtime } from "@upstash/realtime";

const realtime = new Realtime({
  url: process.env.NEXT_PUBLIC_UPSTASH_REDIS_REST_URL!,
  token: process.env.NEXT_PUBLIC_UPSTASH_REDIS_REST_TOKEN!, // Use read-only token
});

const channel = realtime.subscribe("chat:room-1");

channel.on("message", (message) => {
  console.log("Received:", message);
});

// Unsubscribe when done
channel.unsubscribe();
```

### Authentication & Authorization

Use read-only REST tokens for client-side subscriptions. Standard (read-write) tokens should only be used on the server for publishing.

Implement channel authorization via middleware:

```typescript
// API route to generate scoped tokens
export async function POST(req: Request) {
  const { userId, channel } = await req.json();

  // Verify user has access to the requested channel
  if (!canAccess(userId, channel)) {
    return new Response("Forbidden", { status: 403 });
  }

  // Return connection details with read-only token
  return Response.json({
    url: process.env.UPSTASH_REDIS_REST_URL,
    token: process.env.UPSTASH_REDIS_REST_READ_ONLY_TOKEN,
    channel,
  });
}
```

### Realtime via REST API (No SDK)

Use the Redis REST API directly for pub/sub without installing an SDK:

```bash
# Subscribe to a channel (SSE stream)
curl -N -X POST "https://us1-example.upstash.io/subscribe/chat:room-1" \
  -H "Authorization: Bearer $READ_ONLY_TOKEN" \
  -H "Accept: text/event-stream"

# Publish a message to a channel
curl -X POST "https://us1-example.upstash.io/publish/chat:room-1/hello" \
  -H "Authorization: Bearer $TOKEN"
```

### Pattern Subscriptions

Subscribe to multiple channels using glob patterns:

```bash
# Subscribe to all chat channels
curl -N -X POST "https://us1-example.upstash.io/psubscribe/chat:*" \
  -H "Authorization: Bearer $READ_ONLY_TOKEN" \
  -H "Accept: text/event-stream"

# Subscribe to all notification channels for a specific user
curl -N -X POST "https://us1-example.upstash.io/psubscribe/notifications:user-123:*" \
  -H "Authorization: Bearer $READ_ONLY_TOKEN" \
  -H "Accept: text/event-stream"
```

### Use Cases

- **Chat applications**: Real-time message delivery across clients
- **Live notifications**: Push alerts without polling
- **Real-time dashboards**: Stream metrics and KPI updates
- **Collaborative editing signals**: Broadcast cursor positions and presence
- **Live sports scores / ticker updates**: Low-latency score feeds
- **IoT device status updates**: Stream sensor data to dashboards

### React Hook Example

```typescript
import { useEffect, useState } from "react";

interface Message {
  userId: string;
  text: string;
  timestamp: number;
}

function useChatMessages(roomId: string) {
  const [messages, setMessages] = useState<Message[]>([]);

  useEffect(() => {
    const eventSource = new EventSource(
      `/api/subscribe?channel=chat:${roomId}`
    );

    eventSource.onmessage = (event) => {
      const message: Message = JSON.parse(event.data);
      setMessages((prev) => [...prev, message]);
    };

    eventSource.onerror = () => {
      eventSource.close();
    };

    return () => eventSource.close();
  }, [roomId]);

  return messages;
}
```

Usage in a component:

```tsx
function ChatRoom({ roomId }: { roomId: string }) {
  const messages = useChatMessages(roomId);

  return (
    <ul>
      {messages.map((msg, i) => (
        <li key={i}>
          <strong>{msg.userId}</strong>: {msg.text}
        </li>
      ))}
    </ul>
  );
}
```

---

## Common Pitfalls

- **Never expose write tokens on the client** -- use read-only tokens for subscriptions and keep write tokens server-side only
- **SSE browser connection limits** -- browsers allow roughly 6 SSE connections per domain; use a single multiplexed connection or HTTP/2 to avoid hitting the cap
- **Realtime is broadcast-only** -- designed for pub/sub patterns, not request-response; use Redis commands or QStash for request-response workflows
- **Messages are fire-and-forget** -- no built-in persistence or delivery guarantees; use Redis Streams if you need message history or at-least-once delivery
- **Pattern subscriptions can be expensive** -- `psubscribe` with broad patterns across many channels increases message processing cost
- **Search relevance depends on metadata** -- well-structured metadata with meaningful fields significantly improves filter accuracy and result quality
- **Search filters use `=` not `==`** -- the filter syntax uses single equals for equality comparison, unlike most programming languages
- **Embedding model selection matters** -- choose an embedding model that matches your content domain for best semantic search accuracy
- **Upsert replaces entire records** -- when updating metadata, include all fields in the upsert call, not just the changed ones
