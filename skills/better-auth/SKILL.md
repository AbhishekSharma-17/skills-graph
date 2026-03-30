---
name: better-auth
description: "Comprehensive TypeScript authentication framework with plugins for 2FA, passkeys, organizations, and 40+ OAuth providers. MANDATORY TRIGGERS: better-auth, better auth, betterAuth, TypeScript authentication, TS auth framework. Also trigger when user wants to add authentication to a TypeScript/JavaScript app, set up social login, implement passwordless auth, configure multi-tenant organizations, add passkey/WebAuthn support, or build an auth system with session management. When in doubt about whether to use this skill for authentication tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["better-auth", "authentication", "typescript", "oauth", "passkey", "2fa", "session-management", "multi-tenant", "webauthn"]
---

# Better Auth — Skill Router

> The most comprehensive authentication framework for TypeScript — framework-agnostic, plugin-driven, database-flexible.

**Source:** [better-auth.com](https://www.better-auth.com/docs) v1.5.6 | **Package:** `better-auth` (npm) | **License:** MIT

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Setup** | `references/00-overview.md` | Getting started, installation, what Better Auth is, architecture, quickstart |
| **Server API** | `references/01-server-api.md` | Server-side auth instance, API endpoints, request/response, error handling |
| **Client SDK** | `references/02-client-sdk.md` | React/Vue/Svelte/Solid clients, hooks, session hooks, fetch options |
| **Session Management** | `references/03-session-management.md` | Sessions, cookies, caching, freshness, stateless mode, Redis integration |
| **OAuth & Social Providers** | `references/04-oauth-providers.md` | Social sign-in, account linking, 40+ providers, custom providers, tokens |
| **Database & Adapters** | `references/05-database-adapters.md` | Schema, migrations, Prisma/Drizzle/MongoDB adapters, secondary storage |
| **Hooks & Middleware** | `references/06-hooks-middleware.md` | Before/after hooks, middleware, context object, background tasks |
| **Users & Accounts** | `references/07-users-accounts.md` | Profile updates, password management, account linking, user deletion |
| **Plugin System** | `references/08-plugin-system.md` | Plugin architecture, creating plugins, endpoints, schemas, client plugins |
| **Admin & Authorization** | `references/09-admin-authorization.md` | Admin plugin, roles, permissions, banning, impersonation, RBAC |
| **Organization (Multi-Tenant)** | `references/10-organization.md` | Organizations, members, teams, invitations, access control |
| **Security Plugins** | `references/11-security-plugins.md` | 2FA/TOTP, passkeys/WebAuthn, magic link, email OTP, rate limiting |
| **Framework Integrations** | `references/12-framework-integrations.md` | Next.js, Nuxt, SvelteKit, Astro, Hono, Express, Remix, Expo |

## Installation

```bash
npm install better-auth
pnpm add better-auth
yarn add better-auth
bun add better-auth
```

## Quick Reference

- **Docs:** https://www.better-auth.com/docs
- **GitHub:** https://github.com/better-auth/better-auth
- **npm:** https://www.npmjs.com/package/better-auth
