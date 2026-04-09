# Convex — Overview & Quickstart

> Source: [docs.convex.dev](https://docs.convex.dev) | convex v1.34.x

## What is Convex?

Convex is a reactive backend platform that replaces your database, server functions, file storage, scheduling, and search infrastructure with a single, fully managed service. Everything is TypeScript-first with end-to-end type safety — from schema definition to client-side hooks.

### Core Value Proposition

- **Real-time by default** — Queries automatically subscribe to data changes; connected clients update instantly
- **ACID transactions** — All mutations run in serializable transactions with automatic conflict resolution
- **Zero infrastructure** — No servers, no connection strings, no ORMs, no migration scripts
- **TypeScript end-to-end** — Schema types flow from backend to frontend with no code generation gaps
- **Deterministic functions** — Queries and mutations run in a sandboxed environment for automatic caching and retries

## Architecture

```
┌─────────────────────────────────────────────┐
│                  Client App                  │
│  (React, Next.js, Vue, Svelte, Node, etc.)  │
│                                              │
│  useQuery()  useMutation()  useAction()      │
└──────────────────┬──────────────────────────┘
                   │ WebSocket (real-time sync)
                   ▼
┌─────────────────────────────────────────────┐
│              Convex Platform                 │
│                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │ Queries  │ │Mutations │ │ Actions  │    │
│  │(read,    │ │(write,   │ │(side     │    │
│  │ cached,  │ │ ACID)    │ │ effects) │    │
│  │ reactive)│ │          │ │          │    │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘    │
│       │            │            │           │
│  ┌────┴────────────┴────┐  ┌───┴────────┐  │
│  │     Database          │  │ External   │  │
│  │  (Document store,     │  │ APIs       │  │
│  │   indexes, search)    │  │ (Stripe,   │  │
│  ├───────────────────────┤  │  OpenAI,   │  │
│  │  File Storage         │  │  etc.)     │  │
│  ├───────────────────────┤  └────────────┘  │
│  │  Scheduler            │                  │
│  └───────────────────────┘                  │
└─────────────────────────────────────────────┘
```

## Three Function Types

| | Queries | Mutations | Actions |
|---|---------|-----------|---------|
| **Database access** | Read only | Read + write | Via runQuery/runMutation |
| **Transactions** | Yes | Yes | No |
| **Caching** | Automatic | No | No |
| **Real-time** | Yes (subscriptions) | No | No |
| **Side effects** | Not allowed | Not allowed | Allowed (fetch, APIs) |
| **Retries** | Automatic | Automatic | Manual |

## Installation

### New Project

```bash
npm create convex@latest
```

This scaffolds a project with the `convex/` directory, schema, and sample functions.

### Add to Existing Project

```bash
npm install convex

# Initialize Convex in your project
npx convex init
```

### Project Structure

```
my-app/
├── convex/                    # Backend code (deployed to Convex)
│   ├── _generated/            # Auto-generated types and API references
│   │   ├── api.d.ts           # Typed API for all your functions
│   │   ├── dataModel.d.ts     # Types from your schema
│   │   └── server.d.ts        # Typed query/mutation/action constructors
│   ├── schema.ts              # Database schema definition
│   ├── messages.ts            # Example: message functions
│   ├── users.ts               # Example: user functions
│   └── http.ts                # HTTP endpoint routes
├── src/                       # Frontend code
│   └── App.tsx
├── convex.json                # Convex project config (auto-created)
└── package.json
```

### Development Workflow

```bash
# Start the Convex dev server (watches for changes, syncs to cloud)
npx convex dev

# In a separate terminal, start your frontend
npm run dev
```

`npx convex dev` watches your `convex/` directory, pushes function and schema changes to your development deployment, and generates TypeScript types in `convex/_generated/`.

## Quickstart: Chat App

### 1. Define the Schema

```typescript
// convex/schema.ts
import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  messages: defineTable({
    author: v.string(),
    body: v.string(),
  }),
});
```

### 2. Write Backend Functions

```typescript
// convex/messages.ts
import { query, mutation } from "./_generated/server";
import { v } from "convex/values";

// Query: read messages (real-time, cached)
export const list = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("messages").order("desc").take(50);
  },
});

// Mutation: send a message (transactional)
export const send = mutation({
  args: { author: v.string(), body: v.string() },
  handler: async (ctx, args) => {
    await ctx.db.insert("messages", {
      author: args.author,
      body: args.body,
    });
  },
});
```

### 3. Connect the Frontend

```tsx
// src/App.tsx
import { ConvexProvider, ConvexReactClient } from "convex/react";
import { useQuery, useMutation } from "convex/react";
import { api } from "../convex/_generated/api";

const convex = new ConvexReactClient(import.meta.env.VITE_CONVEX_URL);

function App() {
  return (
    <ConvexProvider client={convex}>
      <Chat />
    </ConvexProvider>
  );
}

function Chat() {
  const messages = useQuery(api.messages.list);
  const sendMessage = useMutation(api.messages.send);

  return (
    <div>
      {messages?.map((msg) => (
        <p key={msg._id}>{msg.author}: {msg.body}</p>
      ))}
      <button onClick={() => sendMessage({ author: "Alice", body: "Hello!" })}>
        Send
      </button>
    </div>
  );
}
```

## Supported Frameworks

| Framework | Client Library | Status |
|-----------|---------------|--------|
| React | `convex/react` | First-class |
| Next.js | `convex/react` + SSR helpers | First-class |
| Vue | `@convex-vue/core` | Community |
| Svelte | `convex/svelte` | Official |
| React Native | `convex/react` | First-class |
| Node.js | `convex/server` | Official |
| Python | `convex` (PyPI) | Official |
| Rust | `convex` (crates.io) | Official |
| iOS (Swift) | `ConvexMobile` | Official |
| Android (Kotlin) | `dev.convex:android-client` | Official |

## Key Concepts

- **Deployment** — A Convex project instance (dev or prod) with its own database, functions, and URL
- **Document** — A JSON-like object stored in a table (like a row, but nested/flexible)
- **Table** — A collection of documents (created implicitly on first insert, or defined in schema)
- **System tables** — Built-in tables prefixed with `_` (e.g., `_scheduled_functions`, `_storage`)
- **Generated API** — Type-safe `api` and `internal` objects auto-generated from your function exports

## Environment Variables

```bash
# Set environment variables for your deployment
npx convex env set MY_API_KEY sk-123456

# List all environment variables
npx convex env list

# Access in functions
const key = process.env.MY_API_KEY;
```

## CLI Quick Reference

```bash
npx convex dev          # Start dev server (watch mode)
npx convex deploy       # Deploy to production
npx convex init         # Initialize a new project
npx convex env set K V  # Set environment variable
npx convex env list     # List environment variables
npx convex import       # Import data from file
npx convex export       # Export data to file
npx convex logs         # View function logs
npx convex dashboard    # Open dashboard in browser
```

## Related References

- Functions: `01-functions-queries-mutations.md`, `02-functions-actions-http.md`
- Database: `03-database-schemas.md`, `04-indexes-performance.md`
- Features: `05-authentication.md` through `08-search.md`
- Client: `09-react-client.md`
- Patterns: `11-best-practices.md`
