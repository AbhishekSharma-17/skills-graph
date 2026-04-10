# Multimodal Generation

> Source: https://ai-sdk.dev/docs/ai-sdk-core/image-generation

## Overview

AI SDK supports generating and processing multiple modalities: images, speech, transcription, and video (experimental). These functions follow the same unified pattern as text generation — provider-agnostic with consistent APIs.

## Image Generation

### Basic Usage

```typescript
import { generateImage } from 'ai';

const { image } = await generateImage({
  model: 'openai/dall-e-3',
  prompt: 'A futuristic city skyline at sunset, cyberpunk style',
});

// image.base64 — Base64-encoded image data
// image.uint8Array — Raw binary data
```

### With Options

```typescript
const { image } = await generateImage({
  model: 'openai/dall-e-3',
  prompt: 'A minimalist logo for a tech startup called "NexGen"',
  size: '1024x1024',
  quality: 'hd',
  style: 'natural',
  n: 1, // Number of images
});
```

### Multiple Images

```typescript
const { images } = await generateImage({
  model: 'openai/dall-e-3',
  prompt: 'Abstract geometric patterns',
  n: 4,
});

for (const img of images) {
  await writeFile(`output-${img.id}.png`, img.uint8Array);
}
```

### Image Editing (v6)

Reference images for inpainting, outpainting, style transfer:

```typescript
import { generateImage } from 'ai';

const { image } = await generateImage({
  model: 'openai/dall-e-3',
  prompt: 'Add a rainbow in the sky',
  images: [
    { type: 'url', url: 'https://example.com/landscape.jpg' },
  ],
});
```

### Image Input Formats

```typescript
// URL
images: [{ type: 'url', url: 'https://...' }]

// Base64
images: [{ type: 'base64', data: base64String, mimeType: 'image/png' }]

// Buffer
images: [{ type: 'uint8array', data: buffer, mimeType: 'image/jpeg' }]
```

## Speech Generation

### Text-to-Speech

```typescript
import { generateSpeech } from 'ai';

const { audio } = await generateSpeech({
  model: 'openai/tts-1',
  text: 'Hello! Welcome to our application.',
  voice: 'alloy',
});

// audio.base64 — Base64-encoded audio
// audio.uint8Array — Raw audio bytes
await writeFile('greeting.mp3', audio.uint8Array);
```

### Voice Options

```typescript
const { audio } = await generateSpeech({
  model: 'openai/tts-1-hd',
  text: longArticleText,
  voice: 'nova', // alloy, echo, fable, onyx, nova, shimmer
  speed: 1.0,    // 0.25 to 4.0
  responseFormat: 'mp3', // mp3, opus, aac, flac
});
```

### With ElevenLabs

```typescript
import { elevenlabs } from '@ai-sdk/elevenlabs';

const { audio } = await generateSpeech({
  model: elevenlabs.speech('eleven_multilingual_v2'),
  text: 'Bonjour, comment allez-vous?',
  voice: 'Rachel',
  providerOptions: {
    elevenlabs: {
      stability: 0.5,
      similarityBoost: 0.75,
    },
  },
});
```

## Transcription

### Audio-to-Text

```typescript
import { transcribe } from 'ai';
import { readFile } from 'fs/promises';

const { text, segments } = await transcribe({
  model: 'openai/whisper-1',
  audio: await readFile('meeting-recording.mp3'),
  mimeType: 'audio/mp3',
});

console.log(text); // Full transcription

// Timestamped segments
for (const seg of segments) {
  console.log(`[${seg.start}s - ${seg.end}s]: ${seg.text}`);
}
```

### With Options

```typescript
const { text } = await transcribe({
  model: 'openai/whisper-1',
  audio: audioBuffer,
  mimeType: 'audio/wav',
  language: 'en',         // ISO-639-1 language code
  prompt: 'Technical discussion about AI', // Context hint
  temperature: 0,
});
```

### Transcription Providers

```typescript
// Deepgram
import { deepgram } from '@ai-sdk/deepgram';

const { text } = await transcribe({
  model: deepgram.transcription('nova-2'),
  audio: audioBuffer,
  mimeType: 'audio/mp3',
});

// AssemblyAI
import { assemblyai } from '@ai-sdk/assemblyai';

const { text } = await transcribe({
  model: assemblyai.transcription('best'),
  audio: audioBuffer,
  mimeType: 'audio/mp3',
});
```

## Vision (Image Understanding)

Pass images to language models for analysis:

```typescript
import { generateText } from 'ai';

const { text } = await generateText({
  model: 'anthropic/claude-sonnet-4.5',
  messages: [
    {
      role: 'user',
      content: [
        { type: 'text', text: 'What is in this image? Be specific.' },
        {
          type: 'image',
          image: new URL('https://example.com/photo.jpg'),
        },
      ],
    },
  ],
});
```

### Multiple Images

```typescript
const { text } = await generateText({
  model: 'openai/gpt-5.2',
  messages: [
    {
      role: 'user',
      content: [
        { type: 'text', text: 'Compare these two images.' },
        { type: 'image', image: new URL('https://example.com/before.jpg') },
        { type: 'image', image: new URL('https://example.com/after.jpg') },
      ],
    },
  ],
});
```

### Image from Buffer

```typescript
import { readFile } from 'fs/promises';

const imageData = await readFile('screenshot.png');

const { text } = await generateText({
  model: 'anthropic/claude-sonnet-4.5',
  messages: [
    {
      role: 'user',
      content: [
        { type: 'text', text: 'Describe this UI screenshot.' },
        { type: 'image', image: imageData, mimeType: 'image/png' },
      ],
    },
  ],
});
```

## File Processing (PDFs, Documents)

```typescript
import { generateText } from 'ai';
import { readFile } from 'fs/promises';

const { text } = await generateText({
  model: 'anthropic/claude-sonnet-4.5',
  messages: [
    {
      role: 'user',
      content: [
        { type: 'text', text: 'Summarize this document in 3 bullet points.' },
        {
          type: 'file',
          data: await readFile('report.pdf'),
          mimeType: 'application/pdf',
        },
      ],
    },
  ],
});
```

## Video Generation (Experimental)

```typescript
import { experimental_generateVideo as generateVideo } from 'ai';

const { video } = await generateVideo({
  model: 'google/veo-2',
  prompt: 'A timelapse of a flower blooming in a garden',
  duration: 5, // seconds
});

await writeFile('flower.mp4', video.uint8Array);
```

## Streaming Images in Chat

Server-side generation visible in chat UI:

```typescript
// Server route
import { streamText } from 'ai';

export async function POST(req: Request) {
  const { messages } = await req.json();

  const result = streamText({
    model: 'google/gemini-2.5-pro', // Supports inline image generation
    messages: await convertToModelMessages(messages),
  });

  return result.toUIMessageStreamResponse();
}
```

```typescript
// Client rendering
{m.parts.map((part, i) => {
  if (part.type === 'text') return <p key={i}>{part.text}</p>;
  if (part.type === 'file' && part.mediaType?.startsWith('image/')) {
    return <img key={i} src={part.url} alt="Generated" />;
  }
  return null;
})}
```

## Common Pitfalls

1. **Model capability** — Not all models support all modalities; check provider docs
2. **File size limits** — Image/audio inputs have provider-specific size limits
3. **Cost** — Image/video generation is significantly more expensive than text
4. **Async processing** — Some generations (video) may take minutes; handle timeouts
5. **Format compatibility** — Ensure output format matches your use case (mp3 vs wav, png vs jpg)

## Related Topics

- Text generation → [02-generating-text](02-generating-text.md)
- Providers → [01-providers-and-models](01-providers-and-models.md)
- Chat UI → [07-useChat-hook](07-useChat-hook.md)
