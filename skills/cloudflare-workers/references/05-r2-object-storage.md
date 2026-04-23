# Cloudflare R2 — Object Storage

> Source: [developers.cloudflare.com/r2](https://developers.cloudflare.com/r2/)

## Table of Contents

- [What Is R2](#what-is-r2)
- [Setup](#setup)
- [Core Operations](#core-operations)
- [Multipart Uploads](#multipart-uploads)
- [Conditional Operations](#conditional-operations)
- [Types Reference](#types-reference)
- [Presigned URLs](#presigned-urls)
- [Event Notifications](#event-notifications)
- [Limits and Pricing](#limits-and-pricing)
- [Common Patterns](#common-patterns)

## What Is R2

R2 is Cloudflare's S3-compatible object storage with **zero egress fees**. Access it via Workers bindings or the standard S3 API.

**Best for:** File uploads, images, videos, backups, static assets, data lakes.

Key features:
- S3-compatible API (use any S3 client)
- Workers binding for direct edge access
- Zero egress bandwidth charges
- Multipart uploads for large files
- Storage classes (Standard, Infrequent Access)
- Event notifications on object changes

## Setup

```bash
# Create a bucket
wrangler r2 bucket create my-bucket
```

```toml
# wrangler.toml
[[r2_buckets]]
binding = "MY_BUCKET"
bucket_name = "my-bucket"
```

```typescript
interface Env {
  MY_BUCKET: R2Bucket;
}
```

## Core Operations

### put() — Upload Object

```typescript
// String
await env.MY_BUCKET.put("hello.txt", "Hello, World!");

// JSON
await env.MY_BUCKET.put("data.json", JSON.stringify({ key: "value" }), {
  httpMetadata: { contentType: "application/json" },
});

// Binary from request body
await env.MY_BUCKET.put("upload.bin", request.body);

// With full options
const obj = await env.MY_BUCKET.put("image.png", imageData, {
  httpMetadata: {
    contentType: "image/png",
    cacheControl: "public, max-age=86400",
  },
  customMetadata: {
    uploadedBy: "user:123",
    originalName: "photo.png",
  },
  sha256: expectedHash,  // Integrity check
  storageClass: "Standard",
});
// obj: R2Object (metadata) or null (failed precondition)
```

Writes are **strongly consistent** — once `put()` resolves, the object is globally visible.

### get() — Download Object

```typescript
const obj = await env.MY_BUCKET.get("image.png");
if (obj === null) {
  return new Response("Not Found", { status: 404 });
}

// obj is R2ObjectBody — has body + metadata
return new Response(obj.body, {
  headers: {
    "Content-Type": obj.httpMetadata?.contentType ?? "application/octet-stream",
    "ETag": obj.httpEtag,
  },
});
```

### get() with Range

```typescript
const obj = await env.MY_BUCKET.get("video.mp4", {
  range: { offset: 0, length: 1024 * 1024 },  // First 1MB
});

// Or suffix range (last N bytes)
const tail = await env.MY_BUCKET.get("log.txt", {
  range: { suffix: 1024 },  // Last 1KB
});
```

### head() — Metadata Only

```typescript
const meta = await env.MY_BUCKET.head("image.png");
if (meta) {
  console.log(meta.size, meta.etag, meta.uploaded);
}
// Returns R2Object (no body) or null
```

### delete() — Remove Objects

```typescript
// Single key
await env.MY_BUCKET.delete("old-file.txt");

// Batch delete (up to 1000 keys)
await env.MY_BUCKET.delete(["file1.txt", "file2.txt", "file3.txt"]);
```

Deletes are strongly consistent and idempotent (no error if key doesn't exist).

### list() — List Objects

```typescript
const listed = await env.MY_BUCKET.list();
// => R2Objects { objects, truncated, cursor, delimitedPrefixes }

for (const obj of listed.objects) {
  console.log(obj.key, obj.size, obj.uploaded);
}

// With prefix (folder-like listing)
const images = await env.MY_BUCKET.list({ prefix: "images/" });

// With delimiter (simulate directories)
const dirs = await env.MY_BUCKET.list({ prefix: "uploads/", delimiter: "/" });
// dirs.delimitedPrefixes => ["uploads/2026/", "uploads/2025/"]
// dirs.objects => objects directly in uploads/

// Pagination
let cursor: string | undefined;
const allObjects: R2Object[] = [];
do {
  const result = await env.MY_BUCKET.list({ cursor, limit: 500 });
  allObjects.push(...result.objects);
  cursor = result.truncated ? result.cursor : undefined;
} while (cursor);

// Include metadata in list results
const withMeta = await env.MY_BUCKET.list({
  prefix: "docs/",
  include: ["httpMetadata", "customMetadata"],
});
```

## Multipart Uploads

For files >5MB, use multipart uploads:

```typescript
// Step 1: Create upload
const upload = await env.MY_BUCKET.createMultipartUpload("large-file.zip", {
  httpMetadata: { contentType: "application/zip" },
});

// Step 2: Upload parts (minimum 5MB each, except last part)
const part1 = await upload.uploadPart(1, chunk1);
const part2 = await upload.uploadPart(2, chunk2);
const part3 = await upload.uploadPart(3, chunk3);

// Step 3: Complete
const obj = await upload.complete([part1, part2, part3]);

// Or abort if something goes wrong
// await upload.abort();
```

### Resumable Multipart Upload

```typescript
// Resume a previously started upload (e.g., from a client-driven flow)
const upload = env.MY_BUCKET.resumeMultipartUpload("large-file.zip", uploadId);
const part = await upload.uploadPart(nextPartNumber, chunkData);
```

Incomplete multipart uploads are automatically aborted after 7 days.

## Conditional Operations

Use preconditions to avoid race conditions:

```typescript
// Only overwrite if etag matches (optimistic locking)
const obj = await env.MY_BUCKET.put("config.json", newData, {
  onlyIf: { etagMatches: currentEtag },
});
// Returns null if precondition failed

// Only read if modified
const obj = await env.MY_BUCKET.get("data.json", {
  onlyIf: { etagDoesNotMatch: cachedEtag },
});
// Returns R2Object (metadata only, no body) if not modified

// Date-based conditions
const obj = await env.MY_BUCKET.get("report.pdf", {
  onlyIf: { uploadedAfter: new Date("2026-04-01") },
});
```

## Types Reference

```typescript
interface R2Object {
  key: string;
  version: string;
  size: number;
  etag: string;
  httpEtag: string;               // Quoted etag for HTTP headers
  uploaded: Date;
  httpMetadata?: R2HTTPMetadata;
  customMetadata: Record<string, string>;
  checksums: R2Checksums;
  storageClass: "Standard" | "InfrequentAccess";
  writeHttpMetadata(headers: Headers): void;
}

interface R2ObjectBody extends R2Object {
  body: ReadableStream;
  bodyUsed: boolean;
  arrayBuffer(): Promise<ArrayBuffer>;
  text(): Promise<string>;
  json<T>(): Promise<T>;
  blob(): Promise<Blob>;
}

interface R2HTTPMetadata {
  contentType?: string;
  contentLanguage?: string;
  contentDisposition?: string;
  contentEncoding?: string;
  cacheControl?: string;
  cacheExpiry?: Date;
}

interface R2ListOptions {
  limit?: number;                  // Max 1000 (default 1000)
  prefix?: string;
  cursor?: string;
  delimiter?: string;
  include?: ("httpMetadata" | "customMetadata")[];
}

interface R2Objects {
  objects: R2Object[];
  truncated: boolean;
  cursor?: string;
  delimitedPrefixes: string[];
}

interface R2Conditional {
  etagMatches?: string;
  etagDoesNotMatch?: string;
  uploadedBefore?: Date;
  uploadedAfter?: Date;
}
```

## Presigned URLs

Use the S3-compatible API with `aws4fetch` for presigned URLs:

```typescript
import { AwsClient } from "aws4fetch";

const r2 = new AwsClient({
  accessKeyId: env.R2_ACCESS_KEY,
  secretAccessKey: env.R2_SECRET_KEY,
});

// Generate presigned upload URL
const url = new URL(`https://${env.ACCOUNT_ID}.r2.cloudflarestorage.com/${bucket}/${key}`);
url.searchParams.set("X-Amz-Expires", "3600");

const signed = await r2.sign(new Request(url, { method: "PUT" }), {
  aws: { signQuery: true },
});
```

## Event Notifications

Configure R2 to send events to a Queue when objects change:

```bash
wrangler r2 bucket notification create my-bucket \
  --event-type object-create \
  --queue my-notification-queue
```

```typescript
// Consumer Worker processes R2 events
export default {
  async queue(batch: MessageBatch<R2EventNotification>, env: Env) {
    for (const msg of batch.messages) {
      const { action, bucket, object } = msg.body;
      console.log(`${action} on ${bucket}: ${object.key}`);
    }
  },
};
```

## Limits and Pricing

| Limit | Value |
|-------|-------|
| Max object size | 5 GB (single upload), 5 TB (multipart) |
| Max multipart parts | 10,000 |
| Min part size | 5 MB (except last part) |
| Max custom metadata | 2 KB per object |
| Max buckets | 1,000 per account |
| Storage | $0.015/GB-mo |
| Class A ops (PUT, POST, LIST) | $4.50/million |
| Class B ops (GET, HEAD) | $0.36/million |
| Egress | **Free** |

## Common Patterns

### File Upload API

```typescript
export default {
  async fetch(request: Request, env: Env) {
    if (request.method === "PUT") {
      const url = new URL(request.url);
      const key = url.pathname.slice(1);
      const contentType = request.headers.get("Content-Type") ?? "application/octet-stream";

      const obj = await env.MY_BUCKET.put(key, request.body, {
        httpMetadata: { contentType },
        customMetadata: { uploadedAt: new Date().toISOString() },
      });

      return Response.json({
        key: obj!.key,
        size: obj!.size,
        etag: obj!.etag,
      }, { status: 201 });
    }

    if (request.method === "GET") {
      const key = new URL(request.url).pathname.slice(1);
      const obj = await env.MY_BUCKET.get(key);
      if (!obj) return new Response("Not Found", { status: 404 });

      const headers = new Headers();
      obj.writeHttpMetadata(headers);
      headers.set("ETag", obj.httpEtag);
      return new Response(obj.body, { headers });
    }

    return new Response("Method Not Allowed", { status: 405 });
  },
};
```

## Common Pitfalls

- **No directory concept** — R2 is flat key-value. Use `/` in keys and `delimiter` in `list()` to simulate folders.
- **Multipart minimum** — Each part (except last) must be at least 5MB. Smaller parts cause errors.
- **put() returns null** — If you pass `onlyIf` conditions and they fail, `put()` returns `null`. Check for this.
- **list() limit** — Max 1000 objects per call. Always check `truncated` and paginate.
- **writeHttpMetadata** — Use `obj.writeHttpMetadata(headers)` to set Content-Type, Cache-Control etc. on the response — don't manually copy them.
