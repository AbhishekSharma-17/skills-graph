# Polars — Joins & Concatenation

> Source: [docs.pola.rs](https://docs.pola.rs/user-guide/transformations/joins/)

## Table of Contents

- [Join Types](#join-types)
- [Basic Join Syntax](#basic-join-syntax)
- [Join Types in Detail](#join-types-in-detail)
- [Advanced Joins](#advanced-joins)
- [Concatenation](#concatenation)
- [Pivot & Unpivot](#pivot--unpivot)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## Join Types

| Type | Description | Rows Returned |
|------|-------------|---------------|
| `inner` | Matches in both | Only matching rows |
| `left` | All from left | Left rows + matched right |
| `right` | All from right | Matched left + right rows |
| `full` | All from both | All rows, null where unmatched |
| `cross` | Cartesian product | left_rows × right_rows |
| `semi` | Filter by existence | Left rows that have a match |
| `anti` | Filter by absence | Left rows with no match |

## Basic Join Syntax

```python
import polars as pl

orders = pl.DataFrame({
    "order_id": [1, 2, 3, 4],
    "customer_id": [101, 102, 101, 103],
    "amount": [50.0, 75.0, 30.0, 100.0],
})

customers = pl.DataFrame({
    "customer_id": [101, 102, 104],
    "name": ["Alice", "Bob", "Diana"],
    "city": ["NYC", "LA", "Chicago"],
})

# Same column name in both DataFrames
result = orders.join(customers, on="customer_id", how="inner")

# Different column names
result = orders.join(
    customers,
    left_on="customer_id",
    right_on="customer_id",
    how="left",
)

# Multiple join keys
result = df1.join(df2, on=["key1", "key2"], how="inner")
```

## Join Types in Detail

### Inner Join

```python
# Only rows where customer_id exists in BOTH DataFrames
result = orders.join(customers, on="customer_id", how="inner")
# order_id 4 (customer_id=103) is dropped — no match in customers
# customer_id 104 (Diana) is dropped — no match in orders
```

### Left Join

```python
# All orders, with customer info where available
result = orders.join(customers, on="customer_id", how="left")
# order_id 4 (customer_id=103) has null for name/city
# Diana (customer_id=104) not included
```

### Right Join

```python
# All customers, with order info where available
result = orders.join(customers, on="customer_id", how="right")
# Diana (customer_id=104) included with null order fields
```

### Full (Outer) Join

```python
# All rows from both sides
result = orders.join(customers, on="customer_id", how="full")

# Coalesce duplicate key columns
result = orders.join(customers, on="customer_id", how="full", coalesce=True)
```

### Semi Join

```python
# Orders where the customer exists in the customers table
# (like filter, doesn't add columns from right)
result = orders.join(customers, on="customer_id", how="semi")
# Returns orders 1, 2, 3 (customer 101, 102 exist)
# Does NOT add name/city columns
```

### Anti Join

```python
# Orders where the customer does NOT exist in customers
result = orders.join(customers, on="customer_id", how="anti")
# Returns only order 4 (customer_id=103 not in customers)
```

### Cross Join

```python
# Every combination of rows (Cartesian product)
colors = pl.DataFrame({"color": ["red", "blue"]})
sizes = pl.DataFrame({"size": ["S", "M", "L"]})

result = colors.join(sizes, how="cross")
# 2 × 3 = 6 rows: (red,S), (red,M), (red,L), (blue,S), (blue,M), (blue,L)
```

## Advanced Joins

### Expression-Based Keys

```python
# Join with expression transformation on keys
result = df1.join(
    df2,
    left_on="email",
    right_on=pl.col("email").str.to_lowercase(),
    how="inner",
)
```

### Non-Equi Joins (join_where)

```python
# Join with inequality conditions
players = pl.DataFrame({
    "name": ["Alice", "Bob", "Charlie"],
    "cash": [100, 50, 200],
})
items = pl.DataFrame({
    "item": ["Sword", "Shield", "Potion"],
    "cost": [80, 60, 30],
})

# Players who can afford items
result = players.join_where(items, pl.col("cash") >= pl.col("cost"))
```

### Asof Joins (Nearest Match)

For time-series: match on nearest key rather than exact equality.

```python
trades = pl.DataFrame({
    "time": [
        "2024-01-01 09:30:00", "2024-01-01 09:31:00",
        "2024-01-01 09:32:00",
    ],
    "stock": ["AAPL", "AAPL", "GOOG"],
    "price": [150.0, 151.0, 2800.0],
}).with_columns(pl.col("time").str.to_datetime())

quotes = pl.DataFrame({
    "time": [
        "2024-01-01 09:29:50", "2024-01-01 09:30:30",
        "2024-01-01 09:31:30",
    ],
    "stock": ["AAPL", "AAPL", "GOOG"],
    "bid": [149.5, 150.5, 2799.0],
}).with_columns(pl.col("time").str.to_datetime())

# Match each trade with most recent quote
result = trades.join_asof(
    quotes,
    on="time",             # Match nearest time
    by="stock",            # Within same stock
    strategy="backward",   # Look backward in time (default)
)

# With tolerance (max time difference)
result = trades.join_asof(
    quotes,
    on="time",
    by="stock",
    tolerance="1m",        # Max 1 minute difference
)
```

### Suffix for Duplicate Column Names

```python
result = df1.join(df2, on="id", how="left", suffix="_right")
# Duplicate columns get "_right" suffix
```

## Concatenation

### Vertical (Stack Rows)

```python
# Same schema required
df1 = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
df2 = pl.DataFrame({"a": [5, 6], "b": [7, 8]})

result = pl.concat([df1, df2], how="vertical")
# shape: (4, 2)
```

### Horizontal (Side by Side)

```python
# Same number of rows required
names = pl.DataFrame({"name": ["Alice", "Bob"]})
ages = pl.DataFrame({"age": [30, 25]})

result = pl.concat([names, ages], how="horizontal")
```

### Diagonal (Union with Different Schemas)

```python
# Different columns — missing columns filled with null
df1 = pl.DataFrame({"a": [1], "b": [2]})
df2 = pl.DataFrame({"b": [3], "c": [4]})

result = pl.concat([df1, df2], how="diagonal")
# Columns: a, b, c — with nulls where missing
```

### Align (Outer Join-Style Concat)

```python
result = pl.concat([df1, df2], how="align")
# Aligns by column name, null-fills missing
```

## Pivot & Unpivot

### Pivot (Long to Wide)

```python
long_df = pl.DataFrame({
    "name": ["Alice", "Alice", "Bob", "Bob"],
    "metric": ["score", "rank", "score", "rank"],
    "value": [95, 1, 87, 3],
})

wide_df = long_df.pivot(
    on="metric",          # Column whose values become new column names
    index="name",          # Row identifier
    values="value",        # Values to fill
)
# Result: name | score | rank
#         Alice | 95   | 1
#         Bob   | 87   | 3
```

### Unpivot (Wide to Long)

```python
wide_df = pl.DataFrame({
    "name": ["Alice", "Bob"],
    "q1": [100, 80],
    "q2": [110, 85],
    "q3": [105, 90],
})

long_df = wide_df.unpivot(
    on=["q1", "q2", "q3"],     # Columns to melt
    index="name",               # Keep as identifier
    variable_name="quarter",    # Name for variable column
    value_name="revenue",       # Name for value column
)
```

## Common Patterns

### Lookup Table

```python
# Enrich data with a lookup table
result = (
    transactions
    .join(product_catalog, on="product_id", how="left")
    .join(store_locations, on="store_id", how="left")
)
```

### Self-Join

```python
# Find employees with the same manager
result = employees.join(
    employees.select("employee_id", "manager_id", pl.col("name").alias("colleague")),
    on="manager_id",
    how="inner",
).filter(pl.col("name") != pl.col("colleague"))
```

### Filter by Another Table (Semi Join)

```python
# Only keep orders from VIP customers
vip_orders = orders.join(vip_customers, on="customer_id", how="semi")
```

## Common Pitfalls

1. **Duplicate column names** — Use `suffix` parameter or rename before joining
2. **Join key type mismatch** — Cast to same type before joining
3. **Memory explosion with cross joins** — Result size is left_rows × right_rows
4. **Asof join requires sorted data** — Sort by the `on` column first
5. **Full join column coalescing** — Use `coalesce=True` to merge key columns

## Related Topics

- **Filtering & Selection** → `06-filtering-selection.md`
- **Lazy API** → `04-lazy-api.md`
- **Time Series** → `10-time-series.md`
