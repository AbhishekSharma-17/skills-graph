# Clerk — Enterprise SSO

> Source: [clerk.com/docs/authentication/enterprise-connections/overview](https://clerk.com/docs/authentication/enterprise-connections/overview)

## Table of Contents

- [Overview](#overview)
- [SAML SSO](#saml-sso)
- [OIDC SSO](#oidc-sso)
- [EASIE Protocol](#easie-protocol)
- [Supported Identity Providers](#supported-identity-providers)
- [Domain Configuration](#domain-configuration)
- [Organization-Level SSO](#organization-level-sso)
- [IdP-Initiated SSO](#idp-initiated-sso)
- [Account Linking](#account-linking)
- [Security Considerations](#security-considerations)
- [Pricing](#pricing)
- [Common Patterns](#common-patterns)

## Overview

Clerk Enterprise SSO enables users to authenticate using their organization's Identity Provider (IdP) credentials — Azure AD, Okta, Google Workspace, etc. This is essential for B2B applications selling to companies with centralized identity management.

Two primary protocols:
- **SAML** — XML-based, single-tenant IdP, most enterprise-grade
- **OIDC** — JSON-based, lighter-weight, multi-tenant options available

## SAML SSO

SAML (Security Assertion Markup Language) is the most widely supported enterprise SSO protocol.

### How It Works

1. User visits your app and enters their work email
2. Clerk detects an enterprise connection for that email domain
3. User is redirected to their company's IdP (e.g., Okta)
4. User authenticates with their corporate credentials
5. IdP sends a SAML assertion back to Clerk
6. Clerk creates or updates the user session

### Configuration Steps

1. In Clerk Dashboard, go to **User & Authentication > Enterprise connections**
2. Click **Add connection** and select your IdP
3. Copy the ACS URL and Entity ID from Clerk
4. Configure the SAML app in your IdP:
   - Set the ACS (Assertion Consumer Service) URL
   - Set the Entity ID (Audience URI)
   - Map user attributes (email, firstName, lastName)
5. Copy the IdP metadata URL or upload the XML certificate
6. Paste into Clerk and activate the connection

### Attribute Mapping

Standard SAML attributes Clerk expects:

| Clerk Attribute | Common IdP Attribute |
|----------------|---------------------|
| `email` | `user.email`, `emailAddress` |
| `firstName` | `user.firstName`, `givenName` |
| `lastName` | `user.lastName`, `surname` |

## OIDC SSO

OpenID Connect provides a lighter-weight alternative to SAML:

### Configuration Steps

1. In Clerk Dashboard, add an OIDC enterprise connection
2. In your IdP, register a new OIDC application:
   - Set the redirect URI from Clerk
   - Note the client ID and client secret
3. In Clerk, provide:
   - Discovery URL (`.well-known/openid-configuration`)
   - Client ID and Client Secret
   - Scopes (typically `openid profile email`)

### Custom OIDC Providers

Any OIDC-compatible provider works:
- Keycloak
- Auth0 (as an IdP)
- OneLogin
- PingFederate
- Custom OIDC servers

## EASIE Protocol

EASIE (Easy Authentication and Security for Internet Enterprises) is Clerk's streamlined approach using multi-tenant OpenID providers:

**Supported providers:**
- Google Workspace
- Microsoft Entra ID (Azure AD)

**How it differs from SAML:**
- Multi-tenant infrastructure (shared IdP endpoints)
- Simpler setup — no per-tenant IdP configuration
- Automatic deprovisioning (up to 10-minute delay)
- Only supports one identifier per connection

**Trade-off:** EASIE is faster to set up but uses shared multi-tenant infrastructure. Organizations requiring strict single-tenant isolation should use SAML.

### Automatic Deprovisioning

EASIE connections automatically check if users are still active in their IdP. When a user is suspended or deleted from their corporate directory:
- Their Clerk session is revoked (within ~10 minutes)
- They can't create new sessions
- No manual intervention needed

## Supported Identity Providers

### First-Party SAML Support
- **Microsoft Azure AD / Entra ID** — Step-by-step guide in Clerk docs
- **Google Workspace** — SAML app configuration
- **Okta Workforce** — SAML 2.0 integration
- **Custom SAML** — Any SAML 2.0 compliant IdP

### EASIE Support
- Google Workspace
- Microsoft Entra ID

### Custom OIDC
- Any OIDC-compliant provider

## Domain Configuration

Enterprise connections are scoped to email domains:

**Exact domain matching (default):**
- Connection for `acme.com` → only `user@acme.com` addresses match

**Subdomain support:**
- Enable in Advanced settings
- Connection domain must be an eTLD+1 (e.g., `acme.com`)
- Matches `user@subdomain.acme.com`, `user@eu.acme.com`, etc.

**Multiple domains:**
- Create separate connections for each domain
- Or use verified domains with subdomain support

## Organization-Level SSO

Enterprise connections can be tied to specific organizations:

```
Organization "Acme Corp"
├── Enterprise Connection: SAML (acme.com)
├── Members auto-provisioned on first SSO login
└── Role: org:member (default for SSO users)
```

When a user signs in via enterprise SSO:
1. They're automatically added to the linked organization
2. Assigned a default role (configurable)
3. Their profile is populated from IdP attributes

## IdP-Initiated SSO

SAML supports IdP-initiated flows where users start from their IdP dashboard (e.g., Okta dashboard tile):

1. User clicks the app tile in their IdP
2. IdP sends a SAML assertion directly to Clerk
3. Clerk creates a session and redirects to your app

**Note:** IdP-initiated SSO is only supported for SAML connections, not OIDC or EASIE.

## Account Linking

When enterprise SSO users have existing accounts:

- If a user with the same email already exists, the enterprise connection is linked to the existing account
- User retains their existing data, metadata, and org memberships
- Previous sign-in methods (password, social) remain available alongside SSO

## Security Considerations

**SAML vs EASIE security:**
- SAML uses single-tenant IdP infrastructure — stronger tenant isolation
- EASIE uses multi-tenant IdP — simpler but shared infrastructure
- For regulated industries (healthcare, finance), prefer SAML

**Additional MFA:**
- Clerk can require additional MFA factors after IdP authentication
- Configure in **User & Authentication > Multi-factor**
- Common pattern: IdP handles primary auth, Clerk adds TOTP as second factor

**Native app security:**
- Security-critical nonces are passed only to allowlisted URLs
- Production apps must register custom redirect URLs in the Dashboard or via Backend API

## Pricing

- **Development:** 25 free enterprise connections per instance
- **Production:** Requires Pro or Business plan
- Enterprise connections count as a separate feature tier

## Common Patterns

**B2B SaaS with enterprise SSO:**
```
Sign-up flow:
1. User enters work email (e.g., user@enterprise.com)
2. Clerk checks for enterprise connection
3. If found → redirect to IdP
4. If not found → email/password or social login
5. After auth → create org membership
```

**Mixed auth (SSO + social):**
- Enterprise users: SAML SSO via their IdP
- Individual users: Google OAuth or email/password
- Both coexist — Clerk routes based on email domain

**Just-in-time provisioning:**
- No need to pre-create user accounts
- User is created on first SSO login
- Profile populated from IdP attributes
- Org membership created automatically
