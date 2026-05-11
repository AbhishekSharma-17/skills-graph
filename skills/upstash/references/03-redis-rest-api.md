# Upstash Redis — REST API

## Table of Contents

- [Authentication](#authentication)
- [Command Format](#command-format)
- [Response Format](#response-format)
- [Pipeline API](#pipeline-api)
- [Transaction API](#transaction-api-multiexec)
- [Pub/Sub via REST](#pubsub-via-rest)
- [ACL REST Tokens](#acl-rest-tokens)
- [Supported Commands](#supported-command-categories)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

Upstash Redis exposes every Redis command through a stateless HTTP/REST
interface — no TCP connections, no client libraries required.

- **Base URL**: `https://{region}-{name}-{id}.upstash.io`
- **All standard Redis commands** mapped to URL paths (GET, POST, PUT, HEAD)
- **Edge-compatible** — works from serverless functions, edge workers, and browsers

---

## Authentication

Every request must be authenticated using one of two methods.

```bash
# Header-based (recommended)
curl https://us1-example-12345.upstash.io/get/mykey \
  -H "Authorization: Bearer $UPSTASH_REDIS_REST_TOKEN"

# Query parameter (avoid — tokens appear in logs)
curl "https://us1-example-12345.upstash.io/get/mykey?_token=$UPSTASH_REDIS_REST_TOKEN"
```

### Token Types

| Token Type    | Access Level               | Use Case                        |
|---------------|----------------------------|---------------------------------|
| Standard      | Full read/write access     | Server-side applications        |
| Read-Only     | Only read commands allowed | Client-side or public-facing    |

The read-only token rejects write commands (`SET`, `DEL`, `LPUSH`, etc.) with
`NOPERM` errors.

---

## Command Format

Redis commands map directly to URL path segments: `REST_URL/COMMAND/arg1/arg2/.../argN`

```bash
# SET / GET
curl .../set/foo/bar -H "Authorization: Bearer $TOKEN"       # {"result":"OK"}
curl .../get/foo -H "Authorization: Bearer $TOKEN"            # {"result":"bar"}

# SET with expiration
curl .../set/foo/bar/EX/100 -H "Authorization: Bearer $TOKEN" # {"result":"OK"}

# HSET / HGETALL (hash)
curl .../hset/user:1/name/Alice/role/admin -H "Authorization: Bearer $TOKEN"
# {"result":2}
curl .../hgetall/user:1 -H "Authorization: Bearer $TOKEN"
# {"result":["name","Alice","role","admin"]}

# LPUSH / LRANGE (list)
curl .../lpush/mylist/item1/item2 -H "Authorization: Bearer $TOKEN" # {"result":2}
curl .../lrange/mylist/0/-1 -H "Authorization: Bearer $TOKEN"
# {"result":["item2","item1"]}
```

---

## POST with JSON/Binary Body

For values with special characters, whitespace, or structured data, use POST.

```bash
# JSON value in body
curl -X POST .../set/user:1 -H "Authorization: Bearer $TOKEN" \
  -d '{"name":"Alice","age":30,"roles":["admin","editor"]}'

# Command as JSON array (avoids URL-encoding issues)
curl -X POST https://us1-example-12345.upstash.io \
  -H "Authorization: Bearer $TOKEN" \
  -d '["SET", "foo", "bar", "EX", 100]'

# Binary data
curl -X POST .../set/binkey -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/octet-stream" --data-binary @file.bin
```

---

## Response Format

All responses are JSON with either a `result` or `error` field.

```json
{"result": "OK"}           // Simple string
{"result": 137}            // Integer
{"result": "stored-value"} // Bulk string
{"result": ["a", null]}    // Array
{"result": null}           // Nil
{"error": "ERR wrong number of arguments for 'get' command"}
```

### Response Encoding

- **Base64**: Add `Upstash-Encoding: base64` header — all string values returned base64-encoded (except `"OK"`)
- **RESP2**: Add `Upstash-Response-Format: resp2` header — raw Redis RESP2 binary format
- **Cannot combine** `resp2` and `base64` in the same request

---

## HTTP Status Codes

| Code | Meaning                                       |
|------|-----------------------------------------------|
| 200  | Command executed (always check `result`/`error` in body) |
| 400  | Syntax error or command failure               |
| 401  | Missing or invalid token                      |
| 405  | Unsupported HTTP method                       |

---

## Pipeline API

Send multiple commands in a single HTTP request via `POST /pipeline`.

```bash
curl -X POST https://us1-example-12345.upstash.io/pipeline \
  -H "Authorization: Bearer $TOKEN" \
  -d '[
    ["SET", "key1", "valuex"],
    ["SETEX", "key2", 13, "valuez"],
    ["INCR", "key1"],
    ["ZADD", "myset", 11, "item1", 22, "item2"]
  ]'
# Response: [{"result":"OK"},{"result":"OK"},{"error":"ERR value is not an integer..."},{"result":2}]
```

- Commands execute **sequentially** but are **NOT atomic** — other clients can interleave
- A failing command does **not** abort the remaining commands
- Use `/multi-exec` instead if you need atomicity

---

## Transaction API (MULTI/EXEC)

Atomic command execution via `POST /multi-exec` — same body format as pipeline.

```bash
curl -X POST https://us1-example-12345.upstash.io/multi-exec \
  -H "Authorization: Bearer $TOKEN" \
  -d '[
    ["DECRBY", "account:alice", 50],
    ["INCRBY", "account:bob", 50],
    ["LPUSH", "transfers:log", "alice->bob:50"]
  ]'
# Response: [{"result":50},{"result":150},{"result":1}]
```

- **Atomic** — no interleaving from other clients
- Transactions are **discarded entirely** on: syntax errors, unsupported commands, body size exceeded, daily limit exceeded
- Runtime errors (e.g., `INCR` on non-integer) do **not** discard — other commands still execute

---

## Pub/Sub via REST

Subscribers use Server-Sent Events (SSE); publishers use standard REST calls.

```bash
# Subscribe to channel(s) — SSE stream
curl -N -X POST .../subscribe/chat/notifications \
  -H "Authorization: Bearer $TOKEN" -H "Accept: text/event-stream"

# Pattern subscribe
curl -N -X POST .../psubscribe/chat:* \
  -H "Authorization: Bearer $TOKEN" -H "Accept: text/event-stream"

# Publish (returns subscriber count)
curl -X POST .../publish/chat/hello -H "Authorization: Bearer $TOKEN"
# {"result":2}
```

---

## Monitor (SSE)

`POST /monitor` streams all commands in real-time via SSE (debugging only, adds overhead in production).

---

## ACL REST Tokens

Create fine-grained REST tokens associated with ACL users.

```bash
# Create ACL user and generate REST token
redis-cli> ACL SETUSER readonlyuser on >secretpass ~cached:* +get +mget +hget +hgetall
redis-cli> ACL RESTTOKEN readonlyuser secretpass
# "AYNgAS..."

# Use the custom token (restricted to cached:* keys and read commands)
curl .../get/cached:homepage -H "Authorization: Bearer AYNgAS..."
```

Benefits: restrict commands per token, restrict key patterns, multiple permission
levels, independent token rotation.

---

## Supported Command Categories

**Supported**: Strings, Hashes, Lists, Sets, Sorted Sets, Bitmaps, Geo,
HyperLogLog, Transactions (`/multi-exec`), Generic (DEL, EXISTS, EXPIRE, TTL,
SCAN), Server (DBSIZE, INFO), Scripting (EVAL), Pub/Sub (via SSE), JSON
(JSON.SET/GET/DEL), Streams (non-blocking), Connection (PING, ECHO).

**Not supported**: Cluster commands, blocking operations (BLPOP, BRPOP, BLMOVE,
BZPOPMIN, BZPOPMAX, XREADGROUP BLOCK, WAIT), DEBUG/OBJECT/SLOWLOG, CLIENT
commands. Use polling or Pub/Sub SSE instead of blocking ops.

---

## Common Pitfalls

- **Pipeline is NOT atomic** — use `/multi-exec` when atomicity matters, not `/pipeline`
- **Read-only tokens cannot write** — verify which token your app uses, especially client-side
- **URL-encode special characters** in path segments (`%20` for space, `%2F` for slash) or use POST body with JSON array to avoid encoding
- **Max request body size** — split large pipeline/transaction batches into smaller chunks
- **RESP2 and Base64 are mutually exclusive** — choose one per request
- **Daily request limits** (free tier) — transactions discard entirely when exceeded
- **HTTP timeout ~30s** — use `SCAN` instead of `KEYS *` on large databases
