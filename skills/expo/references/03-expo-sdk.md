# Expo SDK — Core APIs

> Source: https://docs.expo.dev/versions/latest/ | Written for SDK 55.x

## Table of Contents

- [Overview](#overview)
- [Images (expo-image)](#images-expo-image)
- [File System (expo-file-system)](#file-system-expo-file-system)
- [Camera (expo-camera)](#camera-expo-camera)
- [Location (expo-location)](#location-expo-location)
- [Media Library (expo-media-library)](#media-library-expo-media-library)
- [Sensors (expo-sensors)](#sensors-expo-sensors)
- [SQLite (expo-sqlite)](#sqlite-expo-sqlite)
- [Secure Store (expo-secure-store)](#secure-store-expo-secure-store)
- [Haptics (expo-haptics)](#haptics-expo-haptics)
- [Linking (expo-linking)](#linking-expo-linking)
- [Device Info (expo-device)](#device-info-expo-device)
- [Sharing (expo-sharing)](#sharing-expo-sharing)

## Overview

The Expo SDK is a curated collection of libraries that wrap native iOS/Android APIs. All packages are maintained by the Expo team, tested against the current SDK, and work out of the box with Expo Go (where supported) or a dev client.

Install with `npx expo install <package>` to get the correct version for your SDK.

```bash
npx expo install expo-image expo-camera expo-location expo-notifications
```

## Images (expo-image)

Faster, more capable replacement for the React Native `Image` component. Supports HTTP/disk caching, placeholders, blurhash, and WebP/AVIF.

```tsx
import { Image } from 'expo-image';

<Image
  source="https://example.com/cat.jpg"
  placeholder={{ blurhash: 'LKN]Rv%2Tw=w]~RBVZRi};RPxuwH' }}
  contentFit="cover"
  transition={300}
  cachePolicy="memory-disk"
  style={{ width: 200, height: 200 }}
/>
```

Preload images ahead of time:

```tsx
import { Image } from 'expo-image';

await Image.prefetch(['https://example.com/a.jpg', 'https://example.com/b.jpg']);
```

## File System (expo-file-system)

Read/write files on the device, download files over HTTP.

```tsx
import * as FileSystem from 'expo-file-system/next';

// New API (SDK 54+)
const file = new FileSystem.File(FileSystem.Paths.document, 'notes.txt');
file.create();
file.write('Hello');
const contents = file.text();

// List a directory
const dir = new FileSystem.Directory(FileSystem.Paths.document);
for (const entry of dir.list()) {
  console.log(entry.name);
}

// Download with progress
const downloaded = await FileSystem.File.downloadFileAsync(
  'https://example.com/large.zip',
  new FileSystem.File(FileSystem.Paths.cache, 'archive.zip'),
);
```

Storage locations:

- `Paths.document` — user data, backed up
- `Paths.cache` — temporary, may be cleared by OS
- `Paths.bundle` — read-only app assets

## Camera (expo-camera)

```tsx
import { CameraView, useCameraPermissions } from 'expo-camera';
import { useState, useRef } from 'react';
import { View, Text, Button } from 'react-native';

export default function CameraScreen() {
  const [permission, requestPermission] = useCameraPermissions();
  const [facing, setFacing] = useState<'front' | 'back'>('back');
  const camera = useRef<CameraView>(null);

  if (!permission) return <View />;
  if (!permission.granted) {
    return (
      <View>
        <Text>Camera permission required</Text>
        <Button title="Grant" onPress={requestPermission} />
      </View>
    );
  }

  const takePicture = async () => {
    const photo = await camera.current?.takePictureAsync({ quality: 0.8 });
    console.log('Saved to', photo?.uri);
  };

  return (
    <CameraView ref={camera} facing={facing} style={{ flex: 1 }}>
      <Button title="Flip" onPress={() => setFacing(f => (f === 'back' ? 'front' : 'back'))} />
      <Button title="Shoot" onPress={takePicture} />
    </CameraView>
  );
}
```

Barcode scanning:

```tsx
<CameraView
  barcodeScannerSettings={{ barcodeTypes: ['qr', 'ean13'] }}
  onBarcodeScanned={({ data, type }) => console.log(type, data)}
/>
```

Required config plugins (added automatically when you install via `npx expo install`):

```json
{
  "expo": {
    "plugins": [
      ["expo-camera", { "cameraPermission": "Allow $(PRODUCT_NAME) to access your camera" }]
    ]
  }
}
```

## Location (expo-location)

```tsx
import * as Location from 'expo-location';

const { status } = await Location.requestForegroundPermissionsAsync();
if (status !== 'granted') return;

const { coords } = await Location.getCurrentPositionAsync({
  accuracy: Location.Accuracy.Balanced,
});
console.log(coords.latitude, coords.longitude);

// Watch position
const sub = await Location.watchPositionAsync(
  { accuracy: Location.Accuracy.High, distanceInterval: 10 },
  loc => console.log(loc.coords),
);
// later: sub.remove();
```

Background location (requires additional setup):

```tsx
import * as TaskManager from 'expo-task-manager';
import * as Location from 'expo-location';

TaskManager.defineTask('background-location', ({ data, error }) => {
  if (error) return;
  const { locations } = data as any;
  // Send to server
});

await Location.requestBackgroundPermissionsAsync();
await Location.startLocationUpdatesAsync('background-location', {
  accuracy: Location.Accuracy.Balanced,
  timeInterval: 60_000,
});
```

## Media Library (expo-media-library)

Access the device's photo/video library.

```tsx
import * as MediaLibrary from 'expo-media-library';

const { status } = await MediaLibrary.requestPermissionsAsync();

// Save a photo to the camera roll
const asset = await MediaLibrary.createAssetAsync('/path/to/photo.jpg');
await MediaLibrary.createAlbumAsync('MyApp', asset, false);

// Query
const { assets } = await MediaLibrary.getAssetsAsync({
  mediaType: 'photo',
  first: 50,
  sortBy: 'creationTime',
});
```

## Sensors (expo-sensors)

```tsx
import { Accelerometer, Gyroscope } from 'expo-sensors';
import { useEffect, useState } from 'react';

function useAccelerometer() {
  const [data, setData] = useState({ x: 0, y: 0, z: 0 });
  useEffect(() => {
    Accelerometer.setUpdateInterval(100);
    const sub = Accelerometer.addListener(setData);
    return () => sub.remove();
  }, []);
  return data;
}
```

Available: `Accelerometer`, `Gyroscope`, `Magnetometer`, `Barometer`, `Pedometer`, `DeviceMotion`, `LightSensor`.

## SQLite (expo-sqlite)

Embedded SQLite database with modern async API.

```tsx
import * as SQLite from 'expo-sqlite';

const db = await SQLite.openDatabaseAsync('app.db');

// Create table
await db.execAsync(`
  CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE
  );
`);

// Insert with parameters
const result = await db.runAsync(
  'INSERT INTO users (name, email) VALUES (?, ?)',
  'Alice',
  'a@example.com',
);
console.log(result.lastInsertRowId);

// Query all rows
type User = { id: number; name: string; email: string };
const users = await db.getAllAsync<User>('SELECT * FROM users');

// Query first row
const user = await db.getFirstAsync<User>('SELECT * FROM users WHERE id = ?', 1);

// Transaction
await db.withTransactionAsync(async () => {
  await db.runAsync('UPDATE users SET name = ? WHERE id = ?', 'Bob', 1);
  await db.runAsync('DELETE FROM users WHERE id = ?', 2);
});
```

Integrates with Drizzle ORM for type-safe queries:

```bash
npx expo install expo-sqlite drizzle-orm
npm install -D drizzle-kit
```

## Secure Store (expo-secure-store)

Encrypted key-value store (iOS Keychain / Android Keystore). For tokens and secrets.

```tsx
import * as SecureStore from 'expo-secure-store';

await SecureStore.setItemAsync('token', 'abc123');
const token = await SecureStore.getItemAsync('token');
await SecureStore.deleteItemAsync('token');

// Require biometric unlock
await SecureStore.setItemAsync('sensitive', 'data', {
  requireAuthentication: true,
});
```

Size limit: 2KB per value. For larger data, encrypt a key stored here and use FileSystem.

## Haptics (expo-haptics)

```tsx
import * as Haptics from 'expo-haptics';

Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
Haptics.selectionAsync();
```

## Linking (expo-linking)

Open URLs, deep links, email, phone.

```tsx
import * as Linking from 'expo-linking';

// Open a URL
await Linking.openURL('https://example.com');
await Linking.openURL('mailto:a@example.com?subject=Hi');
await Linking.openURL('tel:+15551234');

// Get initial URL (app opened from a deep link)
const url = await Linking.getInitialURL();

// Listen for incoming URLs
const sub = Linking.addEventListener('url', ({ url }) => {
  console.log('Received URL:', url);
});

// Parse a URL
const { hostname, path, queryParams } = Linking.parse(url);
```

## Device Info (expo-device)

```tsx
import * as Device from 'expo-device';

console.log(Device.brand);       // 'Apple' | 'Samsung' | ...
console.log(Device.modelName);   // 'iPhone 15 Pro'
console.log(Device.osName);      // 'iOS' | 'Android'
console.log(Device.osVersion);   // '17.4'
console.log(Device.isDevice);    // false on simulator
```

## Sharing (expo-sharing)

Share files via the native share sheet.

```tsx
import * as Sharing from 'expo-sharing';
import * as FileSystem from 'expo-file-system/next';

const file = new FileSystem.File(FileSystem.Paths.cache, 'report.pdf');
// ... write PDF to file

if (await Sharing.isAvailableAsync()) {
  await Sharing.shareAsync(file.uri, {
    mimeType: 'application/pdf',
    dialogTitle: 'Share report',
  });
}
```

## Permissions Pattern

Most SDK packages expose a hook for permissions:

```tsx
const [permission, requestPermission] = useCameraPermissions();
// permission: { granted, canAskAgain, status }

if (!permission?.granted) {
  return <Button title="Grant camera access" onPress={requestPermission} />;
}
```

Check status without prompting:

```tsx
const { status } = await Location.getForegroundPermissionsAsync();
```

## Common Pitfalls

- **Permissions must be in app.json**: iOS requires usage descriptions (`NSCameraUsageDescription`, etc.). Most SDK packages set these via config plugins — don't forget to add the plugin.
- **Expo Go limitations**: some APIs (push notifications, background location, in-app purchases) require a dev client. Test on a dev build, not Expo Go.
- **File paths change on rebuild**: `FileSystem.documentDirectory` paths are stable across launches but **not across reinstalls**. Store the filename and reconstruct the path.
- **Use the new FileSystem API**: `expo-file-system/next` replaces the legacy `expo-file-system` functions with an object-oriented API. Legacy API still works but is deprecated.

## Related Topics

- Notifications → 09-push-notifications.md
- Secure auth storage → 10-authentication.md
- Config plugin setup → 04-config-plugins.md
