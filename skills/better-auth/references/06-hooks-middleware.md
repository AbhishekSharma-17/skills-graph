# Better Auth — Hooks & Middleware

> Source: [better-auth.com/docs/concepts/hooks](https://www.better-auth.com/docs/concepts/hooks) | Version: 1.5.6

## Table of Contents

- [Overview](#overview)
- [Before Hooks](#before-hooks)
- [After Hooks](#after-hooks)
- [Context Object](#context-object)
- [Response Utilities](#response-utilities)
- [Background Tasks](#background-tasks)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## Overview

Hooks intercept and customize endpoint behavior in Better Auth. They run before or after endpoint execution, enabling request validation, response modification, side effects, and custom logic without creating separate endpoints.

Use hooks for one-off customizations. For reusable logic across multiple endpoints, create a plugin instead.

## Before Hooks

Before hooks run before an endpoint executes. They can:
- Validate and modify requests
- Block execution by throwing errors
- Return early with custom responses

```typescript
import { betterAuth } from "better-auth";
import { createAuthMiddleware, APIError } from "better-auth/api";

export const auth = betterAuth({
  hooks: {
    before: createAuthMiddleware(async (ctx) => {
      // Runs before every endpoint
    }),
  },
});
```

### Restrict Email Domains

```typescript
hooks: {
  before: createAuthMiddleware(async (ctx) => {
    if (ctx.path !== "/sign-up/email") return;

    if (!ctx.body?.email.endsWith("@company.com")) {
      throw new APIError("BAD_REQUEST", {
        message: "Only company emails allowed",
      });
    }
  }),
}
```

### Modify Request Data

```typescript
hooks: {
  before: createAuthMiddleware(async (ctx) => {
    if (ctx.path === "/sign-up/email") {
      return {
        context: {
          ...ctx,
          body: {
            ...ctx.body,
            name: ctx.body.name.trim(),
          },
        },
      };
    }
  }),
}
```

### Block Specific Actions

```typescript
hooks: {
  before: createAuthMiddleware(async (ctx) => {
    if (ctx.path === "/sign-up/email") {
      throw new APIError("FORBIDDEN", {
        message: "Registration is currently disabled",
      });
    }
  }),
}
```

## After Hooks

After hooks run after an endpoint completes. They can:
- Modify responses
- Trigger side effects (notifications, logging)
- Access newly created session data

```typescript
hooks: {
  after: createAuthMiddleware(async (ctx) => {
    // Runs after every endpoint
  }),
}
```

### Send Notification on Registration

```typescript
hooks: {
  after: createAuthMiddleware(async (ctx) => {
    if (ctx.path.startsWith("/sign-up")) {
      const newSession = ctx.context.newSession;
      if (newSession) {
        await sendSlackNotification({
          type: "new-user",
          name: newSession.user.name,
          email: newSession.user.email,
        });
      }
    }
  }),
}
```

### Log Authentication Events

```typescript
hooks: {
  after: createAuthMiddleware(async (ctx) => {
    if (ctx.path.startsWith("/sign-in")) {
      const newSession = ctx.context.newSession;
      if (newSession) {
        await auditLog({
          event: "sign-in",
          userId: newSession.user.id,
          ip: ctx.headers.get("x-forwarded-for"),
          timestamp: new Date(),
        });
      }
    }
  }),
}
```

## Context Object

The `ctx` parameter provides comprehensive request/response access:

### Request Properties

| Property | Type | Description |
|----------|------|-------------|
| `ctx.path` | `string` | Current endpoint path |
| `ctx.body` | `object` | Parsed POST body |
| `ctx.headers` | `Headers` | Request headers |
| `ctx.request` | `Request?` | Request object (may be undefined for server-side calls) |
| `ctx.query` | `object` | URL query parameters |

### Auth Context Properties

| Property | Description |
|----------|-------------|
| `ctx.context.secret` | Auth instance secret for signing |
| `ctx.context.authCookies` | Predefined cookie configuration |
| `ctx.context.password` | Password utilities: `hash()`, `verify()` |
| `ctx.context.adapter` | Database adapter methods |
| `ctx.context.generateId` | ID generation function |

### After Hook Specific

| Property | Description |
|----------|-------------|
| `ctx.context.newSession` | Newly created session (if applicable) |
| `ctx.context.returned` | Response or error from the endpoint |
| `ctx.context.responseHeaders` | Headers set by previous hooks |

## Response Utilities

### JSON Response

```typescript
return ctx.json({
  message: "Custom response",
  data: { key: "value" },
});
```

### Redirect

```typescript
throw ctx.redirect("/sign-up/complete-profile");
```

### Cookie Management

```typescript
// Set a cookie
ctx.setCookies("preference", "dark-mode");

// Set a signed cookie
await ctx.setSignedCookie("secure-data", "value", ctx.context.secret, {
  maxAge: 3600,
  httpOnly: true,
});

// Read cookies
const pref = ctx.getCookies("preference");
const signed = await ctx.getSignedCookie("secure-data");
```

### Throw Errors

```typescript
throw new APIError("BAD_REQUEST", {
  message: "Invalid input",
});

throw new APIError("UNAUTHORIZED", {
  message: "Please sign in",
});

throw new APIError("FORBIDDEN", {
  message: "Insufficient permissions",
});
```

## Background Tasks

### Fire-and-Forget

Schedule operations to run after the response is sent:

```typescript
hooks: {
  after: createAuthMiddleware(async (ctx) => {
    if (ctx.context.newSession) {
      ctx.context.runInBackground(
        sendAnalyticsEvent(ctx.context.newSession.user.id)
      );
    }
  }),
}
```

### Conditional Background

Defers if a handler is configured, otherwise awaits:

```typescript
hooks: {
  after: createAuthMiddleware(async (ctx) => {
    if (ctx.context.newSession) {
      await ctx.context.runInBackgroundOrAwait(
        sendWelcomeEmail(ctx.context.newSession.user)
      );
    }
  }),
}
```

Configure background task handlers:

```typescript
export const auth = betterAuth({
  advanced: {
    backgroundTasks: {
      // Custom handler
    },
  },
});
```

## Common Patterns

### Rate Limit Specific Paths

```typescript
hooks: {
  before: createAuthMiddleware(async (ctx) => {
    if (ctx.path === "/sign-in/email") {
      const ip = ctx.headers.get("x-forwarded-for") || "unknown";
      const attempts = await getLoginAttempts(ip);
      if (attempts > 5) {
        throw new APIError("TOO_MANY_REQUESTS", {
          message: "Too many login attempts",
        });
      }
    }
  }),
}
```

### Add Custom Headers to Response

```typescript
hooks: {
  after: createAuthMiddleware(async (ctx) => {
    ctx.context.responseHeaders?.set("X-Auth-Version", "1.0");
  }),
}
```

### Conditional Logic Based on User

```typescript
hooks: {
  after: createAuthMiddleware(async (ctx) => {
    if (ctx.path === "/sign-in/email" && ctx.context.newSession) {
      const user = ctx.context.newSession.user;
      if (user.email.endsWith("@admin.com")) {
        // Set admin-specific cookies or state
      }
    }
  }),
}
```

## Common Pitfalls

1. **Forgetting `return` in before hooks** — If you don't return anything, the request proceeds unchanged. Return `{ context: ... }` to modify the request.
2. **Throwing in after hooks** — After hooks run post-execution. Throwing an error replaces the response but doesn't undo the operation.
3. **`ctx.request` may be undefined** — For server-side API calls (`auth.api.*`), there's no HTTP request object.
4. **Hooks vs plugins** — Use hooks for project-specific logic. Use plugins for reusable, shareable functionality.
5. **Blocking background tasks** — `runInBackground` is fire-and-forget. Don't await it or use its return value.
