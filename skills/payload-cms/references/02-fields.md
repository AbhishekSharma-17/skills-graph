# Fields

> Source: https://payloadcms.com/docs/fields/overview

## Table of Contents

- [Overview](#overview)
- [Data Fields](#data-fields)
- [Layout Fields](#layout-fields)
- [Common Field Properties](#common-field-properties)
- [Validation](#validation)
- [Conditional Logic](#conditional-logic)
- [Field-Level Access Control](#field-level-access-control)
- [Field Hooks](#field-hooks)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## Overview

Fields define the schema of documents within collections and globals. Every field has a `type` and most have a `name`. Fields support validation, conditional logic, access control, hooks, and admin UI customization.

## Data Fields

### Text and Textarea

```typescript
{ name: 'title', type: 'text', required: true, minLength: 3, maxLength: 200 }
{ name: 'excerpt', type: 'textarea', maxLength: 500 }
```

### Number

```typescript
{ name: 'price', type: 'number', min: 0, max: 99999, hasMany: false }
{ name: 'ratings', type: 'number', hasMany: true }  // Array of numbers
```

### Email

```typescript
{ name: 'contactEmail', type: 'email' }  // Built-in email validation
```

### Select

```typescript
{
  name: 'status',
  type: 'select',
  options: [
    { label: 'Draft', value: 'draft' },
    { label: 'Published', value: 'published' },
    { label: 'Archived', value: 'archived' },
  ],
  defaultValue: 'draft',
  hasMany: false,           // Set true for multi-select
}
```

### Radio

```typescript
{
  name: 'priority',
  type: 'radio',
  options: [
    { label: 'Low', value: 'low' },
    { label: 'Medium', value: 'medium' },
    { label: 'High', value: 'high' },
  ],
}
```

### Checkbox

```typescript
{ name: 'featured', type: 'checkbox', defaultValue: false }
```

### Date

```typescript
{
  name: 'publishDate',
  type: 'date',
  admin: {
    date: {
      pickerAppearance: 'dayAndTime',  // 'dayOnly' | 'dayAndTime' | 'timeOnly'
      displayFormat: 'MMM d, yyyy h:mm a',
    },
  },
}
```

### Point (GeoJSON)

```typescript
{ name: 'location', type: 'point' }  // Stores [longitude, latitude]
```

### JSON

```typescript
{ name: 'metadata', type: 'json' }  // Stores arbitrary JSON
```

### Code

```typescript
{
  name: 'customCSS',
  type: 'code',
  admin: { language: 'css' },  // Syntax highlighting
}
```

### Rich Text

```typescript
{
  name: 'content',
  type: 'richText',
  // Uses the editor configured in payload.config.ts by default
  // Can override per-field with editor property
}
```

### Relationship

```typescript
// Single relationship
{
  name: 'author',
  type: 'relationship',
  relationTo: 'users',
  required: true,
}

// Polymorphic relationship (multiple collection types)
{
  name: 'relatedContent',
  type: 'relationship',
  relationTo: ['posts', 'pages', 'products'],
  hasMany: true,
}
```

### Upload

```typescript
{
  name: 'featuredImage',
  type: 'upload',
  relationTo: 'media',         // Must reference an upload-enabled collection
  required: true,
}
```

## Layout and Structural Fields

### Group — Nest fields under a single property

```typescript
{
  name: 'seo',
  type: 'group',
  fields: [
    { name: 'title', type: 'text' },
    { name: 'description', type: 'textarea' },
    { name: 'keywords', type: 'text' },
  ],
}
// Stored as: { seo: { title: '...', description: '...', keywords: '...' } }
```

### Array — Repeatable sets of fields

```typescript
{
  name: 'highlights',
  type: 'array',
  minRows: 1,
  maxRows: 10,
  fields: [
    { name: 'icon', type: 'text' },
    { name: 'title', type: 'text', required: true },
    { name: 'description', type: 'textarea' },
  ],
}
```

### Blocks — Flexible, polymorphic content

```typescript
{
  name: 'layout',
  type: 'blocks',
  blocks: [
    {
      slug: 'hero',
      fields: [
        { name: 'heading', type: 'text', required: true },
        { name: 'image', type: 'upload', relationTo: 'media' },
        { name: 'cta', type: 'text' },
      ],
    },
    {
      slug: 'contentBlock',
      fields: [
        { name: 'content', type: 'richText' },
      ],
    },
    {
      slug: 'gallery',
      fields: [
        {
          name: 'images',
          type: 'array',
          fields: [
            { name: 'image', type: 'upload', relationTo: 'media', required: true },
            { name: 'caption', type: 'text' },
          ],
        },
      ],
    },
  ],
}
```

### Tabs — Organize fields into tabs in the admin

```typescript
{
  type: 'tabs',
  tabs: [
    {
      label: 'Content',
      fields: [
        { name: 'title', type: 'text', required: true },
        { name: 'content', type: 'richText' },
      ],
    },
    {
      label: 'SEO',
      fields: [
        { name: 'metaTitle', type: 'text' },
        { name: 'metaDescription', type: 'textarea' },
      ],
    },
  ],
}
```

### Row — Place fields side by side

```typescript
{
  type: 'row',
  fields: [
    { name: 'firstName', type: 'text', required: true },
    { name: 'lastName', type: 'text', required: true },
  ],
}
```

### Collapsible — Group fields in a collapsible section

```typescript
{
  type: 'collapsible',
  label: 'Advanced Settings',
  admin: { initCollapsed: true },
  fields: [
    { name: 'customClass', type: 'text' },
    { name: 'anchor', type: 'text' },
  ],
}
```

## Common Field Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | `string` | Database field name (required for data fields) |
| `type` | `string` | Field type (required) |
| `required` | `boolean` | Whether field must have a value |
| `defaultValue` | `any \| function` | Default value or function returning one |
| `unique` | `boolean` | Enforce uniqueness in database |
| `index` | `boolean` | Create a database index on this field |
| `label` | `string \| false` | Admin UI label (false to hide) |
| `validate` | `function` | Custom validation function |
| `access` | `object` | Field-level access control |
| `hooks` | `object` | Field-level hooks |
| `admin` | `object` | Admin UI configuration |
| `localized` | `boolean` | Enable per-locale values |
| `hidden` | `boolean` | Hide from all APIs (admin only) |
| `saveToJWT` | `boolean` | Include in JWT token (auth collections) |

## Validation

```typescript
{
  name: 'slug',
  type: 'text',
  validate: (value, { data, siblingData, operation }) => {
    if (!value) return 'Slug is required'
    if (!/^[a-z0-9-]+$/.test(value)) {
      return 'Slug must contain only lowercase letters, numbers, and hyphens'
    }
    return true  // Return true for valid, string for error message
  },
}
```

## Conditional Logic

Show/hide fields based on other field values:

```typescript
{
  name: 'externalUrl',
  type: 'text',
  admin: {
    condition: (data, siblingData) => {
      return siblingData.linkType === 'external'
    },
  },
}
```

## Field-Level Access Control

```typescript
{
  name: 'internalNotes',
  type: 'textarea',
  access: {
    read: ({ req }) => req.user?.role === 'admin',
    update: ({ req }) => req.user?.role === 'admin',
  },
}
```

## Field Hooks

```typescript
{
  name: 'slug',
  type: 'text',
  hooks: {
    beforeValidate: [
      ({ value, data }) => {
        if (!value && data?.title) {
          return data.title.toLowerCase().replace(/\s+/g, '-')
        }
        return value
      },
    ],
  },
}
```

## Common Patterns

### Polymorphic Link Field

```typescript
const linkFields = [
  {
    name: 'linkType',
    type: 'radio' as const,
    options: [
      { label: 'Internal', value: 'internal' },
      { label: 'External', value: 'external' },
    ],
    defaultValue: 'internal',
  },
  {
    name: 'page',
    type: 'relationship' as const,
    relationTo: 'pages',
    admin: { condition: (_, siblingData) => siblingData?.linkType === 'internal' },
  },
  {
    name: 'url',
    type: 'text' as const,
    admin: { condition: (_, siblingData) => siblingData?.linkType === 'external' },
  },
  { name: 'label', type: 'text' as const, required: true },
  { name: 'newTab', type: 'checkbox' as const },
]
```

## Common Pitfalls

1. **Field names with dots or special chars** — Use only alphanumeric characters and underscores.
2. **Blocks without `slug`** — Every block definition needs a unique `slug`.
3. **Deep nesting** — Arrays inside arrays inside groups gets hard to query. Keep nesting shallow.
4. **Missing `relationTo` on upload fields** — Upload fields must reference an upload-enabled collection.
5. **`hasMany` on relationships** — Don't forget to set `hasMany: true` when a field should allow multiple selections.
