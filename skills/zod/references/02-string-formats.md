# String Format Validators

> Source: [zod.dev/api](https://zod.dev/api)

## Table of Contents

- [Overview](#overview)
- [Email](#email)
- [URL and HTTP URL](#url-and-http-url)
- [UUID and GUID](#uuid-and-guid)
- [IP Addresses](#ip-addresses)
- [CIDR Notation](#cidr-notation)
- [Date and Time (ISO 8601)](#date-and-time-iso-8601)
- [Other Formats](#other-formats)
- [Custom String Formats](#custom-string-formats)
- [Migration from v3](#migration-from-v3)

---

## Overview

Zod v4 promotes string format validators to **top-level functions** instead of methods on `z.string()`. Each format is a subclass of `ZodString`, so all string methods (`.min()`, `.max()`, `.trim()`, etc.) still work.

```typescript
// v4 — top-level (preferred)
z.email();
z.uuid();
z.url();

// v3 style — still works but deprecated
z.string().email();
z.string().uuid();
z.string().url();
```

## Email

Validates email addresses:

```typescript
const Email = z.email();

Email.parse("user@example.com");   // OK
Email.parse("invalid");            // throws ZodError
```

With additional constraints:

```typescript
z.email().min(5).max(255);
z.email({ error: "Invalid email address" });
```

## URL and HTTP URL

```typescript
// Any valid URL (including ftp://, data:, etc.)
z.url();
z.url().parse("https://example.com");   // OK
z.url().parse("ftp://files.example.com"); // OK

// HTTP/HTTPS URLs only
z.httpUrl();
z.httpUrl().parse("https://example.com"); // OK
z.httpUrl().parse("ftp://example.com");   // throws
```

## UUID and GUID

```typescript
// Strict RFC 9562/4122 UUID (v4 behavior)
z.uuid();
z.uuid().parse("550e8400-e29b-41d4-a716-446655440000"); // OK

// Lenient UUID-like validation (v3-compatible behavior)
z.guid();
z.guid().parse("550e8400-e29b-41d4-a716-446655440000"); // OK
```

**Important**: `z.uuid()` in v4 is stricter than `z.string().uuid()` in v3. If you need v3-compatible behavior, use `z.guid()`.

## IP Addresses

v4 splits IP validation into separate validators:

```typescript
// IPv4 only
z.ipv4();
z.ipv4().parse("192.168.1.1");     // OK
z.ipv4().parse("::1");              // throws

// IPv6 only
z.ipv6();
z.ipv6().parse("::1");              // OK
z.ipv6().parse("192.168.1.1");     // throws
```

## CIDR Notation

```typescript
// IPv4 CIDR
z.cidrv4();
z.cidrv4().parse("192.168.1.0/24");  // OK

// IPv6 CIDR
z.cidrv6();
z.cidrv6().parse("2001:db8::/32");   // OK
```

## Date and Time (ISO 8601)

ISO format validators under the `z.iso` namespace:

```typescript
// ISO date (YYYY-MM-DD)
z.iso.date();
z.iso.date().parse("2024-01-15");     // OK

// ISO time (HH:mm:ss or HH:mm:ss.SSS)
z.iso.time();
z.iso.time().parse("14:30:00");       // OK

// ISO datetime (full ISO 8601)
z.iso.datetime();
z.iso.datetime().parse("2024-01-15T14:30:00Z");         // OK
z.iso.datetime().parse("2024-01-15T14:30:00+05:30");    // OK

// ISO duration (P1Y2M3DT4H5M6S)
z.iso.duration();
z.iso.duration().parse("P1Y2M3D");    // OK
z.iso.duration().parse("PT4H5M6S");   // OK
```

## Other Formats

```typescript
// Base64
z.base64();
z.base64().parse("SGVsbG8gV29ybGQ=");  // OK

// Base64URL (no padding in v4)
z.base64url();

// JWT (JSON Web Token structure)
z.jwt();
z.jwt().parse("eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abc");

// Emoji
z.emoji();
z.emoji().parse("🎉"); // OK

// NanoID
z.nanoid();

// Hostname
z.hostname();
z.hostname().parse("example.com"); // OK

// Hash digests
z.hash("sha256");
z.hash("sha512");
z.hash("md5");
```

## Custom String Formats

Register custom format validators for reuse:

```typescript
z.stringFormat("hex-color", (val) => /^#[0-9a-fA-F]{6}$/.test(val));

// Now usable as a format
const color = z.string().check(z.stringFormat("hex-color"));
```

With Zod Mini, formats are the primary way to add string validation:

```typescript
import { z } from "zod/mini";

const Email = z.string().check(z.email);
const Url = z.string().check(z.url);
```

## Migration from v3

| v3 (deprecated) | v4 (preferred) |
|---|---|
| `z.string().email()` | `z.email()` |
| `z.string().url()` | `z.url()` |
| `z.string().uuid()` | `z.uuid()` (stricter) or `z.guid()` (lenient) |
| `z.string().ip()` | `z.ipv4()` or `z.ipv6()` |
| `z.string().cidr()` | `z.cidrv4()` or `z.cidrv6()` |
| `z.string().datetime()` | `z.iso.datetime()` |
| `z.string().date()` | `z.iso.date()` |
| `z.string().time()` | `z.iso.time()` |
| `z.string().duration()` | `z.iso.duration()` |
| `z.string().base64()` | `z.base64()` |

The v3 method syntax still works but is deprecated. Top-level functions are preferred because they return properly typed subclasses.

## Common Patterns

### Email with Normalization

```typescript
const NormalizedEmail = z.email().trim().toLowerCase();
```

### URL Validation with Domain Check

```typescript
const ApiUrl = z.httpUrl().refine(
  (url) => new URL(url).hostname.endsWith("api.example.com"),
  { error: "Must be an api.example.com URL" }
);
```

### Date Range Validation

```typescript
const FutureDate = z.iso.date().refine(
  (date) => new Date(date) > new Date(),
  { error: "Date must be in the future" }
);
```
