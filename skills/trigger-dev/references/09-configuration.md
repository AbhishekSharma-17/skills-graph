# Configuration

> Source: https://trigger.dev/docs — v4.4.3

## Contents

- [trigger.config.ts](#triggerconfigts)
- [Project Settings](#project-settings)
- [Runtime Configuration](#runtime-configuration)
- [Retry Defaults](#retry-defaults)
- [Build Configuration](#build-configuration)
- [Build Extensions](#build-extensions)
- [Telemetry & Observability](#telemetry--observability)
- [Process Management](#process-management)

## trigger.config.ts

The `trigger.config.ts` file at your project root controls how Trigger.dev builds and runs your tasks.

```typescript
import { defineConfig } from "@trigger.dev/sdk/v3";

export default defineConfig({
  // Required: Project reference from dashboard
  project: "proj_xxxx",

  // Directories containing task files
  dirs: ["./trigger"],

  // Default machine for all tasks
  machine: "small-1x",

  // Default max duration (seconds)
  maxDuration: 300,

  // Log level for logger API
  logLevel: "info",

  // Runtime: "node" (default), "node-22", or "bun"
  runtime: "node",

  // Global retry defaults
  retries: {
    enabledInDev: false,
    default: {
      maxAttempts: 3,
      factor: 2,
      minTimeoutInMs: 1000,
      maxTimeoutInMs: 30000,
      randomize: true,
    },
  },

  // Build configuration
  build: {
    external: [],          // Packages to exclude from bundling
    autoDetectExternal: true,
    keepNames: true,       // Preserve function/class names
    minify: false,         // Experimental
    extensions: [],        // Build extensions
  },

  // Lifecycle hooks (global)
  onStart: async (payload, { ctx }) => {
    console.log(`Task ${ctx.task.id} started`);
  },
  onSuccess: async (payload, output, { ctx }) => {
    console.log(`Task ${ctx.task.id} succeeded`);
  },
  onFailure: async (payload, error, { ctx }) => {
    console.error(`Task ${ctx.task.id} failed:`, error);
  },
});
```

## Project Settings

| Property | Type | Description |
|----------|------|-------------|
| `project` | `string` | Project reference from dashboard (required) |
| `dirs` | `string[]` | Task directories (default: `["./trigger"]`) |
| `tsconfig` | `string` | Custom tsconfig path |
| `ignorePatterns` | `string[]` | Glob patterns to exclude from build |

## Runtime Configuration

### Node.js

```typescript
export default defineConfig({
  runtime: "node",       // Node.js 21.7.3 (default)
  // or
  runtime: "node-22",   // Node.js 22.16.0
});
```

### Bun

```typescript
export default defineConfig({
  runtime: "bun",  // Bun 1.3.3
});
```

### Machine Defaults

Set a default machine for all tasks:

```typescript
export default defineConfig({
  machine: "medium-1x",  // 1 vCPU, 2GB RAM
  maxDuration: 600,       // 10 minutes default
});
```

Individual tasks can override these settings.

## Retry Defaults

```typescript
export default defineConfig({
  retries: {
    // Disable retries in development (recommended)
    enabledInDev: false,

    default: {
      maxAttempts: 3,
      factor: 2,
      minTimeoutInMs: 1000,
      maxTimeoutInMs: 30000,
      randomize: true,
    },
  },
});
```

## Build Configuration

### External Packages

Exclude packages that use native binaries or WASM from bundling:

```typescript
export default defineConfig({
  build: {
    external: [
      "sharp",        // Uses native binaries
      "@prisma/client", // Handled by Prisma extension
      "canvas",       // Native dependency
    ],
    autoDetectExternal: true, // Auto-detect (default: true)
  },
});
```

### JSX Configuration

```typescript
export default defineConfig({
  build: {
    jsx: {
      factory: "React.createElement",
      fragment: "React.Fragment",
      automatic: true,  // Use React 17+ JSX transform
    },
  },
});
```

### Import Conditions

```typescript
export default defineConfig({
  build: {
    conditions: ["react-server"], // Custom import conditions
  },
});
```

## Build Extensions

Pre-built extensions hook into the build system for common tools:

### Prisma

```typescript
import { defineConfig } from "@trigger.dev/sdk/v3";
import { prismaExtension } from "@trigger.dev/build/extensions/prisma";

export default defineConfig({
  build: {
    extensions: [
      prismaExtension({
        schema: "prisma/schema.prisma",
        version: "6.4.1",  // Optional: pin version
      }),
    ],
  },
});
```

### Puppeteer

```typescript
import { puppeteer } from "@trigger.dev/build/extensions/puppeteer";

export default defineConfig({
  build: {
    extensions: [puppeteer()],
  },
});
```

### FFmpeg

```typescript
import { ffmpeg } from "@trigger.dev/build/extensions/ffmpeg";

export default defineConfig({
  build: {
    extensions: [ffmpeg()],
  },
});
```

### Additional Packages and Files

```typescript
import {
  additionalPackages,
  additionalFiles,
} from "@trigger.dev/build/extensions";

export default defineConfig({
  build: {
    extensions: [
      additionalPackages({ packages: ["wrangler"] }),
      additionalFiles({
        files: ["assets/template.html", "config/defaults.json"],
      }),
    ],
  },
});
```

### System Packages (apt-get)

```typescript
import { aptGet } from "@trigger.dev/build/extensions/apt-get";

export default defineConfig({
  build: {
    extensions: [
      aptGet({ packages: ["libcairo2-dev", "libjpeg-dev"] }),
    ],
  },
});
```

### Python Extension

```typescript
import { python } from "@trigger.dev/build/extensions/python";

export default defineConfig({
  build: {
    extensions: [
      python({
        requirements: "requirements.txt",
        version: "3.12",
      }),
    ],
  },
});
```

### Environment Variable Sync

```typescript
import { syncEnvVars } from "@trigger.dev/build/extensions/core";

export default defineConfig({
  build: {
    extensions: [
      syncEnvVars(async (ctx) => {
        // Fetch from your secret manager
        return {
          DATABASE_URL: process.env.DATABASE_URL!,
          API_KEY: process.env.API_KEY!,
        };
      }),
    ],
  },
});
```

### Custom esbuild Plugin

```typescript
import { esbuildPlugin } from "@trigger.dev/build/extensions";

export default defineConfig({
  build: {
    extensions: [
      esbuildPlugin(myCustomPlugin, { target: "deploy" }),
    ],
  },
});
```

## Telemetry & Observability

### OpenTelemetry Instrumentations

```typescript
import { defineConfig } from "@trigger.dev/sdk/v3";

export default defineConfig({
  instrumentations: [
    // Auto-instrument HTTP calls
    new HttpInstrumentation(),
    // Auto-instrument Prisma queries
    new PrismaInstrumentation(),
    // Auto-instrument OpenAI calls
    new OpenAIInstrumentation(),
  ],
});
```

### Export to External Services

```typescript
export default defineConfig({
  // Trace exporters
  exporters: [
    new OTLPTraceExporter({
      url: "https://otel.example.com/v1/traces",
    }),
  ],

  // Log exporters
  logExporters: [
    new OTLPLogExporter({
      url: "https://otel.example.com/v1/logs",
    }),
  ],

  // Metric exporters
  metricExporters: [
    new OTLPMetricExporter({
      url: "https://otel.example.com/v1/metrics",
    }),
  ],
});
```

**Important:** Configure exporters via constructor arguments, not environment variables, to avoid conflicts with Trigger.dev's internal telemetry.

### Popular Integrations

| Service | Exporter |
|---------|----------|
| Axiom | `@axiomhq/opentelemetry-node` |
| Honeycomb | `@honeycombio/opentelemetry-node` |
| Datadog | `dd-trace` |
| Grafana | OTLP exporters |

## Process Management

### Process Keep Alive

Reuse worker processes across executions for faster warm starts:

```typescript
export default defineConfig({
  processKeepAlive: {
    enabled: true,
    maxExecutionsPerProcess: 50,  // Recycle after 50 runs
    devMaxPoolSize: 25,           // Max concurrent processes in dev
  },
});
```

### Console Logging

```typescript
export default defineConfig({
  enableConsoleLogging: true,          // Show console output in dev
  disableConsoleInterceptor: false,    // Dashboard log interception
  logLevel: "debug",                   // debug, info, log, warn, error
});
```

### Extra CA Certificates (Self-Hosted)

```typescript
export default defineConfig({
  extraCACerts: "/path/to/ca-certificates.crt",
});
```

## Related Topics

- Writing tasks → `01-writing-tasks.md`
- Build extensions → covered in this file
- Deployment → `10-deployment-cli.md`
