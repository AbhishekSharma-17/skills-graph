# Realtime & Streaming

> Source: https://trigger.dev/docs — v4.4.3

## Contents

- [Overview](#overview)
- [Run Subscriptions](#run-subscriptions)
- [Streaming](#streaming)
- [React Hooks](#react-hooks)
- [Authentication](#authentication)
- [Common Patterns](#common-patterns)

## Overview

Trigger.dev's Realtime API provides two patterns for live updates:

1. **Run subscriptions** — Monitor run status, metadata, and tag changes (automatic, no task code changes)
2. **Streaming** — Pipe continuous data from tasks to your frontend (requires defining streams in task code)

Both use Server-Sent Events (SSE) under the hood.

## Run Subscriptions

Subscribe to real-time updates for individual runs, batches, or groups of runs by tag.

### Subscribe to a Single Run (Backend)

```typescript
import { runs } from "@trigger.dev/sdk/v3";
import type { myTask } from "../trigger/my-task";

// AsyncIterator pattern
for await (const run of runs.subscribeToRun<typeof myTask>(runId)) {
  console.log(`Status: ${run.status}`);
  console.log(`Metadata: ${JSON.stringify(run.metadata)}`);

  if (run.isCompleted) {
    console.log("Output:", run.output);
    break;
  }
  if (run.isFailed) {
    console.error("Error:", run.error);
    break;
  }
}
```

### Subscribe by Tag (Backend)

```typescript
// Watch all runs with a specific tag
for await (const run of runs.subscribeToRunsWithTag("user:alice")) {
  console.log(`Run ${run.id}: ${run.status}`);
}
```

### Subscribe to Batch

```typescript
for await (const run of runs.subscribeToBatch(batchId)) {
  console.log(`Run ${run.id}: ${run.status}`);
}
```

## Streaming

Define typed streams in your tasks and pipe data to the frontend in real-time.

### Define Streams in Task

```typescript
import { task, streams } from "@trigger.dev/sdk/v3";

export const aiStreamTask = task({
  id: "ai-stream",
  run: async (payload: { prompt: string }) => {
    // Define a typed stream
    const textStream = await streams.define<string>("ai-output");

    // Pipe data to the stream
    const response = await openai.chat.completions.create({
      model: "gpt-4o",
      messages: [{ role: "user", content: payload.prompt }],
      stream: true,
    });

    for await (const chunk of response) {
      const content = chunk.choices[0]?.delta?.content;
      if (content) {
        await textStream.write(content);
      }
    }

    // Close the stream when done
    await textStream.close();

    return { status: "complete" };
  },
});
```

### Read Streams (Backend)

```typescript
import { streams } from "@trigger.dev/sdk/v3";

for await (const chunk of streams.subscribe<string>(runId, "ai-output")) {
  process.stdout.write(chunk);
}
```

## React Hooks

The `@trigger.dev/react-hooks` package provides React hooks for real-time updates.

### Installation

```bash
npm install @trigger.dev/react-hooks
```

### useRealtimeRun — Track Run Status

```tsx
import { useRealtimeRun } from "@trigger.dev/react-hooks";
import type { myTask } from "../../trigger/my-task";

function TaskStatus({ runId }: { runId: string }) {
  const { run, error } = useRealtimeRun<typeof myTask>(runId);

  if (error) return <div>Error: {error.message}</div>;
  if (!run) return <div>Loading...</div>;

  return (
    <div>
      <p>Status: {run.status}</p>
      {run.metadata?.progress && (
        <progress value={run.metadata.progress.percent} max={100} />
      )}
      {run.isCompleted && <p>Output: {JSON.stringify(run.output)}</p>}
      {run.isFailed && <p>Error: {run.error}</p>}
    </div>
  );
}
```

### useRealtimeRunsWithTag — Track Multiple Runs

```tsx
import { useRealtimeRunsWithTag } from "@trigger.dev/react-hooks";

function UserTasks({ userId }: { userId: string }) {
  const { runs, error } = useRealtimeRunsWithTag(`user:${userId}`);

  return (
    <ul>
      {runs.map((run) => (
        <li key={run.id}>
          {run.taskIdentifier}: {run.status}
        </li>
      ))}
    </ul>
  );
}
```

### useRealtimeStream — Read Streaming Data

```tsx
import { useRealtimeStream } from "@trigger.dev/react-hooks";

function AIOutput({ runId }: { runId: string }) {
  const { data, isComplete } = useRealtimeStream<string>(runId, "ai-output");

  return (
    <div>
      <pre>{data.join("")}</pre>
      {!isComplete && <span className="cursor-blink" />}
    </div>
  );
}
```

### useRealtimeBatch — Track Batch Progress

```tsx
import { useRealtimeBatch } from "@trigger.dev/react-hooks";

function BatchProgress({ batchId }: { batchId: string }) {
  const { runs } = useRealtimeBatch(batchId);

  const completed = runs.filter((r) => r.isCompleted).length;
  const total = runs.length;

  return (
    <div>
      <progress value={completed} max={total} />
      <span>{completed}/{total} complete</span>
    </div>
  );
}
```

## Authentication

React hooks need authentication to access the Realtime API.

### TriggerAuthContext Provider

```tsx
import { TriggerAuthContext } from "@trigger.dev/react-hooks";

function App() {
  return (
    <TriggerAuthContext.Provider
      value={{
        // Generate a public access token from your backend
        accessToken: publicAccessToken,
        baseURL: "https://api.trigger.dev", // or your self-hosted URL
      }}
    >
      <TaskDashboard />
    </TriggerAuthContext.Provider>
  );
}
```

### Generating Public Access Tokens

From your backend, generate a scoped token for the frontend:

```typescript
import { auth } from "@trigger.dev/sdk/v3";

// In your API route
const token = await auth.createPublicToken({
  scopes: {
    read: {
      runs: true,     // Can read run data
      tags: ["user:alice"], // Limited to specific tags
    },
  },
  expirationTime: "1h",
});

return Response.json({ token });
```

### Trigger + Subscribe Pattern

Trigger a task and subscribe in one operation:

```tsx
import { useRealtimeRunWithStreams } from "@trigger.dev/react-hooks";

function GenerateContent() {
  const [runId, setRunId] = useState<string | null>(null);

  const handleGenerate = async () => {
    const res = await fetch("/api/generate", { method: "POST" });
    const { runId } = await res.json();
    setRunId(runId);
  };

  return (
    <div>
      <button onClick={handleGenerate}>Generate</button>
      {runId && <StreamingOutput runId={runId} />}
    </div>
  );
}
```

## Common Patterns

### Progress Bar

```typescript
// In task
export const importTask = task({
  id: "import-data",
  run: async (payload) => {
    const items = await fetchItems(payload.sourceUrl);
    let processed = 0;

    for (const item of items) {
      await processItem(item);
      processed++;
      await metadata.set("progress", {
        processed,
        total: items.length,
        percent: Math.round((processed / items.length) * 100),
      });
    }

    return { total: processed };
  },
});
```

```tsx
// In React
function ImportProgress({ runId }: { runId: string }) {
  const { run } = useRealtimeRun(runId);
  const progress = run?.metadata?.progress;

  return progress ? (
    <div>
      <progress value={progress.percent} max={100} />
      <p>{progress.processed} / {progress.total}</p>
    </div>
  ) : (
    <p>Starting import...</p>
  );
}
```

### AI Chat with Streaming

```typescript
// In task
export const chatTask = task({
  id: "ai-chat",
  run: async (payload: { messages: Array<{ role: string; content: string }> }) => {
    const textStream = await streams.define<string>("chat-response");

    const response = await openai.chat.completions.create({
      model: "gpt-4o",
      messages: payload.messages,
      stream: true,
    });

    let fullResponse = "";
    for await (const chunk of response) {
      const content = chunk.choices[0]?.delta?.content ?? "";
      fullResponse += content;
      await textStream.write(content);
    }

    await textStream.close();
    return { response: fullResponse };
  },
});
```

```tsx
// In React
function ChatResponse({ runId }: { runId: string }) {
  const { data, isComplete } = useRealtimeStream<string>(runId, "chat-response");
  return (
    <div className="prose">
      <p>{data.join("")}</p>
      {!isComplete && <span className="animate-pulse">|</span>}
    </div>
  );
}
```

## Related Topics

- Writing tasks → `01-writing-tasks.md`
- Runs → `03-runs.md`
- Wait & tokens → `07-wait-and-human-in-loop.md`
