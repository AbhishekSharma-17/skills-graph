# Bun — Child Processes

> Source: [bun.sh/docs/api/spawn](https://bun.sh/docs/api/spawn) | [bun.sh/docs/api/worker](https://bun.sh/docs/api/worker)

## Table of Contents

- [Overview](#overview)
- [Bun.spawn — Async Process Spawning](#bunspawn----async-process-spawning)
- [Command Arguments](#command-arguments)
- [Stdin, Stdout, Stderr Configuration](#stdin-stdout-stderr-configuration)
- [Reading Stdout](#reading-stdout)
- [Process Exit and Exit Codes](#process-exit-and-exit-codes)
- [Bun.spawnSync — Synchronous Variant](#bunspawnsync----synchronous-variant)
- [Killing Processes](#killing-processes)
- [Environment Variables for Spawned Processes](#environment-variables-for-spawned-processes)
- [IPC — Inter-Process Communication](#ipc----inter-process-communication)
- [Worker Threads](#worker-threads)
- [Worker Communication](#worker-communication)
- [SharedArrayBuffer and Transferable Objects](#sharedarraybuffer-and-transferable-objects)
- [Common Pitfalls](#common-pitfalls)

## Overview

Bun provides `Bun.spawn()` (async) and `Bun.spawnSync()` (synchronous) for running external processes. For most shell scripting, the `Bun.$` shell API (see `08-shell-api.md`) is more convenient. `Bun.spawn()` gives lower-level control over stdio, IPC, and process lifecycle. For CPU-intensive work, use Web Workers via `new Worker()`.

## Bun.spawn — Async Process Spawning

```typescript
const proc = Bun.spawn(["echo", "hello", "world"]);
await proc.exited;  // Promise<number> — resolves to exit code

const proc2 = Bun.spawn(["ls", "-la", "/tmp"], {
  cwd: "/home/user",
  env: { PATH: "/usr/bin" },
  stdout: "pipe",
  stderr: "pipe",
  stdin: "ignore",
});
```

## Command Arguments

The first argument must always be a `string[]` — no shell template syntax.

```typescript
const proc = Bun.spawn(["git", "log", "--oneline", "-10"]);

// Spaces in arguments are handled correctly — no shell escaping needed
const proc2 = Bun.spawn(["cp", "file with spaces.txt", "destination/"]);

// Dynamic arguments
const flags = ["--verbose", "--recursive", "--force"];
const proc3 = Bun.spawn(["rm", ...flags, "/tmp/old-cache"]);
```

## Stdin, Stdout, Stderr Configuration

| Value | Behavior |
|-------|----------|
| `"pipe"` | Creates a pipe; readable/writable from JavaScript |
| `"inherit"` | Shares the parent process's stream |
| `"ignore"` | Discards the stream (equivalent to `/dev/null`) |
| `Bun.file(path)` | Redirects to/from a file |
| `ReadableStream` | Pipes from a ReadableStream (stdin only) |
| `number` | Raw file descriptor |

```typescript
// Redirect stdout to a file
const proc = Bun.spawn(["echo", "log entry"], { stdout: Bun.file("output.log") });

// Feed stdin from a file
const proc2 = Bun.spawn(["wc", "-l"], { stdin: Bun.file("data.txt"), stdout: "pipe" });

// Feed stdin from a ReadableStream
const inputStream = new ReadableStream({
  start(controller) {
    controller.enqueue(new TextEncoder().encode("line 1\nline 2\n"));
    controller.close();
  },
});
const proc3 = Bun.spawn(["cat"], { stdin: inputStream, stdout: "pipe" });
```

## Reading Stdout

When stdout is `"pipe"`, `proc.stdout` is a `ReadableStream`:

```typescript
const proc = Bun.spawn(["echo", "hello"], { stdout: "pipe" });
const text = await new Response(proc.stdout).text();    // "hello\n"
const data = await new Response(proc2.stdout).json();
const bytes = await new Response(proc3.stdout).arrayBuffer();

// Stream chunks as they arrive
const reader = proc.stdout.getReader();
while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  process.stdout.write(value);
}

// Pipe stdout of one process into stdin of another
const lsProc = Bun.spawn(["ls", "-la"], { stdout: "pipe" });
const grepProc = Bun.spawn(["grep", ".ts"], { stdin: lsProc.stdout, stdout: "pipe" });
const result = await new Response(grepProc.stdout).text();
```

## Process Exit and Exit Codes

```typescript
const exitCode = await proc.exited;
console.log(`Exited with: ${exitCode}`);

// proc.exitCode is null while still running
if (proc.exitCode === null) { console.log("Still running..."); }

// Helper: run and check success
async function runCommand(cmd: string[]): Promise<boolean> {
  const proc = Bun.spawn(cmd, { stdout: "ignore", stderr: "pipe" });
  const exitCode = await proc.exited;
  if (exitCode !== 0) {
    console.error(`Failed (${exitCode}): ${await new Response(proc.stderr).text()}`);
    return false;
  }
  return true;
}

// Timeout pattern
async function runWithTimeout(cmd: string[], timeoutMs: number) {
  const proc = Bun.spawn(cmd, { stdout: "pipe" });
  const result = await Promise.race([
    proc.exited,
    new Promise<"timeout">((resolve) => setTimeout(() => resolve("timeout"), timeoutMs)),
  ]);
  if (result === "timeout") { proc.kill(); throw new Error(`Timed out after ${timeoutMs}ms`); }
  return new Response(proc.stdout).text();
}
```

## Bun.spawnSync — Synchronous Variant

Blocks the event loop until process exits. Returns stdout/stderr as `Buffer`.

```typescript
const result = Bun.spawnSync(["echo", "hello"]);
console.log(result.exitCode);          // 0
console.log(result.stdout.toString()); // "hello\n"
console.log(result.success);           // true

function hasCommand(name: string): boolean {
  return Bun.spawnSync(["which", name]).exitCode === 0;
}

function getGitBranch(): string {
  const result = Bun.spawnSync(["git", "rev-parse", "--abbrev-ref", "HEAD"]);
  if (!result.success) throw new Error("Not a git repository");
  return result.stdout.toString().trim();
}
```

Use only for short-lived commands in scripts or CLI tools. Never use in servers.

## Killing Processes

```typescript
proc.kill();           // SIGTERM (default)
proc.kill("SIGKILL");  // force kill
proc.kill("SIGINT");   // interrupt

// Graceful shutdown pattern
process.on("SIGTERM", async () => {
  server.kill("SIGTERM");
  await server.exited;
  process.exit(0);
});
```

## Environment Variables for Spawned Processes

```typescript
// Replace environment entirely
const proc = Bun.spawn(["node", "script.js"], {
  env: { NODE_ENV: "production", PORT: "3000", PATH: "/usr/bin:/usr/local/bin" },
});

// Extend parent environment
const proc2 = Bun.spawn(["node", "script.js"], {
  env: { ...process.env, NODE_ENV: "test", DATABASE_URL: "sqlite://test.db" },
});

// Remove a specific variable
const { SECRET_KEY, ...safeEnv } = process.env;
const proc3 = Bun.spawn(["untrusted-tool"], { env: safeEnv });
```

## IPC — Inter-Process Communication

Supports structured cloning (not just strings) between parent and child Bun processes:

```typescript
// parent.ts
const child = Bun.spawn(["bun", "child.ts"], {
  ipc: (message, subprocess) => {
    console.log("From child:", message);
    subprocess.send({ reply: "acknowledged", timestamp: Date.now() });
  },
});
child.send({ task: "process_data", payload: [1, 2, 3] });
await child.exited;
```

```typescript
// child.ts
process.on("message", (message) => { console.log("From parent:", message); });
process.send({ status: "ready", pid: process.pid });
const result = heavyComputation();
process.send({ status: "done", result });
```

IPC messages support: objects, arrays, typed arrays, Maps, Sets, Dates, RegExps.

## Worker Threads

```typescript
// main.ts
const worker = new Worker(new URL("./worker.ts", import.meta.url));
worker.postMessage({ type: "compute", data: [1, 2, 3, 4, 5] });
worker.onmessage = (event: MessageEvent) => console.log("Result:", event.data);
worker.onerror = (event: ErrorEvent) => console.error("Error:", event.message);
worker.terminate();
```

```typescript
// worker.ts
declare const self: Worker;
self.onmessage = (event: MessageEvent) => {
  const { type, data } = event.data;
  if (type === "compute") {
    const result = data.reduce((sum: number, n: number) => sum + n, 0);
    self.postMessage({ type: "result", value: result });
  }
};
```

### node:worker_threads compatibility

```typescript
import { Worker, isMainThread, parentPort, workerData } from "node:worker_threads";

if (isMainThread) {
  const worker = new Worker(import.meta.filename, { workerData: { numbers: [10, 20, 30] } });
  worker.on("message", (result) => console.log("Sum:", result)); // 60
  worker.on("error", (err) => console.error("Worker error:", err));
} else {
  const sum = workerData.numbers.reduce((a: number, b: number) => a + b, 0);
  parentPort!.postMessage(sum);
}
```

## Worker Communication

```typescript
// Request/response pattern with unique IDs
function processImage(imageData: ArrayBuffer): Promise<ArrayBuffer> {
  return new Promise((resolve, reject) => {
    const id = crypto.randomUUID();
    const handler = (event: MessageEvent) => {
      if (event.data.id === id) {
        worker.removeEventListener("message", handler);
        event.data.error ? reject(new Error(event.data.error)) : resolve(event.data.result);
      }
    };
    worker.addEventListener("message", handler);
    worker.postMessage({ id, type: "resize", imageData });
  });
}

// Worker pool pattern
class WorkerPool {
  private workers: Worker[] = [];
  private queue: Array<{ resolve: Function; reject: Function; data: unknown }> = [];
  private available: Worker[] = [];

  constructor(workerUrl: URL, size: number) {
    for (let i = 0; i < size; i++) {
      const worker = new Worker(workerUrl);
      worker.onmessage = (event) => this.onWorkerDone(worker, event.data);
      this.workers.push(worker);
      this.available.push(worker);
    }
  }

  async execute(data: unknown): Promise<unknown> {
    return new Promise((resolve, reject) => {
      const worker = this.available.pop();
      if (worker) {
        worker.postMessage(data);
        (worker as any).__resolve = resolve;
        (worker as any).__reject = reject;
      } else {
        this.queue.push({ resolve, reject, data });
      }
    });
  }

  private onWorkerDone(worker: Worker, result: unknown) {
    (worker as any).__resolve(result);
    const next = this.queue.shift();
    if (next) {
      worker.postMessage(next.data);
      (worker as any).__resolve = next.resolve;
      (worker as any).__reject = next.reject;
    } else {
      this.available.push(worker);
    }
  }

  terminate() { this.workers.forEach((w) => w.terminate()); }
}
```

## SharedArrayBuffer and Transferable Objects

```typescript
// Transferable — zero-copy transfer (ownership moves to worker)
const buffer = new ArrayBuffer(1024 * 1024);
worker.postMessage({ buffer }, [buffer]);
console.log(buffer.byteLength); // 0 — transferred

// SharedArrayBuffer — shared memory between threads
const shared = new SharedArrayBuffer(1024);
const view = new Int32Array(shared);
worker.postMessage({ shared });

Atomics.store(view, 0, 42);
Atomics.notify(view, 0);
```

```typescript
// worker.ts — SharedArrayBuffer
self.onmessage = (event: MessageEvent) => {
  const view = new Int32Array(event.data.shared);
  Atomics.wait(view, 0, 0);          // block until value changes from 0
  const value = Atomics.load(view, 0); // 42
  Atomics.store(view, 1, value * 2);
  Atomics.notify(view, 1);
};
```

## Common Pitfalls

1. **Passing a single string instead of an array** — `Bun.spawn("ls -la")` does not split the string; always use `string[]`
2. **Not consuming stdout when set to `"pipe"`** — If you pipe stdout but never read it, the buffer fills and the child process hangs indefinitely
3. **Using `Bun.spawnSync()` in a server** — Synchronous spawning blocks the event loop; always use `Bun.spawn()` in server code
4. **Forgetting to `await proc.exited`** — Without awaiting, the parent may exit before the child finishes or errors go unhandled
5. **Sending non-cloneable values via IPC** — Functions, symbols, and DOM nodes cannot be sent via IPC
6. **Using `SharedArrayBuffer` without `Atomics`** — Race conditions will occur; always use `Atomics.load()`, `Atomics.store()`, and `Atomics.wait()`
7. **Leaking child processes** — Use `process.on("exit", () => proc.kill())` to ensure child processes are cleaned up when the parent exits
8. **Reading a transferred buffer** — After `postMessage(data, [buffer])`, the buffer is detached and `byteLength` becomes 0; this is by design
