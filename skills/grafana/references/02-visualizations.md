# Grafana — Visualizations

> Source: [grafana.com/docs/grafana/latest/panels-visualizations](https://grafana.com/docs/grafana/latest/panels-visualizations/) — Grafana 13.0

## Overview

Grafana provides 20+ built-in visualization types. Each panel combines a data query with a visualization and formatting options. Choose the visualization based on the data shape and what you want to communicate.

## Visualization Selection Guide

| Visualization | Best For | Data Shape |
|---------------|----------|------------|
| **Time series** | Metrics over time | Time-indexed numeric series |
| **Stat** | Single big number + sparkline | Single value or reduction |
| **Gauge** | Value against min/max | Single value with thresholds |
| **Bar gauge** | Horizontal/vertical bars against thresholds | Single or few values |
| **Table** | Tabular data, logs, multi-field results | Any structured data |
| **Bar chart** | Categorical comparisons | Named categories + values |
| **Pie chart** | Part-of-whole proportions | Category + value pairs |
| **Histogram** | Distribution of values | Numeric series |
| **Heatmap** | Density over two dimensions | Bucketed time-value data |
| **State timeline** | State changes over time | Enum/status values over time |
| **Status history** | Service status matrix | Multiple entities + states |
| **Logs** | Log lines | Log data (Loki, Elasticsearch) |
| **Traces** | Distributed traces | Trace data (Tempo, Jaeger) |
| **Node graph** | Network/dependency topology | Nodes + edges |
| **Geomap** | Geographic data points | Lat/lon coordinates |
| **Candlestick** | OHLC financial data | Open, high, low, close |
| **Canvas** | Custom positioned elements | Free-form layout |
| **Text** | Static markdown/HTML content | None (static) |
| **News** | RSS feed display | RSS URL |
| **Alert list** | Active/recent alerts | Alert data |
| **Dashboard list** | Links to dashboards | Dashboard metadata |
| **Annotation list** | Recent annotations | Annotation data |

## Time Series Panel

The default and most common visualization.

### Display Options

```
Style:        Lines | Bars | Points
Line width:   1-10 pixels
Fill opacity:  0-100%
Gradient:     None | Opacity | Hue | Scheme
Show points:  Auto | Always | Never
Point size:   1-40 pixels
Stack:        Off | Normal | 100%
```

### Axis Configuration

```
Placement:    Auto | Left | Right | Hidden
Label:        Custom axis label
Scale:        Linear | Logarithmic (base 2, 10)
Min/Max:      Fixed bounds or auto
Soft min/max: Preferred bounds (auto-extends if needed)
```

### Thresholds

```json
{
  "thresholds": {
    "mode": "absolute",
    "steps": [
      { "color": "green", "value": null },
      { "color": "yellow", "value": 70 },
      { "color": "red", "value": 90 }
    ]
  }
}
```

Threshold modes:
- **Absolute** — Fixed values (e.g., CPU > 90% = red)
- **Percentage** — Relative to min/max range

### Legend Options

```
Mode:         List | Table | Hidden
Placement:    Bottom | Right
Values:       Min, Max, Mean, Last, Total, Count
```

## Stat Panel

Shows a single value prominently with optional sparkline.

```
Orientation:   Auto | Horizontal | Vertical
Text mode:     Auto | Value | Value and name | Name | None
Color mode:    Value | Background | Background (gradient) | None
Graph mode:    Area | None
Text size:     Auto or fixed
```

**Reduction functions:** Last, First, Min, Max, Mean, Total, Count, Range, Delta, Diff, All values.

## Gauge Panel

Radial gauge showing value against thresholds.

```
Show threshold labels:  true/false
Show threshold markers: true/false
Min value:             0
Max value:             100
```

## Table Panel

Tabular display with sorting, filtering, and column formatting.

### Column Overrides

```json
{
  "overrides": [
    {
      "matcher": { "id": "byName", "options": "Status" },
      "properties": [
        {
          "id": "custom.cellOptions",
          "value": { "type": "color-background" }
        }
      ]
    }
  ]
}
```

### Cell Display Modes

- **Color text** — Apply color to the text value
- **Color background** — Apply color to the cell background
- **Color background (gradient)** — Gradient fill
- **Gauge** — Inline gauge bar
- **LCD gauge** — Segmented LCD bar
- **JSON view** — Expandable JSON
- **Image** — Render URL as image
- **Sparkline** — Inline sparkline chart

### Table Features

- Click column headers to sort
- Filter by column value using the funnel icon
- Pagination for large result sets
- Column width resize (drag borders)
- Cell inspect (click to expand values)

## Bar Chart Panel

Categorical bar chart for comparing values.

```
Orientation:    Vertical | Horizontal
Stacking:       None | Normal | Percent
Group width:    0-1 (spacing between groups)
Bar width:      0-1 (individual bar width)
Show values:    Auto | Always | Never
```

## Heatmap Panel

Visualize density/distribution across two dimensions.

```
Calculate:     true (Grafana buckets) | false (pre-bucketed)
X-Bucket:      Size or count
Y-Bucket:      Size or count  
Color scheme:  Various palettes
Cell display:  Color | Size + Color
```

Use with Prometheus histograms:
```promql
sum(rate(http_request_duration_seconds_bucket[5m])) by (le)
```

## Logs Panel

Purpose-built for log data from Loki, Elasticsearch, etc.

```
Time:           Show/hide timestamp column
Unique labels:  Show/hide unique label column
Common labels:  Show/hide common labels
Wrap lines:     Enable line wrapping
Prettify JSON:  Auto-format JSON log lines
Dedup:          None | Exact | Numbers | Signature
Sort order:     Descending (newest first) | Ascending
```

## Standard Field Options

Options available on most panel types:

| Option | Purpose | Example |
|--------|---------|---------|
| **Unit** | Display unit | `percent (0-100)`, `bytes(SI)`, `reqps` |
| **Min/Max** | Value range | Affects gauge fill, gradient color |
| **Decimals** | Precision | `2` → `95.42%` |
| **Display name** | Field label | `${__field.name} - ${__field.labels.instance}` |
| **Color scheme** | Coloring mode | Classic palette, single color, thresholds |
| **No value** | Placeholder | `N/A`, `0`, `-` |
| **Links** | Data links | URLs with field/variable interpolation |

### Value Mappings

Map specific values to text/color:

```json
{
  "mappings": [
    { "type": "value", "options": { "0": { "text": "Down", "color": "red" } } },
    { "type": "value", "options": { "1": { "text": "Up", "color": "green" } } },
    { "type": "range", "options": { "from": 80, "to": 100, "result": { "text": "High", "color": "orange" } } },
    { "type": "special", "options": { "match": "null", "result": { "text": "No data", "color": "gray" } } }
  ]
}
```

## Overrides

Apply field-specific settings that override defaults:

```json
{
  "overrides": [
    {
      "matcher": { "id": "byName", "options": "errors" },
      "properties": [
        { "id": "color", "value": { "fixedColor": "red", "mode": "fixed" } },
        { "id": "custom.lineWidth", "value": 2 },
        { "id": "custom.fillOpacity", "value": 20 }
      ]
    }
  ]
}
```

Matcher types:
- `byName` — Match by field name
- `byRegexp` — Match by regex pattern
- `byType` — Match by field type (number, string, time)
- `byFrameRefID` — Match by query reference (A, B, C)

## Common Pitfalls

- **Wrong visualization for data** — Use the selection guide above; time series for metrics, tables for multi-field data
- **Missing units** — Always set units; raw numbers are hard to interpret
- **Threshold overload** — 2-3 thresholds max; more creates visual noise
- **Ignoring legend placement** — Use right-side legend for panels with many series
- **No value mappings** — Map status codes and boolean values to human-readable text
