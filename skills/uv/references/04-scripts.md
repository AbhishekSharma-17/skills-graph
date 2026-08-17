# uv — Scripts

> Source: [Running scripts](https://docs.astral.sh/uv/guides/scripts/)

## Table of Contents

- [Running Scripts](#running-scripts)
- [Scripts with Dependencies](#scripts-with-dependencies)
- [Inline Script Metadata (PEP 723)](#inline-script-metadata-pep-723)
- [Shebang Support](#shebang-support)
- [Script Locking](#script-locking)
- [Reproducibility](#reproducibility)
- [GUI Scripts](#gui-scripts)

## Running Scripts

`uv run` executes Python scripts with automatic environment management:

```bash
# Run a script
uv run example.py

# Run with arguments
uv run example.py --verbose --output results.json

# Run a module
uv run -m http.server 8000

# Run inline code
uv run -- python -c "print('hello world')"

# Pipe code via stdin
echo 'print("hello")' | uv run -

# Run with a specific Python version
uv run --python 3.11 example.py
```

### Within a Project

When run inside a project directory (containing `pyproject.toml`), `uv run` automatically:
1. Ensures the lock file is current
2. Syncs the virtual environment
3. Runs the command with project dependencies available

```bash
# Skip project dependencies for standalone scripts
uv run --no-project script.py
```

## Scripts with Dependencies

### Ad-hoc Dependencies (--with)

Add dependencies at invocation time without modifying project configuration:

```bash
# Single dependency
uv run --with rich script.py

# Version-constrained
uv run --with 'rich>12,<14' script.py

# Multiple dependencies
uv run --with requests --with rich script.py

# Override project dependency version
uv run --with 'httpx==0.26.0' script.py

# Combined with --no-project for standalone scripts
uv run --no-project --with requests --with rich script.py
```

## Inline Script Metadata (PEP 723)

The recommended way to declare script dependencies. Metadata is embedded directly in the script file as a TOML comment block:

### Creating a Script with Metadata

```bash
# Initialize a script with Python version
uv init --script example.py --python 3.12

# Add dependencies to a script
uv add --script example.py 'requests<3' 'rich'

# Remove dependencies from a script
uv remove --script example.py rich
```

### Script Format

```python
# /// script
# dependencies = [
#   "requests<3",
#   "rich",
# ]
# requires-python = ">=3.12"
# ///

import requests
from rich import print as rprint

resp = requests.get("https://httpbin.org/json")
rprint(resp.json())
```

### Running Scripts with Inline Metadata

```bash
# uv reads the metadata block automatically
uv run example.py
```

When inline metadata is present:
- Project dependencies are **ignored** (no need for `--no-project`)
- Dependencies are installed into a temporary, cached environment
- The environment is reused across invocations if dependencies haven't changed

### Adding Custom Package Indexes

```bash
uv add --index "https://custom.example.com/simple" --script example.py 'my-package'
```

Produces:

```python
# /// script
# dependencies = [
#   "my-package",
# ]
# requires-python = ">=3.12"
#
# [[tool.uv.index]]
# url = "https://custom.example.com/simple"
# ///
```

### Full Metadata Options

```python
# /// script
# dependencies = [
#   "requests>=2.31",
#   "rich>=13.0",
# ]
# requires-python = ">=3.11"
#
# [tool.uv]
# exclude-newer = "2026-08-17T00:00:00Z"
#
# [tool.uv.sources]
# requests = { git = "https://github.com/psf/requests", tag = "v2.32.0" }
#
# [[tool.uv.index]]
# url = "https://custom.example.com/simple"
# ///
```

## Shebang Support

Make scripts directly executable on Unix systems:

```python
#!/usr/bin/env -S uv run --script

# /// script
# dependencies = ["requests", "rich"]
# requires-python = ">=3.12"
# ///

import requests
from rich import print as rprint

resp = requests.get("https://httpbin.org/json")
rprint(resp.json())
```

```bash
chmod +x example.py
./example.py  # Runs directly, uv handles everything
```

The `-S` flag (split string) is necessary for the shebang to work with arguments.

## Script Locking

Lock script dependencies for reproducible execution:

```bash
# Create a lock file for the script
uv lock --script example.py

# The lock file is created at example.py.lock
# Subsequent runs use the locked versions

# Export script dependencies
uv export --script example.py --format requirements.txt
```

The lock file (`example.py.lock`) is placed adjacent to the script and should be committed to version control for reproducibility.

## Reproducibility

### Exclude Newer Packages

Restrict resolution to packages published before a specific date:

```python
# /// script
# dependencies = ["requests", "rich"]
# requires-python = ">=3.12"
#
# [tool.uv]
# exclude-newer = "2026-08-17T00:00:00Z"
# ///
```

This ensures the script resolves identically regardless of when it's run.

### Python Version Pinning

```bash
# Run with a specific Python version
uv run --python 3.12.3 example.py

# Or in the metadata
# requires-python = "==3.12.*"
```

## GUI Scripts

On Windows, `.pyw` scripts automatically use `pythonw` (no console window):

```bash
uv run --with PyQt5 example.pyw
```

```python
# example.pyw
# /// script
# dependencies = ["PyQt5"]
# ///

from PyQt5.QtWidgets import QApplication, QLabel
import sys

app = QApplication(sys.argv)
label = QLabel("Hello from uv!")
label.show()
sys.exit(app.exec_())
```

## Common Patterns

### Data Processing Script

```python
#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["polars", "rich"]
# requires-python = ">=3.12"
# ///

import polars as pl
from rich.table import Table
from rich.console import Console

df = pl.read_csv("data.csv")
console = Console()
table = Table(title="Summary")
for col in df.columns:
    table.add_column(col)
for row in df.head(5).rows():
    table.add_row(*[str(v) for v in row])
console.print(table)
```

### Quick API Test

```python
#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["httpx", "rich"]
# requires-python = ">=3.12"
# ///

import httpx
from rich import print as rprint

with httpx.Client() as client:
    resp = client.get("https://api.github.com/repos/astral-sh/uv")
    data = resp.json()
    rprint(f"Stars: {data['stargazers_count']:,}")
    rprint(f"Latest: {data['default_branch']}")
```

## Common Pitfalls

1. **Missing `-S` in shebang** — `#!/usr/bin/env uv run` won't work; use `#!/usr/bin/env -S uv run --script`
2. **Using `--with` when inline metadata exists** — `--with` adds to inline deps, not replaces
3. **Forgetting `--no-project` for standalone scripts in project dirs** — Without it, project deps are included (unless inline metadata is present)
4. **macOS older env** — On older macOS, `/usr/bin/env` may not support `-S`; use full path instead
