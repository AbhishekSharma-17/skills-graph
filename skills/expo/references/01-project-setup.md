# Expo — Project Setup

> Source: https://docs.expo.dev/get-started/create-a-project/ | Written for SDK 55.x

## Creating a New Project

The `create-expo-app` CLI scaffolds a new project with TypeScript and Expo Router by default.

```bash
# Default template — Expo Router, tabs, TypeScript
npx create-expo-app@latest my-app

# Choose a template
npx create-expo-app@latest my-app --template blank             # Plain JS
npx create-expo-app@latest my-app --template blank-typescript  # Plain TS
npx create-expo-app@latest my-app --template tabs              # Tab navigation
npx create-expo-app@latest my-app --template navigation        # Stack nav

# With an example (monorepo / auth / etc.)
npx create-expo-app@latest my-app -e with-router
```

The default template already enables:

- TypeScript with strict mode
- Expo Router with typed routes
- New Architecture (Fabric + TurboModules)
- Metro bundler with tree-shaking
- Tab-based layout example

## Project Structure (SDK 55+)

```
my-app/
├── app/                   # File-based routing (Expo Router)
│   ├── _layout.tsx        # Root layout
│   ├── +not-found.tsx     # 404 page
│   ├── +html.tsx          # Web-only HTML wrapper
│   └── (tabs)/            # Grouped route (no path segment)
│       ├── _layout.tsx    # Tab bar layout
│       ├── index.tsx      # /
│       └── explore.tsx    # /explore
├── assets/
│   ├── fonts/
│   └── images/            # icon.png, splash.png, adaptive-icon.png, favicon.png
├── components/            # Reusable UI
│   ├── ThemedText.tsx
│   └── ui/
├── constants/
│   └── Colors.ts
├── hooks/
│   ├── useColorScheme.ts
│   └── useThemeColor.ts
├── app.json               # Expo config (static)
├── app.config.ts          # Dynamic config (optional, overrides app.json)
├── eas.json               # EAS build/submit/update profiles
├── metro.config.js        # Metro bundler
├── babel.config.js        # Babel config
├── tsconfig.json          # TS config (extends expo/tsconfig.base)
└── package.json
```

## Dev Server

```bash
# Start Metro bundler (default port 8081)
npx expo start

# Tunnel mode (device on different network)
npx expo start --tunnel

# Clear Metro cache
npx expo start --clear

# Specific platform
npx expo start --ios
npx expo start --android
npx expo start --web

# Dev client mode (if using custom native code)
npx expo start --dev-client
```

### Keyboard shortcuts (in dev server)

| Key | Action |
|-----|--------|
| `a` | Open on Android |
| `i` | Open on iOS simulator |
| `w` | Open on web |
| `r` | Reload app |
| `j` | Open debugger |
| `m` | Toggle dev menu |
| `shift+m` | More tools (profiler, etc.) |
| `o` | Open project in editor |

## TypeScript Configuration

`tsconfig.json` extends Expo's base config:

```json
{
  "extends": "expo/tsconfig.base",
  "compilerOptions": {
    "strict": true,
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": [
    "**/*.ts",
    "**/*.tsx",
    ".expo/types/**/*.ts",
    "expo-env.d.ts"
  ]
}
```

Typed routes are auto-generated in `.expo/types/router.d.ts`. Enable them in `app.json`:

```json
{
  "expo": {
    "experiments": {
      "typedRoutes": true
    }
  }
}
```

## Installing Packages

**Always use `npx expo install`** instead of `npm install` — it installs the version pinned to your SDK.

```bash
# Safe — respects SDK version
npx expo install expo-image expo-notifications

# Verify all Expo packages are aligned
npx expo install --check

# Auto-fix version mismatches
npx expo install --fix
```

For non-Expo libraries, use `npm install` normally. Check compatibility at https://reactnative.directory.

## Environment Variables

Expo loads environment variables from `.env` files at dev time and build time.

```bash
# .env
EXPO_PUBLIC_API_URL=https://api.example.com
SUPABASE_SECRET=sk_...   # Server-only, NOT exposed
```

Only variables prefixed with `EXPO_PUBLIC_` are embedded in the JS bundle:

```tsx
const apiUrl = process.env.EXPO_PUBLIC_API_URL;
```

Per-environment files are loaded in this order (later overrides earlier):

1. `.env`
2. `.env.local`
3. `.env.development` / `.env.production`
4. `.env.development.local` / `.env.production.local`

For EAS builds, define secrets via:

```bash
eas env:create
# Enter name, value, and environment (development/preview/production)
```

## Path Aliases

Configure in `tsconfig.json` and `babel.config.js`:

```js
// babel.config.js
module.exports = function (api) {
  api.cache(true);
  return {
    presets: ['babel-preset-expo'],
    plugins: [
      ['module-resolver', {
        alias: { '@': './' },
      }],
    ],
  };
};
```

## Metro Configuration

`metro.config.js`:

```js
const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);

// Enable CSS for web
config.resolver.assetExts.push('db', 'sqlite');

// Custom transformer
config.transformer.minifierPath = 'metro-minify-terser';

module.exports = config;
```

Enable package exports (SDK 53+):

```js
config.resolver.unstable_enablePackageExports = true;
```

## Monorepo Setup

Expo supports monorepos via `node_modules` hoisting:

```js
// metro.config.js
const { getDefaultConfig } = require('expo/metro-config');
const path = require('path');

const projectRoot = __dirname;
const workspaceRoot = path.resolve(projectRoot, '../..');

const config = getDefaultConfig(projectRoot);
config.watchFolders = [workspaceRoot];
config.resolver.nodeModulesPaths = [
  path.resolve(projectRoot, 'node_modules'),
  path.resolve(workspaceRoot, 'node_modules'),
];
config.resolver.disableHierarchicalLookup = true;

module.exports = config;
```

## Running on a Device

### iOS Simulator (macOS only)

```bash
# Install Xcode from the App Store, then open once to accept license
xcode-select --install
sudo xcodebuild -runFirstLaunch

npx expo start
# Press 'i'
```

### Android Emulator

```bash
# Install Android Studio → AVD Manager → create emulator
# Start emulator first, then:
npx expo start
# Press 'a'
```

### Physical Device with Expo Go

Install Expo Go from App Store / Play Store, scan the QR code from `npx expo start`. Works only if your project has no custom native code.

### Physical Device with Dev Client

```bash
# First time: build a dev client
eas build --profile development --platform ios
# Install on device, then:
npx expo start --dev-client
# Scan QR to open in the dev client
```

## Upgrading Expo SDK

```bash
# Upgrade to latest SDK
npx expo install expo@latest --fix

# Check for config issues
npx expo-doctor

# Prebuild to regenerate native projects (if using ios/ or android/ folders)
npx expo prebuild --clean
```

Review the SDK release notes on https://blog.expo.dev for breaking changes.

## Common Pitfalls

- **Don't run `npm install` for Expo packages** — it will install versions that don't match your SDK and cause runtime crashes.
- **Don't commit `.expo/` or `.expo-shared/`** — they contain machine-local state.
- **Don't import from `expo` itself for most APIs** — import from the specific package (`import { Image } from 'expo-image'`).
- **Monorepo + dev client**: you usually need to set `projectRoot` in `eas.json` and configure `NODE_ENV` during builds.

## Related Topics

- Expo Router configuration → 02-expo-router.md
- Adding native features → 03-expo-sdk.md, 04-config-plugins.md
- Dev clients vs Expo Go → 05-dev-clients.md
- Monorepo builds → 06-eas-build.md, 12-common-patterns.md
