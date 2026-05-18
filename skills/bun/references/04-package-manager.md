# Bun — Package Manager

> Source: [bun.sh/docs/cli/install](https://bun.sh/docs/cli/install)

## Table of Contents

- [How bun install Works](#how-bun-install-works)
- [Adding and Removing Packages](#adding-and-removing-packages)
- [Lockfile Format](#lockfile-format)
- [Workspaces](#workspaces)
- [Private Registries](#private-registries)
- [Overrides and Resolutions](#overrides-and-resolutions)
- [Patching Packages](#patching-packages)
- [Lifecycle Scripts](#lifecycle-scripts)
- [Global Installs](#global-installs)
- [Package Cache and Offline Mode](#package-cache-and-offline-mode)
- [bunx — Package Runner](#bunx--package-runner)
- [Common Pitfalls](#common-pitfalls)

---

## How bun install Works

Bun's package manager is written in Zig and resolves/installs npm-compatible packages up to 25x faster than npm via hardlinks from a global cache, parallel resolution, and binary lockfile parsing.

```bash
bun install               # install from package.json
bun install --force       # clean install
bun install --dry-run     # preview without writing to disk
bun install --frozen-lockfile  # fail if bun.lock would change (CI)
```

---

## Adding and Removing Packages

```bash
# Add dependencies
bun add express
bun add zod hono drizzle-orm
bun add -d typescript @types/node    # dev dependency
bun add --peer react                 # peer dependency
bun add --optional fsevents          # optional dependency
bun add express@4.18.2 --exact       # exact version
bun add git+https://github.com/user/repo.git
bun add https://example.com/package.tgz
bun add ./packages/my-lib

# Remove
bun remove express
bun remove express lodash moment
```

### Version Ranges

```bash
bun add express@^4.18.0   # caret (compatible)
bun add express@~4.18.0   # tilde (patch-level)
bun add express@4.18.2    # exact
bun add express@latest
bun add express@next
```

---

## Lockfile Format

### bun.lock (Bun 1.2+)

Since Bun 1.2, the lockfile is a text-based, human-readable format replacing the binary `bun.lockb`:

```jsonc
// bun.lock
{
  "lockfileVersion": 1,
  "workspaces": {
    "": { "dependencies": { "express": "^4.18.2" } }
  },
  "packages": {
    "express@4.18.2": {
      "resolved": "https://registry.npmjs.org/express/-/express-4.18.2.tgz",
      "integrity": "sha512-...",
      "dependencies": { /* ... */ }
    }
  }
}
```

Commit `bun.lock` to version control. Delete `bun.lockb` after migrating to Bun 1.2+.

```bash
bun install --no-save   # skip saving the lockfile
```

---

## Workspaces

### Root package.json

```json
{
  "name": "my-monorepo",
  "private": true,
  "workspaces": ["packages/*", "apps/*"]
}
```

### Workspace Protocol

```json
{
  "name": "@myorg/web-app",
  "dependencies": {
    "@myorg/shared-utils": "workspace:*",
    "@myorg/ui-components": "workspace:^1.0.0"
  }
}
```

### Running Commands in Workspaces

```bash
bun install                              # install all workspace dependencies
bun run --filter @myorg/web-app dev      # run script in one workspace
bun run --filter '*' build               # run script in all workspaces
bun add zod --filter @myorg/shared-utils # add dep to specific workspace
```

### Structure

```
my-monorepo/
  package.json          # root with "workspaces" field
  bun.lock              # single lockfile for all workspaces
  packages/
    shared-utils/package.json
    ui-components/package.json
  apps/
    web/package.json
```

---

## Private Registries

Configure in `bunfig.toml`:

```toml
[install]
registry = "https://npm.mycompany.com/"

[install.scopes]
"@myorg" = { url = "https://npm.mycompany.com/", token = "$NPM_TOKEN" }
"@another" = { url = "https://other-registry.com/", token = "$OTHER_TOKEN" }
```

Use `$VAR_NAME` syntax for tokens — never hardcode them. Bun also reads `.npmrc` as a fallback:

```ini
# .npmrc
@myorg:registry=https://npm.mycompany.com/
//npm.mycompany.com/:_authToken=${NPM_TOKEN}
```

---

## Overrides and Resolutions

Force specific versions of transitive dependencies:

```json
{
  "overrides": {
    "lodash": "4.17.21",
    "semver": ">=7.5.4",
    "express": { "qs": "6.11.2" }
  }
}
```

Bun also supports the `resolutions` field (Yarn compatibility):

```json
{
  "resolutions": {
    "lodash": "4.17.21",
    "**/minimist": "1.2.8"
  }
}
```

---

## Patching Packages

```bash
bun patch express          # open package for editing in a temp dir
bun patch --commit express # generate patches/express@4.18.2.patch
```

After committing, Bun adds the patch to `package.json` and applies it on every `bun install`:

```json
{
  "patchedDependencies": {
    "express@4.18.2": "patches/express@4.18.2.patch"
  }
}
```

---

## Lifecycle Scripts

```json
{
  "scripts": {
    "preinstall": "echo before install",
    "postinstall": "echo after install",
    "prepublishOnly": "bun run build"
  }
}
```

Bun does not run lifecycle scripts from third-party packages by default. Allow them explicitly:

```json
{
  "trustedDependencies": ["esbuild", "sharp", "bcrypt"]
}
```

```toml
# bunfig.toml — disable all lifecycle scripts
[install]
lifecycle-scripts = false
```

---

## Global Installs

```bash
bun install -g typescript    # install globally (~/.bun/bin)
tsc --version                # run globally installed binary
ls ~/.bun/install/global/node_modules/

# Custom path
export BUN_INSTALL="/opt/bun"
```

Ensure `$BUN_INSTALL/bin` is in your `PATH`.

---

## Package Cache and Offline Mode

Packages are cached at `~/.bun/install/cache/` and hardlinked into projects.

```bash
bun pm cache rm              # clear the cache
du -sh ~/.bun/install/cache/ # view cache size

bun install --prefer-offline                          # use cache, no network
bun install --prefer-offline --frozen-lockfile        # strict offline
bun install --force                                   # bypass cache, re-download
```

---

## bunx — Package Runner

`bunx` is Bun's `npx` equivalent — auto-installs and runs packages without adding them to the project.

```bash
bunx cowsay "Hello from Bun!"
bunx create-next-app@latest my-app
bunx prisma migrate dev
bunx @biomejs/biome check ./src

# Also runs local binaries from node_modules/.bin
bunx tsc --noEmit
bunx eslint src/

# Alias
bun x cowsay "Hello!"
```

---

## Common Pitfalls

**1. Missing trustedDependencies**: Packages with native addons (sharp, bcrypt, esbuild) require `trustedDependencies`. Without it, `postinstall` silently skips, causing runtime errors.

**2. Confusing bun.lock with bun.lockb**: Bun 1.2+ uses text-based `bun.lock`. Delete `bun.lockb` and commit only `bun.lock`.

**3. Environment variables in bunfig.toml**: Use `$VAR_NAME` syntax, not `${VAR_NAME}`.

**4. Workspace resolution order**: `workspace:*` resolves the local package first. If the version doesn't satisfy a constraint like `workspace:^2.0.0`, install fails rather than falling back to the registry.

**5. Frozen lockfile in CI**: Always use `bun install --frozen-lockfile` in CI to prevent silent lockfile changes.

**6. Global PATH not configured**: After `bun install -g`, binaries go to `~/.bun/bin`. Add it to `PATH` or commands won't be found.

**7. Patches not applied**: Always use `bun patch --commit` to persist patches in `patchedDependencies`. Patches only on disk are not applied after a clean install.

---

**Related:** [00-overview.md](00-overview.md) for CLI commands, [05-bundler.md](05-bundler.md) for building projects
