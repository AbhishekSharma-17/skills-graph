# Credentials and Security

> Source: https://docs.n8n.io/build/understand-workflows/create-and-edit-credentials/

## Table of Contents

- [Credential Management](#credential-management)
- [Creating Credentials](#creating-credentials)
- [Credential Types](#credential-types)
- [OAuth2 Setup](#oauth2-setup)
- [Dynamic Credentials](#dynamic-credentials)
- [Domain Restrictions](#domain-restrictions)
- [End-User Credentials](#end-user-credentials)
- [Security Configuration](#security-configuration)
- [Instance-Level Security](#instance-level-security)
- [Common Pitfalls](#common-pitfalls)

## Credential Management

Credentials store authentication information for connecting workflows to external services. They are encrypted at rest and scoped to users or projects.

### Key Principles

- Credentials are **encrypted** using the instance's encryption key
- Each credential is tied to a specific **service type** (e.g., Gmail, Slack, GitHub)
- Credentials are **automatically tested** when saved
- Multiple workflows can share the same credential
- Credentials can be scoped to **personal space** or **projects** (team plans)

## Creating Credentials

### From the Credentials Page

1. Click **Create** in the side menu
2. Select credential location (personal space or project)
3. Choose the app or service
4. Enter authentication details (API key, OAuth tokens, etc.)
5. n8n tests the credential automatically on save

### From a Node

1. Open a node that requires credentials
2. Click the credential dropdown
3. Select **Create New Credential**
4. Fill in required fields
5. Save and the credential auto-attaches to the node

### Naming Conventions

Default format: `<node name> account`

Best practice: `<service> - <purpose> - <environment>`

```
Examples:
  Gmail - Marketing Notifications - Production
  Stripe - Test Mode - Development
  GitHub - CI Bot - Production
```

## Credential Types

### API Key

```
Service: OpenAI
API Key: sk-proj-...
→ Sent as Authorization header or query parameter
```

### Username/Password

```
Service: IMAP Email
Email: user@example.com
Password: ********
Host: imap.gmail.com
Port: 993
```

### OAuth2

```
Service: Google Sheets
→ Click "Connect" to initiate OAuth flow
→ Authorize in browser popup
→ Token stored and auto-refreshed
```

### Header Auth

```
Service: Custom API
Header Name: X-API-Key
Header Value: your-secret-key
```

### Custom Auth

```
Service: Custom
→ Define arbitrary headers, query params, or body fields
→ Full flexibility for non-standard APIs
```

## OAuth2 Setup

### Built-In OAuth (Recommended)

For supported services (Google, GitHub, Slack, etc.):

1. Select the credential type (e.g., Google Sheets OAuth2)
2. Click **Connect my account**
3. Authorize in the browser popup
4. Token is stored and auto-refreshed

### Custom OAuth2

For services without built-in support:

```
Grant Type: Authorization Code
Authorization URL: https://provider.com/oauth/authorize
Access Token URL: https://provider.com/oauth/token
Client ID: your-client-id
Client Secret: your-client-secret
Scope: read write
Authentication: Header | Body
```

### OAuth2 Callback URL

For self-hosted instances, configure the callback URL:

```
https://your-n8n.com/rest/oauth2-credential/callback
```

This URL must be registered in the OAuth provider's application settings.

## Dynamic Credentials

Use expressions to select or populate credentials at runtime:

### Dynamic Credential Selection

```
Credential to use: {{ $json["credentialName"] }}
→ Select from multiple stored credentials based on workflow data
```

### Dynamic Credential Values

```
API Key: {{ $json["apiKey"] }}
→ Populate credential fields from workflow data
→ Useful when credentials come from a form or external source
```

### Example: Multi-Tenant API Access

```
Form Trigger (user selects account)
  → Code node (load API key from database)
  → HTTP Request (credential field uses expression)
  → Process response
```

## Domain Restrictions

Restrict which URLs a credential can be used with in HTTP Request nodes:

### Configuration

```
Allowed HTTP Request Domains:
  All        → No restrictions (default)
  Specific   → Comma-separated list of domains
  None       → Cannot be used in HTTP Request nodes
```

### Example

```
Credential: Internal API Key
Allowed Domains: api.internal.com, staging-api.internal.com
→ Prevents credential from being sent to unauthorized URLs
```

## End-User Credentials

Enterprise feature allowing workflows to run with the triggering user's own credentials:

### Setup

```
Credential Type: End-User OAuth2
→ Each user authorizes individually
→ Workflow runs with the triggering user's token
→ Data stays private to each user
```

### Use Cases

- Multi-user form submissions that access per-user data
- Team workflows where each member's Google Drive is separate
- Customer-facing automations requiring individual authorization

## Security Configuration

### Encryption Key

```bash
# Set in environment variables — CRITICAL for production
export N8N_ENCRYPTION_KEY=your-strong-random-key

# If lost, all stored credentials become unrecoverable
# Generate a strong key:
openssl rand -hex 32
```

### Credential Encryption at Rest

- All credential data is encrypted using AES-256 with the encryption key
- Encryption happens before database storage
- Decryption occurs at runtime when the workflow executes
- Without the encryption key, credential data is unreadable

### Rotate Encryption Keys

```bash
# Export current credentials
n8n export:credentials --all --output=credentials_backup.json

# Update the encryption key
export N8N_ENCRYPTION_KEY=new-key-here

# Re-import credentials (they'll be re-encrypted with the new key)
n8n import:credentials --input=credentials_backup.json
```

## Instance-Level Security

### SSL/TLS

```bash
# Reverse proxy (recommended)
# Configure nginx/caddy in front of n8n

# Direct SSL
export N8N_SSL_KEY=/path/to/key.pem
export N8N_SSL_CERT=/path/to/cert.pem
```

### SSO (Single Sign-On)

Enterprise feature supporting SAML and LDAP:

```bash
export N8N_SSO_ENABLED=true
# Configure SAML IdP settings in the admin panel
```

### Disable Public API

```bash
export N8N_PUBLIC_API_DISABLED=true
→ Prevents external access to the n8n REST API
```

### Block Specific Nodes

```bash
export NODES_EXCLUDE='["n8n-nodes-base.executeCommand","n8n-nodes-base.readWriteFile"]'
→ Prevents use of potentially dangerous nodes
```

### SSRF Protection

```bash
export N8N_SSRF_PROTECTION_ENABLED=true
→ Blocks HTTP requests to internal/private network addresses
→ Prevents Server-Side Request Forgery attacks
```

### Security Audit

```bash
# Run the built-in security audit
n8n audit
→ Checks for common misconfigurations
→ Reports credential exposure risks
→ Identifies insecure workflow patterns
```

### Redact Execution Data

```bash
export N8N_EXECUTION_DATA_REDACT_SENSITIVE=true
→ Removes sensitive data from execution logs
→ Credentials and secrets are masked in execution history
```

## Common Pitfalls

- **Losing the encryption key** — if `N8N_ENCRYPTION_KEY` is lost, all credentials are permanently unrecoverable; back it up securely
- **OAuth callback URL mismatch** — self-hosted OAuth requires the correct callback URL registered with the provider
- **Credential sharing** — credentials are scoped to owners; explicitly share when team members need access
- **Domain restrictions** — restricting domains only affects HTTP Request nodes, not dedicated app nodes
- **Test vs production credentials** — use separate credentials for development and production environments
- **Token expiry** — n8n handles OAuth2 refresh automatically, but check if the refresh token itself has expired

## Related Topics

- HTTP Request → `06-http-request-and-apis.md`
- Error Handling → `08-error-handling.md`
- Deployment → `10-deployment-and-scaling.md`
