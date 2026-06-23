# Turso ORM Integrations

> Source: [docs.turso.tech/sdk/ts/orm](https://docs.turso.tech/sdk/ts/orm/drizzle)

## Table of Contents
- [Drizzle ORM](#drizzle-orm)
- [Prisma](#prisma)
- [SQLAlchemy (Python)](#sqlalchemy-python)
- [Vector Columns with Drizzle](#vector-columns-with-drizzle)
- [Common Pitfalls](#common-pitfalls)

## Drizzle ORM

### Installation

```bash
npm install drizzle-orm @libsql/client
npm install -D drizzle-kit dotenv
```

### Package.json Scripts

```json
{
  "scripts": {
    "db:generate": "drizzle-kit generate",
    "db:migrate": "drizzle-kit migrate",
    "db:studio": "drizzle-kit studio"
  }
}
```

### Drizzle Config

```typescript
// drizzle.config.ts
import { defineConfig } from "drizzle-kit";

export default defineConfig({
  schema: "./db/schema.ts",
  out: "./migrations",
  dialect: "turso",
  dbCredentials: {
    url: process.env.TURSO_DATABASE_URL!,
    authToken: process.env.TURSO_AUTH_TOKEN!,
  },
});
```

### Schema Definition

```typescript
// db/schema.ts
import { sql } from "drizzle-orm";
import { integer, text, sqliteTable, real } from "drizzle-orm/sqlite-core";

export const users = sqliteTable("users", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  name: text("name").notNull(),
  email: text("email").notNull().unique(),
  createdAt: text("created_at").default(sql`(datetime('now'))`),
});

export const posts = sqliteTable("posts", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  userId: integer("user_id").notNull().references(() => users.id),
  title: text("title").notNull(),
  content: text("content"),
  published: integer("published", { mode: "boolean" }).default(false),
});
```

### Client Setup

```typescript
// db/client.ts
import { drizzle } from "drizzle-orm/libsql";
import { createClient } from "@libsql/client";
import * as schema from "./schema";

// Remote
const client = createClient({
  url: process.env.TURSO_DATABASE_URL!,
  authToken: process.env.TURSO_AUTH_TOKEN!,
});

// Local development
// const client = createClient({ url: "file:local.db" });

// Edge runtime
// import { createClient } from "@libsql/client/web";

export const db = drizzle(client, { schema });
```

### Migrations

```bash
# Generate migration files from schema changes
npm run db:generate

# Apply migrations to database
npm run db:migrate

# Open Drizzle Studio (visual DB manager)
npm run db:studio
```

### Querying

```typescript
import { db } from "./db/client";
import { users, posts } from "./db/schema";
import { eq, desc, and } from "drizzle-orm";

// Insert
const newUser = await db.insert(users).values({
  name: "Alice",
  email: "alice@example.com",
}).returning();

// Select all
const allUsers = await db.select().from(users);

// Filtered query
const user = await db.select().from(users).where(eq(users.id, 1));

// Join
const postsWithAuthors = await db
  .select({
    postTitle: posts.title,
    authorName: users.name,
  })
  .from(posts)
  .innerJoin(users, eq(posts.userId, users.id))
  .where(eq(posts.published, true))
  .orderBy(desc(posts.id));

// Update
await db.update(users).set({ name: "Alice Updated" }).where(eq(users.id, 1));

// Delete
await db.delete(users).where(eq(users.id, 1));

// Upsert
await db.insert(users)
  .values({ id: 1, name: "Alice", email: "alice@example.com" })
  .onConflictDoUpdate({
    target: users.email,
    set: { name: "Alice Updated" },
  });
```

### Batch Operations with Drizzle

```typescript
const results = await db.batch([
  db.insert(users).values({ name: "Alice", email: "a@test.com" }),
  db.insert(users).values({ name: "Bob", email: "b@test.com" }),
  db.select().from(users),
]);
```

## Prisma

### Installation

```bash
npm install prisma @prisma/client @prisma/adapter-libsql @libsql/client
npx prisma init --datasource-provider sqlite
```

### Schema

```prisma
// prisma/schema.prisma
generator client {
  provider        = "prisma-client-js"
  previewFeatures = ["driverAdapters"]
}

datasource db {
  provider = "sqlite"
  url      = "file:./dev.db"
}

model User {
  id        Int      @id @default(autoincrement())
  name      String
  email     String   @unique
  posts     Post[]
  createdAt DateTime @default(now())
}

model Post {
  id        Int      @id @default(autoincrement())
  title     String
  content   String?
  published Boolean  @default(false)
  author    User     @relation(fields: [authorId], references: [id])
  authorId  Int
}
```

### Client Setup with Turso Adapter

```typescript
import { PrismaClient } from "@prisma/client";
import { PrismaLibSQL } from "@prisma/adapter-libsql";
import { createClient } from "@libsql/client";

const libsql = createClient({
  url: process.env.TURSO_DATABASE_URL!,
  authToken: process.env.TURSO_AUTH_TOKEN!,
});

const adapter = new PrismaLibSQL(libsql);
const prisma = new PrismaClient({ adapter });
```

### Migrations

```bash
# Generate migration
npx prisma migrate dev --name init

# Apply to production
npx prisma migrate deploy

# Push schema without migration (dev only)
npx prisma db push
```

### Querying

```typescript
// Create
const user = await prisma.user.create({
  data: { name: "Alice", email: "alice@example.com" },
});

// Find
const users = await prisma.user.findMany({
  where: { name: { contains: "Alice" } },
  include: { posts: true },
});

// Update
await prisma.user.update({
  where: { id: 1 },
  data: { name: "Alice Updated" },
});

// Delete
await prisma.user.delete({ where: { id: 1 } });
```

## SQLAlchemy (Python)

### Installation

```bash
pip install sqlalchemy libsql
```

### Connection Setup

```python
from sqlalchemy import create_engine, Column, Integer, String, text
from sqlalchemy.orm import declarative_base, Session
import os

# Remote Turso connection
url = os.environ["TURSO_DATABASE_URL"].replace("libsql://", "")
token = os.environ["TURSO_AUTH_TOKEN"]
engine = create_engine(
    f"sqlite+libsql://{url}?authToken={token}&secure=true",
    echo=False,
)

# Local development
# engine = create_engine("sqlite+libsql:///app.db")
```

### ORM Models

```python
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)

# Create tables
Base.metadata.create_all(engine)
```

### Querying

```python
with Session(engine) as session:
    # Create
    user = User(name="Alice", email="alice@example.com")
    session.add(user)
    session.commit()

    # Read
    users = session.query(User).filter(User.name.like("%Alice%")).all()

    # Update
    user = session.query(User).filter_by(id=1).first()
    user.name = "Alice Updated"
    session.commit()

    # Delete
    session.query(User).filter_by(id=1).delete()
    session.commit()
```

## Vector Columns with Drizzle

Drizzle supports Turso's native vector type through custom column definitions:

```typescript
import { customType, sqliteTable, text, integer } from "drizzle-orm/sqlite-core";
import { sql } from "drizzle-orm";

// Define custom vector type
const float32Array = customType<{ data: number[]; driverData: Buffer }>({
  dataType() {
    return "F32_BLOB(1536)";
  },
  toDriver(value: number[]): Buffer {
    return Buffer.from(new Float32Array(value).buffer);
  },
  fromDriver(value: Buffer): number[] {
    return Array.from(new Float32Array(value.buffer));
  },
});

// Use in schema
export const documents = sqliteTable("documents", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  title: text("title").notNull(),
  content: text("content"),
  embedding: float32Array("embedding"),
});

// Insert with raw SQL for vector conversion
await db.run(sql`
  INSERT INTO documents (title, content, embedding)
  VALUES (${title}, ${content}, vector32(${JSON.stringify(embedding)}))
`);

// Query with vector distance
const results = await db.all(sql`
  SELECT title, content
  FROM vector_top_k('docs_idx', vector32(${JSON.stringify(queryVec)}), 10) AS v
  JOIN documents d ON d.rowid = v.id
`);
```

## Common Pitfalls

1. **Drizzle dialect** — Use `dialect: "turso"` in drizzle.config.ts, not `"sqlite"`
2. **Prisma driver adapter** — Must enable `previewFeatures = ["driverAdapters"]` in schema.prisma
3. **Prisma migration target** — Prisma migrations run against the datasource URL. For Turso Cloud, you need to push migrations, then the adapter handles runtime queries
4. **SQLAlchemy URL format** — Replace `libsql://` with empty string and use `sqlite+libsql://` scheme
5. **Edge runtime** — Use `@libsql/client/web` import for Cloudflare Workers / Vercel Edge
6. **Vector operations** — ORMs don't natively support vector functions. Use raw SQL (`sql` tagged template in Drizzle, `text()` in SQLAlchemy) for vector operations
