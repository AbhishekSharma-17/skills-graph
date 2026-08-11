# Settings Management

> Source: [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) · PyPI: `pydantic-settings`

## Table of Contents
- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Environment Variables](#environment-variables)
- [Dotenv Files](#dotenv-files)
- [Nested Settings](#nested-settings)
- [Field Priorities](#field-priorities)
- [Secrets](#secrets)
- [Custom Sources](#custom-sources)
- [Practical Patterns](#practical-patterns)

## Installation

Settings management is a separate package:

```bash
pip install pydantic-settings
```

## Basic Usage

`BaseSettings` works like `BaseModel` but loads values from environment variables:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "MyApp"
    debug: bool = False
    database_url: str
    api_key: str

# Reads from environment variables:
# APP_NAME, DEBUG, DATABASE_URL, API_KEY
settings = Settings()
```

Environment variable names are derived from field names — uppercased by default.

```bash
export DATABASE_URL="postgresql://localhost/mydb"
export API_KEY="sk-abc123"
export DEBUG="true"
```

```python
settings = Settings()
print(settings.database_url)  # postgresql://localhost/mydb
print(settings.debug)         # True (coerced from "true")
```

## Environment Variables

### Custom Prefix

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MYAPP_")

    debug: bool = False
    port: int = 8000

# Reads MYAPP_DEBUG, MYAPP_PORT
```

### Custom Variable Names

```python
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    db_host: str = Field(validation_alias="DB_HOST")
    db_port: int = Field(default=5432, validation_alias="POSTGRES_PORT")
```

### Case Sensitivity

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="app_", case_sensitive=True)
    Name: str  # reads app_Name, not APP_NAME
```

By default, env var lookup is case-insensitive.

### Parsing Complex Types

Environment variables are strings, but Pydantic coerces them:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    port: int              # "8080" -> 8080
    debug: bool            # "true"/"1"/"yes" -> True
    tags: list[str]        # '["a","b"]' -> ["a", "b"] (JSON parsed)
    metadata: dict[str, int]  # '{"x": 1}' -> {"x": 1}
```

For lists and dicts, set the env var to a JSON string:

```bash
export TAGS='["web", "api"]'
export METADATA='{"version": 1, "priority": 5}'
```

## Dotenv Files

Load settings from `.env` files:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    database_url: str
    secret_key: str
    debug: bool = False
```

`.env` file format:

```
DATABASE_URL=postgresql://localhost/mydb
SECRET_KEY=super-secret-key
DEBUG=true
```

### Multiple Env Files

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),  # .env.local overrides .env
    )
    database_url: str
```

### Env File at Runtime

```python
settings = Settings(_env_file=".env.production")
```

### Extra Env Vars

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",  # ignore unknown env vars (default)
    )
```

## Nested Settings

### Using env_nested_delimiter

```python
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

class DatabaseConfig(BaseModel):
    host: str = "localhost"
    port: int = 5432
    name: str = "mydb"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="__")
    database: DatabaseConfig = DatabaseConfig()

# Set via environment:
# DATABASE__HOST=prod-server
# DATABASE__PORT=5433
# DATABASE__NAME=proddb
```

### Nested with Prefix

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_nested_delimiter="__",
    )
    database: DatabaseConfig = DatabaseConfig()

# APP_DATABASE__HOST=prod-server
```

## Field Priorities

Settings values are resolved in this priority order (highest wins):

1. **Init arguments** — `Settings(debug=True)`
2. **Environment variables** — `export DEBUG=true`
3. **Dotenv file** — `.env` file entries
4. **Secrets directory** — files in `secrets_dir`
5. **Default values** — field defaults in the class

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    debug: bool = False  # lowest priority

# Priority: Settings(debug=True) > $DEBUG > .env DEBUG= > False
```

### Customizing Priority

Override `settings_customise_sources` to reorder or add sources:

```python
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
)

class Settings(BaseSettings):
    debug: bool = False

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            dotenv_settings,  # dotenv before env
            env_settings,
            file_secret_settings,
        )
```

## Secrets

Load secrets from files in a directory (useful for Docker Swarm/Kubernetes):

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(secrets_dir="/run/secrets")
    database_password: str
    api_key: str

# Reads from:
# /run/secrets/database_password
# /run/secrets/api_key
```

Each secret is a file whose name matches the field name and whose content is the value.

## Custom Sources

Create custom settings sources for TOML, YAML, databases, etc.:

```python
import json
from pathlib import Path
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource

class JsonSettingsSource(PydanticBaseSettingsSource):
    def get_field_value(self, field, field_name):
        file_path = Path("config.json")
        if file_path.exists():
            data = json.loads(file_path.read_text())
            return data.get(field_name), field_name, False
        return None, field_name, False

    def __call__(self):
        data = {}
        for field_name, field_info in self.settings_cls.model_fields.items():
            value, _, _ = self.get_field_value(field_info, field_name)
            if value is not None:
                data[field_name] = value
        return data

class Settings(BaseSettings):
    debug: bool = False
    port: int = 8000

    @classmethod
    def settings_customise_sources(cls, settings_cls, **kwargs):
        return (
            kwargs["init_settings"],
            kwargs["env_settings"],
            JsonSettingsSource(settings_cls),
        )
```

## Practical Patterns

### Singleton Settings

```python
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    redis_url: str

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

### FastAPI Integration

```python
from functools import lru_cache
from fastapi import Depends, FastAPI
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "My API"
    database_url: str

@lru_cache
def get_settings():
    return Settings()

app = FastAPI()

@app.get("/info")
async def info(settings: Settings = Depends(get_settings)):
    return {"app": settings.app_name}
```

### Environment-Specific Config

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", f".env.{__import__('os').getenv('ENV', 'dev')}"),
    )
    debug: bool = False
    database_url: str
```

## Common Pitfalls

1. **`pydantic-settings` is a separate package** — `pip install pydantic-settings`
2. **Env var names are uppercased** by default — `db_host` reads `DB_HOST`
3. **Complex types need JSON strings** in env vars — `export TAGS='["a","b"]'`
4. **Init kwargs override env vars** — `Settings(debug=True)` wins over `$DEBUG`
5. **Dotenv files don't override env vars** by default — actual env vars take priority
6. **`secrets_dir` reads file content**, not filenames — the file content becomes the value
7. **Cache settings with `@lru_cache`** — re-reading env/files on every access is wasteful
