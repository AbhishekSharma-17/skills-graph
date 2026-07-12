# Web Development

> Source: https://docs.deno.com/runtime/fundamentals/web_dev/

## Table of Contents

- [Framework Options](#framework-options)
- [Fresh Framework](#fresh-framework)
- [Hono on Deno](#hono-on-deno)
- [Oak Middleware](#oak-middleware)
- [Next.js on Deno](#nextjs-on-deno)
- [Astro on Deno](#astro-on-deno)
- [Vite Integration](#vite-integration)
- [API Development Patterns](#api-development-patterns)
- [Web Standard APIs](#web-standard-apis)
- [Static Site Generation](#static-site-generation)

## Framework Options

| Framework | Type | Best For |
|-----------|------|----------|
| Fresh | Full-stack (Deno-native) | Islands architecture, minimal JS |
| Hono | API/Web (lightweight) | APIs, edge functions, middleware |
| Oak | Middleware (Express-like) | REST APIs, familiar patterns |
| Next.js | Full-stack (React) | React apps, SSR/SSG |
| Astro | Content-focused | Static sites, content-heavy |
| SvelteKit | Full-stack (Svelte) | Svelte applications |

## Fresh Framework

Fresh is the Deno-native full-stack web framework using Preact and islands architecture:

```bash
# Create a Fresh project
deno run -A -r https://fresh.deno.dev my-app
cd my-app
deno task dev
```

### Project Structure

```
my-app/
├── deno.json
├── main.ts           # Entry point
├── fresh.gen.ts      # Auto-generated manifest
├── routes/
│   ├── index.tsx     # / route (server-rendered)
│   ├── about.tsx     # /about route
│   ├── api/
│   │   └── joke.ts  # /api/joke API route
│   └── greet/
│       └── [name].tsx  # /greet/:name dynamic route
├── islands/
│   └── Counter.tsx   # Interactive client component
├── components/
│   └── Button.tsx    # Shared components
└── static/
    └── logo.svg      # Static assets
```

### Server Route

```tsx
// routes/index.tsx
import Counter from "../islands/Counter.tsx";

export default function Home() {
  return (
    <div>
      <h1>Welcome to Fresh</h1>
      <Counter start={0} />
    </div>
  );
}
```

### Island Component (Client-Side Interactive)

```tsx
// islands/Counter.tsx
import { useSignal } from "@preact/signals";

export default function Counter({ start }: { start: number }) {
  const count = useSignal(start);
  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => count.value++}>+1</button>
    </div>
  );
}
```

### API Route

```typescript
// routes/api/users.ts
import { Handlers } from "$fresh/server.ts";

export const handler: Handlers = {
  async GET(_req, _ctx) {
    const users = await db.getUsers();
    return new Response(JSON.stringify(users), {
      headers: { "content-type": "application/json" },
    });
  },

  async POST(req, _ctx) {
    const body = await req.json();
    const user = await db.createUser(body);
    return new Response(JSON.stringify(user), { status: 201 });
  },
};
```

### Dynamic Routes

```tsx
// routes/blog/[slug].tsx
import { PageProps } from "$fresh/server.ts";

export default function BlogPost(props: PageProps) {
  const { slug } = props.params;
  return <article><h1>Post: {slug}</h1></article>;
}
```

## Hono on Deno

Lightweight, fast web framework that works on Deno, Node, and edge platforms:

```typescript
import { Hono } from "npm:hono";
import { cors } from "npm:hono/cors";
import { logger } from "npm:hono/logger";
import { validator } from "npm:hono/validator";

const app = new Hono();

// Middleware
app.use("*", logger());
app.use("/api/*", cors());

// Routes
app.get("/", (c) => c.text("Hello from Hono on Deno!"));

app.get("/api/users/:id", (c) => {
  const id = c.req.param("id");
  return c.json({ id, name: "User" });
});

app.post("/api/users", async (c) => {
  const body = await c.req.json();
  return c.json({ id: crypto.randomUUID(), ...body }, 201);
});

// Grouped routes
const api = new Hono();
api.get("/health", (c) => c.json({ status: "ok" }));
api.get("/version", (c) => c.json({ version: "1.0.0" }));
app.route("/api", api);

// Error handling
app.onError((err, c) => {
  console.error(err);
  return c.json({ error: "Internal Server Error" }, 500);
});

app.notFound((c) => c.json({ error: "Not Found" }, 404));

Deno.serve({ port: 3000 }, app.fetch);
```

### Hono with Validation

```typescript
import { Hono } from "npm:hono";
import { zValidator } from "npm:@hono/zod-validator";
import { z } from "npm:zod";

const app = new Hono();

const createUserSchema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
  age: z.number().int().positive().optional(),
});

app.post(
  "/users",
  zValidator("json", createUserSchema),
  async (c) => {
    const data = c.req.valid("json");
    // data is typed: { name: string, email: string, age?: number }
    return c.json({ id: crypto.randomUUID(), ...data }, 201);
  },
);
```

## Oak Middleware

Express-like middleware framework for Deno:

```typescript
import { Application, Router } from "jsr:@oak/oak";

const app = new Application();
const router = new Router();

// Middleware
app.use(async (ctx, next) => {
  const start = performance.now();
  await next();
  const ms = performance.now() - start;
  ctx.response.headers.set("X-Response-Time", `${ms}ms`);
});

// Routes
router.get("/", (ctx) => {
  ctx.response.body = "Hello from Oak!";
});

router.get("/api/users/:id", (ctx) => {
  const id = ctx.params.id;
  ctx.response.body = { id, name: "User" };
});

router.post("/api/users", async (ctx) => {
  const body = await ctx.request.body.json();
  ctx.response.status = 201;
  ctx.response.body = { id: crypto.randomUUID(), ...body };
});

app.use(router.routes());
app.use(router.allowedMethods());

await app.listen({ port: 8000 });
```

## Next.js on Deno

Run Next.js applications directly on Deno:

```bash
# Create Next.js project with Deno
deno run -A npm:create-next-app@latest my-next-app
cd my-next-app
deno task dev
```

### deno.json for Next.js

```jsonc
{
  "tasks": {
    "dev": "deno run -A npm:next dev",
    "build": "deno run -A npm:next build",
    "start": "deno run -A npm:next start"
  },
  "nodeModulesDir": "auto"
}
```

## Astro on Deno

```bash
# Create Astro project
deno run -A npm:create-astro@latest my-astro-app
cd my-astro-app

# Add Deno adapter
deno run -A npm:astro add @astrojs/deno
```

```jsonc
// deno.json
{
  "tasks": {
    "dev": "deno run -A npm:astro dev",
    "build": "deno run -A npm:astro build",
    "preview": "deno run --allow-net --allow-read ./dist/server/entry.mjs"
  },
  "nodeModulesDir": "auto"
}
```

## Vite Integration

Use Vite as a build tool with Deno:

```bash
deno run -A npm:create-vite@latest my-vite-app -- --template react-ts
cd my-vite-app
deno install
deno task dev
```

```jsonc
// deno.json
{
  "tasks": {
    "dev": "deno run -A npm:vite",
    "build": "deno run -A npm:vite build",
    "preview": "deno run -A npm:vite preview"
  },
  "nodeModulesDir": "auto",
  "compilerOptions": {
    "jsx": "react-jsx",
    "jsxImportSource": "react"
  }
}
```

## API Development Patterns

### RESTful API with Deno.serve

```typescript
Deno.serve(async (req) => {
  const url = new URL(req.url);
  const path = url.pathname;
  const method = req.method;

  // CORS
  if (method === "OPTIONS") {
    return new Response(null, {
      headers: {
        "access-control-allow-origin": "*",
        "access-control-allow-methods": "GET, POST, PUT, DELETE",
        "access-control-allow-headers": "content-type, authorization",
      },
    });
  }

  // Route: GET /api/users
  if (method === "GET" && path === "/api/users") {
    const users = await getUsers();
    return Response.json(users);
  }

  // Route: POST /api/users
  if (method === "POST" && path === "/api/users") {
    const body = await req.json();
    const user = await createUser(body);
    return Response.json(user, { status: 201 });
  }

  // Route: GET /api/users/:id
  const userMatch = new URLPattern({ pathname: "/api/users/:id" }).exec(req.url);
  if (method === "GET" && userMatch) {
    const id = userMatch.pathname.groups.id!;
    const user = await getUser(id);
    if (!user) return Response.json({ error: "Not found" }, { status: 404 });
    return Response.json(user);
  }

  return Response.json({ error: "Not found" }, { status: 404 });
});
```

### Middleware Pattern

```typescript
type Handler = (req: Request) => Response | Promise<Response>;
type Middleware = (req: Request, next: Handler) => Response | Promise<Response>;

function compose(...middlewares: Middleware[]): Handler {
  return (req: Request) => {
    let index = 0;
    const next: Handler = (req) => {
      if (index >= middlewares.length) {
        return new Response("Not Found", { status: 404 });
      }
      const mw = middlewares[index++];
      return mw(req, next);
    };
    return next(req);
  };
}

// Usage
const handler = compose(
  loggingMiddleware,
  corsMiddleware,
  authMiddleware,
  routerMiddleware,
);

Deno.serve(handler);
```

## Web Standard APIs

Deno provides browser-compatible web APIs for server-side use:

```typescript
// FormData (file uploads)
Deno.serve(async (req) => {
  const form = await req.formData();
  const file = form.get("file") as File;
  const content = await file.arrayBuffer();
  await Deno.writeFile(`./uploads/${file.name}`, new Uint8Array(content));
  return new Response("Uploaded!");
});

// Headers API
const headers = new Headers();
headers.set("content-type", "application/json");
headers.append("set-cookie", "session=abc");

// Response.json() shorthand
return Response.json({ data: "value" });
return Response.redirect("https://example.com");

// Request clone (for reading body twice)
const clone = req.clone();
const text = await clone.text();
const json = await req.json();
```

## Static Site Generation

### Using Deno + Lume

```bash
# Create Lume project
deno run -A https://deno.land/x/lume/init.ts
deno task build  # Generates static _site/
deno task serve  # Preview locally
```

### DIY Static Generator

```typescript
import { walk } from "jsr:@std/fs";
import { join, relative } from "jsr:@std/path";

const CONTENT_DIR = "./content";
const OUTPUT_DIR = "./dist";

for await (const entry of walk(CONTENT_DIR, { exts: [".md"] })) {
  const markdown = await Deno.readTextFile(entry.path);
  const html = renderMarkdown(markdown); // Your markdown renderer
  const outPath = join(OUTPUT_DIR, relative(CONTENT_DIR, entry.path).replace(".md", ".html"));
  await Deno.mkdir(join(OUTPUT_DIR, relative(CONTENT_DIR, entry.path, "..")), { recursive: true });
  await Deno.writeTextFile(outPath, wrapInLayout(html));
}
```

## Common Pitfalls

1. **Framework compatibility** — not all Vite plugins work with Deno; check compatibility first
2. **node_modules required** — Next.js, Astro, and Vite need `"nodeModulesDir": "auto"` in deno.json
3. **Permission scope** — web frameworks often need broad permissions (`-A`) during development
4. **Fresh vs traditional SPA** — Fresh sends no JS by default; only islands get client-side code
5. **Port conflicts** — Fresh defaults to 8000, Vite to 5173, Next.js to 3000
6. **Hot reload** — use `--watch` for Deno.serve apps, or framework-specific dev servers
