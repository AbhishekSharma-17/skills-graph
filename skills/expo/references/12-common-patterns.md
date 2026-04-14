# Expo — Common Patterns & Best Practices

> Source: https://docs.expo.dev/ | Written for SDK 55.x

## Table of Contents

- [Project Structure](#project-structure)
- [Environment Variants (Dev/Preview/Prod)](#environment-variants-devpreviewprod)
- [Monorepo Setup](#monorepo-setup)
- [Testing](#testing)
- [CI/CD Pipelines](#cicd-pipelines)
- [Upgrading Expo SDK](#upgrading-expo-sdk)
- [Migration from Bare React Native](#migration-from-bare-react-native)
- [Performance Optimization](#performance-optimization)
- [Error Tracking](#error-tracking)
- [Analytics](#analytics)
- [App Store Compliance](#app-store-compliance)

## Project Structure

A scalable Expo project layout:

```
my-app/
├── app/                    # Routes (Expo Router)
├── components/             # Reusable UI
│   ├── ui/                 # Primitives (Button, Card, Input)
│   └── features/           # Domain components
├── lib/                    # Business logic
│   ├── api.ts              # API client
│   ├── auth.tsx            # Auth context
│   ├── storage.ts          # Secure store wrappers
│   └── utils.ts
├── hooks/                  # Custom hooks
├── constants/              # Colors, sizes, config
├── types/                  # Shared TS types
├── assets/
│   ├── fonts/
│   └── images/
├── plugins/                # Custom config plugins
├── scripts/                # One-off scripts (generate icons, etc.)
├── app.json / app.config.ts
├── eas.json
└── package.json
```

## Environment Variants (Dev/Preview/Prod)

Install `app.config.ts` approach → 04-config-plugins.md.

Key principles:

1. **Different bundle IDs per env** so you can side-install:
   ```
   com.example.myapp.dev     (development)
   com.example.myapp.preview (staging)
   com.example.myapp         (production)
   ```

2. **Different names/icons per env** for visual differentiation.

3. **Environment-specific API URLs and keys** via `EXPO_PUBLIC_*` env vars.

4. **Separate EAS Update channels** (`development`, `preview`, `production`) so staging hotfixes don't leak to production.

Full recipe:

```ts
// app.config.ts
import { ExpoConfig, ConfigContext } from 'expo/config';

const VARIANT = process.env.APP_VARIANT ?? 'development';
const isDev = VARIANT === 'development';
const isPreview = VARIANT === 'preview';
const isProd = VARIANT === 'production';

const bundleId = isProd
  ? 'com.example.myapp'
  : isPreview
  ? 'com.example.myapp.preview'
  : 'com.example.myapp.dev';

export default ({ config }: ConfigContext): ExpoConfig => ({
  ...config,
  name: isProd ? 'MyApp' : isPreview ? 'MyApp Preview' : 'MyApp Dev',
  slug: 'my-app',
  icon: isDev ? './assets/icon-dev.png' : './assets/icon.png',
  ios: { ...config.ios, bundleIdentifier: bundleId },
  android: { ...config.android, package: bundleId },
  extra: {
    apiUrl: process.env.EXPO_PUBLIC_API_URL,
    variant: VARIANT,
    eas: { projectId: 'xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx' },
  },
});
```

```json
// eas.json
{
  "build": {
    "development": { "env": { "APP_VARIANT": "development" }, "channel": "development" },
    "preview":     { "env": { "APP_VARIANT": "preview" },     "channel": "preview"     },
    "production":  { "env": { "APP_VARIANT": "production" },  "channel": "production"  }
  }
}
```

## Monorepo Setup

Recommended with pnpm or Yarn workspaces for sharing code across mobile + web.

```
my-workspace/
├── apps/
│   ├── mobile/    # Expo app
│   └── web/       # Next.js
├── packages/
│   ├── ui/        # Shared components (web-compatible)
│   └── types/     # Shared TS types
└── package.json   # workspaces: ["apps/*", "packages/*"]
```

Configure Metro for monorepo (see 01-project-setup.md). In `eas.json`, set the root:

```json
{
  "cli": { "appVersionSource": "remote", "requireCommit": true },
  "build": {
    "production": {
      "cache": { "paths": ["../../node_modules"] }
    }
  }
}
```

EAS auto-detects workspaces. If you see "Missing workspace root", set `EAS_PROJECT_ROOT=apps/mobile` env var.

## Testing

### Unit tests with Jest

```bash
npx expo install jest jest-expo @testing-library/react-native
```

`jest.config.js`:

```js
module.exports = {
  preset: 'jest-expo',
  transformIgnorePatterns: [
    'node_modules/(?!(jest-)?react-native|@react-native|expo(nent)?|@expo(nent)?/.*|react-clone-referenced-element|@react-navigation)',
  ],
};
```

```tsx
// __tests__/Counter.test.tsx
import { render, fireEvent } from '@testing-library/react-native';
import Counter from '../components/Counter';

test('increments on press', () => {
  const { getByText } = render(<Counter />);
  fireEvent.press(getByText('+'));
  expect(getByText('1')).toBeTruthy();
});
```

### E2E with Maestro

```bash
# Install Maestro CLI
curl -Ls "https://get.maestro.mobile.dev" | bash
```

```yaml
# flows/login.yaml
appId: com.example.myapp
---
- launchApp
- tapOn: "Login"
- inputText: "test@example.com"
- tapOn: "Next"
- inputText: "password"
- tapOn: "Sign in"
- assertVisible: "Welcome"
```

Run:

```bash
maestro test flows/login.yaml
```

Integrates with EAS Build:

```bash
eas build --profile preview --platform android
maestro test flows/ --apk <downloaded-apk>
```

### Detox (alternative)

More mature but heavier setup. Works great for complex flows.

## CI/CD Pipelines

### GitHub Actions — full release workflow

```yaml
name: Release
on:
  push:
    tags: ['v*']

jobs:
  build-and-submit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: npm }
      - uses: expo/expo-github-action@v8
        with: { eas-version: latest, token: ${{ secrets.EXPO_TOKEN }} }
      - run: npm ci
      - run: npm test
      - run: eas build --profile production --platform all --non-interactive --auto-submit

  publish-update:
    if: startsWith(github.ref, 'refs/heads/main')
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: expo/expo-github-action@v8
        with: { eas-version: latest, token: ${{ secrets.EXPO_TOKEN }} }
      - run: npm ci
      - run: eas update --branch main --message "${{ github.event.head_commit.message }}"
```

### Preview deploys per PR

```yaml
name: Preview
on: pull_request

jobs:
  preview:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: expo/expo-github-action@v8
        with: { token: ${{ secrets.EXPO_TOKEN }} }
      - run: npm ci
      - run: eas update --branch pr-${{ github.event.number }} --message "${{ github.event.pull_request.title }}"
      - uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '🚀 Preview: `pr-${{ github.event.number }}` branch published. Switch channel in dev client to test.',
            });
```

## Upgrading Expo SDK

1. Read the [SDK changelog](https://blog.expo.dev) for breaking changes.
2. Upgrade the core package:
   ```bash
   npx expo install expo@latest --fix
   ```
3. Check for misaligned dependencies:
   ```bash
   npx expo install --check
   npx expo-doctor
   ```
4. If you have an `ios/` or `android/` folder, regenerate:
   ```bash
   npx expo prebuild --clean
   ```
5. Rebuild a dev client:
   ```bash
   eas build --profile development --platform all
   ```
6. Test thoroughly (SDK upgrades often touch New Architecture compat).
7. Release a new binary — OTA updates can't cross runtime versions.

## Migration from Bare React Native

If you have an existing RN project:

```bash
# Install Expo in the existing project
npx install-expo-modules@latest

# Now you can use any expo-* package
npx expo install expo-image expo-notifications
```

This keeps your native folders as-is (bare workflow). To move to managed:

```bash
npx expo prebuild --clean  # Moves to managed, regenerates native
rm -rf ios android         # Only after verifying prebuild is clean
```

## Performance Optimization

### Hermes (default)

Enabled automatically. Smaller bundles, faster startup.

### New Architecture (default SDK 55)

Enable in older projects:

```json
{ "expo": { "newArchEnabled": true } }
```

Benefits: ~30% faster startup, lower memory, concurrent rendering support.

### Use FlashList for long lists

```bash
npx expo install @shopify/flash-list
```

```tsx
import { FlashList } from '@shopify/flash-list';

<FlashList
  data={items}
  renderItem={({ item }) => <Row item={item} />}
  estimatedItemSize={80}
/>
```

### Image optimization

- Use `expo-image` (not React Native's `Image`) — automatic caching, WebP/AVIF support
- Set `contentFit` and explicit dimensions to avoid layout thrash
- Preload above-the-fold images with `Image.prefetch`

### Profile performance

```tsx
import { PerformanceObserver, performance } from 'react-native-performance';

new PerformanceObserver(list => {
  list.getEntries().forEach(entry => console.log(entry));
}).observe({ type: 'measure', buffered: true });
```

In dev, open React Native DevTools → Profiler tab.

## Error Tracking

### Sentry

```bash
npx expo install @sentry/react-native
```

```tsx
// app/_layout.tsx
import * as Sentry from '@sentry/react-native';

Sentry.init({
  dsn: 'https://...',
  tracesSampleRate: 1.0,
  enableAutoSessionTracking: true,
});

export default Sentry.wrap(function RootLayout() {
  return <Slot />;
});
```

Add to config plugins:

```json
{
  "plugins": [["@sentry/react-native/expo", { "url": "https://sentry.io/" }]]
}
```

Upload source maps on build:

```bash
eas build --profile production --platform all
# Sentry auto-uploads if SENTRY_AUTH_TOKEN is set as EAS secret
```

## Analytics

### PostHog

```bash
npm install posthog-react-native
```

```tsx
import { PostHogProvider } from 'posthog-react-native';

<PostHogProvider apiKey="phc_..." options={{ host: 'https://app.posthog.com' }}>
  <App />
</PostHogProvider>
```

### Expo Insights (Expo-native)

Free analytics via the Expo dashboard:

```bash
npx expo install expo-insights
```

```tsx
import 'expo-insights'; // Side-effect import at app root
```

Tracks launches, OS/device distribution, crash-free sessions.

## App Store Compliance

### Privacy (iOS Privacy Manifest — required)

`app.json`:

```json
{
  "expo": {
    "ios": {
      "privacyManifests": {
        "NSPrivacyAccessedAPITypes": [
          {
            "NSPrivacyAccessedAPIType": "NSPrivacyAccessedAPICategoryUserDefaults",
            "NSPrivacyAccessedAPITypeReasons": ["CA92.1"]
          }
        ],
        "NSPrivacyTracking": false
      }
    }
  }
}
```

### App Tracking Transparency (if using ATT)

```bash
npx expo install expo-tracking-transparency
```

```tsx
import { requestTrackingPermissionsAsync } from 'expo-tracking-transparency';

const { status } = await requestTrackingPermissionsAsync();
if (status === 'granted') {
  // Use IDFA
}
```

### Export compliance

```json
{ "ios": { "infoPlist": { "ITSAppUsesNonExemptEncryption": false } } }
```

### Play Store data safety

Complete the form in Play Console → Policy → Data safety. There's no automation — you must match your actual data collection.

## Common Pitfalls

- **Creating separate bundle IDs per env without creating separate App Store listings**: each bundle ID needs its own app record.
- **Committing `.env` files with secrets**: use `.env.local` for local-only, and EAS secrets for builds.
- **Never running `npx expo-doctor` before release**: catches 90% of "why doesn't it build" issues in 30 seconds.
- **Skipping E2E tests**: unit tests pass but login flow breaks on real devices. Automate one happy-path E2E before shipping.
- **Not profiling before optimizing**: assume nothing. Hermes + FlashList + New Arch typically wins by default.
- **Forgetting to rotate EAS tokens**: when team members leave, invalidate their tokens via the Expo web dashboard.

## Related Topics

- Env variants deep-dive → 04-config-plugins.md
- EAS Update in CI → 07-eas-update.md
- Auth context → 10-authentication.md
