# Strapi — Content Types & Data Modeling

> Source: https://docs.strapi.io/cms/backend-customization/models

## Content Type Categories

| Type | Description | API Behavior |
|------|-------------|--------------|
| **Collection Type** | Multiple entries (Articles, Products, Users) | Full CRUD endpoints |
| **Single Type** | One entry (Homepage, Site Config, About Page) | GET/PUT/DELETE only |
| **Component** | Reusable field group (SEO, Address, Social Links) | No dedicated API endpoint |

## Creating Content Types

### Via Admin Panel (Content-Type Builder)

1. Navigate to Content-Type Builder in the admin sidebar
2. Click "Create new collection type" or "Create new single type"
3. Set display name (auto-generates API ID)
4. Add fields via the field picker
5. Configure advanced settings (draft/publish, i18n)
6. Save — server restarts automatically

### Via CLI

```bash
npm run strapi generate
# Select "content-type" and follow prompts
```

### Via Schema File (Manual)

Create `src/api/<api-name>/content-types/<type-name>/schema.json`:

```json
{
  "kind": "collectionType",
  "collectionName": "articles",
  "info": {
    "singularName": "article",
    "pluralName": "articles",
    "displayName": "Article",
    "description": "Blog articles"
  },
  "options": {
    "draftAndPublish": true
  },
  "pluginOptions": {
    "i18n": {
      "localized": true
    }
  },
  "attributes": {
    "title": {
      "type": "string",
      "required": true,
      "maxLength": 200
    },
    "slug": {
      "type": "uid",
      "targetField": "title"
    },
    "content": {
      "type": "richtext"
    },
    "publishedDate": {
      "type": "date"
    },
    "cover": {
      "type": "media",
      "multiple": false,
      "allowedTypes": ["images"]
    },
    "category": {
      "type": "relation",
      "relation": "manyToOne",
      "target": "api::category.category",
      "inversedBy": "articles"
    },
    "tags": {
      "type": "relation",
      "relation": "manyToMany",
      "target": "api::tag.tag",
      "inversedBy": "articles"
    },
    "seo": {
      "type": "component",
      "repeatable": false,
      "component": "shared.seo"
    },
    "blocks": {
      "type": "dynamiczone",
      "components": [
        "blocks.hero",
        "blocks.quote",
        "blocks.rich-text",
        "blocks.gallery"
      ]
    }
  }
}
```

## Field Types Reference

### Scalar Fields

| Type | Description | Example |
|------|-------------|---------|
| `string` | Short text (max 255 chars) | Title, Name |
| `text` | Long text (unlimited) | Description |
| `richtext` | Rich text with formatting | Article body |
| `email` | Email-validated string | Contact email |
| `password` | Hashed string (never returned in API) | Secret |
| `uid` | URL-friendly unique identifier | Slug |
| `integer` | Whole number | Quantity |
| `biginteger` | Large integer | View count |
| `float` | Decimal number | Rating |
| `decimal` | Precise decimal | Price |
| `boolean` | True/false | Is featured |
| `date` | Date only (YYYY-MM-DD) | Publish date |
| `time` | Time only (HH:mm:ss) | Opening time |
| `datetime` | Full timestamp | Created at |
| `enumeration` | Fixed set of string values | Status |
| `json` | Arbitrary JSON | Settings |
| `blocks` | Block-based rich text editor | Structured content |

### Special Fields

| Type | Description |
|------|-------------|
| `media` | File upload (images, videos, documents) |
| `relation` | Link to another content type |
| `component` | Embedded reusable field group |
| `dynamiczone` | Flexible area accepting multiple component types |
| `customField` | Custom field registered by a plugin |

## Field Validations

```json
{
  "title": {
    "type": "string",
    "required": true,
    "unique": true,
    "minLength": 3,
    "maxLength": 200,
    "default": "Untitled",
    "private": false,
    "configurable": true
  },
  "price": {
    "type": "decimal",
    "required": true,
    "min": 0,
    "max": 99999.99
  },
  "status": {
    "type": "enumeration",
    "enum": ["draft", "review", "published", "archived"],
    "default": "draft",
    "required": true
  }
}
```

Database-level validations via `column`:

```json
{
  "sku": {
    "type": "string",
    "column": {
      "notNullable": true,
      "unique": true,
      "defaultTo": "UNKNOWN"
    }
  }
}
```

## Relations

### Relation Types

| Type | Description | Example |
|------|-------------|---------|
| `oneToOne` | One entry links to one entry | User → Profile |
| `oneToMany` | One entry links to many entries | Author → Articles |
| `manyToOne` | Many entries link to one entry | Articles → Category |
| `manyToMany` | Many entries link to many entries | Articles ↔ Tags |

### Defining Bidirectional Relations

On the "owning" side (Article):
```json
{
  "category": {
    "type": "relation",
    "relation": "manyToOne",
    "target": "api::category.category",
    "inversedBy": "articles"
  }
}
```

On the "inverse" side (Category):
```json
{
  "articles": {
    "type": "relation",
    "relation": "oneToMany",
    "target": "api::article.article",
    "mappedBy": "category"
  }
}
```

## Components

Components are reusable field groups stored in `src/components/<category>/<name>.json`:

```json
// src/components/shared/seo.json
{
  "collectionName": "components_shared_seos",
  "info": {
    "displayName": "SEO",
    "icon": "search"
  },
  "attributes": {
    "metaTitle": {
      "type": "string",
      "maxLength": 60
    },
    "metaDescription": {
      "type": "text",
      "maxLength": 160
    },
    "ogImage": {
      "type": "media",
      "multiple": false,
      "allowedTypes": ["images"]
    }
  }
}
```

Use in a content type:

```json
{
  "seo": {
    "type": "component",
    "repeatable": false,
    "component": "shared.seo"
  },
  "socialLinks": {
    "type": "component",
    "repeatable": true,
    "component": "shared.social-link"
  }
}
```

## Dynamic Zones

Dynamic zones let editors choose from multiple component types per entry:

```json
{
  "blocks": {
    "type": "dynamiczone",
    "components": [
      "blocks.hero",
      "blocks.rich-text",
      "blocks.quote",
      "blocks.gallery",
      "blocks.cta"
    ]
  }
}
```

Each entry in a dynamic zone includes `__component` to identify its type in API responses.

## Common Pitfalls

- **Renaming API IDs** after creation requires manual file renaming and database migration
- **Component categories** use dot notation in schema references (`shared.seo`)
- **Dynamic zone components** must be registered in the zone's `components` array before use
- **Relation targets** use the full UID format: `api::<api-name>.<content-type-name>`
- **Private fields** (like `password`) are never returned in API responses regardless of population
- **UID fields** auto-generate slugs from a `targetField` but can be manually overridden
