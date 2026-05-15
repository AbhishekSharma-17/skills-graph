# React Email

> Source: https://react.email/docs

## Table of Contents
- [What Is React Email](#what-is-react-email)
- [Installation & Setup](#installation--setup)
- [Core Components](#core-components)
- [Layout Components](#layout-components)
- [Content Components](#content-components)
- [Styling with Tailwind](#styling-with-tailwind)
- [Building a Template](#building-a-template)
- [Rendering to HTML](#rendering-to-html)
- [Sending with Resend](#sending-with-resend)
- [Visual Editor](#visual-editor)
- [Preview & Development](#preview--development)
- [Template Patterns](#template-patterns)
- [Common Pitfalls](#common-pitfalls)

## What Is React Email

React Email is an open-source component library for building email templates using React and TypeScript. It provides unstyled, cross-client-compatible primitives that render to HTML email. Created by the Resend team, it handles the inconsistencies between Gmail, Outlook, Apple Mail, and other email clients.

Key features:
- All components in a single `react-email` package (since v6)
- Built-in Tailwind CSS support
- Open-source visual editor (v6.0+)
- 2M+ weekly npm downloads
- TypeScript-first with full type safety

## Installation & Setup

```bash
npm install react-email
```

All components are re-exported from the main package:

```typescript
import {
  Html, Head, Body, Container, Section,
  Row, Column, Heading, Text, Button,
  Link, Img, Hr, Preview, Tailwind,
  Font, CodeBlock, CodeInline, Markdown,
} from 'react-email';
```

### Development Preview

```bash
npx react-email dev
```

Opens a local preview server at `localhost:3000` showing all templates in your `emails/` directory.

## Core Components

### Html / Head / Body

Every email template starts with these structural components:

```tsx
import { Html, Head, Body, Preview } from 'react-email';

export function MyEmail() {
  return (
    <Html lang="en">
      <Head />
      <Preview>Preview text shown in inbox</Preview>
      <Body style={{ backgroundColor: '#f6f9fc', fontFamily: 'sans-serif' }}>
        {/* content */}
      </Body>
    </Html>
  );
}
```

- `<Html>` — wraps the entire email, sets `lang` and `dir`
- `<Head>` — includes `<meta>` tags and `<Font>` declarations
- `<Body>` — root content container
- `<Preview>` — hidden text shown as inbox preview (replaces `preheader`)

### Container

Centers content with a max-width:

```tsx
<Container style={{ maxWidth: '600px', margin: '0 auto', padding: '20px' }}>
  {/* Centered content */}
</Container>
```

## Layout Components

### Section / Row / Column

```tsx
<Section style={{ padding: '24px' }}>
  <Row>
    <Column style={{ width: '50%' }}>Left content</Column>
    <Column style={{ width: '50%' }}>Right content</Column>
  </Row>
</Section>
```

`<Section>` renders as a `<table>`, `<Row>` as `<tr>`, `<Column>` as `<td>` — ensuring email client compatibility.

### Hr (Divider)

```tsx
<Hr style={{ borderColor: '#e6ebf1', margin: '20px 0' }} />
```

## Content Components

### Heading / Text

```tsx
<Heading as="h1" style={{ fontSize: '24px', fontWeight: 'bold' }}>
  Welcome!
</Heading>
<Text style={{ fontSize: '16px', lineHeight: '24px', color: '#525f7f' }}>
  Thanks for signing up.
</Text>
```

### Button

```tsx
<Button
  href="https://yourdomain.com/activate"
  style={{
    backgroundColor: '#000',
    color: '#fff',
    padding: '12px 20px',
    borderRadius: '5px',
    textDecoration: 'none',
    fontSize: '14px',
  }}
>
  Activate Account
</Button>
```

### Link / Img

```tsx
<Link href="https://yourdomain.com" style={{ color: '#2563eb' }}>
  Visit our site
</Link>

<Img
  src="https://yourdomain.com/logo.png"
  width="120"
  height="36"
  alt="Company Logo"
/>
```

### CodeBlock / Markdown

```tsx
<CodeBlock
  code="npm install resend"
  language="bash"
  theme="dracula"
/>

<Markdown>{`
  # Hello
  This is **markdown** content.
`}</Markdown>
```

## Styling with Tailwind

React Email includes a `<Tailwind>` wrapper that enables Tailwind CSS classes:

```tsx
import { Html, Head, Body, Tailwind, Text, Button } from 'react-email';

export function StyledEmail() {
  return (
    <Html>
      <Head />
      <Tailwind>
        <Body className="bg-white font-sans">
          <Text className="text-xl font-bold text-gray-900">Hello!</Text>
          <Button
            href="https://example.com"
            className="bg-blue-600 text-white px-6 py-3 rounded-md"
          >
            Click Me
          </Button>
        </Body>
      </Tailwind>
    </Html>
  );
}
```

The `<Tailwind>` component compiles classes to inline styles at render time, ensuring compatibility with all email clients.

### Custom Tailwind Config

```tsx
<Tailwind
  config={{
    theme: {
      extend: {
        colors: {
          brand: '#007bff',
        },
      },
    },
  }}
>
  <Text className="text-brand">Brand colored text</Text>
</Tailwind>
```

## Building a Template

### Complete Welcome Email

```tsx
import {
  Html, Head, Body, Container, Section,
  Heading, Text, Button, Img, Hr, Preview, Tailwind,
} from 'react-email';

interface WelcomeEmailProps {
  name: string;
  activationUrl: string;
}

export function WelcomeEmail({ name, activationUrl }: WelcomeEmailProps) {
  return (
    <Html>
      <Head />
      <Preview>Welcome to our platform, {name}!</Preview>
      <Tailwind>
        <Body className="bg-gray-50 font-sans">
          <Container className="max-w-[600px] mx-auto p-8">
            <Img
              src="https://yourdomain.com/logo.png"
              width="120"
              height="36"
              alt="Logo"
              className="mx-auto mb-8"
            />
            <Section className="bg-white rounded-lg p-8 shadow-sm">
              <Heading className="text-2xl font-bold text-gray-900 text-center">
                Welcome, {name}!
              </Heading>
              <Text className="text-base text-gray-600 mt-4">
                We are excited to have you on board. Click the button below to
                activate your account.
              </Text>
              <Section className="text-center mt-8">
                <Button
                  href={activationUrl}
                  className="bg-black text-white px-8 py-3 rounded-md font-medium"
                >
                  Activate Account
                </Button>
              </Section>
            </Section>
            <Hr className="border-gray-200 my-8" />
            <Text className="text-sm text-gray-400 text-center">
              You received this because you signed up at yourdomain.com
            </Text>
          </Container>
        </Body>
      </Tailwind>
    </Html>
  );
}

export default WelcomeEmail;
```

## Rendering to HTML

Use `render()` to convert a React Email component to an HTML string:

```typescript
import { render } from 'react-email';
import { WelcomeEmail } from './emails/welcome';

const html = await render(WelcomeEmail({ name: 'Alice', activationUrl: '...' }));
const text = await render(WelcomeEmail({ name: 'Alice', activationUrl: '...' }), {
  plainText: true,
});
```

This is required when using batch sends (which don't support the `react` parameter directly).

## Sending with Resend

```typescript
import { Resend } from 'resend';
import { WelcomeEmail } from '@/emails/welcome';

const resend = new Resend(process.env.RESEND_API_KEY);

await resend.emails.send({
  from: 'App <noreply@yourdomain.com>',
  to: 'user@example.com',
  subject: 'Welcome!',
  react: WelcomeEmail({ name: 'Alice', activationUrl: 'https://...' }),
});
```

## Visual Editor

React Email 6.0 introduced an open-source visual editor:

```bash
npm install @react-email/editor
```

The editor can be embedded in your application, allowing non-developers to edit email templates visually. Templates can also be uploaded to Resend for team collaboration.

## Preview & Development

```bash
# Start dev server
npx react-email dev

# Export templates to HTML
npx react-email export

# Build for production
npx react-email build
```

**File structure:**
```
emails/
├── welcome.tsx
├── order-confirmation.tsx
├── password-reset.tsx
└── components/
    ├── header.tsx
    └── footer.tsx
```

## Template Patterns

### Shared Layout

```tsx
function EmailLayout({ children, preview }: { children: React.ReactNode; preview: string }) {
  return (
    <Html>
      <Head />
      <Preview>{preview}</Preview>
      <Tailwind>
        <Body className="bg-gray-50 font-sans">
          <Container className="max-w-[600px] mx-auto p-8">
            <Img src="https://yourdomain.com/logo.png" width="120" height="36" alt="Logo" />
            {children}
            <Hr className="border-gray-200 my-8" />
            <Text className="text-xs text-gray-400 text-center">
              Company Inc. | 123 Street, City
            </Text>
          </Container>
        </Body>
      </Tailwind>
    </Html>
  );
}
```

### Conditional Content

```tsx
function OrderEmail({ status, trackingUrl }: { status: string; trackingUrl?: string }) {
  return (
    <EmailLayout preview={`Order ${status}`}>
      <Heading>Order {status}</Heading>
      {status === 'shipped' && trackingUrl && (
        <Button href={trackingUrl}>Track Package</Button>
      )}
    </EmailLayout>
  );
}
```

## Common Pitfalls

1. **Using `className` without `<Tailwind>` wrapper** — classes won't compile to inline styles.
2. **Complex CSS** — email clients strip `<style>` blocks. Use inline styles or Tailwind.
3. **Background images** — not supported in Outlook. Use `<Img>` instead.
4. **Web fonts** — limited support. Use `<Font>` component with fallbacks.
5. **`<div>` for layout** — use `<Section>`, `<Row>`, `<Column>` for table-based layout.
6. **Not testing across clients** — always preview in Gmail, Outlook, and Apple Mail.
