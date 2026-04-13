# Dagger Secrets Management

> Source: https://docs.dagger.io/features/secrets | Version: 0.20.x

## Table of Contents
- [Overview](#overview)
- [Creating Secrets](#creating-secrets)
- [Using Secrets in Containers](#using-secrets-in-containers)
- [Secret Providers](#secret-providers)
- [Secrets as Function Arguments](#secrets-as-function-arguments)
- [CLI Secret Passing](#cli-secret-passing)
- [Security Guarantees](#security-guarantees)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## Overview

Dagger provides native support for handling sensitive data — passwords, API keys, SSH keys, and access tokens. Secrets are first-class types that prevent sensitive values from leaking into logs, cache keys, container filesystem layers, or environment output.

## Creating Secrets

### From Environment Variables (in code)

```python
import os
import dagger

@dagger.function
async def deploy(self, source: dagger.Directory) -> str:
    token = dag.set_secret("deploy-token", os.environ["DEPLOY_TOKEN"])
    return await (
        dag.container()
        .from_("alpine")
        .with_secret_variable("DEPLOY_TOKEN", token)
        .with_exec(["sh", "-c", "curl -H \"Authorization: Bearer $DEPLOY_TOKEN\" https://api.example.com/deploy"])
        .stdout()
    )
```

### As Function Arguments

The recommended approach — secrets are passed from outside:

```python
@dagger.function
async def deploy(
    self,
    source: dagger.Directory,
    registry_password: dagger.Secret,
) -> str:
    """Deploy to container registry.

    Args:
        source: Application source
        registry_password: Container registry password
    """
    return await (
        dag.container()
        .from_("python:3.12")
        .with_directory("/app", source)
        .with_secret_variable("REGISTRY_PASS", registry_password)
        .with_exec(["python", "deploy.py"])
        .stdout()
    )
```

## Using Secrets in Containers

### As Environment Variables

```python
ctr = (
    dag.container()
    .from_("alpine")
    .with_secret_variable("API_KEY", api_key_secret)
    .with_secret_variable("DB_PASSWORD", db_pass_secret)
)
```

### As Mounted Files

```python
ctr = (
    dag.container()
    .from_("alpine")
    .with_mounted_secret("/run/secrets/ssh-key", ssh_key_secret)
    .with_mounted_secret("/run/secrets/tls-cert", tls_cert_secret)
)
```

### In Registry Authentication

```python
ctr = (
    dag.container()
    .with_registry_auth("ghcr.io", "username", registry_token)
    .from_("ghcr.io/myorg/private-image:latest")
)
```

## Secret Providers

### Environment Variable Provider (`env://`)

```bash
# CLI usage
dagger call deploy --registry-password=env:REGISTRY_PASSWORD
```

Reads from the host environment variable.

### File Provider (`file://`)

```bash
# CLI usage
dagger call deploy --ssh-key=file:$HOME/.ssh/id_rsa
```

Reads from a file on the host filesystem.

### Command Provider (`cmd://`)

```bash
# CLI usage
dagger call deploy --token=cmd:"aws secretsmanager get-secret-value --secret-id my-token --query SecretString --output text"
```

Executes a command and uses its stdout as the secret value.

### HashiCorp Vault (`vault://`)

```bash
dagger call deploy --api-key=vault://secret/data/myapp#api_key
```

### 1Password (`op://`)

```bash
dagger call deploy --api-key=op://vault-name/item-name/field-name
```

### AWS Secrets Manager (`aws+sm://`)

```bash
dagger call deploy --db-password=aws+sm://my-db-password
dagger call deploy --db-password=aws+sm://my-db-password?region=us-east-1
```

### AWS Parameter Store (`aws+ps://`)

```bash
dagger call deploy --config=aws+ps:///my/app/config
```

## CLI Secret Passing

```bash
# From environment variable
dagger call deploy --registry-password=env:REGISTRY_PASSWORD

# From file
dagger call deploy --ssh-key=file:~/.ssh/id_rsa

# From command output
dagger call deploy --token=cmd:"op read op://dev/api/token"

# From Vault
dagger call deploy --api-key=vault://secret/data/prod#api_key
```

## Security Guarantees

Dagger secrets provide these protections:

1. **Log scrubbing**: Secret values are never printed in logs or terminal output
2. **Cache isolation**: Secrets don't affect cache keys — changing a secret doesn't invalidate build cache
3. **Layer exclusion**: Secrets are not baked into container image layers
4. **Memory only**: Secret values exist only in memory during execution
5. **No filesystem persistence**: `with_secret_variable` doesn't write to `/proc` or environment files

## Common Patterns

### Multi-Registry Authentication

```python
@dagger.function
async def publish_multi(
    self,
    source: dagger.Directory,
    ghcr_token: dagger.Secret,
    dockerhub_token: dagger.Secret,
) -> list[str]:
    """Publish to multiple registries."""
    ctr = await self.build(source)

    refs = []
    for registry, user, token in [
        ("ghcr.io/myorg", "myuser", ghcr_token),
        ("docker.io/myorg", "myuser", dockerhub_token),
    ]:
        ref = await (
            ctr
            .with_registry_auth(registry, user, token)
            .publish(f"{registry}/myapp:latest")
        )
        refs.append(ref)

    return refs
```

### SSH Key for Private Dependencies

```python
@dagger.function
async def build(
    self,
    source: dagger.Directory,
    ssh_key: dagger.Secret,
) -> dagger.Container:
    """Build with private Git dependencies."""
    return (
        dag.container()
        .from_("python:3.12")
        .with_mounted_secret("/root/.ssh/id_rsa", ssh_key)
        .with_exec(["chmod", "600", "/root/.ssh/id_rsa"])
        .with_exec(["ssh-keyscan", "github.com", ">>", "/root/.ssh/known_hosts"])
        .with_directory("/app", source)
        .with_workdir("/app")
        .with_exec(["pip", "install", "-r", "requirements.txt"])
    )
```

### Git Authentication

```python
@dagger.function
async def clone_private(self, token: dagger.Secret) -> dagger.Directory:
    """Clone a private repository."""
    return (
        dag.git(
            "https://github.com/myorg/private-repo.git",
            auth_token=token,
        )
        .branch("main")
        .tree()
    )
```

## Common Pitfalls

1. **Printing secrets**: `with_exec(["echo", "$SECRET"])` won't show the value but avoid patterns that could leak
2. **Baking into images**: Use `with_secret_variable` not `with_env_variable` for sensitive data
3. **Hardcoding in source**: Never put secrets in module source code — pass as arguments
4. **Forgetting provider prefix**: CLI requires `env:`, `file:`, or `cmd:` prefix
5. **Cache confusion**: Secret changes don't invalidate cache — this is by design for security
