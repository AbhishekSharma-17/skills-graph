# Storybook — Sharing & Publishing

> Source: https://storybook.js.org/docs/sharing/publish-storybook | v10.5.3

## Table of Contents

- [Building for Production](#building-for-production)
- [Chromatic Publishing](#chromatic-publishing)
- [Static Hosting](#static-hosting)
- [CI/CD Automation](#cicd-automation)
- [Storybook Composition](#storybook-composition)
- [Embedding Stories](#embedding-stories)
- [SEO Configuration](#seo-configuration)

## Building for Production

Storybook builds into a static web application that can be deployed anywhere:

```bash
# Build static output
npm run build-storybook

# Custom output directory
npm run build-storybook -- --output-dir ./docs

# Preview locally
npx http-server ./storybook-static
```

### Performance Optimization

For faster CI builds, enable test mode (disables unnecessary features):

```bash
npm run build-storybook -- --test
```

### Legacy Browser Support

Use the `--preview-only` flag to skip the manager UI build:

```bash
npm run build-storybook -- --preview-only
```

Access stories via `/iframe.html?navigator=true`.

## Chromatic Publishing

Chromatic is the official publishing platform built by the Storybook team. It provides versioning, visual testing, and team collaboration.

### Setup

1. Sign up at [chromatic.com](https://www.chromatic.com)
2. Create a project and get a token
3. Install and deploy:

```bash
npm install chromatic --save-dev
npx chromatic --project-token=<your-token>
```

### Features

- Component history and versioning per commit
- Automatic UI review scanning
- Cross-browser visual testing
- Storybook Composition support
- Secure authentication
- PR/merge request status checks

### Configuration

```json
{
  "projectId": "Project:abc123",
  "buildScriptName": "build-storybook",
  "zip": true,
  "debug": false
}
```

## Static Hosting

Since Storybook produces static files, deploy to any hosting service:

### GitHub Pages

Use the community GitHub Action:

```yaml
# .github/workflows/deploy-storybook.yml
name: Deploy Storybook
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pages: write
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npm run build-storybook
      - uses: actions/upload-pages-artifact@v3
        with:
          path: storybook-static
      - uses: actions/deploy-pages@v4
```

### Netlify

```bash
# Build command
npm run build-storybook

# Publish directory
storybook-static/
```

### Vercel

```json
{
  "buildCommand": "npm run build-storybook",
  "outputDirectory": "storybook-static"
}
```

### AWS S3

```bash
aws s3 sync storybook-static/ s3://my-storybook-bucket/ --delete
```

### Component Publishing Protocol (CPP)

| Level | Features | Examples |
|-------|----------|---------|
| CPP Level 1 | Versioned endpoints, `/index.json`, `/metadata.json` | Chromatic |
| CPP Level 0 | Static hosting only | Netlify, S3, GitHub Pages |

## CI/CD Automation

### Chromatic in GitHub Actions

```yaml
name: Chromatic
on: push
jobs:
  chromatic:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
      - run: npm ci
      - uses: chromaui/action@latest
        with:
          projectToken: ${{ secrets.CHROMATIC_PROJECT_TOKEN }}
          token: ${{ secrets.GITHUB_TOKEN }}
```

### Combined Testing + Deployment

```yaml
name: Storybook CI
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    container:
      image: mcr.microsoft.com/playwright:v1.58.2-noble
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npm run test-storybook
      - run: npm run build-storybook
      - uses: actions/upload-artifact@v4
        with:
          name: storybook
          path: storybook-static/
```

## Storybook Composition

Combine multiple Storybooks into a single view. Useful for monorepos and multi-team projects.

### Reference External Storybooks

```typescript
// .storybook/main.ts
const config: StorybookConfig = {
  refs: {
    'design-system': {
      title: 'Design System',
      url: 'https://design-system.example.com',
    },
    'shared-components': {
      title: 'Shared Components',
      url: 'https://shared.example.com',
    },
  },
};
```

### Package Composition

For npm-published Storybooks:

```typescript
refs: {
  'my-package': {
    title: 'My Package',
    url: 'https://storybook.my-package.com',
    version: '^2.0.0',
  },
}
```

## Embedding Stories

### In External Sites

Use Chromatic's embed feature or the iframe URL:

```html
<iframe
  src="https://your-storybook.chromatic.com/iframe.html?id=button--primary&viewMode=story"
  width="100%"
  height="400"
  style="border: 1px solid #ccc; border-radius: 4px;"
></iframe>
```

### In Notion/Figma

Chromatic-published Storybooks can be embedded directly into Notion pages and Figma files using their respective embed features.

### Design Integration

The Storybook Connect plugin for Figma links Figma components to their Storybook stories, enabling designers and developers to stay in sync.

## SEO Configuration

### Add Description

```html
<!-- .storybook/manager-head.html -->
<meta name="description" content="Components for my design system" />
```

### Prevent Indexing

```html
<!-- .storybook/manager-head.html -->
<meta name="robots" content="noindex" />
```

## Common Pitfalls

1. **Large build output** — Use `--test` flag for CI builds
2. **Missing static assets** — Ensure `staticDirs` is configured in main.ts
3. **Composition CORS** — External Storybooks must allow cross-origin requests
4. **Chromatic token exposure** — Always use CI secrets, never commit tokens

## Related Topics

- [Configuration](10-configuration.md) — Build and preview configuration
- [Visual & A11y Testing](07-visual-a11y-testing.md) — Chromatic visual testing
- [AI Integration](12-ai-integration.md) — MCP server and agent setup
