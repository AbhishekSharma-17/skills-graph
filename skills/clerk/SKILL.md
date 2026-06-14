---
name: clerk
description: "Clerk authentication and user management for React and Next.js — sign-in/sign-up flows, middleware route protection, organizations, webhooks, session tokens, and enterprise SSO. MANDATORY TRIGGERS: clerk, Clerk, @clerk/nextjs, @clerk/clerk-react, ClerkProvider, clerkMiddleware, SignIn, SignUp, UserButton, useUser, useAuth, auth(), currentUser(), createRouteMatcher. Also trigger when user wants to add authentication to a Next.js or React app, protect routes with middleware, implement social login or OAuth, set up multi-tenant organizations, handle auth webhooks, customize sign-in UI, or integrate enterprise SSO (SAML/OIDC). When in doubt about whether to use this skill for authentication tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["clerk", "authentication", "nextjs", "react", "auth", "middleware", "organizations", "sso", "webhooks", "user-management"]
---

# Clerk — Skill Router

> Authentication and user management for modern web applications.

**Source:** [clerk.com/docs](https://clerk.com/docs) | **Package:** `@clerk/nextjs` v7.5 (Core 3) | **License:** MIT

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Setup** | `references/00-overview.md` | Getting started, installation, ClerkProvider, environment variables |
| **Authentication Strategies** | `references/01-authentication-strategies.md` | Email/password, magic links, OTP, passkeys, social OAuth, MFA |
| **Middleware & Route Protection** | `references/02-middleware-route-protection.md` | clerkMiddleware, createRouteMatcher, protecting routes, public routes |
| **Prebuilt Components** | `references/03-components.md` | SignIn, SignUp, UserButton, UserProfile, OrganizationSwitcher, Show |
| **Server-Side Auth** | `references/04-server-side-auth.md` | auth(), currentUser(), protect(), Route Handlers, Server Actions |
| **Client Hooks** | `references/05-hooks.md` | useUser, useAuth, useClerk, useSignIn, useSignUp, useSession, useOrganization |
| **User Management** | `references/06-user-management.md` | User object, metadata, CRUD via clerkClient, Backend API |
| **Organizations** | `references/07-organizations.md` | Multi-tenancy, roles, permissions, invitations, verified domains |
| **Webhooks** | `references/08-webhooks.md` | Event types, Svix verification, endpoint setup, handling events |
| **Customization** | `references/09-customization.md` | Themes, appearance prop, CSS variables, localization, custom pages |
| **Session & Token Management** | `references/10-session-tokens.md` | JWT claims, getToken, cross-origin requests, session lifetime, multi-session |
| **Enterprise SSO** | `references/11-enterprise-sso.md` | SAML, OIDC, EASIE, verified domains, IdP configuration |
| **Testing & Development** | `references/12-testing.md` | Testing tokens, Playwright/Cypress integration, mock auth, E2E testing |

## Installation

```bash
# CLI setup (recommended)
npm install -g clerk
clerk auth login
clerk init

# Manual setup
npm install @clerk/nextjs

# React (non-Next.js)
npm install @clerk/clerk-react
```

## Quick Reference

- [Clerk Docs](https://clerk.com/docs)
- [Next.js Quickstart](https://clerk.com/docs/nextjs/getting-started/quickstart)
- [API Reference](https://clerk.com/docs/reference/nextjs/overview)
- [GitHub](https://github.com/clerk/javascript)
- [Changelog](https://clerk.com/changelog)
