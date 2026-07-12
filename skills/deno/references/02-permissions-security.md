# Permissions and Security

> Source: https://docs.deno.com/runtime/fundamentals/security/

## Table of Contents

- [Security Model](#security-model)
- [Permission Categories](#permission-categories)
- [Granting Permissions](#granting-permissions)
- [Deny Flags](#deny-flags)
- [Fine-Grained Scoping](#fine-grained-scoping)
- [Interactive Prompts](#interactive-prompts)
- [Runtime Permission API](#runtime-permission-api)
- [Per-Test Permissions](#per-test-permissions)
- [Security Best Practices](#security-best-practices)

## Security Model

Deno operates with a **secure-by-default** sandbox. Programs have no access to sensitive APIs unless explicitly granted via command-line flags. This protects against:

- Supply-chain attacks (malicious npm packages)
- Accidental data exfiltration
- Unauthorized file system access
- Unintended network connections

```bash
# This FAILS — no permissions granted
deno run server.ts
# error: Denied net access to "0.0.0.0:8000"

# Grant specific permissions
deno run --allow-net=0.0.0.0:8000 server.ts
```

## Permission Categories

| Flag | Short | Controls |
|------|-------|----------|
| `--allow-read` | `-R` | File system read access |
| `--allow-write` | `-W` | File system write access |
| `--allow-net` | `-N` | Network access (TCP, UDP, HTTP) |
| `--allow-env` | `-E` | Environment variable access |
| `--allow-run` | `-S` | Subprocess execution |
| `--allow-ffi` | | Foreign function interface (native libs) |
| `--allow-import` | | Dynamic `import()` from remote URLs |
| `--allow-all` | `-A` | Grant all permissions (disable sandbox) |

## Granting Permissions

### Broad Permissions (entire category)

```bash
# Allow all file reads
deno run --allow-read main.ts
deno run -R main.ts  # Short form

# Allow all network access
deno run --allow-net main.ts
deno run -N main.ts

# Allow all environment variables
deno run --allow-env main.ts
deno run -E main.ts

# Combine multiple
deno run -RNE main.ts
```

### Scoped Permissions (recommended)

```bash
# Only read from specific directories
deno run --allow-read=./data,./config main.ts

# Only connect to specific hosts
deno run --allow-net=api.example.com,localhost:3000 main.ts

# Only access specific env vars
deno run --allow-env=DATABASE_URL,API_KEY main.ts

# Only run specific executables
deno run --allow-run=git,node main.ts

# Only write to specific paths
deno run --allow-write=./output,/tmp main.ts
```

### Network Port Scoping

```bash
# Allow specific ports
deno run --allow-net=:8000,:8080 main.ts

# Allow host with specific port
deno run --allow-net=api.example.com:443 main.ts

# Allow entire host (any port)
deno run --allow-net=example.com main.ts
```

## Deny Flags

Deny flags override allow flags, enabling "allow everything except X" patterns:

```bash
# Read anything EXCEPT /etc and ~/.ssh
deno run --allow-read --deny-read=/etc,~/.ssh main.ts

# Access any network EXCEPT internal hosts
deno run --allow-net --deny-net=10.0.0.0/8,192.168.0.0/16 main.ts

# Access all env vars EXCEPT secrets
deno run --allow-env --deny-env=SECRET_KEY,PRIVATE_KEY main.ts
```

### Precedence Rules

1. Deny flags always win over allow flags
2. Scoped allows take precedence over broad denies for their specific path
3. No flag = denied by default

```bash
# --deny-read=/etc wins over --allow-read
deno run --allow-read --deny-read=/etc main.ts
# Result: Can read everything except /etc
```

## Fine-Grained Scoping

### File System Paths

```bash
# Absolute paths
deno run --allow-read=/home/user/project/data main.ts

# Relative paths (from CWD)
deno run --allow-read=./src,./config main.ts

# Multiple paths (comma-separated)
deno run --allow-write=./logs,./cache,/tmp main.ts
```

### Network Hosts

```bash
# Domain only (any port)
deno run --allow-net=api.github.com main.ts

# Domain with port
deno run --allow-net=localhost:5432 main.ts

# Multiple hosts
deno run --allow-net=api.example.com:443,db.example.com:5432 main.ts

# IP addresses
deno run --allow-net=127.0.0.1:8000 main.ts
```

### Environment Variables

```bash
# Specific variables
deno run --allow-env=NODE_ENV,PORT,DATABASE_URL main.ts

# Prefix patterns (access all AWS_* vars)
deno run --allow-env=AWS_ main.ts
```

## Interactive Prompts

When running in a terminal without explicit permission flags, Deno prompts interactively:

```
┌ ⚠️  Deno requests read access to "./config.json"
├ Run again with --allow-read to bypass this prompt.
├ Allow? [y/n/A] (y = yes, n = no, A = allow all reads)
```

Options:
- `y` — Grant this specific request
- `n` — Deny this request
- `A` — Grant all requests in this category

Prompts are disabled when stdin is not a TTY (CI environments), in which case ungranted permissions are denied.

## Runtime Permission API

Query, request, and revoke permissions programmatically:

### Querying Permissions

```typescript
const status = await Deno.permissions.query({
  name: "read",
  path: "./data",
});

if (status.state === "granted") {
  const data = await Deno.readTextFile("./data/config.json");
} else if (status.state === "prompt") {
  // Can request from user
} else {
  // state === "denied"
}
```

### Requesting Permissions

```typescript
const status = await Deno.permissions.request({
  name: "net",
  host: "api.example.com:443",
});

if (status.state === "granted") {
  const resp = await fetch("https://api.example.com/data");
}
```

### Revoking Permissions

```typescript
// Downgrade previously granted permission
await Deno.permissions.revoke({ name: "read", path: "./temp" });
```

### Permission Descriptors

```typescript
// File system
{ name: "read", path: "/some/path" }
{ name: "write", path: "/some/path" }

// Network
{ name: "net", host: "example.com:443" }

// Environment
{ name: "env", variable: "API_KEY" }

// Subprocess
{ name: "run", command: "git" }

// FFI
{ name: "ffi", path: "/path/to/lib.so" }
```

## Per-Test Permissions

Restrict permissions for individual tests:

```typescript
Deno.test({
  name: "reads config file",
  permissions: {
    read: ["./config"],
    write: false,
    net: false,
    env: false,
    run: false,
  },
  fn() {
    const config = Deno.readTextFileSync("./config/app.json");
    // Network access would throw here
  },
});

// Shorthand: no permissions at all
Deno.test({
  name: "pure computation",
  permissions: "none",
  fn() {
    assertEquals(add(1, 2), 3);
  },
});
```

## Security Best Practices

### Principle of Least Privilege

```bash
# BAD: overly broad
deno run -A server.ts

# GOOD: minimal required permissions
deno run \
  --allow-net=0.0.0.0:8000 \
  --allow-read=./public,./views \
  --allow-env=PORT,DATABASE_URL \
  server.ts
```

### Storing Permissions in deno.json

```jsonc
{
  "tasks": {
    "start": "deno run --allow-net=:8000 --allow-read=./public --allow-env=PORT server.ts",
    "dev": "deno run --watch --allow-net --allow-read --allow-env server.ts"
  }
}
```

### Sandbox-Bypassing Permissions

These permissions can escape the sandbox — use with extreme caution:

- `--allow-run` — Subprocesses have no Deno permission restrictions
- `--allow-ffi` — Native code runs outside the sandbox
- `--allow-write` + `--allow-run` — Can overwrite and execute binaries

### Auditing Dependencies

```bash
# Check for known vulnerabilities
deno audit

# Auto-fix vulnerable dependencies
deno audit fix

# Inspect dependency tree
deno info main.ts
```

## Common Patterns

### Conditional Permission Handling

```typescript
async function loadConfig() {
  const perm = await Deno.permissions.query({ name: "read", path: "./.env" });

  if (perm.state === "granted") {
    return await Deno.readTextFile("./.env");
  }

  // Fall back to environment variables
  return Deno.env.get("CONFIG") ?? "{}";
}
```

### Permission-Aware Libraries

```typescript
export async function connectDB(url: string) {
  const host = new URL(url).hostname;
  const perm = await Deno.permissions.request({
    name: "net",
    host,
  });

  if (perm.state !== "granted") {
    throw new Error(`Network permission denied for ${host}`);
  }

  return await connect(url);
}
```

## Common Pitfalls

1. **Using `-A` in production** — defeats the entire security model
2. **Forgetting port in --allow-net** — `--allow-net=localhost` allows ALL ports on localhost
3. **Relative paths change with CWD** — use absolute paths for predictable behavior
4. **Subprocess escape** — a subprocess spawned with `--allow-run` has full system access
5. **Dynamic imports** — `import()` from remote URLs requires `--allow-import`
