# Better Auth — Users & Accounts

> Source: [better-auth.com/docs/concepts/users-accounts](https://www.better-auth.com/docs/concepts/users-accounts) | Version: 1.5.6

## Table of Contents

- [Overview](#overview)
- [User Profile Management](#user-profile-management)
- [Email Changes](#email-changes)
- [Password Management](#password-management)
- [Account Management](#account-management)
- [Account Linking](#account-linking)
- [Account Unlinking](#account-unlinking)
- [User Deletion](#user-deletion)
- [Common Pitfalls](#common-pitfalls)

## Overview

Better Auth manages users and accounts as separate entities. A **user** represents an identity (email, name, image). An **account** represents an authentication method linked to a user (email/password, GitHub OAuth, Google OAuth, etc.). One user can have multiple accounts.

## User Profile Management

### Update Profile

```typescript
// Client-side
await authClient.updateUser({
  name: "Jane Doe",
  image: "https://example.com/avatar.jpg",
});
```

Custom fields (added via `additionalFields`) can also be updated:

```typescript
await authClient.updateUser({
  name: "Jane Doe",
  theme: "dark", // Custom field
});
```

### Server-Side Update

```typescript
await auth.api.updateUser({
  body: { name: "Jane Doe" },
  headers: await headers(),
});
```

## Email Changes

Enable email changes in configuration:

```typescript
export const auth = betterAuth({
  user: {
    changeEmail: {
      enabled: true,
    },
  },
  emailVerification: {
    sendVerificationEmail: async ({ user, url, token }) => {
      await sendEmail({
        to: user.email,
        subject: "Verify your new email",
        body: `Click here to verify: ${url}`,
      });
    },
  },
});
```

```typescript
// Client-side
const { data, error } = await authClient.changeEmail({
  newEmail: "new@example.com",
  callbackURL: "/settings",
});
```

### Advanced Email Change Options

```typescript
user: {
  changeEmail: {
    enabled: true,
    // Require confirmation via current email first
    sendChangeEmailConfirmation: true,
    // Allow change without verification if current email is unverified
    updateEmailWithoutVerification: false,
  },
}
```

## Password Management

### Change Password

```typescript
const { data, error } = await authClient.changePassword({
  currentPassword: "oldpassword123",
  newPassword: "newpassword456",
  revokeOtherSessions: true, // Sign out all other devices
});
```

### Set Password (for OAuth Users)

For users who signed up via OAuth and don't have a password:

```typescript
// Server-side only
await auth.api.setPassword({
  body: { newPassword: "password123" },
  headers: await headers(),
});
```

### Verify Password

Confirm user identity before sensitive operations:

```typescript
// Server-side only
const isValid = await auth.api.verifyPassword({
  body: { password: "current_password" },
  headers: await headers(),
});
```

### Forgot Password Flow

```typescript
// 1. Request reset
await authClient.forgetPassword({
  email: "user@example.com",
  redirectTo: "/reset-password",
});

// 2. Server sends email (configure handler)
export const auth = betterAuth({
  emailAndPassword: {
    enabled: true,
    sendResetPassword: async ({ user, url, token }) => {
      await sendEmail({
        to: user.email,
        subject: "Reset your password",
        body: `Reset here: ${url}`,
      });
    },
  },
});

// 3. User clicks link, arrives at reset page
await authClient.resetPassword({
  newPassword: "newpassword456",
  token: searchParams.get("token")!, // From URL
});
```

## Account Management

### List Accounts

```typescript
const { data: accounts } = await authClient.listAccounts();
// Returns: [{ id, providerId, accountId, ... }]
```

### Token Encryption

Better Auth does NOT encrypt OAuth tokens by default. Implement encryption via database hooks:

```typescript
databaseHooks: {
  account: {
    create: {
      before: async (account) => {
        const encrypted = { ...account };
        if (account.accessToken) {
          encrypted.accessToken = encrypt(account.accessToken);
        }
        if (account.refreshToken) {
          encrypted.refreshToken = encrypt(account.refreshToken);
        }
        return { data: encrypted };
      },
    },
  },
}
```

## Account Linking

Account linking connects multiple auth methods to one user. Enabled by default when the provider confirms email verification.

```typescript
// Configure trusted providers for auto-linking
account: {
  accountLinking: {
    enabled: true,
    trustedProviders: ["google", "github"],
    allowDifferentEmails: false, // default
  },
}
```

### Manual Linking

```typescript
// Link a social provider
await authClient.linkSocial({
  provider: "google",
  callbackURL: "/settings",
});

// Link with ID token
await authClient.linkSocial({
  provider: "google",
  idToken: {
    token: "id_token",
    nonce: "nonce",
    accessToken: "access_token",
    refreshToken: "refresh_token",
  },
});
```

## Account Unlinking

```typescript
// Unlink by provider
await authClient.unlinkAccount({
  providerId: "google",
});

// Unlink specific account
await authClient.unlinkAccount({
  providerId: "google",
  accountId: "123",
});
```

Unlinking is blocked if the user has only one account. Enable `allowUnlinkingAll` to override.

## User Deletion

### Enable Deletion

```typescript
export const auth = betterAuth({
  user: {
    deleteUser: {
      enabled: true,
    },
  },
});
```

### Simple Deletion

```typescript
await authClient.deleteUser();
```

### Deletion with Email Verification

```typescript
user: {
  deleteUser: {
    enabled: true,
    sendDeleteAccountVerification: async ({ user, url, token }, request) => {
      await sendEmail({
        to: user.email,
        subject: "Confirm account deletion",
        body: `Click to confirm: ${url}`,
      });
    },
  },
}
```

### Deletion Callbacks

```typescript
user: {
  deleteUser: {
    enabled: true,
    beforeDelete: async (user) => {
      // Block deletion for admin accounts
      if (user.email.includes("admin")) {
        throw new APIError("BAD_REQUEST", {
          message: "Admin accounts cannot be deleted",
        });
      }
    },
    afterDelete: async (user, request) => {
      // Cleanup: remove related data
      await deleteUserContent(user.id);
      await removeFromMailingList(user.email);
    },
  },
}
```

### Deletion Methods

Users can prove identity for deletion via:
- Providing current password
- Using a fresh session token
- Confirming via email verification

## Common Pitfalls

1. **No password for OAuth users** — Users who signed up via social login don't have a password. Use `setPassword` (server-side) or the forgot password flow to set one.
2. **Unlink last account** — By default, users can't unlink their only auth method. Enable `allowUnlinkingAll` only if you have recovery mechanisms.
3. **Token encryption** — Implement it yourself via database hooks. Better Auth stores OAuth tokens in plaintext by default.
4. **Email change verification** — Without `sendVerificationEmail` configured, email changes may not require verification.
5. **Deletion cascading** — Better Auth deletes user, sessions, and accounts. Use `afterDelete` for custom data cleanup.
