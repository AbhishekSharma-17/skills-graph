# Audit Report — Resend

> **Audit Date:** 2026-05-15 | **Skill Version:** 1.0.0 | **Auditor:** Claude (automated)

## Scorecard

| Category | Score | Notes |
|----------|-------|-------|
| **Completeness** | 9/10 | Covers all Resend products: transactional emails, broadcasts, audiences, React Email, webhooks, domains. Minor gap: inbound email (agent inbox) only briefly mentioned. |
| **Accuracy** | 9/10 | Based on official docs and llms-full.txt. Code examples follow documented API patterns. SDK version tracked at 6.12.x. |
| **Structure** | 10/10 | All files are leaf nodes under 500 lines. SKILL.md is 48 lines. Files >300 lines have TOC with anchor links. |
| **Navigation** | 9/10 | 12 routing entries with clear "Read When" triggers. Any topic reachable in 1 hop from SKILL.md. |
| **Freshness** | 10/10 | All files written for resend 6.12.x (npm, published May 2026) and React Email 6.0. |
| **Actionability** | 9/10 | Every reference includes runnable code in TypeScript and/or Python. Framework integrations cover 10+ platforms. |
| **Maintenance** | 10/10 | VERSION.json with per-file tracking, CHANGELOG, check-updates.py with npm registry integration. |
| **Overall** | 9/10 | Comprehensive email API skill covering transactional, marketing, templates, webhooks, and multi-SDK patterns. |

## Coverage Analysis

### Topics Covered
- [x] Sending emails — parameters, content types, attachments, scheduling, tags, custom headers
- [x] Batch emails — bulk send, limitations, chunking for >100 emails
- [x] Idempotency — key patterns, retry strategies, conflict handling
- [x] React Email — all components, Tailwind, rendering, visual editor, template patterns
- [x] Webhooks — all 15 event types, Svix verification, handler patterns for Next.js and FastAPI
- [x] Domains — DNS setup, SPF/DKIM/DMARC, verification, deliverability best practices
- [x] Audiences — CRUD, contact properties, segments, topics
- [x] Contacts — create/update/remove, bulk import, subscription management
- [x] Broadcasts — lifecycle, dynamic content, scheduling, A/B testing
- [x] Node.js SDK — all resource methods with TypeScript types
- [x] Python SDK — sync/async, Django/Flask/FastAPI integration
- [x] Framework integrations — Next.js, Express, FastAPI, Cloudflare Workers, Vercel Edge, AWS Lambda, Supabase, Hono, SvelteKit, Remix
- [x] API keys — permissions, domain restriction, rotation
- [x] Security — rate limits, error codes, environment config, webhook verification
- [x] CLI & MCP — command reference, AI tool integration

### Topics NOT Covered (and why)
- **Inbound email (Agent Inbox)** — newer feature, briefly mentioned in webhooks. Full coverage warrants its own reference when stabilized.
- **Ruby/Go/Elixir/Java/PHP SDKs** — mentioned in overview, but dedicated references only for Node.js and Python (primary audience).
- **Resend dashboard deep-dive** — UI-specific features change frequently. Focused on API/SDK patterns.
- **Email content strategy** — copywriting, A/B testing methodology — out of scope for an API skill.

## Integrity Check Results

```
All 12 references verified on disk
Total .md files in references/: 12
```

## Recommendations

1. Add dedicated reference for Agent Inbox (inbound email) when it reaches broader adoption
2. Add reference for Ruby/Go SDKs if user demand arises
3. Monitor React Email for v7 breaking changes (visual editor evolution)
4. Track Resend pricing changes and update overview accordingly
