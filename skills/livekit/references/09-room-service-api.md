# Room Service API

> Source: [docs.livekit.io/reference/other/roomservice-api](https://docs.livekit.io/reference/other/roomservice-api/) — Server-side management

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Room Management](#room-management)
- [Participant Management](#participant-management)
- [Track Management](#track-management)
- [Data & Messaging](#data--messaging)
- [Metadata Updates](#metadata-updates)
- [Python SDK Examples](#python-sdk-examples)
- [Node.js SDK Examples](#nodejs-sdk-examples)
- [REST API Direct](#rest-api-direct)

---

## Overview

The Room Service API enables server-side management of rooms, participants, and tracks. It uses Twirp (protobuf-based RPC) over HTTP.

**Key characteristics:**
- All endpoints require Bearer token authentication
- Fully distributed across multiple nodes
- Accepts both `snake_case` and `camelCase` parameters
- Server SDKs handle auth automatically

## Authentication

All API calls require a Bearer token generated from your API key/secret:

```python
from livekit import api

# Python SDK handles auth automatically
lk_api = api.LiveKitAPI(
    url="https://your-project.livekit.cloud",
    api_key="your-api-key",
    api_secret="your-api-secret",
)
```

```javascript
// Node.js SDK
import { RoomServiceClient } from 'livekit-server-sdk';

const client = new RoomServiceClient(
  'https://your-project.livekit.cloud',
  'your-api-key',
  'your-api-secret'
);
```

## Room Management

### CreateRoom

```python
room = await lk_api.room.create_room(
    api.CreateRoomRequest(
        name="my-room",                  # Required, unique identifier
        empty_timeout=300,                # Close after 5 min empty
        departure_timeout=60,             # Close 60s after last participant
        max_participants=20,              # Hard cap
        metadata='{"type": "support"}',   # Arbitrary JSON
    )
)
print(f"Room created: {room.sid}")
```

**Permission required:** `roomCreate`

### ListRooms

```python
# List all active rooms
rooms = await lk_api.room.list_rooms(api.ListRoomsRequest())

# Filter by names
rooms = await lk_api.room.list_rooms(
    api.ListRoomsRequest(names=["room-1", "room-2"])
)

for room in rooms.rooms:
    print(f"{room.name}: {room.num_participants} participants")
```

**Permission required:** `roomList`

### DeleteRoom

```python
await lk_api.room.delete_room(
    api.DeleteRoomRequest(room="my-room")
)
# All participants are disconnected
```

**Permission required:** `roomCreate`

## Participant Management

### ListParticipants

```python
response = await lk_api.room.list_participants(
    api.ListParticipantsRequest(room="my-room")
)
for p in response.participants:
    print(f"{p.identity}: {p.state}")
```

### GetParticipant

```python
participant = await lk_api.room.get_participant(
    api.RoomParticipantIdentity(
        room="my-room",
        identity="user-123",
    )
)
print(f"Name: {participant.name}, Joined: {participant.joined_at}")
```

### RemoveParticipant

```python
await lk_api.room.remove_participant(
    api.RoomParticipantIdentity(
        room="my-room",
        identity="user-123",
    )
)
# On LiveKit Cloud, also revokes current tokens
```

### UpdateParticipant

```python
await lk_api.room.update_participant(
    api.UpdateParticipantRequest(
        room="my-room",
        identity="user-123",
        metadata='{"role": "premium"}',
        permission=api.ParticipantPermission(
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True,
        ),
    )
)
# Updates broadcast to all participants in the room
```

**Permission required:** `roomAdmin` for all participant operations.

## Track Management

### MutePublishedTrack

```python
await lk_api.room.mute_published_track(
    api.MuteRoomTrackRequest(
        room="my-room",
        identity="user-123",
        track_sid="TR_xxxxx",
        muted=True,
    )
)
```

**Note:** Remote unmuting is disabled by default for security. Enable via server config if needed.

### UpdateSubscriptions

```python
# Admin can subscribe a participant to specific tracks
await lk_api.room.update_subscriptions(
    api.UpdateSubscriptionsRequest(
        room="my-room",
        identity="user-123",
        track_sids=["TR_xxxxx", "TR_yyyyy"],
        subscribe=True,
    )
)
```

## Data & Messaging

### SendData

```python
import json

await lk_api.room.send_data(
    api.SendDataRequest(
        room="my-room",
        data=json.dumps({"type": "alert", "message": "System update"}).encode(),
        kind=api.DataPacketKind.RELIABLE,    # or LOSSY
        topic="system",                       # Optional topic filter
        destination_identities=["user-123"],  # Optional: specific recipients
    )
)
```

**Delivery modes:**
- `RELIABLE` — TCP-like, guaranteed delivery, ordered
- `LOSSY` — UDP-like, best-effort, lower latency

## Metadata Updates

### UpdateRoomMetadata

```python
await lk_api.room.update_room_metadata(
    api.UpdateRoomMetadataRequest(
        room="my-room",
        metadata='{"status": "active", "queue_position": 3}',
    )
)
# Broadcasts to all participants
```

## Python SDK Examples

```python
from livekit import api
import asyncio

async def main():
    lk_api = api.LiveKitAPI()

    # Create room
    room = await lk_api.room.create_room(
        api.CreateRoomRequest(name="demo-room", empty_timeout=600)
    )

    # Generate token for a participant
    token = (
        api.AccessToken()
        .with_identity("user-1")
        .with_grants(api.VideoGrants(
            room_join=True,
            room="demo-room",
            can_publish=True,
            can_subscribe=True,
        ))
        .to_jwt()
    )

    # List participants (after they've joined)
    participants = await lk_api.room.list_participants(
        api.ListParticipantsRequest(room="demo-room")
    )

    # Send a message
    await lk_api.room.send_data(
        api.SendDataRequest(
            room="demo-room",
            data=b'Hello from server!',
            kind=api.DataPacketKind.RELIABLE,
        )
    )

    # Clean up
    await lk_api.room.delete_room(
        api.DeleteRoomRequest(room="demo-room")
    )

asyncio.run(main())
```

## Node.js SDK Examples

```javascript
import { RoomServiceClient, AccessToken } from 'livekit-server-sdk';

const client = new RoomServiceClient(
  process.env.LIVEKIT_URL,
  process.env.LIVEKIT_API_KEY,
  process.env.LIVEKIT_API_SECRET
);

// Create room
const room = await client.createRoom({ name: 'demo-room', emptyTimeout: 600 });

// List rooms
const rooms = await client.listRooms();

// List participants
const participants = await client.listParticipants('demo-room');

// Remove participant
await client.removeParticipant('demo-room', 'user-123');

// Send data
const encoder = new TextEncoder();
await client.sendData(
  'demo-room',
  encoder.encode(JSON.stringify({ type: 'notification' })),
  DataPacket_Kind.RELIABLE
);

// Delete room
await client.deleteRoom('demo-room');
```

## REST API Direct

For languages without an SDK, use Twirp directly:

```bash
# Create room
curl -X POST "https://your-project.livekit.cloud/twirp/livekit.RoomService/CreateRoom" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-room", "empty_timeout": 300}'

# List rooms
curl -X POST "https://your-project.livekit.cloud/twirp/livekit.RoomService/ListRooms" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'

# Delete room
curl -X POST "https://your-project.livekit.cloud/twirp/livekit.RoomService/DeleteRoom" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"room": "my-room"}'
```

**Twirp endpoint pattern:** `POST /twirp/livekit.RoomService/<MethodName>`

### Data Models

**Room:** sid, name, empty_timeout, departure_timeout, max_participants, creation_time, turn_password, metadata, num_participants, active_recording

**ParticipantInfo:** sid, identity, name, state (JOINING/JOINED/ACTIVE/DISCONNECTED), tracks, metadata, joined_at, permission, is_publisher

**TrackInfo:** sid, type (AUDIO/VIDEO), source (CAMERA/MICROPHONE/SCREEN_SHARE), name, mime_type, muted, width, height, simulcast, codec
