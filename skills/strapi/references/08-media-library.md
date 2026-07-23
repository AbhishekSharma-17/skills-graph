# Strapi — Media Library

> Source: https://docs.strapi.io/cms/features/media-library

## Overview

The Media Library manages all uploaded assets in Strapi — images, videos, audio files, and documents. It provides a centralized interface with search, filtering, folder organization, and image optimization.

## Supported File Types

| Category | Formats |
|----------|---------|
| **Images** | JPEG, PNG, GIF, SVG, TIFF, ICO, DVU |
| **Video** | MPEG, MP4, MOV, WMV, AVI, FLV |
| **Audio** | MP3, WAV, OGG |
| **Files** | CSV, ZIP, PDF, XLS, XLSX, JSON |

## Upload API

### REST Upload

```bash
POST /api/upload
Content-Type: multipart/form-data

# Single file
curl -X POST http://localhost:1337/api/upload \
  -H "Authorization: Bearer <jwt>" \
  -F "files=@./image.png" \
  -F "ref=api::article.article" \
  -F "refId=<documentId>" \
  -F "field=cover"
```

### Upload Parameters

| Parameter | Description |
|-----------|-------------|
| `files` | File(s) to upload |
| `ref` | Content type UID (e.g., `api::article.article`) |
| `refId` | Document ID of the entry to attach to |
| `field` | Field name in the content type |
| `path` | Folder path in media library |
| `fileInfo` | JSON with `name`, `alternativeText`, `caption` |

### Upload with Metadata

```bash
curl -X POST http://localhost:1337/api/upload \
  -H "Authorization: Bearer <jwt>" \
  -F "files=@./photo.jpg" \
  -F 'fileInfo={"name": "hero-image", "alternativeText": "Product hero shot", "caption": "Main product image"}'
```

### Update File Info

```bash
POST /api/upload?id=<fileId>
Content-Type: multipart/form-data

-F 'fileInfo={"alternativeText": "Updated alt text", "caption": "New caption"}'
```

### Delete File

```bash
DELETE /api/upload/files/<fileId>
Authorization: Bearer <jwt>
```

## Storage Providers

### Local Provider (Default)

Files stored on the server filesystem in `public/uploads/`.

### Amazon S3

```bash
npm install @strapi/provider-upload-aws-s3
```

```javascript
// config/plugins.js
module.exports = ({ env }) => ({
  upload: {
    config: {
      provider: 'aws-s3',
      providerOptions: {
        baseUrl: env('CDN_URL'),
        s3Options: {
          credentials: {
            accessKeyId: env('AWS_ACCESS_KEY_ID'),
            secretAccessKey: env('AWS_ACCESS_SECRET'),
          },
          region: env('AWS_REGION'),
          params: {
            Bucket: env('AWS_BUCKET'),
            ACL: env('AWS_BUCKET_ACL', 'public-read'),
          },
        },
      },
      actionOptions: {
        upload: {},
        uploadStream: {},
        delete: {},
      },
    },
  },
});
```

### Cloudinary

```bash
npm install @strapi/provider-upload-cloudinary
```

```javascript
// config/plugins.js
module.exports = ({ env }) => ({
  upload: {
    config: {
      provider: 'cloudinary',
      providerOptions: {
        cloud_name: env('CLOUDINARY_NAME'),
        api_key: env('CLOUDINARY_KEY'),
        api_secret: env('CLOUDINARY_SECRET'),
      },
      actionOptions: {
        upload: {},
        uploadStream: {},
        delete: {},
      },
    },
  },
});
```

### Security Middleware for External Providers

When using external providers, update the security middleware to allow loading assets:

```javascript
// config/middlewares.js
module.exports = [
  'strapi::logger',
  'strapi::errors',
  {
    name: 'strapi::security',
    config: {
      contentSecurityPolicy: {
        directives: {
          'connect-src': ["'self'", 'https:'],
          'img-src': ["'self'", 'data:', 'blob:', 'your-bucket.s3.amazonaws.com'],
          'media-src': ["'self'", 'data:', 'blob:', 'your-bucket.s3.amazonaws.com'],
        },
      },
    },
  },
  'strapi::cors',
  'strapi::poweredBy',
  'strapi::query',
  'strapi::body',
  'strapi::session',
  'strapi::favicon',
  'strapi::public',
];
```

## Image Optimization

### Responsive Images

Enable in Settings → Media Library → "Responsive friendly upload":

```javascript
// config/plugins.js
module.exports = ({ env }) => ({
  upload: {
    config: {
      breakpoints: {
        xlarge: 1920,
        large: 1000,
        medium: 750,
        small: 500,
      },
    },
  },
});
```

When enabled, Strapi generates multiple image sizes at the configured breakpoints. API responses include format URLs:

```json
{
  "url": "/uploads/image.jpg",
  "formats": {
    "large": { "url": "/uploads/large_image.jpg", "width": 1000, "height": 667 },
    "medium": { "url": "/uploads/medium_image.jpg", "width": 750, "height": 500 },
    "small": { "url": "/uploads/small_image.jpg", "width": 500, "height": 333 },
    "thumbnail": { "url": "/uploads/thumbnail_image.jpg", "width": 245, "height": 163 }
  }
}
```

### Size Optimization

Enable in Settings → Media Library → "Size optimization" to automatically reduce image dimensions while maintaining quality.

### Sharp Configuration

Strapi uses the sharp library for image processing:

```javascript
// config/plugins.js
module.exports = ({ env }) => ({
  upload: {
    config: {
      sizeLimit: 250 * 1024 * 1024,  // 250 MB max
      sharp: {
        cache: { memory: 50, files: 20, items: 100 },
        concurrency: 10,
      },
    },
  },
});
```

## File Security

### Type Validation

Strapi validates actual MIME type, not just file extension:

```javascript
// config/plugins.js
module.exports = ({ env }) => ({
  upload: {
    config: {
      security: {
        allowedTypes: ['image/jpeg', 'image/png', 'application/pdf'],
        // OR
        deniedTypes: ['application/x-msdownload'],
      },
    },
  },
});
```

### Size Limits

```javascript
upload: {
  config: {
    sizeLimit: 10 * 1024 * 1024,  // 10 MB
  },
}
```

## Folder Organization

- Create nested folders for organizing assets
- Move files between folders via drag-and-drop
- Bulk select and move/delete assets
- Unlimited folder nesting depth

## Common Pitfalls

- **Media upload is REST-only** — GraphQL does not support file upload; use `POST /api/upload`
- **External providers require CSP updates** — assets won't load without adding provider domains to `img-src` and `media-src`
- **Responsive images** are only generated for images above the breakpoint size — a 400px image won't generate a `large` format
- **Thumbnail is always generated** at 245px width regardless of breakpoint settings
- **MIME type validation** uses actual file content, not extension — renaming a file won't bypass restrictions
- **`ref`, `refId`, and `field`** must all be provided together to attach a file to a content entry
