# Audit Report — Clerk Skill

**Date:** 2026-06-14
**Skill Version:** 1.0.0
**Source Tracked:** @clerk/nextjs v7.5 (Core 3)

## Quality Scores

| Category | Score (1-5) | Notes |
|----------|:-----------:|-------|
| **Architecture** | 5 | Clean router + 13 leaf nodes, no file >500 lines, all focused |
| **Content Quality** | 5 | Practical code examples, tables, runnable snippets throughout |
| **Completeness** | 4 | Covers all core features; billing hooks mentioned but not deeply covered |
| **Maintainability** | 5 | VERSION.json tracks all references, check-updates.py validates integrity |
| **Trigger Quality** | 5 | MANDATORY TRIGGERS cover all key imports and common user intents |

## Coverage Analysis

### Fully Covered
- Next.js App Router integration (ClerkProvider, middleware, auth())
- Authentication strategies (email, OAuth, passkeys, MFA)
- Prebuilt components (SignIn, SignUp, UserButton, OrganizationSwitcher)
- Server-side auth (auth(), currentUser(), protect())
- Client hooks (useUser, useAuth, useClerk, useSignIn, useSignUp)
- User management (CRUD, metadata, database sync)
- Organizations (multi-tenancy, roles, permissions, invitations)
- Webhooks (setup, verification, handler patterns)
- Customization (themes, variables, elements, CSS, localization)
- Session tokens (JWT, getToken, custom templates, cross-origin)
- Enterprise SSO (SAML, OIDC, EASIE)
- Testing (testing tokens, Playwright, Cypress, mocking)

### Partially Covered
- Billing hooks (listed but not deeply documented — feature is relatively new)
- Pages Router patterns (covered in server-side auth but not primary focus)
- Non-Next.js frameworks (React, Vue, Astro mentioned but not deeply covered)

### Not Covered (Intentionally)
- Clerk Dashboard UI walkthrough (changes frequently, better served by docs)
- Pricing details (changes frequently)
- Individual OAuth provider setup (20+ providers, each with its own guide)

## Recommendations for v1.1
1. Add deeper Clerk Billing / subscription management reference when feature matures
2. Consider React-only reference for non-Next.js projects
3. Add Clerk + Supabase / Clerk + Convex integration patterns
