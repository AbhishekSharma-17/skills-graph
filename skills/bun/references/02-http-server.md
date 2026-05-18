# Bun -- HTTP Server

> Source: [bun.sh/docs/api/http](https://bun.sh/docs/api/http) | Bun.serve() API and request handling

## Table of Contents

- [Bun.serve() Basics](#bunserve-basics)
- [Request Object](#request-object)
- [Response Object](#response-object)
- [Route-Based Dispatch](#route-based-dispatch)
- [Static File Serving](#static-file-serving)
- [TLS and HTTPS](#tls-and-https)
- [Server Lifecycle](#server-lifecycle)
- [Streaming Responses](#streaming-responses)
- [Error Handling](#error-handling)
- [Performance Tips](#performance-tips)
- [Common Pitfalls](#common-pitfalls)

---

## Bun.serve() Basics

```typescript
const server = Bun.serve({
  port: 3000,
  hostname: "0.0.0.0",

  fetch(req: Request): Response | Promise<Response> {
    return new Response("Hello from Bun!");
  },
});

console.log(`Server running at ${server.url}`);
```

When no port is specified, Bun defaults to `3000` or `PORT` from the environment. The fetch handler can be async for I/O operations:

```typescript
Bun.serve({
  port: 3000,
  async fetch(req) {
    const data = await Bun.file("./data.json").json();
    return Response.json(data);
  },
});
```

## Request Object

The `req` parameter is a standard Web API `Request` with full URL, method, headers, and body access.

```typescript
Bun.serve({
  async fetch(req) {
    const url = new URL(req.url);
    console.log(req.method);           // "GET", "POST", etc.
    console.log(url.pathname);         // "/api/users"
    console.log(url.searchParams);     // URLSearchParams object

    const auth = req.headers.get("Authorization");

    // Body parsing methods
    const json = await req.json();           // Parse JSON body
    const text = await req.text();           // Raw text body
    const form = await req.formData();       // Multipart/form-data
    const binary = await req.arrayBuffer();  // Binary body

    return new Response("OK");
  },
});
```

### File upload handling

```typescript
if (req.method === "POST" && url.pathname === "/upload") {
  const formData = await req.formData();
  const file = formData.get("file") as File;
  if (file) {
    await Bun.write(`./uploads/${file.name}`, file);
    return Response.json({ uploaded: file.name, size: file.size });
  }
}
```

## Response Object

```typescript
// Plain text
new Response("Hello, world!");

// With status and headers
new Response("Created", {
  status: 201,
  headers: { "Content-Type": "text/plain", "X-Request-Id": crypto.randomUUID() },
});

// JSON (convenience method -- optimized internal path)
Response.json({ message: "Success", data: [1, 2, 3] });
Response.json({ error: "Not Found" }, { status: 404 });

// Redirect
Response.redirect("https://example.com", 301);
Response.redirect("/login", 302);

// HTML
new Response("<h1>Hello</h1>", { headers: { "Content-Type": "text/html" } });

// No content
new Response(null, { status: 204 });

// File response (streamed efficiently)
new Response(Bun.file("./public/index.html"));
```

## Route-Based Dispatch

### URL-based routing

```typescript
Bun.serve({
  async fetch(req) {
    const url = new URL(req.url);
    const { pathname } = url;
    const method = req.method;

    if (method === "GET" && pathname === "/") return new Response("Home");
    if (method === "GET" && pathname === "/health") return Response.json({ status: "ok" });

    // Parameterized routes
    const userMatch = pathname.match(/^\/api\/users\/(\d+)$/);
    if (userMatch) {
      const userId = parseInt(userMatch[1]);
      if (method === "GET") return Response.json({ id: userId, name: "Alice" });
      if (method === "DELETE") return new Response(null, { status: 204 });
    }

    if (method === "GET" && pathname === "/api/users") return Response.json({ users: [] });
    if (method === "POST" && pathname === "/api/users") {
      const body = await req.json();
      return Response.json({ id: 1, ...body }, { status: 201 });
    }

    return Response.json({ error: "Not Found" }, { status: 404 });
  },
});
```

### Minimal router abstraction

```typescript
type Handler = (req: Request, params: Record<string, string>) => Response | Promise<Response>;

class Router {
  private routes: { method: string; pattern: RegExp; names: string[]; handler: Handler }[] = [];

  private add(method: string, path: string, handler: Handler) {
    const names: string[] = [];
    const pattern = new RegExp(
      "^" + path.replace(/:(\w+)/g, (_, n) => { names.push(n); return "([^/]+)"; }) + "$"
    );
    this.routes.push({ method, pattern, names, handler });
  }

  get(path: string, handler: Handler) { this.add("GET", path, handler); }
  post(path: string, handler: Handler) { this.add("POST", path, handler); }
  put(path: string, handler: Handler) { this.add("PUT", path, handler); }
  delete(path: string, handler: Handler) { this.add("DELETE", path, handler); }

  handle(req: Request): Response | Promise<Response> {
    const url = new URL(req.url);
    for (const r of this.routes) {
      if (r.method !== req.method) continue;
      const m = url.pathname.match(r.pattern);
      if (m) {
        const params: Record<string, string> = {};
        r.names.forEach((n, i) => { params[n] = m[i + 1]; });
        return r.handler(req, params);
      }
    }
    return Response.json({ error: "Not Found" }, { status: 404 });
  }
}

const router = new Router();
router.get("/api/users", async () => Response.json({ users: [] }));
router.get("/api/users/:id", async (_, p) => Response.json({ id: p.id }));
router.post("/api/users", async (req) => Response.json(await req.json(), { status: 201 }));

Bun.serve({ port: 3000, fetch: (req) => router.handle(req) });
```

## Static File Serving

### Pre-allocated static responses (Bun 1.1+)

```typescript
Bun.serve({
  static: {
    "/": new Response(await Bun.file("./public/index.html").text(), {
      headers: { "Content-Type": "text/html" },
    }),
    "/favicon.ico": new Response(await Bun.file("./public/favicon.ico").bytes(), {
      headers: { "Content-Type": "image/x-icon" },
    }),
  },
  fetch(req) { return new Response("API route"); },
});
```

### Dynamic file serving

```typescript
import { join } from "node:path";
const PUBLIC_DIR = join(import.meta.dir, "public");

Bun.serve({
  async fetch(req) {
    const url = new URL(req.url);
    if (url.pathname.startsWith("/static/")) {
      const file = Bun.file(join(PUBLIC_DIR, url.pathname.replace("/static/", "")));
      if (await file.exists()) {
        return new Response(file, {
          headers: { "Cache-Control": "public, max-age=31536000, immutable" },
        });
      }
      return new Response("File not found", { status: 404 });
    }
    return new Response("API");
  },
});
```

## TLS and HTTPS

```typescript
Bun.serve({
  port: 443,
  tls: {
    key: Bun.file("./certs/key.pem"),
    cert: Bun.file("./certs/cert.pem"),
  },
  fetch(req) { return new Response("Secure connection!"); },
});
```

### SNI for multiple domains

```typescript
Bun.serve({
  port: 443,
  tls: {
    key: Bun.file("./certs/default-key.pem"),
    cert: Bun.file("./certs/default-cert.pem"),
    serverName: {
      "api.example.com": {
        key: Bun.file("./certs/api-key.pem"),
        cert: Bun.file("./certs/api-cert.pem"),
      },
    },
  },
  fetch(req) { return new Response(`Hello from ${req.headers.get("host")}`); },
});
```

## Server Lifecycle

```typescript
const server = Bun.serve({
  port: 3000,
  fetch(req) { return new Response("OK"); },
});

console.log(server.url);         // URL { href: "http://localhost:3000/" }
console.log(server.port);        // 3000
console.log(server.hostname);    // "0.0.0.0"
console.log(server.development); // true if NODE_ENV !== "production"

// Hot-reload the fetch handler without dropping connections
server.reload({
  fetch(req) { return new Response("Version 2"); },
});

// Graceful shutdown
process.on("SIGINT", () => { server.stop(); process.exit(0); });
process.on("SIGTERM", () => { server.stop(); process.exit(0); });
```

## Streaming Responses

### ReadableStream

```typescript
Bun.serve({
  fetch(req) {
    const stream = new ReadableStream({
      async start(controller) {
        for (let i = 0; i < 10; i++) {
          controller.enqueue(new TextEncoder().encode(`Chunk ${i}\n`));
          await Bun.sleep(100);
        }
        controller.close();
      },
    });
    return new Response(stream, { headers: { "Content-Type": "text/plain" } });
  },
});
```

### Server-Sent Events (SSE)

```typescript
Bun.serve({
  fetch(req) {
    if (new URL(req.url).pathname !== "/events") return new Response("Not Found", { status: 404 });

    const stream = new ReadableStream({
      async start(controller) {
        const encoder = new TextEncoder();
        let id = 0;
        const interval = setInterval(() => {
          const event = `id: ${id++}\nevent: update\ndata: ${JSON.stringify({
            time: new Date().toISOString(), value: Math.random(),
          })}\n\n`;
          controller.enqueue(encoder.encode(event));
        }, 1000);

        req.signal.addEventListener("abort", () => {
          clearInterval(interval);
          controller.close();
        });
      },
    });

    return new Response(stream, {
      headers: { "Content-Type": "text/event-stream", "Cache-Control": "no-cache" },
    });
  },
});
```

## Error Handling

### Error callback

```typescript
Bun.serve({
  fetch(req) {
    if (new URL(req.url).pathname === "/crash") throw new Error("Something went wrong");
    return new Response("OK");
  },
  error(error) {
    console.error("Server error:", error.message);
    return Response.json(
      { error: "Internal Server Error",
        ...(Bun.env.NODE_ENV !== "production" && { detail: error.message }) },
      { status: 500 }
    );
  },
});
```

### Structured error classes

```typescript
class AppError extends Error {
  constructor(message: string, public statusCode = 500, public code = "INTERNAL_ERROR") {
    super(message);
  }
}
class NotFoundError extends AppError {
  constructor(resource: string) { super(`${resource} not found`, 404, "NOT_FOUND"); }
}
class ValidationError extends AppError {
  constructor(message: string) { super(message, 400, "VALIDATION_ERROR"); }
}

Bun.serve({
  async fetch(req) {
    try {
      if (new URL(req.url).pathname === "/api/users/999") throw new NotFoundError("User");
      return Response.json({ ok: true });
    } catch (err) {
      if (err instanceof AppError) {
        return Response.json({ error: err.code, message: err.message }, { status: err.statusCode });
      }
      console.error("Unexpected error:", err);
      return Response.json({ error: "INTERNAL_ERROR", message: "Unexpected error" }, { status: 500 });
    }
  },
});
```

## Performance Tips

1. **Use Response.json()** instead of `new Response(JSON.stringify(data))` -- optimized internal path.
2. **Use the static option** for known responses -- they skip the fetch handler entirely.
3. **Avoid unnecessary URL parsing** -- use string checks (`req.url.endsWith("/health")`) when you only need the path.
4. **Use Bun.file() in responses** instead of reading into memory -- streams the file directly.
5. **Reuse objects across requests** -- create headers and common responses once at module scope.

```typescript
const CORS_HEADERS = new Headers({
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE",
  "Access-Control-Allow-Headers": "Content-Type, Authorization",
});

Bun.serve({
  static: { "/health": Response.json({ status: "ok" }) },
  fetch(req) {
    if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS_HEADERS });
    return new Response("Dynamic route");
  },
});
```

## Common Pitfalls

### 1. Reusing Response objects

Response bodies can only be consumed once. Returning the same stored Response for multiple requests fails on the second request. Use the `static` option instead, or create a new Response each time.

### 2. Not awaiting body parsing

```typescript
// WRONG: returns a Promise, not the parsed value
const body = req.json();

// CORRECT
const body = await req.json();
```

### 3. Forgetting CORS preflight

Always handle OPTIONS requests in cross-origin scenarios. Missing preflight handling causes browsers to block requests entirely.

### 4. Not cleaning up SSE connections

Server-Sent Events connections stay open indefinitely. Always listen for `req.signal` abort and clean up timers or subscriptions.

### 5. Blocking the event loop in fetch handlers

Long-running synchronous operations block all other requests. Offload CPU-intensive work to a subprocess with `Bun.spawn()`.

### 6. Port conflicts with --watch vs --hot

`--watch` kills and restarts the process, which can briefly fail if the port is not released. Use `--hot` for servers, or use port 0 in tests to let the OS assign a port.
