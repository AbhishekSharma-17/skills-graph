# Upstash Redis — Commands Reference

Complete reference for all Redis commands supported by the `@upstash/redis` SDK. All methods are available on the `Redis` client instance and return promises.

## Table of Contents

- [String Commands](#string-commands)
- [Hash Commands](#hash-commands)
- [List Commands](#list-commands)
- [Set Commands](#set-commands)
- [Sorted Set Commands](#sorted-set-commands)
- [JSON Commands](#json-commands)
- [Stream Commands](#stream-commands)
- [Key Management Commands](#key-management-commands)
- [Scripting](#scripting)
- [Pub/Sub](#pubsub)
- [Server Commands](#server-commands)
- [Unsupported Commands](#unsupported-commands)

---

## String Commands

Strings are the most basic Redis data type and can hold any serializable data.

```ts
// SET with options
set(key, value, opts?): Promise<"OK" | T | null>
// opts: { ex, px, exat, pxat, nx, xx, get }
//   ex: seconds TTL | px: milliseconds TTL
//   exat/pxat: Unix timestamp expiry (seconds/ms)
//   nx: only set if not exists | xx: only set if exists
//   get: return old value

// GET variants
get<T>(key): Promise<T | null>
getdel<T>(key): Promise<T | null>          // get and delete
getrange(key, start, end): Promise<string>
getset<T>(key, value): Promise<T | null>   // set new, return old

// Increment / Decrement
incr(key): Promise<number>
incrby(key, amount): Promise<number>
incrbyfloat(key, amount): Promise<number>
decr(key): Promise<number>
decrby(key, amount): Promise<number>

// Multi-key
mget<T>(...keys): Promise<(T | null)[]>
mset(kv: Record<string, TValue>): Promise<"OK">
msetnx(kv: Record<string, TValue>): Promise<0 | 1>

// String manipulation
append(key, value): Promise<number>     // returns new length
strlen(key): Promise<number>
setrange(key, offset, value): Promise<number>
```

```ts
await redis.set("greeting", "hello", { ex: 60 });
const val = await redis.get<string>("greeting");   // "hello"
await redis.incr("counter");                       // 1
await redis.mset({ k1: "a", k2: "b" });
await redis.mget("k1", "k2");                      // ["a", "b"]
```

---

## Hash Commands

Hash commands operate on keys holding field-value pair maps. Useful for representing objects.

```ts
// Core operations
hset(key, field, value): Promise<number>
hset(key, kv: Record<string, TValue>): Promise<number>
hget<T>(key, field): Promise<T | null>
hgetall<T>(key): Promise<T | null>
hdel(key, ...fields): Promise<number>
hexists(key, field): Promise<0 | 1>

// Numeric
hincrby(key, field, amount): Promise<number>
hincrbyfloat(key, field, amount): Promise<number>

// Inspection
hkeys(key): Promise<string[]>
hvals<T>(key): Promise<T[]>
hlen(key): Promise<number>

// Multi-field / conditional
hmget<T>(key, ...fields): Promise<(T | null)[]>
hsetnx(key, field, value): Promise<0 | 1>

// Scanning
hscan(key, cursor, opts?): Promise<[number, string[]]>
// opts: { match?: string, count?: number }

// Field expiration
hexpire(key, seconds, ...fields): Promise<number[]>
httl(key, ...fields): Promise<number[]>

// Get-and-modify
hgetdel(key, ...fields): Promise<(string | null)[]>
hgetex(key, opts, ...fields): Promise<(string | null)[]>
hsetex(key, opts, values): Promise<number>
// opts: { ex?, px?, exat?, pxat?, persist? }
```

```ts
await redis.hset("user:1", { name: "Alice", age: "30" });
const name = await redis.hget<string>("user:1", "name");  // "Alice"
const user = await redis.hgetall("user:1");  // { name: "Alice", age: "30" }
await redis.hsetex("session:1", { ex: 3600 }, { token: "abc", user: "alice" });
```

---

## List Commands

Lists are ordered sequences of string values with push/pop from both ends.

```ts
// Push / Pop
lpush(key, ...values): Promise<number>
rpush(key, ...values): Promise<number>
lpop<T>(key, count?): Promise<T | T[] | null>
rpop<T>(key, count?): Promise<T | T[] | null>
lpushx(key, ...values): Promise<number>   // only if key exists
rpushx(key, ...values): Promise<number>   // only if key exists

// Access
lrange<T>(key, start, stop): Promise<T[]>
lindex<T>(key, index): Promise<T | null>
llen(key): Promise<number>
lpos(key, element): Promise<number | null>

// Modification
linsert(key, "BEFORE"|"AFTER", pivot, element): Promise<number>
lset(key, index, element): Promise<"OK">
ltrim(key, start, stop): Promise<"OK">
lmove(source, dest, from, to): Promise<string | null>
// from/to: "LEFT" | "RIGHT"
lrem(key, count, element): Promise<number>
```

```ts
await redis.lpush("tasks", "task1", "task2");
const all = await redis.lrange("tasks", 0, -1);  // ["task2", "task1"]
const item = await redis.lpop<string>("tasks");   // "task2"
```

---

## Set Commands

Sets are unordered collections of unique string values.

```ts
// Add / Remove
sadd(key, ...members): Promise<number>
srem(key, ...members): Promise<number>

// Query
smembers<T>(key): Promise<T[]>
sismember(key, member): Promise<0 | 1>
scard(key): Promise<number>

// Random
spop<T>(key, count?): Promise<T | T[] | null>
srandmember<T>(key, count?): Promise<T | T[] | null>

// Set operations (return elements)
sdiff<T>(...keys): Promise<T[]>
sinter<T>(...keys): Promise<T[]>
sunion<T>(...keys): Promise<T[]>

// Set operations (store result)
sdiffstore(dest, ...keys): Promise<number>
sinterstore(dest, ...keys): Promise<number>
sunionstore(dest, ...keys): Promise<number>

// Utility
smove(source, dest, member): Promise<0 | 1>
sscan(key, cursor, opts?): Promise<[number, string[]]>
// opts: { match?: string, count?: number }
```

```ts
await redis.sadd("tags", "redis", "serverless");
const tags = await redis.smembers("tags");            // ["redis", "serverless"]
await redis.sadd("s1", "a", "b", "c");
await redis.sadd("s2", "b", "c", "d");
const diff = await redis.sdiff("s1", "s2");           // ["a"]
```

---

## Sorted Set Commands

Sorted sets associate a score with each member for ordering.

```ts
// Add
zadd(key, opts?, ...scoreMembers): Promise<number | null>
// opts: { nx, xx, gt, lt, ch, incr }
// scoreMembers: { score: number, member: TValue }

// Range queries
zrange<T>(key, min, max, opts?): Promise<T[]>
// opts: { rev, byScore, byLex, offset, count, withScores }

// Rank / Score
zrank(key, member): Promise<number | null>
zrevrank(key, member): Promise<number | null>
zscore(key, member): Promise<number | null>
zmscore(key, ...members): Promise<(number | null)[]>

// Remove / Count
zrem(key, ...members): Promise<number>
zcard(key): Promise<number>
zcount(key, min, max): Promise<number>

// Increment
zincrby(key, increment, member): Promise<number>

// Pop
zpopmax<T>(key, count?): Promise<T[]>
zpopmin<T>(key, count?): Promise<T[]>

// Range removal
zremrangebyrank(key, start, stop): Promise<number>
zremrangebyscore(key, min, max): Promise<number>
zremrangebylex(key, min, max): Promise<number>

// Store operations
zinterstore(dest, numkeys, ...keys): Promise<number>
zunionstore(dest, numkeys, ...keys): Promise<number>
zdiffstore(dest, numkeys, ...keys): Promise<number>

// Scanning
zscan(key, cursor, opts?): Promise<[number, string[]]>
```

```ts
await redis.zadd("leaderboard", { score: 100, member: "player1" });
const top = await redis.zrange("leaderboard", 0, 2, { rev: true });
await redis.zincrby("leaderboard", 50, "player1");    // 150
const scores = await redis.zmscore("leaderboard", "player1", "player2");
```

---

## JSON Commands

All JSON methods are accessed via `redis.json.*`. Paths use JSONPath syntax (`$` = root).

```ts
// Core
redis.json.set(key, path, value): Promise<"OK">
redis.json.get(key, ...paths): Promise<any>
redis.json.del(key, path?): Promise<number>
redis.json.clear(key, path?): Promise<number>

// Multi-key
redis.json.mget(keys, path): Promise<any[]>
redis.json.mset(...entries: [key, path, value][]): Promise<"OK">
redis.json.merge(key, path, value): Promise<"OK">

// Array operations
redis.json.arrappend(key, path, ...values): Promise<number[]>
redis.json.arrinsert(key, path, index, ...values): Promise<number[]>
redis.json.arrindex(key, path, value): Promise<number[]>
redis.json.arrlen(key, path): Promise<number[]>
redis.json.arrpop(key, path, index?): Promise<any[]>
redis.json.arrtrim(key, path, start, stop): Promise<number[]>

// Numeric
redis.json.numincrby(key, path, value): Promise<string>
redis.json.nummultby(key, path, value): Promise<string>

// Object inspection
redis.json.objkeys(key, path?): Promise<string[][]>
redis.json.objlen(key, path?): Promise<number[]>

// String operations
redis.json.strappend(key, path, value): Promise<number[]>
redis.json.strlen(key, path): Promise<number[]>

// Utility
redis.json.toggle(key, path): Promise<number[]>
redis.json.type(key, path?): Promise<string[]>
```

```ts
await redis.json.set("doc", "$", { name: "Alice", scores: [95, 87] });
const doc = await redis.json.get("doc", "$");
await redis.json.arrappend("doc", "$.scores", 92);
await redis.json.toggle("doc", "$.active");
const keys = await redis.json.objkeys("doc", "$");
```

---

## Stream Commands

Streams provide append-only log data structures for event sourcing and message queues.

```ts
// Basic operations
xadd(key, id, fields: Record<string, string>): Promise<string>
xlen(key): Promise<number>
xrange(key, start, end, count?): Promise<StreamEntry[]>
xrevrange(key, end, start, count?): Promise<StreamEntry[]>
xdel(key, ...ids): Promise<number>
xtrim(key, strategy: "MAXLEN"|"MINID", threshold): Promise<number>

// Reading
xread(streams: { key, id }[], opts?: { count }): Promise<StreamReadResult[]>

// Consumer groups
xgroup("CREATE", key, group, id): Promise<"OK">
xreadgroup(group, consumer, streams, opts?): Promise<StreamReadResult[]>
xack(key, group, ...ids): Promise<number>
xclaim(key, group, consumer, minIdleTime, ...ids): Promise<StreamEntry[]>
xautoclaim(key, group, consumer, minIdleTime, start, opts?): Promise<XAutoclaimResult>
xpending(key, group, opts?): Promise<XPendingResult>

// Info
xinfo("STREAM", key): Promise<StreamInfo>
```

```ts
const id = await redis.xadd("events", "*", { type: "click", page: "/home" });
const entries = await redis.xrange("events", "-", "+", 10);
```

---

## Key Management Commands

Key management commands operate on keys regardless of their value type.

```ts
// Delete / Exists
del(...keys): Promise<number>
unlink(...keys): Promise<number>      // async delete (background reclaim)
exists(...keys): Promise<number>

// Expiration
expire(key, seconds): Promise<0 | 1>
pexpire(key, ms): Promise<0 | 1>
expireat(key, timestamp): Promise<0 | 1>
pexpireat(key, timestampMs): Promise<0 | 1>
persist(key): Promise<0 | 1>          // remove expiration

// TTL (returns -1 if no expiry, -2 if key missing)
ttl(key): Promise<number>
pttl(key): Promise<number>

// Rename
rename(key, newkey): Promise<"OK">
renamenx(key, newkey): Promise<0 | 1>

// Discovery
type(key): Promise<string>
scan(cursor, opts?): Promise<[number, string[]]>
// opts: { match?, count?, type? }
keys(pattern): Promise<string[]>       // avoid in production
randomkey(): Promise<string | null>
touch(...keys): Promise<number>
```

```ts
await redis.expire("temp", 300);
const remaining = await redis.ttl("temp");  // 300
await redis.del("key1", "key2");

let cursor = 0;
do {
  const [next, keys] = await redis.scan(cursor, { match: "user:*", count: 100 });
  cursor = next;
} while (cursor !== 0);
```

---

## Scripting

Execute Lua scripts atomically on the server.

```ts
eval(script, keys: string[], args: string[]): Promise<any>
evalsha(sha, keys: string[], args: string[]): Promise<any>
scriptLoad(script): Promise<string>
scriptExists(...shas): Promise<number[]>
scriptFlush(): Promise<"OK">
```

```ts
const sha = await redis.scriptLoad("return redis.call('get', KEYS[1])");
const result = await redis.evalsha(sha, ["mykey"], []);
```

---

## Pub/Sub

Upstash supports the publish side of Pub/Sub over the REST API.

```ts
publish(channel, message): Promise<number>  // returns subscriber count
```

```ts
const receivers = await redis.publish("notifications", "Hello!");
```

> **Note:** `SUBSCRIBE` / `PSUBSCRIBE` require persistent connections and are not available in the REST SDK. Use the Upstash SSE endpoint for subscribing.

---

## Server Commands

```ts
dbsize(): Promise<number>
flushall(): Promise<"OK">
flushdb(): Promise<"OK">
```

```ts
const count = await redis.dbsize();
```

---

## Unsupported Commands

The following are not supported due to the serverless HTTP-based architecture:

| Category | Commands |
|---|---|
| **Cluster** | All cluster management commands (`CLUSTER *`) |
| **Blocking operations** | `BLPOP`, `BRPOP`, `BLMOVE`, `BZPOPMIN`, `BZPOPMAX`, `BLMPOP`, `BZMPOP` |
| **Transaction watch** | `WATCH`, `UNWATCH` |
| **Connection** | `WAIT`, `CLIENT` (except `CLIENT SETINFO`) |
| **Debug** | `DEBUG`, `SLOWLOG`, `MEMORY DOCTOR` |

Blocking commands are incompatible with the stateless REST protocol. Use polling with `LPOP`/`RPOP` or QStash for queue-based workloads.
