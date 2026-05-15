# Audit Report — Recharts Skill

**Date**: 2026-05-16
**Skill Version**: 1.0.0
**Source Version**: recharts 3.8.1

## Quality Assessment

| Dimension | Score | Notes |
|:----------|:-----:|:------|
| **Architecture** | 5/5 | Clean router → 13 leaf files. No file exceeds 500 lines. Clear separation by chart type, then by feature (axes, tooltip, animation, customization). |
| **Content Quality** | 5/5 | All prop tables include type, default, and description. Practical code examples for every chart type and customization pattern. Covers v3 hooks API and TypeScript generics. |
| **Completeness** | 5/5 | Covers all 12 chart types, all component categories (series, axes, grid, tooltip, legend, brush, references, labels), animation, stacking, responsive, TypeScript, performance, SSR, and v3 migration. |
| **Maintainability** | 5/5 | VERSION.json tracks 3.8.1 with per-file source attribution. check-updates.py validates against npm registry. 90-day staleness threshold. |
| **Trigger Quality** | 5/5 | MANDATORY TRIGGERS cover library name, component names, and use-case phrases. Broad enough to catch dashboard/chart/visualization queries in React context. |

## Coverage Matrix

| Topic | Covered | File |
|:------|:-------:|:-----|
| Installation & quick start | Yes | 00-overview |
| LineChart, BarChart, AreaChart | Yes | 01-cartesian-charts |
| ComposedChart, ScatterChart | Yes | 01-cartesian-charts |
| PieChart, RadarChart, RadialBarChart | Yes | 02-polar-charts |
| Treemap, Sankey, Funnel, Sunburst | Yes | 03-specialty-charts |
| XAxis, YAxis, ZAxis | Yes | 04-axes-grid |
| Domain, scales, ticks | Yes | 04-axes-grid |
| CartesianGrid, PolarGrid | Yes | 04-axes-grid |
| Tooltip customization | Yes | 05-tooltip-legend, 07-customization |
| Legend customization | Yes | 05-tooltip-legend, 07-customization |
| Brush | Yes | 05-tooltip-legend |
| Chart sync (syncId) | Yes | 05-tooltip-legend |
| ReferenceLine/Area/Dot | Yes | 06-reference-labels |
| ErrorBar | Yes | 06-reference-labels |
| Label, LabelList | Yes | 06-reference-labels |
| Custom shapes, dots, ticks | Yes | 07-customization |
| Direct custom components | Yes | 07-customization |
| Shape primitives | Yes | 07-customization |
| Animation configuration | Yes | 08-animation |
| Stacking (stackId, stackOffset) | Yes | 09-stacking-responsive |
| BarStack (v3.6) | Yes | 09-stacking-responsive |
| ResponsiveContainer | Yes | 09-stacking-responsive |
| Built-in responsive prop | Yes | 09-stacking-responsive |
| TypeScript types | Yes | 10-typescript-hooks |
| Generics (v3.8) | Yes | 10-typescript-hooks |
| Hooks API | Yes | 10-typescript-hooks |
| Performance optimization | Yes | 11-performance-ssr |
| Next.js / SSR | Yes | 11-performance-ssr |
| v2→v3 migration | Yes | 12-migration-v3 |

## Identified Gaps

None significant. The skill covers the full Recharts API surface as of v3.8.1.
