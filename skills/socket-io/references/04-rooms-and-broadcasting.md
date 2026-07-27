# Socket.IO Rooms and Broadcasting

> Source: https://socket.io/docs/v4/rooms/

## Table of Contents

- [What Are Rooms?](#what-are-rooms)
- [Joining and Leaving](#joining-and-leaving)
- [Broadcasting to Rooms](#broadcasting-to-rooms)
- [Room Events](#room-events)
- [Adapter Internals](#adapter-internals)
- [Common Patterns](#common-patterns)

## What Are Rooms?

Rooms are arbitrary channels that sockets can join and leave. They exist only on the server — clients have no direct knowledge of room membership.

Key characteristics:
- **Server-side only** — clients cannot access room lists
- **Arbitrary strings** — any string works as a room name
- **Auto-joined** — each socket automatically joins a room named by its own `socket.id`
- **Auto-left** — sockets leave all rooms on disconnect
- **No creation step** — rooms are created implicitly on first join

## Joining and Leaving

### Basic Join/Leave

```javascript
io.on("connection", (socket) => {
  // Join a single room
  socket.join("general");

  // Join multiple rooms
  socket.join(["general", "announcements"]);

  // Leave a room
  socket.leave("general");

  // Check current rooms
  console.log(socket.rooms); // Set { "socket-id", "general", "announcements" }
});
```

### Dynamic Room Joining

```javascript
io.on("connection", (socket) => {
  // Join room based on user data
  socket.on("join:room", (roomName) => {
    socket.join(roomName);
    socket.to(roomName).emit("user:joined", {
      userId: socket.data.userId,
      room: roomName
    });
  });

  socket.on("leave:room", (roomName) => {
    socket.to(roomName).emit("user:left", {
      userId: socket.data.userId,
      room: roomName
    });
    socket.leave(roomName);
  });
});
```

### Server-Side Room Management

```javascript
// Make ALL sockets join a room
io.socketsJoin("maintenance-mode");

// Make sockets in "room1" also join "room2"
io.in("room1").socketsJoin("room2");

// Make ALL sockets leave a room
io.socketsLeave("maintenance-mode");

// Make sockets in "room1" leave "room2"
io.in("room1").socketsLeave("room2");

// Disconnect all sockets in a room
io.in("room1").disconnectSockets();
io.in("room1").disconnectSockets(true); // close underlying transport
```

## Broadcasting to Rooms

### Target Specific Rooms

```javascript
// Send to ALL in "room1" (including sender if in room)
io.to("room1").emit("event", data);
io.in("room1").emit("event", data); // alias

// Send to "room1" excluding sender
socket.to("room1").emit("event", data);

// Send to multiple rooms (union of members)
io.to("room1").to("room2").emit("event", data);
socket.to("room1").to("room2").emit("event", data);

// Send to "room1" but NOT "room2"
io.to("room1").except("room2").emit("event", data);
socket.to("room1").except("room2").emit("event", data);

// Send to ALL except "room1"
io.except("room1").emit("event", data);
socket.broadcast.except("room1").emit("event", data);
```

### Direct-to-Socket via Room

Every socket auto-joins a room matching its socket.id:

```javascript
// Send to a specific socket (private message)
io.to(targetSocketId).emit("private:message", { from: socket.id, text: msg });
```

### Fetch Sockets in a Room

```javascript
// Get all sockets in a room
const sockets = await io.in("room1").fetchSockets();

for (const s of sockets) {
  console.log(s.id);
  console.log(s.data);
  console.log(s.rooms);
  s.emit("hello");         // emit to individual socket
  s.join("another-room");  // server-side join
  s.leave("room1");
  s.disconnect();
}
```

### Count Sockets in a Room

```javascript
// Using adapter
const adapter = io.of("/").adapter;
const roomMembers = adapter.rooms.get("room1");
const count = roomMembers ? roomMembers.size : 0;

// Or using fetchSockets
const sockets = await io.in("room1").fetchSockets();
console.log(`${sockets.length} users in room1`);
```

## Room Events

Since Socket.IO v3.1.0, the adapter emits room lifecycle events:

```javascript
const adapter = io.of("/").adapter;

adapter.on("create-room", (room) => {
  console.log(`Room created: ${room}`);
});

adapter.on("delete-room", (room) => {
  console.log(`Room deleted: ${room}`);
});

adapter.on("join-room", (room, socketId) => {
  console.log(`Socket ${socketId} joined ${room}`);
});

adapter.on("leave-room", (room, socketId) => {
  console.log(`Socket ${socketId} left ${room}`);
});
```

## Adapter Internals

The adapter manages rooms using two ES6 Maps:

```
sids: Map<SocketId, Set<Room>>
  "abc123" → Set { "abc123", "general", "vip" }
  "def456" → Set { "def456", "general" }

rooms: Map<Room, Set<SocketId>>
  "abc123"  → Set { "abc123" }
  "def456"  → Set { "def456" }
  "general" → Set { "abc123", "def456" }
  "vip"     → Set { "abc123" }
```

When `socket.join("room")` is called, both maps are updated. Broadcasting to a room iterates the socket IDs in `rooms.get("room")`.

## Common Patterns

### User-Based Rooms (Multi-Device)

```javascript
io.on("connection", (socket) => {
  const userId = socket.handshake.auth.userId;

  // Join user-specific room (all devices of same user)
  socket.join(`user:${userId}`);

  // Notify across all user's devices
  io.to(`user:${userId}`).emit("notification", {
    text: "You have a new message"
  });
});
```

### Entity-Based Rooms

```javascript
io.on("connection", (socket) => {
  socket.on("subscribe:project", (projectId) => {
    socket.join(`project:${projectId}`);
  });

  socket.on("project:update", (projectId, data) => {
    // Notify all watchers except sender
    socket.to(`project:${projectId}`).emit("project:changed", data);
  });
});
```

### Chat Room with Presence

```javascript
io.on("connection", (socket) => {
  socket.on("chat:join", async (roomName) => {
    socket.join(roomName);
    socket.data.username = socket.handshake.auth.username;

    // Get current members
    const members = await io.in(roomName).fetchSockets();
    const usernames = members.map((s) => s.data.username);

    // Send member list to joining user
    socket.emit("chat:members", usernames);

    // Notify room of new member
    socket.to(roomName).emit("chat:user-joined", socket.data.username);
  });

  socket.on("disconnecting", () => {
    for (const room of socket.rooms) {
      if (room !== socket.id) {
        socket.to(room).emit("chat:user-left", socket.data.username);
      }
    }
  });
});
```

### Room-Based Access Control

```javascript
io.on("connection", (socket) => {
  socket.on("join:room", async (roomName) => {
    const hasAccess = await checkPermission(socket.data.userId, roomName);
    if (hasAccess) {
      socket.join(roomName);
      socket.emit("room:joined", roomName);
    } else {
      socket.emit("room:denied", roomName);
    }
  });
});
```

### Private Messaging

```javascript
io.on("connection", (socket) => {
  socket.on("dm:send", (targetUserId, message) => {
    // Use the user-based room pattern
    io.to(`user:${targetUserId}`).emit("dm:receive", {
      from: socket.data.userId,
      message,
      timestamp: Date.now()
    });
  });
});
```
