# Supabase — Realtime

> Source: https://supabase.com/docs/guides/realtime

## Table of Contents

- [Overview](#overview)
- [Channel Basics](#channel-basics)
- [Broadcast](#broadcast)
- [Presence](#presence)
- [Postgres Changes](#postgres-changes)
- [Private Channels](#private-channels)
- [Connection Management](#connection-management)
- [Common Pitfalls](#common-pitfalls)

## Overview

Supabase Realtime enables live data synchronization through WebSockets. It provides three features:

| Feature | Purpose | Use Case |
|---------|---------|----------|
| **Broadcast** | Low-latency messaging between clients | Chat, cursor tracking, game events, notifications |
| **Presence** | Track and sync online user state | "Who's online", typing indicators, active users |
| **Postgres Changes** | Listen to database INSERT/UPDATE/DELETE | Live dashboards, order tracking, activity feeds |

## Channel Basics

All Realtime features use **channels**. A channel is a named topic that clients subscribe to:

```typescript
const channel = supabase.channel('room-1')

channel.subscribe((status) => {
  if (status === 'SUBSCRIBED') {
    console.log('Connected to room-1')
  }
})

// Clean up when done
supabase.removeChannel(channel)

// Or remove all channels
supabase.removeAllChannels()
```

## Broadcast

Send ephemeral messages between connected clients in real-time.

### Subscribe to Messages

```typescript
const channel = supabase.channel('chat-room')

channel
  .on('broadcast', { event: 'message' }, (payload) => {
    console.log('Received:', payload.payload)
    // { user: 'Alice', text: 'Hello!' }
  })
  .subscribe()

// Listen to ALL broadcast events
channel
  .on('broadcast', { event: '*' }, (payload) => {
    console.log('Event:', payload.event, payload.payload)
  })
  .subscribe()
```

### Send Messages

```typescript
// Send via WebSocket (after subscription)
channel.send({
  type: 'broadcast',
  event: 'message',
  payload: { user: 'Alice', text: 'Hello!' },
})

// Send via HTTP (before or without subscription)
await channel.send({
  type: 'broadcast',
  event: 'message',
  payload: { user: 'Alice', text: 'Hello!' },
})
```

### Configuration Options

```typescript
const channel = supabase.channel('room', {
  config: {
    broadcast: {
      self: true,   // Receive your own messages (default: false)
      ack: true,    // Wait for server acknowledgment (default: false)
    },
  },
})
```

### Broadcast from Database

Trigger broadcasts from SQL (stored in `realtime.messages` for 3 days):

```sql
select realtime.send(
  jsonb_build_object('message', 'Hello from the database!'),
  'new-message',     -- event name
  'chat-room',       -- channel/topic
  false              -- private channel?
);
```

### Broadcast via REST API

```bash
curl -X POST 'https://<ref>.supabase.co/realtime/v1/api/broadcast' \
  -H 'apikey: <anon-key>' \
  -H 'Content-Type: application/json' \
  -d '{
    "messages": [{
      "topic": "chat-room",
      "event": "message",
      "payload": { "text": "Hello via REST" }
    }]
  }'
```

## Presence

Track which users are online and synchronize shared state.

### Track User State

```typescript
const channel = supabase.channel('online-users')

channel
  .on('presence', { event: 'sync' }, () => {
    const state = channel.presenceState()
    console.log('Online users:', state)
  })
  .on('presence', { event: 'join' }, ({ key, newPresences }) => {
    console.log('User joined:', newPresences)
  })
  .on('presence', { event: 'leave' }, ({ key, leftPresences }) => {
    console.log('User left:', leftPresences)
  })
  .subscribe(async (status) => {
    if (status === 'SUBSCRIBED') {
      await channel.track({
        user_id: currentUser.id,
        username: currentUser.name,
        online_at: new Date().toISOString(),
      })
    }
  })
```

### Update Presence State

```typescript
await channel.track({
  user_id: currentUser.id,
  username: currentUser.name,
  status: 'typing',  // Updated state
})
```

### Untrack (Go Offline)

```typescript
await channel.untrack()
```

### Reading Presence State

```typescript
const state = channel.presenceState()
// Returns: { '<user-key>': [{ user_id: '...', username: '...', ... }] }

// Count online users
const onlineCount = Object.keys(state).length
```

## Postgres Changes

Listen to database changes in real-time via logical replication.

### Subscribe to All Changes on a Table

```typescript
const channel = supabase.channel('db-changes')

channel
  .on(
    'postgres_changes',
    { event: '*', schema: 'public', table: 'todos' },
    (payload) => {
      console.log('Change:', payload.eventType)  // INSERT, UPDATE, DELETE
      console.log('New:', payload.new)
      console.log('Old:', payload.old)
    }
  )
  .subscribe()
```

### Filter by Event Type

```typescript
// Only INSERTs
channel.on(
  'postgres_changes',
  { event: 'INSERT', schema: 'public', table: 'messages' },
  (payload) => console.log('New message:', payload.new)
)

// Only UPDATEs
channel.on(
  'postgres_changes',
  { event: 'UPDATE', schema: 'public', table: 'orders' },
  (payload) => {
    console.log('Before:', payload.old)
    console.log('After:', payload.new)
  }
)

// Only DELETEs
channel.on(
  'postgres_changes',
  { event: 'DELETE', schema: 'public', table: 'todos' },
  (payload) => console.log('Deleted:', payload.old)
)
```

### Filter by Column Value

```typescript
// Only changes where user_id matches
channel.on(
  'postgres_changes',
  {
    event: '*',
    schema: 'public',
    table: 'todos',
    filter: 'user_id=eq.550e8400-e29b-41d4-a716-446655440000',
  },
  (payload) => console.log('My todo changed:', payload)
)

// Filter operators: eq, neq, gt, gte, lt, lte, in
// IN filter example
channel.on(
  'postgres_changes',
  {
    event: 'INSERT',
    schema: 'public',
    table: 'orders',
    filter: 'status=in.(pending,processing)',
  },
  (payload) => console.log('New order:', payload.new)
)
```

### Enabling Postgres Changes

You must enable replication for each table:

```sql
-- Via Supabase Dashboard: Database → Replication → Enable for specific tables
-- Or via SQL:
alter publication supabase_realtime add table todos;
alter publication supabase_realtime add table messages;
```

### Full Row Data on DELETE

By default, DELETE only returns the row ID. To get full row data:

```sql
alter table todos replica identity full;
```

## Private Channels

Secure channels that require authentication:

```typescript
const channel = supabase.channel('private-room', {
  config: { private: true },
})
```

Private channels verify the user's JWT and can enforce RLS policies.

## Connection Management

```typescript
// Check connection state
const states = supabase.getChannels()

// Handle reconnection
channel.subscribe((status, err) => {
  if (status === 'SUBSCRIBED') {
    console.log('Connected')
  } else if (status === 'CHANNEL_ERROR') {
    console.error('Error:', err)
  } else if (status === 'TIMED_OUT') {
    console.log('Reconnecting...')
  }
})
```

## Common Pitfalls

1. **Forgetting to enable replication** — Postgres Changes won't work until you add the table to `supabase_realtime` publication.
2. **Not cleaning up channels** — Always call `removeChannel()` or `removeAllChannels()` when components unmount to prevent memory leaks.
3. **Expecting DELETE to have full row data** — By default, DELETE events only include the primary key. Set `replica identity full` to get all columns.
4. **Using Postgres Changes for high-frequency updates** — Postgres Changes goes through the WAL (Write-Ahead Log). For high-frequency data (cursor positions, game state), use Broadcast instead.
5. **Not handling reconnection** — WebSocket connections can drop. The client auto-reconnects, but you should handle the `CHANNEL_ERROR` and `TIMED_OUT` states gracefully.
6. **Subscribing without waiting for SUBSCRIBED** — Sending broadcast messages before the channel is subscribed sends them via HTTP instead of WebSocket, which has higher latency.
