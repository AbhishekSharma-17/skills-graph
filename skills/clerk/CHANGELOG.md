# Changelog

## [1.0.0] — 2026-06-14

**Source version tracked:** @clerk/nextjs v7.5 (Core 3)

### Added
- `00-overview.md` — What Clerk is, installation, ClerkProvider, middleware setup, project structure
- `01-authentication-strategies.md` — Email/password, OTP, magic links, passkeys, OAuth, MFA, Web3
- `02-middleware-route-protection.md` — clerkMiddleware, createRouteMatcher, role/permission guards, chaining
- `03-components.md` — SignIn, SignUp, UserButton, UserProfile, OrganizationSwitcher, Show, Protect
- `04-server-side-auth.md` — auth(), currentUser(), protect(), Route Handlers, Server Actions, clerkClient
- `05-hooks.md` — useUser, useAuth, useClerk, useSignIn, useSignUp, useSession, useOrganization, billing hooks
- `06-user-management.md` — User object, metadata (public/private/unsafe), CRUD operations, database sync
- `07-organizations.md` — Multi-tenancy, roles, permissions, invitations, verified domains, components
- `08-webhooks.md` — Event types, Svix verification, Next.js handler, database sync, retries
- `09-customization.md` — Themes, design tokens, element styles, CSS, localization, custom pages, headless
- `10-session-tokens.md` — JWT claims, getToken, custom templates, session lifetime, multi-session, M2M
- `11-enterprise-sso.md` — SAML, OIDC, EASIE protocol, IdP setup, domain config, account linking
- `12-testing.md` — Testing tokens, Playwright/Cypress integration, fake users, mocking, webhook testing

### Stats
- Routing entries: 13
- Reference files: 13
- Total lines: ~4,700
