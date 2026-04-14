# Authentication in Expo

> Source: https://docs.expo.dev/guides/authentication/ | Written for SDK 55.x

## Table of Contents

- [Overview](#overview)
- [Secure Token Storage](#secure-token-storage)
- [Session Management Pattern](#session-management-pattern)
- [OAuth with expo-auth-session](#oauth-with-expo-auth-session)
- [Sign in with Apple](#sign-in-with-apple)
- [Google Sign-In](#google-sign-in)
- [Biometric Authentication](#biometric-authentication)
- [Integration with Backend](#integration-with-backend)
- [Route Protection](#route-protection)
- [Common Pitfalls](#common-pitfalls)

## Overview

Expo doesn't ship an authentication framework — it provides primitives:

- **expo-auth-session** — OAuth 2.0 / OIDC flows (Google, GitHub, Apple, etc.)
- **expo-apple-authentication** — Sign in with Apple (native)
- **expo-local-authentication** — Biometric (Face ID, Touch ID, fingerprint)
- **expo-secure-store** — Encrypted keychain for tokens
- **expo-crypto** — Hashing (SHA, HMAC, random UUIDs)

Pair these with your backend or use a hosted service: Supabase Auth, Clerk, Better Auth, Auth0, Firebase Auth.

## Secure Token Storage

Never store auth tokens in `AsyncStorage` or plain files. Use `expo-secure-store`:

```bash
npx expo install expo-secure-store
```

```tsx
import * as SecureStore from 'expo-secure-store';

// Save
await SecureStore.setItemAsync('access_token', token);

// Read
const token = await SecureStore.getItemAsync('access_token');

// Delete
await SecureStore.deleteItemAsync('access_token');

// With biometric unlock
await SecureStore.setItemAsync('refresh_token', refreshToken, {
  requireAuthentication: true,
  authenticationPrompt: 'Unlock to access your account',
});
```

Value size limit: 2KB. For larger payloads (e.g. JWT with claims), encrypt separately.

## Session Management Pattern

A complete session context:

```tsx
// lib/auth.tsx
import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import * as SecureStore from 'expo-secure-store';

type Session = { userId: string; accessToken: string; refreshToken: string };

type AuthContextType = {
  session: Session | null;
  isLoading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const accessToken = await SecureStore.getItemAsync('access_token');
      const refreshToken = await SecureStore.getItemAsync('refresh_token');
      const userId = await SecureStore.getItemAsync('user_id');
      if (accessToken && refreshToken && userId) {
        setSession({ accessToken, refreshToken, userId });
      }
      setIsLoading(false);
    })();
  }, []);

  async function signIn(email: string, password: string) {
    const res = await fetch('https://api.example.com/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) throw new Error('Invalid credentials');

    const { accessToken, refreshToken, user } = await res.json();
    await SecureStore.setItemAsync('access_token', accessToken);
    await SecureStore.setItemAsync('refresh_token', refreshToken);
    await SecureStore.setItemAsync('user_id', user.id);
    setSession({ accessToken, refreshToken, userId: user.id });
  }

  async function signOut() {
    await SecureStore.deleteItemAsync('access_token');
    await SecureStore.deleteItemAsync('refresh_token');
    await SecureStore.deleteItemAsync('user_id');
    setSession(null);
  }

  return (
    <AuthContext.Provider value={{ session, isLoading, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be inside AuthProvider');
  return ctx;
}
```

Wire into the root layout:

```tsx
// app/_layout.tsx
import { AuthProvider } from '@/lib/auth';
import { Slot } from 'expo-router';

export default function RootLayout() {
  return (
    <AuthProvider>
      <Slot />
    </AuthProvider>
  );
}
```

## OAuth with expo-auth-session

Supports any OAuth 2.0 / OIDC provider. Handles PKCE, state, and redirect automatically.

```bash
npx expo install expo-auth-session expo-crypto expo-web-browser
```

Set a scheme in `app.json`:

```json
{
  "expo": { "scheme": "myapp" }
}
```

### GitHub OAuth example

```tsx
import * as AuthSession from 'expo-auth-session';
import * as WebBrowser from 'expo-web-browser';
import { useEffect } from 'react';

WebBrowser.maybeCompleteAuthSession();

const discovery = {
  authorizationEndpoint: 'https://github.com/login/oauth/authorize',
  tokenEndpoint: 'https://github.com/login/oauth/access_token',
  revocationEndpoint: 'https://github.com/settings/connections/applications/<client-id>',
};

export function useGitHubLogin() {
  const redirectUri = AuthSession.makeRedirectUri({ scheme: 'myapp' });

  const [request, response, promptAsync] = AuthSession.useAuthRequest(
    {
      clientId: 'YOUR_GITHUB_CLIENT_ID',
      scopes: ['read:user', 'user:email'],
      redirectUri,
    },
    discovery,
  );

  useEffect(() => {
    if (response?.type === 'success' && request) {
      AuthSession.exchangeCodeAsync(
        {
          clientId: 'YOUR_GITHUB_CLIENT_ID',
          clientSecret: 'YOUR_GITHUB_CLIENT_SECRET', // Use a backend proxy in production!
          code: response.params.code,
          redirectUri,
          extraParams: { code_verifier: request.codeVerifier! },
        },
        discovery,
      ).then(tokens => {
        // Store tokens, fetch user, etc.
      });
    }
  }, [response]);

  return { promptAsync, isReady: !!request };
}
```

**Security**: never ship a client secret in a mobile app. Use Authorization Code + PKCE (no secret) or exchange the code via your backend.

## Sign in with Apple

Required on iOS if you offer third-party sign-in (App Store Guideline 4.8).

```bash
npx expo install expo-apple-authentication
```

```json
// app.json
{
  "expo": {
    "ios": {
      "usesAppleSignIn": true
    },
    "plugins": ["expo-apple-authentication"]
  }
}
```

```tsx
import * as AppleAuthentication from 'expo-apple-authentication';
import { Platform } from 'react-native';

export function AppleSignInButton() {
  if (Platform.OS !== 'ios') return null;

  return (
    <AppleAuthentication.AppleAuthenticationButton
      buttonType={AppleAuthentication.AppleAuthenticationButtonType.SIGN_IN}
      buttonStyle={AppleAuthentication.AppleAuthenticationButtonStyle.BLACK}
      cornerRadius={8}
      style={{ width: 260, height: 44 }}
      onPress={async () => {
        try {
          const credential = await AppleAuthentication.signInAsync({
            requestedScopes: [
              AppleAuthentication.AppleAuthenticationScope.FULL_NAME,
              AppleAuthentication.AppleAuthenticationScope.EMAIL,
            ],
          });
          // Send credential.identityToken to your backend for verification
        } catch (e: any) {
          if (e.code !== 'ERR_REQUEST_CANCELED') throw e;
        }
      }}
    />
  );
}
```

Verify `identityToken` server-side against Apple's JWK: https://appleid.apple.com/auth/keys.

## Google Sign-In

Multiple options:

1. **expo-auth-session with Google endpoints** (cross-platform, works in Expo Go)
2. **@react-native-google-signin/google-signin** (native, iOS/Android only, requires dev client)

### expo-auth-session approach

```tsx
import * as Google from 'expo-auth-session/providers/google';

WebBrowser.maybeCompleteAuthSession();

const [request, response, promptAsync] = Google.useAuthRequest({
  iosClientId: 'YOUR_IOS_CLIENT_ID.apps.googleusercontent.com',
  androidClientId: 'YOUR_ANDROID_CLIENT_ID.apps.googleusercontent.com',
  webClientId: 'YOUR_WEB_CLIENT_ID.apps.googleusercontent.com',
  scopes: ['profile', 'email'],
});

// Trigger
await promptAsync();

// Handle
if (response?.type === 'success') {
  const { authentication } = response;
  // authentication.accessToken, authentication.idToken
}
```

## Biometric Authentication

```bash
npx expo install expo-local-authentication
```

```tsx
import * as LocalAuthentication from 'expo-local-authentication';

async function authenticate() {
  const hasHardware = await LocalAuthentication.hasHardwareAsync();
  const isEnrolled = await LocalAuthentication.isEnrolledAsync();
  if (!hasHardware || !isEnrolled) return false;

  const { success } = await LocalAuthentication.authenticateAsync({
    promptMessage: 'Authenticate to continue',
    fallbackLabel: 'Use passcode',
    cancelLabel: 'Cancel',
  });
  return success;
}
```

Check what's supported:

```tsx
const types = await LocalAuthentication.supportedAuthenticationTypesAsync();
// [1 = fingerprint, 2 = facial recognition, 3 = iris]
```

## Integration with Backend

### Supabase

```bash
npx expo install @supabase/supabase-js
```

```tsx
import { createClient } from '@supabase/supabase-js';
import * as SecureStore from 'expo-secure-store';

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  auth: {
    storage: {
      getItem: (key) => SecureStore.getItemAsync(key),
      setItem: (key, value) => SecureStore.setItemAsync(key, value),
      removeItem: (key) => SecureStore.deleteItemAsync(key),
    },
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: false,
  },
});
```

### Clerk

```bash
npx expo install @clerk/clerk-expo
```

```tsx
import { ClerkProvider, SignedIn, SignedOut } from '@clerk/clerk-expo';
import * as SecureStore from 'expo-secure-store';

const tokenCache = {
  getToken: (key: string) => SecureStore.getItemAsync(key),
  saveToken: (key: string, value: string) => SecureStore.setItemAsync(key, value),
};

export default function App() {
  return (
    <ClerkProvider publishableKey={CLERK_KEY} tokenCache={tokenCache}>
      <SignedIn><AppRoutes /></SignedIn>
      <SignedOut><LoginScreen /></SignedOut>
    </ClerkProvider>
  );
}
```

## Route Protection

Using Expo Router + auth context:

```tsx
// app/(app)/_layout.tsx
import { Redirect, Stack } from 'expo-router';
import { useAuth } from '@/lib/auth';

export default function AppLayout() {
  const { session, isLoading } = useAuth();

  if (isLoading) return null; // Or a splash screen
  if (!session) return <Redirect href="/(auth)/login" />;

  return <Stack />;
}
```

And redirect authenticated users away from the auth group:

```tsx
// app/(auth)/_layout.tsx
import { Redirect, Stack } from 'expo-router';
import { useAuth } from '@/lib/auth';

export default function AuthLayout() {
  const { session } = useAuth();
  if (session) return <Redirect href="/" />;
  return <Stack />;
}
```

## Common Pitfalls

- **Storing tokens in AsyncStorage**: plaintext on disk. Use SecureStore.
- **Using client secrets in mobile apps**: anyone can extract them from the bundle. Use PKCE or proxy through a backend.
- **Not handling token refresh**: implement an axios/fetch interceptor that refreshes on 401 and retries.
- **Using `maybeCompleteAuthSession` wrong**: call it at module load **outside** React components, so the browser session completes correctly on redirect.
- **Deep link scheme mismatch**: redirect URIs must match `scheme` in `app.json` exactly. Use `AuthSession.makeRedirectUri({ scheme: 'myapp' })` to generate them.

## Related Topics

- Secure storage → 03-expo-sdk.md (Secure Store section)
- Deep linking → 02-expo-router.md
- Backend tokens in EAS Build → 06-eas-build.md
