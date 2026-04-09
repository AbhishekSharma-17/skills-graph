# LiveKit Core Concepts

> Source: [docs.livekit.io](https://docs.livekit.io) — Rooms, Participants, Tracks, Tokens, WebRTC

## Table of Contents

- [Rooms](#rooms)
- [Participants](#participants)
- [Tracks](#tracks)
- [Access Tokens](#access-tokens)
- [Connecting to LiveKit](#connecting-to-livekit)
- [WebRTC Transport](#webrtc-transport)
- [Data Channels](#data-channels)
- [Connection Resilience](#connection-resilience)
- [Permissions Model](#permissions-model)

---

## Rooms

Rooms are virtual spaces where participants connect and share media. Every LiveKit session happens inside a room.

```python
# Server-side room creation (Python SDK)
from livekit import api

lk_api = api.LiveKitAPI()
room = await lk_api.room.create_room(
    api.CreateRoomRequest(
        name="my-room",
        empty_timeout=300,          # Close after 5 min empty
        max_participants=10,
        metadata='{"type": "support"}'
    )
)
```

**Room properties:**
- `name` — Unique identifier (required)
- `empty_timeout` — Seconds before closing when empty (default: 300)
- `departure_timeout` — Seconds after last participant leaves
- `max_participants` — Hard cap on concurrent participants
- `metadata` — Arbitrary JSON string, broadcast to all participants

**Room lifecycle:**
1. Created via API or auto-created when first participant joins
2. Active while participants are connected
3. Closed when empty for `empty_timeout` seconds
4. Deleted via `DeleteRoom` API call

## Participants

Participants are entities in a room — both users and AI agents.

**Participant types:**
- **STANDARD** — Regular users connecting via client SDKs
- **SIP** — Callers connecting via telephony/SIP
- **AGENT** — AI agents built with the Agents framework

**Participant properties:**
- `sid` — Server-assigned unique ID
- `identity` — Developer-assigned unique string (must be unique per room)
- `name` — Display name (not unique)
- `metadata` — Arbitrary JSON, updatable at runtime
- `permissions` — Granular publish/subscribe controls

```javascript
// JavaScript — accessing participants
const room = new Room();
await room.connect(wsUrl, token);

// Local participant (you)
const local = room.localParticipant;

// Remote participants
room.remoteParticipants.forEach((participant) => {
  console.log(participant.identity, participant.name);
});

// Listen for new participants
room.on('participantConnected', (participant) => {
  console.log(`${participant.identity} joined`);
});
```

## Tracks

Tracks are media streams (audio/video) flowing between participants.

**Track sources:**
- `CAMERA` — Video from camera
- `MICROPHONE` — Audio from microphone
- `SCREEN_SHARE` — Screen capture video
- `SCREEN_SHARE_AUDIO` — Screen capture audio

**Track properties:**
- `sid` — Unique track ID
- `type` — `AUDIO` or `VIDEO`
- `source` — One of the sources above
- `muted` — Current mute state
- `codec` — Encoding codec (opus, vp8, h264, etc.)
- `dimensions` — Width/height for video tracks
- `simulcast_layers` — Quality layers for adaptive streaming

```javascript
// Publishing tracks
const room = new Room();
await room.connect(wsUrl, token);

// Publish camera and microphone
await room.localParticipant.enableCameraAndMicrophone();

// Subscribe to remote tracks
room.on('trackSubscribed', (track, publication, participant) => {
  if (track.kind === 'video') {
    const element = track.attach();
    document.getElementById('remote-video').appendChild(element);
  }
});
```

## Access Tokens

Access tokens are JWTs that authenticate participants and define their permissions.

```python
# Python — generate an access token
from livekit import api
import time

token = (
    api.AccessToken()
    .with_identity("user-123")
    .with_name("Alice")
    .with_grants(
        api.VideoGrants(
            room_join=True,
            room="my-room",
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True,
        )
    )
    .with_ttl(3600)  # 1 hour
    .to_jwt()
)
```

```javascript
// Node.js — generate an access token
import { AccessToken } from 'livekit-server-sdk';

const token = new AccessToken('api-key', 'api-secret', {
  identity: 'user-123',
  name: 'Alice',
  ttl: '1h',
});
token.addGrant({
  roomJoin: true,
  room: 'my-room',
  canPublish: true,
  canSubscribe: true,
});
const jwt = await token.toJwt();
```

**Token fields:**
- `identity` — Unique participant ID (required)
- `name` — Display name
- `grants` — Permissions (room access, publish, subscribe, admin)
- `ttl` — Token lifetime
- `metadata` — Participant metadata

## Connecting to LiveKit

Two parameters needed: **WebSocket URL** and **Access Token**.

```javascript
// JavaScript basic connection
import { Room } from 'livekit-client';

const room = new Room();
await room.connect('wss://your-project.livekit.cloud', token);

// React (recommended)
import { LiveKitRoom } from '@livekit/components-react';

function App() {
  return (
    <LiveKitRoom serverUrl="wss://your-project.livekit.cloud" token={token}>
      {/* Your components */}
    </LiveKitRoom>
  );
}
```

**Connection URLs:**
- Cloud: `wss://<project>.livekit.cloud`
- Self-hosted dev: `ws://localhost:7880`

## WebRTC Transport

LiveKit's transport layer handles:
- **SFU architecture** — Server forwards media selectively (not peer-to-peer mesh)
- **Simulcast** — Multiple quality layers for adaptive streaming
- **Codec support** — Opus (audio), VP8/VP9/H.264/AV1 (video)
- **Network adaptation** — Automatic quality adjustment based on bandwidth

**Connection priority order:**
1. ICE over UDP (preferred, lowest latency)
2. TURN with UDP (port 3478)
3. ICE over TCP (VPN/firewall fallback)
4. TURN with TLS (most restricted networks)

## Data Channels

Beyond audio/video, LiveKit supports realtime data exchange:

- **Text streams** — Structured text messaging
- **Byte streams** — Binary data transfer
- **RPC (Remote Procedure Calls)** — Request/response between participants
- **Data packets** — Fire-and-forget messages (reliable or lossy)

```python
# Server-side — send data to a room
await lk_api.room.send_data(
    api.SendDataRequest(
        room="my-room",
        data=b'{"event": "notification", "text": "Hello!"}',
        kind=api.DataPacketKind.RELIABLE,
        topic="notifications",
    )
)
```

## Connection Resilience

LiveKit handles disconnections automatically:
- Reconnects WebSocket signaling
- Performs ICE restart for WebRTC
- Fires `Reconnecting` and `Reconnected` events
- Republishes local tracks automatically

```javascript
room.on('reconnecting', () => console.log('Reconnecting...'));
room.on('reconnected', () => console.log('Reconnected!'));
room.on('disconnected', (reason) => console.log('Disconnected:', reason));
```

## Permissions Model

Granular per-participant controls:

| Permission | Description |
|-----------|-------------|
| `canSubscribe` | Receive tracks from others |
| `canPublish` | Send audio/video tracks |
| `canPublishData` | Send data messages |
| `canPublishSources` | Restrict to specific sources (camera, mic, screen) |
| `canUpdateMetadata` | Modify own metadata |
| `hidden` | Invisible to other participants |
| `recorder` | Marker for recording bots |

Permissions set via access token grants or updated at runtime via Room Service API.
