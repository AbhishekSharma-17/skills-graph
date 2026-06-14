# Clerk — Prebuilt Components

> Source: [clerk.com/docs/components](https://clerk.com/docs/components/overview)

## Table of Contents

- [Overview](#overview)
- [Authentication Components](#authentication-components)
- [User Management Components](#user-management-components)
- [Organization Components](#organization-components)
- [Control Components](#control-components)
- [Dedicated Pages](#dedicated-pages)
- [Component Props](#component-props)
- [Appearance Customization](#appearance-customization)
- [Common Patterns](#common-patterns)

## Overview

Clerk provides prebuilt React components that handle complete UI flows for authentication, user profiles, and organization management. Components are fully responsive, accessible, and customizable via the `appearance` prop.

All components work in both App Router and Pages Router.

## Authentication Components

### `<SignIn />`

Renders a complete sign-in form with all configured strategies:

```tsx
import { SignIn } from '@clerk/nextjs'

export default function SignInPage() {
  return <SignIn />
}
```

Props:
- `routing` — `"path"` (default) | `"hash"` | `"virtual"`
- `path` — URL path when using path routing (e.g., `/sign-in`)
- `signUpUrl` — URL for the sign-up page link
- `forceRedirectUrl` — Always redirect here after sign-in
- `fallbackRedirectUrl` — Redirect here if no redirect URL in the original request
- `initialValues` — Pre-fill form fields (`emailAddress`, `phoneNumber`, `username`)
- `transferable` — Allow transferring to existing account on identifier conflict

### `<SignUp />`

Renders a complete sign-up form:

```tsx
import { SignUp } from '@clerk/nextjs'

export default function SignUpPage() {
  return <SignUp />
}
```

Props mirror `<SignIn />` with additions:
- `unsafeMetadata` — Set initial `unsafeMetadata` on the user

### `<SignInButton />`

Trigger button that opens the sign-in flow:

```tsx
import { SignInButton } from '@clerk/nextjs'

<SignInButton mode="modal">
  <button className="btn">Sign In</button>
</SignInButton>
```

Props:
- `mode` — `"modal"` (overlay) | `"redirect"` (navigate to sign-in page)
- `forceRedirectUrl` / `fallbackRedirectUrl` — Post-auth redirect
- `children` — Custom trigger element (default: plain button)

### `<SignUpButton />`

Trigger button for sign-up flow. Same props as `<SignInButton />`.

### `<SignOutButton />`

Signs the user out:

```tsx
import { SignOutButton } from '@clerk/nextjs'

<SignOutButton>
  <button>Sign Out</button>
</SignOutButton>
```

Props:
- `redirectUrl` — Where to go after sign-out
- `signOutOptions` — `{ sessionId?: string }` for multi-session

## User Management Components

### `<UserButton />`

Avatar dropdown with user menu (sign out, manage account, switch accounts):

```tsx
import { UserButton } from '@clerk/nextjs'

<UserButton
  afterSignOutUrl="/"
  appearance={{
    elements: {
      avatarBox: 'w-10 h-10',
    },
  }}
/>
```

Props:
- `afterSignOutUrl` — Redirect after sign-out
- `afterMultiSessionSingleSignOutUrl` — Redirect after signing out one session
- `afterSwitchSessionUrl` — Redirect after switching accounts
- `showName` — Display user name next to avatar
- `userProfileMode` — `"modal"` | `"navigation"`
- `userProfileUrl` — URL for navigation mode

Custom menu items:

```tsx
<UserButton>
  <UserButton.MenuItems>
    <UserButton.Link
      label="My Orders"
      href="/orders"
      labelIcon={<ShoppingCartIcon />}
    />
    <UserButton.Action label="Help" onClick={() => openHelp()} />
  </UserButton.MenuItems>
</UserButton>
```

### `<UserProfile />`

Full-page user profile management:

```tsx
import { UserProfile } from '@clerk/nextjs'

export default function ProfilePage() {
  return <UserProfile path="/profile" />
}
```

Includes sections for:
- Account details (name, email, phone)
- Connected accounts (OAuth providers)
- Security (password, MFA, active sessions)

Custom pages:

```tsx
<UserProfile>
  <UserProfile.Page label="Preferences" url="preferences">
    <MyPreferencesForm />
  </UserProfile.Page>
</UserProfile>
```

## Organization Components

### `<OrganizationSwitcher />`

Dropdown for switching between organizations:

```tsx
import { OrganizationSwitcher } from '@clerk/nextjs'

<OrganizationSwitcher
  afterCreateOrganizationUrl="/org/:slug"
  afterSelectOrganizationUrl="/org/:slug"
/>
```

Props:
- `hidePersonal` — Hide the personal workspace option
- `afterCreateOrganizationUrl` — Redirect after creating org (`:slug` and `:id` placeholders)
- `afterSelectOrganizationUrl` — Redirect after switching org
- `organizationProfileMode` — `"modal"` | `"navigation"`

### `<OrganizationProfile />`

Organization settings page with member management:

```tsx
import { OrganizationProfile } from '@clerk/nextjs'

<OrganizationProfile
  path="/org/settings"
  appearance={{
    elements: {
      card: 'shadow-none',
    },
  }}
/>
```

### `<CreateOrganization />`

Form for creating a new organization:

```tsx
import { CreateOrganization } from '@clerk/nextjs'

<CreateOrganization afterCreateOrganizationUrl="/org/:slug" />
```

### `<OrganizationList />`

List all organizations the user belongs to:

```tsx
import { OrganizationList } from '@clerk/nextjs'

<OrganizationList
  afterSelectOrganizationUrl="/org/:slug"
  afterCreateOrganizationUrl="/org/:slug"
/>
```

## Control Components

### `<Show />`

Conditionally render content based on auth state:

```tsx
import { Show } from '@clerk/nextjs'

<Show when="signed-in">
  <p>Welcome back!</p>
</Show>

<Show when="signed-out">
  <SignInButton />
</Show>
```

### `<Protect />`

Render content only for authorized users:

```tsx
import { Protect } from '@clerk/nextjs'

<Protect
  permission="org:billing:manage"
  fallback={<p>Not authorized</p>}
>
  <BillingDashboard />
</Protect>

<Protect
  role="org:admin"
  fallback={<p>Admin only</p>}
>
  <AdminPanel />
</Protect>
```

### `<ClerkLoaded />`

Render children only after Clerk has fully loaded:

```tsx
import { ClerkLoaded } from '@clerk/nextjs'

<ClerkLoaded>
  <MyAuthenticatedComponent />
</ClerkLoaded>
```

### `<ClerkLoading />`

Render children while Clerk is still loading:

```tsx
import { ClerkLoading } from '@clerk/nextjs'

<ClerkLoading>
  <Spinner />
</ClerkLoading>
```

## Dedicated Pages

Set up dedicated sign-in and sign-up pages with catch-all routes:

```tsx
// app/sign-in/[[...sign-in]]/page.tsx
import { SignIn } from '@clerk/nextjs'

export default function SignInPage() {
  return (
    <div className="flex justify-center items-center min-h-screen">
      <SignIn />
    </div>
  )
}
```

```tsx
// app/sign-up/[[...sign-up]]/page.tsx
import { SignUp } from '@clerk/nextjs'

export default function SignUpPage() {
  return (
    <div className="flex justify-center items-center min-h-screen">
      <SignUp />
    </div>
  )
}
```

Set the environment variables to point to these pages:

```env
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
```

## Component Props

Common props shared across components:

| Prop | Type | Description |
|------|------|-------------|
| `appearance` | `Appearance` | Customize styles and theme |
| `localization` | `Localization` | Override text strings |
| `routing` | `"path" \| "hash" \| "virtual"` | URL routing strategy |
| `path` | `string` | Base path for path-based routing |

## Appearance Customization

Quick customization via the `appearance` prop:

```tsx
<SignIn
  appearance={{
    baseTheme: dark,
    variables: {
      colorPrimary: '#6366f1',
      borderRadius: '0.5rem',
    },
    elements: {
      formButtonPrimary: 'bg-indigo-600 hover:bg-indigo-700',
      card: 'shadow-xl',
      headerTitle: 'text-2xl font-bold',
    },
  }}
/>
```

See `references/09-customization.md` for full customization details.

## Common Patterns

**Header with auth controls:**
```tsx
function Header() {
  return (
    <header className="flex justify-between p-4">
      <Logo />
      <nav>
        <Show when="signed-out">
          <SignInButton mode="modal" />
          <SignUpButton mode="modal" />
        </Show>
        <Show when="signed-in">
          <OrganizationSwitcher />
          <UserButton />
        </Show>
      </nav>
    </header>
  )
}
```

**Protected page with role check:**
```tsx
function AdminPage() {
  return (
    <Protect role="org:admin" fallback={<NotAuthorized />}>
      <AdminDashboard />
    </Protect>
  )
}
```
