# Mastra — Voice

> Source: [mastra.ai/docs/agents/adding-voice](https://mastra.ai/docs/agents/adding-voice) · `@mastra/core` v1.37.x

## Overview

Mastra agents can speak responses and listen to user input through voice capabilities. The framework supports text-to-speech (TTS), speech-to-text (STT), and real-time speech-to-speech interactions with 12+ providers.

## Voice Agent Types

| Type | Description | Use Case |
|------|-------------|----------|
| Basic | Single provider for TTS and STT | Voice-enabled chatbots |
| Composite | Mix different providers for TTS/STT | Best-of-breed per modality |
| Real-Time | WebSocket-based speech-to-speech | Live phone calls, voice assistants |

## Basic Voice Agent

```typescript
import { Agent } from '@mastra/core/agent'
import { OpenAIVoice } from '@mastra/voice-openai'

const voiceAgent = new Agent({
  id: 'voice-agent',
  name: 'Voice Agent',
  instructions: 'You are a helpful voice assistant. Keep responses short and conversational.',
  model: 'openai/gpt-5-mini',
  voice: new OpenAIVoice({
    speaker: 'alloy',  // Voice preset
  }),
})
```

## Composite Voice Agent

Mix different providers for TTS and STT:

```typescript
import { CompositeVoice } from '@mastra/core/voice'
import { ElevenLabsVoice } from '@mastra/voice-elevenlabs'
import { DeepgramVoice } from '@mastra/voice-deepgram'

const voice = new CompositeVoice({
  tts: new ElevenLabsVoice({
    apiKey: process.env.ELEVENLABS_API_KEY,
    voiceId: 'rachel',
  }),
  stt: new DeepgramVoice({
    apiKey: process.env.DEEPGRAM_API_KEY,
  }),
})

const agent = new Agent({
  id: 'composite-voice-agent',
  voice,
})
```

## Real-Time Voice Agent

WebSocket-based for live speech-to-speech interactions:

```typescript
import { OpenAIRealtimeVoice } from '@mastra/voice-openai-realtime'

const realtimeVoice = new OpenAIRealtimeVoice({
  model: 'gpt-4o-realtime-preview',
})

const agent = new Agent({
  id: 'realtime-agent',
  name: 'Realtime Agent',
  instructions: 'You are a conversational assistant.',
  model: 'openai/gpt-5-mini',
  voice: realtimeVoice,
})

// Connect and manage real-time session
await realtimeVoice.connect()

// Stream microphone input
realtimeVoice.send(audioBuffer)

// Listen for events
realtimeVoice.on('speaking', (audioData) => {
  // Play audio to user
  speaker.write(audioData)
})

realtimeVoice.on('writing', (transcription) => {
  console.log(`${transcription.role}: ${transcription.text}`)
})

// Cleanup
await realtimeVoice.close()
```

## Key Methods

### speak() — Text to Audio

```typescript
const audioStream = await agent.voice.speak('Hello, how can I help you?', {
  format: 'mp3',  // or 'm4a', 'wav', 'pcm'
})

// Write to file
const writeStream = fs.createWriteStream('response.mp3')
audioStream.pipe(writeStream)
```

### listen() — Audio to Text

```typescript
const audioBuffer = fs.readFileSync('user-input.wav')
const transcription = await agent.voice.listen(audioBuffer, {
  language: 'en',
})
console.log(transcription.text)
```

### connect() / close() — Real-Time Sessions

```typescript
// Start real-time connection
await agent.voice.connect()

// End session
await agent.voice.close()
```

### send() — Stream Audio Data

```typescript
// Stream microphone input to real-time voice
agent.voice.send(microphoneChunk)
```

## Event System

Real-time voice agents emit events:

```typescript
agent.voice.on('speaking', (audioData) => {
  // Agent is producing audio
})

agent.voice.on('writing', ({ role, text }) => {
  // Transcribed text available
  console.log(`${role}: ${text}`)
})

agent.voice.on('error', (error) => {
  console.error('Voice error:', error)
})
```

## Supported Providers

### TTS + STT (Both Directions)

| Provider | Package |
|----------|---------|
| OpenAI | `@mastra/voice-openai` |
| Google | `@mastra/voice-google` |
| Azure | `@mastra/voice-azure` |
| Sarvam | `@mastra/voice-sarvam` |

### TTS Only

| Provider | Package |
|----------|---------|
| ElevenLabs | `@mastra/voice-elevenlabs` |
| PlayAI | `@mastra/voice-playai` |
| Murf | `@mastra/voice-murf` |
| Speechify | `@mastra/voice-speechify` |
| Cloudflare | `@mastra/voice-cloudflare` |

### STT Only

| Provider | Package |
|----------|---------|
| Deepgram | `@mastra/voice-deepgram` |

### Real-Time (Speech-to-Speech)

| Provider | Package |
|----------|---------|
| OpenAI Realtime | `@mastra/voice-openai-realtime` |
| AWS Nova Sonic | `@mastra/voice-aws-nova-sonic` |

## Common Patterns

### Voice-Enabled Customer Support

```typescript
const supportAgent = new Agent({
  id: 'voice-support',
  name: 'Voice Support',
  instructions: 'You are a customer support agent. Speak clearly and concisely.',
  model: 'openai/gpt-5.4',
  tools: { orderLookup, ticketCreate },
  memory: new Memory({ options: { lastMessages: 20 } }),
  voice: new CompositeVoice({
    tts: new ElevenLabsVoice({ voiceId: 'professional' }),
    stt: new DeepgramVoice(),
  }),
})
```

### Voice Pipeline in Workflow

```typescript
const voiceWorkflow = createWorkflow({
  id: 'voice-pipeline',
  inputSchema: z.object({ audioBuffer: z.any() }),
  outputSchema: z.object({ audioResponse: z.any() }),
})
  .then(transcribeStep)   // STT
  .then(processStep)      // Agent generates response
  .then(synthesizeStep)   // TTS
  .commit()
```

## Pitfalls

1. **Audio format compatibility** — match the format between STT input and TTS output
2. **Real-time latency** — WebSocket connections add overhead; use for conversational flows only
3. **Provider mixing** — CompositeVoice works for separate TTS+STT; real-time requires a single provider
4. **Cost** — voice API calls are priced per minute/character; monitor usage
5. **Keep voice instructions short** — long system prompts increase first-response latency in real-time mode
