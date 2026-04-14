# Expo Router — File-Based Routing

> Source: https://docs.expo.dev/router/introduction/ | Written for expo-router 5.x (SDK 55)

## Table of Contents

- [Overview](#overview)
- [File Conventions](#file-conventions)
- [Layouts](#layouts)
- [Navigation](#navigation)
- [Dynamic Routes](#dynamic-routes)
- [Groups & Slots](#groups--slots)
- [Tabs & Drawer](#tabs--drawer)
- [Modals](#modals)
- [Typed Routes](#typed-routes)
- [Linking & Deep Links](#linking--deep-links)
- [Route Params & Search Params](#route-params--search-params)
- [Common Pitfalls](#common-pitfalls)

## Overview

Expo Router is a file-based routing library for React Native that brings Next.js-style routing to native apps. Files in the `app/` directory become routes automatically.

Routing is built on top of React Navigation (Stack, Tabs, Drawer) — you get the same navigator primitives, but declared via directory structure.

Install in an existing project:

```bash
npx expo install expo-router react-native-safe-area-context react-native-screens
```

Then set the entry point in `package.json`:

```json
{
  "main": "expo-router/entry"
}
```

And add the scheme in `app.json`:

```json
{
  "expo": {
    "scheme": "myapp",
    "plugins": ["expo-router"]
  }
}
```

## File Conventions

| File | Route |
|------|-------|
| `app/index.tsx` | `/` |
| `app/settings.tsx` | `/settings` |
| `app/users/[id].tsx` | `/users/:id` |
| `app/users/[...rest].tsx` | Catch-all (e.g. `/users/a/b/c`) |
| `app/_layout.tsx` | Layout for the directory |
| `app/+not-found.tsx` | 404 route |
| `app/+html.tsx` | Web HTML wrapper (static render only) |
| `app/(tabs)/index.tsx` | `/` — group doesn't add a segment |
| `app/(auth)/login.tsx` | `/login` |

Filenames map to routes; directory structure defines nesting.

## Layouts

Each directory can have a `_layout.tsx` that wraps all child routes.

```tsx
// app/_layout.tsx
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';

export default function RootLayout() {
  return (
    <>
      <StatusBar style="auto" />
      <Stack>
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen name="modal" options={{ presentation: 'modal' }} />
        <Stack.Screen name="+not-found" />
      </Stack>
    </>
  );
}
```

Layouts compose: `app/(tabs)/_layout.tsx` runs inside `app/_layout.tsx`.

```tsx
// app/(tabs)/_layout.tsx
import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

export default function TabsLayout() {
  return (
    <Tabs screenOptions={{ tabBarActiveTintColor: '#0ea5e9' }}>
      <Tabs.Screen
        name="index"
        options={{
          title: 'Home',
          tabBarIcon: ({ color }) => <Ionicons name="home" size={24} color={color} />,
        }}
      />
      <Tabs.Screen
        name="explore"
        options={{
          title: 'Explore',
          tabBarIcon: ({ color }) => <Ionicons name="search" size={24} color={color} />,
        }}
      />
    </Tabs>
  );
}
```

## Navigation

### Imperative navigation

```tsx
import { router, useRouter } from 'expo-router';

// Push a new screen
router.push('/users/42');

// Replace current screen (no back)
router.replace('/login');

// Go back
router.back();

// Navigate with params
router.push({ pathname: '/users/[id]', params: { id: 42 } });

// Inside a component — useRouter for re-render on nav changes
function MyButton() {
  const r = useRouter();
  return <Button onPress={() => r.push('/settings')} title="Go" />;
}
```

### Declarative navigation

```tsx
import { Link } from 'expo-router';

<Link href="/settings">Settings</Link>
<Link href={{ pathname: '/users/[id]', params: { id: 42 } }}>User</Link>

// Typed Link with asChild (renders a custom component)
<Link href="/settings" asChild>
  <Pressable><Text>Settings</Text></Pressable>
</Link>

// Replace instead of push
<Link href="/login" replace>Login</Link>
```

## Dynamic Routes

```tsx
// app/users/[id].tsx
import { useLocalSearchParams } from 'expo-router';
import { View, Text } from 'react-native';

export default function UserDetail() {
  const { id } = useLocalSearchParams<{ id: string }>();
  return (
    <View>
      <Text>User ID: {id}</Text>
    </View>
  );
}
```

### Catch-all routes

```tsx
// app/docs/[...slug].tsx
export default function Docs() {
  const { slug } = useLocalSearchParams<{ slug: string[] }>();
  // /docs/a/b/c → slug = ['a', 'b', 'c']
  return <Text>{slug.join('/')}</Text>;
}
```

## Groups & Slots

**Groups** wrap routes in a shared layout without adding a path segment. Named with parentheses: `(tabs)`, `(auth)`, `(app)`.

```
app/
├── (auth)/
│   ├── _layout.tsx
│   ├── login.tsx        # /login
│   └── signup.tsx       # /signup
├── (app)/
│   ├── _layout.tsx      # Requires auth
│   ├── index.tsx        # /
│   └── profile.tsx      # /profile
└── _layout.tsx
```

You can redirect based on auth state in the layout:

```tsx
// app/(app)/_layout.tsx
import { Redirect, Stack } from 'expo-router';
import { useAuth } from '@/lib/auth';

export default function AppLayout() {
  const { user } = useAuth();
  if (!user) return <Redirect href="/login" />;
  return <Stack />;
}
```

## Tabs & Drawer

### Tabs

Use `Tabs` from `expo-router`. See layout example above.

### Drawer

Install `@react-navigation/drawer` and `react-native-gesture-handler`:

```bash
npx expo install @react-navigation/drawer react-native-gesture-handler react-native-reanimated
```

```tsx
// app/_layout.tsx
import { Drawer } from 'expo-router/drawer';
import { GestureHandlerRootView } from 'react-native-gesture-handler';

export default function RootLayout() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <Drawer>
        <Drawer.Screen name="index" options={{ title: 'Home' }} />
        <Drawer.Screen name="profile" options={{ title: 'Profile' }} />
      </Drawer>
    </GestureHandlerRootView>
  );
}
```

## Modals

Present a route as a modal with `presentation: 'modal'`:

```tsx
// app/_layout.tsx
<Stack>
  <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
  <Stack.Screen
    name="share"
    options={{
      presentation: 'modal',
      headerTitle: 'Share',
    }}
  />
</Stack>

// app/share.tsx
import { router } from 'expo-router';

export default function Share() {
  return (
    <View>
      <Text>Share dialog</Text>
      <Button title="Close" onPress={() => router.back()} />
    </View>
  );
}
```

Other presentations: `card` (default), `transparentModal`, `containedModal`, `fullScreenModal`.

## Typed Routes

Enable typed routes for autocomplete and compile-time validation:

```json
// app.json
{
  "expo": {
    "experiments": {
      "typedRoutes": true
    }
  }
}
```

This generates types automatically:

```tsx
import { Link, router } from 'expo-router';

// Autocompletes all valid routes
<Link href="/users/42" />          // OK
<Link href="/not-a-route" />       // Type error

router.push('/settings');          // OK
router.push({
  pathname: '/users/[id]',
  params: { id: 42 },              // Type-checked
});
```

## Linking & Deep Links

Expo Router auto-generates deep linking config from your directory structure.

Set the URL scheme in `app.json`:

```json
{
  "expo": {
    "scheme": "myapp"
  }
}
```

Your app opens on `myapp://users/42` automatically.

For web-style deep links (Universal Links / App Links):

```json
{
  "expo": {
    "ios": {
      "associatedDomains": ["applinks:myapp.example.com"]
    },
    "android": {
      "intentFilters": [
        {
          "action": "VIEW",
          "autoVerify": true,
          "data": [{ "scheme": "https", "host": "myapp.example.com" }],
          "category": ["BROWSABLE", "DEFAULT"]
        }
      ]
    }
  }
}
```

Test a deep link locally:

```bash
npx uri-scheme open myapp://users/42 --ios
npx uri-scheme open myapp://users/42 --android
```

## Route Params & Search Params

- `useLocalSearchParams()` — params for the **current** screen only.
- `useGlobalSearchParams()` — params for the **topmost** screen (rerenders on any nav change; use sparingly).

```tsx
// /users/42?tab=posts
const { id, tab } = useLocalSearchParams<{ id: string; tab?: string }>();
```

Update search params without navigation:

```tsx
import { router } from 'expo-router';

router.setParams({ tab: 'settings' });
```

## Protecting Routes

### Server-side (prerender)

```tsx
// app/(app)/_layout.tsx
import { Redirect } from 'expo-router';

export default function Layout() {
  const session = useSession();
  if (!session) return <Redirect href="/login" />;
  return <Stack />;
}
```

### With a Boundary

```tsx
import { Stack, useSegments, useRouter } from 'expo-router';
import { useEffect } from 'react';

export default function Layout() {
  const segments = useSegments();
  const router = useRouter();
  const { user } = useAuth();

  useEffect(() => {
    const inAuthGroup = segments[0] === '(auth)';
    if (!user && !inAuthGroup) router.replace('/login');
    else if (user && inAuthGroup) router.replace('/');
  }, [user, segments]);

  return <Stack />;
}
```

## Common Pitfalls

- **Layouts re-mount on every navigation** if you include them as a child instead of at the directory level. Always place `_layout.tsx` in the same directory as the routes it wraps.
- **`useLocalSearchParams` vs `useGlobalSearchParams`**: global rerenders on every navigation change, which can cause perf issues. Use local for screen params.
- **Typed routes need a dev-server restart** after enabling — otherwise `.expo/types/router.d.ts` isn't generated.
- **Modals on Android**: `presentation: 'modal'` renders as a card by default on Android. Use `fullScreenModal` for true modal behavior.
- **Tabs inside Stack**: don't nest Tabs inside another Stack with a visible header — you'll get double headers. Set `headerShown: false` on the parent.

## Related Topics

- Auth flows → 10-authentication.md
- App entry configuration → 04-config-plugins.md
- Navigation patterns → 12-common-patterns.md
