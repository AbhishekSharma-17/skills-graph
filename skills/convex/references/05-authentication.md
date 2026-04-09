# Authentication

> Source: [docs.convex.dev/auth](https://docs.convex.dev/auth) | convex v1.34.x

## Table of Contents

- [Auth Architecture](#auth-architecture)
- [Convex Auth (Built-in)](#convex-auth-built-in)
- [Clerk Integration](#clerk-integration)
- [Auth0 Integration](#auth0-integration)
- [WorkOS AuthKit](#workos-authkit)
- [Custom OIDC Providers](#custom-oidc-providers)
- [Authorization Patterns](#authorization-patterns)
- [Service-to-Service Auth](#service-to-service-auth)

## Auth Architecture

Convex authenticates WebSocket connections and HTTP requests using OpenID Connect (OIDC) ID tokens (JWTs). The flow:

1. Client authenticates with an identity provider (Clerk, Auth0, etc.)
2. Provider issues a JWT ID token
3. Client sends the token with Convex requests
4. Convex validates the token and makes user identity available via `ctx.auth`

## Convex Auth (Built-in)

Convex Auth is the native auth library — no external service needed:

```bash
npm install @convex-dev/auth
npx @convex-dev/auth  # Interactive setup
```

### Supported Methods

- **Social login** — GitHub, Google, Apple, etc. via OAuth
- **Email OTP** — One-time codes sent via email
- **SMS OTP** — One-time codes sent via SMS
- **Password** — Email + password authentication

### Setup

```typescript
// convex/auth.ts
import { convexAuth } from "@convex-dev/auth/server";
import GitHub from "@auth/core/providers/github";
import Google from "@auth/core/providers/google";
import { Password } from "@convex-dev/auth/providers/Password";

export const { auth, signIn, signOut, store } = convexAuth({
  providers: [GitHub, Google, Password],
});
```

```typescript
// convex/http.ts
import { httpRouter } from "convex/server";
import { auth } from "./auth";

const http = httpRouter();
auth.addHttpRoutes(http);
export default http;
```

### Client Integration (React)

```tsx
import { ConvexAuthProvider } from "@convex-dev/auth/react";
import { useAuthActions } from "@convex-dev/auth/react";

// Wrap your app
function App() {
  return (
    <ConvexAuthProvider client={convex}>
      <Router />
    </ConvexAuthProvider>
  );
}

// Sign in component
function SignIn() {
  const { signIn } = useAuthActions();

  return (
    <div>
      <button onClick={() => signIn("github")}>Sign in with GitHub</button>
      <button onClick={() => signIn("google")}>Sign in with Google</button>
    </div>
  );
}
```

### Getting the Current User

```typescript
// convex/users.ts
import { query } from "./_generated/server";
import { getAuthUserId } from "@convex-dev/auth/server";

export const currentUser = query({
  args: {},
  handler: async (ctx) => {
    const userId = await getAuthUserId(ctx);
    if (!userId) return null;
    return await ctx.db.get(userId);
  },
});
```

## Clerk Integration

```bash
npm install @clerk/clerk-react
```

### Convex Config

```typescript
// convex/auth.config.ts
export default {
  providers: [
    {
      domain: process.env.CLERK_JWT_ISSUER_DOMAIN,
      applicationID: "convex",
    },
  ],
};
```

### Client Setup

```tsx
import { ClerkProvider, useAuth } from "@clerk/clerk-react";
import { ConvexProviderWithClerk } from "convex/react-clerk";

function App() {
  return (
    <ClerkProvider publishableKey={CLERK_KEY}>
      <ConvexProviderWithClerk client={convex} useAuth={useAuth}>
        <Router />
      </ConvexProviderWithClerk>
    </ClerkProvider>
  );
}
```

## Auth0 Integration

```typescript
// convex/auth.config.ts
export default {
  providers: [
    {
      domain: "https://your-tenant.auth0.com",
      applicationID: "your-auth0-client-id",
    },
  ],
};
```

```tsx
// Client
import { Auth0Provider, useAuth0 } from "@auth0/auth0-react";
import { ConvexProviderWithAuth0 } from "convex/react-auth0";

function App() {
  return (
    <Auth0Provider domain={AUTH0_DOMAIN} clientId={AUTH0_CLIENT_ID}>
      <ConvexProviderWithAuth0 client={convex}>
        <Router />
      </ConvexProviderWithAuth0>
    </Auth0Provider>
  );
}
```

## WorkOS AuthKit

```typescript
// convex/auth.config.ts
export default {
  providers: [
    {
      domain: "https://api.workos.com",
      applicationID: "your-workos-client-id",
    },
  ],
};
```

## Custom OIDC Providers

Any OpenID Connect provider works:

```typescript
// convex/auth.config.ts
export default {
  providers: [
    {
      domain: "https://your-oidc-provider.com",
      applicationID: "your-app-id",
    },
  ],
};
```

Requirements: The provider must expose a `.well-known/openid-configuration` endpoint.

## Authorization Patterns

### Check Auth in Every Public Function

```typescript
export const createPost = mutation({
  args: { title: v.string(), body: v.string() },
  handler: async (ctx, args) => {
    const identity = await ctx.auth.getUserIdentity();
    if (!identity) {
      throw new Error("Not authenticated");
    }

    return await ctx.db.insert("posts", {
      authorId: identity.subject,
      title: args.title,
      body: args.body,
    });
  },
});
```

### Role-Based Access Control

```typescript
async function requireAdmin(ctx: QueryCtx | MutationCtx) {
  const identity = await ctx.auth.getUserIdentity();
  if (!identity) throw new Error("Not authenticated");

  const user = await ctx.db
    .query("users")
    .withIndex("by_token", (q) => q.eq("tokenIdentifier", identity.tokenIdentifier))
    .unique();

  if (!user || user.role !== "admin") {
    throw new Error("Unauthorized: admin required");
  }
  return user;
}

export const deleteUser = mutation({
  args: { userId: v.id("users") },
  handler: async (ctx, args) => {
    await requireAdmin(ctx);
    await ctx.db.delete(args.userId);
  },
});
```

### Resource-Level Authorization

```typescript
export const updatePost = mutation({
  args: { postId: v.id("posts"), body: v.string() },
  handler: async (ctx, args) => {
    const identity = await ctx.auth.getUserIdentity();
    if (!identity) throw new Error("Not authenticated");

    const post = await ctx.db.get(args.postId);
    if (!post) throw new Error("Post not found");
    if (post.authorId !== identity.subject) {
      throw new Error("Unauthorized: not the author");
    }

    await ctx.db.patch(args.postId, { body: args.body });
  },
});
```

### UserIdentity Object

```typescript
const identity = await ctx.auth.getUserIdentity();
// Returns null if not authenticated, otherwise:
{
  tokenIdentifier: string,  // Unique: "issuer|subject"
  subject: string,          // User ID from the provider
  issuer: string,           // Token issuer URL
  name?: string,
  email?: string,
  pictureUrl?: string,
  // ... other OIDC claims
}
```

## Service-to-Service Auth

For external services calling Convex HTTP endpoints without user context:

```typescript
// Set a shared secret as environment variable
// npx convex env set WEBHOOK_SECRET "your-secret"

export const webhook = httpAction(async (ctx, request) => {
  const secret = request.headers.get("x-webhook-secret");
  if (secret !== process.env.WEBHOOK_SECRET) {
    return new Response("Unauthorized", { status: 401 });
  }

  // Process webhook...
  return new Response("OK", { status: 200 });
});
```

## Related References

- HTTP actions for webhooks: `02-functions-actions-http.md`
- Best practices (access control): `11-best-practices.md`
- React client integration: `09-react-client.md`
