# Supabase — Storage

> Source: https://supabase.com/docs/guides/storage

## Overview

Supabase Storage manages files of any size with fine-grained access controls. It supports S3-compatible access, a global CDN (285+ cities), resumable uploads (TUS protocol), and on-the-fly image transformations. Files are organized into **buckets**, and access is controlled through RLS policies on the `storage.objects` table.

## Bucket Types

| Type | Purpose |
|------|---------|
| **Public** | Files accessible via URL without authentication |
| **Private** | Files require signed URLs or authenticated access |

### Creating Buckets

```sql
-- Via SQL
insert into storage.buckets (id, name, public)
values ('avatars', 'avatars', true);

-- With file size and type restrictions
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'documents',
  'documents',
  false,
  5242880,  -- 5MB
  array['application/pdf', 'image/png', 'image/jpeg']
);
```

```typescript
// Via SDK
const { data, error } = await supabase.storage.createBucket('avatars', {
  public: true,
  fileSizeLimit: 1048576,  // 1MB
  allowedMimeTypes: ['image/png', 'image/jpeg', 'image/webp'],
})
```

## Uploading Files

### Standard Upload (< 6MB)

```typescript
const { data, error } = await supabase.storage
  .from('avatars')
  .upload('public/avatar1.png', file, {
    cacheControl: '3600',
    upsert: false,  // true to overwrite existing
    contentType: 'image/png',
  })
```

### Resumable Upload (Large Files)

```typescript
const { data, error } = await supabase.storage
  .from('videos')
  .upload('path/to/video.mp4', file, {
    // TUS resumable upload for files > 6MB
    // Automatically handles interruptions
  })
```

### Upload from Server (Node.js)

```typescript
import { readFileSync } from 'fs'

const fileBuffer = readFileSync('./local-file.pdf')
const { data, error } = await supabase.storage
  .from('documents')
  .upload('reports/q1-2026.pdf', fileBuffer, {
    contentType: 'application/pdf',
  })
```

### Signed Upload URL (Client Uploads Without Auth)

```typescript
// Server: generate a signed upload URL
const { data, error } = await supabase.storage
  .from('avatars')
  .createSignedUploadUrl('user123/avatar.png')

// Client: upload using the signed URL
const { data, error } = await supabase.storage
  .from('avatars')
  .uploadToSignedUrl('user123/avatar.png', data.token, file)
```

## Downloading Files

```typescript
// Download as blob
const { data, error } = await supabase.storage
  .from('documents')
  .download('reports/q1-2026.pdf')
// data is a Blob

// Get public URL (public buckets only)
const { data } = supabase.storage
  .from('avatars')
  .getPublicUrl('public/avatar1.png')
// data.publicUrl = 'https://<ref>.supabase.co/storage/v1/object/public/avatars/public/avatar1.png'

// Signed URL (private buckets, time-limited)
const { data, error } = await supabase.storage
  .from('documents')
  .createSignedUrl('reports/q1-2026.pdf', 3600)  // 1 hour expiry
// data.signedUrl = '...'

// Bulk signed URLs
const { data, error } = await supabase.storage
  .from('documents')
  .createSignedUrls(['file1.pdf', 'file2.pdf'], 3600)
```

## File Management

```typescript
// List files in a bucket/folder
const { data, error } = await supabase.storage
  .from('documents')
  .list('reports', {
    limit: 100,
    offset: 0,
    sortBy: { column: 'created_at', order: 'desc' },
    search: 'q1',  // Filter by name prefix
  })

// Move/rename a file
const { data, error } = await supabase.storage
  .from('documents')
  .move('old/path/file.pdf', 'new/path/file.pdf')

// Copy a file
const { data, error } = await supabase.storage
  .from('documents')
  .copy('source/file.pdf', 'destination/file.pdf')

// Delete files
const { data, error } = await supabase.storage
  .from('documents')
  .remove(['file1.pdf', 'folder/file2.pdf'])

// Empty a bucket
const { data, error } = await supabase.storage.emptyBucket('temp-uploads')

// Delete a bucket (must be empty)
const { data, error } = await supabase.storage.deleteBucket('temp-uploads')
```

## Image Transformations

Transform images on the fly via URL parameters or the SDK:

```typescript
// Via SDK
const { data } = supabase.storage
  .from('avatars')
  .getPublicUrl('avatar.png', {
    transform: {
      width: 200,
      height: 200,
      resize: 'cover',    // 'cover' | 'contain' | 'fill'
      format: 'origin',   // 'origin' | 'avif' (auto-detect best format)
      quality: 80,         // 1-100
    },
  })

// Via URL parameters
// https://<ref>.supabase.co/storage/v1/render/image/public/avatars/avatar.png?width=200&height=200&resize=cover
```

### Transformation Parameters

| Parameter | Values | Default |
|-----------|--------|---------|
| `width` | 1-2560 px | Original |
| `height` | 1-2560 px | Original |
| `resize` | `cover`, `contain`, `fill` | `cover` |
| `format` | `origin`, `avif` | `origin` |
| `quality` | 1-100 | 80 |

## Storage Access Policies (RLS)

Access to files is controlled via RLS policies on `storage.objects`:

```sql
-- Allow authenticated users to upload to their own folder
create policy "Users upload to own folder"
  on storage.objects for insert
  to authenticated
  with check (
    bucket_id = 'avatars'
    and (storage.foldername(name))[1] = (select auth.uid())::text
  );

-- Allow public read access to a bucket
create policy "Public read avatars"
  on storage.objects for select
  to anon, authenticated
  using (bucket_id = 'avatars');

-- Allow users to update/delete their own files
create policy "Users manage own files"
  on storage.objects for update
  to authenticated
  using (
    bucket_id = 'documents'
    and owner_id = (select auth.uid())
  );

create policy "Users delete own files"
  on storage.objects for delete
  to authenticated
  using (
    bucket_id = 'documents'
    and owner_id = (select auth.uid())
  );
```

### Storage Helper Functions

| Function | Returns | Purpose |
|----------|---------|---------|
| `storage.filename(name)` | `text` | Extracts filename from path |
| `storage.foldername(name)` | `text[]` | Extracts folder path components |
| `storage.extension(name)` | `text` | Extracts file extension |

## S3 Compatible Access

Supabase Storage is S3-compatible. Use any S3 client:

```typescript
import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3'

const s3 = new S3Client({
  region: 'auto',
  endpoint: `https://<project-ref>.supabase.co/storage/v1/s3`,
  credentials: {
    accessKeyId: '<service-role-key>',
    secretAccessKey: '<service-role-key>',
  },
  forcePathStyle: true,
})

await s3.send(new PutObjectCommand({
  Bucket: 'avatars',
  Key: 'avatar.png',
  Body: fileBuffer,
  ContentType: 'image/png',
}))
```

## Common Pitfalls

1. **Not setting RLS on storage.objects** — Without policies, no one can access files through the API (even in public buckets, you need SELECT policies for listing).
2. **Using `owner` instead of `owner_id`** — The `owner` column is deprecated. Use `owner_id` (UUID) for policy checks.
3. **File path collisions** — Use user IDs or UUIDs in paths (e.g., `{user_id}/avatar.png`) to avoid conflicts.
4. **Ignoring file size limits** — Set `fileSizeLimit` on buckets to prevent abuse. The platform default is 50MB.
5. **Not using CDN URLs** — Always serve public assets through the CDN URL for performance. Transformations are cached at the CDN edge.
6. **Forgetting `upsert: true`** — By default, uploading to an existing path fails. Set `upsert: true` to overwrite.
