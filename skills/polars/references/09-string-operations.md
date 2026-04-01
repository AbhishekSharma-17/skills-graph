# Polars — String Operations

> Source: [docs.pola.rs](https://docs.pola.rs/user-guide/expressions/strings/)

## Table of Contents

- [The str Namespace](#the-str-namespace)
- [Pattern Matching](#pattern-matching)
- [Pattern Extraction](#pattern-extraction)
- [Replacement](#replacement)
- [Case Conversion](#case-conversion)
- [Splitting & Joining](#splitting--joining)
- [Stripping & Padding](#stripping--padding)
- [Slicing](#slicing)
- [Length & Counting](#length--counting)
- [Parsing & Conversion](#parsing--conversion)
- [Common Patterns](#common-patterns)

## The str Namespace

All string operations are accessed through the `.str` namespace on string columns:

```python
import polars as pl

df = pl.DataFrame({
    "text": ["Hello World", "foo bar", "POLARS IS FAST"],
    "email": ["alice@example.com", "bob@test.org", "charlie@example.com"],
    "code": ["ABC-123", "DEF-456", "GHI-789"],
})

# Access via .str
pl.col("text").str.to_uppercase()
pl.col("email").str.contains("@example")
```

## Pattern Matching

### contains — Test for Pattern

```python
# Regex pattern (default)
df.filter(pl.col("text").str.contains("W.rld"))

# Literal string (no regex)
df.filter(pl.col("text").str.contains("World", literal=True))

# Case-insensitive (use regex flag)
df.filter(pl.col("text").str.contains("(?i)hello"))
```

### starts_with / ends_with

```python
df.filter(pl.col("email").str.starts_with("alice"))
df.filter(pl.col("email").str.ends_with(".com"))

# Dynamic values from another column
df.filter(pl.col("text").str.starts_with(pl.col("prefix")))
```

### count_matches

```python
# Count occurrences of pattern
df.with_columns(
    pl.col("text").str.count_matches(r"\w+").alias("word_count"),
    pl.col("code").str.count_matches(r"\d").alias("digit_count"),
)
```

## Pattern Extraction

### extract — First Match

```python
# Extract first regex group match
df.with_columns(
    pl.col("code").str.extract(r"([A-Z]+)-(\d+)", group_index=1).alias("letters"),
    pl.col("code").str.extract(r"([A-Z]+)-(\d+)", group_index=2).alias("numbers"),
)
```

### extract_all — All Matches

```python
# Returns List(String) with all matches
df.with_columns(
    pl.col("text").str.extract_all(r"\b\w{4,}\b").alias("long_words"),
)
```

### extract_groups — Named Groups

```python
df.with_columns(
    pl.col("email").str.extract_groups(
        r"(?P<user>\w+)@(?P<domain>[\w.]+)"
    ).alias("email_parts"),
)
# Returns Struct with "user" and "domain" fields
```

## Replacement

### replace — First Occurrence

```python
df.with_columns(
    pl.col("text").str.replace(r"\d+", "NUM").alias("cleaned"),
)
```

### replace_all — All Occurrences

```python
df.with_columns(
    pl.col("text").str.replace_all(r"\s+", "_").alias("underscored"),
    pl.col("code").str.replace_all(r"\d", "X").alias("masked"),
)
```

### Literal Replacement

```python
df.with_columns(
    pl.col("text").str.replace("World", "Polars", literal=True),
)
```

**Note:** Polars uses Rust's `regex` crate syntax, which differs slightly from Python's `re`. Notable differences: no lookahead/lookbehind support in default mode.

## Case Conversion

```python
df.with_columns(
    pl.col("text").str.to_lowercase().alias("lower"),
    pl.col("text").str.to_uppercase().alias("upper"),
    pl.col("text").str.to_titlecase().alias("title"),
)
# "Hello World" → "hello world", "HELLO WORLD", "Hello World"
```

## Splitting & Joining

### split — Into List

```python
# Split into List(String)
df.with_columns(
    pl.col("text").str.split(" ").alias("words"),
)

# Split with limit
df.with_columns(
    pl.col("text").str.splitn(" ", 2).alias("first_two"),
)
```

### join — List to String

```python
# After splitting or from list column
df.with_columns(
    pl.col("words").list.join(", ").alias("joined"),
)
```

### concat_str — Combine Columns

```python
# Concatenate multiple columns into one string
df.with_columns(
    pl.concat_str(["first_name", " ", "last_name"]).alias("full_name"),
)

# With separator
df.with_columns(
    pl.concat_str(["city", "state", "zip"], separator=", ").alias("address"),
)
```

## Stripping & Padding

### Stripping (Trimming)

```python
# Strip whitespace
pl.col("text").str.strip_chars()            # Leading + trailing
pl.col("text").str.strip_chars_start()      # Leading only
pl.col("text").str.strip_chars_end()        # Trailing only

# Strip specific characters (character SET)
pl.col("text").str.strip_chars(", .!")      # Any of these chars

# Strip exact prefix/suffix (literal STRING)
pl.col("url").str.strip_prefix("https://")
pl.col("file").str.strip_suffix(".csv")
```

**Important distinction:**
- `strip_chars("abc")` removes any of 'a', 'b', or 'c' from edges
- `strip_prefix("abc")` removes the exact string "abc" from the start

### Padding

```python
# Pad to fixed width
pl.col("id").str.pad_start(5, "0")   # "42" → "00042"
pl.col("id").str.pad_end(10, " ")    # Right-pad with spaces
```

## Slicing

```python
# Substring by position
pl.col("code").str.slice(0, 3)     # First 3 chars: "ABC"
pl.col("code").str.slice(4)        # From position 4: "123"
pl.col("code").str.slice(-3)       # Last 3 chars: "123"

# Head / Tail
pl.col("code").str.head(3)        # First 3 chars
pl.col("code").str.tail(3)        # Last 3 chars

# Dynamic offset from column
pl.col("text").str.slice(pl.col("start_pos"), pl.col("length"))
```

## Length & Counting

```python
# Character count (Unicode-aware)
pl.col("text").str.len_chars()

# Byte count (faster for ASCII-only text)
pl.col("text").str.len_bytes()
```

## Parsing & Conversion

### String to Numeric

```python
pl.col("amount").cast(pl.Float64)
pl.col("count").cast(pl.Int64)

# With cleanup first
pl.col("price").str.replace_all(r"[$,]", "").cast(pl.Float64)
```

### String to Temporal

```python
# To date
pl.col("date_str").str.to_date("%Y-%m-%d")

# To datetime
pl.col("ts_str").str.to_datetime("%Y-%m-%d %H:%M:%S")

# To time
pl.col("time_str").str.to_time("%H:%M:%S")
```

### JSON Parsing

```python
# Parse JSON strings into Struct
pl.col("json_data").str.json_decode()

# Extract specific JSON path
pl.col("json_data").str.json_path_match("$.name")
```

## Common Patterns

### Email Domain Extraction

```python
df.with_columns(
    pl.col("email").str.extract(r"@(.+)$", group_index=1).alias("domain"),
)
```

### URL Parsing

```python
df.with_columns(
    pl.col("url").str.extract(r"https?://([^/]+)", group_index=1).alias("host"),
    pl.col("url").str.extract(r"https?://[^/]+(/.+)$", group_index=1).alias("path"),
)
```

### Clean and Normalize Text

```python
df.with_columns(
    pl.col("text")
    .str.strip_chars()
    .str.to_lowercase()
    .str.replace_all(r"\s+", " ")
    .alias("normalized"),
)
```

### Split Column into Multiple

```python
# Split "first last" into separate columns
df.with_columns(
    pl.col("full_name").str.split(" ").list.get(0).alias("first_name"),
    pl.col("full_name").str.split(" ").list.get(-1).alias("last_name"),
)

# Or use extract with groups
df.with_columns(
    pl.col("full_name").str.extract(r"^(\S+)\s+(.+)$", group_index=1).alias("first"),
    pl.col("full_name").str.extract(r"^(\S+)\s+(.+)$", group_index=2).alias("last"),
)
```

## Related Topics

- **Expressions** → `02-expressions.md`
- **Data Types** → `03-data-types.md`
- **Filtering & Selection** → `06-filtering-selection.md`
