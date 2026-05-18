# Bun -- Runtime Fundamentals

> Source: [bun.sh/docs/runtime](https://bun.sh/docs/runtime) | Module system, TypeScript, plugins, and globals

## Table of Contents

- [Module Resolution](#module-resolution)
- [TypeScript and JSX Support](#typescript-and-jsx-support)
- [Environment Variables](#environment-variables)
- [Global APIs](#global-apis)
- [Watch Mode and Hot Reloading](#watch-mode-and-hot-reloading)
- [Plugin System](#plugin-system)
- [Node.js Globals Compatibility](#nodejs-globals-compatibility)
- [import.meta Properties](#importmeta-properties)
- [Common Pitfalls](#common-pitfalls)

---

## Module Resolution

Bun uses ESM as its default module system and supports CommonJS for backward compatibility.

```typescript
// ESM (default)
import { serve } from "bun";
import { readFile } from "node:fs/promises";
import * as path from "node:path";
const module = await import("./utils.ts");

// CommonJS (supported)
const fs = require("node:fs");
module.exports = { myFunction };
```

### Resolution order

1. Explicit file path (`./foo.ts`, `../bar.js`)
2. `node:` prefix for built-in modules (`node:fs`)
3. `bun:` prefix for Bun-specific modules (`bun:test`, `bun:sqlite`)
4. Package name from `node_modules` (`hono`, `zod`)
5. Path mapping from `tsconfig.json` `paths` field

### Auto-install missing packages

Bun auto-installs packages on first import if they are not in `node_modules`. Disable in production:

```toml
# bunfig.toml
[install]
auto = "disable"
```

### File extensions resolved automatically

```typescript
// Bun tries: .ts, .tsx, .js, .jsx, .mjs, .cjs, .json, .node
import { handler } from "./routes/users";
// Resolves to ./routes/users.ts, ./routes/users.js, etc.
```

## TypeScript and JSX Support

Bun transpiles TypeScript and JSX natively at runtime with zero configuration.

```typescript
// server.ts -- run directly: bun server.ts
interface User {
  id: number;
  name: string;
  email: string;
}

function greet(user: User): string {
  return `Hello, ${user.name}!`;
}
```

### tsconfig.json integration

Bun reads `tsconfig.json` for path aliases, JSX config, and compiler options.

```json
{
  "compilerOptions": {
    "target": "ESNext",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "paths": {
      "@/*": ["./src/*"],
      "@db/*": ["./src/database/*"]
    }
  }
}
```

```typescript
// Path aliases work immediately
import { db } from "@db/client";
import { UserService } from "@/services/user";

// Type-only imports are stripped at transpile time
import type { User } from "./models";
import { type Request, serve } from "bun";
```

### Decorators

```typescript
// Enable in tsconfig.json with "experimentalDecorators": true
function Log(target: any, key: string, descriptor: PropertyDescriptor) {
  const original = descriptor.value;
  descriptor.value = function (...args: any[]) {
    console.log(`Calling ${key} with`, args);
    return original.apply(this, args);
  };
}

class UserService {
  @Log
  getUser(id: number) {
    return { id, name: "Alice" };
  }
}
```

## Environment Variables

Bun automatically loads `.env` files without requiring the `dotenv` package.

### Loading order (highest to lowest priority)

1. Process environment (already set in shell)
2. `.env.local` (local overrides, gitignored)
3. `.env.production` / `.env.development` / `.env.test` (based on `NODE_ENV`)
4. `.env` (default values)

### Accessing environment variables

```typescript
// Bun.env (recommended -- typed proxy object)
const dbUrl = Bun.env.DATABASE_URL;
const port = Bun.env.PORT ?? "3000";

// process.env (Node.js compatible)
const secret = process.env.JWT_SECRET;

// Validation pattern
if (!Bun.env.API_KEY) {
  throw new Error("API_KEY environment variable is required");
}
```

```bash
# Inline variables for a single command
PORT=4000 bun run server.ts
DATABASE_URL=postgres://localhost/test NODE_ENV=test bun test
```

## Global APIs

### The Bun global object

```typescript
// File I/O
const content = await Bun.file("data.json").text();
const bytes = await Bun.file("image.png").arrayBuffer();
await Bun.write("output.txt", "Hello, world!");
await Bun.write("copy.png", Bun.file("original.png"));

// Hashing (extremely fast native implementation)
const hash = Bun.hash("some string");                    // CityHash64
const passwordHash = await Bun.password.hash("secret");  // Argon2id by default
const valid = await Bun.password.verify("secret", passwordHash);

// Sleep
await Bun.sleep(1000);

// Shell (tagged template for shell commands)
import { $ } from "bun";
const result = await $`ls -la`.text();
const files = await $`find . -name "*.ts"`.lines();

// Runtime info
console.log(Bun.nanoseconds()); // High-resolution timer
console.log(Bun.version);       // "1.3.x"
console.log(Bun.revision);      // Git commit SHA of Bun build
```

### Web-standard globals

```typescript
// fetch (native, no import needed)
const response = await fetch("https://api.example.com/data");
const data = await response.json();

// URL and URLSearchParams
const url = new URL("https://example.com/path?q=bun");
console.log(url.searchParams.get("q")); // "bun"

// crypto
const uuid = crypto.randomUUID();
const buffer = crypto.getRandomValues(new Uint8Array(32));

// TextEncoder / TextDecoder
const encoder = new TextEncoder();
const encoded = encoder.encode("hello");

// structuredClone (deep clone)
const clone = structuredClone({ nested: { value: 42 } });

// AbortController
const controller = new AbortController();
setTimeout(() => controller.abort(), 5000);
const res = await fetch(url, { signal: controller.signal });

// performance
const start = performance.now();
// ... operation ...
console.log(`Took ${performance.now() - start}ms`);
```

## Watch Mode and Hot Reloading

### Watch mode (--watch)

Restarts the entire process when files change. All state is lost on restart.

```bash
bun --watch run server.ts
```

### Hot reloading (--hot)

Reloads modules in-place without restarting the process. Global state is preserved.

```bash
bun --hot run server.ts
```

```typescript
// With --hot, use globalThis to preserve state across reloads
let requestCount = globalThis.requestCount ?? 0;
globalThis.requestCount = requestCount;

const server = Bun.serve({
  port: 3000,
  fetch(req) {
    globalThis.requestCount++;
    return new Response(`Requests: ${globalThis.requestCount}`);
  },
});
```

| Feature | `--watch` | `--hot` |
|---------|-----------|---------|
| Process restart | Full restart | In-place reload |
| Global state | Lost | Preserved |
| Open connections | Dropped | Maintained |
| Use case | General development | Servers, long-running processes |

## Plugin System

Bun's plugin API allows custom loaders and module resolution hooks.

```typescript
// plugins/yaml-loader.ts
import { plugin } from "bun";

plugin({
  name: "yaml-loader",
  setup(build) {
    const { load } = require("js-yaml");

    build.onLoad({ filter: /\.(yaml|yml)$/ }, async (args) => {
      const text = await Bun.file(args.path).text();
      const parsed = load(text);
      return {
        contents: `export default ${JSON.stringify(parsed)}`,
        loader: "js",
      };
    });
  },
});
```

Register plugins via `bunfig.toml` so they load before any application code:

```toml
preload = ["./plugins/yaml-loader.ts"]
```

```typescript
// Now YAML imports work throughout the project
import config from "./config.yaml";
console.log(config.database.host);
```

### Custom module resolution

```typescript
import { plugin } from "bun";

plugin({
  name: "virtual-modules",
  setup(build) {
    build.onResolve({ filter: /^virtual:/ }, (args) => {
      return { path: args.path, namespace: "virtual" };
    });

    build.onLoad({ filter: /.*/, namespace: "virtual" }, (args) => {
      if (args.path === "virtual:build-info") {
        return {
          contents: `export const buildTime = "${new Date().toISOString()}";`,
          loader: "js",
        };
      }
    });
  },
});
```

## Node.js Globals Compatibility

```typescript
// process -- fully available
console.log(process.pid);
console.log(process.cwd());
console.log(process.argv);
console.log(process.env.NODE_ENV);

// Buffer -- globally available without import
const buf = Buffer.from("hello world", "utf-8");
console.log(buf.toString("base64")); // aGVsbG8gd29ybGQ=

// __dirname and __filename (available in both ESM and CJS)
console.log(__dirname);  // /Users/alice/project/src
console.log(__filename); // /Users/alice/project/src/index.ts

// require() works even in ESM files
const fs = require("node:fs");

// setTimeout, setInterval, setImmediate
const timer = setTimeout(() => console.log("delayed"), 1000);
clearTimeout(timer);

// globalThis
globalThis.myGlobal = "accessible everywhere";
```

## import.meta Properties

```typescript
// File information
console.log(import.meta.dir);      // Directory: "/Users/alice/project/src"
console.log(import.meta.file);     // Filename: "index.ts"
console.log(import.meta.path);     // Full path: "/Users/alice/project/src/index.ts"
console.log(import.meta.url);      // URL: "file:///Users/alice/project/src/index.ts"

// Environment (same as Bun.env)
console.log(import.meta.env.NODE_ENV);

// Main module check
if (import.meta.main) {
  console.log("Running as main module");
  startServer();
}

// Resolve a module path
const resolvedPath = import.meta.resolve("./utils");
```

### Practical pattern: entry point guard

```typescript
// src/server.ts
export function createApp() {
  return Bun.serve({
    port: 3000,
    fetch(req) {
      return new Response("Hello!");
    },
  });
}

// Only start server when run directly -- importable for tests
if (import.meta.main) {
  const server = createApp();
  console.log(`Listening on ${server.url}`);
}
```

## Common Pitfalls

### 1. Confusing --watch and --hot behavior

Using `--hot` with code that re-creates listeners or connections on reload causes resource leaks. Use `--watch` for anything other than HTTP servers.

```typescript
// WRONG with --hot: opens a new DB connection on each reload
const db = new Database("mydb.sqlite");

// CORRECT with --hot: reuse existing connection
const db = globalThis.__db ?? (globalThis.__db = new Database("mydb.sqlite"));
```

### 2. Importing from bun: namespace in cross-runtime code

Code importing `bun:test`, `bun:sqlite`, or other `bun:` modules will not run under Node.js. Isolate Bun-specific code if cross-runtime support is needed.

### 3. Assuming .env files load in test mode

`bun test` does not automatically set `NODE_ENV=test`. Set it explicitly:

```bash
NODE_ENV=test bun test
```

Or in `bunfig.toml`:

```toml
[test.env]
NODE_ENV = "test"
```

### 4. Forgetting that auto-install changes the lockfile

When auto-install resolves a missing package, it modifies `bun.lockb` silently. This causes unexpected lockfile diffs in version control.

### 5. Relying on import.meta.url for file paths

`import.meta.url` returns a `file://` URL. Use `import.meta.dir` and `import.meta.path` for file system paths instead.

```typescript
// Fragile: requires URL parsing
const dir = new URL(".", import.meta.url).pathname;

// Better: use Bun's extensions
const dir = import.meta.dir;
```

### 6. Not preloading plugins before they are needed

Plugins must execute before any module that depends on them. Always register via `bunfig.toml` preload.
