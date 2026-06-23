<p align="center">
  <h1 align="center">Skills Graph</h1>
  <p align="center">
    <strong>Precision-engineered AI agent skills with interconnected reference architectures.</strong>
    <br />
    <em>A methodology for building skills that carry 294,000+ lines of knowledge<br />while loading only what the AI actually needs.</em>
  </p>
  <p align="center">
    <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
    <a href="#-the-agent-skills-standard"><img src="https://img.shields.io/badge/Agent%20Skills-Universal%20Standard-purple.svg" alt="Skills Standard"></a>
    <a href="#-platform-compatibility"><img src="https://img.shields.io/badge/Platforms-25%2B-green.svg" alt="Platforms"></a>
    <a href="#-skills-catalog"><img src="https://img.shields.io/badge/Skills-65%20Production%20Ready-orange.svg" alt="Skills"></a>
    <a href="#-the-technique-progressive-reference-architecture"><img src="https://img.shields.io/badge/Knowledge-294%2C000%2B%20Lines-red.svg" alt="Lines"></a>
  </p>
</p>

<br />

<details open>
<summary><strong>Table of Contents</strong></summary>

&nbsp;

| Section | |
|:--------|:--|
| [Overview](#-overview) | What Skills Graph is and why it exists |
| [Skills Catalog](#-skills-catalog) | All available skills at a glance |
| [The Problem](#-the-problem-with-current-skills) | Why conventional skills fail |
| [Side-by-Side Comparison](#-skills-graph-vs-conventional-skills) | Token economics, quality, maintenance |
| [The Technique](#-the-technique-progressive-reference-architecture) | The 3-level progressive loading system |
| [Five Pillars](#-the-five-pillars) | Deep dive into the methodology |
| [Skill Workflows](#-skill-workflows-cross-skill-orchestration) | How skills collaborate on complex tasks |
| [Graph in Action](#-how-the-interconnected-graph-works) | Navigation flows and dependency visualization |
| [Skill Anatomy](#-anatomy-of-a-skill) | The 6 standard components |
| [Installation](#-installation) | Smithery, manual, and native integration |
| [Platform Compatibility](#-platform-compatibility) | 25+ supported platforms |
| [Maintenance](#-maintenance--tooling) | Automated scripts and version tracking |
| [Contributing](#-contributing) | How to build your own Skills Graph skill |

</details>

<br />

---

## Overview

> *"A 99,000-line knowledge base that costs the same as a 50-line skill -- until you actually need it."*

Skills Graph is a **methodology** and a **collection** of production-grade AI agent skills built using **Progressive Reference Architecture (PRA)** -- a systematic approach to creating deeply interconnected, graph-structured knowledge bases that AI coding assistants can navigate with surgical precision.

Instead of dumping documentation into a single monolithic file or a flat folder of loosely related references, Skills Graph organizes knowledge as a **directed acyclic graph (DAG)** where every reference file is a node, every cross-reference is an edge, and a lightweight router sits at the root to guide the AI to exactly the information it needs -- nothing more, nothing less.

<table>
<tr><td><strong>Skills</strong></td><td>65 production-ready (Agno, MS Agent Framework, Remotion Prompt Generator, Trigger.dev, Drizzle ORM, Hono, Zod, Claude Agent SDK, Langfuse, Better Auth, Polars, Qdrant, OpenTelemetry, Inngest, LiteLLM, DSPy, Design Engineering, LiveKit, Convex, AI SDK, Payload CMS, Motion, Dagger, Expo, Terraform, Astro, Supabase, Dagster, tRPC, Cloudflare Workers, PostHog, NestJS, LangGraph, Ollama, Vitest, Prisma ORM, CrewAI, shadcn/ui, Upstash, Resend, Recharts, GitHub Actions, Bun, Pulumi, Tauri, Mastra, Turborepo, Effect-TS, SvelteKit, Playwright, OpenAI Agents SDK, Weaviate, Haystack, W&amp;B, dbt, LlamaIndex, Temporal, Pydantic AI, vLLM, Clerk, Stripe, Grafana, Redis, Kubernetes, Turso)</td></tr>
<tr><td><strong>Total Knowledge</strong></td><td>294,000+ lines across 1,003 reference files</td></tr>
<tr><td><strong>Router Overhead</strong></td><td>69-231 lines (the only cost when skill triggers)</td></tr>
<tr><td><strong>Context Efficiency</strong></td><td>~97% reduction vs monolithic approach</td></tr>
<tr><td><strong>Platform Support</strong></td><td>25+ AI coding assistants</td></tr>
<tr><td><strong>Maintenance</strong></td><td>Automated version checking, staleness detection, integrity validation</td></tr>
</table>

---

## Skills Catalog

Production-ready skills built with the Skills Graph methodology.

| # | Skill | Framework | Version | Files | Lines | Status |
|:-:|:------|:----------|:-------:|:-----:|:-----:|:------:|
| 1 | **[Agno](agno-skill/)** | [Agno](https://github.com/agno-agi/agno) v2.5.3 | `1.2.0` | 116 | 23,431 | Production |
| 2 | **[MS Agent Framework](ms-agent-framework/)** | [MS Agent Framework](https://github.com/microsoft/agent-framework) 1.0.0b | `2.0.0` | 61 | ~14,000 | Production |
| 3 | **[Remotion Prompt Generator](skills/remotion-prompt-generator/)** | [Remotion](https://remotion.dev) 4.x | `1.1.0` | 15 | ~2,733 | Production |
| 4 | **[Trigger.dev](skills/trigger-dev/)** | [Trigger.dev](https://trigger.dev) v4.4.3 | `1.0.0` | 11 | ~3,512 | Production |
| 5 | **[Drizzle ORM](skills/drizzle-orm/)** | [Drizzle ORM](https://orm.drizzle.team) v0.45.1 | `1.0.0` | 12 | ~3,539 | Production |
| 6 | **[Hono](skills/hono/)** | [Hono](https://hono.dev) v4.12.0 | `1.0.0` | 12 | ~3,430 | Production |
| 7 | **[Zod](skills/zod/)** | [Zod](https://zod.dev) v4.x | `1.0.0` | 13 | ~3,686 | Production |
| 8 | **[Claude Agent SDK](skills/claude-agent-sdk/)** | [Claude Agent SDK](https://platform.claude.com/docs/en/agent-sdk/overview) Python 0.1.51 / TS 0.2.86 | `1.1.0` | 16 | ~5,817 | Production |
| 9 | **[Langfuse](skills/langfuse/)** | [Langfuse](https://langfuse.com/docs) v3.162.0 | `1.0.0` | 13 | ~3,993 | Production |
| 10 | **[Better Auth](skills/better-auth/)** | [Better Auth](https://www.better-auth.com/docs) v1.5.6 | `1.0.0` | 13 | ~4,232 | Production |
| 11 | **[Polars](skills/polars/)** | [Polars](https://docs.pola.rs/) v1.39.3 | `1.0.0` | 13 | ~4,003 | Production |
| 12 | **[Qdrant](skills/qdrant/)** | [Qdrant](https://qdrant.tech/documentation/) v1.17.1 | `1.0.0` | 13 | ~3,735 | Production |
| 13 | **[OpenTelemetry](skills/opentelemetry/)** | [OpenTelemetry](https://opentelemetry.io/docs/) Spec v1.55.0 | `1.0.0` | 13 | ~4,289 | Production |
| 14 | **[Inngest](skills/inngest/)** | [Inngest](https://www.inngest.com/docs) TS SDK v3.x | `1.0.0` | 13 | ~4,556 | Production |
| 15 | **[LiteLLM](skills/litellm/)** | [LiteLLM](https://docs.litellm.ai) v1.52.0 | `1.0.0` | 13 | ~2,165 | Production |
| 16 | **[DSPy](skills/dspy/)** | [DSPy](https://dspy.ai) v2.5.43 | `1.0.0` | 9 | ~1,887 | Production |
| 17 | **[Design Engineering](skills/design-engineering/)** | Original — consolidated from 27 design skills | `1.0.0` | 27 | ~7,137 | Production |
| 18 | **[LiveKit](skills/livekit/)** | [LiveKit Agents](https://docs.livekit.io) v1.5.2 | `1.0.0` | 12 | ~3,671 | Production |
| 19 | **[Convex](skills/convex/)** | [Convex](https://docs.convex.dev) v1.34.1 | `1.0.0` | 13 | ~4,443 | Production |
| 20 | **[AI SDK](skills/ai-sdk/)** | [AI SDK](https://ai-sdk.dev) v6.0.158 | `1.0.0` | 13 | ~4,118 | Production |
| 21 | **[Payload CMS](skills/payload-cms/)** | [Payload CMS](https://payloadcms.com/docs) v3.82.0 | `1.0.0` | 13 | ~3,442 | Production |
| 22 | **[Motion](skills/motion/)** | [Motion](https://motion.dev/docs) v12.38.0 | `1.0.0` | 13 | ~4,662 | Production |
| 23 | **[Dagger](skills/dagger/)** | [Dagger](https://docs.dagger.io) v0.20.3 | `1.0.0` | 13 | ~3,737 | Production |
| 24 | **[Expo](skills/expo/)** | [Expo SDK](https://docs.expo.dev) v55.0.15 | `1.0.0` | 13 | ~4,809 | Production |
| 25 | **[Terraform](skills/terraform/)** | [Terraform](https://developer.hashicorp.com/terraform/docs) v1.14.8 | `1.0.0` | 13 | ~4,327 | Production |
| 26 | **[Astro](skills/astro/)** | [Astro](https://docs.astro.build) v5.17.0 | `1.0.0` | 13 | ~3,460 | Production |
| 27 | **[Supabase](skills/supabase/)** | [Supabase](https://supabase.com/docs) supabase-js 2.49.x | `1.0.0` | 13 | ~3,846 | Production |
| 28 | **[Dagster](skills/dagster/)** | [Dagster](https://docs.dagster.io) v1.13.1 | `1.0.0` | 13 | ~3,461 | Production |
| 29 | **[tRPC](skills/trpc/)** | [tRPC](https://trpc.io) v11.16.0 | `1.0.0` | 12 | ~4,347 | Production |
| 30 | **[Cloudflare Workers](skills/cloudflare-workers/)** | [Cloudflare Workers](https://developers.cloudflare.com/workers/) Wrangler 3.x | `1.0.0` | 13 | ~4,645 | Production |
| 31 | **[PostHog](skills/posthog/)** | [PostHog](https://posthog.com/docs) posthog-python 7.13.0 | `1.0.0` | 13 | ~4,615 | Production |
| 32 | **[NestJS](skills/nestjs/)** | [NestJS](https://docs.nestjs.com) @nestjs/core 11.1.x | `1.0.0` | 13 | ~5,519 | Production |
| 33 | **[LangGraph](skills/langgraph/)** | [LangGraph](https://docs.langchain.com/oss/python/langgraph/overview) langgraph 1.x | `1.0.0` | 13 | ~4,146 | Production |
| 34 | **[Ollama](skills/ollama/)** | [Ollama](https://docs.ollama.com) ollama 0.22.x | `1.0.0` | 13 | ~3,970 | Production |
| 35 | **[Vitest](skills/vitest/)** | [Vitest](https://vitest.dev) vitest 4.x | `1.0.0` | 12 | ~4,436 | Production |
| 36 | **[Prisma ORM](skills/prisma-orm/)** | [Prisma ORM](https://www.prisma.io/docs) @prisma/client 7.x | `1.0.0` | 13 | ~5,241 | Production |
| 37 | **[CrewAI](skills/crewai/)** | [CrewAI](https://docs.crewai.com) crewai 1.3.x | `1.0.0` | 13 | ~3,618 | Production |
| 38 | **[shadcn/ui](skills/shadcn-ui/)** | [shadcn/ui](https://ui.shadcn.com) shadcn 4.7.x | `1.0.0` | 13 | ~5,000 | Production |
| 39 | **[Upstash](skills/upstash/)** | [Upstash](https://upstash.com/docs) @upstash/redis 1.38.0 | `1.0.0` | 12 | ~4,654 | Production |
| 40 | **[Resend](skills/resend/)** | [Resend](https://resend.com/docs) resend 6.12.x | `1.0.0` | 12 | ~3,740 | Production |
| 41 | **[Recharts](skills/recharts/)** | [Recharts](https://recharts.org) v3.8.1 | `1.0.0` | 13 | ~3,743 | Production |
| 42 | **[GitHub Actions](skills/github-actions/)** | [GitHub Actions](https://docs.github.com/en/actions) 2026.05 | `1.0.0` | 13 | ~5,849 | Production |
| 43 | **[Bun](skills/bun/)** | [Bun](https://bun.com/docs) v1.3.x | `1.0.0` | 13 | ~5,240 | Production |
| 44 | **[Pulumi](skills/pulumi/)** | [Pulumi](https://www.pulumi.com/docs/) v3.242.0 | `1.0.0` | 13 | ~3,958 | Production |
| 45 | **[Tauri](skills/tauri/)** | [Tauri](https://v2.tauri.app/) v2.9.x | `1.0.0` | 13 | ~4,305 | Production |
| 46 | **[Mastra](skills/mastra/)** | [Mastra](https://mastra.ai/docs) @mastra/core 1.37.x | `1.0.0` | 14 | ~4,026 | Production |
| 47 | **[Turborepo](skills/turborepo/)** | [Turborepo](https://turborepo.dev/docs) turbo 2.9.x | `1.0.0` | 13 | ~3,482 | Production |
| 48 | **[Effect-TS](skills/effect-ts/)** | [Effect](https://effect.website/docs) effect 3.21.x | `1.0.0` | 13 | ~4,471 | Production |
| 49 | **[SvelteKit](skills/sveltekit/)** | [SvelteKit](https://svelte.dev/docs/kit) @sveltejs/kit 2.57.x | `1.0.0` | 13 | ~4,550 | Production |
| 50 | **[Playwright](skills/playwright/)** | [Playwright](https://playwright.dev) @playwright/test 1.59 | `1.0.0` | 13 | ~3,771 | Production |
| 51 | **[OpenAI Agents SDK](skills/openai-agents-sdk/)** | [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) openai-agents 0.17.x | `1.0.0` | 13 | ~3,548 | Production |
| 52 | **[Weaviate](skills/weaviate/)** | [Weaviate](https://docs.weaviate.io/weaviate) v1.37 | `1.0.0` | 13 | ~3,909 | Production |
| 53 | **[Haystack](skills/haystack/)** | [Haystack](https://docs.haystack.deepset.ai) haystack-ai 2.30.0 | `1.0.0` | 13 | ~4,090 | Production |
| 54 | **[W&B](skills/wandb/)** | [Weights & Biases](https://docs.wandb.ai) wandb 0.27.1 | `1.0.0` | 13 | ~3,731 | Production |
| 55 | **[dbt](skills/dbt/)** | [dbt](https://docs.getdbt.com) dbt-core 1.11.11 | `1.0.0` | 13 | ~4,636 | Production |
| 56 | **[LlamaIndex](skills/llamaindex/)** | [LlamaIndex](https://developers.llamaindex.ai/python/framework/) llama-index 0.14.22 | `1.0.0` | 13 | ~4,058 | Production |
| 57 | **[Temporal](skills/temporal/)** | [Temporal](https://docs.temporal.io) temporalio 1.28.0 | `1.0.0` | 13 | ~4,188 | Production |
| 58 | **[Pydantic AI](skills/pydantic-ai/)** | [Pydantic AI](https://pydantic.dev/docs/ai/) pydantic-ai 1.107.0 | `1.0.0` | 13 | ~3,486 | Production |
| 59 | **[vLLM](skills/vllm/)** | [vLLM](https://docs.vllm.ai/) vllm 0.22.1 | `1.0.0` | 13 | ~3,804 | Production |
| 60 | **[Clerk](skills/clerk/)** | [Clerk](https://clerk.com/docs) @clerk/nextjs v7.5 (Core 3) | `1.0.0` | 13 | ~4,641 | Production |
| 61 | **[Stripe](skills/stripe/)** | [Stripe](https://docs.stripe.com) API 2026-05-27.dahlia | `1.0.0` | 13 | ~3,920 | Production |
| 62 | **[Grafana](skills/grafana/)** | [Grafana](https://grafana.com/docs/grafana/latest/) 13.0.2 | `1.0.0` | 13 | ~3,899 | Production |
| 63 | **[Redis](skills/redis/)** | [Redis](https://redis.io/docs/latest/) 8.6 | `1.0.0` | 13 | ~4,459 | Production |
| 64 | **[Kubernetes](skills/kubernetes/)** | [Kubernetes](https://kubernetes.io/docs/home/) 1.36 | `1.0.0` | 13 | ~5,106 | Production |
| 65 | **[Turso](skills/turso/)** | [Turso](https://docs.turso.tech) v0.6.1 | `1.0.0` | 13 | ~3,994 | Production |
| | | | | **990** | **~294,189** | |

<br />

<details>
<summary><strong>Agno Skill -- Detailed Coverage (click to expand)</strong></summary>

&nbsp;

> Build AI agents, multi-agent teams, and agentic workflows with the Agno open-source framework.

| Domain | Topics |
|:-------|:-------|
| **Core** | Agents, Teams, Workflows, Workflow Patterns (8 types) |
| **Tools** | 120+ built-in toolkits across 11 categories (search, data, web, dev, comms, media, productivity), custom tools, MCP |
| **Models** | 40+ providers, model-as-string syntax, response caching, multimodal compatibility matrix |
| **Storage** | 18 database backends (Postgres, MongoDB, Redis, DynamoDB, SQLite, Supabase, and more) |
| **Knowledge** | RAG pipelines, 14+ vector databases, 12+ embedding providers, chunking, hybrid search |
| **Memory** | Automatic and agentic memory, MemoryManager, MemoryTools, multi-user isolation |
| **Learning** | Learning Machines, 6 learning stores, 3 modes (Always/Agentic/Propose) |
| **Safety** | Guardrails (PII, prompt injection, content moderation), Human-in-the-Loop, hooks |
| **Observability** | 12 monitoring platforms, OpenTelemetry tracing, custom logging |
| **Production** | AgentOS (50+ API endpoints), deployment templates (Docker, Railway, AWS ECS), 6 chat interfaces |
| **Advanced** | Reasoning (3 approaches), multimodal (image/audio/video), evals, context management, culture |

**Graph topology:** 12 router nodes / 104 leaf nodes / 34 routing entries

</details>

<br />

<details>
<summary><strong>Remotion Prompt Generator -- Detailed Coverage (click to expand)</strong></summary>

&nbsp;

> Generate detailed, production-ready prompts for the Remotion Dev skill to create programmatic React-based videos.

| Domain | Topics |
|:-------|:-------|
| **Remotion Capabilities** | Core architecture, compositions, sequences, hooks, output formats, platform dimensions, animation system, asset support, audio, data-driven videos, 3D, rendering options, limitations, packages ecosystem |
| **Intelligent Inference** | Signal extraction from vague prompts, keyword-to-capability mapping, auto-fill decision engine, industry auto-detection (10 industries), smart scene generation, uploaded asset analysis, context clue mining |
| **Video Types** | Marketing & SaaS, Social Media, Data & Analytics, Education & Explainer, E-commerce & Real Estate, Entertainment & Media, Personalized & Data-Driven |
| **Prompt Engineering** | 12-section structured prompt format, scene description format, animation specification language, spring presets, color palettes, font recommendations, quality checklist |
| **Discovery Workflow** | 16 follow-up questions in 4 tiers, progressive questioning strategy, requirement validation, vague request handling, asset inventory |
| **Asset & Styling** | Platform safe zones, logo placement patterns, image treatments, background patterns, branding by industry, text sizing, aspect ratio reference |
| **Animation & Effects** | Entrance/exit/continuous animations, spring physics presets, transition catalog, text animation patterns (8 types), scene composition layouts (6 patterns), timing guide, 3D basics |
| **Domain Examples** | Prompt patterns for SaaS, e-commerce, finance, real estate, education, healthcare, events, personal brand, agency, crypto/web3 |

**Graph topology:** 1 router node / 14 leaf nodes / 8 routing entries

</details>

<br />

<details>
<summary><strong>Trigger.dev -- Detailed Coverage (click to expand)</strong></summary>

&nbsp;

> Build and deploy TypeScript background jobs, AI workflows, and scheduled tasks with retries, queues, observability, and elastic scaling.

| Domain | Topics |
|:-------|:-------|
| **Overview & Setup** | Architecture, installation, quickstart, SDK imports, framework support (Next.js, Express, Hono, Remix, etc.), key terminology |
| **Writing Tasks** | Task definition, configuration (retry/queue/machine/maxDuration), lifecycle hooks (init, onStart, onSuccess, onFailure, catchError), machine presets (micro to large-2x), payload/output limits, Zod validation, structured logging |
| **Triggering Tasks** | tasks.trigger(), batchTrigger(), triggerAndWait(), batch.triggerByTaskAndWait(), streaming batches, trigger options (delay, TTL, idempotency, debounce, concurrencyKey, queue, priority, tags, metadata) |
| **Runs** | 10 run states, run lifecycle, metadata API (set/append/increment), tags (max 5 per run), runs.list/retrieve/subscribe/poll, cancellation, replay, reschedule |
| **Scheduled Tasks** | Declarative cron (in-code), imperative cron (dynamic/per-user), 5-field cron syntax, timezone + DST handling, schedule management API (create/update/deactivate/delete), environment rules |
| **Concurrency & Queues** | Queue mechanics, environment concurrency (base + burst), task-level limits, shared queues, per-tenant queuing (concurrencyKey), free vs paid tier pattern, queue management API, priority queues |
| **Error Handling** | Retry config (maxAttempts, factor, backoff), global vs task-level, retry.onThrow (block-level), retry.fetch (HTTP with status codes + Retry-After), catchError (dynamic), AbortTaskRunError, OpenAI retry pattern |
| **Wait & HITL** | wait.for/wait.until duration pauses, waitpoint tokens (create/complete/list), HTTP + SDK + client-side completion, approval workflows, multi-step chains, drip campaigns, AI + human review |
| **Realtime & Streaming** | Run subscriptions (SSE), streams.define + write, React hooks (useRealtimeRun, useRealtimeStream, useRealtimeBatch, useRealtimeRunsWithTag), TriggerAuthContext, public access tokens, progress bars, AI chat streaming |
| **Configuration** | trigger.config.ts reference, runtime (Node/Bun), build config, 8 build extensions (Prisma, Puppeteer, FFmpeg, Python, aptGet, envSync, packages, files), OpenTelemetry + exporters, process keep-alive |
| **Deployment** | dev command, deploy command (all flags), 4 environments (DEV/STAGING/PREVIEW/PROD), CI/CD (GitHub Actions, GitLab CI), self-hosting (Docker, Kubernetes), preview branches, monorepo setup |

**Graph topology:** 0 router nodes / 11 leaf nodes / 11 routing entries

</details>

<br />

<details>
<summary><strong>Design Engineering -- Detailed Coverage (click to expand)</strong></summary>

&nbsp;

> Full-lifecycle frontend design engineering: plan, build, style, review, refine, harden, and ship production-grade interfaces. Consolidated from 27 specialized design skills.

| Phase | Topics |
|:------|:-------|
| **Plan** | Context gathering, teach mode, .impeccable.md setup, discovery interviews, design briefs, craft flow (5-step build process) |
| **Build** | Typography (font selection, type scale, vertical rhythm, web fonts), Color (OKLCH, 60-30-10 rule, palettes, dark mode), Layout (4pt scale, grids, container queries, hierarchy), Motion (duration rules, easing, staggered animations, delight, overdrive toolkit), Interaction (8 states, forms, dialogs, Popover API, focus management), UX Copy (button labels, error formula, onboarding, translation), Responsive (mobile-first, input detection, safe areas, adaptation) |
| **Style** | 4 complete archetypes: Minimalist Editorial (warm monochrome, bento), Brutalist Industrial (Swiss typography, CRT terminal), High-End Agency ($150k+ aesthetics, spring physics), Creative Arsenal (Bento 2.0, scroll hijack, magnetic UI) |
| **Review** | Design critique (two-assessment methodology), Nielsen's 10 heuristics (0-4 scoring), 5 test personas (power user, first-timer, accessibility, stress tester, mobile), Cognitive load (3 types, 8-item checklist), Technical audit (a11y, performance, theming, responsive) |
| **Refine** | Polish (18-point checklist), Intensity UP (bolder), Intensity DOWN (quieter), Distill (simplify to essence) |
| **System** | Design system normalization, component/token extraction, migration strategy |
| **Harden** | i18n (RTL, CJK, text expansion), edge cases, error handling, Core Web Vitals (LCP, FID/INP, CLS), performance optimization |
| **Upgrade** | 12-category audit checklist, upgrade techniques, fix priority order, anti-patterns bible |

**Graph topology:** 2 router nodes / 25 leaf nodes / 27 routing entries

</details>

<br />

**Planned:**&ensp; Semantic Kernel &middot; D3.js &middot; Docker

> Want a skill for a framework not listed? [Open an issue](../../issues) or [contribute one](#-contributing).

---

## The Problem with Current Skills

Most AI agent skills today are built using one of three broken patterns:

<table>
<tr>
<th width="33%">The Monolith</th>
<th width="33%">The Flat Dump</th>
<th width="33%">The Copy-Paste</th>
</tr>
<tr>
<td>

```
my-skill/
└── SKILL.md  # 3,000-5,000+ lines
```

AI loads **everything** every time. 5,000 tokens burned on a simple question.

</td>
<td>

```
my-skill/
├── SKILL.md
└── references/
    ├── agents.md
    ├── tools.md
    └── ...40 more files
```

Files exist but AI has **no guidance** on which to read. Guesses wrong.

</td>
<td>

```
my-skill/
└── SKILL.md  # 500 lines of fragments
```

Cherry-picked docs with **no version tracking**. Stale within weeks.

</td>
</tr>
</table>

**What all three share:** no version tracking, no staleness detection, no integrity validation, no self-audit, no cross-platform awareness.

---

## Skills Graph vs. Conventional Skills

### Token Economics

| Scenario | Monolith | Flat Files | **Skills Graph** |
|:---------|:--------:|:----------:|:----------------:|
| Skill idle (not triggered) | ~100 | ~100 | ~100 |
| Skill triggers (any query) | **~5,000** | ~500 | ~500 |
| Simple question | **~5,000** | ~800 (maybe wrong file) | **~700** |
| Moderate question | **~5,000** | ~1,500 (2-3 files, guessing) | **~900** |
| Complex question | **~5,000** | ~3,000 (5+ files) | **~1,200** |
| Total knowledge available | 5,000 lines | varies | **40,000+ lines** |

> **Skills Graph skills carry 7x more knowledge while using 4-7x fewer tokens per query.**

### Architecture

| Dimension | Conventional | Skills Graph |
|:----------|:------------|:-------------|
| Structure | Single file or flat folder | Hierarchical DAG with router nodes |
| Entry point | SKILL.md (500-5,000 lines) | SKILL.md (69-231 lines, pure router) |
| Navigation | None -- AI guesses | Routing tables with "Read When" conditions |
| Reference organization | Flat list | Graph: routers branch to sub-references |
| Loading strategy | All-or-nothing | Progressive: metadata -> router -> specific leaf |
| Depth of knowledge | Shallow (limited by file size) | Deep (unlimited -- leaf nodes expand the graph) |

### Maintenance

| Capability | Conventional | Skills Graph |
|:-----------|:------------|:-------------|
| Version tracking | None | `VERSION.json` with semantic versioning |
| Framework version pinning | None | Per-file `written_for` metadata |
| Staleness detection | Manual | Automated (`--stale` flag, configurable) |
| Integrity validation | None | Automated (`--integrity` verifies routing table) |
| Upstream change detection | None | PyPI version check + docs sitemap diffing |
| Architecture audit | Never | `AUDIT-REPORT.md` with scorecard |

---

## The Technique: Progressive Reference Architecture

PRA is built on a single principle: **the AI should pay only for the knowledge it actually uses.**

```
                    ALWAYS IN CONTEXT
                    +-------------------------+
  Level 1           |  YAML Metadata          |  ~100 tokens
  (Metadata)        |  name + description     |  Same cost whether skill
                    |  + trigger keywords     |  has 5 files or 500
                    +------------+------------+
                                 |
                    LOADED WHEN SKILL TRIGGERS
                    +------------v------------+
  Level 2           |  SKILL.md Router Body   |  ~500 tokens
  (Router)          |  Routing table with     |  Maps intent -> file
                    |  "Read When" conditions |  34 routes in 69 lines
                    +------------+------------+
                                 |
                    LOADED ON DEMAND (specific path only)
                    +------------v------------+
  Level 3           |  Reference Graph        |  ~200-400 tokens per node
  (References)      |  Router nodes -> Leaves |  Only the relevant path
                    |  116 files, 23,431 lines|  is ever loaded
                    +-------------------------+
```

**Level 1 -- Metadata** (always loaded): YAML frontmatter with name, description, trigger keywords. ~100 tokens. Identical cost whether the skill has 5 or 500 reference files.

**Level 2 -- Router** (loaded on trigger): The SKILL.md body -- a lean routing table mapping user intent to specific files via "Read When" conditions. ~500 tokens.

**Level 3 -- References** (loaded on demand): The knowledge graph itself. Router nodes fan out to sub-references; leaf nodes contain actual knowledge. The AI navigates the graph, loading only the path relevant to the current query.

---

## The Five Pillars

### 1. Intent-Based Routing

Every navigation decision is driven by **user intent**, not file naming or alphabetical order.

```markdown
| Reference     | File                    | Read When                                              |
|---------------|-------------------------|---------------------------------------------------------|
| **Knowledge** | `references/knowledge.md` | RAG pipelines, vector databases, embedders, chunking... |
| **Memory**    | `references/memory.md`    | Automatic vs agentic memory, MemoryManager...           |
```

The "Read When" column is the critical innovation. When a user asks *"how do I set up a RAG pipeline with Pinecone?"*, the AI sees "RAG pipelines, vector databases" and loads `knowledge.md` directly -- no guessing.

For router nodes, the pattern repeats at a deeper level with **Sub-Reference tables**, giving two levels of intent matching before the AI ever reads content.

### 2. Hierarchical Decomposition

Large topics are recursively split using the **router + sub-files** pattern:

```
tools.md (router -- 56 lines)
  |-- tools/creating-tools.md        (leaf -- @tool decorator)
  |-- tools/custom-toolkits.md       (leaf -- Toolkit classes)
  |-- tools/advanced.md              (leaf -- hooks, caching, RunContext)
  |-- tools/mcp-tools.md             (leaf -- Model Context Protocol)
  |-- tools/builtin-search.md        (leaf -- DuckDuckGo, Tavily, Exa...)
  |-- tools/builtin-data.md          (leaf -- SQL, Pandas, BigQuery...)
  |-- tools/builtin-web.md           (leaf -- Firecrawl, Crawl4AI...)
  |-- tools/builtin-dev.md           (leaf -- GitHub, Docker, Shell...)
  |-- tools/builtin-comms.md         (leaf -- Email, Slack, Discord...)
  |-- tools/builtin-media.md         (leaf -- DALL-E, ElevenLabs...)
  +-- tools/builtin-productivity.md  (leaf -- Google Calendar, Notion...)
```

**The rules:** >500 lines = must split. >300 lines = must have TOC. Routers under 100 lines. Leaves 200-500 lines.

### 3. Zero-Cost Idle State

A 50-line skill and a 23,431-line skill have **identical idle cost** (~100 tokens). Install dozens of Skills Graph skills without bloating your AI's context. They only consume tokens when you actually need them.

### 4. Version-Aware Maintenance

Every skill tracks versions at three levels:

```json
{
  "skill_version": "1.2.0",
  "agno_version_tracked": "2.5.3",
  "references": {
    "agents.md": { "written_for": "2.5.2", "last_updated": "2026-02-18" },
    "evals.md":  { "written_for": "2.5.3", "last_updated": "2026-02-21" }
  }
}
```

When Agno 2.6.0 releases, you know exactly which files target 2.5.2 and might need updates. Automated scripts handle staleness detection and integrity validation.

### 5. Self-Auditing Architecture

Every skill includes an `AUDIT-REPORT.md` scoring itself across quality dimensions:

| Category | Score |
|:---------|:-----:|
| SKILL.md size (69 lines) | 5/5 |
| Progressive disclosure | 4/5 |
| Reference splitting | 4/5 |
| YAML frontmatter | 5/5 |
| TOC on large files | 4/5 |
| Description triggering | 4/5 |
| Tooling & maintenance | 5/5 |

Plus: comparison with exemplary skills, cross-platform compatibility analysis, and a prioritized improvement plan.

---

## Skill Workflows: Cross-Skill Orchestration

Skills Graph skills are powerful individually, but the full potential emerges when **multiple skills collaborate on a single complex task** -- what we call **Skill Workflows**.

### The Problem

A developer says: *"Build me a production-ready multi-agent customer support system."*

No single skill can answer this. The task spans agent architecture, tool integration, workflow orchestration, database/memory, deployment, and safety. With conventional skills, the AI either picks one skill (partial answer) or loads everything (blows the context budget).

### The Solution

Skill Workflows **decompose the task into phases** and traverse multiple skill graphs surgically:

```
  PLAN                          EXECUTE                       SYNTHESIZE
+------------------+          +------------------+          +------------------+
| Decompose task   |          | For each phase:  |          | Combine outputs  |
| into phases      |--------->| Route to skill(s)|--------->| from all phases  |
| Identify which   |          | Traverse graph   |          | into a coherent  |
| skills per phase |          | Load only needed |          | solution         |
|                  |          | leaf nodes       |          |                  |
+------------------+          +------------------+          +------------------+
```

### Complex Example: Multi-Framework Agent Migration

> **Task:** *"Migrate a customer support system from Microsoft Agent Framework (sequential orchestration, Azure Functions, Cosmos DB, content safety) to Agno with AgentOS."*

**Phase 1 -- Understand Source** (MS Agent Framework skill):

```
SKILL.md (109 routes)
    |
    |-->  12c-orchestration-handoff.md      <-- handoff pattern
    |-->  12a-orchestration-sequential.md   <-- sequential builder
    |-->  08-memory.md                      <-- memory providers
    |-->  19-security.md                    <-- content safety
    +-->  13a-azure-functions.md            <-- deployment model

Tokens loaded: ~2,000
```

**Phase 2 -- Design Target** (Agno skill):

```
SKILL.md (34 routes)
    |
    |-->  teams.md                          <-- multi-agent coordination
    |-->  database.md (router)
    |       +-->  database/backends.md      <-- MongoDB/Cosmos equivalent
    |-->  memory.md (router)
    |       +-->  memory/core-concepts.md   <-- map memory model
    |-->  guardrails.md (router)
    |       +-->  guardrails/builtin-guardrails.md
    +-->  agentos.md (router)
            +-->  agentos/setup-api.md      <-- production deployment

Tokens loaded: ~2,500
```

**Phase 3 -- Migration Mapping:**

```
Source (MS Agent Framework)          Target (Agno)
---------------------------------    ------------------------------
HandoffBuilder + 4 agents            Team(mode="route") + 4 agents
SequentialBuilder pipeline           Workflow with Router step
InMemoryHistoryProvider + Cosmos     MongoDb(db_url="cosmos://...")
Content Safety middleware            @guardrail + input validation
Azure Functions deployment           AgentOS + Docker on Azure
A2A protocol                         AgentOS SSE streaming API
```

**Phase 4 -- Generate Code** using leaf nodes already loaded.

<table>
<tr>
<th>Without Skill Workflows</th>
<th>With Skill Workflows</th>
</tr>
<tr>
<td>

Load entire MS skill: ~14,000 tokens<br />
Load entire Agno skill: ~23,000 tokens<br />
**Total: ~37,000 tokens**<br />
(likely exceeds context budget)

</td>
<td>

Phase 1 (5 MS leaves): ~2,000 tokens<br />
Phase 2 (9 Agno nodes): ~2,500 tokens<br />
Phases 3-4: 0 additional<br />
**Total: ~4,500 tokens (88% reduction)**

</td>
</tr>
</table>

The AI accessed 37,000+ lines of knowledge while loading only 4,500 tokens -- because the graph structure let it navigate to exactly 14 nodes (out of 177) relevant to this specific task.

### Workflow Skills (Future Vision)

The natural evolution: **Workflow Skills** -- meta-skills whose references are not documentation but **execution plans** that orchestrate other skills.

```
workflow-skills/
|-- SKILL.md                        # Routes by task type
+-- references/
    |-- agent-migration.md          # Cross-framework migration
    |-- greenfield-agent-system.md  # New agent system from scratch
    |-- rag-pipeline-design.md      # RAG system design
    |-- production-hardening.md     # Prototype -> production
    +-- multi-agent-debug.md        # Debug multi-agent issues
```

Each workflow reference would contain phase decomposition, skill routing maps, decision points, and synthesis templates. A Workflow Skill doesn't contain framework knowledge -- it contains **orchestration intelligence** that composes knowledge from other skills.

This is the endgame: from individual skill graphs to a **graph of graphs**.

---

## How the Interconnected Graph Works

### Router Pattern

Every complex topic uses a **router file** with conditional loading guidance:

```markdown
# Agno Memory

## Sub-References

| Sub-Reference    | File                             | Read When                              |
|------------------|----------------------------------|----------------------------------------|
| **Core Concepts**| `memory/core-concepts.md`        | Automatic vs agentic memory, setup...  |
| **Tools & Mgr**  | `memory/tools-manager.md`        | MemoryTools, MemoryManager, sharing... |
| **Patterns**     | `memory/patterns-best-practices.md` | Teams with memory, optimization...  |

## Quick Start
[minimal code -- enough for simple cases without loading sub-references]
```

The router itself answers simple queries. The Sub-Reference table guides deeper for complex ones.

### Navigation Flow

```
User: "How do I add persistent memory to my Agno agent with Postgres?"

  Step 1   SKILL.md metadata (always in context)
           AI sees "agno" in user's stack --> skill triggers
           Cost: 0 additional tokens

  Step 2   SKILL.md routing table loads
           Finds: Memory --> references/memory.md
           Cost: +500 tokens

  Step 3   AI reads references/memory.md (router node)
           Sees Sub-References, picks "Core Concepts"
           Cost: +200 tokens

  Step 4   AI reads memory/core-concepts.md (leaf node)
           Gets detailed memory setup with database config
           Cost: +350 tokens

  Total:   ~1,050 tokens out of 23,431 available (4.5%)
```

### Dependency Graph (Agno Skill)

```
                            SKILL.md
                          (34 routes)
                               |
         +-------------+-------+-------+--------------+
         |             |       |       |              |
    Foundation    Execution    |   State & Memory   Safety
    +----+---+   +----+---+   |   +----+----+    +---+---+
  agents   teams tools/  models|  memory/ database/ guardrails/
  (leaf)  (leaf) (router)(leaf)|  (router)(router)  (router)
                   |           |     |       |         |
           +-------+-----+    |  +--+--+  +-+--+   +--+--+
        creating custom  MCP  | core tools backends builtin
        (leaf)  kits   (leaf) | (leaf)(leaf)(leaf)  (leaf)
               (leaf)         |
                 |            |        Production
         +-------+------+    |     +-----+------+
      search    data   web   |   agentos/     deploy
      (leaf)   (leaf) (leaf) |   (router)     (leaf)
                             |      |
       ...6 more builtin     |   +--+--+
          categories         |  setup config
                             |  (leaf)(leaf)
                             |
                        Knowledge & Learning
                       +-----+------+
                    knowledge    learning
                     (leaf)      (leaf)
```

Each root-to-leaf path is a navigation sequence. The AI never loads sibling branches.

---

## Anatomy of a Skill

Every Skills Graph skill has six standard components:

| Component | Purpose |
|:----------|:--------|
| **`SKILL.md`** | The router. Only file with YAML frontmatter. Routing table mapping intent to references. Under 100 lines. |
| **`references/`** | The knowledge graph. Router nodes (Sub-Reference tables) and leaf nodes (actual knowledge). No frontmatter on any reference file. |
| **`VERSION.json`** | Version tracking. Skill version, framework version, per-file metadata, docs sitemap, statistics. |
| **`CHANGELOG.md`** | Release history. Added, Changed, Split, Fixed, Stats categories per version. |
| **`scripts/`** | Maintenance automation. Version checking, sitemap diffing, staleness detection, integrity validation. |
| **`AUDIT-REPORT.md`** | Architecture quality. Self-assessment scorecard, exemplary skill comparison, improvement plan. |

---

## Repository Structure

```
skills-graph/
|-- README.md
|-- CONTRIBUTING.md                     # Full skill creation guide with templates
|-- SECURITY.md                         # Security policy and vulnerability reporting
|-- CODE_OF_CONDUCT.md                  # Community standards
|-- LICENSE
|-- .github/
|   |-- PULL_REQUEST_TEMPLATE.md        # PR checklist for skill contributions
|   +-- ISSUE_TEMPLATE/                 # Bug reports, skill requests, improvements
|
|-- _template/                          # Copy-paste starter for new skills
|   |-- SKILL.md                        # Router template with instructions
|   |-- VERSION.json                    # Version tracking template
|   |-- CHANGELOG.md                    # Release history template
|   |-- AUDIT-REPORT.md                 # Quality scorecard template
|   |-- scripts/check-updates.py        # Maintenance script template
|   +-- references/                     # Leaf + router node examples
|
|-- skills/
|   |-- agno-skill/                     # v1.2.0 | 116 files | 23,431 lines
|   |   |-- SKILL.md                    # 69 lines, 34 routing entries
|   |   |-- VERSION.json
|   |   |-- CHANGELOG.md
|   |   |-- AUDIT-REPORT.md
|   |   |-- scripts/
|   |   |   +-- check-updates.py
|   |   +-- references/
|   |       |-- agents.md               teams.md       workflows.md
|   |       |-- models.md               knowledge.md   learning.md
|   |       |-- reasoning.md            multimodal.md  deploy.md
|   |       |-- tools.md -------> tools/           (11 sub-files)
|   |       |-- memory.md ------> memory/          (3 sub-files)
|   |       |-- database.md ----> database/        (3 sub-files)
|   |       |-- guardrails.md --> guardrails/      (3 sub-files)
|   |       |-- context-mgmt.md > context-mgmt/    (5 sub-files)
|   |       |-- agentos.md -----> agentos/         (2 sub-files)
|   |       |-- evals.md -------> evals/           (4 sub-files)
|   |       +-- ... (30+ more topic files)
|   |
|   |-- ms-agent-framework/             # v2.0.0 | 61 files | ~14,000 lines
|   |   |-- SKILL.md                    # ~55 lines, 22 routing entries
|   |   |-- metadata/
|   |   |-- scripts/
|   |   +-- references/                 # 01-10 core, 11-11l workflows,
|   |                                   # 12a-12e orchestration, 13-23 deploy+patterns
|   |
|   |-- remotion-prompt-generator/      # v1.1.0 | 15 files | ~2,733 lines
|   |   |-- SKILL.md                    # 56 lines, 8 routing entries
|   |   |-- VERSION.json
|   |   |-- CHANGELOG.md
|   |   |-- AUDIT-REPORT.md
|   |   |-- scripts/
|   |   |   +-- check-updates.py
|   |   +-- references/
|   |       |-- remotion-capabilities.md    [ALWAYS LOADED]
|   |       |-- intelligent-inference.md    [ALWAYS LOADED]
|   |       |-- video-types.md (router) --> video-types/  (7 sub-files)
|   |       |-- prompt-engineering.md
|   |       |-- discovery-workflow.md
|   |       |-- asset-styling-guide.md
|   |       |-- animation-effects.md
|   |       +-- prompt-engineering/domain-examples.md
|   |
|   +-- trigger-dev/                    # v1.0.0 | 11 files | ~3,512 lines
|       |-- SKILL.md                    # 48 lines, 11 routing entries
|       |-- VERSION.json
|       |-- CHANGELOG.md
|       |-- AUDIT-REPORT.md
|       |-- scripts/
|       |   +-- check-updates.py
|       +-- references/
|           |-- 00-overview.md          # Setup, quickstart, architecture
|           |-- 01-writing-tasks.md     # Task definition, hooks, machines
|           |-- 02-triggering-tasks.md  # Trigger methods, batches, options
|           |-- 03-runs.md             # Lifecycle, states, metadata, tags
|           |-- 04-scheduled-tasks.md  # Cron, timezones, schedule API
|           |-- 05-concurrency-queues.md # Queues, per-tenant, burst
|           |-- 06-error-handling-retries.md # Retries, backoff, catchError
|           |-- 07-wait-and-human-in-loop.md # Tokens, approvals, HITL
|           |-- 08-realtime-streaming.md # React hooks, SSE, streaming
|           |-- 09-configuration.md    # Config, build extensions, telemetry
|           +-- 10-deployment-cli.md   # Deploy, CI/CD, self-hosting
|
+-- drizzle-orm/                      # v1.0.0 | 12 files | ~3,539 lines
    |-- SKILL.md                      # 53 lines, 12 routing entries
    |-- VERSION.json
    |-- CHANGELOG.md
    |-- AUDIT-REPORT.md
    |-- scripts/
    |   +-- check-updates.py
    +-- references/
        |-- 00-overview.md            # Setup, drivers, quickstart
        |-- 01-schema-declaration.md  # Tables, column types, enums
        |-- 02-indexes-constraints.md # PKs, FKs, unique, check, indexes
        |-- 03-relations.md           # 1:1, 1:N, M:N, self-referencing
        |-- 04-select-queries.md      # SELECT, filters, aggregations, CTEs
        |-- 05-mutations.md           # INSERT, UPDATE, DELETE, upsert
        |-- 06-joins.md              # Inner, left, right, full, lateral
        |-- 07-relational-queries.md # findMany, findFirst, nested with
        |-- 08-transactions.md       # Transactions, savepoints, isolation
        |-- 09-migrations.md         # drizzle-kit, generate, push, pull
        |-- 10-performance.md        # Prepared stmts, replicas, logging
        +-- 11-validation.md         # Zod, Valibot, TypeBox integration
|
+-- hono/                             # v1.0.0 | 12 files | ~3,430 lines
    |-- SKILL.md                      # 52 lines, 12 routing entries
    |-- VERSION.json
    |-- CHANGELOG.md
    |-- AUDIT-REPORT.md
    |-- scripts/
    |   +-- check-updates.py
    +-- references/
        |-- 00-overview.md            # Setup, runtimes, quickstart
        |-- 01-routing.md             # HTTP methods, params, wildcards, groups
        |-- 02-context-api.md         # c.json, c.text, c.req, c.env, streaming
        |-- 03-middleware.md          # Built-in, custom, factory pattern
        |-- 04-authentication.md      # JWT, Bearer, Basic auth, API keys
        |-- 05-validation.md          # Zod validator, all targets, RPC types
        |-- 06-rpc-type-safety.md     # hc client, AppType, SWR/TanStack
        |-- 07-jsx-rendering.md       # SSR JSX, Suspense, streaming, client
        |-- 08-error-handling.md      # HTTPException, onError, notFound
        |-- 09-testing.md             # app.request, Vitest, env mocking
        |-- 10-runtime-adapters.md    # Node.js, CF Workers, Bun, Deno, Lambda
        +-- 11-best-practices.md      # Structure, security, performance, CI/CD
|
+-- design-engineering/               # v1.0.0 | 27 files | ~7,137 lines
    |-- SKILL.md                      # 65 lines, 18 routing entries
    |-- VERSION.json
    |-- CHANGELOG.md
    |-- AUDIT-REPORT.md
    |-- scripts/
    |   +-- check-updates.py
    +-- references/
        |-- 00-overview.md            # Philosophy, config dials, anti-slop manifesto
        |-- 01-context-gathering.md   # Teach mode, .impeccable.md setup
        |-- 02-shape-discovery.md     # Discovery interview, design brief
        |-- 03-craft-flow.md          # 5-step build process
        |-- 04-typography.md          # Fonts, scale, rhythm, OpenType
        |-- 05-color-system.md        # OKLCH, palettes, dark mode, contrast
        |-- 06-layout-spacing.md      # 4pt scale, grids, hierarchy, depth
        |-- 07-motion-delight.md      # Animation, delight, overdrive toolkit
        |-- 08-interaction.md         # States, forms, dialogs, Popover API
        |-- 09-ux-copy.md             # Copy, errors, onboarding, translation
        |-- 10-responsive.md          # Mobile-first, input detection, adaptation
        |-- 11-style-archetypes.md    # ROUTER -> 4 visual styles
        |-- style-archetypes/
        |   |-- minimalist.md         # Editorial minimalism, warm monochrome
        |   |-- brutalist-industrial.md # Swiss typography, CRT terminal
        |   |-- high-end-agency.md    # $150k+ agency aesthetics
        |   +-- creative-arsenal.md   # Bento 2.0, scroll hijack, magnetic UI
        |-- 12-critique-evaluate.md   # ROUTER -> 5 evaluation types
        |-- critique-evaluate/
        |   |-- design-critique.md    # Two-assessment methodology
        |   |-- heuristics-scoring.md # Nielsen's 10, 0-4 scoring
        |   |-- personas.md           # 5 test personas
        |   |-- cognitive-load.md     # 3 types, working memory rule
        |   +-- technical-audit.md    # A11y, perf, theming, responsive
        |-- 13-refine-intensity.md    # Polish, bolder, quieter, distill
        |-- 14-design-system.md       # Normalize, extract tokens/components
        |-- 15-harden-production.md   # i18n, edge cases, Core Web Vitals
        |-- 16-redesign-upgrade.md    # 12-category audit, upgrade techniques
        +-- 17-anti-patterns.md       # Consolidated ban list from 27 skills
|
+-- livekit/                           # v1.0.0 | 12 files | ~3,671 lines
    |-- SKILL.md                      # 52 lines, 12 routing entries
    |-- VERSION.json
    |-- CHANGELOG.md
    |-- AUDIT-REPORT.md
    |-- scripts/
    |   +-- check-updates.py
    +-- references/
        |-- 00-overview.md            # Architecture, installation, CLI, quickstart
        |-- 01-core-concepts.md       # Rooms, participants, tracks, tokens, WebRTC
        |-- 02-agent-sessions.md      # AgentSession lifecycle, events, RoomIO
        |-- 03-voice-pipeline.md      # STT-LLM-TTS, VAD, turn detection, interruptions
        |-- 04-models-plugins.md      # Provider plugins, LiveKit Inference, OpenAI compat
        |-- 05-tools-function-calling.md # function_tool, provider tools, MCP, RPC
        |-- 06-multi-agent-workflows.md  # Agent handoffs, tasks, task groups
        |-- 07-frontend-sdks.md       # React components, JS SDK, mobile SDKs
        |-- 08-telephony-sip.md       # SIP trunking, phone numbers, DTMF
        |-- 09-room-service-api.md    # Twirp API, room/participant management
        |-- 10-deployment-observability.md # Cloud, Docker, K8s, metrics
        +-- 11-recipes-patterns.md    # Push-to-talk, RAG, translation, IVR
```

---

## Installation

### Via skills CLI (Recommended)

> **[Browse all skills on skills.sh](https://skills.sh)**

```bash
# See what skills are available before installing
npx skills add AbhishekSharma-17/skills-graph --list

# Install all skills from this repo
npx skills add AbhishekSharma-17/skills-graph

# Install a specific skill
npx skills add AbhishekSharma-17/skills-graph --skill agno
npx skills add AbhishekSharma-17/skills-graph --skill ms-agent-framework
npx skills add AbhishekSharma-17/skills-graph --skill remotion-prompt-generator
npx skills add AbhishekSharma-17/skills-graph --skill trigger-dev
npx skills add AbhishekSharma-17/skills-graph --skill drizzle-orm
npx skills add AbhishekSharma-17/skills-graph --skill hono
npx skills add AbhishekSharma-17/skills-graph --skill zod
npx skills add AbhishekSharma-17/skills-graph --skill claude-agent-sdk
npx skills add AbhishekSharma-17/skills-graph --skill design-engineering
npx skills add AbhishekSharma-17/skills-graph --skill livekit

# Install globally (available across all projects)
npx skills add AbhishekSharma-17/skills-graph -g

# Search for any skill in the ecosystem
npx skills find
```

### Via Smithery

```bash
smithery install agno
```

### Via Install Script

```bash
# Interactive menu — pick which skills to install
./install/install-skills.sh

# Install all skills at once
./install/install-skills.sh --all

# Install a specific skill
./install/install-skills.sh --skill claude-agent-sdk

# See all available commands
./install/install-skills.sh --help
```

> See **[install/COMMANDS.md](install/COMMANDS.md)** for the full copy-paste command reference for every skill.

### Manual Install

Copy the skill folder to your platform's skill directory:

| Platform | Project Path | Global Path |
|:---------|:-------------|:------------|
| Claude Code | `.claude/skills/agno/` | `~/.claude/skills/agno/` |
| Gemini CLI | `.gemini/skills/agno/` | `~/.gemini/skills/agno/` |
| Cursor | `.cursor/skills/agno/` | `~/.cursor/skills/agno/` |
| Windsurf | `.windsurf/skills/agno/` | `~/.codeium/windsurf/skills/agno/` |
| Codex | `.codex/skills/agno/` | `~/.codex/skills/agno/` |
| Trae | `.trae/skills/agno/` | `~/.trae/skills/agno/` |
| Antigravity | `.agent/skills/agno/` | `~/.gemini/antigravity/skills/agno/` |

### Agno Native Integration

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.skills import Skills, LocalSkills

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    skills=Skills(loaders=[LocalSkills("/path/to/agno-skill")])
)
```

---

## Platform Compatibility

The Agent Skills standard (`SKILL.md` format) works on 25+ platforms with identical semantics.

| Platform | Type | Status |
|:---------|:-----|:------:|
| Claude Code | CLI | Full |
| Gemini CLI | CLI | Full |
| Cursor | IDE | Full |
| Windsurf | IDE | Full |
| Codex | CLI | Full |
| Trae | IDE | Full |
| Antigravity | IDE | Full |
| Amp | IDE | Full |
| Goose | CLI | Full |
| OpenCode | CLI | Full |
| GitHub Copilot | Extension | Partial |

---

## The Agent Skills Standard

Agent Skills is a universal format for extending AI coding assistants. Originally introduced in Claude Code (Oct 2025), went open Dec 2025, adopted by 25+ platforms.

1. `SKILL.md` with YAML frontmatter (`name` + `description`) as entry point
2. Optional `references/` for knowledge files
3. Optional `scripts/` for executable tools
4. 3-level loading: metadata (always) -> SKILL.md (on trigger) -> references (on demand)

Skills Graph builds on this by structuring references as an interconnected graph and adding version tracking, maintenance automation, and self-auditing -- practices that don't exist in the base spec.

---

## Maintenance & Tooling

```bash
# Full report
python skills/agno-skill/scripts/check-updates.py --report

# Individual checks
python skills/agno-skill/scripts/check-updates.py --version     # PyPI latest
python skills/agno-skill/scripts/check-updates.py --sitemap     # New doc pages
python skills/agno-skill/scripts/check-updates.py --stale 30    # Files older than 30 days
python skills/agno-skill/scripts/check-updates.py --integrity   # Verify routing table

# MS Agent Framework
python skills/ms-agent-framework/scripts/check-freshness.py --verbose

# Remotion Prompt Generator
python skills/remotion-prompt-generator/scripts/check-updates.py --report

# Trigger.dev
python skills/trigger-dev/scripts/check-updates.py --report
```

```
====== AGNO VERSION CHECK ======
Skill version:     1.2.0
Tracked Agno:      2.5.3
Latest on PyPI:    2.5.3
  UP TO DATE

====== FILE INTEGRITY ======
34 routing entries checked
116 reference files verified
0 broken references found
  ALL REFERENCES VALID
```

---

## Contributing

> **[Read the full Contributing Guide (CONTRIBUTING.md)](CONTRIBUTING.md)** -- complete standards, copy-paste templates, and step-by-step instructions for building a Skills Graph skill from scratch.

### Quick Summary

1. **Start with the router** -- `SKILL.md` with routing table and "Read When" conditions. Under 100 lines.
2. **Organize as a graph** -- Router files for complex topics, leaf files for focused content.
3. **Add intent-based navigation** -- Every entry tells the AI when to load that file.
4. **No frontmatter on references** -- Only `SKILL.md` gets YAML frontmatter.
5. **Track versions** -- `VERSION.json` with per-file metadata.
6. **Add maintenance scripts** -- Automate version checking and integrity validation.
7. **Audit yourself** -- `AUDIT-REPORT.md` with quality scorecard.

### Quality Checklist

- [ ] `SKILL.md` `name` exactly matches the folder name
- [ ] `SKILL.md` under 100 lines (pure router)
- [ ] Every reference reachable from routing table
- [ ] Router files have "Read When" / "Sub-References" tables
- [ ] Files >300 lines have TOC
- [ ] Files >500 lines split into router + sub-files
- [ ] `VERSION.json` tracks framework version + per-file metadata
- [ ] `CHANGELOG.md` documents all releases
- [ ] Maintenance script passes integrity checks
- [ ] `AUDIT-REPORT.md` exists with scorecard
- [ ] Description includes explicit trigger keywords

The full guide includes templates for every file (SKILL.md, VERSION.json, CHANGELOG.md, AUDIT-REPORT.md, check-updates.py), size rules, naming conventions, common mistakes, and production examples from both the Agno and MS Agent Framework skills.

---

## Author

**Abhishek Sharma**

---

## License

MIT License -- see [LICENSE](LICENSE).

Reference documentation is curated from frameworks under their own licenses:
**Agno** ([Apache 2.0](https://github.com/agno-agi/agno/blob/main/LICENSE)) &middot;
**MS Agent Framework** ([MIT](https://github.com/microsoft/agent-framework/blob/main/LICENSE))

---

## Acknowledgments

[Agno](https://github.com/agno-agi/agno) &middot;
[Microsoft Agent Framework](https://github.com/microsoft/agent-framework) &middot;
[Trigger.dev](https://github.com/triggerdotdev/trigger.dev) &middot;
[Agent Skills Standard](https://docs.anthropic.com) (Anthropic) &middot;
[Smithery](https://smithery.ai)
