# Bun — File I/O

> Source: [bun.sh/docs/api/file-io](https://bun.sh/docs/api/file-io)

## Table of Contents

- [Bun.file() — Creating File References](#bunfile--creating-file-references)
- [Reading Files](#reading-files)
- [Bun.write() — Writing Files](#bunwrite--writing-files)
- [Writing Different Data Types](#writing-different-data-types)
- [Streaming Reads](#streaming-reads)
- [FileSink API — Incremental Writes](#filesink-api--incremental-writes)
- [BunFile Properties](#bunfile-properties)
- [Glob API](#glob-api)
- [MIME Type Detection](#mime-type-detection)
- [Temporary Files](#temporary-files)
- [Standard I/O Streams](#standard-io-streams)
- [Performance Comparison vs Node.js](#performance-comparison-vs-nodejs)
- [Common Pitfalls](#common-pitfalls)

---

## Bun.file() — Creating File References

`Bun.file()` creates a lazy reference — no disk I/O until a read method is called. `BunFile` is a `Blob` subclass and works anywhere a `Blob` is accepted.

```typescript
const file = Bun.file("./data.json");            // lazy, no I/O
const absolute = Bun.file("/etc/hosts");
const fromUrl = Bun.file(new URL("./data.txt", import.meta.url));

// Works as a Blob — Content-Type auto-detected from extension
const response = new Response(Bun.file("./image.png"));
```

---

## Reading Files

All read methods are async and return Promises.

```typescript
const content = await Bun.file("./README.md").text();        // string
const pkg = await Bun.file("./package.json").json();         // parsed object
const buffer = await Bun.file("./binary.dat").arrayBuffer(); // ArrayBuffer
const bytes = await Bun.file("./image.png").bytes();         // Uint8Array

// Stream (memory-efficient for large files)
const stream = Bun.file("./large-file.csv").stream();
for await (const chunk of stream) { /* chunk is Uint8Array */ }

// Existence check
const file = Bun.file("./maybe-exists.txt");
if (await file.exists()) {
  const content = await file.text();
}
```

---

## Bun.write() — Writing Files

Creates the file if it doesn't exist, overwrites if it does. Returns bytes written. Creates parent directories automatically.

```typescript
await Bun.write("./output.txt", "Hello, Bun!");
const bytesWritten = await Bun.write("./output.txt", "Hello!");

// Write to a BunFile reference
await Bun.write(Bun.file("./output.txt"), "Hello!");

// Creates deep/nested/ directories if missing
await Bun.write("./deep/nested/output.txt", "content");
```

---

## Writing Different Data Types

```typescript
// String
await Bun.write("./file.txt", "plain text");

// Uint8Array / ArrayBuffer
await Bun.write("./binary.dat", new Uint8Array([72, 101, 108, 108, 111]));
await Bun.write("./empty.dat", new ArrayBuffer(1024));

// Blob
await Bun.write("./from-blob.txt", new Blob(["Hello!"], { type: "text/plain" }));

// BunFile (copy)
await Bun.write("./copy.png", Bun.file("./original.png"));

// Response body (download to disk)
const response = await fetch("https://example.com/image.png");
await Bun.write("./downloaded.png", response);

// ReadableStream
await Bun.write("./streamed-output.dat", getReadableStream());
```

---

## Streaming Reads

```typescript
// Count lines without loading entire file into memory
const file = Bun.file("./large-dataset.csv");
const decoder = new TextDecoder();
let lineCount = 0;
for await (const chunk of file.stream()) {
  lineCount += decoder.decode(chunk, { stream: true }).split("\n").length - 1;
}

// Serve a large file via HTTP
Bun.serve({
  fetch(req) {
    const file = Bun.file("./large-video.mp4");
    return new Response(file.stream(), { headers: { "Content-Type": file.type } });
  },
});

// Stream to another file
const source = Bun.file("./input.dat");
const writer = Bun.file("./output.dat").writer();
for await (const chunk of source.stream()) { writer.write(chunk); }
writer.end();
```

---

## FileSink API — Incremental Writes

The `FileSink` API provides a writable interface for incremental writes — useful for logs and large file generation.

```typescript
const writer = Bun.file("./log.txt").writer();

writer.write("First line\n");
writer.write("Second line\n");
writer.write(new Uint8Array([84, 104, 105, 114, 100]));  // "Third"
writer.flush();     // force buffered data to disk
writer.write("Fourth line\n");
writer.end();       // flush remaining data and close

// Writer options
const writer2 = Bun.file("./output.dat").writer({ highWaterMark: 1024 * 1024 });

// CSV export pattern
const csvWriter = Bun.file("./export.csv").writer();
csvWriter.write("id,name,email\n");
for (const user of getAllUsers()) {
  csvWriter.write(`${user.id},${user.name},${user.email}\n`);
}
csvWriter.end();

// ref/unref — control whether writer keeps process alive
writer.unref();  // allow process to exit even if writer is open
writer.ref();    // default behavior
```

---

## BunFile Properties

```typescript
const file = Bun.file("./package.json");
file.name;   // "package.json"
file.size;   // file size in bytes
file.type;   // "application/json" (auto-detected MIME)

// exists() — check disk presence
if (await file.exists()) { const config = await file.json(); }

// stat() — detailed metadata
const stat = await file.stat();
if (stat) {
  stat.size; stat.mtime; stat.atime; stat.birthtime;
  stat.isFile(); stat.isDirectory(); stat.isSymbolicLink();
}

// slice() — reference a portion (like Blob.slice)
const first1KB = Bun.file("./large.bin").slice(0, 1024);
const text = await first1KB.text();
```

---

## Glob API

```typescript
const glob = new Bun.Glob("**/*.ts");

// Scan files on disk
for await (const path of glob.scan(".")) {
  console.log(path);  // "src/index.ts", "src/utils.ts"
}

// With options
for await (const path of glob.scan({
  cwd: "./src",
  dot: false,          // skip dotfiles
  absolute: true,      // return absolute paths
  onlyFiles: true,
})) { /* ... */ }

// Collect into array
const files = await Array.fromAsync(glob.scan("./src"));

// Test a string against a pattern
const g = new Bun.Glob("*.test.ts");
g.match("utils.test.ts");        // true
g.match("utils.ts");             // false
new Bun.Glob("**/*.test.ts").match("src/utils.test.ts");  // true
```

### Common Glob Patterns

| Pattern | Matches |
|---------|---------|
| `*.ts` | TypeScript files in current directory |
| `**/*.ts` | TypeScript files recursively |
| `src/**/*.{ts,tsx}` | TS and TSX files under src/ |
| `!**/*.test.ts` | Exclude test files |

---

## MIME Type Detection

```typescript
Bun.file("./style.css").type;    // "text/css"
Bun.file("./app.js").type;       // "text/javascript;charset=utf-8"
Bun.file("./data.json").type;    // "application/json"
Bun.file("./image.png").type;    // "image/png"
Bun.file("./doc.pdf").type;      // "application/pdf"
Bun.file("./unknown.xyz").type;  // "application/octet-stream"

// Useful for serving files over HTTP
Bun.serve({
  fetch(req) {
    const file = Bun.file(`./public${new URL(req.url).pathname}`);
    return new Response(file);  // Content-Type set automatically
  },
});
```

---

## Temporary Files

```typescript
const tmpPath = `/tmp/bun-${Date.now()}.txt`;
await Bun.write(tmpPath, "temporary content");
const content = await Bun.file(tmpPath).text();
const { unlinkSync } = require("node:fs");
unlinkSync(tmpPath);

// Using OS temp directory
import { tmpdir } from "node:os";
import { join } from "node:path";
const tmpFile = join(tmpdir(), `session-${crypto.randomUUID()}.json`);
await Bun.write(tmpFile, JSON.stringify({ user: "Alice", ts: Date.now() }));
const session = await Bun.file(tmpFile).json();
```

---

## Standard I/O Streams

```typescript
// stdin — read all or stream line-by-line
const input = await Bun.stdin.text();  // blocks until EOF

const decoder = new TextDecoder();
for await (const chunk of Bun.stdin.stream()) {
  const line = decoder.decode(chunk).trim();
  if (line === "quit") break;
}

// stdout / stderr writers
const writer = Bun.stdout.writer();
writer.write("Hello from stdout\n");
writer.flush();

const errWriter = Bun.stderr.writer();
errWriter.write("Error message\n");
errWriter.flush();

// Pipe stdin to a file
await Bun.write("./captured-input.txt", await Bun.stdin.text());
```

---

## Performance Comparison vs Node.js

Bun uses native Zig syscalls instead of libuv's thread pool, giving ~4x better throughput.

| Operation | Bun | Node.js | Speedup |
|-----------|-----|---------|---------|
| Read 1MB text | ~0.3ms | ~1.2ms | ~4x |
| Write 1MB | ~0.2ms | ~0.9ms | ~4.5x |
| Glob scan 10K files | ~15ms | ~60ms | ~4x |
| Copy large file | ~0.5ms | ~2ms | ~4x |

```typescript
// Prefer Bun native API over Node.js fs
const content = await Bun.file("./data.json").text();   // faster
// vs
import { readFile } from "node:fs/promises";
const content = await readFile("./data.json", "utf-8"); // slower
```

Node.js `fs` module is supported in Bun for compatibility, but use `Bun.file()` / `Bun.write()` for best performance.

---

## Common Pitfalls

**1. Bun.file() does not read immediately**: It's lazy — forgetting to `await` a read method like `.text()` returns a Promise, not the content.

**2. Bun.write() overwrites by default**: No "append" mode. To append, use `FileSink` (`Bun.file().writer()`), or read-then-concatenate.

**3. BunFile.size may be stale**: `file.size` reads from OS stat cache. Call `file.stat()` for a fresh value if another process may have modified the file.

**4. Glob patterns are relative to cwd**: `glob.scan(".")` returns relative paths. Pass `{ absolute: true }` if you need full paths for `Bun.file()`.

**5. stream() returns Uint8Array chunks, not strings**: Decode with `TextDecoder` when streaming text files.

**6. FileSink must be ended**: Forgetting `writer.end()` can leave unflushed data in the buffer. Always call `.end()` when finished.

**7. stdin blocks the process**: `Bun.stdin.text()` blocks until stdin is closed (EOF). Use `Bun.stdin.stream()` for interactive programs.

---

**Related:** [02-http-server.md](02-http-server.md) for serving files, [08-shell-api.md](08-shell-api.md) for shell-based file operations
