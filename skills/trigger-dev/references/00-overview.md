# Trigger.dev Overview & Setup

> Source: https://trigger.dev/docs — v4.4.3

## What is Trigger.dev?

Trigger.dev is an open-source platform for building and deploying background jobs, AI workflows, and scheduled tasks in TypeScript. It provides:

- **Long-running tasks** — No timeout limits. Tasks can run for hours or days.
- **Durable execution** — Automatic checkpointing means tasks survive crashes and restarts.
- **Retries with backoff** — Configurable exponential backoff with jitter.
- **Queues and concurrency** — Built-in queue management with per-task and per-tenant concurrency limits.
- **Scheduled tasks** — Cron-based scheduling with timezone support and DST handling.
- **Realtime updates** — Stream task progress and data to your frontend via SSE.
- **Human-in-the-loop** — Pause tasks and wait for external approval via tokens.
- **Elastic scaling** — Auto-scales workers based on queue depth.
- **Observability** — OpenTelemetry integration, structured logging, distributed tracing.
- **Build extensions** — Prisma, Puppeteer, FFmpeg, Python, and custom extensions.

## When to Use Trigger.dev

| Use Case | Example |
|----------|---------|
| Background processing | PDF generation, image processing, data import/export |
| AI workflows | LLM chains, RAG pipelines, agent orchestration |
| Scheduled jobs | Daily reports, data sync, cleanup tasks |
| Webhooks | Process incoming webhooks reliably with retries |
| Email sequences | Drip campaigns with delays between sends |
| Multi-step workflows | Order processing, onboarding flows |
| Fan-out processing | Process thousands of items in parallel batches |

## When NOT to Use Trigger.dev

- Simple synchronous API handlers (use your web framework directly)
- Sub-second latency requirements (tasks have queue overhead)
- Stateless lambda-style functions with no retry needs (use Vercel/Cloudflare Functions)

## Architecture

```
Your App (Next.js, Express, etc.)
    |
    | tasks.trigger("my-task", payload)
    |
    v
Trigger.dev Cloud / Self-hosted
    |
    |-- Queue Management
    |-- Worker Orchestration
    |-- Checkpointing
    |-- Retry Logic
    |
    v
Task Workers (isolated containers)
    |
    |-- Your task code runs here
    |-- Auto-scaled based on load
    |-- Configurable machine size (CPU/RAM)
```

**Key concept:** Your task code lives in your repo alongside your app code. Trigger.dev bundles and deploys it to isolated workers. You trigger tasks from your backend using the SDK.

## Installation & Project Setup

### New Project

```bash
# Initialize Trigger.dev in your project
npx trigger.dev@latest init
```

This creates:
- `trigger.config.ts` — Project configuration
- `trigger/` directory — Where your tasks live
- Updates `package.json` with the SDK dependency

### Existing Project

```bash
# Install the SDK
npm install @trigger.dev/sdk
# or
pnpm add @trigger.dev/sdk
# or
yarn add @trigger.dev/sdk
```

### Project Structure

```
my-app/
├── trigger.config.ts       # Trigger.dev configuration
├── trigger/                # Task definitions
│   ├── my-task.ts
│   ├── email-sequence.ts
│   └── data-import.ts
├── src/                    # Your app code
│   └── api/
│       └── route.ts        # Triggers tasks from here
└── package.json
```

### Environment Setup

Set the `TRIGGER_SECRET_KEY` environment variable for backend triggering:

```bash
# .env
TRIGGER_SECRET_KEY=tr_dev_xxxx  # Development
TRIGGER_SECRET_KEY=tr_prod_xxxx # Production
```

Get your keys from the Trigger.dev dashboard → Project → API Keys.

## Quickstart: Your First Task

### 1. Define a Task

```typescript
// trigger/hello-world.ts
import { task } from "@trigger.dev/sdk/v3";

export const helloWorldTask = task({
  id: "hello-world",
  maxDuration: 300, // 5 minutes max
  run: async (payload: { name: string }) => {
    console.log(`Hello, ${payload.name}!`);

    // Simulate some work
    await new Promise((resolve) => setTimeout(resolve, 1000));

    return {
      message: `Processed greeting for ${payload.name}`,
      timestamp: new Date().toISOString(),
    };
  },
});
```

### 2. Run the Dev Server

```bash
npx trigger.dev@latest dev
```

This starts a local dev server that connects to the Trigger.dev cloud (or your self-hosted instance) and registers your tasks.

### 3. Trigger from Your Backend

```typescript
// src/api/greet.ts
import { tasks } from "@trigger.dev/sdk/v3";
import type { helloWorldTask } from "../../trigger/hello-world";

export async function POST(request: Request) {
  const { name } = await request.json();

  const handle = await tasks.trigger<typeof helloWorldTask>(
    "hello-world",
    { name }
  );

  return Response.json({
    runId: handle.id,
    message: "Task triggered successfully",
  });
}
```

### 4. Monitor in Dashboard

Open `https://cloud.trigger.dev` to see your task runs, logs, and status in real-time.

## SDK Imports

All v4 functionality comes from the `@trigger.dev/sdk/v3` module:

```typescript
// Core
import { task, queue } from "@trigger.dev/sdk/v3";

// Scheduling
import { schedules } from "@trigger.dev/sdk/v3";

// Management
import { tasks, runs, queues, envvars } from "@trigger.dev/sdk/v3";

// Wait functions
import { wait } from "@trigger.dev/sdk/v3";

// Retry utilities
import { retry } from "@trigger.dev/sdk/v3";

// Logging
import { logger } from "@trigger.dev/sdk/v3";

// Streams
import { streams } from "@trigger.dev/sdk/v3";

// Metadata
import { metadata } from "@trigger.dev/sdk/v3";

// Configuration
import { configure } from "@trigger.dev/sdk/v3";
```

## Supported Frameworks

Trigger.dev works with any TypeScript/JavaScript backend:

| Framework | Integration |
|-----------|-------------|
| Next.js | `tasks.trigger()` from API routes or server actions |
| Express | `tasks.trigger()` from route handlers |
| Fastify | `tasks.trigger()` from route handlers |
| Hono | `tasks.trigger()` from route handlers |
| Remix | `tasks.trigger()` from loaders/actions |
| NestJS | `tasks.trigger()` from services |
| SvelteKit | `tasks.trigger()` from server endpoints |
| Nuxt | `tasks.trigger()` from server routes |

## Key Terminology

| Term | Definition |
|------|-----------|
| **Task** | A function that runs in the background with retries and observability |
| **Run** | A single execution of a task with a specific payload |
| **Attempt** | One execution try within a run (runs can have multiple attempts via retries) |
| **Queue** | A FIFO queue that manages task concurrency |
| **Waitpoint** | A checkpoint where a task pauses and releases compute resources |
| **Handle** | A reference to a triggered run, used to track or wait for results |
| **Deployment** | A versioned bundle of your tasks deployed to workers |

## Related Topics

- Writing tasks → `01-writing-tasks.md`
- Triggering tasks → `02-triggering-tasks.md`
- Configuration → `09-configuration.md`
- Deployment → `10-deployment-cli.md`
