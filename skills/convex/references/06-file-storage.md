# File Storage

> Source: [docs.convex.dev/file-storage](https://docs.convex.dev/file-storage) | convex v1.34.x

## Overview

Convex File Storage lets you upload, store, serve, and delete files alongside your database. Files are stored in a system table `_storage` and served via generated URLs.

## Upload Flow

### Method 1: Client Upload (Recommended)

```typescript
// convex/files.ts
import { mutation } from "./_generated/server";
import { v } from "convex/values";

// Step 1: Generate an upload URL
export const generateUploadUrl = mutation(async (ctx) => {
  return await ctx.storage.generateUploadUrl();
});

// Step 3: Save the file reference to your table
export const saveFile = mutation({
  args: { storageId: v.id("_storage"), name: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db.insert("files", {
      storageId: args.storageId,
      name: args.name,
      uploadedAt: Date.now(),
    });
  },
});
```

```tsx
// Client (React)
function FileUpload() {
  const generateUploadUrl = useMutation(api.files.generateUploadUrl);
  const saveFile = useMutation(api.files.saveFile);

  async function handleUpload(file: File) {
    // Step 1: Get upload URL
    const uploadUrl = await generateUploadUrl();

    // Step 2: Upload the file directly
    const result = await fetch(uploadUrl, {
      method: "POST",
      headers: { "Content-Type": file.type },
      body: file,
    });
    const { storageId } = await result.json();

    // Step 3: Save reference in database
    await saveFile({ storageId, name: file.name });
  }

  return (
    <input
      type="file"
      onChange={(e) => e.target.files?.[0] && handleUpload(e.target.files[0])}
    />
  );
}
```

### Method 2: Server-Side Upload (Actions)

```typescript
"use node";
import { action } from "./_generated/server";
import { internal } from "./_generated/api";

export const downloadAndStore = action({
  args: { url: v.string() },
  handler: async (ctx, args) => {
    // Download from external URL
    const response = await fetch(args.url);
    const blob = await response.blob();

    // Store in Convex
    const storageId = await ctx.storage.store(blob);

    // Save reference
    await ctx.runMutation(internal.files.saveStorageId, { storageId });
    return storageId;
  },
});
```

### Method 3: HTTP Action Upload

```typescript
// convex/http.ts
http.route({
  path: "/upload",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const blob = await request.blob();
    const storageId = await ctx.storage.store(blob);

    await ctx.runMutation(internal.files.saveStorageId, {
      storageId,
      contentType: request.headers.get("Content-Type") || "application/octet-stream",
    });

    return new Response(JSON.stringify({ storageId }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  }),
});
```

## Serving Files

### Get a URL for a Storage ID

```typescript
export const getFileUrl = query({
  args: { storageId: v.id("_storage") },
  handler: async (ctx, args) => {
    return await ctx.storage.getUrl(args.storageId);
  },
});
```

The returned URL is a signed, temporary URL that can be used directly in `<img>`, `<video>`, `<a>` tags, etc.

### Serve Files via HTTP Action

```typescript
http.route({
  path: "/files",
  method: "GET",
  handler: httpAction(async (ctx, request) => {
    const url = new URL(request.url);
    const storageId = url.searchParams.get("id");

    const blob = await ctx.storage.get(storageId);
    if (!blob) {
      return new Response("Not found", { status: 404 });
    }

    return new Response(blob, {
      headers: {
        "Content-Type": blob.type || "application/octet-stream",
      },
    });
  }),
});
```

## File Metadata

```typescript
export const getFileMetadata = query({
  args: { storageId: v.id("_storage") },
  handler: async (ctx, args) => {
    const metadata = await ctx.storage.getMetadata(args.storageId);
    // Returns: { contentType: string, size: number } or null
    return metadata;
  },
});
```

## Deleting Files

```typescript
export const deleteFile = mutation({
  args: { storageId: v.id("_storage") },
  handler: async (ctx, args) => {
    // Delete from storage
    await ctx.storage.delete(args.storageId);

    // Also clean up any database references
    const fileDoc = await ctx.db
      .query("files")
      .withIndex("by_storage", (q) => q.eq("storageId", args.storageId))
      .unique();
    if (fileDoc) {
      await ctx.db.delete(fileDoc._id);
    }
  },
});
```

## Schema for Files

```typescript
// convex/schema.ts
export default defineSchema({
  files: defineTable({
    storageId: v.id("_storage"),
    name: v.string(),
    uploadedBy: v.id("users"),
    uploadedAt: v.number(),
  })
    .index("by_storage", ["storageId"])
    .index("by_user", ["uploadedBy"]),
});
```

## Storage API Reference

| Method | Available In | Description |
|--------|-------------|-------------|
| `ctx.storage.generateUploadUrl()` | Mutations | Get a presigned upload URL |
| `ctx.storage.store(blob)` | Actions, HTTP Actions | Store a Blob directly |
| `ctx.storage.get(id)` | Actions, HTTP Actions | Get file as Blob |
| `ctx.storage.getUrl(id)` | Queries, Mutations | Get a serving URL |
| `ctx.storage.getMetadata(id)` | Queries, Mutations | Get content type and size |
| `ctx.storage.delete(id)` | Mutations | Delete a stored file |

## Common Patterns

### Image with Fallback

```tsx
function Avatar({ storageId }: { storageId?: Id<"_storage"> }) {
  const url = useQuery(api.files.getFileUrl, storageId ? { storageId } : "skip");
  return <img src={url || "/default-avatar.png"} alt="Avatar" />;
}
```

### Multiple File Upload

```tsx
async function uploadMultiple(files: File[]) {
  const results = await Promise.all(
    files.map(async (file) => {
      const uploadUrl = await generateUploadUrl();
      const res = await fetch(uploadUrl, {
        method: "POST",
        headers: { "Content-Type": file.type },
        body: file,
      });
      const { storageId } = await res.json();
      return { storageId, name: file.name };
    })
  );
  // Save all references in one mutation
  await saveFiles({ files: results });
}
```

## Related References

- HTTP actions: `02-functions-actions-http.md`
- Database schemas: `03-database-schemas.md`
- React client: `09-react-client.md`
