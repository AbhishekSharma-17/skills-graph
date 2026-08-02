# Streamlit — Caching & Performance

> Source: [docs.streamlit.io/develop/concepts/architecture/caching](https://docs.streamlit.io/develop/concepts/architecture/caching) | Version: 1.59.x

## Table of Contents

- [Why Caching Matters](#why-caching-matters)
- [st.cache_data](#stcache_data)
- [st.cache_resource](#stcache_resource)
- [Cache Parameters](#cache-parameters)
- [Parameter Hashing](#parameter-hashing)
- [Mutation Safety](#mutation-safety)
- [Advanced Features](#advanced-features)
- [Choosing the Right Cache](#choosing-the-right-cache)
- [Performance Tips](#performance-tips)
- [Common Pitfalls](#common-pitfalls)

## Why Caching Matters

Streamlit reruns the entire script on every interaction. Without caching:
- A CSV load runs on every click
- An ML model reloads on every slider move
- An API call fires on every checkbox toggle

Caching stores function results so they only compute once for a given set of inputs.

## st.cache_data

For **serializable data** — DataFrames, arrays, strings, numbers, dicts. Returns a **copy** of the cached value (safe from mutation).

```python
@st.cache_data
def load_data(url: str) -> pd.DataFrame:
    return pd.read_csv(url)

df = load_data("https://example.com/data.csv")
# Second call with same URL returns cached copy instantly
```

### When to Use

- Loading data from CSV, Parquet, databases
- API calls that return JSON/data
- DataFrame transformations and aggregations
- NumPy computations
- ML model inference (the prediction, not the model itself)
- Any function that returns data you want to display

### How It Works

1. First call: function executes, result is serialized (pickled) and cached
2. Same-arguments call: cached result is deserialized and returned as a **new copy**
3. Different arguments: function executes again, new result cached

The copy-on-return behavior means mutations to the returned value never affect the cache:

```python
@st.cache_data
def get_list():
    return [1, 2, 3]

my_list = get_list()
my_list.append(4)     # Only affects this copy
get_list()             # Still returns [1, 2, 3]
```

## st.cache_resource

For **unserializable, shared objects** — database connections, ML models, file handles. Returns the **same object** (no copy).

```python
@st.cache_resource
def load_model():
    from transformers import pipeline
    return pipeline("sentiment-analysis")

model = load_model()
# All users/sessions share the SAME model instance
```

### When to Use

- Loading ML models (PyTorch, TensorFlow, Hugging Face)
- Database connections (`sqlalchemy.Engine`, `psycopg2.connection`)
- HTTP clients (`httpx.Client`, `requests.Session`)
- Thread pools, process pools
- Any large object you don't want to serialize

### How It Works

1. First call: function executes, result stored **by reference**
2. Same-arguments call: returns the **exact same object**
3. Shared across all users and sessions in the server process

## Cache Parameters

### ttl — Time-to-Live

Invalidate cache entries after a duration:

```python
@st.cache_data(ttl=3600)          # 3600 seconds = 1 hour
def fetch_weather():
    return api.get_weather()

@st.cache_data(ttl="1h")          # String format also works
def fetch_stocks():
    return api.get_stocks()

from datetime import timedelta
@st.cache_data(ttl=timedelta(hours=1))
def fetch_news():
    return api.get_news()
```

### max_entries

Limit the number of cached results (LRU eviction):

```python
@st.cache_data(max_entries=100)
def compute(seed: int):
    return np.random.RandomState(seed).rand(10000)
```

### show_spinner

Control the loading indicator:

```python
@st.cache_data(show_spinner=True)           # Default spinner
def load():
    ...

@st.cache_data(show_spinner="Loading data...")  # Custom message
def load():
    ...

@st.cache_data(show_spinner=False)          # No spinner
def load():
    ...
```

### persist

Save cache to disk for persistence across server restarts:

```python
@st.cache_data(persist="disk")
def expensive_computation():
    return compute_something()
```

## Parameter Hashing

All function parameters must be hashable for caching to work. Streamlit hashes parameters to create cache keys.

### Unhashable Parameters — Underscore Prefix

Prefix parameter names with `_` to exclude them from the hash:

```python
@st.cache_data
def query(_connection, sql: str) -> pd.DataFrame:
    return pd.read_sql(sql, _connection)

# Only `sql` is hashed — `_connection` is ignored
```

### Custom Hash Functions

Define how to hash custom types:

```python
class MyModel:
    def __init__(self, name: str, version: int):
        self.name = name
        self.version = version

@st.cache_data(hash_funcs={MyModel: lambda m: f"{m.name}_{m.version}"})
def predict(model: MyModel, data):
    return model.run(data)
```

### Common hash_funcs Patterns

```python
# Pydantic models
hash_funcs={MyPydanticModel: lambda m: m.model_dump_json()}

# Datetime with timezone
hash_funcs={datetime: lambda dt: dt.isoformat()}

# Custom class by attribute
hash_funcs={Config: lambda c: (c.db_url, c.table_name)}
```

## Mutation Safety

### st.cache_data — Safe (Copies)

```python
@st.cache_data
def get_data():
    return {"users": [1, 2, 3]}

data = get_data()
data["users"].append(4)    # Only this copy is affected
get_data()                  # Still returns {"users": [1, 2, 3]}
```

### st.cache_resource — Unsafe (Shared Reference)

```python
@st.cache_resource
def get_list():
    return [1, 2, 3]

lst = get_list()
lst.append(4)              # Mutates the cached object!
get_list()                  # Now returns [1, 2, 3, 4] for ALL users
```

**Rules for `st.cache_resource`:**
- Never mutate the returned object
- If mutation is unavoidable, use locks for thread safety
- Consider `st.cache_data` if the object is serializable

### Thread Safety with cache_resource

```python
import threading

@st.cache_resource
def get_shared_state():
    return {"data": [], "lock": threading.Lock()}

state = get_shared_state()
with state["lock"]:
    state["data"].append("new_item")
```

## Advanced Features

### Static Element Replay

Cached functions can contain Streamlit display calls — they replay on cache hits:

```python
@st.cache_data
def load_and_display(url):
    df = pd.read_csv(url)
    st.info(f"Loaded {len(df)} rows")     # Replays from cache
    return df
```

### Experimental Widget Support

```python
@st.cache_data(experimental_allow_widgets=True)
def get_filtered_data():
    n_rows = st.slider("Rows to show", 10, 1000, 100)
    return load_all_data().head(n_rows)
```

Caveat: each unique widget value creates a new cache entry.

### Clearing Cache

```python
# Clear all cache_data entries
st.cache_data.clear()

# Clear all cache_resource entries
st.cache_resource.clear()

# Clear a specific function's cache
load_data.clear()
```

## Choosing the Right Cache

| Criterion | `st.cache_data` | `st.cache_resource` |
|-----------|-----------------|---------------------|
| **Returns** | Copy (deserialized) | Same object (reference) |
| **Thread-safe** | Yes (isolated copies) | No (shared, manual locking) |
| **Best for** | DataFrames, dicts, lists | Connections, models, clients |
| **Mutation risk** | None (copies) | High (shared state) |
| **Serializable** | Required (pickle) | Not required |
| **Memory** | Higher (copies per caller) | Lower (single instance) |
| **Speed** | Slower (serialize/deserialize) | Faster (no serialization) |
| **Cross-session** | Shared | Shared |

### Decision Tree

1. Is the object serializable (DataFrame, dict, list, number)? → `@st.cache_data`
2. Is it a connection, model, or client? → `@st.cache_resource`
3. Is it >100M rows and you need speed? → `@st.cache_resource` (but handle mutations)
4. Is it a small config dict? → `st.session_state` (not caching)

## Performance Tips

### 1. Cache Data Loading

```python
@st.cache_data
def load_data():
    return pd.read_csv("large_file.csv")

# NOT:
# df = pd.read_csv("large_file.csv")  # Reloads every rerun
```

### 2. Separate Data from Display

```python
@st.cache_data
def compute_stats(df):
    return df.describe()

# Display is not cached — that's fine
stats = compute_stats(df)
st.dataframe(stats)
```

### 3. Use Fragments for Partial Reruns

```python
@st.fragment
def chart_section():
    # Only this section reruns when its widgets change
    metric = st.selectbox("Metric", ["Revenue", "Users", "Orders"])
    st.line_chart(get_metric_data(metric))
```

### 4. Avoid Wide Layout Waste

Use `st.columns` to prevent unnecessary recomputation of independent sections.

## Common Pitfalls

### 1. Forgetting to Cache

```python
# Slow — loads on every rerun
df = pd.read_csv("data.csv")

# Fast — cached
@st.cache_data
def load():
    return pd.read_csv("data.csv")
df = load()
```

### 2. Caching Functions with Side Effects

```python
# Bad — email sent on every cache miss
@st.cache_data
def process_and_notify(data):
    result = process(data)
    send_email(result)       # Side effect!
    return result
```

### 3. Lambda/Closure as Parameter

```python
# Fails — lambdas aren't hashable
@st.cache_data
def compute(func):           # ❌
    return func(42)

# Fix — use underscore prefix
@st.cache_data
def compute(_func, key):     # ✅
    return _func(42)
```

## Related Topics

- `00-overview.md` — Execution model (why caching is needed)
- `05-session-state.md` — State vs cache
- `07-forms-fragments.md` — Fragments for partial reruns
- `11-connections-config.md` — Caching database connections
