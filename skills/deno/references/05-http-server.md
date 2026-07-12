# HTTP Server

> Source: https://docs.deno.com/runtime/fundamentals/http_server/

## Table of Contents

- [Deno.serve API](#denoserve-api)
- [Request Handling](#request-handling)
- [Response Patterns](#response-patterns)
- [Routing](#routing)
- [Static File Serving](#static-file-serving)
- [WebSocket Upgrade](#websocket-upgrade)
- [Streaming Responses](#streaming-responses)
- [HTTPS/TLS](#httpstls)
- [Server Configuration](#server-configuration)
- [Graceful Shutdown](#graceful-shutdown)
- [deno serve Command](#deno-serve-command)

## Deno.serve API

`Deno.serve` is the built-in high-performance HTTP server supporting HTTP/1.1 and HTTP/2 with web-standard `Request` and `Response` objects.

### Basic Server

```typescript
Deno.serve((_req: Request) => {
  return new Response("Hello, World!");
});
// Listening on http://0.0.0.0:8000/
```

### With Configuration

```typescript
Deno.serve({
  port: 3000,
  hostname: "0.0.0.0",
  onListen({ port, hostname }) {
    console.log(`Server running at http://${hostname}:${port}/`);
  },
}, handler);
```

### Full Signature

```typescript
Deno.serve(options?: ServeOptions, handler?: ServeHandler): HttpServer;
Deno.serve(handler: ServeHandler): HttpServer;

type ServeHandler = (
  request: Request,
  info: ServeHandlerInfo,
) => Response | Promise<Response>;

interface ServeHandlerInfo {
  remoteAddr: Deno.NetAddr;
  completed: Promise<void>;
}
```

## Request Handling

### Inspecting the Request

```typescript
Deno.serve(async (req: Request) => {
  // Method and URL
  console.log(req.method);           // "GET", "POST", etc.
  const url = new URL(req.url);
  console.log(url.pathname);         // "/api/users"
  console.log(url.searchParams);     // URLSearchParams

  // Headers
  const contentType = req.headers.get("content-type");
  const auth = req.headers.get("authorization");

  // Body (for POST/PUT/PATCH)
  const text = await req.text();
  const json = await req.json();
  const formData = await req.formData();
  const buffer = await req.arrayBuffer();

  return new Response("OK");
});
```

### Client Information

```typescript
Deno.serve((req, info) => {
  const clientIp = info.remoteAddr.hostname;
  const clientPort = info.remoteAddr.port;
  console.log(`Request from ${clientIp}:${clientPort}`);
  return new Response("OK");
});
```

## Response Patterns

### Basic Responses

```typescript
// Plain text
new Response("Hello, World!");

// JSON
new Response(JSON.stringify({ status: "ok" }), {
  headers: { "content-type": "application/json" },
});

// HTML
new Response("<h1>Hello</h1>", {
  headers: { "content-type": "text/html" },
});

// Status codes
new Response("Not Found", { status: 404 });
new Response(null, { status: 204 }); // No content
new Response(null, { status: 301, headers: { location: "/new-path" } });
```

### Response Helpers

```typescript
function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json" },
  });
}

function redirect(url: string, status = 302): Response {
  return new Response(null, { status, headers: { location: url } });
}

function notFound(): Response {
  return new Response("Not Found", { status: 404 });
}
```

### Setting Headers

```typescript
const response = new Response("OK");
response.headers.set("x-request-id", crypto.randomUUID());
response.headers.set("cache-control", "max-age=3600");
response.headers.append("set-cookie", "session=abc123; HttpOnly");
```

## Routing

### Manual URL Pattern Routing

```typescript
const routes = new Map<URLPattern, (req: Request, match: URLPatternResult) => Response>();

routes.set(
  new URLPattern({ pathname: "/api/users/:id" }),
  (_req, match) => {
    const id = match.pathname.groups.id;
    return new Response(`User: ${id}`);
  },
);

routes.set(
  new URLPattern({ pathname: "/api/posts" }),
  (req) => {
    if (req.method === "GET") return new Response("All posts");
    if (req.method === "POST") return new Response("Created", { status: 201 });
    return new Response("Method Not Allowed", { status: 405 });
  },
);

Deno.serve((req) => {
  for (const [pattern, handler] of routes) {
    const match = pattern.exec(req.url);
    if (match) return handler(req, match);
  }
  return new Response("Not Found", { status: 404 });
});
```

### Using @std/http route()

```typescript
import { route, type Route } from "jsr:@std/http/route";

const routes: Route[] = [
  {
    pattern: new URLPattern({ pathname: "/api/users" }),
    handler: (_req) => new Response("Users list"),
  },
  {
    pattern: new URLPattern({ pathname: "/api/users/:id" }),
    handler: (_req, _info, params) => new Response(`User ${params?.pathname.groups.id}`),
  },
];

function defaultHandler(_req: Request): Response {
  return new Response("Not Found", { status: 404 });
}

Deno.serve(route(routes, defaultHandler));
```

### Using Hono Framework

```typescript
import { Hono } from "npm:hono";

const app = new Hono();

app.get("/", (c) => c.text("Hello!"));
app.get("/api/users/:id", (c) => {
  const id = c.req.param("id");
  return c.json({ id, name: "User" });
});
app.post("/api/users", async (c) => {
  const body = await c.req.json();
  return c.json(body, 201);
});

Deno.serve(app.fetch);
```

## Static File Serving

### Using @std/http File Server

```typescript
import { serveDir } from "jsr:@std/http/file-server";

Deno.serve((req) => {
  const url = new URL(req.url);

  // Serve API routes
  if (url.pathname.startsWith("/api/")) {
    return handleApi(req);
  }

  // Serve static files from ./public
  return serveDir(req, {
    fsRoot: "./public",
    urlRoot: "",
    showDirListing: false,
    enableCors: true,
  });
});
```

### Manual File Serving

```typescript
Deno.serve(async (req) => {
  const url = new URL(req.url);
  const filepath = `./public${url.pathname}`;

  try {
    const file = await Deno.open(filepath, { read: true });
    return new Response(file.readable, {
      headers: { "content-type": getContentType(filepath) },
    });
  } catch {
    return new Response("Not Found", { status: 404 });
  }
});
```

## WebSocket Upgrade

```typescript
Deno.serve((req) => {
  // Check for upgrade request
  if (req.headers.get("upgrade") !== "websocket") {
    return new Response("Expected WebSocket", { status: 426 });
  }

  const { socket, response } = Deno.upgradeWebSocket(req);

  socket.addEventListener("open", () => {
    console.log("Client connected");
  });

  socket.addEventListener("message", (event) => {
    console.log("Received:", event.data);
    socket.send(`Echo: ${event.data}`);
  });

  socket.addEventListener("close", () => {
    console.log("Client disconnected");
  });

  socket.addEventListener("error", (event) => {
    console.error("WebSocket error:", event);
  });

  return response;
});
```

### WebSocket with JSON Messages

```typescript
const { socket, response } = Deno.upgradeWebSocket(req);

socket.addEventListener("message", (event) => {
  const msg = JSON.parse(event.data);

  switch (msg.type) {
    case "ping":
      socket.send(JSON.stringify({ type: "pong", timestamp: Date.now() }));
      break;
    case "subscribe":
      // Handle subscription
      break;
  }
});

return response;
```

## Streaming Responses

### Server-Sent Events (SSE)

```typescript
Deno.serve((_req) => {
  const body = new ReadableStream({
    start(controller) {
      const encoder = new TextEncoder();
      let id = 0;

      const timer = setInterval(() => {
        const data = JSON.stringify({ time: new Date().toISOString(), id: id++ });
        controller.enqueue(encoder.encode(`data: ${data}\n\n`));
      }, 1000);

      // Cleanup on client disconnect
      setTimeout(() => {
        clearInterval(timer);
        controller.close();
      }, 30000);
    },
    cancel() {
      // Client disconnected
    },
  });

  return new Response(body, {
    headers: {
      "content-type": "text/event-stream",
      "cache-control": "no-cache",
      "connection": "keep-alive",
    },
  });
});
```

### Chunked Transfer

```typescript
Deno.serve(async (_req) => {
  const file = await Deno.open("./large-file.csv", { read: true });
  return new Response(file.readable, {
    headers: { "content-type": "text/csv" },
  });
});
```

## HTTPS/TLS

```typescript
const cert = await Deno.readTextFile("./cert.pem");
const key = await Deno.readTextFile("./key.pem");

Deno.serve({
  port: 443,
  cert,
  key,
}, (_req) => new Response("Secure!"));
```

For development, generate self-signed certs:

```bash
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

## Server Configuration

```typescript
Deno.serve({
  port: 8000,                    // Default: 8000
  hostname: "0.0.0.0",          // Default: "0.0.0.0"
  cert: certPem,                 // TLS certificate (PEM)
  key: keyPem,                   // TLS private key (PEM)
  reusePort: true,              // Allow port sharing between processes
  automaticCompression: true,    // Auto gzip/brotli based on Accept-Encoding

  onListen({ port, hostname }) {
    console.log(`Listening on ${hostname}:${port}`);
  },

  onError(error) {
    console.error("Server error:", error);
    return new Response("Internal Server Error", { status: 500 });
  },
}, handler);
```

## Graceful Shutdown

```typescript
const server = Deno.serve(handler);

// Handle termination signals
Deno.addSignalListener("SIGINT", async () => {
  console.log("Shutting down gracefully...");
  await server.shutdown(); // Finishes in-flight requests
  Deno.exit(0);
});

// Or await the server's finished promise
await server.finished;
```

## deno serve Command

Export a default handler to use `deno serve`:

```typescript
// server.ts
export default {
  fetch(request: Request): Response {
    return new Response(`Path: ${new URL(request.url).pathname}`);
  },
} satisfies Deno.ServeDefaultExport;
```

```bash
# Start with automatic port assignment
deno serve server.ts

# Custom port
deno serve --port 3000 server.ts

# Parallel workers for multi-core
deno serve --parallel server.ts
```

## Common Pitfalls

1. **Body consumed twice** — `req.json()` and `req.text()` can only be called once; clone first if needed
2. **Missing await** — handler can be async, but forgetting `await` causes unhandled rejections
3. **WebSocket HTTP/2** — WebSocket upgrade only works over HTTP/1.1 currently
4. **Client disconnect during stream** — always handle the `cancel()` callback in ReadableStream
5. **Port already in use** — use `reusePort: true` or check with `lsof -i :8000`
