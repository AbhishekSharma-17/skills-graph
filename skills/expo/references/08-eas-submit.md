# EAS Submit — App Store & Play Store Submission

> Source: https://docs.expo.dev/submit/introduction/ | Written for eas-cli 18.x

## Overview

EAS Submit uploads your built binaries to Apple's App Store Connect (`.ipa`) and Google Play Console (`.aab`). It handles authentication, upload, metadata, and can be chained with EAS Build for one-command release.

## Prerequisites

### iOS

- Apple Developer Program membership ($99/year)
- An app record in App Store Connect (https://appstoreconnect.apple.com/apps)
- Either:
  - App Store Connect API Key (recommended), or
  - App-specific password for your Apple ID

### Android

- Google Play Console account ($25 one-time)
- An app record in Play Console
- A **Service Account JSON key** for API access

## iOS Submission

### Option 1: App Store Connect API Key (recommended)

1. In App Store Connect → Users and Access → Keys → **Generate API Key**
2. Download the `.p8` file (can only download once!)
3. Note the Key ID and Issuer ID

Add to EAS:

```bash
eas credentials
# → iOS → App Store Connect API Key → Upload
```

Or configure in `eas.json`:

```json
{
  "submit": {
    "production": {
      "ios": {
        "ascAppId": "1234567890",
        "appleTeamId": "ABCDEF1234",
        "ascApiKeyPath": "./AuthKey_XXX.p8",
        "ascApiKeyId": "XXXXXXXX",
        "ascApiKeyIssuerId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
      }
    }
  }
}
```

### Submit command

```bash
# Submit latest production build
eas submit --profile production --platform ios --latest

# Submit a specific build
eas submit --profile production --platform ios --id <build-id>

# Submit a local .ipa
eas submit --profile production --platform ios --path ./MyApp.ipa

# Auto-submit after a build
eas build --profile production --platform ios --auto-submit
```

### Post-submission

- Processing on Apple takes 10-30 minutes
- Once processed, the build appears in TestFlight
- You must complete the App Store listing (screenshots, privacy, description) separately
- Submit for review from App Store Connect

## Android Submission

### Service Account setup

1. Google Play Console → Settings → Developer account → API access → **Learn how to create service accounts**
2. Create a Google Cloud project, enable Google Play Android Developer API
3. Create a Service Account with role "Service Account User"
4. Generate JSON key, download it
5. Back in Play Console → Grant access to the service account with "Admin (all permissions)" initially, then narrow as needed

Add to EAS:

```bash
eas credentials
# → Android → Google Play Store → Upload service account JSON
```

Or in `eas.json`:

```json
{
  "submit": {
    "production": {
      "android": {
        "serviceAccountKeyPath": "./play-service-account.json",
        "track": "production",
        "releaseStatus": "draft"
      }
    }
  }
}
```

### Submit command

```bash
# Submit latest build
eas submit --profile production --platform android --latest

# Submit to a specific track
eas submit --profile production --platform android --latest  # uses track from eas.json
```

### Android tracks

| Track | Purpose |
|-------|---------|
| `internal` | Internal testing, up to 100 testers |
| `alpha` | Closed alpha |
| `beta` | Open or closed beta |
| `production` | Full rollout |

### Release status

- `draft` — upload, don't release (review in console)
- `completed` — release immediately
- `inProgress` — staged rollout (requires `rollout`)
- `halted` — upload paused

## Both Platforms in One Command

```bash
eas build --profile production --platform all --auto-submit
```

EAS queues:

1. iOS build
2. Android build
3. iOS submit (once build completes)
4. Android submit (once build completes)

## Submit Profiles

```json
{
  "submit": {
    "production": {
      "ios": {
        "ascAppId": "123",
        "appleTeamId": "ABC"
      },
      "android": {
        "serviceAccountKeyPath": "./play-sa.json",
        "track": "production"
      }
    },
    "preview": {
      "android": {
        "serviceAccountKeyPath": "./play-sa.json",
        "track": "internal",
        "releaseStatus": "draft"
      }
    }
  }
}
```

Invoke a specific profile:

```bash
eas submit --profile preview --platform android --latest
```

## TestFlight (iOS)

After submission, builds auto-appear in TestFlight within 30 minutes.

Manage testers in App Store Connect:

- **Internal testers** (up to 100): your team. Get the build immediately.
- **External testers** (up to 10,000): need Beta App Review (~1 day). Testers install via TestFlight app.

## Phased Rollout

### iOS

Phased release in App Store Connect: 7-day ramp (1% → 2% → 5% → 10% → 20% → 50% → 100%).

### Android

```json
{
  "submit": {
    "production": {
      "android": {
        "releaseStatus": "inProgress",
        "rollout": 0.1   // 10%
      }
    }
  }
}
```

Increase via Play Console or re-run submit.

## Store Metadata (experimental)

EAS can auto-submit some metadata from `store.config.json`:

```json
{
  "apple": {
    "title": "My App",
    "subtitle": "Best app ever",
    "description": "...",
    "keywords": ["social", "productivity"],
    "marketingUrl": "https://example.com",
    "supportUrl": "https://example.com/support",
    "privacyPolicyUrl": "https://example.com/privacy"
  }
}
```

```bash
eas metadata:push
```

Still experimental — preview features change frequently.

## Version & Build Number Rules

### iOS

- `version` (CFBundleShortVersionString): marketing version, `1.2.3`. Shown to users.
- `buildNumber` (CFBundleVersion): monotonically increasing per `version`. Must be unique per submission.

### Android

- `version` (versionName): marketing version.
- `versionCode`: integer, must be strictly greater than any previous submission to the same track.

Use `autoIncrement: true` in `eas.json` to avoid manual bumps:

```json
{
  "build": {
    "production": {
      "autoIncrement": true
    }
  }
}
```

## Troubleshooting

### "Invalid provisioning profile"

Regenerate credentials or ensure your bundleID matches App Store Connect exactly.

### "This version is already in use" (Android)

`versionCode` wasn't incremented. Bump it manually or use `autoIncrement`.

### "This bundle is invalid — The Info.plist contains disallowed keys"

Some config plugins add unsupported keys (usually dev-only). Check your `app.json` `ios.infoPlist` for keys that shouldn't be in production.

### "Service account has insufficient permissions"

In Play Console, grant the service account `Admin (all permissions)` on the specific app (not account-wide).

### iOS submission hangs for hours

Check App Store Connect email for "Missing Compliance" or "Export Compliance" prompts.

## Common Pitfalls

- **Forgetting to create the app record first**: EAS Submit doesn't create the App Store or Play Store listing. You must create the app record in each console before the first submission.
- **Wrong bundleID/package**: submission fails if `bundleIdentifier` / `android.package` don't match the listing in the console.
- **Screenshot / metadata rejection**: EAS only uploads binaries; App Store listing metadata is separate. Use `eas metadata:push` or the web consoles.
- **Uploading debug builds**: building with `distribution: "internal"` produces unsigned/ad-hoc builds. For store submission, build with a production profile (no `distribution: "internal"`).
- **Missing export compliance**: Apple requires `ITSAppUsesNonExemptEncryption` in Info.plist:
  ```json
  { "ios": { "infoPlist": { "ITSAppUsesNonExemptEncryption": false } } }
  ```

## Related Topics

- Building binaries → 06-eas-build.md
- Managing credentials → 06-eas-build.md
- CI pipelines with auto-submit → 12-common-patterns.md
