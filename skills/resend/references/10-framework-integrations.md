# Framework Integrations

> Source: https://resend.com/docs

## Table of Contents
- [Next.js](#nextjs)
- [Express.js](#expressjs)
- [FastAPI](#fastapi)
- [Cloudflare Workers](#cloudflare-workers)
- [Vercel Edge Functions](#vercel-edge-functions)
- [AWS Lambda](#aws-lambda)
- [Supabase Edge Functions](#supabase-edge-functions)
- [Hono](#hono)
- [SvelteKit](#sveltekit)
- [Remix](#remix)
- [MCP Server](#mcp-server)
- [CLI](#cli)

## Next.js

### App Router — Route Handler

```typescript
// app/api/send/route.ts
import { Resend } from 'resend';
import { WelcomeEmail } from '@/emails/welcome';

const resend = new Resend(process.env.RESEND_API_KEY);

export async function POST(request: Request) {
  const { email, name } = await request.json();

  const { data, error } = await resend.emails.send({
    from: 'App <noreply@yourdomain.com>',
    to: email,
    subject: `Welcome, ${name}!`,
    react: WelcomeEmail({ name }),
  });

  if (error) {
    return Response.json({ error }, { status: 400 });
  }

  return Response.json({ id: data.id });
}
```

### App Router — Server Action

```typescript
// app/actions/send-email.ts
'use server';

import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);

export async function sendContactEmail(formData: FormData) {
  const email = formData.get('email') as string;
  const message = formData.get('message') as string;

  const { error } = await resend.emails.send({
    from: 'Contact <contact@yourdomain.com>',
    to: 'team@yourdomain.com',
    subject: `Contact from ${email}`,
    text: message,
    replyTo: email,
  });

  if (error) {
    return { success: false, error: error.message };
  }

  return { success: true };
}
```

### Pages Router — API Route

```typescript
// pages/api/send.ts
import type { NextApiRequest, NextApiResponse } from 'next';
import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { data, error } = await resend.emails.send({
    from: 'App <noreply@yourdomain.com>',
    to: req.body.email,
    subject: 'Hello',
    html: '<p>Hello from Next.js</p>',
  });

  if (error) return res.status(400).json(error);
  return res.status(200).json(data);
}
```

## Express.js

```typescript
import express from 'express';
import { Resend } from 'resend';

const app = express();
const resend = new Resend(process.env.RESEND_API_KEY);

app.use(express.json());

app.post('/api/send', async (req, res) => {
  const { data, error } = await resend.emails.send({
    from: 'App <noreply@yourdomain.com>',
    to: req.body.email,
    subject: req.body.subject,
    html: req.body.html,
  });

  if (error) return res.status(400).json(error);
  return res.json(data);
});

app.listen(3000);
```

## FastAPI

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import resend
import os

app = FastAPI()
resend.api_key = os.environ["RESEND_API_KEY"]

class EmailRequest(BaseModel):
    to: str
    subject: str
    html: str

@app.post("/api/send")
async def send_email(req: EmailRequest):
    try:
        email = await resend.Emails.send_async({
            "from": "App <noreply@yourdomain.com>",
            "to": [req.to],
            "subject": req.subject,
            "html": req.html,
        })
        return {"id": email["id"]}
    except resend.exceptions.ResendError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)
```

## Cloudflare Workers

```typescript
import { Resend } from 'resend';

interface Env {
  RESEND_API_KEY: string;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method !== 'POST') {
      return new Response('Method not allowed', { status: 405 });
    }

    const resend = new Resend(env.RESEND_API_KEY);
    const { email, subject, html } = await request.json();

    const { data, error } = await resend.emails.send({
      from: 'App <noreply@yourdomain.com>',
      to: email,
      subject,
      html,
    });

    if (error) {
      return Response.json(error, { status: 400 });
    }

    return Response.json(data);
  },
};
```

## Vercel Edge Functions

```typescript
// app/api/send/route.ts
import { Resend } from 'resend';

export const runtime = 'edge';

const resend = new Resend(process.env.RESEND_API_KEY);

export async function POST(request: Request) {
  const { email, name } = await request.json();

  const { data, error } = await resend.emails.send({
    from: 'App <noreply@yourdomain.com>',
    to: email,
    subject: `Hello ${name}`,
    html: `<p>Welcome, ${name}!</p>`,
  });

  if (error) return Response.json(error, { status: 400 });
  return Response.json(data);
}
```

## AWS Lambda

```typescript
import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);

export const handler = async (event: any) => {
  const body = JSON.parse(event.body);

  const { data, error } = await resend.emails.send({
    from: 'App <noreply@yourdomain.com>',
    to: body.email,
    subject: body.subject,
    html: body.html,
  });

  if (error) {
    return { statusCode: 400, body: JSON.stringify(error) };
  }

  return { statusCode: 200, body: JSON.stringify(data) };
};
```

## Supabase Edge Functions

```typescript
// supabase/functions/send-email/index.ts
import { Resend } from 'npm:resend';

const resend = new Resend(Deno.env.get('RESEND_API_KEY'));

Deno.serve(async (req) => {
  const { email, subject, html } = await req.json();

  const { data, error } = await resend.emails.send({
    from: 'App <noreply@yourdomain.com>',
    to: email,
    subject,
    html,
  });

  if (error) return new Response(JSON.stringify(error), { status: 400 });
  return new Response(JSON.stringify(data));
});
```

## Hono

```typescript
import { Hono } from 'hono';
import { Resend } from 'resend';

const app = new Hono();

app.post('/api/send', async (c) => {
  const resend = new Resend(c.env.RESEND_API_KEY);
  const { email, subject, html } = await c.req.json();

  const { data, error } = await resend.emails.send({
    from: 'App <noreply@yourdomain.com>',
    to: email,
    subject,
    html,
  });

  if (error) return c.json(error, 400);
  return c.json(data);
});

export default app;
```

## SvelteKit

```typescript
// src/routes/api/send/+server.ts
import { Resend } from 'resend';
import { RESEND_API_KEY } from '$env/static/private';
import { json, error } from '@sveltejs/kit';

const resend = new Resend(RESEND_API_KEY);

export async function POST({ request }) {
  const { email, subject, html } = await request.json();

  const { data, error: sendError } = await resend.emails.send({
    from: 'App <noreply@yourdomain.com>',
    to: email,
    subject,
    html,
  });

  if (sendError) throw error(400, sendError.message);
  return json(data);
}
```

## Remix

```typescript
// app/routes/api.send.tsx
import { json, type ActionFunctionArgs } from '@remix-run/node';
import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);

export async function action({ request }: ActionFunctionArgs) {
  const formData = await request.formData();

  const { data, error } = await resend.emails.send({
    from: 'App <noreply@yourdomain.com>',
    to: formData.get('email') as string,
    subject: formData.get('subject') as string,
    html: formData.get('html') as string,
  });

  if (error) return json(error, { status: 400 });
  return json(data);
}
```

## MCP Server

Resend provides an MCP (Model Context Protocol) server for AI tool integration:

```bash
npx resend-mcp
```

Compatible with Claude Desktop, Cursor, Windsurf, and other MCP-aware tools. Enables AI assistants to send emails programmatically.

## CLI

```bash
# Install
npm install -g resend

# Login
resend login

# Send email
resend emails send --from "you@yourdomain.com" --to "user@example.com" --subject "Hello" --html "<p>Hi</p>"

# Manage API keys
resend api-keys create --name "My Key"
resend api-keys list
resend api-keys delete --id <key-id>

# Manage domains
resend domains list
resend domains create --name yourdomain.com
resend domains verify --id <domain-id>
```
