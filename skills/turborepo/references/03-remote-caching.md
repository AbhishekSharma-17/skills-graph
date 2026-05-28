# Turborepo — Remote Caching

> Source: [turborepo.dev/docs/core-concepts/remote-caching](https://turborepo.dev/docs/core-concepts/remote-caching)

## Table of Contents

- [What Is Remote Caching](#what-is-remote-caching)
- [Vercel Remote Cache](#vercel-remote-cache)
- [Self-Hosted Remote Cache](#self-hosted-remote-cache)
- [Configuration](#configuration)
- [Team Sharing](#team-sharing)
- [Security](#security)
- [Common Pitfalls](#common-pitfalls)

## What Is Remote Caching

By default, Turborepo caches task outputs locally on disk. Remote Caching extends this by uploading cache artifacts to a shared server, allowing:

- **CI speedup** — CI runners reuse cache from previous runs instead of rebuilding everything
- **Team sharing** — One developer's build populates the cache for the whole team
- **Cross-machine** — Your laptop reuses artifacts built on CI (and vice versa)

```
Developer A builds → uploads cache → Remote Cache Server
Developer B runs same task → downloads cache → instant result

CI builds → uploads cache → Remote Cache Server
Next CI run → downloads cache → skips unchanged tasks
```

## Vercel Remote Cache

Vercel provides a free, zero-configuration remote cache service that works on all Vercel plans (including free).

### Setup

```bash
# Authenticate with Vercel
npx turbo login

# Link your monorepo to a Vercel team/project
npx turbo link
```

After linking, all `turbo run` commands automatically use the Vercel Remote Cache.

### Verify It Works

```bash
# Run a build (populates remote cache)
turbo run build

# Clear local cache
rm -rf node_modules/.cache/turbo

# Run again (should hit remote cache)
turbo run build
# Look for: "Remote cache hit" in output
```

### Disable for a Run

```bash
turbo run build --remote-only=false
```

### Unlink

```bash
npx turbo unlink
```

## Self-Hosted Remote Cache

You can host your own remote cache server if you don't want to use Vercel or need data sovereignty.

### Popular Self-Hosted Options

| Server | Language | Storage | Notes |
|--------|----------|---------|-------|
| [ducktors/turborepo-remote-cache](https://github.com/ducktors/turborepo-remote-cache) | Node.js | S3, GCS, Azure, local | Most popular community solution |
| [fox1t/turborepo-remote-cache](https://github.com/fox1t/turborepo-remote-cache) | Node.js | S3-compatible | Lightweight |
| Custom | Any | Any | Implement the Turborepo Remote Cache API |

### Self-Hosted Configuration

Since `turbo login` and `turbo link` only work with Vercel, self-hosted caches are configured via environment variables or config files.

**Option 1: Environment Variables**

```bash
export TURBO_API="https://cache.example.com"
export TURBO_TEAM="my-team"
export TURBO_TOKEN="your-auth-token"
```

**Option 2: .turbo/config.json**

Create `.turbo/config.json` in the repo root:

```json
{
  "teamId": "my-team",
  "apiUrl": "https://cache.example.com"
}
```

Then set `TURBO_TOKEN` as an environment variable (don't commit tokens).

**Option 3: CLI Flags**

```bash
turbo run build \
  --api="https://cache.example.com" \
  --team="my-team" \
  --token="your-auth-token"
```

## Configuration

### Remote Cache Behavior Flags

```bash
# Only read from remote cache, don't write
turbo run build --remote-cache-read-only

# Prefer remote cache timeout (milliseconds)
turbo run build --remote-cache-timeout=5000
```

### CI Configuration

In CI environments, set these environment variables:

```yaml
# GitHub Actions example
env:
  TURBO_TOKEN: ${{ secrets.TURBO_TOKEN }}
  TURBO_TEAM: my-team
  # For Vercel Remote Cache:
  TURBO_REMOTE_ONLY: false   # Use both local and remote
```

For Vercel-hosted projects, remote caching is automatic — no additional configuration needed.

### Selective Remote Caching

You can enable remote caching for some tasks but not others using the `--remote-cache-read-only` flag or by setting `cache: false` on tasks that shouldn't be cached at all.

## Team Sharing

### How Teams Benefit

1. **Developer A** runs `turbo run build` → builds `@repo/ui` → uploads artifact to remote cache
2. **Developer B** pulls latest code → runs `turbo run build` → `@repo/ui` hasn't changed → downloads cached artifact → instant

### Scoping by Team

Remote cache is scoped by team. All members of the same team share the same cache namespace:

```bash
# Vercel
npx turbo link   # Select your team during linking

# Self-hosted
TURBO_TEAM="frontend-team" turbo run build
```

## Security

### Token Management

- **Never commit tokens** — Use environment variables or CI secrets
- **Rotate tokens regularly** — Vercel tokens can be regenerated in the dashboard
- **Use read-only tokens for CI** where possible (Vercel supports this)

### Artifact Integrity

Enable cache signing to prevent tampering with cached artifacts:

```bash
export TURBO_REMOTE_CACHE_SIGNATURE_KEY="your-secret-key"
```

Then in `.turbo/config.json`:

```json
{
  "signature": true
}
```

This signs every artifact on upload and verifies on download. If verification fails, Turborepo treats it as a cache miss and rebuilds.

### Encryption

Vercel Remote Cache encrypts artifacts at rest and in transit. For self-hosted solutions, ensure your server uses HTTPS and encrypts stored artifacts.

## Common Pitfalls

1. **Missing TURBO_TOKEN in CI** — The most common remote cache issue. Ensure the token is available as a secret in your CI provider.

2. **Team mismatch** — Developers and CI must use the same `TURBO_TEAM` value, or they'll have separate cache namespaces.

3. **Slow network vs. rebuild** — For very fast tasks (<2 seconds), the network overhead of remote cache might make it slower. Turborepo handles this with timeouts, but it's worth noting.

4. **Large artifacts** — Caching enormous outputs (e.g., large bundles) can be slow to upload/download. Narrow your `outputs` to only what's needed.

5. **Not clearing local cache before testing remote** — To verify remote cache works, delete `node_modules/.cache/turbo` first.

## Related

- [Caching](02-caching.md) — How local caching works
- [CI/CD Integration](07-ci-cd.md) — Setting up remote cache in CI
