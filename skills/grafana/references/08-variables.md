# Grafana — Variables & Templating

> Source: [grafana.com/docs/grafana/latest/dashboards/variables](https://grafana.com/docs/grafana/latest/dashboards/variables/) — Grafana 13.0

## Overview

Variables make dashboards interactive and reusable. They appear as dropdown selectors at the top of the dashboard and can be referenced in queries, panel titles, annotations, and data links using the `$variable` or `${variable}` syntax.

## Variable Types

| Type | Purpose | Values |
|------|---------|--------|
| **Query** | Dynamic values from a data source | Metric names, label values, SQL results |
| **Custom** | Manually defined list of values | Predefined options |
| **Text box** | Free-form user input | Any text |
| **Constant** | Hidden fixed value | Path prefixes, environment names |
| **Interval** | Time interval selector | `10s`, `1m`, `5m`, `1h`, etc. |
| **Data source** | Data source selector | Available data sources of a type |
| **Ad hoc filters** | Auto-generated label filters | Key-value label pairs |

## Query Variables

The most common type — fetches values dynamically from a data source.

### Prometheus Label Values

```promql
# All values of a label
label_values(job)

# Label values filtered by metric
label_values(http_requests_total, instance)

# Label values with filter
label_values(http_requests_total{job="$job"}, path)

# Metric names
metrics(http_*)

# Query result
query_result(count by (service)(up))
```

### Loki Label Values

```logql
# All label values
label_values(namespace)

# Label values filtered by another label
label_values({job="$job"}, level)
```

### SQL (PostgreSQL/MySQL)

```sql
SELECT DISTINCT environment FROM deployments ORDER BY environment
SELECT hostname FROM servers WHERE environment = '$environment'
```

### Variable Options

| Setting | Purpose | Example |
|---------|---------|---------|
| **Regex** | Filter/transform results | `/^prod-/` (only values starting with `prod-`) |
| **Sort** | Order of dropdown values | Alphabetical, Numerical, Reverse |
| **Multi-value** | Allow selecting multiple values | Enables `$variable` → `val1\|val2` |
| **Include All** | Add "All" option | `$__all` selects everything |
| **Custom All** | Custom value for "All" | `.*` (regex for all) |
| **Refresh** | When to reload values | On dashboard load, On time range change |

## Custom Variables

Define a fixed list of values:

```
Values: production, staging, development
```

Or with display labels:

```
Values: prod : Production, stg : Staging, dev : Development
```

The format is `value : label` — value is used in queries, label is shown in the dropdown.

## Text Box Variables

Allow free-form text input:

```
Name: search_term
Label: Search
Default: error
```

Use in Loki queries:
```logql
{job="api"} |= "$search_term"
```

## Constant Variables

Hidden values for reusable path components:

```
Name: cluster_prefix
Value: us-east-1.prod
Hide: Variable
```

Reference in queries: `http_requests_total{cluster="$cluster_prefix-api"}`

## Interval Variables

Provide time interval selection for aggregation:

```
Name: interval
Values: 10s, 30s, 1m, 5m, 15m, 1h
Auto option: Enabled
Step count: 30   # divides time range into 30 intervals
```

Use in PromQL: `rate(http_requests_total[$interval])`

## Data Source Variables

Let users switch between data sources:

```
Name: datasource
Type: Data source
Plugin type: prometheus
```

Reference in panel data source configuration: `${datasource}`

## Ad Hoc Filters

Auto-generated key-value filters applied to all panels using a specific data source:

1. Create variable with type **Ad hoc filters**
2. Select the target data source
3. Users can dynamically add filters like `job = api`, `namespace = production`
4. Filters are automatically injected into all queries targeting that data source

## Variable Syntax

### Interpolation Formats

| Syntax | Output | Use Case |
|--------|--------|----------|
| `$variable` | `production` | Simple substitution |
| `${variable}` | `production` | When adjacent to text |
| `${variable:csv}` | `a,b,c` | Comma-separated (multi-value) |
| `${variable:pipe}` | `a\|b\|c` | Pipe-separated (regex) |
| `${variable:json}` | `["a","b","c"]` | JSON array |
| `${variable:singlequote}` | `'a','b','c'` | SQL IN clause |
| `${variable:doublequote}` | `"a","b","c"` | Quoted values |
| `${variable:regex}` | `(a\|b\|c)` | Regex group |
| `${variable:raw}` | `a,b,c` | No escaping |
| `${variable:text}` | Display text | Label instead of value |
| `${variable:queryparam}` | `var-env=prod` | URL query parameter |

### Multi-Value in Queries

```promql
# Prometheus (automatic regex)
http_requests_total{job=~"$job"}

# SQL (use singlequote format)
SELECT * FROM servers WHERE env IN (${environment:singlequote})

# Loki (automatic regex)
{namespace=~"$namespace"}
```

## Chained Variables

Variables can reference other variables to create cascading filters:

```
Variable 1: environment
  Query: label_values(up, environment)

Variable 2: service
  Query: label_values(up{environment="$environment"}, service)

Variable 3: instance
  Query: label_values(up{environment="$environment", service="$service"}, instance)
```

When the user changes `environment`, `service` reloads with matching values, and `instance` reloads based on both.

### Variable Ordering

Variables are evaluated top-to-bottom. A variable can only reference variables defined above it in the list.

## Built-in Variables

| Variable | Value | Example |
|----------|-------|---------|
| `$__from` | Start of time range (epoch ms) | `1718700000000` |
| `$__to` | End of time range (epoch ms) | `1718703600000` |
| `$__interval` | Calculated interval | `15s` |
| `$__interval_ms` | Interval in milliseconds | `15000` |
| `$__range` | Time range duration | `1h` |
| `$__range_s` | Time range in seconds | `3600` |
| `$__rate_interval` | Safe rate interval | `1m` |
| `$__org.id` | Organization ID | `1` |
| `$__user.id` | User ID | `42` |
| `$__user.login` | Username | `admin` |
| `$__dashboard.uid` | Dashboard UID | `abc123` |
| `$__name` | Series name | Field or series label |
| `$timeFilter` | Time filter for SQL | `time > 1718700000` |
| `$__timeFilter(col)` | SQL time filter function | `col >= '2026-06-18' AND col <= '2026-06-19'` |

## Repeating Panels and Rows

### Repeat Panel by Variable

1. Edit a panel → **Panel options** → **Repeat options**
2. Select a multi-value variable to repeat by
3. Choose direction: Horizontal or Vertical
4. Set max per row (for horizontal repeat)

The panel is duplicated for each selected value of the variable.

### Repeat Row by Variable

1. Click the row header → **Edit** (gear icon)
2. Enable **Repeat for** and select a variable
3. The entire row (with all its panels) is repeated for each value

## Common Pitfalls

- **Variable order matters** — Chained variables must be defined in dependency order (top to bottom)
- **Missing regex escaping** — Special characters in variable values can break PromQL/LogQL regex selectors
- **Refresh on time range change** — Enable this for variables that depend on the time range
- **Multi-value without regex** — For Prometheus, always use `=~` (not `=`) when multi-value is enabled
- **Include All performance** — "All" with high cardinality variables can create very expensive queries
- **Constant vs Custom** — Use Constant for values users should never see; Custom for selectable options
