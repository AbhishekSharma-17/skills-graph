# Turso Python SDK

> Source: [docs.turso.tech/sdk/python](https://docs.turso.tech/sdk/python/quickstart)

## Table of Contents
- [Package Selection](#package-selection)
- [Local / Embedded (pyturso)](#local--embedded-pyturso)
- [Remote Access (libsql)](#remote-access-libsql)
- [Sync Mode](#sync-mode)
- [Query Execution](#query-execution)
- [Parameter Binding](#parameter-binding)
- [Transactions](#transactions)
- [Result Handling](#result-handling)
- [SQLAlchemy Integration](#sqlalchemy-integration)
- [Flask Integration](#flask-integration)
- [Common Pitfalls](#common-pitfalls)

## Package Selection

| Package | Use Case | Install |
|---------|----------|---------|
| `pyturso` | Local/embedded, sync-enabled, new Rust engine | `pip install pyturso` |
| `libsql` | Remote/over-the-wire to Turso Cloud | `pip install libsql` |

For new projects, prefer `pyturso`. Use `libsql` when you only need remote access without local files.

## Local / Embedded (pyturso)

```bash
pip install pyturso
# or
uv add pyturso
```

```python
import turso

# File-based database
db = turso.connect("app.db")

# In-memory database
db = turso.connect(":memory:")

# Create tables
db.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL
    )
""")

# Insert data
db.execute("INSERT INTO users (name, email) VALUES (?, ?)", ("Alice", "alice@example.com"))
db.commit()

# Query data
for row in db.execute("SELECT * FROM users"):
    print(row)

# Single row
row = db.execute("SELECT * FROM users WHERE id = ?", (1,)).fetchone()
```

## Remote Access (libsql)

```bash
pip install libsql
# or
uv add libsql
```

```python
import libsql
import os

conn = libsql.connect(
    database=os.environ["TURSO_DATABASE_URL"],
    auth_token=os.environ["TURSO_AUTH_TOKEN"],
)

# Execute queries
conn.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))
conn.commit()

# Fetch results
rows = conn.execute("SELECT * FROM users").fetchall()
for row in rows:
    print(row)
```

## Sync Mode

Local reads/writes with explicit cloud synchronization:

```python
import turso.sync
import os

db = turso.sync.connect(
    "app.db",
    remote_url=os.environ["TURSO_DATABASE_URL"],
    auth_token=os.environ["TURSO_AUTH_TOKEN"],
)

# All reads/writes happen locally
db.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))
db.commit()

# Sync with cloud
db.push()   # Send local changes to cloud
db.pull()   # Fetch remote changes locally
```

### Offline-First Pattern

```python
import turso.sync
import os

db = turso.sync.connect(
    "app.db",
    remote_url=os.environ.get("TURSO_DATABASE_URL", ""),
    auth_token=os.environ.get("TURSO_AUTH_TOKEN", ""),
)

# Works without internet — writes go to local file
db.execute("INSERT INTO logs (message) VALUES (?)", ("offline event",))
db.commit()

# When connectivity is available, sync
try:
    db.push()
    db.pull()
except Exception:
    pass  # Will sync on next successful attempt
```

## Query Execution

### Execute with Commit

```python
# Writes require explicit commit
db.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))
db.execute("INSERT INTO users (name) VALUES (?)", ("Bob",))
db.commit()
```

### Execute Many

```python
users = [("Alice",), ("Bob",), ("Charlie",)]
db.executemany("INSERT INTO users (name) VALUES (?)", users)
db.commit()
```

### Fetch Patterns

```python
# Fetch all rows
rows = db.execute("SELECT * FROM users").fetchall()

# Fetch one row
row = db.execute("SELECT * FROM users WHERE id = ?", (1,)).fetchone()

# Iterate directly
for row in db.execute("SELECT * FROM users"):
    print(row)

# With column names
cursor = db.execute("SELECT * FROM users")
columns = [desc[0] for desc in cursor.description]
for row in cursor:
    user = dict(zip(columns, row))
    print(user)
```

## Parameter Binding

### Positional Parameters

```python
db.execute("SELECT * FROM users WHERE id = ? AND name = ?", (1, "Alice"))
```

### Named Parameters

```python
db.execute(
    "SELECT * FROM users WHERE name = :name AND email = :email",
    {"name": "Alice", "email": "alice@example.com"}
)
```

## Transactions

```python
# Automatic with context manager
try:
    db.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", (100, 1))
    db.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (100, 2))
    db.commit()
except Exception:
    db.rollback()
    raise
```

### Read-Only Transactions

```python
# Use executescript for DDL or multi-statement operations
db.executescript("""
    BEGIN;
    SELECT * FROM users;
    SELECT * FROM orders;
    COMMIT;
""")
```

## Result Handling

### Row Objects

```python
cursor = db.execute("SELECT id, name, email FROM users")

# Tuple access
row = cursor.fetchone()
id_val = row[0]
name = row[1]
email = row[2]

# Description for column names
columns = [desc[0] for desc in cursor.description]
# ['id', 'name', 'email']
```

### Affected Rows

```python
cursor = db.execute("DELETE FROM users WHERE active = 0")
print(f"Deleted {cursor.rowcount} users")
db.commit()
```

### Last Insert ID

```python
db.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))
print(f"New user ID: {db.execute('SELECT last_insert_rowid()').fetchone()[0]}")
db.commit()
```

## SQLAlchemy Integration

```bash
pip install sqlalchemy libsql
```

```python
from sqlalchemy import create_engine, text
import os

# Remote connection
url = os.environ["TURSO_DATABASE_URL"].replace("libsql://", "")
token = os.environ["TURSO_AUTH_TOKEN"]
engine = create_engine(
    f"sqlite+libsql://{url}?authToken={token}&secure=true",
    echo=True,
)

# Local file connection
engine = create_engine("sqlite+libsql:///app.db")

# Usage with SQLAlchemy ORM
with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM users"))
    for row in result:
        print(row)
```

### With SQLAlchemy ORM Models

```python
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base, Session

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)

# Create tables
Base.metadata.create_all(engine)

# Query
with Session(engine) as session:
    users = session.query(User).all()
```

## Flask Integration

```python
from flask import Flask, g
import turso

app = Flask(__name__)

def get_db():
    if "db" not in g:
        g.db = turso.connect("app.db")
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()

@app.route("/users")
def list_users():
    db = get_db()
    rows = db.execute("SELECT * FROM users").fetchall()
    return {"users": [dict(zip(["id", "name"], row)) for row in rows]}
```

## Common Pitfalls

1. **Forgetting `db.commit()`** — Writes are not persisted until you call `commit()`. This follows Python's DB-API 2.0 convention
2. **Using `pyturso` for remote-only** — `pyturso` is for local/embedded use. Use `libsql` package for pure remote access
3. **SQLAlchemy URL format** — Must use `sqlite+libsql://` scheme and replace `libsql://` from the Turso URL
4. **Thread safety** — Connections are not thread-safe. Use connection-per-thread or connection pooling
5. **Not closing connections** — Always close connections when done, especially in web frameworks. Use context managers or teardown hooks
6. **Parameter tuple for single values** — `db.execute("... WHERE id = ?", (1,))` needs the trailing comma for a single-element tuple
