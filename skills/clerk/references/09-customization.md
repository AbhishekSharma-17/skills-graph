# Clerk — Customization

> Source: [clerk.com/docs/customization/overview](https://clerk.com/docs/customization/overview)

## Table of Contents

- [Overview](#overview)
- [Customization Layers](#customization-layers)
- [Themes](#themes)
- [Design Tokens (Variables)](#design-tokens-variables)
- [Element Customization](#element-customization)
- [Custom CSS](#custom-css)
- [Global Appearance](#global-appearance)
- [Localization](#localization)
- [Custom Pages](#custom-pages)
- [Custom Menu Items](#custom-menu-items)
- [Email and SMS Templates](#email-and-sms-templates)
- [Headless Mode](#headless-mode)
- [Common Patterns](#common-patterns)

## Overview

Clerk components are customizable at multiple levels — from theme presets to fully headless builds. Choose the right level based on how much control you need:

1. **Themes** — Pre-built visual presets (simplest)
2. **Design tokens** — Modify colors, fonts, spacing
3. **Element styles** — Target specific component parts
4. **Custom CSS** — Full CSS control with stable class names
5. **Headless** — Build your own UI with Clerk's API layer

## Customization Layers

All customization flows through the `appearance` prop, available on `<ClerkProvider>` (global) and individual components (per-component).

```tsx
<ClerkProvider
  appearance={{
    baseTheme: myTheme,
    variables: { /* design tokens */ },
    elements: { /* element overrides */ },
    layout: { /* layout options */ },
  }}
>
```

## Themes

Clerk ships with prebuilt themes:

```tsx
import { dark } from '@clerk/themes'
import { shadc } from '@clerk/themes/shadcn'

// Dark theme
<ClerkProvider appearance={{ baseTheme: dark }}>

// shadcn-compatible theme
<ClerkProvider appearance={{ baseTheme: shadc }}>

// Combine themes
<ClerkProvider appearance={{ baseTheme: [dark, shadc] }}>
```

The `simple` theme strips most decorative styles, giving you a clean base for custom CSS.

## Design Tokens (Variables)

Modify core design values across all components:

```tsx
<ClerkProvider
  appearance={{
    variables: {
      // Colors
      colorPrimary: '#6366f1',
      colorDanger: '#ef4444',
      colorSuccess: '#22c55e',
      colorWarning: '#f59e0b',
      colorBackground: '#ffffff',
      colorInputBackground: '#f9fafb',
      colorInputText: '#111827',
      colorText: '#111827',
      colorTextSecondary: '#6b7280',
      colorTextOnPrimaryBackground: '#ffffff',

      // Typography
      fontFamily: '"Inter", sans-serif',
      fontFamilyButtons: '"Inter", sans-serif',
      fontSize: '0.875rem',
      fontWeight: { normal: 400, medium: 500, semibold: 600, bold: 700 },

      // Spacing and shape
      borderRadius: '0.5rem',
      spacingUnit: '1rem',
    },
  }}
>
```

## Element Customization

Target specific parts of components using the `elements` object:

```tsx
<SignIn
  appearance={{
    elements: {
      // Root card container
      card: 'shadow-xl border border-gray-200',
      
      // Header
      headerTitle: 'text-2xl font-bold text-gray-900',
      headerSubtitle: 'text-sm text-gray-500',
      
      // Form elements
      formButtonPrimary:
        'bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg',
      formButtonReset: 'text-indigo-600 hover:text-indigo-700',
      formFieldInput:
        'border-gray-300 focus:border-indigo-500 focus:ring-indigo-500',
      formFieldLabel: 'text-sm font-medium text-gray-700',
      
      // Social buttons
      socialButtonsBlockButton:
        'border border-gray-300 hover:bg-gray-50',
      socialButtonsBlockButtonText: 'text-gray-700 font-medium',
      
      // Footer
      footerActionLink: 'text-indigo-600 hover:text-indigo-700',
      
      // Divider
      dividerLine: 'bg-gray-200',
      dividerText: 'text-gray-400',
      
      // User button
      avatarBox: 'w-10 h-10',
      userButtonPopoverCard: 'shadow-lg',
    },
  }}
/>
```

You can use Tailwind CSS classes directly in element values.

**Common element keys:**

| Key | Target |
|-----|--------|
| `card` | Main container |
| `headerTitle` | Component title |
| `headerSubtitle` | Subtitle text |
| `formButtonPrimary` | Primary action button |
| `formFieldInput` | Text inputs |
| `formFieldLabel` | Input labels |
| `socialButtonsBlockButton` | OAuth provider buttons |
| `footerActionLink` | Footer links |
| `avatarBox` | User avatar container |
| `badge` | Status badges |
| `alert` | Alert messages |
| `navbar` | Navigation bar |
| `navbarButton` | Nav buttons |
| `profileSection` | Profile sections |

## Custom CSS

Clerk assigns stable CSS classes to elements. Use your own stylesheets:

```css
/* globals.css */
.cl-card {
  box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  border-radius: 1rem;
}

.cl-formButtonPrimary {
  background-color: #6366f1;
  border-radius: 0.5rem;
}

.cl-formButtonPrimary:hover {
  background-color: #4f46e5;
}

.cl-socialButtonsBlockButton {
  border: 1px solid #e5e7eb;
}

.cl-userButtonAvatarBox {
  width: 2.5rem;
  height: 2.5rem;
}
```

CSS class naming pattern: `cl-{elementKey}`.

## Global Appearance

Set appearance globally via `<ClerkProvider>`, then override per-component:

```tsx
<ClerkProvider
  appearance={{
    variables: {
      colorPrimary: '#6366f1',
    },
    elements: {
      formButtonPrimary: 'rounded-lg',
    },
  }}
>
  {/* This SignIn inherits global + adds its own overrides */}
  <SignIn
    appearance={{
      elements: {
        card: 'shadow-none border',
      },
    }}
  />
</ClerkProvider>
```

Per-component `appearance` merges with (does not replace) the global appearance.

## Localization

Override any text string in Clerk components:

```tsx
import { enUS } from '@clerk/localizations'

<ClerkProvider
  localization={{
    ...enUS,
    signIn: {
      start: {
        title: 'Welcome back',
        subtitle: 'Sign in to continue',
        actionText: 'Don\'t have an account?',
        actionLink: 'Create one',
      },
    },
    signUp: {
      start: {
        title: 'Create your account',
        subtitle: 'Get started in seconds',
      },
    },
    userButton: {
      action__manageAccount: 'My Settings',
      action__signOut: 'Log Out',
    },
    formFieldLabel__emailAddress: 'Work email',
    formButtonPrimary: 'Continue',
  }}
>
```

**Available localization packages:**
```bash
npm install @clerk/localizations
```

Includes: English, Spanish, French, German, Italian, Portuguese, Japanese, Korean, Chinese, Arabic, and 20+ more.

```tsx
import { frFR } from '@clerk/localizations'

<ClerkProvider localization={frFR}>
```

## Custom Pages

Add custom pages to `<UserProfile>` and `<OrganizationProfile>`:

```tsx
<UserProfile>
  <UserProfile.Page
    label="Preferences"
    url="preferences"
    labelIcon={<SettingsIcon />}
  >
    <MyPreferencesForm />
  </UserProfile.Page>

  <UserProfile.Page
    label="Billing"
    url="billing"
    labelIcon={<CreditCardIcon />}
  >
    <BillingDashboard />
  </UserProfile.Page>
</UserProfile>
```

Reorder existing pages:

```tsx
<UserProfile>
  {/* Custom page appears first */}
  <UserProfile.Page label="Preferences" url="preferences">
    <Preferences />
  </UserProfile.Page>

  {/* Built-in pages follow */}
  <UserProfile.Page label="account" />
  <UserProfile.Page label="security" />
</UserProfile>
```

## Custom Menu Items

Add items to `<UserButton>` dropdown:

```tsx
<UserButton>
  <UserButton.MenuItems>
    <UserButton.Link
      label="My Orders"
      href="/orders"
      labelIcon={<PackageIcon />}
    />
    <UserButton.Link
      label="Settings"
      href="/settings"
      labelIcon={<SettingsIcon />}
    />
    <UserButton.Action
      label="Help Center"
      labelIcon={<HelpIcon />}
      onClick={() => window.open('https://help.example.com')}
    />
  </UserButton.MenuItems>
</UserButton>
```

## Email and SMS Templates

Customize transactional emails in the Clerk Dashboard under **Customization > Emails**:

- Verification emails (OTP, magic links)
- Organization invitation emails
- Password reset emails
- Welcome emails

Templates support:
- HTML with inline CSS
- Variable interpolation (`{{user.firstName}}`, `{{verification_code}}`)
- Custom branding (logo, colors, footer)
- Multi-language variants

## Headless Mode

For completely custom UIs, use Clerk's hooks and skip all prebuilt components:

```tsx
import { useSignIn, useSignUp, useUser, useAuth } from '@clerk/nextjs'

// Build your own sign-in form
function CustomAuth() {
  const { signIn, setActive } = useSignIn()
  // ... handle all UI yourself
}
```

This gives you full control over:
- Form layout and styling
- Validation UX
- Step transitions
- Error display
- Loading states

See `references/05-hooks.md` for hook details.

## Common Patterns

**Brand-matched auth pages:**
```tsx
<SignIn
  appearance={{
    variables: {
      colorPrimary: '#your-brand-color',
      fontFamily: '"YourFont", sans-serif',
    },
    elements: {
      card: 'shadow-none border-0 bg-transparent',
      headerTitle: 'text-3xl font-display',
      formButtonPrimary: 'bg-brand hover:bg-brand-dark',
    },
    layout: {
      socialButtonsPlacement: 'top',
      socialButtonsVariant: 'blockButton',
    },
  }}
/>
```

**Dark mode support:**
```tsx
import { dark } from '@clerk/themes'

const isDark = useTheme() === 'dark'

<ClerkProvider
  appearance={{
    baseTheme: isDark ? dark : undefined,
  }}
>
```
