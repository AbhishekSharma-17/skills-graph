# Nuxt — SEO & Meta Tags

> Source: [nuxt.com/docs/getting-started/seo-meta](https://nuxt.com/docs/getting-started/seo-meta)

## Table of Contents

- [Overview](#overview)
- [useHead Composable](#usehead-composable)
- [useSeoMeta Composable](#useseometa-composable)
- [Head Components](#head-components)
- [Title Templates](#title-templates)
- [Page-Level Metadata](#page-level-metadata)
- [Global Defaults](#global-defaults)
- [Open Graph and Twitter Cards](#open-graph-and-twitter-cards)
- [Common Pitfalls](#common-pitfalls)

## Overview

Nuxt provides head tag management powered by [Unhead](https://unjs.io). Three approaches available:

| Method | Best For |
|--------|----------|
| `useHead()` | Programmatic, reactive head tags |
| `useSeoMeta()` | Type-safe SEO meta tags |
| `<Head>` components | Template-based head management |
| `nuxt.config.ts` `app.head` | Static, site-wide defaults |

## useHead Composable

The primary composable for managing `<head>` content. Supports reactive values:

```vue
<script setup>
useHead({
  title: 'My Page Title',
  meta: [
    { name: 'description', content: 'Page description for search engines' },
    { name: 'robots', content: 'index, follow' }
  ],
  link: [
    { rel: 'canonical', href: 'https://example.com/page' },
    { rel: 'stylesheet', href: '/css/custom.css' }
  ],
  script: [
    { src: '/js/analytics.js', defer: true }
  ],
  htmlAttrs: {
    lang: 'en',
    dir: 'ltr'
  },
  bodyAttrs: {
    class: 'theme-light'
  }
})
```

### Reactive Head

```vue
<script setup>
const title = ref('Loading...')

useHead({
  title,  // Updates when ref changes
  meta: [
    { name: 'description', content: () => `${title.value} - My Site` }
  ]
})

onMounted(async () => {
  const data = await fetchPageData()
  title.value = data.title
})
</script>
```

### Computed Values

```vue
<script setup>
const route = useRoute()

useHead({
  title: computed(() => `${route.meta.title || 'Untitled'} | My App`),
  meta: computed(() => [
    { property: 'og:url', content: `https://example.com${route.path}` }
  ])
})
</script>
```

## useSeoMeta Composable

Type-safe SEO meta tag management. Prevents common mistakes with property names:

```vue
<script setup>
useSeoMeta({
  title: 'My Amazing Site',
  description: 'This is my amazing site built with Nuxt.',
  ogTitle: 'My Amazing Site',
  ogDescription: 'This is my amazing site built with Nuxt.',
  ogImage: 'https://example.com/og-image.png',
  ogUrl: 'https://example.com',
  ogType: 'website',
  twitterCard: 'summary_large_image',
  twitterTitle: 'My Amazing Site',
  twitterDescription: 'This is my amazing site built with Nuxt.',
  twitterImage: 'https://example.com/twitter-image.png'
})
```

### Reactive SEO Meta

```vue
<script setup>
const { data: post } = await useFetch(`/api/posts/${route.params.slug}`)

useSeoMeta({
  title: () => post.value?.title || 'Blog',
  description: () => post.value?.excerpt || '',
  ogTitle: () => post.value?.title || 'Blog',
  ogImage: () => post.value?.image || '/default-og.png'
})
</script>
```

### useServerSeoMeta

For server-side only meta tags (reduces client-side JavaScript):

```vue
<script setup>
useServerSeoMeta({
  robots: 'index, follow',
  ogSiteName: 'My Site'
})
</script>
```

## Head Components

Nuxt provides capitalized components for template-based head management:

```vue
<template>
  <div>
    <Head>
      <Title>{{ pageTitle }}</Title>
      <Meta name="description" :content="description" />
      <Meta property="og:title" :content="pageTitle" />
      <Link rel="canonical" :href="canonicalUrl" />
      <Style>
        body { background: #f0f0f0; }
      </Style>
      <Script type="application/ld+json">
        {{ structuredData }}
      </Script>
    </Head>

    <h1>{{ pageTitle }}</h1>
  </div>
</template>
```

Available components: `<Head>`, `<Title>`, `<Meta>`, `<Link>`, `<Style>`, `<Script>`, `<Body>`, `<Html>`.

## Title Templates

Define a consistent title pattern across your site:

```vue
<!-- app/app.vue -->
<script setup>
useHead({
  titleTemplate: '%s | My App'
})
</script>
```

### Function-Based Templates

```vue
<script setup>
useHead({
  titleTemplate: (titleChunk) => {
    return titleChunk ? `${titleChunk} — My App` : 'My App'
  }
})
</script>
```

### Per-Page Title

```vue
<!-- app/pages/about.vue -->
<script setup>
useHead({
  title: 'About Us'  // Renders as "About Us | My App"
})
</script>
```

### Disabling Title Template

```vue
<script setup>
useHead({
  title: 'Standalone Title',
  titleTemplate: ''  // Override to disable template for this page
})
</script>
```

## Page-Level Metadata

### definePageMeta

Set metadata per page using `definePageMeta`:

```vue
<script setup>
definePageMeta({
  title: 'Dashboard',
  description: 'User dashboard overview',
  layout: 'admin',
  middleware: ['auth']
})
</script>
```

Access page meta in layouts:

```vue
<!-- app/layouts/default.vue -->
<script setup>
const route = useRoute()

useHead({
  title: route.meta.title as string
})
</script>
```

### Combining definePageMeta with useHead

```vue
<script setup>
// Static metadata (available in route.meta)
definePageMeta({
  title: 'Product Details'
})

// Dynamic head tags (can use async data)
const { data: product } = await useFetch(`/api/products/${route.params.id}`)

useHead({
  title: product.value?.name,
  meta: [
    { name: 'description', content: product.value?.description }
  ]
})
</script>
```

## Global Defaults

Set site-wide defaults in `nuxt.config.ts`:

```typescript
export default defineNuxtConfig({
  app: {
    head: {
      title: 'My App',
      htmlAttrs: { lang: 'en' },
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'Default description for my app' }
      ],
      link: [
        { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' }
      ]
    }
  }
})
```

Nuxt includes default `<meta charset="utf-8">` and `<meta name="viewport">` tags. Customize or override them in `app.head`.

## Open Graph and Twitter Cards

### Complete Social Media Setup

```vue
<script setup>
useSeoMeta({
  // Basic
  title: 'My Page',
  description: 'A description of my page',

  // Open Graph
  ogType: 'website',
  ogTitle: 'My Page',
  ogDescription: 'A description of my page',
  ogImage: 'https://example.com/og.png',
  ogImageWidth: 1200,
  ogImageHeight: 630,
  ogUrl: 'https://example.com/my-page',
  ogSiteName: 'My Site',
  ogLocale: 'en_US',

  // Twitter
  twitterCard: 'summary_large_image',
  twitterSite: '@mysite',
  twitterCreator: '@author',
  twitterTitle: 'My Page',
  twitterDescription: 'A description of my page',
  twitterImage: 'https://example.com/twitter.png'
})
</script>
```

### Structured Data (JSON-LD)

```vue
<script setup>
useHead({
  script: [
    {
      type: 'application/ld+json',
      innerHTML: JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'Article',
        headline: 'My Article Title',
        author: {
          '@type': 'Person',
          name: 'John Doe'
        },
        datePublished: '2026-01-01'
      })
    }
  ]
})
</script>
```

## Common Pitfalls

- **Duplicate meta tags** — Nuxt deduplicates by `name`, `property`, or `hid`. If you see duplicates, ensure consistent keys across layouts and pages.
- **Missing og:image dimensions** — Social platforms may not render images without `ogImageWidth` and `ogImageHeight`.
- **Static-only in nuxt.config** — `app.head` in `nuxt.config.ts` cannot use reactive values or composables. Use `useHead()` in `app.vue` for dynamic global tags.
- **useSeoMeta vs useHead** — `useSeoMeta` handles only `<meta>` tags. For `<link>`, `<script>`, or `<html>` attributes, use `useHead()`.
- **Client-side title flicker** — When using `useSeoMeta` with async data, the title may flash. Use `useServerSeoMeta` for static tags and `useSeoMeta` with reactive getters for dynamic content.
