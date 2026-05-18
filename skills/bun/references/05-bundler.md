# Bun — Bundler

> Source: [bun.sh/docs/bundler](https://bun.sh/docs/bundler)

## Table of Contents

- [Bun.build() API](#bunbuild-api)
- [CLI Usage](#cli-usage)
- [Target Environments](#target-environments)
- [Output Formats](#output-formats)
- [Code Splitting](#code-splitting)
- [Tree Shaking](#tree-shaking)
- [Minification](#minification)
- [Source Maps](#source-maps)
- [Loaders](#loaders)
- [Plugins API](#plugins-api)
- [External Packages](#external-packages)
- [Define and Environment Variables](#define-and-environment-variables)
- [CSS Bundling](#css-bundling)
- [HTML Entrypoints](#html-entrypoints)
- [Common Pitfalls](#common-pitfalls)

---

## Bun.build() API

```typescript
const result = await Bun.build({
  entrypoints: ["./src/index.ts"],
  outdir: "./dist",
  target: "browser",           // "browser" | "bun" | "node"
  format: "esm",               // "esm" | "cjs" | "iife"
  splitting: true,
  minify: true,
  sourcemap: "external",       // "external" | "inline" | "none"
  root: "./src",
  naming: {
    entry: "[dir]/[name].[hash].[ext]",
    chunk: "[name]-[hash].[ext]",
    asset: "[name]-[hash].[ext]",
  },
  publicPath: "/assets/",
  external: ["lightningcss"],
  define: { "process.env.NODE_ENV": JSON.stringify("production") },
  loader: { ".svg": "file", ".txt": "text" },
  plugins: [myPlugin],
});

if (!result.success) {
  for (const log of result.logs) console.error(log);
  process.exit(1);
}
```

### BuildArtifact Properties

Each output extends `Blob`:

```typescript
for (const artifact of result.outputs) {
  artifact.path;    // absolute path
  artifact.size;    // bytes
  artifact.type;    // MIME type
  artifact.kind;    // "entry-point" | "chunk" | "asset" | "sourcemap"
  artifact.hash;    // content hash
  artifact.loader;  // loader that produced this output

  const text = await artifact.text();
  const bytes = await artifact.bytes();
}
```

---

## CLI Usage

```bash
bun build ./src/index.ts --outdir ./dist
bun build ./src/index.ts ./src/worker.ts --outdir ./dist

bun build ./src/index.ts \
  --outdir ./dist \
  --target browser \
  --splitting \
  --minify \
  --sourcemap=external

bun build ./src/index.ts          # stdout (no outdir)
bun build ./src/cli.ts --compile --outfile ./myapp  # standalone executable
```

### CLI Flags Reference

| Flag | Description |
|------|-------------|
| `--outdir` | Output directory |
| `--outfile` | Output file (single entrypoint) |
| `--target` | Target environment |
| `--format` | Output format (esm, cjs, iife) |
| `--splitting` | Enable code splitting |
| `--minify` | Minify all |
| `--minify-whitespace` | Whitespace only |
| `--minify-syntax` | Syntax only |
| `--minify-identifiers` | Identifiers only |
| `--sourcemap` | Source map mode |
| `--external` | Mark packages as external |
| `--define` | Compile-time constants |
| `--loader` | Custom file loaders |
| `--compile` | Create standalone executable |

---

## Target Environments

```typescript
// browser (default) — web browsers, removes server-only code
await Bun.build({ entrypoints: ["./src/app.ts"], outdir: "./dist", target: "browser" });

// bun — preserves Bun-specific APIs (Bun.file, Bun.serve, Bun.$)
await Bun.build({ entrypoints: ["./src/server.ts"], outdir: "./dist", target: "bun" });

// node — preserves Node.js built-ins, CommonJS compatibility
await Bun.build({ entrypoints: ["./src/index.ts"], outdir: "./dist", target: "node", format: "cjs" });
```

---

## Output Formats

```typescript
// ESM (default) — import/export syntax
await Bun.build({ entrypoints: ["./src/index.ts"], outdir: "./dist", format: "esm" });

// CommonJS — require/module.exports
await Bun.build({ entrypoints: ["./src/index.ts"], outdir: "./dist", format: "cjs" });

// IIFE — for <script> tags without module systems
await Bun.build({ entrypoints: ["./src/index.ts"], outdir: "./dist", format: "iife" });
```

---

## Code Splitting

Shared code between entrypoints is extracted into chunks. Requires `format: "esm"`.

```typescript
await Bun.build({
  entrypoints: ["./src/page-home.ts", "./src/page-about.ts"],
  outdir: "./dist",
  splitting: true,
});
```

Dynamic imports are also split automatically:

```typescript
const module = await import("./heavy-module.ts");
```

---

## Tree Shaking

Dead code elimination is automatic. Unused exports are removed.

```typescript
// utils.ts
export function usedFunction() { return "used"; }
export function unusedFunction() { return "unused"; } // removed from bundle
```

Mark packages as side-effect-free for more aggressive shaking:

```json
{ "sideEffects": false }
```

Or specify which files have side effects:

```json
{ "sideEffects": ["./src/polyfills.ts", "*.css"] }
```

---

## Minification

```typescript
// Full minification
await Bun.build({ entrypoints: ["./src/index.ts"], outdir: "./dist", minify: true });

// Granular control
await Bun.build({
  entrypoints: ["./src/index.ts"],
  outdir: "./dist",
  minify: {
    whitespace: true,    // remove spaces/newlines
    syntax: true,        // shorten expressions (true → !0)
    identifiers: true,   // mangle variable names
  },
});
```

```bash
bun build ./src/index.ts --outdir ./dist --minify
bun build ./src/index.ts --outdir ./dist --minify-whitespace --minify-syntax
```

---

## Source Maps

```typescript
await Bun.build({ entrypoints: ["./src/index.ts"], outdir: "./dist", sourcemap: "external" });
```

| Value | Behavior |
|-------|----------|
| `"none"` | No source maps (default) |
| `"external"` | Separate `.map` files alongside output |
| `"inline"` | Embedded as base64 data URL in output |

---

## Loaders

### Built-in Loaders

| Loader | Extensions | Output |
|--------|-----------|--------|
| `js` | `.js`, `.mjs`, `.cjs` | JavaScript |
| `ts` | `.ts`, `.mts`, `.cts` | TypeScript (stripped) |
| `tsx` | `.tsx` | TypeScript + JSX |
| `jsx` | `.jsx` | JSX |
| `json` | `.json` | JSON (inlined) |
| `toml` | `.toml` | TOML (inlined as object) |
| `css` | `.css` | CSS |
| `text` | `.txt` | String import |
| `file` | Any | Copied to outdir, returns URL |
| `wasm` | `.wasm` | WebAssembly |

### Custom Loader Mapping

```typescript
await Bun.build({
  entrypoints: ["./src/index.ts"],
  outdir: "./dist",
  loader: {
    ".svg": "file",    // import returns URL path
    ".txt": "text",    // import returns string contents
    ".data": "json",   // parse as JSON
  },
});
```

```typescript
import logo from "./logo.svg";     // "/assets/logo-abc123.svg"
import readme from "./README.txt"; // "This is the readme content..."
import config from "./config.json"; // { key: "value" }
```

---

## Plugins API

```typescript
import type { BunPlugin } from "bun";

const envPlugin: BunPlugin = {
  name: "env-loader",
  setup(build) {
    build.onResolve({ filter: /^env$/ }, (args) => ({
      path: args.path, namespace: "env",
    }));

    build.onLoad({ filter: /.*/, namespace: "env" }, () => ({
      contents: `export default ${JSON.stringify(Bun.env)}`,
      loader: "js",
    }));
  },
};

await Bun.build({ entrypoints: ["./src/index.ts"], outdir: "./dist", plugins: [envPlugin] });
```

### YAML Plugin Example (onResolve + onLoad)

```typescript
build.onResolve({ filter: /\.yaml$/ }, (args) => ({
  path: args.path, namespace: "yaml-ns",
}));

build.onLoad({ filter: /\.yaml$/, namespace: "yaml-ns" }, async (args) => {
  const text = await Bun.file(args.path).text();
  return { contents: `export default ${JSON.stringify(parseYAML(text))}`, loader: "js" };
});
```

### Runtime Plugin (via bunfig.toml preload)

```typescript
// preload.ts
Bun.plugin({
  name: "yaml-runtime",
  setup(build) {
    build.onLoad({ filter: /\.yaml$/ }, async (args) => {
      const text = await Bun.file(args.path).text();
      return { contents: `export default ${JSON.stringify(parseYAML(text))}`, loader: "js" };
    });
  },
});
```

```toml
# bunfig.toml
preload = ["./preload.ts"]
```

---

## External Packages

Exclude packages from the bundle — they remain as `import` statements in output.

```typescript
await Bun.build({
  entrypoints: ["./src/index.ts"],
  outdir: "./dist",
  external: ["express", "lightningcss", "@aws-sdk/*"],
});
```

```bash
bun build ./src/index.ts --outdir ./dist --external express --external lightningcss
```

Use external for native addons (`.node` files), runtime-available deps, and packages with dynamic requires.

---

## Define and Environment Variables

Replace identifiers with constant values at compile time:

```typescript
await Bun.build({
  entrypoints: ["./src/index.ts"],
  outdir: "./dist",
  define: {
    "process.env.NODE_ENV": JSON.stringify("production"),
    "API_URL": JSON.stringify("https://api.example.com"),
    "__DEV__": "false",
  },
});
```

```typescript
// Source
if (process.env.NODE_ENV === "production") { enableAnalytics(); }
// After define
if ("production" === "production") { enableAnalytics(); }
// After tree shaking (dead branch removed)
enableAnalytics();
```

Always use `JSON.stringify()` to produce quoted string values in `define`.

---

## CSS Bundling

```typescript
// CSS as entrypoint
await Bun.build({ entrypoints: ["./src/styles.css"], outdir: "./dist", minify: true });

// CSS imported from JS — extracted into separate file
import "./styles.css";  // produces a separate CSS output
```

The bundler resolves `@import` statements and produces a single CSS output.

---

## HTML Entrypoints

```bash
bun build ./index.html --outdir ./dist
```

```html
<!DOCTYPE html>
<html>
<head>
  <link rel="stylesheet" href="./src/styles.css">
</head>
<body>
  <div id="app"></div>
  <script type="module" src="./src/index.ts"></script>
</body>
</html>
```

Bun parses the HTML, bundles all discovered scripts and styles, and produces an updated HTML file with correct references.

```typescript
await Bun.build({ entrypoints: ["./index.html"], outdir: "./dist", minify: true });
```

---

## Common Pitfalls

**1. Code splitting requires ESM**: `splitting: true` with `format: "cjs"` or `"iife"` silently disables splitting. Always use `format: "esm"` when splitting.

**2. Missing external for native addons**: Packages with `.node` binaries (sharp, better-sqlite3, bcrypt) must be in `external`. Bundling them produces runtime errors.

**3. define values must be expressions**: Values in `define` are JS expression strings. Use `JSON.stringify("production")` not `"production"`, or output will be an unquoted identifier.

**4. Plugins registered in bunfig.toml vs Bun.build**: Runtime plugins (`Bun.plugin()` in a preload file) only apply to `bun run`. Build plugins (passed to `Bun.build({ plugins })`) only apply to bundling. They are separate systems.

**5. CSS not extracted automatically**: CSS imports only produce separate files when bundling JS entrypoints. For standalone CSS output, add the CSS file as its own entrypoint.

**6. Source maps in production**: `sourcemap: "inline"` exposes source code to end users. Use `"external"` and serve source maps only to your error tracking service.

**7. Tree shaking and side effects**: If expected code is removed, the module likely has undeclared side effects. Add `"sideEffects"` to the library's `package.json` or restructure imports.

---

**Related:** [04-package-manager.md](04-package-manager.md) for managing dependencies, [12-frontend-dev.md](12-frontend-dev.md) for the dev server
