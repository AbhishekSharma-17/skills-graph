# Changelog — Upstash

All notable changes to this skill are documented here.

Format: `[Skill Version] - YYYY-MM-DD (Source vX.Y.Z)`

---

## [1.0.0] - 2026-05-12 (Source @upstash/redis v1.38.0)

### Added
- Initial skill creation covering the full Upstash serverless data platform
- Redis SDK (TypeScript): initialization, environment variables, auto-pipelining
- Redis commands: strings, hashes, lists, sets, sorted sets, JSON, streams, scripting
- REST API: HTTP endpoints, authentication, pipelining, transactions, pub/sub
- Rate limiting: algorithms (fixed window, sliding window, token bucket), configuration
- QStash messaging: publishing, scheduling, queues, callbacks, DLQ, batching
- Workflow: durable functions, context methods, error handling, parallel steps
- Vector database: embeddings, similarity search, metadata filtering, hybrid search
- Python SDKs: upstash-redis, upstash-qstash, upstash-vector, upstash-ratelimit
- Framework integrations: Next.js, Cloudflare Workers, Vercel, AWS Lambda, Deno
- Patterns & recipes: caching, sessions, leaderboards, pub/sub, job queues
- Search & Realtime: full-text search, channel messaging, authentication
- VERSION.json with per-file tracking
- AUDIT-REPORT.md with initial scorecard
- Maintenance script: scripts/check-updates.py

### Reference Files
| File | Lines | Type |
|------|-------|------|
| `00-overview.md` | ~339 | Leaf |
| `01-redis-sdk-typescript.md` | ~414 | Leaf |
| `02-redis-commands.md` | ~449 | Leaf |
| `03-redis-rest-api.md` | ~241 | Leaf |
| `04-rate-limiting.md` | ~368 | Leaf |
| `05-qstash-messaging.md` | ~424 | Leaf |
| `06-workflow.md` | ~433 | Leaf |
| `07-vector-database.md` | ~419 | Leaf |
| `08-python-sdks.md` | ~345 | Leaf |
| `09-framework-integrations.md` | ~420 | Leaf |
| `10-patterns-recipes.md` | ~399 | Leaf |
| `11-search-realtime.md` | ~403 | Leaf |

### Stats
- Routing entries: 12
- Reference files: 12
- Total lines: ~4,654
