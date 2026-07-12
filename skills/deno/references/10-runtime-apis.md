# Runtime APIs

> Source: https://docs.deno.com/runtime/reference/deno_namespace_apis/

## Table of Contents

- [File System APIs](#file-system-apis)
- [Network APIs](#network-apis)
- [Subprocess APIs](#subprocess-apis)
- [Environment and System](#environment-and-system)
- [Foreign Function Interface (FFI)](#foreign-function-interface-ffi)
- [WebAssembly](#webassembly)
- [Web Platform APIs](#web-platform-apis)
- [Timers and Scheduling](#timers-and-scheduling)
- [Error Classes](#error-classes)

## File System APIs

### Reading Files

```typescript
// Read entire file as text
const text = await Deno.readTextFile("./config.json");

// Read as bytes
const bytes = await Deno.readFile("./image.png");

// Sync variants
const textSync = Deno.readTextFileSync("./config.json");
const bytesSync = Deno.readFileSync("./image.png");
```

### Writing Files

```typescript
// Write text
await Deno.writeTextFile("./output.txt", "Hello, World!");

// Write bytes
const data = new TextEncoder().encode("binary data");
await Deno.writeFile("./output.bin", data);

// Append mode
await Deno.writeTextFile("./log.txt", "new line\n", { append: true });

// Create only (fail if exists)
await Deno.writeTextFile("./new.txt", "content", { createNew: true });

// Set permissions (Unix)
await Deno.writeTextFile("./script.sh", "#!/bin/bash\necho hi", { mode: 0o755 });
```

### File Handles

```typescript
// Open with specific options
const file = await Deno.open("./data.txt", { read: true, write: true });

// Read into buffer
const buf = new Uint8Array(1024);
const bytesRead = await file.read(buf);

// Write from buffer
await file.write(new TextEncoder().encode("hello"));

// Seek to position
await file.seek(0, Deno.SeekMode.Start);

// Get file info via handle
const stat = await file.stat();

// CRITICAL: always close
file.close();

// Or use the readable stream (auto-closes)
const readable = (await Deno.open("file.txt")).readable;
```

### Directory Operations

```typescript
// Read directory contents
for await (const entry of Deno.readDir("./src")) {
  console.log(entry.name, entry.isFile, entry.isDirectory, entry.isSymlink);
}

// Create directory
await Deno.mkdir("./new-dir");
await Deno.mkdir("./deep/nested/dir", { recursive: true });

// Remove files/directories
await Deno.remove("./file.txt");
await Deno.remove("./directory", { recursive: true });

// Rename/move
await Deno.rename("./old.txt", "./new.txt");

// Copy (using streams)
const src = await Deno.open("./source.txt");
const dst = await Deno.create("./dest.txt");
await src.readable.pipeTo(dst.writable);

// File/directory info
const info = await Deno.stat("./file.txt");
console.log(info.size, info.mtime, info.isFile);

// Symlinks
await Deno.symlink("./target", "./link");
const target = await Deno.readLink("./link");
const realPath = await Deno.realPath("./link");
```

### Temporary Files

```typescript
// Create temp file
const tmpFile = await Deno.makeTempFile({ prefix: "app_", suffix: ".json" });

// Create temp directory
const tmpDir = await Deno.makeTempDir({ prefix: "build_" });
```

### Watching File Changes

```typescript
const watcher = Deno.watchFs("./src");
for await (const event of watcher) {
  console.log(event.kind, event.paths);
  // kind: "create" | "modify" | "remove" | "access"
}
```

## Network APIs

### TCP Connections

```typescript
// Client: connect to a TCP server
const conn = await Deno.connect({ hostname: "localhost", port: 5432 });
await conn.write(new TextEncoder().encode("HELLO\n"));
const buf = new Uint8Array(256);
await conn.read(buf);
conn.close();

// Server: listen for TCP connections
const listener = Deno.listen({ port: 8080 });
for await (const conn of listener) {
  handleConnection(conn);
}
```

### TLS Connections

```typescript
// TLS client
const tlsConn = await Deno.connectTls({
  hostname: "example.com",
  port: 443,
});

// TLS server
const tlsListener = Deno.listenTls({
  port: 443,
  cert: await Deno.readTextFile("./cert.pem"),
  key: await Deno.readTextFile("./key.pem"),
});
```

### UDP

```typescript
const socket = Deno.listenDatagram({ port: 9000, transport: "udp" });
for await (const [data, addr] of socket) {
  console.log(`From ${addr.hostname}:${addr.port}:`, new TextDecoder().decode(data));
  await socket.send(new TextEncoder().encode("ACK"), addr);
}
```

## Subprocess APIs

### Deno.Command (Recommended)

```typescript
// Simple execution
const command = new Deno.Command("git", {
  args: ["status", "--porcelain"],
});
const { code, stdout, stderr } = await command.output();
console.log(new TextDecoder().decode(stdout));

// With options
const cmd = new Deno.Command("node", {
  args: ["script.js"],
  cwd: "./project",
  env: { NODE_ENV: "production" },
  stdin: "piped",
  stdout: "piped",
  stderr: "piped",
});

// Spawn with streaming I/O
const child = cmd.spawn();

// Write to stdin
const writer = child.stdin.getWriter();
await writer.write(new TextEncoder().encode("input data\n"));
await writer.close();

// Read stdout as stream
const reader = child.stdout.getReader();
while (true) {
  const { value, done } = await reader.read();
  if (done) break;
  console.log(new TextDecoder().decode(value));
}

const status = await child.status;
console.log("Exit code:", status.code);
```

### Piping Between Processes

```typescript
const grep = new Deno.Command("grep", {
  args: ["error"],
  stdin: "piped",
  stdout: "piped",
});

const child = grep.spawn();

// Pipe a file into grep
const file = await Deno.open("./app.log");
file.readable.pipeTo(child.stdin);

// Read grep output
const output = await child.output();
console.log(new TextDecoder().decode(output.stdout));
```

## Environment and System

### Environment Variables

```typescript
// Get variable
const port = Deno.env.get("PORT") ?? "8000";

// Set variable (current process only)
Deno.env.set("NODE_ENV", "production");

// Delete variable
Deno.env.delete("TEMP_VAR");

// Get all variables
const allEnv = Deno.env.toObject();

// Check if set
Deno.env.has("DATABASE_URL"); // boolean
```

### System Information

```typescript
// OS and architecture
Deno.build.os;       // "darwin" | "linux" | "windows"
Deno.build.arch;     // "x86_64" | "aarch64"
Deno.build.target;   // "x86_64-apple-darwin"

// Deno version info
Deno.version.deno;       // "2.9.0"
Deno.version.v8;         // "13.x.x"
Deno.version.typescript; // "5.x.x"

// Process info
Deno.pid;            // Process ID
Deno.ppid;           // Parent process ID
Deno.hostname();     // Machine hostname
Deno.memoryUsage();  // { rss, heapTotal, heapUsed, external }
Deno.osRelease();    // OS release string
Deno.osUptime();     // Uptime in seconds
Deno.uid();          // User ID (Unix)
Deno.gid();          // Group ID (Unix)
```

### Process Control

```typescript
// Exit
Deno.exit(0);
Deno.exit(1);

// Signal handling
Deno.addSignalListener("SIGINT", () => {
  console.log("Interrupted!");
  Deno.exit(0);
});

Deno.addSignalListener("SIGTERM", () => {
  console.log("Terminated!");
  cleanup();
});
```

### Standard Streams

```typescript
// Read from stdin
const decoder = new TextDecoder();
for await (const chunk of Deno.stdin.readable) {
  console.log("Input:", decoder.decode(chunk));
}

// Write to stdout/stderr
const encoder = new TextEncoder();
await Deno.stdout.write(encoder.encode("stdout output\n"));
await Deno.stderr.write(encoder.encode("stderr output\n"));
```

## Foreign Function Interface (FFI)

Call native C/Rust libraries:

```typescript
const lib = Deno.dlopen("./libmath.so", {
  add: { parameters: ["i32", "i32"], result: "i32" },
  multiply: { parameters: ["f64", "f64"], result: "f64" },
});

const sum = lib.symbols.add(40, 2);        // 42
const product = lib.symbols.multiply(3.14, 2.0); // 6.28

lib.close();
```

### Callback from Native Code

```typescript
const callback = new Deno.UnsafeCallback(
  { parameters: ["i32"], result: "void" },
  (value) => {
    console.log("Native called us with:", value);
  },
);

// Pass callback.pointer to native function
lib.symbols.register_callback(callback.pointer);

// Must explicitly unref when done
callback.unref();
```

## WebAssembly

### Direct Import (v2.1+)

```typescript
// Import WASM with type checking
import { add, multiply } from "./math.wasm";

console.log(add(1, 2));       // 3
console.log(multiply(3, 4));  // 12
```

### Streaming Instantiation

```typescript
const { instance } = await WebAssembly.instantiateStreaming(
  fetch(new URL("./module.wasm", import.meta.url)),
  { env: { log: console.log } },
);

const result = (instance.exports.compute as CallableFunction)(42);
```

### Manual Loading

```typescript
const wasmCode = await Deno.readFile("./module.wasm");
const wasmModule = new WebAssembly.Module(wasmCode);
const instance = new WebAssembly.Instance(wasmModule, imports);
```

## Web Platform APIs

Deno implements many browser-standard APIs:

```typescript
// Fetch API
const response = await fetch("https://api.example.com/data");
const data = await response.json();

// URL and URLSearchParams
const url = new URL("https://example.com/path?key=value");
url.searchParams.set("page", "2");

// URLPattern (routing)
const pattern = new URLPattern({ pathname: "/users/:id" });
const match = pattern.exec("https://example.com/users/123");

// Web Crypto
const key = await crypto.subtle.generateKey({ name: "AES-GCM", length: 256 }, true, ["encrypt", "decrypt"]);
const uuid = crypto.randomUUID();

// Streams API
const stream = new ReadableStream({ /* ... */ });
const transform = new TransformStream({ /* ... */ });

// TextEncoder/TextDecoder
const encoder = new TextEncoder();
const decoder = new TextDecoder();

// AbortController
const controller = new AbortController();
setTimeout(() => controller.abort(), 5000);
await fetch(url, { signal: controller.signal });

// structuredClone
const deep = structuredClone(complexObject);

// Performance
performance.now();
performance.mark("start");
performance.measure("duration", "start");

// Web Workers
const worker = new Worker(import.meta.resolve("./worker.ts"), { type: "module" });
worker.postMessage({ data: "hello" });
```

## Timers and Scheduling

```typescript
// Standard timers
const id = setTimeout(() => console.log("delayed"), 1000);
clearTimeout(id);

const interval = setInterval(() => console.log("tick"), 500);
clearInterval(interval);

// Cron (Deno Deploy / unstable)
Deno.cron("daily-cleanup", "0 0 * * *", () => {
  console.log("Running daily cleanup");
});
```

## Error Classes

Deno provides 20+ typed error classes:

```typescript
try {
  await Deno.readTextFile("./nonexistent.txt");
} catch (e) {
  if (e instanceof Deno.errors.NotFound) {
    console.log("File does not exist");
  } else if (e instanceof Deno.errors.PermissionDenied) {
    console.log("Need --allow-read permission");
  }
}
```

Key error classes:
- `Deno.errors.NotFound` — resource doesn't exist
- `Deno.errors.PermissionDenied` — missing permission
- `Deno.errors.ConnectionRefused` — TCP connection failed
- `Deno.errors.ConnectionReset` — connection dropped
- `Deno.errors.AddrInUse` — port already bound
- `Deno.errors.BrokenPipe` — write to closed pipe
- `Deno.errors.TimedOut` — operation timed out
- `Deno.errors.InvalidData` — malformed input
- `Deno.errors.AlreadyExists` — resource already exists

## Common Pitfalls

1. **Forgetting to close resources** — always close file handles, connections, listeners
2. **Sync vs async** — prefer async APIs; sync blocks the event loop
3. **Permission errors at runtime** — check permissions before attempting operations
4. **FFI memory leaks** — unref callbacks and close libraries when done
5. **stdin blocking** — reading stdin blocks; use with caution in servers
