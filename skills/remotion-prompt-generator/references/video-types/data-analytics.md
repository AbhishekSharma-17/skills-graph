# Data & Analytics Video Prompts

Guidance for creating animated data visualizations, dashboard videos, KPI animations, and statistical explainers.

## Common Data Video Types

| Type | Duration | Key Element |
|------|----------|-------------|
| **KPI highlight** | 10-15s | Single metric counting up + context |
| **Dashboard overview** | 30-60s | Multiple metrics, chart animations |
| **Trend analysis** | 30-60s | Line/bar chart over time |
| **Comparison** | 15-30s | Side-by-side or sequential bars |
| **Year-in-review** | 60-120s | Multiple data points, story arc |
| **Report summary** | 30-60s | Key findings, charts, takeaways |

## Data Animation Patterns

### Counting Numbers
```
Number counts from 0 to target over 40-60 frames
Font: Large (72-96px), bold, primary color
Suffix/prefix: "$", "%", "K", "M" — static, number animates
Optional: color change at milestones
```

### Bar Chart Animation
```
Bars grow from 0 to full height
Staggered start: 5-8 frame delay per bar
Duration per bar: 30-40 frames
Labels: fade in after bar reaches full height
Optional: highlight max/min with accent color
```

### Line Chart Animation
```
Line draws left to right (SVG path animation)
Duration: 60-90 frames
Data points: appear as line passes them (spring pop)
Area fill: fades in after line complete
```

### Pie/Donut Chart
```
Segments fill clockwise from 12 o'clock
Each segment: 20-30 frames
Labels: appear after segment fills
Center text: total or key metric
```

## Data-Driven Prompt Template

```markdown
## Data Input
Props schema:
{
  title: string,
  period: string,
  metrics: Array<{ label: string, value: number, change: number, color?: string }>,
  chartData: Array<{ date: string, value: number }>
}

Sample data:
{
  "title": "Q4 2025 Performance",
  "period": "Oct - Dec 2025",
  "metrics": [
    { "label": "Revenue", "value": 2400000, "change": 23.5, "color": "#10b981" },
    { "label": "Users", "value": 150000, "change": 45.2, "color": "#3b82f6" },
    { "label": "NPS", "value": 72, "change": 8, "color": "#8b5cf6" }
  ]
}
```

## Example Scene: Metric Card Animation

```
Scene: KPI Cards (frames 0-120, 4s)
Layout: 3 cards in row, equal width, 20px gap
Card style: rounded corners (12px), background #1e293b, padding 24px

Per card (staggered 8-frame delay):
1. Card background: fade-in (0.0 → 1.0 over 10 frames)
2. Label text: "Revenue" (18px, #94a3b8, fade-in)
3. Value: counting animation (0 → $2.4M over 40 frames, 36px, white, bold)
4. Change badge: "+23.5%" in green pill, spring-scale entrance
```

## Color Coding for Data

| Data Meaning | Color | Hex |
|-------------|-------|-----|
| Positive/growth | Green | #10b981 |
| Negative/decline | Red | #ef4444 |
| Neutral | Gray | #94a3b8 |
| Primary metric | Blue | #3b82f6 |
| Secondary metric | Purple | #8b5cf6 |
| Highlight | Yellow/Amber | #f59e0b |
