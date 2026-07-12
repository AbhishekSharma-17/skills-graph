# Standard Library (@std)

> Source: https://docs.deno.com/runtime/fundamentals/standard_library/ | Registry: https://jsr.io/@std

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Core Packages](#core-packages)
- [File System (@std/fs)](#file-system-stdfs)
- [Path Utilities (@std/path)](#path-utilities-stdpath)
- [Assertions (@std/assert)](#assertions-stdassert)
- [Testing Utilities (@std/testing)](#testing-utilities-stdtesting)
- [HTTP Utilities (@std/http)](#http-utilities-stdhttp)
- [Async Utilities (@std/async)](#async-utilities-stdasync)
- [CLI Utilities (@std/cli)](#cli-utilities-stdcli)
- [Collections (@std/collections)](#collections-stdcollections)
- [Data Formats](#data-formats)
- [Encoding (@std/encoding)](#encoding-stdencoding)
- [Crypto (@std/crypto)](#crypto-stdcrypto)

## Overview

The Deno Standard Library is a collection of 43+ audited, modular packages published on JSR under `@std/`. Each package is independently versioned, has zero third-party dependencies, and roughly 70% are cross-compatible with Node.js.

Key principles:
- **Audited** — reviewed by the Deno team
- **Modular** — import only what you need
- **Stable** — follows SemVer strictly
- **Cross-runtime** — many packages work in Node.js and browsers

## Installation

```bash
# Add specific packages
deno add jsr:@std/assert
deno add jsr:@std/path
deno add jsr:@std/fs

# Or add all at once
deno add jsr:@std/assert jsr:@std/path jsr:@std/fs jsr:@std/http

# Direct usage without install
import { join } from "jsr:@std/path@^1.0.0";
```

## Core Packages

| Package | Description |
|---------|-------------|
| `@std/assert` | Assertion functions for testing |
| `@std/async` | Async utilities (delay, debounce, pool) |
| `@std/bytes` | Uint8Array manipulation |
| `@std/cli` | CLI tools (arg parsing, spinners, prompts) |
| `@std/collections` | Array/object utility functions |
| `@std/crypto` | Web Crypto API extensions |
| `@std/csv` | CSV parsing and serialization |
| `@std/encoding` | Hex, base64, varint encoding |
| `@std/expect` | Jest-compatible assertions |
| `@std/fmt` | Colors, printf, duration formatting |
| `@std/fs` | File system helpers (walk, copy, exists) |
| `@std/html` | HTML entity escaping |
| `@std/http` | HTTP server utilities and file serving |
| `@std/json` | Streaming JSON parsing |
| `@std/log` | Configurable logging framework |
| `@std/math` | Basic math utilities |
| `@std/media-types` | MIME type utilities |
| `@std/msgpack` | MessagePack encoding/decoding |
| `@std/net` | Network utilities |
| `@std/path` | Cross-platform path manipulation |
| `@std/random` | Seeded random number generators |
| `@std/regexp` | RegExp utilities |
| `@std/semver` | Semantic versioning |
| `@std/streams` | Web Streams API utilities |
| `@std/testing` | Test utilities (mock, time, BDD, snapshot) |
| `@std/text` | Text manipulation (case, distance) |
| `@std/toml` | TOML parsing/serialization |
| `@std/ulid` | ULID generation |
| `@std/uuid` | UUID generation/validation |
| `@std/xml` | XML parsing/serialization |
| `@std/yaml` | YAML parsing/serialization |

## File System (@std/fs)

```typescript
import {
  copy,
  ensureDir,
  ensureFile,
  exists,
  move,
  walk,
  expandGlob,
} from "jsr:@std/fs";

// Check if path exists
if (await exists("./config.json")) {
  console.log("Config found");
}

// Ensure directory exists (creates recursively)
await ensureDir("./output/reports");

// Ensure file exists (creates if missing)
await ensureFile("./logs/app.log");

// Copy files/directories
await copy("./src", "./backup/src", { overwrite: true });

// Move/rename
await move("./old-name.ts", "./new-name.ts");

// Walk directory tree
for await (const entry of walk("./src", { exts: [".ts"] })) {
  console.log(entry.path); // Full path
  console.log(entry.name); // Filename
  console.log(entry.isFile); // boolean
}

// Glob expansion
for await (const entry of expandGlob("src/**/*.test.ts")) {
  console.log(entry.path);
}
```

## Path Utilities (@std/path)

```typescript
import {
  basename,
  dirname,
  extname,
  join,
  resolve,
  relative,
  parse,
  format,
  normalize,
  isAbsolute,
  fromFileUrl,
  toFileUrl,
  SEP,
} from "jsr:@std/path";

// Join path segments
const configPath = join("src", "config", "app.json");
// → "src/config/app.json"

// Parse path components
const parsed = parse("/home/user/project/main.ts");
// { root: "/", dir: "/home/user/project", base: "main.ts", ext: ".ts", name: "main" }

// Resolve relative to absolute
const abs = resolve("./src/main.ts");

// Get relative path
const rel = relative("/home/user", "/home/user/project/src");
// → "project/src"

// Convert URL to file path
const path = fromFileUrl("file:///home/user/main.ts");
// → "/home/user/main.ts"
```

## Assertions (@std/assert)

```typescript
import {
  assert,
  assertEquals,
  assertExists,
  assertGreater,
  assertInstanceOf,
  assertMatch,
  assertNotEquals,
  assertObjectMatch,
  assertRejects,
  assertStrictEquals,
  assertStringIncludes,
  assertThrows,
} from "jsr:@std/assert";

// Deep equality
assertEquals([1, 2, 3], [1, 2, 3]);

// Reference equality
assertStrictEquals("hello", "hello");

// Partial object match
assertObjectMatch(
  { name: "Alice", age: 30, email: "alice@test.com" },
  { name: "Alice", age: 30 },
);

// Error testing
assertThrows(() => { throw new TypeError("bad"); }, TypeError, "bad");
await assertRejects(async () => { throw new Error("async"); }, Error);

// Type narrowing
assertExists(value); // value is non-null after this
assertInstanceOf(err, TypeError); // err is TypeError after this
```

## Testing Utilities (@std/testing)

```typescript
// Mocking
import { assertSpyCalls, spy, stub } from "jsr:@std/testing/mock";

const fetchSpy = spy(globalThis, "fetch");
// ... call code that uses fetch
assertSpyCalls(fetchSpy, 1);
fetchSpy.restore();

// Time mocking
import { FakeTime } from "jsr:@std/testing/time";

using time = new FakeTime(new Date("2026-06-01"));
time.tick(1000); // Advance 1 second

// BDD style
import { describe, it, beforeEach, afterEach } from "jsr:@std/testing/bdd";

// Snapshot testing
import { assertSnapshot } from "jsr:@std/testing/snapshot";
```

## HTTP Utilities (@std/http)

```typescript
import { serveDir, serveFile } from "jsr:@std/http/file-server";
import { route } from "jsr:@std/http/route";
import { STATUS_CODE, STATUS_TEXT } from "jsr:@std/http/status";
import { UserAgent } from "jsr:@std/http/user-agent";

// Static file server
Deno.serve((req) => serveDir(req, { fsRoot: "./public" }));

// Single file
Deno.serve((req) => serveFile(req, "./index.html"));

// Route helper
Deno.serve(route([
  { pattern: new URLPattern({ pathname: "/api/health" }), handler: () => new Response("OK") },
], () => new Response("Not Found", { status: 404 })));

// Status constants
console.log(STATUS_CODE.OK); // 200
console.log(STATUS_TEXT[404]); // "Not Found"
```

## Async Utilities (@std/async)

```typescript
import {
  deadline,
  debounce,
  delay,
  MuxAsyncIterator,
  Pool,
  retry,
} from "jsr:@std/async";

// Delay execution
await delay(1000); // Wait 1 second

// Timeout a promise
const result = await deadline(fetch("https://api.example.com"), 5000);
// Throws if fetch takes > 5 seconds

// Retry with backoff
const data = await retry(
  () => fetch("https://flaky-api.com/data").then((r) => r.json()),
  { maxAttempts: 3, minTimeout: 1000, multiplier: 2 },
);

// Debounce function calls
const save = debounce((text: string) => {
  Deno.writeTextFileSync("./draft.txt", text);
}, 300);

// Pool concurrent operations
const pool = new Pool(5); // Max 5 concurrent
const results = await Promise.all(
  urls.map((url) => pool.queue(() => fetch(url))),
);
```

## CLI Utilities (@std/cli)

```typescript
import { parseArgs } from "jsr:@std/cli/parse-args";
import { Spinner } from "jsr:@std/cli/spinner";
import { promptSecret } from "jsr:@std/cli/prompt-secret";

// Argument parsing
const args = parseArgs(Deno.args, {
  string: ["name", "output"],
  boolean: ["verbose", "help"],
  alias: { v: "verbose", h: "help", n: "name", o: "output" },
  default: { verbose: false },
});
// deno run main.ts --name=test -v → { name: "test", verbose: true }

// Loading spinner
const spinner = new Spinner({ message: "Processing..." });
spinner.start();
await doWork();
spinner.stop();

// Secret input (hidden)
const password = promptSecret("Enter password: ");
```

## Collections (@std/collections)

```typescript
import {
  chunk,
  deepMerge,
  distinctBy,
  groupBy,
  mapEntries,
  mapValues,
  partition,
  sortBy,
  zip,
} from "jsr:@std/collections";

// Group by key
const grouped = groupBy(users, (u) => u.role);
// { admin: [...], user: [...] }

// Chunk array
const batches = chunk([1, 2, 3, 4, 5], 2);
// [[1, 2], [3, 4], [5]]

// Partition by predicate
const [active, inactive] = partition(users, (u) => u.isActive);

// Sort by property
const sorted = sortBy(users, (u) => u.name);

// Distinct by key
const unique = distinctBy(events, (e) => e.userId);

// Deep merge objects
const config = deepMerge(defaults, overrides);
```

## Data Formats

```typescript
// YAML
import { parse, stringify } from "jsr:@std/yaml";
const data = parse(await Deno.readTextFile("config.yaml"));
const yamlStr = stringify({ key: "value" });

// TOML
import { parse, stringify } from "jsr:@std/toml";
const config = parse(await Deno.readTextFile("config.toml"));

// CSV
import { parse, stringify } from "jsr:@std/csv";
const records = parse(csvText, { skipFirstRow: true });
const csvOutput = stringify(data, { columns: ["name", "age"] });

// JSON (streaming)
import { JsonParseStream } from "jsr:@std/json";
const stream = file.readable
  .pipeThrough(new TextDecoderStream())
  .pipeThrough(new JsonParseStream());
```

## Encoding (@std/encoding)

```typescript
import {
  decodeBase64,
  encodeBase64,
  decodeHex,
  encodeHex,
} from "jsr:@std/encoding";

// Base64
const encoded = encodeBase64("Hello, World!");
const decoded = new TextDecoder().decode(decodeBase64(encoded));

// Hex
const hex = encodeHex(new TextEncoder().encode("hello"));
const bytes = decodeHex(hex);
```

## Crypto (@std/crypto)

```typescript
import { crypto } from "jsr:@std/crypto";

// Hash data
const hash = await crypto.subtle.digest(
  "SHA-256",
  new TextEncoder().encode("hello"),
);
const hashHex = Array.from(new Uint8Array(hash))
  .map((b) => b.toString(16).padStart(2, "0"))
  .join("");

// HMAC
import { encodeHex } from "jsr:@std/encoding";

const key = await crypto.subtle.generateKey(
  { name: "HMAC", hash: "SHA-256" },
  true,
  ["sign", "verify"],
);
const signature = await crypto.subtle.sign(
  "HMAC",
  key,
  new TextEncoder().encode("message"),
);
```

## Common Pitfalls

1. **Version pinning** — always pin `@std` versions in `deno.json` for reproducibility
2. **Subpath imports** — import from specific subpaths: `"jsr:@std/http/file-server"` not `"jsr:@std/http"`
3. **Unstable packages** — some packages (marked `unstable`) may have breaking changes
4. **Node.js compat** — not all `@std` packages work in Node.js; check JSR page for compatibility
5. **Auto-import confusion** — `@std/assert` has many exports; use specific named imports
