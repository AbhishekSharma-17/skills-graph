# Prisma Raw Queries

> Source: [prisma.io/docs/orm/prisma-client/queries/raw-database-access](https://www.prisma.io/docs/orm/prisma-client/queries/raw-database-access) — Prisma ORM v7.x

## Table of Contents

- [When to Use Raw Queries](#when-to-use-raw-queries)
- [$queryRaw — Safe Read Queries](#queryraw--safe-read-queries)
- [$executeRaw — Safe Write Queries](#executeraw--safe-write-queries)
- [Unsafe Variants](#unsafe-variants)
- [Prisma.sql Helper](#prismasql-helper)
- [Typed Results](#typed-results)
- [TypedSQL](#typedsql)
- [MongoDB Raw Commands](#mongodb-raw-commands)
- [SQL Injection Prevention](#sql-injection-prevention)
- [Common Patterns](#common-patterns)
- [Limitations](#limitations)

---

## When to Use Raw Queries

Use raw queries when:
- Prisma Client doesn't support a specific SQL feature (e.g., CTEs, window functions)
- You need database-specific syntax (PostgreSQL `EXPLAIN`, `COPY`, `LISTEN/NOTIFY`)
- Performance-critical queries where hand-tuned SQL is needed
- Complex aggregations, pivots, or recursive queries
- Full-text search with database-specific syntax

Prefer Prisma Client for standard CRUD — it's type-safe and prevents SQL injection.

## $queryRaw — Safe Read Queries

Returns an array of records using tagged template literals:

```typescript
// Basic query
const users = await prisma.$queryRaw`SELECT * FROM "User"`;

// With parameters (automatically parameterized — SQL injection safe)
const email = "alice@example.com";
const users = await prisma.$queryRaw`
  SELECT * FROM "User" WHERE email = ${email}
`;

// Multiple parameters
const users = await prisma.$queryRaw`
  SELECT * FROM "User"
  WHERE role = ${role}
  AND "createdAt" > ${startDate}
  ORDER BY "createdAt" DESC
  LIMIT ${limit}
`;
```

### How Parameters Work

Tagged template literals create parameterized queries — variables become `$1`, `$2`, etc. in PostgreSQL:

```typescript
// This code:
const name = "Alice";
await prisma.$queryRaw`SELECT * FROM "User" WHERE name = ${name}`;

// Becomes this SQL:
// SELECT * FROM "User" WHERE name = $1
// Parameters: ["Alice"]
```

## $executeRaw — Safe Write Queries

Returns the count of affected rows:

```typescript
// UPDATE
const count = await prisma.$executeRaw`
  UPDATE "User" SET active = true WHERE "lastLogin" > ${cutoffDate}
`;
console.log(`Updated ${count} users`);

// DELETE
const deleted = await prisma.$executeRaw`
  DELETE FROM "Session" WHERE "expiresAt" < ${new Date()}
`;

// INSERT
await prisma.$executeRaw`
  INSERT INTO "AuditLog" (action, "userId", "createdAt")
  VALUES (${action}, ${userId}, NOW())
`;
```

## Unsafe Variants

Accept raw strings instead of tagged templates. **Use only with trusted content**:

### $queryRawUnsafe

```typescript
// Dynamic table name (can't be parameterized)
const table = "User";
const users = await prisma.$queryRawUnsafe(
  `SELECT * FROM "${table}" WHERE role = $1`,
  "ADMIN"
);

// CAUTION: Never interpolate user input!
// This is vulnerable to SQL injection:
// const users = await prisma.$queryRawUnsafe(`SELECT * FROM "${userInput}"`);
```

### $executeRawUnsafe

```typescript
// Dynamic table or column names
const result = await prisma.$executeRawUnsafe(
  `ALTER TABLE "${tableName}" ADD COLUMN "${columnName}" TEXT`
);
```

### Parameterized Unsafe Queries

```typescript
// PostgreSQL: $1, $2, $3...
await prisma.$queryRawUnsafe(
  'SELECT * FROM "User" WHERE name = $1 AND role = $2',
  "Alice",
  "ADMIN"
);

// MySQL: ?
await prisma.$queryRawUnsafe(
  "SELECT * FROM User WHERE name = ? AND role = ?",
  "Alice",
  "ADMIN"
);
```

## Prisma.sql Helper

Build queries dynamically while maintaining safety:

```typescript
import { Prisma } from "./generated/prisma/index.js";

// Build a query fragment
const query = Prisma.sql`SELECT * FROM "User" WHERE name = ${name}`;
const result = await prisma.$queryRaw(query);

// Compose fragments
const where = Prisma.sql`WHERE role = ${role}`;
const orderBy = Prisma.sql`ORDER BY "createdAt" DESC`;
const result = await prisma.$queryRaw`
  SELECT * FROM "User" ${where} ${orderBy}
`;

// Dynamic IN clause
const ids = [1, 2, 3, 4, 5];
const result = await prisma.$queryRaw`
  SELECT * FROM "User" WHERE id IN (${Prisma.join(ids)})
`;

// Raw SQL (unescaped — use for known-safe identifiers only)
const column = "email";
const result = await prisma.$queryRaw`
  SELECT ${Prisma.raw(`"${column}"`)} FROM "User"
`;

// Empty query fragment
const maybeFilter = condition
  ? Prisma.sql`AND status = ${status}`
  : Prisma.empty;

const result = await prisma.$queryRaw`
  SELECT * FROM "User" WHERE active = true ${maybeFilter}
`;
```

## Typed Results

Specify the expected return type with generics:

```typescript
interface UserResult {
  id: number;
  email: string;
  name: string | null;
}

const users = await prisma.$queryRaw<UserResult[]>`
  SELECT id, email, name FROM "User" WHERE role = ${role}
`;
// users is typed as UserResult[]

// With aggregate
interface PostStats {
  authorId: number;
  postCount: bigint;
  avgViews: number;
}

const stats = await prisma.$queryRaw<PostStats[]>`
  SELECT "authorId", COUNT(*) as "postCount", AVG(views) as "avgViews"
  FROM "Post"
  GROUP BY "authorId"
`;
```

**Note**: Prisma doesn't validate that the actual query result matches your type — you're asserting the shape.

### Type Mapping Considerations

```typescript
// PostgreSQL COUNT returns BigInt
const result = await prisma.$queryRaw<{ count: bigint }[]>`
  SELECT COUNT(*) as count FROM "User"
`;
const count = Number(result[0].count); // Convert BigInt to number

// Decimal fields return Prisma.Decimal
const prices = await prisma.$queryRaw<{ price: Prisma.Decimal }[]>`
  SELECT price FROM "Product"
`;
```

## TypedSQL

Write SQL in `.sql` files with full type safety:

```sql
-- prisma/sql/getUsersByRole.sql
-- @param {String} $1:role
SELECT id, email, name FROM "User" WHERE role = $1::text
```

```bash
npx prisma generate --sql
```

```typescript
import { getUsersByRole } from "./generated/prisma/sql/index.js";

const admins = await prisma.$queryRawTyped(getUsersByRole("ADMIN"));
// Fully typed input and output
```

## MongoDB Raw Commands

```typescript
// Run a MongoDB command
const result = await prisma.$runCommandRaw({
  aggregate: "User",
  pipeline: [
    { $match: { role: "ADMIN" } },
    { $group: { _id: "$department", count: { $sum: 1 } } },
  ],
  cursor: {},
});

// Find raw
const users = await prisma.user.findRaw({
  filter: { role: "ADMIN" },
  options: { projection: { _id: 0, email: 1, name: 1 } },
});

// Aggregate raw
const result = await prisma.user.aggregateRaw({
  pipeline: [
    { $group: { _id: "$role", total: { $sum: 1 } } },
    { $sort: { total: -1 } },
  ],
});
```

## SQL Injection Prevention

### Safe Approaches (Recommended)

```typescript
// 1. Tagged template literals — always safe
const users = await prisma.$queryRaw`
  SELECT * FROM "User" WHERE email = ${userInput}
`;

// 2. Prisma.sql helper — safe composition
const query = Prisma.sql`SELECT * FROM "User" WHERE id = ${id}`;
await prisma.$queryRaw(query);

// 3. Parameterized unsafe queries — safe for values
await prisma.$queryRawUnsafe(
  'SELECT * FROM "User" WHERE email = $1',
  userInput
);
```

### Dangerous Patterns (Avoid)

```typescript
// NEVER interpolate user input into raw strings
await prisma.$queryRawUnsafe(
  `SELECT * FROM "User" WHERE email = '${userInput}'`  // SQL INJECTION!
);

// NEVER use user input for identifiers without validation
await prisma.$queryRawUnsafe(
  `SELECT * FROM "${userInput}"`  // SQL INJECTION!
);
```

## Common Patterns

### Complex Aggregation

```typescript
const stats = await prisma.$queryRaw<
  { month: string; signups: bigint; revenue: Prisma.Decimal }[]
>`
  SELECT
    TO_CHAR("createdAt", 'YYYY-MM') as month,
    COUNT(*) as signups,
    COALESCE(SUM(amount), 0) as revenue
  FROM "User"
  LEFT JOIN "Payment" ON "User".id = "Payment"."userId"
  WHERE "User"."createdAt" >= ${startDate}
  GROUP BY month
  ORDER BY month DESC
`;
```

### Full-Text Search (PostgreSQL)

```typescript
const results = await prisma.$queryRaw`
  SELECT id, title, ts_rank(search_vector, query) AS rank
  FROM "Post",
    to_tsquery('english', ${searchTerm}) query
  WHERE search_vector @@ query
  ORDER BY rank DESC
  LIMIT ${limit}
`;
```

### Raw Queries in Transactions

```typescript
await prisma.$transaction(async (tx) => {
  await tx.$executeRaw`
    UPDATE "Account" SET balance = balance - ${amount}
    WHERE id = ${fromId} AND balance >= ${amount}
  `;

  await tx.$executeRaw`
    UPDATE "Account" SET balance = balance + ${amount}
    WHERE id = ${toId}
  `;
});
```

## Limitations

1. **Single query per call** — Cannot append multiple statements (no `;` chaining)
2. **No dynamic identifiers** — Table/column names can't be template parameters
3. **No ALTER with safe methods** — PostgreSQL prepared statements don't support `ALTER`
4. **Type assertion only** — `$queryRaw<Type>` doesn't validate the actual result shape
5. **BigInt in results** — PostgreSQL `COUNT` returns `BigInt`; convert with `Number()` if needed
