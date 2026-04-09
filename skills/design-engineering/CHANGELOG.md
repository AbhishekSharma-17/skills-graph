# Changelog — Design Engineering

## [1.0.0] — 2026-04-09

**Consolidated from:** 27 specialized design skills into one Skills Graph skill

### Added

- **SKILL.md** — Smart router with 18 routing entries across 6 lifecycle phases (Plan, Build, Style, Review, Refine, Harden)
- **00-overview.md** — Core philosophy, anti-slop manifesto, config dials (DESIGN_VARIANCE, MOTION_INTENSITY, VISUAL_DENSITY)
- **01-context-gathering.md** — Teach mode, .impeccable.md setup, context protocol (from: impeccable)
- **02-shape-discovery.md** — Discovery interview, design brief format (from: shape)
- **03-craft-flow.md** — 5-step build process, 7-step implementation order (from: impeccable/craft)
- **04-typography.md** — Font selection, reflex font bans, type scale, vertical rhythm (from: typeset + impeccable)
- **05-color-system.md** — OKLCH, 60-30-10 rule, palette structure, dark mode (from: colorize + impeccable)
- **06-layout-spacing.md** — 4pt scale, grids, container queries, optical adjustments (from: arrange + impeccable)
- **07-motion-delight.md** — Duration rules, easing, delight principles, overdrive toolkit (from: animate + delight + impeccable + overdrive)
- **08-interaction.md** — 8 states, focus, forms, dialogs, Popover API (from: impeccable)
- **09-ux-copy.md** — Button labels, error formula, onboarding, translation (from: clarify + onboard + impeccable)
- **10-responsive.md** — Mobile-first, input detection, safe areas, adaptation (from: adapt + impeccable)
- **11-style-archetypes.md** — Router to 4 visual style systems
- **style-archetypes/minimalist.md** — Editorial minimalism, warm monochrome (from: minimalist-ui)
- **style-archetypes/brutalist-industrial.md** — Swiss + military terminal (from: industrial-brutalist-ui)
- **style-archetypes/high-end-agency.md** — $150k+ agency aesthetics (from: high-end-visual-design)
- **style-archetypes/creative-arsenal.md** — Bento, scroll animations, hero paradigms (from: design-taste-frontend)
- **12-critique-evaluate.md** — Router to 5 evaluation references
- **critique-evaluate/design-critique.md** — Two-assessment methodology, report format (from: critique)
- **critique-evaluate/heuristics-scoring.md** — Nielsen's 10, 0-4 scoring (from: critique)
- **critique-evaluate/personas.md** — 5 test personas with red flags (from: critique)
- **critique-evaluate/cognitive-load.md** — 3 types, 8-item checklist, working memory (from: critique)
- **critique-evaluate/technical-audit.md** — 5-dimension scan, health score (from: audit)
- **13-refine-intensity.md** — Polish + bolder + quieter + distill (from: 4 skills merged)
- **14-design-system.md** — Normalize + extract tokens/components (from: normalize + extract)
- **15-harden-production.md** — Edge cases, i18n, Core Web Vitals (from: harden + optimize)
- **16-redesign-upgrade.md** — 12-category audit, upgrade techniques (from: redesign-existing-projects)
- **17-anti-patterns.md** — Consolidated ban list from all 27 source skills

### Conflict Resolutions

- Font bans (impeccable) vs font recommendations (minimalist-ui, brutalist-ui): resolved by scoping recommendations to their specific style archetype
- Overlapping micro-interaction guidance (animate + delight): merged into single motion-delight reference
- Duplicate anti-pattern lists across 5+ skills: deduplicated into definitive anti-patterns bible

### Stats

- Routing entries: 18 (root) + 4 (style archetypes) + 5 (critique/evaluate) = 27
- Reference files: 27 total (18 top-level + 4 style-archetype + 5 critique-evaluate)
- Total lines: ~7,137 across all references
- Source skills consolidated: 27
