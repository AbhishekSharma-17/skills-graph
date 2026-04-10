# useChat Hook

> Source: https://ai-sdk.dev/docs/ai-sdk-ui/chatbot

## Overview

The `useChat` hook from `@ai-sdk/react` provides complete state management for chat interfaces — messages, streaming status, input handling, error recovery, and transport configuration. It connects to server-side `streamText` via configurable transports.

## Basic Setup

### Client Component

```typescript
'use client';
import { useChat } from '@ai-sdk/react';
import { DefaultChatTransport } from 'ai';
import { useState } from 'react';

export default function Chat() {
  const { messages, sendMessage, status } = useChat({
    transport: new DefaultChatTransport({ api: '/api/chat' }),
  });
  const [input, setInput] = useState('');

  return (
    <div>
      {messages.map(m => (
        <div key={m.id}>
          <strong>{m.role}:</strong>
          {m.parts.map((part, i) => {
            if (part.type === 'text') return <span key={i}>{part.text}</span>;
            if (part.type === 'reasoning') return <em key={i}>{part.text}</em>;
            return null;
          })}
        </div>
      ))}

      <form onSubmit={e => {
        e.preventDefault();
        if (input.trim()) {
          sendMessage({ text: input });
          setInput('');
        }
      }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          disabled={status !== 'ready'}
          placeholder="Type a message..."
        />
        <button type="submit" disabled={status !== 'ready'}>Send</button>
      </form>
    </div>
  );
}
```

### Server Route (Next.js)

```typescript
// app/api/chat/route.ts
import { streamText, UIMessage, convertToModelMessages } from 'ai';

export const maxDuration = 30;

export async function POST(req: Request) {
  const { messages }: { messages: UIMessage[] } = await req.json();

  const result = streamText({
    model: 'anthropic/claude-sonnet-4.5',
    system: 'You are a helpful assistant.',
    messages: await convertToModelMessages(messages),
  });

  return result.toUIMessageStreamResponse();
}
```

## Status Management

| Status | Meaning | UI Action |
|--------|---------|-----------|
| `ready` | Idle, accepting input | Enable send button |
| `submitted` | Request sent, awaiting stream start | Show spinner |
| `streaming` | Actively receiving chunks | Show stop button |
| `error` | Request failed | Show retry button |

```typescript
const { status, stop, regenerate } = useChat({ /* ... */ });

// Loading indicator
{(status === 'submitted' || status === 'streaming') && <Spinner />}

// Stop button
{status === 'streaming' && (
  <button onClick={stop}>Stop</button>
)}

// Retry on error
{status === 'error' && (
  <button onClick={regenerate}>Retry</button>
)}
```

## Message Parts

Messages contain typed parts for rich rendering:

```typescript
interface UIMessage {
  id: string;
  role: 'user' | 'assistant';
  parts: Array<
    | { type: 'text'; text: string }
    | { type: 'reasoning'; text: string }
    | { type: 'tool-invocation'; toolName: string; args: unknown; result?: unknown; state: string }
    | { type: 'source-url'; url: string; title?: string }
    | { type: 'source-document'; id: string; title?: string }
    | { type: 'file'; url: string; mediaType: string; filename?: string }
  >;
  metadata?: Record<string, unknown>;
}
```

### Rendering Parts

```typescript
{messages.map(m => (
  <div key={m.id}>
    {m.parts.map((part, i) => {
      switch (part.type) {
        case 'text':
          return <Markdown key={i}>{part.text}</Markdown>;
        case 'reasoning':
          return <details key={i}><summary>Thinking...</summary>{part.text}</details>;
        case 'tool-invocation':
          return <ToolCard key={i} name={part.toolName} state={part.state} result={part.result} />;
        case 'file':
          if (part.mediaType.startsWith('image/'))
            return <img key={i} src={part.url} alt={part.filename} />;
          return null;
        case 'source-url':
          return <a key={i} href={part.url}>{part.title}</a>;
        default:
          return null;
      }
    })}
  </div>
))}
```

## Transport Configuration

### DefaultChatTransport

```typescript
const { messages, sendMessage } = useChat({
  transport: new DefaultChatTransport({
    api: '/api/chat',
    headers: { Authorization: `Bearer ${token}` },
    body: { userId: currentUser.id },
    credentials: 'include',
  }),
});
```

### Dynamic Headers/Body

```typescript
transport: new DefaultChatTransport({
  api: '/api/chat',
  headers: () => ({
    Authorization: `Bearer ${getLatestToken()}`,
  }),
  body: () => ({
    sessionId: getCurrentSession(),
  }),
}),
```

### DirectChatTransport (Server-Side)

Skip HTTP — connect directly to an agent:

```typescript
import { DirectChatTransport, ToolLoopAgent } from 'ai';

const agent = new ToolLoopAgent({
  model: 'anthropic/claude-sonnet-4.5',
  tools: { /* ... */ },
});

const { messages, sendMessage } = useChat({
  transport: new DirectChatTransport({ agent }),
});
```

### TextStreamChatTransport

For simple text-only streams:

```typescript
import { TextStreamChatTransport } from 'ai';

const { messages } = useChat({
  transport: new TextStreamChatTransport({ api: '/api/chat' }),
});
```

## Sending Messages

### Basic Text

```typescript
sendMessage({ text: 'Hello!' });
```

### With Files

```typescript
sendMessage({
  text: 'What is in this image?',
  files: fileInputRef.current.files, // FileList from <input type="file">
});
```

### With File Objects

```typescript
sendMessage({
  text: 'Analyze these',
  files: [
    { type: 'file', url: 'https://example.com/photo.jpg', mediaType: 'image/jpeg' },
    { type: 'file', url: 'data:image/png;base64,...', mediaType: 'image/png' },
  ],
});
```

### With Request Options

```typescript
sendMessage(
  { text: input },
  {
    headers: { 'X-Custom': 'value' },
    body: { temperature: 0.9, model: 'gpt-5.2' },
    metadata: { userId: '123', sessionId: 'abc' },
  }
);
```

## Message Manipulation

```typescript
const { messages, setMessages } = useChat({ /* ... */ });

// Delete a message
const handleDelete = (id: string) => {
  setMessages(msgs => msgs.filter(m => m.id !== id));
};

// Edit a message (remove it and everything after, then re-send)
const handleEdit = (id: string, newText: string) => {
  const idx = messages.findIndex(m => m.id === id);
  setMessages(msgs => msgs.slice(0, idx));
  sendMessage({ text: newText });
};
```

## Event Callbacks

```typescript
const { messages, sendMessage } = useChat({
  transport: new DefaultChatTransport({ api: '/api/chat' }),
  onFinish: ({ message, messages, isAbort, isDisconnect, isError }) => {
    if (!isError && !isAbort) {
      saveToHistory(messages);
    }
  },
  onError: (error) => {
    toast.error('Failed to get response');
    console.error(error);
  },
  onData: (data) => {
    // Receive custom data parts from server
    if (data.progress) updateProgressBar(data.progress);
  },
});
```

## Message Metadata

### Server-Side

```typescript
return result.toUIMessageStreamResponse({
  messageMetadata: ({ part }) => {
    if (part.type === 'start') {
      return { createdAt: Date.now(), model: 'claude-sonnet-4.5' };
    }
    if (part.type === 'finish') {
      return { totalTokens: part.totalUsage.totalTokens };
    }
  },
});
```

### Client-Side

```typescript
{messages.map(m => (
  <div key={m.id}>
    {m.metadata?.model && <Badge>{m.metadata.model}</Badge>}
    {m.parts.map(/* ... */)}
    {m.metadata?.totalTokens && (
      <span className="text-xs">{m.metadata.totalTokens} tokens</span>
    )}
  </div>
))}
```

## Tool Invocation UI

Handle tool calls with approval in the UI:

```typescript
{m.parts.map((part, i) => {
  if (part.type === 'tool-invocation') {
    switch (part.state) {
      case 'partial-call':
        return <div key={i}>Calling {part.toolName}...</div>;
      case 'call':
        return <div key={i}>{part.toolName}({JSON.stringify(part.args)})</div>;
      case 'requires-approval':
        return (
          <div key={i}>
            <p>Approve {part.toolName}?</p>
            <button onClick={() => approveToolCall(part)}>Approve</button>
            <button onClick={() => denyToolCall(part)}>Deny</button>
          </div>
        );
      case 'result':
        return <div key={i}>Result: {JSON.stringify(part.result)}</div>;
    }
  }
})}
```

## Throttling Updates

Reduce React re-renders during fast streaming:

```typescript
const { messages } = useChat({
  transport: new DefaultChatTransport({ api: '/api/chat' }),
  experimental_throttle: 50, // Max one update per 50ms
});
```

## Multiple Chat Instances

```typescript
// Separate chat instances on same page
const chat1 = useChat({
  id: 'general-chat',
  transport: new DefaultChatTransport({ api: '/api/chat' }),
});

const chat2 = useChat({
  id: 'code-chat',
  transport: new DefaultChatTransport({ api: '/api/code-chat' }),
});
```

## Initial Messages

```typescript
const { messages } = useChat({
  transport: new DefaultChatTransport({ api: '/api/chat' }),
  initialMessages: [
    { id: '1', role: 'assistant', parts: [{ type: 'text', text: 'Hello! How can I help?' }] },
  ],
});
```

## Common Pitfalls

1. **Missing 'use client'** — useChat is a client hook; component must be a Client Component
2. **Wrong transport** — `DefaultChatTransport` expects `toUIMessageStreamResponse()` on server
3. **Stale closures** — Use callback form of `setMessages` for correct state
4. **No maxDuration** — Serverless functions timeout; set `export const maxDuration = 30`
5. **Missing convertToModelMessages** — UIMessages must be converted before passing to `streamText`
6. **Status not checked** — Always disable input when `status !== 'ready'`

## Related Topics

- Streaming → [06-streaming-patterns](06-streaming-patterns.md)
- Tools → [04-tool-calling](04-tool-calling.md)
- Deployment → [12-deployment-patterns](12-deployment-patterns.md)
