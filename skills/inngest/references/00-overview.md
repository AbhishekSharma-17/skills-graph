# Inngest — Overview & Quickstart

> Source: [inngest.com/docs](https://www.inngest.com/docs)

## Table of Contents

- [What is Inngest?](#what-is-inngest)
- [Core Concepts](#core-concepts)
- [Architecture](#architecture)
- [Installation](#installation)
- [TypeScript Quickstart (Next.js)](#typescript-quickstart-nextjs)
- [Python Quickstart (FastAPI)](#python-quickstart-fastapi)
- [Dev Server](#dev-server)
- [Key Terminology](#key-terminology)
- [When to Use Inngest](#when-to-use-inngest)
- [Inngest vs Alternatives](#inngest-vs-alternatives)

---

## What is Inngest?

Inngest is a durable workflow orchestration platform that lets you write reliable step functions without managing queues, workers, or infrastructure. Functions are triggered by events or cron schedules and execute as durable, retriable workflows.

Key value proposition:
- **No queues** — Inngest manages the queue; you just write functions
- **No workers** — Functions run via HTTP; Inngest calls your code
- **Durable execution** — State persists across retries, sleeps, and failures
- **Any platform** — Serverless, edge, containers, or traditional servers

## Core Concepts

### Events
Events are the primary trigger mechanism. An event is a JSON payload with a `name` and `data` field:

```typescript
await inngest.send({
  name: "user/signup.completed",
  data: {
    userId: "usr_123",
    email: "user@example.com",
    plan: "pro",
  },
});
```

### Functions
Functions are the units of work. Each function has a unique ID, one or more triggers, and a handler:

```typescript
const processSignup = inngest.createFunction(
  { id: "process-signup", triggers: { event: "user/signup.completed" } },
  async ({ event, step }) => {
    // Durable, retriable logic here
  }
);
```

### Steps
Steps are checkpointed units within a function. Each step is independently retriable and its result is memoized:

```typescript
const user = await step.run("fetch-user", async () => {
  return db.users.find(event.data.userId);
});
```

## Architecture

```
┌──────────────┐    Events     ┌──────────────────┐
│  Your App    │──────────────>│  Inngest Platform │
│  (SDK)       │               │  (Queue + State)  │
└──────────────┘               └────────┬─────────┘
       ^                                │
       │         HTTP invocation        │
       └────────────────────────────────┘
```

1. Your app sends events via the SDK
2. Inngest platform queues and schedules function runs
3. Inngest calls your function handlers via HTTP
4. Step results are persisted; failed steps are retried

## Installation

### TypeScript / JavaScript

```bash
# Install the SDK
npm install inngest

# Install the CLI for local dev
npx inngest-cli@latest dev
```

### Python

```bash
# Python 3.10+ required
pip install inngest

# CLI for local dev
npx inngest-cli@latest dev
```

## TypeScript Quickstart (Next.js)

### 1. Create the Inngest client

```typescript
// src/inngest/client.ts
import { Inngest } from "inngest";

export const inngest = new Inngest({ id: "my-app" });
```

### 2. Create a function

```typescript
// src/inngest/functions.ts
import { inngest } from "./client";

export const sendWelcomeEmail = inngest.createFunction(
  { id: "send-welcome-email", triggers: { event: "user/signup.completed" } },
  async ({ event, step }) => {
    const user = await step.run("get-user", async () => {
      return await db.users.findById(event.data.userId);
    });

    await step.run("send-email", async () => {
      return await emailService.send({
        to: user.email,
        template: "welcome",
      });
    });

    await step.sleep("wait-3-days", "3d");

    await step.run("send-followup", async () => {
      return await emailService.send({
        to: user.email,
        template: "onboarding-tips",
      });
    });

    return { status: "complete" };
  }
);
```

### 3. Serve the functions

```typescript
// src/app/api/inngest/route.ts (Next.js App Router)
import { serve } from "inngest/next";
import { inngest } from "../../../inngest/client";
import { sendWelcomeEmail } from "../../../inngest/functions";

export const { GET, POST, PUT } = serve({
  client: inngest,
  functions: [sendWelcomeEmail],
});
```

### 4. Send an event

```typescript
// From any server-side code
import { inngest } from "./inngest/client";

await inngest.send({
  name: "user/signup.completed",
  data: { userId: "usr_123" },
});
```

### 5. Start development

```bash
# Terminal 1: Start your app
INNGEST_DEV=1 npm run dev

# Terminal 2: Start Inngest Dev Server
npx inngest-cli@latest dev
```

Open http://localhost:8288 to see the Inngest Dev Server dashboard.

## Python Quickstart (FastAPI)

### 1. Create the client and function

```python
# main.py
import logging
import inngest
import inngest.fast_api
from fastapi import FastAPI

inngest_client = inngest.Inngest(
    app_id="my-python-app",
    logger=logging.getLogger("uvicorn"),
)

@inngest_client.create_function(
    fn_id="process-upload",
    trigger=inngest.TriggerEvent(event="file/uploaded"),
)
async def process_upload(ctx: inngest.Context) -> str:
    file_url = ctx.event.data["url"]
    ctx.logger.info(f"Processing file: {file_url}")
    # Your processing logic here
    return "done"

app = FastAPI()
inngest.fast_api.serve(app, inngest_client, [process_upload])
```

### 2. Start development

```bash
# Terminal 1
INNGEST_DEV=1 uvicorn main:app --reload

# Terminal 2
npx inngest-cli@latest dev -u http://127.0.0.1:8000/api/inngest --no-discovery
```

## Dev Server

The Inngest Dev Server provides:
- **Function discovery** — Auto-detects registered functions
- **Event sending** — Test functions with custom payloads
- **Run monitoring** — Watch step-by-step execution
- **Timeline view** — Inspect memoized state and retries
- **MCP support** — Connect AI assistants like Claude Code

```bash
# Start with defaults (discovers apps on common ports)
npx inngest-cli@latest dev

# Specify your app URL explicitly
npx inngest-cli@latest dev -u http://localhost:3000/api/inngest
```

## Key Terminology

| Term | Definition |
|------|-----------|
| **Event** | JSON payload with `name` and `data` that triggers functions |
| **Function** | A durable unit of work with triggers, config, and a handler |
| **Step** | A checkpointed operation within a function (retriable, memoized) |
| **Run** | A single execution of a function triggered by an event |
| **Durable execution** | State persists across retries, sleeps, and infrastructure failures |
| **Memoization** | Completed step results are cached and replayed on re-execution |
| **Serve handler** | HTTP endpoint that exposes your functions to the Inngest platform |
| **Event key** | API key for sending events to Inngest |
| **Signing key** | Secret key for verifying Inngest platform requests |

## When to Use Inngest

**Good fit:**
- Multi-step workflows (onboarding sequences, data pipelines)
- Background jobs with retry requirements
- Scheduled/cron tasks
- Event-driven architectures
- AI agent orchestration with durable state
- Fan-out processing (batch imports, bulk operations)

**Not ideal for:**
- Sub-100ms latency requirements (HTTP invocation overhead)
- Simple fire-and-forget tasks with no retry needs
- Real-time streaming (use WebSockets/SSE instead)

## Inngest vs Alternatives

| Feature | Inngest | BullMQ | Temporal | Trigger.dev |
|---------|---------|--------|----------|-------------|
| Queue management | Managed | Self-hosted Redis | Self-hosted | Managed |
| Language support | TS, Python, Go | Node.js | Multi-language | TS |
| Durable execution | Yes | No | Yes | Yes |
| Serverless-native | Yes | No | No | Yes |
| Local dev tools | Dev Server | Redis + Dashboard | Dev Server | Dev Server |
| Step-level retries | Yes | Job-level | Yes | Yes |
| Event-driven | Yes | Job-based | Signal-based | Event + Job |
