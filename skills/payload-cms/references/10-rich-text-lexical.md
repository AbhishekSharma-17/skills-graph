# Rich Text — Lexical Editor

> Source: https://payloadcms.com/docs/rich-text/overview

## Overview

Payload uses Meta's Lexical editor as its default rich text editor. The Lexical integration is provided through the `@payloadcms/richtext-lexical` package, which abstracts the editor through a `RichTextAdapter` interface for rendering, validation, serialization, hooks, and GraphQL population.

Lexical is a highly extensible, performant editor framework that supports collaborative editing, custom nodes, and complex content structures.

## Installation and Setup

```bash
npm install @payloadcms/richtext-lexical
```

```typescript
// payload.config.ts
import { buildConfig } from 'payload'
import { lexicalEditor } from '@payloadcms/richtext-lexical'

export default buildConfig({
  editor: lexicalEditor({
    // Global editor configuration
  }),
  // ... collections, globals, etc.
})
```

## Default Features

The Lexical editor ships with these features enabled by default:
- Bold, italic, underline, strikethrough
- Headings (H1-H6)
- Links (internal + external)
- Ordered and unordered lists
- Blockquotes
- Code blocks
- Inline code
- Horizontal rules
- Paragraphs
- Upload/media embedding
- Relationship embedding

## Customizing Features

### Per-Config (Global)

```typescript
import { lexicalEditor } from '@payloadcms/richtext-lexical'
import {
  BoldFeature,
  ItalicFeature,
  LinkFeature,
  HeadingFeature,
  UnorderedListFeature,
  OrderedListFeature,
  BlockquoteFeature,
  UploadFeature,
} from '@payloadcms/richtext-lexical'

export default buildConfig({
  editor: lexicalEditor({
    features: [
      BoldFeature(),
      ItalicFeature(),
      LinkFeature({
        enabledCollections: ['pages', 'posts'],
      }),
      HeadingFeature({
        enabledHeadingSizes: ['h2', 'h3', 'h4'],  // Restrict heading levels
      }),
      UnorderedListFeature(),
      OrderedListFeature(),
      BlockquoteFeature(),
      UploadFeature({
        collections: {
          media: { fields: [{ name: 'caption', type: 'text' }] },
        },
      }),
    ],
  }),
})
```

### Per-Field Override

```typescript
{
  name: 'content',
  type: 'richText',
  editor: lexicalEditor({
    features: ({ defaultFeatures }) => [
      ...defaultFeatures,
      // Add additional features for this specific field
    ],
  }),
}

// Or a minimal editor
{
  name: 'excerpt',
  type: 'richText',
  editor: lexicalEditor({
    features: [
      BoldFeature(),
      ItalicFeature(),
      LinkFeature(),
    ],
  }),
}
```

## Blocks Feature

Embed structured content blocks within rich text:

```typescript
import { BlocksFeature } from '@payloadcms/richtext-lexical'

editor: lexicalEditor({
  features: ({ defaultFeatures }) => [
    ...defaultFeatures,
    BlocksFeature({
      blocks: [
        {
          slug: 'callout',
          fields: [
            {
              name: 'type',
              type: 'select',
              options: ['info', 'warning', 'success', 'error'],
              defaultValue: 'info',
            },
            { name: 'content', type: 'richText' },
          ],
        },
        {
          slug: 'codeBlock',
          fields: [
            {
              name: 'language',
              type: 'select',
              options: ['javascript', 'typescript', 'python', 'bash'],
            },
            { name: 'code', type: 'code' },
          ],
        },
      ],
    }),
  ],
})
```

## Link Feature Configuration

```typescript
LinkFeature({
  enabledCollections: ['pages', 'posts'],  // Collections available for internal links
  fields: [
    // Additional fields on links
    {
      name: 'rel',
      type: 'select',
      options: ['nofollow', 'noreferrer', 'noopener'],
      hasMany: true,
    },
    {
      name: 'newTab',
      type: 'checkbox',
      defaultValue: false,
    },
  ],
})
```

## HTML Serialization

Convert Lexical state to HTML for frontend rendering:

```typescript
import {
  convertLexicalToHTML,
  consolidateHTMLConverters,
} from '@payloadcms/richtext-lexical'

// In a server component or API route
const html = await convertLexicalToHTML({
  converters: consolidateHTMLConverters({ editorConfig }),
  data: doc.content,  // The Lexical JSON state
})
```

### Custom HTML Converters

```typescript
import { HTMLConverter } from '@payloadcms/richtext-lexical'

const customConverters: HTMLConverter[] = [
  {
    nodeTypes: ['heading'],
    converter: ({ node }) => {
      const tag = node.tag  // h1, h2, etc.
      const id = node.children?.[0]?.text?.toLowerCase().replace(/\s+/g, '-')
      return `<${tag} id="${id}">${node.children.map(c => c.text).join('')}</${tag}>`
    },
  },
]
```

## Lexical State Structure

Rich text is stored as a Lexical JSON tree:

```json
{
  "root": {
    "type": "root",
    "children": [
      {
        "type": "heading",
        "tag": "h2",
        "children": [
          { "type": "text", "text": "Hello World", "format": 1 }
        ]
      },
      {
        "type": "paragraph",
        "children": [
          { "type": "text", "text": "This is a paragraph with " },
          { "type": "text", "text": "bold text", "format": 1 },
          { "type": "text", "text": "." }
        ]
      }
    ]
  }
}
```

## Common Patterns

### Headings with Anchor Links

```typescript
HeadingFeature({
  enabledHeadingSizes: ['h2', 'h3', 'h4'],
})

// In your frontend, generate anchor IDs from heading text
function generateAnchor(text: string): string {
  return text.toLowerCase().replace(/[^a-z0-9]+/g, '-')
}
```

### Table of Contents from Rich Text

```typescript
function extractHeadings(lexicalData: any) {
  const headings: { text: string; level: string; id: string }[] = []

  function walk(node: any) {
    if (node.type === 'heading') {
      const text = node.children?.map((c: any) => c.text).join('') || ''
      headings.push({
        text,
        level: node.tag,
        id: text.toLowerCase().replace(/[^a-z0-9]+/g, '-'),
      })
    }
    if (node.children) {
      node.children.forEach(walk)
    }
  }

  walk(lexicalData.root)
  return headings
}
```

## Common Pitfalls

1. **Features array replaces defaults** — When passing a `features` array, you replace ALL defaults. Use the function form `({ defaultFeatures }) => [...]` to extend.
2. **HTML serialization on client** — `convertLexicalToHTML` should run server-side. Don't ship the converter to the client bundle.
3. **Deep nesting in blocks** — Rich text within blocks within rich text gets complex. Keep nesting shallow.
4. **Large Lexical state** — Rich text with many images and blocks can produce large JSON. Consider lazy-loading content.
5. **Missing upload collection** — The Upload feature requires an upload-enabled collection to be configured.
