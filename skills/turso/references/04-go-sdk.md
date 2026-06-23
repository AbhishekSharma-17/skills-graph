# Turso Go SDK

> Source: [docs.turso.tech/sdk/go](https://docs.turso.tech/sdk/go/quickstart)

## Table of Contents
- [Package Selection](#package-selection)
- [Local with Sync (tursogo)](#local-with-sync-tursogo)
- [Remote Access (libsql-client-go)](#remote-access-libsql-client-go)
- [Query Execution](#query-execution)
- [Parameter Binding](#parameter-binding)
- [Transactions](#transactions)
- [Sync Operations](#sync-operations)
- [Common Pitfalls](#common-pitfalls)

## Package Selection

| Package | Use Case | CGO Required |
|---------|----------|-------------|
| `turso.tech/database/tursogo` | Local/embedded + sync, `database/sql` driver | No |
| `github.com/tursodatabase/libsql-client-go` | Remote access via libSQL wire protocol | No |
| `github.com/tursodatabase/go-libsql` | Embedded replicas (legacy) | Yes |

For new projects, prefer `tursogo` — it implements Go's standard `database/sql` interface and requires no CGO.

## Local with Sync (tursogo)

```bash
go get turso.tech/database/tursogo
```

### Local-Only Database

```go
package main

import (
    "database/sql"
    "fmt"
    "log"

    _ "turso.tech/database/tursogo"
)

func main() {
    db, err := sql.Open("turso", "app.db")
    if err != nil {
        log.Fatal(err)
    }
    defer db.Close()

    // Create table
    _, err = db.Exec(`CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL
    )`)
    if err != nil {
        log.Fatal(err)
    }

    // Insert
    result, err := db.Exec("INSERT INTO users (name, email) VALUES (?, ?)", "Alice", "alice@example.com")
    if err != nil {
        log.Fatal(err)
    }
    id, _ := result.LastInsertId()
    fmt.Printf("Inserted user ID: %d\n", id)

    // Query
    rows, err := db.Query("SELECT id, name, email FROM users")
    if err != nil {
        log.Fatal(err)
    }
    defer rows.Close()

    for rows.Next() {
        var id int
        var name, email string
        rows.Scan(&id, &name, &email)
        fmt.Printf("%d: %s <%s>\n", id, name, email)
    }
}
```

### Sync-Enabled Database

```go
package main

import (
    "context"
    "fmt"
    "log"
    "os"

    turso "turso.tech/database/tursogo"
)

func main() {
    ctx := context.Background()

    syncDb, err := turso.NewTursoSyncDb(ctx, turso.TursoSyncDbConfig{
        Path:      "app.db",
        RemoteUrl: os.Getenv("TURSO_DATABASE_URL"),
        AuthToken: os.Getenv("TURSO_AUTH_TOKEN"),
    })
    if err != nil {
        log.Fatal(err)
    }

    // Get standard database/sql handle
    db := syncDb.DB()
    defer db.Close()

    // All reads/writes happen locally
    db.Exec("INSERT INTO users (name) VALUES (?)", "Alice")

    // Sync with cloud
    if err := syncDb.Push(ctx); err != nil {
        log.Printf("Push failed: %v", err)
    }

    if err := syncDb.Pull(ctx); err != nil {
        log.Printf("Pull failed: %v", err)
    }

    fmt.Println("Synced successfully")
}
```

## Remote Access (libsql-client-go)

```bash
go get github.com/tursodatabase/libsql-client-go/libsql
```

```go
package main

import (
    "database/sql"
    "fmt"
    "log"
    "os"

    _ "github.com/tursodatabase/libsql-client-go/libsql"
)

func main() {
    url := os.Getenv("TURSO_DATABASE_URL") + "?authToken=" + os.Getenv("TURSO_AUTH_TOKEN")
    db, err := sql.Open("libsql", url)
    if err != nil {
        log.Fatal(err)
    }
    defer db.Close()

    rows, err := db.Query("SELECT id, name FROM users")
    if err != nil {
        log.Fatal(err)
    }
    defer rows.Close()

    for rows.Next() {
        var id int
        var name string
        rows.Scan(&id, &name)
        fmt.Printf("%d: %s\n", id, name)
    }
}
```

## Query Execution

### Exec (INSERT, UPDATE, DELETE)

```go
result, err := db.Exec("INSERT INTO users (name, email) VALUES (?, ?)", "Alice", "alice@example.com")
if err != nil {
    log.Fatal(err)
}
rowsAffected, _ := result.RowsAffected()
lastID, _ := result.LastInsertId()
```

### Query (SELECT — multiple rows)

```go
rows, err := db.Query("SELECT id, name FROM users WHERE active = ?", true)
if err != nil {
    log.Fatal(err)
}
defer rows.Close()

for rows.Next() {
    var id int
    var name string
    if err := rows.Scan(&id, &name); err != nil {
        log.Fatal(err)
    }
    fmt.Printf("%d: %s\n", id, name)
}
if err := rows.Err(); err != nil {
    log.Fatal(err)
}
```

### QueryRow (SELECT — single row)

```go
var name string
err := db.QueryRow("SELECT name FROM users WHERE id = ?", 1).Scan(&name)
if err == sql.ErrNoRows {
    fmt.Println("No user found")
} else if err != nil {
    log.Fatal(err)
}
```

### Prepared Statements

```go
stmt, err := db.Prepare("INSERT INTO users (name, email) VALUES (?, ?)")
if err != nil {
    log.Fatal(err)
}
defer stmt.Close()

for _, user := range users {
    _, err := stmt.Exec(user.Name, user.Email)
    if err != nil {
        log.Fatal(err)
    }
}
```

## Parameter Binding

Go uses `?` positional placeholders:

```go
// Positional (only supported form)
db.Query("SELECT * FROM users WHERE id = ? AND name = ?", 1, "Alice")

// Named parameters are NOT supported via database/sql
// Use positional ? placeholders
```

## Transactions

```go
tx, err := db.Begin()
if err != nil {
    log.Fatal(err)
}

_, err = tx.Exec("UPDATE accounts SET balance = balance - ? WHERE id = ?", 100, fromID)
if err != nil {
    tx.Rollback()
    log.Fatal(err)
}

_, err = tx.Exec("UPDATE accounts SET balance = balance + ? WHERE id = ?", 100, toID)
if err != nil {
    tx.Rollback()
    log.Fatal(err)
}

if err := tx.Commit(); err != nil {
    log.Fatal(err)
}
```

### Context-Aware Transactions

```go
ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
defer cancel()

tx, err := db.BeginTx(ctx, &sql.TxOptions{ReadOnly: true})
if err != nil {
    log.Fatal(err)
}

rows, err := tx.QueryContext(ctx, "SELECT * FROM users")
// ... process rows ...

tx.Commit()
```

## Sync Operations

```go
// Push local changes to cloud
err := syncDb.Push(ctx)

// Pull remote changes
err := syncDb.Pull(ctx)

// Checkpoint — compact local WAL
err := syncDb.Checkpoint(ctx)
```

## Common Pitfalls

1. **Always `defer rows.Close()`** — Failing to close rows leaks connections
2. **Check `rows.Err()` after iteration** — Errors during iteration are surfaced here, not via `rows.Next()`
3. **No named parameters** — Go's `database/sql` only supports `?` positional placeholders
4. **Auth token in URL** — For `libsql-client-go`, append `?authToken=...` to the URL string
5. **CGO dependency** — `go-libsql` (embedded replicas) requires CGO; prefer `tursogo` for CGO-free operation
6. **Connection pooling** — `database/sql` manages a pool automatically. Don't open/close `sql.DB` per request
