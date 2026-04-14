# Styling & UI in Expo

> Source: https://docs.expo.dev/develop/user-interface/styling/ | Written for SDK 55.x

## Table of Contents

- [Overview](#overview)
- [StyleSheet (Built-in)](#stylesheet-built-in)
- [NativeWind (Tailwind for RN)](#nativewind-tailwind-for-rn)
- [Styled Components](#styled-components)
- [Unistyles](#unistyles)
- [Theming](#theming)
- [Safe Areas](#safe-areas)
- [Responsive Layouts](#responsive-layouts)
- [Dark Mode](#dark-mode)
- [Fonts & Typography](#fonts--typography)
- [Animations](#animations)
- [Icons & Vector Graphics](#icons--vector-graphics)

## Overview

React Native doesn't support CSS directly — it uses a subset of CSS properties exposed via JavaScript objects. The style system is backed by Yoga, a cross-platform flexbox implementation.

Styling options, ordered by popularity in 2026:

1. **StyleSheet** — built-in, no deps, verbose
2. **NativeWind** — Tailwind utility classes
3. **Unistyles v3** — themed StyleSheet with runtime
4. **Styled Components / Emotion** — CSS-in-JS
5. **Tamagui** — full design system, compiler-optimized

## StyleSheet (Built-in)

```tsx
import { View, Text, StyleSheet } from 'react-native';

export default function Card() {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>Card Title</Text>
      <Text style={[styles.body, { color: 'red' }]}>Body text</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    padding: 16,
    borderRadius: 12,
    backgroundColor: '#fff',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 2, // Android
  },
  title: { fontSize: 18, fontWeight: '600', marginBottom: 8 },
  body: { fontSize: 14, color: '#666' },
});
```

### Platform-specific styles

```tsx
import { Platform } from 'react-native';

const styles = StyleSheet.create({
  header: {
    paddingTop: Platform.OS === 'ios' ? 44 : 24,
    ...Platform.select({
      ios: { shadowColor: '#000', shadowOffset: { width: 0, height: 2 } },
      android: { elevation: 4 },
    }),
  },
});
```

## NativeWind (Tailwind for RN)

NativeWind v4 compiles Tailwind classes to StyleSheet objects at build time.

```bash
npx expo install nativewind tailwindcss react-native-reanimated react-native-safe-area-context
npx tailwindcss init
```

`tailwind.config.js`:

```js
module.exports = {
  content: ['./app/**/*.{js,jsx,ts,tsx}', './components/**/*.{js,jsx,ts,tsx}'],
  presets: [require('nativewind/preset')],
  theme: { extend: {} },
  plugins: [],
};
```

`metro.config.js`:

```js
const { getDefaultConfig } = require('expo/metro-config');
const { withNativeWind } = require('nativewind/metro');

const config = getDefaultConfig(__dirname);
module.exports = withNativeWind(config, { input: './global.css' });
```

`global.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

Import once in root layout:

```tsx
import '../global.css';
```

Usage:

```tsx
import { View, Text } from 'react-native';

export default function Card() {
  return (
    <View className="p-4 bg-white rounded-xl shadow-md dark:bg-gray-800">
      <Text className="text-lg font-semibold text-gray-900 dark:text-white">
        Hello NativeWind
      </Text>
    </View>
  );
}
```

Dynamic classes:

```tsx
<View className={`p-4 ${isActive ? 'bg-blue-500' : 'bg-gray-200'}`} />
```

## Styled Components

```bash
npm install styled-components
npm install -D @types/styled-components-react-native
```

```tsx
import styled from 'styled-components/native';

const Card = styled.View`
  padding: 16px;
  border-radius: 12px;
  background-color: ${props => props.theme.cardBg};
`;

const Title = styled.Text<{ size?: number }>`
  font-size: ${props => (props.size ?? 18)}px;
  font-weight: 600;
`;

export default () => (
  <Card>
    <Title size={20}>Hello</Title>
  </Card>
);
```

Theme provider:

```tsx
import { ThemeProvider } from 'styled-components/native';

const theme = { cardBg: '#fff', textColor: '#111' };

<ThemeProvider theme={theme}>
  <App />
</ThemeProvider>
```

## Unistyles

Unistyles v3 is a fast, themed StyleSheet replacement with runtime variants.

```bash
npm install react-native-unistyles
```

```tsx
import { StyleSheet } from 'react-native-unistyles';

StyleSheet.configure({
  themes: {
    light: { colors: { bg: '#fff', text: '#000' } },
    dark: { colors: { bg: '#000', text: '#fff' } },
  },
  settings: {
    adaptiveThemes: true, // follows system
  },
});

// In a component
const styles = StyleSheet.create(theme => ({
  container: { backgroundColor: theme.colors.bg, padding: 16 },
  text: { color: theme.colors.text },
}));

<View style={styles.container}>
  <Text style={styles.text}>Hi</Text>
</View>
```

## Theming

### With React Context

```tsx
import { createContext, useContext, ReactNode } from 'react';
import { useColorScheme } from 'react-native';

const themes = {
  light: { bg: '#fff', text: '#111', tint: '#0ea5e9' },
  dark:  { bg: '#111', text: '#fff', tint: '#38bdf8' },
};

const ThemeContext = createContext(themes.light);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const scheme = useColorScheme() ?? 'light';
  return <ThemeContext.Provider value={themes[scheme]}>{children}</ThemeContext.Provider>;
}

export const useTheme = () => useContext(ThemeContext);
```

### Expo Router's built-in useColorScheme

```tsx
import { useColorScheme } from 'react-native';

const scheme = useColorScheme(); // 'light' | 'dark' | null
```

## Safe Areas

Handle notches, status bars, and home indicators:

```bash
npx expo install react-native-safe-area-context
```

```tsx
// Wrap the app once at the root
import { SafeAreaProvider } from 'react-native-safe-area-context';

<SafeAreaProvider>
  <App />
</SafeAreaProvider>
```

Then use in screens:

```tsx
import { SafeAreaView } from 'react-native-safe-area-context';

<SafeAreaView edges={['top', 'bottom']}>
  <YourContent />
</SafeAreaView>

// Or use the hook for manual control
import { useSafeAreaInsets } from 'react-native-safe-area-context';

const insets = useSafeAreaInsets();
<View style={{ paddingTop: insets.top, paddingBottom: insets.bottom }} />
```

## Responsive Layouts

### Dimensions hook

```tsx
import { useWindowDimensions } from 'react-native';

function Layout() {
  const { width, height } = useWindowDimensions();
  const isTablet = width >= 768;
  return <View style={{ flexDirection: isTablet ? 'row' : 'column' }} />;
}
```

### NativeWind responsive

NativeWind supports mobile-first breakpoints:

```tsx
<View className="w-full md:w-1/2 lg:w-1/3" />
```

Default breakpoints:

- `sm: 640px`
- `md: 768px`
- `lg: 1024px`
- `xl: 1280px`

## Dark Mode

### System-following

```tsx
import { useColorScheme, View, Text } from 'react-native';

function Card() {
  const scheme = useColorScheme();
  return (
    <View style={{ backgroundColor: scheme === 'dark' ? '#111' : '#fff' }}>
      <Text style={{ color: scheme === 'dark' ? '#fff' : '#111' }}>Hi</Text>
    </View>
  );
}
```

### App-controlled

```tsx
import { Appearance } from 'react-native';

Appearance.setColorScheme('dark');
```

Set preference in `app.json`:

```json
{
  "expo": {
    "userInterfaceStyle": "automatic" // 'light' | 'dark' | 'automatic'
  }
}
```

### NativeWind dark mode

```tsx
<View className="bg-white dark:bg-gray-900">
  <Text className="text-black dark:text-white">Auto</Text>
</View>
```

## Fonts & Typography

```bash
npx expo install expo-font
```

Add fonts via `useFonts` hook:

```tsx
import { useFonts, Inter_400Regular, Inter_700Bold } from '@expo-google-fonts/inter';
import * as SplashScreen from 'expo-splash-screen';
import { useEffect } from 'react';

SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const [loaded] = useFonts({ Inter_400Regular, Inter_700Bold });

  useEffect(() => {
    if (loaded) SplashScreen.hideAsync();
  }, [loaded]);

  if (!loaded) return null;
  return <YourApp />;
}
```

Use as fontFamily:

```tsx
<Text style={{ fontFamily: 'Inter_700Bold', fontSize: 24 }}>Bold</Text>
```

Custom fonts (from files):

```ts
useFonts({
  'MyFont-Regular': require('../assets/fonts/MyFont-Regular.ttf'),
  'MyFont-Bold': require('../assets/fonts/MyFont-Bold.ttf'),
});
```

## Animations

### react-native-reanimated (recommended)

Already included in most Expo templates. Animations run on the UI thread.

```tsx
import Animated, { useSharedValue, useAnimatedStyle, withSpring } from 'react-native-reanimated';
import { Pressable } from 'react-native';

function Button() {
  const scale = useSharedValue(1);
  const style = useAnimatedStyle(() => ({ transform: [{ scale: scale.value }] }));

  return (
    <Pressable
      onPressIn={() => (scale.value = withSpring(0.95))}
      onPressOut={() => (scale.value = withSpring(1))}
    >
      <Animated.View style={style}>
        <Text>Press me</Text>
      </Animated.View>
    </Pressable>
  );
}
```

### Layout animations (shared elements)

```tsx
import Animated, { FadeIn, FadeOut, Layout } from 'react-native-reanimated';

<Animated.View entering={FadeIn} exiting={FadeOut} layout={Layout.springify()}>
  <Content />
</Animated.View>
```

### Motion for RN

Cross-platform Framer Motion API:

```bash
npm install motion/react-native
```

```tsx
import { motion } from 'motion/react-native';

<motion.View
  animate={{ opacity: 1, y: 0 }}
  initial={{ opacity: 0, y: 20 }}
  transition={{ type: 'spring' }}
>
  <Text>Animated</Text>
</motion.View>
```

## Icons & Vector Graphics

### @expo/vector-icons

```tsx
import { Ionicons, MaterialIcons, FontAwesome } from '@expo/vector-icons';

<Ionicons name="home" size={24} color="#0ea5e9" />
<MaterialIcons name="notifications" size={24} />
<FontAwesome name="user" size={24} />
```

Browse all icons: https://icons.expo.fyi

### Custom SVG

Install `react-native-svg` and use `Svg`, `Path`, `Circle`, `Rect`, etc. from the package. Supports the full SVG spec on both iOS and Android.

### SVGR (use .svg files as components)

Install `react-native-svg-transformer` and wire it into `metro.config.js` via `babelTransformerPath`, then import `.svg` files directly:

```tsx
import Logo from '../assets/logo.svg';
<Logo width={100} height={40} />
```

## Common Pitfalls

- **Using regular CSS units**: `padding: '16px'` doesn't work — use numeric values `padding: 16`.
- **Forgetting `elevation` for Android shadows**: iOS uses `shadowColor/Offset/Opacity/Radius`, Android uses `elevation`. Need both.
- **Absolute positioning without `flex: 1` parent**: absolute children collapse to 0 dimensions if parent has none.
- **Mixing NativeWind with inline styles**: inline `style` props win over `className`. Use one or the other per element.
- **Loading fonts inside children instead of root**: causes flash-of-fallback-font. Load at root, gate rendering on `loaded`.
- **Forgetting SafeAreaProvider**: `useSafeAreaInsets()` returns zeros without the provider at the root.

## Related Topics

- Animations → 03-expo-sdk.md (Haptics section pairs well with animations)
- Font loading and splash → 04-config-plugins.md
- Icons in tabs → 02-expo-router.md
