# Hono — JSX & Rendering

> Source: [hono.dev/docs/guides/jsx](https://hono.dev/docs/guides/jsx)

## Overview

Hono includes a built-in JSX engine (`hono/jsx`) that works for server-side rendering without React. It supports functional components, fragments, Suspense for streaming, and client-side hydration via `hono/jsx/dom`.

## Setup

### TypeScript Configuration

```json
{
  "compilerOptions": {
    "jsx": "react-jsx",
    "jsxImportSource": "hono/jsx"
  }
}
```

Use `.tsx` file extension for files containing JSX.

### Basic JSX Response

```tsx
import { Hono } from 'hono'

const app = new Hono()

app.get('/', (c) => {
  return c.html(
    <html>
      <head><title>My App</title></head>
      <body>
        <h1>Hello Hono JSX!</h1>
      </body>
    </html>
  )
})
```

## Components

### Functional Components

```tsx
interface UserProps {
  name: string
  email: string
}

const UserCard = ({ name, email }: UserProps) => (
  <div class="card">
    <h2>{name}</h2>
    <p>{email}</p>
  </div>
)

app.get('/user', (c) => {
  return c.html(
    <UserCard name="Yusuke" email="yusuke@example.com" />
  )
})
```

### Children

```tsx
import type { FC } from 'hono/jsx'

const Layout: FC = ({ children }) => (
  <html>
    <head><title>My App</title></head>
    <body>
      <nav>Navigation</nav>
      <main>{children}</main>
      <footer>Footer</footer>
    </body>
  </html>
)

app.get('/', (c) => {
  return c.html(
    <Layout>
      <h1>Home Page</h1>
      <p>Welcome to my app</p>
    </Layout>
  )
})
```

### Fragments

```tsx
import { Fragment } from 'hono/jsx'

const ItemList = ({ items }: { items: string[] }) => (
  <>
    {items.map(item => <li>{item}</li>)}
  </>
)
```

### Async Components

Components can be async for data fetching:

```tsx
const UserList = async () => {
  const users = await db.query('SELECT * FROM users')
  return (
    <ul>
      {users.map(user => (
        <li key={user.id}>{user.name}</li>
      ))}
    </ul>
  )
}

app.get('/users', (c) => {
  return c.html(<UserList />)
})
```

## JSX Renderer Middleware

Use `jsxRenderer` for layout templating:

```tsx
import { jsxRenderer } from 'hono/jsx-renderer'

app.use(jsxRenderer(({ children, title }) => (
  <html>
    <head>
      <title>{title ?? 'Default Title'}</title>
      <link rel="stylesheet" href="/styles.css" />
    </head>
    <body>
      <header>Site Header</header>
      <main>{children}</main>
    </body>
  </html>
)))

app.get('/', (c) => {
  return c.render(
    <div>
      <h1>Home</h1>
      <p>Welcome!</p>
    </div>,
    { title: 'Home Page' }
  )
})

app.get('/about', (c) => {
  return c.render(
    <div>
      <h1>About</h1>
    </div>,
    { title: 'About Us' }
  )
})
```

## Streaming with Suspense

### SSR Streaming

Enable streaming for async components:

```tsx
import { Suspense } from 'hono/jsx'
import { renderToReadableStream } from 'hono/jsx/streaming'

const SlowComponent = async () => {
  await new Promise(r => setTimeout(r, 2000))
  return <div>Loaded after 2 seconds!</div>
}

app.get('/', (c) => {
  const stream = renderToReadableStream(
    <html>
      <body>
        <h1>Streaming SSR</h1>
        <Suspense fallback={<div>Loading...</div>}>
          <SlowComponent />
        </Suspense>
      </body>
    </html>
  )
  return c.body(stream, {
    headers: {
      'Content-Type': 'text/html; charset=UTF-8',
      'Transfer-Encoding': 'chunked',
    },
  })
})
```

### Using jsxRenderer with Streaming

```tsx
app.get('*', jsxRenderer(
  ({ children }) => (
    <html>
      <body>
        <h1>SSR Streaming</h1>
        {children}
      </body>
    </html>
  ),
  { stream: true }
))

app.get('/', (c) => {
  return c.render(
    <Suspense fallback={<div>Loading...</div>}>
      <AsyncComponent />
    </Suspense>
  )
})
```

## Client Components (hono/jsx/dom)

Hono supports client-side interactivity via `hono/jsx/dom`:

### Islands Architecture

```tsx
// components/Counter.tsx (client component)
import { useState } from 'hono/jsx'

export const Counter = () => {
  const [count, setCount] = useState(0)
  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount(count + 1)}>+1</button>
    </div>
  )
}
```

### Hooks Available

Hono's JSX supports common hooks:

| Hook | Description |
|------|-------------|
| `useState` | Component state |
| `useEffect` | Side effects |
| `useRef` | DOM references |
| `useCallback` | Memoized callbacks |
| `useMemo` | Memoized values |
| `useContext` | Context API |

## Raw HTML

Insert raw HTML strings safely:

```tsx
import { raw } from 'hono/html'

app.get('/', (c) => {
  const htmlContent = '<strong>Bold text</strong>'
  return c.html(
    <div>
      {raw(htmlContent)}
    </div>
  )
})
```

## HTML Helpers

Use the `html` tagged template literal:

```typescript
import { html } from 'hono/html'

app.get('/', (c) => {
  const name = 'Hono'
  return c.html(html`
    <html>
      <body>
        <h1>Hello ${name}!</h1>
      </body>
    </html>
  `)
})
```

## Common Pitfalls

1. **Using `className` instead of `class`** — Hono JSX uses `class`, not `className` (unlike React)
2. **Forgetting `jsxImportSource`** — Without the tsconfig setting, JSX won't compile correctly
3. **Using `.ts` extension** — JSX files must use `.tsx` extension
4. **Not streaming with async components** — Async components without streaming will block the entire response
5. **React imports** — Don't import from `react`; use `hono/jsx` for server and `hono/jsx/dom` for client
6. **Missing Content-Type for streaming** — Set `text/html; charset=UTF-8` when using `renderToReadableStream`
