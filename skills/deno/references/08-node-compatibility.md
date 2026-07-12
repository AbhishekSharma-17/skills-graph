# Node.js Compatibility

> Source: https://docs.deno.com/runtime/reference/node/

## Table of Contents

- [Compatibility Overview](#compatibility-overview)
- [Built-in Node Modules](#built-in-node-modules)
- [npm Package Support](#npm-package-support)
- [package.json Support](#packagejson-support)
- [CommonJS Support](#commonjs-support)
- [Global Variables](#global-variables)
- [Node Modules Directory](#node-modules-directory)
- [Native Addons](#native-addons)
- [Migration from Node.js](#migration-from-nodejs)
- [Compatibility Limitations](#compatibility-limitations)

## Compatibility Overview

Deno 2.x provides comprehensive Node.js compatibility:
- Over 75% of Node's own test suite passes
- Nearly every `node:` built-in module is implemented
- Full npm package support via `npm:` specifiers
- `package.json` scripts and dependencies work natively
- CommonJS `require()` supported alongside ESM

## Built-in Node Modules

Import Node.js built-in modules using the `node:` prefix:

```typescript
import * as fs from "node:fs/promises";
import * as path from "node:path";
import * as http from "node:http";
import * as crypto from "node:crypto";
import { EventEmitter } from "node:events";
import { Buffer } from "node:buffer";
import * as os from "node:os";
import * as stream from "node:stream";
import * as url from "node:url";
import * as util from "node:util";
import * as zlib from "node:zlib";
import * as child_process from "node:child_process";
import * as net from "node:net";
import * as tls from "node:tls";
import * as readline from "node:readline";
import * as worker_threads from "node:worker_threads";
```

### Supported node: Modules

| Module | Status | Notes |
|--------|--------|-------|
| `node:assert` | Full | All assertion functions |
| `node:buffer` | Full | Buffer class and utilities |
| `node:child_process` | Full | spawn, exec, fork |
| `node:cluster` | Partial | Basic functionality |
| `node:console` | Full | Console output |
| `node:crypto` | Full | Hash, cipher, HMAC, sign/verify |
| `node:dns` | Full | DNS lookups |
| `node:events` | Full | EventEmitter |
| `node:fs` | Full | File system (sync + async) |
| `node:http` | Full | HTTP client/server |
| `node:https` | Full | HTTPS client/server |
| `node:net` | Full | TCP sockets |
| `node:os` | Full | OS information |
| `node:path` | Full | Path manipulation |
| `node:process` | Full | Process info and control |
| `node:querystring` | Full | URL query parsing |
| `node:readline` | Full | Interactive input |
| `node:stream` | Full | Readable/Writable/Transform |
| `node:string_decoder` | Full | String decoding |
| `node:test` | Full | Node's test runner |
| `node:timers` | Full | setTimeout, setInterval |
| `node:tls` | Full | TLS/SSL |
| `node:url` | Full | URL parsing |
| `node:util` | Full | Utilities |
| `node:vm` | Partial | Basic VM contexts |
| `node:worker_threads` | Full | Multi-threading |
| `node:zlib` | Full | Compression |

## npm Package Support

### Installing npm Packages

```bash
# Add to deno.json imports
deno add npm:express
deno add npm:zod
deno add npm:@prisma/client
```

### Import Syntax

```typescript
// Via deno.json import map (recommended)
import { z } from "zod";
import express from "express";

// Direct npm: specifier
import chalk from "npm:chalk@5";
import { Hono } from "npm:hono@4";

// With version range
import _ from "npm:lodash@^4.17.0";

// Scoped packages
import { PrismaClient } from "npm:@prisma/client@^5.0.0";
```

### How npm Packages Work

1. First run downloads packages to a global cache (`~/.cache/deno/npm/`)
2. No local `node_modules` by default (cleaner project directories)
3. Deno resolves the full dependency tree and hoists appropriately
4. Packages run under Deno's permission system

### Permissions for npm Packages

npm packages operate under Deno's security model:

```bash
# If a package reads files, grant read permission
deno run --allow-read main.ts

# If a package needs network
deno run --allow-net main.ts

# If a package reads env vars (common)
deno run --allow-env main.ts

# Combined (common for most npm packages)
deno run -RNE main.ts
```

## package.json Support

Deno understands `package.json` for Node.js project compatibility:

```json
{
  "name": "my-app",
  "type": "module",
  "scripts": {
    "dev": "node server.js",
    "build": "tsc"
  },
  "dependencies": {
    "express": "^4.18.0",
    "zod": "^3.23.0"
  },
  "devDependencies": {
    "@types/express": "^4.17.0"
  }
}
```

### Running Node Projects with Deno

```bash
# Install dependencies
deno install

# Run scripts from package.json
deno task dev

# Run main entry point
deno run -RNE main.js
```

### Using Both deno.json and package.json

They can coexist. Use `deno.json` for Deno tooling and `package.json` for Node compat:

```
project/
├── deno.json       # Deno config: lint, fmt, compiler options
├── package.json    # npm dependencies
├── deno.lock       # Lock file
└── src/
    └── main.ts
```

## CommonJS Support

Deno supports CommonJS modules for Node.js compatibility:

```javascript
// CommonJS module (file.cjs or "type": "commonjs" in package.json)
const fs = require("fs");
const { join } = require("path");

module.exports = { readConfig };
```

### Detection Rules

1. `.cjs` extension → always CommonJS
2. `.mjs` extension → always ESM
3. `package.json` with `"type": "commonjs"` → `.js` files are CJS
4. `package.json` with `"type": "module"` (or missing) → `.js` files are ESM

### Using require() in ESM

```typescript
// Create a require function in ESM context
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);

const config = require("./config.json");
```

## Global Variables

### Available Globals

| Node.js Global | Deno Equivalent | Notes |
|----------------|-----------------|-------|
| `process` | `process` (auto-available) | Full process object |
| `Buffer` | Import from `node:buffer` | Not auto-global |
| `__dirname` | `import.meta.dirname` | Module-level only |
| `__filename` | `import.meta.filename` | Module-level only |
| `global` | `globalThis` | Standard JS |
| `require` | Use `import` or `createRequire` | ESM preferred |
| `console` | `console` | Same |
| `setTimeout` | `setTimeout` | Same |
| `setInterval` | `setInterval` | Same |

### Migration Pattern

```typescript
// Node.js
const dir = __dirname;
const file = __filename;

// Deno
const dir = import.meta.dirname;
const file = import.meta.filename;
```

```typescript
// Node.js
if (require.main === module) { /* entry point */ }

// Deno
if (import.meta.main) { /* entry point */ }
```

## Node Modules Directory

Three modes for managing `node_modules`:

### None (Default)

```jsonc
// deno.json
{ "nodeModulesDir": "none" }
```

- Uses global cache (`~/.cache/deno/npm/`)
- No `node_modules/` in project
- Cleanest for pure Deno projects

### Auto

```jsonc
{ "nodeModulesDir": "auto" }
```

- Creates `node_modules/` automatically on `deno install`
- Required for some tools (Prisma, native addons)
- Uses isolated (pnpm-like) layout by default

### Manual

```jsonc
{ "nodeModulesDir": "manual" }
```

- Requires explicit `deno install` to create `node_modules/`
- Most control over when modules are downloaded

### Linker Strategy

```jsonc
{
  "nodeModulesDir": "auto",
  "nodeModulesLinker": "hoisted"  // npm-style flat layout
}
```

## Native Addons

Node-API (N-API) native addons are supported with limitations:

```bash
# Requires local node_modules
deno install --node-modules-dir

# Requires FFI permission
deno run --allow-ffi --allow-read main.ts

# May need to approve build scripts
deno approve-scripts npm:better-sqlite3
```

### Common Packages with Native Addons

- `better-sqlite3`
- `@prisma/client` (uses engine binary)
- `canvas`
- `sharp`
- `bcrypt`

## Migration from Node.js

### Step-by-Step Migration

1. **Add deno.json** alongside existing package.json:

```jsonc
{
  "tasks": {
    "dev": "deno run --watch -RNE src/main.ts"
  },
  "nodeModulesDir": "auto"
}
```

2. **Install dependencies**:

```bash
deno install
```

3. **Run the project**:

```bash
deno task dev
# or
deno run -RNE src/main.ts
```

4. **Gradually adopt Deno features**:
   - Replace `require()` with `import`
   - Replace `__dirname` with `import.meta.dirname`
   - Add `deno.json` tasks to replace npm scripts
   - Move deps from `package.json` to `deno.json` imports

### Express to Deno

```typescript
// Works unchanged with Deno!
import express from "npm:express";

const app = express();
app.get("/", (_req, res) => res.json({ message: "Hello from Deno!" }));
app.listen(3000);
```

```bash
deno run --allow-net --allow-read --allow-env server.ts
```

## Compatibility Limitations

| Feature | Status | Workaround |
|---------|--------|------------|
| Native addons | Supported | Needs `node_modules` + `--allow-ffi` |
| `package.json` `bin` scripts | Supported | Via `deno task` |
| npm lifecycle scripts | Gated | Use `deno approve-scripts` |
| `node_modules` layout assumptions | Partial | Use `nodeModulesLinker: "hoisted"` |
| Domain-specific globals | Not supported | Use polyfills |
| `NODE_PATH` | Not supported | Use import maps |
| Debugger protocol differences | Minor | Deno uses Chrome DevTools protocol |

### Known Issue: Types Under node16 Resolution

Some npm packages provide incorrect types:

```typescript
// Workaround: explicit type import
// @ts-types="npm:@types/lodash"
import _ from "npm:lodash";
```

## Common Pitfalls

1. **Missing `node:` prefix** — bare imports like `require("fs")` work but `node:fs` is preferred
2. **Permission errors with npm packages** — common packages need `-RNE` (read, net, env)
3. **Missing node_modules** — Prisma and native addons require `"nodeModulesDir": "auto"`
4. **Build scripts blocked** — use `deno approve-scripts` for packages with postinstall
5. **Type conflicts** — Deno types and `@types/node` can conflict; prefer Deno types
