# Remotion Prompt Generator Changelog

## [1.1.0] — 2026-02-22

**Source tracked: Remotion 4.x** | **Author: Abhishek Sharma**

### Added
- **Intelligent Inference Engine** (`references/intelligent-inference.md`) — Signal extraction from vague prompts, keyword-to-capability mapping, auto-fill decision engine, industry auto-detection, smart scene generation, 11 vague prompt example walkthroughs, Remotion capability-fit matrix
- **MANDATORY: Web Search Requirement** — Skill now requires web search before generating prompts to gather context on user's product, industry, competitors, and design trends
- **MANDATORY: Always-Load References** — `remotion-capabilities.md` and `intelligent-inference.md` must always be read before generating any prompt
- **Inference-First Principle** — Instead of asking 10 questions, extract signals → auto-fill defaults → propose plan → ask only 2-3 critical gaps

### Changed
- **SKILL.md** — Added MANDATORY sections for always-load references and web search; updated routing table with 8 entries; updated workflow to inference-first approach
- **Author** — Updated to Abhishek Sharma
- **Version** — Bumped to 1.1.0

### Stats
- 8 routing entries in SKILL.md
- 15 reference files (7 leaf nodes, 1 router node, 7 sub-files)
- ~3,200 total lines

---

## [1.0.0] — 2026-02-22

**Source tracked: Remotion 4.x** | **Author: Abhishek Sharma**

### Added
- **SKILL.md Router** — 7 routing entries covering capabilities, video types, prompt engineering, discovery workflow, assets, animations, and domain examples
- **Remotion Capabilities** — Comprehensive reference for what Remotion can and cannot do, all supported formats, packages, and limitations
- **Video Types Router** — Routes to 7 domain-specific sub-files (marketing, social, data, education, e-commerce, entertainment, personalized)
- **Prompt Engineering** — Structured 12-section prompt output format, scene description format, animation specification language, color palettes, font recommendations
- **Discovery Workflow** — 16 follow-up questions organized in 4 tiers, progressive questioning strategy, requirement validation checklist, vague request handling
- **Asset & Styling Guide** — Platform safe zones, logo patterns, image treatments, backgrounds, branding by industry, text sizing guidelines
- **Animation & Effects** — Entrance/exit/continuous animation catalog, spring presets, transition catalog, text animation patterns, scene composition layouts, timing guide
- **Marketing & SaaS** — 4 video structures, complete SaaS launch prompt example, feature showcase template
- **Social Media** — Platform specs, hook formula, TikTok/Reels template, LinkedIn template, caption integration
- **Data & Analytics** — Chart animation patterns (bar, line, pie), KPI counting, data-driven prompt template
- **Education & Explainer** — Tutorial structures, code animation patterns, diagram animation patterns
- **E-commerce & Real Estate** — Product showcase, catalog, sale/promo, property tour, listing templates
- **Entertainment & Media** — Music visualizer types, podcast audiogram, event promo templates
- **Personalized & Data-Driven** — Year-in-review, customer journey, batch rendering, Zod schema patterns
- **Domain Examples** — Prompt patterns for 10 industries (SaaS, e-commerce, finance, real estate, education, healthcare, events, creator, agency, crypto)

### Stats
- 7 routing entries in SKILL.md
- 14 reference files (6 leaf nodes, 1 router node, 7 sub-files)
- ~2,800 total lines
