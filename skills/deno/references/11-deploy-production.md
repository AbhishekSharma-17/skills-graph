# Deployment and Production

> Source: https://docs.deno.com/deploy/ | https://docs.deno.com/runtime/reference/continuous_integration/

## Table of Contents

- [Deno Deploy](#deno-deploy)
- [deno compile (Standalone Binaries)](#deno-compile-standalone-binaries)
- [Docker Deployment](#docker-deployment)
- [CI/CD with GitHub Actions](#cicd-with-github-actions)
- [Process Management](#process-management)
- [Environment Configuration](#environment-configuration)
- [Performance Tuning](#performance-tuning)
- [Monitoring and Observability](#monitoring-and-observability)

## Deno Deploy

Deno Deploy is a serverless platform for running JavaScript/TypeScript at the edge with global distribution.

### Features

- Global edge deployment (35+ regions)
- Zero cold-start for Deno applications
- Built-in KV database (Deno.openKv)
- Cron job scheduling (Deno.cron)
- Automatic HTTPS
- GitHub integration for continuous deployment
- Framework support: Fresh, Next.js, Astro, SvelteKit

### Deploy from CLI

```bash
# Link project to Deno Deploy
deno deploy

# Deploy with specific entry point
deno deploy --entrypoint=main.ts

# Production deploy
deno deploy --prod

# Preview deploy (unique URL)
deno deploy --preview
```

### Deploy Configuration

```jsonc
// deno.json
{
  "deploy": {
    "project": "my-project-name",
    "entrypoint": "main.ts",
    "exclude": ["tests/", "*.test.ts"]
  }
}
```

### Deno KV (Deploy Database)

```typescript
const kv = await Deno.openKv();

// Set a value
await kv.set(["users", "user-123"], { name: "Alice", email: "alice@test.com" });

// Get a value
const result = await kv.get(["users", "user-123"]);
console.log(result.value); // { name: "Alice", ... }

// List by prefix
const users = kv.list({ prefix: ["users"] });
for await (const entry of users) {
  console.log(entry.key, entry.value);
}

// Atomic transactions
await kv.atomic()
  .check({ key: ["users", "user-123"], versionstamp: result.versionstamp })
  .set(["users", "user-123"], { ...result.value, name: "Alice Smith" })
  .commit();

// Delete
await kv.delete(["users", "user-123"]);

// Enqueue (built-in message queue)
await kv.enqueue({ type: "email", to: "user@test.com", subject: "Welcome" });
kv.listenQueue(async (msg) => {
  await sendEmail(msg);
});
```

### Deno Cron (Deploy Scheduled Tasks)

```typescript
Deno.cron("cleanup-expired-sessions", "0 */6 * * *", async () => {
  const kv = await Deno.openKv();
  // Clean up expired sessions every 6 hours
});

Deno.cron("daily-report", "0 9 * * 1-5", async () => {
  // Send report on weekdays at 9 AM
});
```

## deno compile (Standalone Binaries)

Create self-contained executables with no runtime dependency:

```bash
# Basic compile
deno compile --allow-net --allow-read server.ts

# Named output
deno compile --output=dist/myapp main.ts

# Cross-compile
deno compile --target=x86_64-unknown-linux-gnu --output=dist/myapp-linux main.ts
deno compile --target=aarch64-apple-darwin --output=dist/myapp-mac-arm main.ts
deno compile --target=x86_64-pc-windows-msvc --output=dist/myapp.exe main.ts

# Include static assets
deno compile --include=./public --include=./templates main.ts

# Self-extracting (v2.9+)
deno compile --output=dist/app.deb main.ts   # Linux package
deno compile --output=dist/app.msi main.ts   # Windows installer
```

### Accessing Embedded Files

```typescript
// Files included via --include are accessible normally
const html = await Deno.readTextFile("./public/index.html");
```

### Compile Targets

| Target | OS | Architecture |
|--------|----|-------------|
| `x86_64-unknown-linux-gnu` | Linux | x86_64 |
| `aarch64-unknown-linux-gnu` | Linux | ARM64 |
| `x86_64-pc-windows-msvc` | Windows | x86_64 |
| `x86_64-apple-darwin` | macOS | x86_64 |
| `aarch64-apple-darwin` | macOS | ARM64 (Apple Silicon) |

## Docker Deployment

### Basic Dockerfile

```dockerfile
FROM denoland/deno:2.9.0

WORKDIR /app

# Cache dependencies
COPY deno.json deno.lock ./
RUN deno install

# Copy source
COPY . .

# Cache compilation
RUN deno check main.ts

EXPOSE 8000
USER deno

CMD ["deno", "run", "--allow-net", "--allow-read", "--allow-env", "main.ts"]
```

### Multi-Stage Build (Smaller Image)

```dockerfile
# Build stage
FROM denoland/deno:2.9.0 AS builder
WORKDIR /app
COPY . .
RUN deno compile --allow-net --allow-read --allow-env --output=server main.ts

# Runtime stage
FROM debian:bookworm-slim
COPY --from=builder /app/server /usr/local/bin/server
EXPOSE 8000
USER 1000
CMD ["server"]
```

### Docker Compose

```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgres://db:5432/app
      - PORT=8000
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:16
    environment:
      POSTGRES_DB: app
      POSTGRES_PASSWORD: secret
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

## CI/CD with GitHub Actions

### Basic Workflow

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: denoland/setup-deno@v2
        with:
          deno-version: v2.x
          cache: true

      - run: deno ci
      - run: deno fmt --check
      - run: deno lint
      - run: deno check main.ts
      - run: deno test --allow-all --coverage=./cov
      - run: deno coverage ./cov --lcov > lcov.info

      - uses: codecov/codecov-action@v4
        with:
          file: ./lcov.info
```

### Deploy on Push

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: denoland/setup-deno@v2
        with:
          deno-version: v2.x
      - run: deno deploy --prod --token=${{ secrets.DENO_DEPLOY_TOKEN }}
```

### Cross-Platform Testing

```yaml
jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: denoland/setup-deno@v2
        with:
          deno-version: v2.x
          cache: true
      - run: deno test --allow-all
```

## Process Management

### Using systemd (Linux)

```ini
# /etc/systemd/system/deno-app.service
[Unit]
Description=Deno Application
After=network.target

[Service]
Type=simple
User=deno
WorkingDirectory=/opt/app
ExecStart=/usr/bin/deno run --allow-net --allow-read --allow-env main.ts
Restart=on-failure
RestartSec=5
Environment=PORT=8000
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable deno-app
sudo systemctl start deno-app
sudo journalctl -u deno-app -f
```

### Graceful Shutdown

```typescript
const server = Deno.serve({ port: 8000 }, handler);

const shutdown = async () => {
  console.log("Graceful shutdown...");
  await server.shutdown();
  Deno.exit(0);
};

Deno.addSignalListener("SIGINT", shutdown);
Deno.addSignalListener("SIGTERM", shutdown);

await server.finished;
```

## Environment Configuration

### .env Files (Development)

```typescript
// Load .env in development
import "jsr:@std/dotenv/load";

const port = parseInt(Deno.env.get("PORT") ?? "8000");
const dbUrl = Deno.env.get("DATABASE_URL");
```

### Configuration Pattern

```typescript
function loadConfig() {
  return {
    port: parseInt(Deno.env.get("PORT") ?? "8000"),
    host: Deno.env.get("HOST") ?? "0.0.0.0",
    database: Deno.env.get("DATABASE_URL") ?? "sqlite://./dev.db",
    logLevel: Deno.env.get("LOG_LEVEL") ?? "info",
    isProduction: Deno.env.get("DENO_ENV") === "production",
  };
}
```

## Performance Tuning

### Parallel Workers (deno serve)

```bash
# Use all available CPU cores
deno serve --parallel server.ts
```

### Automatic Compression

```typescript
Deno.serve({
  port: 8000,
  automaticCompression: true, // gzip/brotli based on Accept-Encoding
}, handler);
```

### Static Asset Caching

```typescript
Deno.serve((req) => {
  const url = new URL(req.url);

  if (url.pathname.startsWith("/static/")) {
    return serveDir(req, {
      fsRoot: "./public",
      headers: ["cache-control:public, max-age=31536000, immutable"],
    });
  }

  return handler(req);
});
```

## Monitoring and Observability

### OpenTelemetry Integration

```typescript
// Deno has built-in OpenTelemetry support
// Enable via environment variables:
// OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
// OTEL_SERVICE_NAME=my-deno-app

// Traces, metrics, and logs are automatically collected
```

```bash
# Run with OTel enabled
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 \
OTEL_SERVICE_NAME=my-app \
deno run --allow-all --unstable-otel main.ts
```

### Health Check Endpoint

```typescript
app.get("/health", () => {
  return new Response(JSON.stringify({
    status: "healthy",
    version: Deno.version.deno,
    uptime: performance.now(),
    memory: Deno.memoryUsage(),
  }), {
    headers: { "content-type": "application/json" },
  });
});
```

## Common Pitfalls

1. **Missing permissions in Docker** — explicitly list all needed `--allow-*` flags in CMD
2. **Lock file in CI** — use `deno ci` not `deno install` for reproducible builds
3. **Compile target mismatch** — compile on the same arch/OS as deployment, or cross-compile explicitly
4. **No graceful shutdown** — always handle SIGTERM for container orchestrators
5. **Deno Deploy limits** — 50ms CPU time per request, 512MB memory per isolate
6. **KV consistency** — `Deno.openKv()` is eventually consistent across regions in Deploy
