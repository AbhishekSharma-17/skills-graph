# Frontend SDKs

> Source: [docs.livekit.io/frontends](https://docs.livekit.io/frontends/) — React, JavaScript, Swift, Android, Flutter

## Table of Contents

- [SDK Overview](#sdk-overview)
- [React Components](#react-components)
- [JavaScript SDK](#javascript-sdk)
- [Session Management](#session-management)
- [Audio Visualization](#audio-visualization)
- [Chat & Text Interface](#chat--text-interface)
- [Video Rendering](#video-rendering)
- [Mobile SDKs](#mobile-sdks)
- [Web Embed](#web-embed)
- [Common Patterns](#common-patterns)

---

## SDK Overview

| Platform | Package | Installation |
|----------|---------|-------------|
| React | `@livekit/components-react` | `npm i @livekit/components-react livekit-client` |
| JavaScript | `livekit-client` | `npm i livekit-client` |
| Swift/SwiftUI | `livekit-swift` | Swift Package Manager |
| Android/Kotlin | `livekit-android` | Maven/JitPack |
| Flutter | `livekit_client` | `flutter pub add livekit_client` |
| React Native | `@livekit/react-native` | `npm i @livekit/react-native` |

## React Components

### Quick Setup

```bash
npm install @livekit/components-react livekit-client
```

### LiveKitRoom Provider

The root component that manages the room connection:

```tsx
import { LiveKitRoom } from '@livekit/components-react';

function App() {
  return (
    <LiveKitRoom
      serverUrl="wss://your-project.livekit.cloud"
      token={accessToken}
      connect={true}
      onConnected={() => console.log('Connected!')}
      onDisconnected={() => console.log('Disconnected')}
    >
      <VoiceAgent />
    </LiveKitRoom>
  );
}
```

### Pre-built Voice Agent UI

```tsx
import {
  LiveKitRoom,
  RoomAudioRenderer,
  VoiceAssistant,
  BarVisualizer,
  DisconnectButton,
} from '@livekit/components-react';

function VoiceAgentApp() {
  return (
    <LiveKitRoom serverUrl={serverUrl} token={token} connect={true}>
      <RoomAudioRenderer />
      <VoiceAssistant>
        <BarVisualizer />
      </VoiceAssistant>
      <DisconnectButton>Leave</DisconnectButton>
    </LiveKitRoom>
  );
}
```

### Key React Components

| Component | Purpose |
|-----------|---------|
| `LiveKitRoom` | Room connection provider |
| `RoomAudioRenderer` | Renders all audio tracks |
| `VoiceAssistant` | Voice agent interface wrapper |
| `BarVisualizer` | Audio level visualization |
| `VideoTrack` | Renders a video track |
| `ParticipantTile` | Participant video + audio tile |
| `DisconnectButton` | Leave the room |
| `ChatEntry` | Single chat message |
| `Chat` | Full chat interface |

### React Hooks

```tsx
import {
  useRoom,
  useParticipants,
  useLocalParticipant,
  useRemoteParticipants,
  useTracks,
  useRoomInfo,
  useConnectionState,
} from '@livekit/components-react';

function MyComponent() {
  const room = useRoom();
  const participants = useParticipants();
  const localParticipant = useLocalParticipant();
  const connectionState = useConnectionState();
  const tracks = useTracks();

  return (
    <div>
      <p>Status: {connectionState}</p>
      <p>Participants: {participants.length}</p>
    </div>
  );
}
```

## JavaScript SDK

### Basic Connection

```javascript
import { Room, RoomEvent } from 'livekit-client';

const room = new Room();

// Event handlers
room.on(RoomEvent.Connected, () => {
  console.log('Connected to room');
});

room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
  if (track.kind === 'audio') {
    const element = track.attach();
    document.body.appendChild(element);
  }
});

room.on(RoomEvent.Disconnected, (reason) => {
  console.log('Disconnected:', reason);
});

// Connect
await room.connect('wss://your-project.livekit.cloud', token);
```

### Publishing Media

```javascript
// Enable camera and microphone
await room.localParticipant.enableCameraAndMicrophone();

// Publish only microphone
await room.localParticipant.setMicrophoneEnabled(true);

// Publish screen share
await room.localParticipant.setScreenShareEnabled(true);

// Mute/unmute
await room.localParticipant.setMicrophoneEnabled(false);
```

### Data Messages

```javascript
// Send data to all participants
const encoder = new TextEncoder();
room.localParticipant.publishData(
  encoder.encode(JSON.stringify({ type: 'chat', message: 'Hello!' })),
  { reliable: true, topic: 'chat' }
);

// Receive data
room.on(RoomEvent.DataReceived, (data, participant, kind, topic) => {
  const decoder = new TextDecoder();
  const message = JSON.parse(decoder.decode(data));
  console.log(`${participant.identity}: ${message.message}`);
});
```

## Session Management

### Token Generation (Server-side)

```javascript
// Node.js token server
import { AccessToken } from 'livekit-server-sdk';
import express from 'express';

const app = express();

app.get('/api/token', async (req, res) => {
  const { room, identity } = req.query;

  const token = new AccessToken(
    process.env.LIVEKIT_API_KEY,
    process.env.LIVEKIT_API_SECRET,
    { identity, ttl: '1h' }
  );
  token.addGrant({ roomJoin: true, room, canPublish: true, canSubscribe: true });

  res.json({ token: await token.toJwt() });
});
```

### React Token Flow

```tsx
function App() {
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    fetch(`/api/token?room=my-room&identity=user-${Date.now()}`)
      .then(res => res.json())
      .then(data => setToken(data.token));
  }, []);

  if (!token) return <div>Connecting...</div>;

  return (
    <LiveKitRoom serverUrl={serverUrl} token={token} connect={true}>
      <AgentUI />
    </LiveKitRoom>
  );
}
```

## Audio Visualization

```tsx
import { BarVisualizer, useVoiceAssistant } from '@livekit/components-react';

function AgentVisualizer() {
  const { state, audioTrack } = useVoiceAssistant();

  return (
    <div>
      <BarVisualizer
        state={state}
        barCount={5}
        trackRef={audioTrack}
      />
      <p>Agent is {state}</p>
    </div>
  );
}
```

## Chat & Text Interface

```tsx
import { Chat, ChatEntry } from '@livekit/components-react';

function ChatInterface() {
  return (
    <Chat
      messageFormatter={(message) => (
        <ChatEntry
          entry={message}
          hideName={false}
          hideTimestamp={false}
        />
      )}
    />
  );
}
```

## Video Rendering

```tsx
import { VideoTrack, ParticipantTile } from '@livekit/components-react';

function VideoGrid() {
  const tracks = useTracks([Track.Source.Camera]);

  return (
    <div className="grid grid-cols-2 gap-4">
      {tracks.map((track) => (
        <ParticipantTile key={track.participant.sid} trackRef={track} />
      ))}
    </div>
  );
}
```

## Mobile SDKs

### Swift/SwiftUI

```swift
import LiveKit
import LiveKitComponents

struct ContentView: View {
    @StateObject var room = Room()

    var body: some View {
        RoomScope(room) {
            VStack {
                ForEach(room.remoteParticipants.values) { participant in
                    ParticipantView(participant: participant)
                }
            }
        }
        .task {
            try? await room.connect(url: serverUrl, token: token)
        }
    }
}
```

### Flutter

```dart
import 'package:livekit_client/livekit_client.dart';

final room = Room();
await room.connect(serverUrl, token);

// Listen for tracks
room.on<TrackSubscribedEvent>((event) {
  if (event.track is AudioTrack) {
    (event.track as AudioTrack).start();
  }
});
```

## Web Embed

Embed a LiveKit agent in any website:

```html
<iframe
  src="https://your-frontend.com/agent?room=embed-room"
  width="400"
  height="600"
  allow="microphone; camera"
  style="border: none; border-radius: 12px;"
></iframe>
```

## Common Patterns

### Connection state handling

```tsx
function ConnectionStatus() {
  const state = useConnectionState();

  switch (state) {
    case 'connecting': return <Spinner />;
    case 'connected': return <AgentUI />;
    case 'reconnecting': return <ReconnectingBanner />;
    case 'disconnected': return <ReconnectButton />;
  }
}
```

### Agent state display

```tsx
function AgentStatus() {
  const { state } = useVoiceAssistant();
  const labels = {
    listening: 'Listening...',
    thinking: 'Thinking...',
    speaking: 'Speaking...',
  };
  return <p>{labels[state] || state}</p>;
}
```
