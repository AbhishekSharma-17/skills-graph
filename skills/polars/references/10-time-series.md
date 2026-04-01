# Polars — Time Series

> Source: [docs.pola.rs](https://docs.pola.rs/user-guide/transformations/time-series/)

## Table of Contents

- [Temporal Types](#temporal-types)
- [Parsing Dates](#parsing-dates)
- [The dt Namespace](#the-dt-namespace)
- [Date Arithmetic](#date-arithmetic)
- [group_by_dynamic](#group_by_dynamic)
- [Rolling Windows](#rolling-windows)
- [Resampling](#resampling)
- [Timezone Handling](#timezone-handling)
- [Common Patterns](#common-patterns)

## Temporal Types

| Type | Description | Internal Representation |
|------|-------------|------------------------|
| `Date` | Calendar date | Days since Unix epoch (1970-01-01) |
| `Time` | Time of day | Nanoseconds since midnight |
| `Datetime` | Date + time | Microseconds since epoch (configurable: ns, us, ms) |
| `Duration` | Time delta | Result of date/datetime subtraction |

```python
import polars as pl
import datetime as dt

df = pl.DataFrame({
    "date": [dt.date(2024, 1, 15), dt.date(2024, 6, 30)],
    "time": [dt.time(9, 30, 0), dt.time(17, 0, 0)],
    "datetime": [dt.datetime(2024, 1, 15, 9, 30), dt.datetime(2024, 6, 30, 17, 0)],
})
# date: Date, time: Time, datetime: Datetime("us")
```

## Parsing Dates

### From CSV/Files

```python
# Auto-detect dates during read
df = pl.read_csv("data.csv", try_parse_dates=True)

# Parquet preserves types automatically
df = pl.read_parquet("data.parquet")
```

### From Strings

```python
# String to Date
df.with_columns(
    pl.col("date_str").str.to_date("%Y-%m-%d"),
)

# String to Datetime
df.with_columns(
    pl.col("ts_str").str.to_datetime("%Y-%m-%d %H:%M:%S"),
)

# String to Time
df.with_columns(
    pl.col("time_str").str.to_time("%H:%M:%S"),
)

# Common format codes:
# %Y = 4-digit year, %m = month (01-12), %d = day (01-31)
# %H = hour (00-23), %M = minute (00-59), %S = second (00-59)
# %f = microseconds, %z = timezone offset (+0000)
# %b = abbreviated month (Jan), %B = full month (January)
```

### From Unix Timestamps

```python
# Unix seconds to Datetime
df.with_columns(
    (pl.col("unix_ts") * 1_000_000).cast(pl.Datetime("us")).alias("datetime"),
)

# Or use from_epoch
df.with_columns(
    pl.from_epoch(pl.col("unix_ts"), time_unit="s").alias("datetime"),
)
```

## The dt Namespace

Extract components and perform temporal operations:

### Date/Time Components

```python
df.with_columns(
    pl.col("datetime").dt.year().alias("year"),
    pl.col("datetime").dt.month().alias("month"),
    pl.col("datetime").dt.day().alias("day"),
    pl.col("datetime").dt.hour().alias("hour"),
    pl.col("datetime").dt.minute().alias("minute"),
    pl.col("datetime").dt.second().alias("second"),
    pl.col("datetime").dt.microsecond().alias("microsecond"),
)
```

### Calendar Properties

```python
df.with_columns(
    pl.col("date").dt.weekday().alias("weekday"),       # 1=Mon, 7=Sun
    pl.col("date").dt.week().alias("week_number"),       # ISO week
    pl.col("date").dt.ordinal_day().alias("day_of_year"),
    pl.col("date").dt.quarter().alias("quarter"),
    pl.col("date").dt.is_leap_year().alias("leap_year"),
)
```

### Truncation

```python
# Truncate to period boundary
df.with_columns(
    pl.col("datetime").dt.truncate("1h").alias("hour_start"),
    pl.col("datetime").dt.truncate("1d").alias("day_start"),
    pl.col("datetime").dt.truncate("1mo").alias("month_start"),
    pl.col("datetime").dt.truncate("1w").alias("week_start"),
)
```

### Rounding

```python
df.with_columns(
    pl.col("datetime").dt.round("15m").alias("nearest_15min"),
    pl.col("datetime").dt.round("1h").alias("nearest_hour"),
)
```

### Type Conversion

```python
# Datetime → Date (drop time)
pl.col("datetime").dt.date()

# Datetime → Time (drop date)
pl.col("datetime").dt.time()

# Date → Datetime
pl.col("date").cast(pl.Datetime("us"))

# Datetime → epoch
pl.col("datetime").dt.epoch("s")     # Seconds since epoch
pl.col("datetime").dt.epoch("ms")    # Milliseconds
```

## Date Arithmetic

```python
# Duration literals
df.with_columns(
    (pl.col("date") + pl.duration(days=30)).alias("plus_30_days"),
    (pl.col("datetime") + pl.duration(hours=2)).alias("plus_2_hours"),
    (pl.col("date") - pl.duration(weeks=1)).alias("minus_1_week"),
)

# Difference between dates
df.with_columns(
    (pl.col("end_date") - pl.col("start_date")).alias("duration"),
    (pl.col("end_date") - pl.col("start_date")).dt.total_days().alias("days_between"),
)

# Duration methods
pl.col("duration").dt.total_days()
pl.col("duration").dt.total_hours()
pl.col("duration").dt.total_minutes()
pl.col("duration").dt.total_seconds()
pl.col("duration").dt.total_milliseconds()
```

## group_by_dynamic

Group rows into fixed time windows for temporal aggregations.

### Basic Usage

```python
# Daily aggregation
df.group_by_dynamic("timestamp", every="1d").agg(
    pl.col("value").mean().alias("daily_avg"),
    pl.col("value").sum().alias("daily_sum"),
    pl.len().alias("count"),
)

# Monthly aggregation
df.group_by_dynamic("date", every="1mo").agg(
    pl.col("revenue").sum().alias("monthly_revenue"),
)

# Weekly (starting Monday)
df.group_by_dynamic("date", every="1w").agg(
    pl.col("sales").sum(),
)
```

### Parameters

```python
df.group_by_dynamic(
    "timestamp",
    every="1h",           # Window frequency
    period="2h",          # Window duration (default: same as every)
    offset="30m",         # Shift window start
    closed="left",        # "left", "right", "both", "none"
    label="left",         # Which boundary to use as label
    start_by="window",    # "window", "datapoint", "monday", etc.
    include_boundaries=True,  # Add _lower/_upper boundary columns
).agg(...)
```

### Overlapping Windows

```python
# 2-hour windows every 1 hour (50% overlap)
df.group_by_dynamic(
    "timestamp",
    every="1h",      # New window every hour
    period="2h",     # Each window spans 2 hours
).agg(
    pl.col("value").mean().alias("rolling_2h_avg"),
)
```

### With Additional Grouping

```python
# Dynamic grouping within categories
df.group_by_dynamic(
    "timestamp",
    every="1d",
    group_by="category",       # Also group by category
).agg(
    pl.col("sales").sum().alias("daily_sales"),
)
```

## Rolling Windows

Value-based windows (one window per row):

```python
# Rolling 7-day average
df.sort("date").with_columns(
    pl.col("value").rolling_mean(window_size=7).alias("7d_avg"),
    pl.col("value").rolling_sum(window_size=7).alias("7d_sum"),
    pl.col("value").rolling_std(window_size=7).alias("7d_std"),
    pl.col("value").rolling_min(window_size=7).alias("7d_min"),
    pl.col("value").rolling_max(window_size=7).alias("7d_max"),
)

# Time-based rolling (variable row counts)
df.rolling(index_column="date", period="7d").agg(
    pl.col("value").mean().alias("7d_rolling_avg"),
)
```

### Shift and Lag

```python
df.sort("date").with_columns(
    pl.col("value").shift(1).alias("prev_value"),         # Lag by 1
    pl.col("value").shift(-1).alias("next_value"),        # Lead by 1
    pl.col("value").shift(7).alias("week_ago"),           # Lag by 7
    pl.col("value").diff().alias("daily_change"),         # Difference from previous
    pl.col("value").pct_change().alias("pct_change"),     # Percentage change
)
```

## Resampling

Convert between time frequencies:

```python
# Upsample (increase frequency with fill)
df.upsample(time_column="date", every="1d").with_columns(
    pl.col("value").interpolate(),  # Fill gaps with interpolation
)

# Downsample (decrease frequency with aggregation)
df.group_by_dynamic("timestamp", every="1h").agg(
    pl.col("value").mean(),
)
```

## Timezone Handling

```python
# Set timezone
df.with_columns(
    pl.col("datetime").dt.replace_time_zone("UTC").alias("utc"),
)

# Convert timezone
df.with_columns(
    pl.col("utc_datetime").dt.convert_time_zone("America/New_York").alias("eastern"),
    pl.col("utc_datetime").dt.convert_time_zone("Europe/London").alias("london"),
)

# Remove timezone
df.with_columns(
    pl.col("tz_datetime").dt.replace_time_zone(None).alias("naive"),
)

# Parse mixed timezone offsets
df.with_columns(
    pl.col("ts_str")
    .str.to_datetime("%Y-%m-%dT%H:%M:%S%z")
    .dt.convert_time_zone("UTC")
    .alias("normalized"),
)
```

## Common Patterns

### Business Days Filter

```python
df.filter(
    pl.col("date").dt.weekday().is_between(1, 5)  # Mon=1 to Fri=5
)
```

### Year-over-Year Comparison

```python
df.with_columns(
    pl.col("revenue").shift(365).over("product").alias("revenue_last_year"),
    ((pl.col("revenue") - pl.col("revenue").shift(365).over("product"))
     / pl.col("revenue").shift(365).over("product") * 100)
    .alias("yoy_growth_pct"),
)
```

### Date Range Generation

```python
# Generate date range
dates = pl.date_range(
    dt.date(2024, 1, 1),
    dt.date(2024, 12, 31),
    "1d",
    eager=True,
)

# As DataFrame
calendar = pl.DataFrame({"date": dates})
```

## Related Topics

- **Data Types** → `03-data-types.md`
- **Aggregation & GroupBy** → `07-aggregation-groupby.md`
- **Missing Data** → `11-missing-data.md`
