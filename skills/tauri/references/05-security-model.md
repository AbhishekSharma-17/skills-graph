# Tauri Security Model

> Source: https://v2.tauri.app/security/ | Version: 2.9.x

## Table of Contents

- [Security Architecture Overview](#security-architecture-overview)
- [Permissions](#permissions)
- [Capabilities](#capabilities)
- [Defining Capabilities](#defining-capabilities)
- [Scopes](#scopes)
- [Content Security Policy](#content-security-policy)
- [Remote URL Access](#remote-url-access)
- [Platform-Specific Capabilities](#platform-specific-capabilities)
- [Common Pitfalls](#common-pitfalls)

## Security Architecture Overview

Tauri v2 replaced v1's simple allowlist with a full Access Control List (ACL) system. The model has three layers:

```
Capabilities (WHO gets WHAT)
    └── Permissions (WHAT actions are allowed/denied)
        └── Scopes (WHERE those actions apply)
```

- **Permissions**: Define which commands can or cannot be executed
- **Capabilities**: Grant permissions to specific windows/webviews
- **Scopes**: Restrict the data/paths a permission applies to

By default, **nothing is allowed**. Every command requires explicit permission grants.

## Permissions

Permissions describe explicit privileges for commands. Each plugin and the core define their own permissions.

### Core Permissions

```json
// Core permissions for built-in Tauri features
"core:default"           // Safe defaults (basic window, event, menu, tray, image)
"core:event:default"     // Listen and emit events
"core:window:default"    // Basic window operations
"core:window:allow-close"
"core:window:allow-set-title"
"core:window:allow-minimize"
"core:window:allow-maximize"
"core:webview:default"   // Basic webview operations
"core:menu:default"      // Menu operations
"core:tray:default"      // System tray operations
"core:image:default"     // Image operations
"core:app:default"       // App lifecycle (name, version, exit)
"core:resources:default" // Read bundled resources
"core:path:default"      // Path resolution
```

### Plugin Permissions

```json
// File system plugin
"fs:default"              // No default access
"fs:allow-read"           // Allow reading files
"fs:allow-write"          // Allow writing files
"fs:allow-exists"         // Check file existence
"fs:allow-mkdir"          // Create directories
"fs:allow-remove"         // Delete files/dirs
"fs:read-all"             // Read from any path
"fs:write-all"            // Write to any path

// Dialog plugin
"dialog:default"          // Allow all dialog types
"dialog:allow-open"       // Open file picker
"dialog:allow-save"       // Save file picker
"dialog:allow-message"    // Message dialog

// HTTP plugin
"http:default"            // Allow HTTP requests
"http:allow-fetch"        // Allow fetch API

// Shell / Opener plugin
"opener:default"          // Open URLs/files with default app
"opener:allow-open-url"   // Open URLs in browser
"opener:allow-open-path"  // Open files with associated app
```

### Custom Command Permissions

Define permissions for your own commands in `src-tauri/permissions/`:

```json
// src-tauri/permissions/my-commands.json
{
  "identifier": "my-commands",
  "description": "Permissions for custom commands",
  "permissions": [
    {
      "identifier": "allow-greet",
      "description": "Allow the greet command",
      "commands": {
        "allow": ["greet"]
      }
    },
    {
      "identifier": "allow-admin",
      "description": "Allow admin commands",
      "commands": {
        "allow": ["delete_user", "update_config"]
      }
    }
  ]
}
```

### Permission Sets

Group permissions into reusable sets:

```json
// src-tauri/permissions/user-set.json
{
  "identifier": "user-permissions",
  "description": "Standard user permissions",
  "set": [
    "my-commands:allow-greet",
    "fs:allow-read",
    "dialog:allow-open"
  ]
}
```

## Capabilities

Capabilities bind permissions to windows/webviews. They define WHO gets WHAT.

### Default Capability

```json
// src-tauri/capabilities/default.json
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "default",
  "description": "Default capability for the main window",
  "windows": ["main"],
  "permissions": [
    "core:default",
    "opener:default",
    "my-commands:allow-greet",
    "fs:allow-read",
    "dialog:default"
  ]
}
```

### Multiple Capabilities

```json
// src-tauri/capabilities/admin.json
{
  "identifier": "admin-capability",
  "description": "Admin window with elevated permissions",
  "windows": ["admin"],
  "permissions": [
    "core:default",
    "my-commands:allow-admin",
    "fs:read-all",
    "fs:write-all"
  ]
}

// src-tauri/capabilities/settings.json
{
  "identifier": "settings-capability",
  "description": "Settings window — read-only",
  "windows": ["settings"],
  "permissions": [
    "core:default",
    "core:window:allow-close",
    "fs:allow-read"
  ]
}
```

## Defining Capabilities

### In JSON Files

Place `.json` files in `src-tauri/capabilities/`:

```json
{
  "identifier": "main-capability",
  "description": "Main window permissions",
  "windows": ["main"],
  "permissions": [
    "core:default",
    "fs:default",
    {
      "identifier": "fs:allow-read",
      "allow": [
        { "path": "$APPDATA/**" },
        { "path": "$RESOURCE/**" }
      ]
    }
  ]
}
```

### Inline in tauri.conf.json

```json
{
  "app": {
    "security": {
      "capabilities": [
        {
          "identifier": "inline-cap",
          "windows": ["main"],
          "permissions": ["core:default"]
        }
      ]
    }
  }
}
```

## Scopes

Scopes restrict WHERE a permission applies — typically file paths or URLs.

### File System Scopes

```json
{
  "identifier": "scoped-fs",
  "windows": ["main"],
  "permissions": [
    {
      "identifier": "fs:allow-read",
      "allow": [
        { "path": "$APPDATA/**" },
        { "path": "$HOME/Documents/**" },
        { "path": "$RESOURCE/**" }
      ],
      "deny": [
        { "path": "$HOME/Documents/secret/**" }
      ]
    },
    {
      "identifier": "fs:allow-write",
      "allow": [
        { "path": "$APPDATA/**" }
      ]
    }
  ]
}
```

### Path Variables

| Variable | Description |
|:---------|:------------|
| `$APPDATA` | App data directory |
| `$APPCONFIG` | App config directory |
| `$APPLOCALDATA` | App local data directory |
| `$APPLOG` | App log directory |
| `$APPCACHE` | App cache directory |
| `$HOME` | User home directory |
| `$DESKTOP` | Desktop directory |
| `$DOCUMENT` | Documents directory |
| `$DOWNLOAD` | Downloads directory |
| `$RESOURCE` | Bundled resources directory |
| `$TEMP` | Temporary directory |

### HTTP Scopes

```json
{
  "identifier": "http:allow-fetch",
  "allow": [
    { "url": "https://api.example.com/**" },
    { "url": "https://cdn.example.com/**" }
  ],
  "deny": [
    { "url": "https://api.example.com/admin/**" }
  ]
}
```

## Content Security Policy

Configure CSP in `tauri.conf.json`:

```json
{
  "app": {
    "security": {
      "csp": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' asset: http://asset.localhost; connect-src 'self' https://api.example.com"
    }
  }
}
```

### Recommended CSP

```
default-src 'self';
script-src 'self';
style-src 'self' 'unsafe-inline';
img-src 'self' asset: http://asset.localhost data:;
font-src 'self' data:;
connect-src 'self' https://your-api.com;
```

## Remote URL Access

By default, only bundled code can access Tauri APIs. To allow remote URLs:

```json
{
  "identifier": "remote-access",
  "windows": ["main"],
  "remote": {
    "urls": ["https://trusted-app.example.com/*"]
  },
  "permissions": [
    "core:event:default"
  ]
}
```

**Security warning**: Granting remote URLs access to Tauri commands is dangerous. Only do this with fully trusted domains.

## Platform-Specific Capabilities

Target capabilities to specific platforms:

```json
{
  "identifier": "desktop-capability",
  "description": "Desktop-only features",
  "windows": ["main"],
  "platforms": ["linux", "macOS", "windows"],
  "permissions": [
    "core:default",
    "global-shortcut:default",
    "core:window:allow-set-always-on-top"
  ]
}

// src-tauri/capabilities/mobile.json
{
  "identifier": "mobile-capability",
  "description": "Mobile-only features",
  "windows": ["main"],
  "platforms": ["iOS", "android"],
  "permissions": [
    "core:default",
    "barcode-scanner:default",
    "biometric:default",
    "haptics:default",
    "nfc:default"
  ]
}
```

## Common Pitfalls

- **Silent failures**: Commands without proper permissions don't error on the Rust side — they just aren't callable from the frontend
- **Overly broad scopes**: Using `fs:read-all` or `fs:write-all` defeats the purpose — always scope to specific paths
- **Missing `core:default`**: Almost every window needs `core:default` — without it, basic operations fail
- **Forgetting event permissions**: `emit()` and `listen()` require `core:event:default` in the capability
- **Remote URL security**: Granting Tauri API access to remote URLs is a major security risk — avoid unless absolutely necessary
- **Platform string case**: Use `"macOS"`, `"iOS"` (exact case) in the `platforms` array, not `"macos"` or `"ios"`
