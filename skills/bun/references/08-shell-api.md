# Bun -- Shell API

> Source: [bun.sh/docs/runtime/shell](https://bun.sh/docs/runtime/shell)

## Table of Contents

- [Overview](#overview)
- [Running Commands](#running-commands)
- [Capturing Output](#capturing-output)
- [Piping Commands](#piping-commands)
- [Environment Variables](#environment-variables)
- [Error Handling](#error-handling)
- [Escaping and Security](#escaping-and-security)
- [Quiet Mode](#quiet-mode)
- [Working Directory](#working-directory)
- [Stdin Input](#stdin-input)
- [Shell Scripting Patterns](#shell-scripting-patterns)
- [Comparison with Alternatives](#comparison-with-alternatives)
- [Common Pitfalls](#common-pitfalls)

## Overview

Bun provides a built-in shell API via the `$` tagged template literal. It is a cross-platform shell that works on macOS, Linux, and Windows without depending on a system shell like bash or PowerShell. The shell implements common commands (`ls`, `cat`, `echo`, `rm`, `cd`, `mv`, `cp`, `mkdir`, etc.) natively in JavaScript for consistent behavior across platforms.

```typescript
import { $ } from "bun";

await $`echo "Hello from Bun Shell"`;
```

The shell launches as a child process by default but can execute many commands in-process for speed.

## Running Commands

The `$` function accepts a tagged template literal representing a shell command. By default, stdout and stderr are inherited from the parent process:

```typescript
import { $ } from "bun";

// Simple command — output goes to terminal
await $`echo hello world`;

// Multi-word commands work naturally
await $`ls -la /tmp`;

// Run any system binary
await $`git status`;

// Multiple commands on one line with semicolons
await $`echo "step 1"; echo "step 2"`;
```

Commands are awaited as promises. The returned object is a `ShellOutput` containing the exit code, stdout, and stderr.

## Capturing Output

To capture output instead of printing to the terminal, call `.text()`, `.json()`, `.lines()`, `.blob()`, or `.arrayBuffer()` on the result:

```typescript
import { $ } from "bun";

// Capture as trimmed string
const text = await $`echo "hello"`.text();
console.log(text); // "hello"

// Capture and parse as JSON
const pkg = await $`cat package.json`.json();
console.log(pkg.name);

// Capture as array of lines (filters empty lines)
const files = await $`ls -1 src/`.lines();
for (const file of files) {
  console.log(`Found: ${file}`);
}

// Capture as raw bytes
const buffer = await $`cat image.png`.arrayBuffer();

// Capture as Blob
const blob = await $`cat data.bin`.blob();
```

When you call `.text()` or similar methods, stdout is automatically redirected to a pipe instead of the terminal. The result is always trimmed of trailing whitespace.

```typescript
import { $ } from "bun";

// Full ShellOutput object
const result = await $`ls -la`.quiet();
console.log(result.exitCode);  // 0
console.log(result.stdout);    // Buffer
console.log(result.stderr);    // Buffer
console.log(result.text());    // stdout as string
```

## Piping Commands

Chain commands with the `.pipe()` method to send one command's stdout into another's stdin:

```typescript
import { $ } from "bun";

// Pipe grep into wc
const count = await $`cat access.log`
  .pipe($`grep "200 OK"`)
  .pipe($`wc -l`)
  .text();

console.log(`Successful requests: ${count.trim()}`);

// Pipe into Bun.file() to write output to a file
await $`echo "log entry"`.pipe(Bun.file("output.log"));

// Pipe into a Response object or ReadableStream
const stream = $`cat large-file.txt`.pipe($`grep pattern`);
```

You can also use the standard shell pipe syntax within the template:

```typescript
import { $ } from "bun";

// Shell-native pipe syntax
const result = await $`cat file.txt | grep "error" | sort | uniq -c`.text();
```

## Environment Variables

Access environment variables in shell commands with `$VAR` syntax. Bun resolves them from the current `process.env`:

```typescript
import { $ } from "bun";

// Access existing env vars
await $`echo $HOME`;
await $`echo $PATH`;

// Interpolated JS variables are NOT treated as env vars
const name = "world";
await $`echo ${name}`; // prints "world" — JS interpolation

// Set environment variables for a command using .env()
await $`echo $MY_VAR`.env({ MY_VAR: "custom_value" });

// Merge with existing environment
await $`printenv`.env({
  ...process.env,
  CUSTOM_KEY: "custom_value",
});

// Override specific env vars — other vars are inherited
await $`node script.js`.env({ NODE_ENV: "production" });
```

The `.env()` method sets environment variables for that specific command. By default, the child process inherits the parent's environment.

## Error Handling

By default, the shell throws an error if a command exits with a non-zero exit code:

```typescript
import { $ } from "bun";

// Throws ShellError if command fails
try {
  await $`exit 1`;
} catch (err) {
  console.error(err.exitCode); // 1
  console.error(err.stderr.toString());
  console.error(err.message);  // includes command and exit code
}

// Throws if file does not exist
try {
  await $`cat nonexistent.txt`;
} catch (err) {
  console.error(`Command failed: ${err.message}`);
}
```

Use `.nothrow()` to suppress the exception. The result will still contain the exit code:

```typescript
import { $ } from "bun";

// Never throws, even on non-zero exit
const result = await $`grep "needle" haystack.txt`.nothrow();

if (result.exitCode !== 0) {
  console.log("Pattern not found");
} else {
  console.log(result.text());
}

// Combine with .quiet() for silent non-throwing execution
const check = await $`which python3`.nothrow().quiet();
const hasPython = check.exitCode === 0;
```

You can set `.nothrow()` globally to change the default behavior:

```typescript
import { $ } from "bun";

$.nothrow(); // All subsequent commands will not throw on failure

const r1 = await $`false`;
console.log(r1.exitCode); // 1 — no exception
```

## Escaping and Security

Interpolated JavaScript values are automatically escaped to prevent shell injection. This is a critical security feature:

```typescript
import { $ } from "bun";

// SAFE: user input is escaped automatically
const userInput = "; rm -rf /";
await $`echo ${userInput}`; // prints: ; rm -rf /
// The semicolon and rm command are treated as literal strings

// SAFE: filenames with spaces are handled correctly
const filename = "my file (copy).txt";
await $`cat ${filename}`; // works correctly

// SAFE: special characters are escaped
const pattern = "*.js";
await $`echo ${pattern}`; // prints: *.js (no glob expansion)

// Array interpolation — each element becomes a separate argument
const args = ["-la", "/tmp"];
await $`ls ${args}`; // equivalent to: ls -la /tmp

// WARNING: do NOT use raw string concatenation
const unsafeInput = getUserInput();
// BAD: await $`echo ${unsafeInput}`  <-- actually this IS safe in Bun.$
// DANGEROUS: manual string building bypasses escaping
// const cmd = `echo ${unsafeInput}`; exec(cmd); <-- never do this
```

If you need to insert raw unescaped content, use `$.raw()`:

```typescript
import { $ } from "bun";

// Raw content is NOT escaped — use with caution
const glob = $.raw("*.ts");
await $`ls ${glob}`; // glob expansion happens
```

## Quiet Mode

Use `.quiet()` to suppress stdout from being printed to the terminal. Stderr is still shown by default:

```typescript
import { $ } from "bun";

// Suppress stdout output
await $`echo "this won't show"`.quiet();

// Capture output quietly
const result = await $`ls -la`.quiet().text();
console.log(`Got ${result.split("\n").length} lines`);

// Set quiet mode globally
$.quiet();
await $`echo "silenced by default"`;

// Stderr still shows even in quiet mode
await $`echo "error message" >&2`.quiet(); // stderr still visible
```

## Working Directory

Use `.cwd()` to set the working directory for a command:

```typescript
import { $ } from "bun";

// Run command in a specific directory
const files = await $`ls -1`.cwd("/tmp").text();

// Useful for monorepo scripts
await $`bun install`.cwd("./packages/frontend");
await $`bun test`.cwd("./packages/backend");

// Chain with other modifiers
const result = await $`git log --oneline -5`
  .cwd("/path/to/repo")
  .quiet()
  .text();
```

## Stdin Input

Provide input to a command's stdin using the object form or `.stdin()`:

```typescript
import { $ } from "bun";

// Pipe a string into a command's stdin
const sorted = await $`sort`.stdin("banana\napple\ncherry\n").text();
console.log(sorted); // "apple\nbanana\ncherry"

// Pipe a Buffer
const buf = Buffer.from("hello world\n");
const wc = await $`wc -w`.stdin(buf).text();
console.log(wc.trim()); // "2"

// Pipe a Bun.file()
const result = await $`grep "error"`.stdin(Bun.file("app.log")).text();

// Pipe a Response body
const response = await fetch("https://example.com/data.csv");
const lines = await $`wc -l`.stdin(response).text();
```

## Shell Scripting Patterns

Build complex scripts by combining shell features:

```typescript
import { $ } from "bun";

// Sequential execution
async function deploy() {
  await $`bun run build`;
  await $`bun run test`;
  await $`docker build -t myapp .`;
  await $`docker push myapp:latest`;
}

// Conditional execution based on exit codes
async function setupProject() {
  const hasGit = await $`git rev-parse --git-dir`.nothrow().quiet();
  if (hasGit.exitCode !== 0) {
    await $`git init`;
  }

  const hasDeps = await $`test -d node_modules`.nothrow().quiet();
  if (hasDeps.exitCode !== 0) {
    await $`bun install`;
  }
}

// Parallel command execution
async function lintAndTest() {
  const [lintResult, testResult] = await Promise.all([
    $`bun run lint`.nothrow().quiet(),
    $`bun run test`.nothrow().quiet(),
  ]);

  if (lintResult.exitCode !== 0) {
    console.error("Lint failed:", lintResult.stderr.toString());
  }
  if (testResult.exitCode !== 0) {
    console.error("Tests failed:", testResult.stderr.toString());
  }
}

// File processing pipeline
async function processLogs(directory: string) {
  const files = await $`find ${directory} -name "*.log" -mtime -1`.lines();

  for (const file of files) {
    if (!file) continue;
    const errorCount = await $`grep -c "ERROR" ${file}`.nothrow().text();
    if (parseInt(errorCount.trim()) > 0) {
      console.log(`${file}: ${errorCount.trim()} errors`);
    }
  }
}

// Environment-aware commands
async function startServer() {
  const env = process.env.NODE_ENV ?? "development";
  if (env === "production") {
    await $`bun run start`.env({ NODE_ENV: "production", PORT: "8080" });
  } else {
    await $`bun --watch run src/index.ts`.env({ NODE_ENV: "development" });
  }
}
```

## Comparison with Alternatives

| Feature | Bun.$ | child_process | execa | zx |
|---------|-------|---------------|-------|-----|
| **Template literal API** | Yes | No | No | Yes |
| **Cross-platform** | Yes (built-in cmds) | OS-dependent | OS-dependent | OS-dependent |
| **Auto-escaping** | Yes | Manual | Yes | Yes |
| **No dependencies** | Yes | Yes (stdlib) | npm package | npm package |
| **Piping** | `.pipe()` + `\|` | Manual streams | `.pipe()` | `\|` in template |
| **JSON parsing** | `.json()` | Manual | Manual | Manual |
| **Throws on failure** | Default | No | Default | Default |
| **Glob support** | `$.raw()` | N/A | N/A | Yes |

```typescript
// child_process (Node.js)
import { execSync } from "child_process";
const output = execSync("ls -la").toString();

// execa
import { execa } from "execa";
const { stdout } = await execa("ls", ["-la"]);

// Bun.$ — most concise
import { $ } from "bun";
const output = await $`ls -la`.text();
```

The Bun shell is faster than spawning a system shell because many commands run in-process. It also provides consistent behavior across operating systems by implementing core utilities itself.

## Common Pitfalls

1. **Forgetting `await`** -- `$\`command\`` returns a promise; without `await`, the command runs but you cannot inspect the result or catch errors
2. **Using `.text()` on large binary output** -- Use `.arrayBuffer()` or `.blob()` for binary data; `.text()` assumes UTF-8 and trims trailing whitespace
3. **Expecting glob expansion on interpolated values** -- Interpolated JS values are escaped; use `$.raw()` when you need shell globbing on dynamic values
4. **Mixing `.nothrow()` with `try/catch`** -- When `.nothrow()` is set, the command never throws, so catch blocks will never execute for exit-code failures
5. **Assuming system shell behavior** -- Bun's shell is not bash; some bash-specific features like process substitution (`<()`) or advanced redirections may not be available
6. **Not checking `.exitCode` after `.nothrow()`** -- The command silently succeeds even on failure; always check `.exitCode` when using `.nothrow()`
7. **Setting global modes unintentionally** -- `$.quiet()` and `$.nothrow()` without a command change the default for ALL subsequent `$` calls in the process
