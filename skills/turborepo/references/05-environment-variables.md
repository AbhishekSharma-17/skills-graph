# Turborepo — Environment Variables

> Source: [turborepo.dev/docs/crafting-your-repository/using-environment-variables](https://turborepo.dev/docs/crafting-your-repository/using-environment-variables)

## Table of Contents

- [Overview](#overview)
- [Environment Variable Keys](#environment-variable-keys)
- [Environment Modes](#environment-modes)
- [Framework Inference](#framework-inference)
- [Wildcards](#wildcards)
- [.env Files](#env-files)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## Overview

Environment variables are critical for caching correctness. If a task depends on an environment variable (e.g., `DATABASE_URL`) and that variable changes, the task should rebuild. Turborepo provides four keys to control how env vars interact with caching:

| Key | Scope | In Hash? | Available at Runtime? |
|-----|-------|----------|----------------------|
| `globalEnv` | All tasks | Yes | Yes |
| `env` | Per task | Yes | Yes |
| `globalPassThroughEnv` | All tasks | No | Yes |
| `passThroughEnv` | Per task | No | Yes |

## Environment Variable Keys

### globalEnv

Variables that affect ALL tasks. When any of these change, every task's cache is busted.

```jsonc
{
  "globalEnv": [
    "NODE_ENV",            // Production vs development
    "CI",                  // Running in CI
    "VERCEL_ENV"           // Vercel environment
  ]
}
```

**Use for:** Variables that fundamentally change how every task runs (node environment, CI flag).

### env (Per-Task)

Variables that affect a specific task. Only that task's cache is busted when these change.

```jsonc
{
  "tasks": {
    "build": {
      "env": [
        "API_URL",
        "SENTRY_DSN",
        "STRIPE_PUBLIC_KEY"
      ]
    },
    "test": {
      "env": [
        "DATABASE_URL",
        "TEST_API_KEY"
      ]
    }
  }
}
```

**Use for:** Variables that change task output (API URLs baked into builds, test database URLs).

### globalPassThroughEnv

Variables available at runtime but NOT included in the hash. Changing these won't bust cache.

```jsonc
{
  "globalPassThroughEnv": [
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_REGION"
  ]
}
```

**Use for:** Runtime credentials that don't affect build output.

### passThroughEnv (Per-Task)

Same as `globalPassThroughEnv` but scoped to a specific task:

```jsonc
{
  "tasks": {
    "deploy": {
      "passThroughEnv": [
        "DEPLOY_TOKEN",
        "DEPLOY_TARGET"
      ]
    }
  }
}
```

## Environment Modes

Turborepo has two environment modes that control which variables are available to tasks at runtime.

### Strict Mode (Default in v2)

Only variables explicitly listed in `env`, `globalEnv`, `passThroughEnv`, or `globalPassThroughEnv` are available to the task. All other variables are filtered out.

```bash
# Strict mode is default
turbo run build

# Explicitly enable
turbo run build --env-mode=strict
```

**Benefit:** Ensures caching is correct — if a task uses an unlisted variable, you'll discover it immediately because the variable won't be available.

### Loose Mode

All environment variables from the parent process are available. Variables in `env`/`globalEnv` are still included in the hash, but unlisted variables are also available (just not hashed).

```bash
turbo run build --env-mode=loose
```

**Use case:** Migration from v1 or when you can't enumerate all env vars immediately.

### Checking Which Variables Are Used

Run with `--summarize` to see which variables contributed to the hash:

```bash
turbo run build --summarize
# Check .turbo/runs/<run-id>.json for env var details
```

## Framework Inference

Turborepo automatically detects framework-specific environment variables and includes them in task hashes. This means `NEXT_PUBLIC_API_URL` is automatically considered an input for Next.js packages without you listing it in `env`.

| Framework | Pattern | Auto-Behavior |
|-----------|---------|---------------|
| Next.js | `NEXT_PUBLIC_*` | Included in hash |
| Vite | `VITE_*` | Included in hash |
| Create React App | `REACT_APP_*` | Included in hash |
| Nuxt | `NUXT_*`, `NITRO_*` | Included in hash |
| Gatsby | `GATSBY_*` | Included in hash |
| SvelteKit | `PUBLIC_*` | Included in hash |

### Opting Out of Inference

If you need to disable framework inference:

```jsonc
{
  "tasks": {
    "build": {
      "env": [
        "!NEXT_PUBLIC_*"     // Exclude all NEXT_PUBLIC_ vars from hash
      ]
    }
  }
}
```

## Wildcards

Use wildcards to match multiple environment variables with a prefix:

```jsonc
{
  "tasks": {
    "build": {
      "env": [
        "NEXT_PUBLIC_*",       // All vars starting with NEXT_PUBLIC_
        "MY_APP_*",            // Custom prefix
        "!MY_APP_DEBUG_*"      // Exclude debug vars from the match
      ]
    }
  }
}
```

## .env Files

Turborepo does NOT automatically load `.env` files. It's the framework's or dotenv's responsibility to load them. However, you should account for `.env` files as task inputs:

```jsonc
{
  "globalDependencies": [".env"],
  "tasks": {
    "build": {
      "inputs": [
        "src/**",
        ".env",
        ".env.local",
        ".env.production"
      ]
    }
  }
}
```

This ensures that changes to `.env` files cause cache misses.

## Common Patterns

### Typical Web Application

```jsonc
{
  "globalEnv": ["NODE_ENV", "CI"],
  "globalPassThroughEnv": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
  "tasks": {
    "build": {
      "env": [
        "NEXT_PUBLIC_*",
        "API_BASE_URL",
        "SENTRY_DSN"
      ]
    },
    "test": {
      "env": ["DATABASE_URL", "REDIS_URL"],
      "passThroughEnv": ["CI_JOB_ID"]
    },
    "deploy": {
      "cache": false,
      "passThroughEnv": ["DEPLOY_TOKEN", "DEPLOY_ENV"]
    }
  }
}
```

### Separating Build-Time vs Runtime Variables

```jsonc
{
  "tasks": {
    "build": {
      "env": [
        "NEXT_PUBLIC_API_URL",     // Baked into build output → hash it
        "NEXT_PUBLIC_SITE_URL"
      ],
      "passThroughEnv": [
        "DATABASE_URL"             // Server-only runtime → don't hash
      ]
    }
  }
}
```

## Common Pitfalls

1. **Not listing env vars in Strict Mode** — Your task will fail silently or behave differently because the variable is filtered out. Start in Loose Mode if migrating.

2. **Using globalEnv for per-task variables** — `DATABASE_URL` in `globalEnv` busts cache for ALL tasks, even `lint`. Use per-task `env` instead.

3. **Forgetting framework inference** — If you set `NEXT_PUBLIC_API_URL` differently in staging vs production, caching will correctly miss even without listing it in `env` — but you should still list it explicitly for clarity.

4. **Hardcoding env vars in code** — If a build reads env vars at compile time (e.g., Vite's `import.meta.env`), those vars MUST be in `env` or the build cache will be stale.

5. **Pass-through for CI-specific vars** — Variables like `GITHUB_SHA` or `CI_JOB_ID` change every run. Use `passThroughEnv` to make them available without busting cache.

## Related

- [Caching](02-caching.md) — How env vars affect cache hashing
- [Configuration](01-configuration.md) — Full turbo.json reference
- [CI/CD Integration](07-ci-cd.md) — Setting env vars in CI pipelines
