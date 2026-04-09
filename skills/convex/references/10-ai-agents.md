# AI & Agents

> Source: [docs.convex.dev/ai](https://docs.convex.dev/ai) | convex v1.34.x

## Table of Contents

- [Why Convex for AI](#why-convex-for-ai)
- [LLM Integration Pattern](#llm-integration-pattern)
- [Streaming Responses](#streaming-responses)
- [Tool Calling](#tool-calling)
- [Agent Pattern](#agent-pattern)
- [RAG with Vector Search](#rag-with-vector-search)
- [Conversation Threading](#conversation-threading)
- [AI Components](#ai-components)

## Why Convex for AI

Convex is well-suited for AI applications because:

- **Real-time UI updates** — Streaming LLM responses update all connected clients instantly
- **Durable execution** — Long-running agent workflows survive server restarts
- **Built-in vector search** — No separate vector DB needed for RAG
- **Scheduler** — Chain multi-step agent workflows with retries
- **ACID transactions** — Safely update conversation state and tool results

## LLM Integration Pattern

The standard pattern: mutation captures user intent, action calls the LLM:

```typescript
// convex/chat.ts
import { mutation, internalAction } from "./_generated/server";
import { internal } from "./_generated/api";
import { v } from "convex/values";

// Step 1: User sends message (mutation — instant, transactional)
export const sendMessage = mutation({
  args: { conversationId: v.id("conversations"), body: v.string() },
  handler: async (ctx, args) => {
    // Store user message
    await ctx.db.insert("messages", {
      conversationId: args.conversationId,
      role: "user",
      body: args.body,
    });

    // Create placeholder for assistant response
    const assistantMsgId = await ctx.db.insert("messages", {
      conversationId: args.conversationId,
      role: "assistant",
      body: "",
      status: "generating",
    });

    // Schedule LLM call
    await ctx.scheduler.runAfter(0, internal.chat.generateResponse, {
      conversationId: args.conversationId,
      assistantMsgId,
    });
  },
});

// Step 2: Generate response (action — calls external API)
export const generateResponse = internalAction({
  args: {
    conversationId: v.id("conversations"),
    assistantMsgId: v.id("messages"),
  },
  handler: async (ctx, args) => {
    // Load conversation history
    const messages = await ctx.runQuery(internal.chat.getHistory, {
      conversationId: args.conversationId,
    });

    // Call LLM
    const response = await openai.chat.completions.create({
      model: "gpt-4o",
      messages: messages.map((m) => ({
        role: m.role as "user" | "assistant",
        content: m.body,
      })),
    });

    const content = response.choices[0].message.content || "";

    // Update the placeholder message
    await ctx.runMutation(internal.chat.updateMessage, {
      messageId: args.assistantMsgId,
      body: content,
      status: "complete",
    });
  },
});
```

## Streaming Responses

Stream LLM tokens to the database for real-time client updates:

```typescript
export const generateStreaming = internalAction({
  args: {
    conversationId: v.id("conversations"),
    assistantMsgId: v.id("messages"),
  },
  handler: async (ctx, args) => {
    const messages = await ctx.runQuery(internal.chat.getHistory, {
      conversationId: args.conversationId,
    });

    const stream = await openai.chat.completions.create({
      model: "gpt-4o",
      messages: messages.map((m) => ({
        role: m.role as "user" | "assistant",
        content: m.body,
      })),
      stream: true,
    });

    let fullContent = "";
    let lastUpdate = 0;

    for await (const chunk of stream) {
      const delta = chunk.choices[0]?.delta?.content || "";
      fullContent += delta;

      // Batch updates (every 100ms) to avoid excessive writes
      if (Date.now() - lastUpdate > 100) {
        await ctx.runMutation(internal.chat.updateMessage, {
          messageId: args.assistantMsgId,
          body: fullContent,
          status: "generating",
        });
        lastUpdate = Date.now();
      }
    }

    // Final update
    await ctx.runMutation(internal.chat.updateMessage, {
      messageId: args.assistantMsgId,
      body: fullContent,
      status: "complete",
    });
  },
});
```

The client subscribes with `useQuery` — the message body updates automatically as tokens stream in.

## Tool Calling

Implement LLM tool calling with Convex:

```typescript
const tools = [
  {
    type: "function" as const,
    function: {
      name: "search_documents",
      description: "Search the knowledge base",
      parameters: {
        type: "object",
        properties: {
          query: { type: "string", description: "Search query" },
        },
        required: ["query"],
      },
    },
  },
  {
    type: "function" as const,
    function: {
      name: "create_task",
      description: "Create a new task",
      parameters: {
        type: "object",
        properties: {
          title: { type: "string" },
          priority: { type: "string", enum: ["low", "medium", "high"] },
        },
        required: ["title"],
      },
    },
  },
];

export const agentStep = internalAction({
  args: { conversationId: v.id("conversations"), messageId: v.id("messages") },
  handler: async (ctx, args) => {
    const history = await ctx.runQuery(internal.chat.getHistory, {
      conversationId: args.conversationId,
    });

    const response = await openai.chat.completions.create({
      model: "gpt-4o",
      messages: history,
      tools,
    });

    const message = response.choices[0].message;

    if (message.tool_calls) {
      for (const toolCall of message.tool_calls) {
        const toolArgs = JSON.parse(toolCall.function.arguments);
        let result: string;

        switch (toolCall.function.name) {
          case "search_documents":
            const docs = await ctx.runQuery(internal.search.query, {
              query: toolArgs.query,
            });
            result = JSON.stringify(docs);
            break;
          case "create_task":
            const taskId = await ctx.runMutation(internal.tasks.create, {
              title: toolArgs.title,
              priority: toolArgs.priority || "medium",
            });
            result = `Created task: ${taskId}`;
            break;
          default:
            result = "Unknown tool";
        }

        // Store tool result and continue the loop
        await ctx.runMutation(internal.chat.addToolResult, {
          conversationId: args.conversationId,
          toolCallId: toolCall.id,
          result,
        });
      }

      // Continue agent loop
      await ctx.scheduler.runAfter(0, internal.chat.agentStep, {
        conversationId: args.conversationId,
        messageId: args.messageId,
      });
    } else {
      // Final text response
      await ctx.runMutation(internal.chat.updateMessage, {
        messageId: args.messageId,
        body: message.content || "",
        status: "complete",
      });
    }
  },
});
```

## Agent Pattern

Multi-step agent with durable execution:

```typescript
// convex/agent.ts
export const runAgent = internalAction({
  args: { taskId: v.id("agent_tasks") },
  handler: async (ctx, args) => {
    const task = await ctx.runQuery(internal.agent.getTask, {
      taskId: args.taskId,
    });

    // Update status
    await ctx.runMutation(internal.agent.updateStatus, {
      taskId: args.taskId,
      status: "running",
      step: task.currentStep,
    });

    try {
      // Execute current step
      const result = await executeStep(ctx, task);

      if (result.nextStep) {
        // More steps to go — schedule next step
        await ctx.runMutation(internal.agent.saveStepResult, {
          taskId: args.taskId,
          step: task.currentStep,
          result: result.data,
          nextStep: result.nextStep,
        });

        await ctx.scheduler.runAfter(0, internal.agent.runAgent, {
          taskId: args.taskId,
        });
      } else {
        // Agent complete
        await ctx.runMutation(internal.agent.markComplete, {
          taskId: args.taskId,
          finalResult: result.data,
        });
      }
    } catch (error) {
      await ctx.runMutation(internal.agent.markFailed, {
        taskId: args.taskId,
        error: String(error),
      });
    }
  },
});
```

## RAG with Vector Search

See `08-search.md` for the full vector search reference. The key pattern:

```typescript
export const answerWithContext = action({
  args: { question: v.string() },
  handler: async (ctx, args) => {
    // 1. Embed the question
    const embedding = await generateEmbedding(args.question);

    // 2. Find relevant chunks
    const results = await ctx.vectorSearch("chunks", "by_embedding", {
      vector: embedding,
      limit: 5,
    });

    // 3. Load chunk content
    const chunks = await ctx.runQuery(internal.chunks.getByIds, {
      ids: results.map((r) => r._id),
    });

    // 4. Generate answer with context
    const context = chunks.filter(Boolean).map((c) => c!.text).join("\n---\n");

    const response = await openai.chat.completions.create({
      model: "gpt-4o",
      messages: [
        { role: "system", content: `Answer using this context:\n${context}` },
        { role: "user", content: args.question },
      ],
    });

    return response.choices[0].message.content;
  },
});
```

## Conversation Threading

Store conversation history with Convex's reactive queries:

```typescript
// Schema
conversations: defineTable({
  title: v.optional(v.string()),
  userId: v.id("users"),
  model: v.string(),
}).index("by_user", ["userId"]),

chatMessages: defineTable({
  conversationId: v.id("conversations"),
  role: v.union(v.literal("user"), v.literal("assistant"), v.literal("system")),
  content: v.string(),
  status: v.optional(v.union(v.literal("generating"), v.literal("complete"))),
  tokenCount: v.optional(v.number()),
}).index("by_conversation", ["conversationId"]),
```

```tsx
// Client: messages update in real-time as they stream
function ChatThread({ conversationId }) {
  const messages = useQuery(api.chat.listMessages, { conversationId });

  return messages?.map((msg) => (
    <div key={msg._id} className={msg.role}>
      {msg.content}
      {msg.status === "generating" && <TypingIndicator />}
    </div>
  ));
}
```

## AI Components

Convex offers pre-built components for common AI patterns:

- **@convex-dev/agent** — Full-featured AI agent framework with threads, tool use, and memory
- **Action Cache** — Cache expensive LLM calls
- **Workpool** — Priority queue for AI task processing
- **Workflow** — Durable multi-step agent execution with suspension and retry

## Related References

- Vector search details: `08-search.md`
- Actions: `02-functions-actions-http.md`
- Scheduling (for agent loops): `07-scheduling.md`
- React client (for streaming UI): `09-react-client.md`
