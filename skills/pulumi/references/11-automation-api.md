# Automation API

> Source: https://www.pulumi.com/docs/iac/packages-and-automation/automation-api/ | Version: 3.242.0

## Table of Contents

- [Overview](#overview)
- [Python Automation API](#python-automation-api)
- [Inline Programs](#inline-programs)
- [Local Programs](#local-programs)
- [Stack Operations](#stack-operations)
- [Configuration and Secrets](#configuration-and-secrets)
- [Event Handling](#event-handling)
- [Use Cases](#use-cases)
- [Best Practices](#best-practices)

## Overview

The Automation API lets you use Pulumi as a library — no CLI required. Embed infrastructure provisioning inside web servers, CLIs, CI/CD pipelines, or any application. It provides programmatic access to:

- Stack lifecycle: create, select, update, preview, refresh, destroy
- Configuration management
- Stack outputs
- Event streams

```bash
# Python
pip install pulumi

# TypeScript
npm install @pulumi/pulumi
```

## Python Automation API

```python
import pulumi.automation as auto
```

### Core Concepts

- **Workspace** — manages project settings, credentials, and plugins
- **Stack** — an instance of a Pulumi program with its own state
- **Program** — the function that defines infrastructure (inline) or a directory path (local)

## Inline Programs

Define infrastructure as a Python function — no separate project directory needed:

```python
import pulumi
import pulumi.automation as auto
import pulumi_aws as aws


def pulumi_program():
    """Define infrastructure inline."""
    bucket = aws.s3.BucketV2("auto-bucket",
        tags={"CreatedBy": "automation-api"},
    )
    pulumi.export("bucket_name", bucket.id)
    pulumi.export("bucket_arn", bucket.arn)


# Create or select a stack
stack = auto.create_or_select_stack(
    stack_name="dev",
    project_name="my-automation",
    program=pulumi_program,
)

# Configure the stack
stack.set_config("aws:region", auto.ConfigValue(value="us-east-1"))

# Preview changes
preview_result = stack.preview(on_output=print)
print(f"Changes: {preview_result.change_summary}")

# Deploy
up_result = stack.up(on_output=print)
print(f"Bucket: {up_result.outputs['bucket_name'].value}")

# Destroy when done
stack.destroy(on_output=print)
stack.workspace.remove_stack("dev")
```

### Parameterized Inline Programs

```python
def create_infrastructure(env: str, replicas: int):
    """Factory function that returns a Pulumi program."""

    def program():
        for i in range(replicas):
            aws.ec2.Instance(f"web-{env}-{i}",
                instance_type="t3.micro",
                ami="ami-12345678",
                tags={"Environment": env, "Index": str(i)},
            )

    return program


# Create stacks for different environments
for env, replicas in [("dev", 1), ("staging", 2), ("prod", 3)]:
    stack = auto.create_or_select_stack(
        stack_name=env,
        project_name="web-fleet",
        program=create_infrastructure(env, replicas),
    )
    stack.set_config("aws:region", auto.ConfigValue("us-east-1"))
    stack.up(on_output=print)
```

## Local Programs

Point to an existing Pulumi project directory:

```python
import pulumi.automation as auto

# Reference an existing project on disk
stack = auto.create_or_select_stack(
    stack_name="prod",
    work_dir="/path/to/my-infrastructure",
)

# Set config
stack.set_config("aws:region", auto.ConfigValue("us-east-1"))

# Deploy
result = stack.up(on_output=print)
```

### Select Existing Stack

```python
# Select an existing stack (errors if not found)
stack = auto.select_stack(
    stack_name="prod",
    work_dir="/path/to/project",
)

# Get current outputs
outputs = stack.outputs()
print(outputs["bucket_name"].value)
```

## Stack Operations

### Preview

```python
preview = stack.preview(on_output=print)

# Access preview results
print(f"Creates: {preview.change_summary.get('create', 0)}")
print(f"Updates: {preview.change_summary.get('update', 0)}")
print(f"Deletes: {preview.change_summary.get('delete', 0)}")
```

### Up (Deploy)

```python
result = stack.up(
    on_output=print,            # Stream output
    parallel=10,                # Parallelism
    # target=["urn:..."],       # Target specific resources
    # target_dependents=True,   # Include dependents
)

print(f"Summary: {result.summary}")
print(f"Outputs: {result.outputs}")

# Access typed outputs
bucket = result.outputs["bucket_name"]
print(f"Value: {bucket.value}")
print(f"Secret: {bucket.secret}")  # True if output is a secret
```

### Refresh

```python
refresh_result = stack.refresh(on_output=print)
```

### Destroy

```python
destroy_result = stack.destroy(on_output=print)
```

### Stack Info

```python
# Get stack outputs
outputs = stack.outputs()

# Get stack history
history = stack.history()
for entry in history:
    print(f"{entry.start_time}: {entry.result}")

# Export/import state
state = stack.export_stack()
stack.import_stack(state)
```

## Configuration and Secrets

```python
# Set plain config
stack.set_config("key", auto.ConfigValue(value="plain-value"))

# Set secret config
stack.set_config("dbPassword", auto.ConfigValue(
    value="s3cr3t!",
    secret=True,
))

# Set multiple values
stack.set_all_config({
    "aws:region": auto.ConfigValue("us-east-1"),
    "app:replicas": auto.ConfigValue("3"),
    "app:apiKey": auto.ConfigValue("sk-123", secret=True),
})

# Get config
val = stack.get_config("key")
print(val.value, val.secret)

# Get all config
all_config = stack.get_all_config()

# Remove config
stack.remove_config("key")
```

## Event Handling

Stream deployment events for custom UIs or logging:

```python
# Simple output streaming
result = stack.up(on_output=lambda msg: print(f"[pulumi] {msg}"))

# Capture events programmatically
events = []

def on_event(event):
    events.append(event)
    if hasattr(event, "resource_pre_event"):
        print(f"Operating on: {event.resource_pre_event.metadata.type}")

result = stack.up(on_event=on_event)
```

## Use Cases

### Self-Service Infrastructure Portal

```python
from fastapi import FastAPI
import pulumi.automation as auto

app = FastAPI()

@app.post("/environments")
async def create_environment(name: str, tier: str):
    """API endpoint to provision a new environment."""

    def program():
        import pulumi_aws as aws
        instance_type = "t3.micro" if tier == "dev" else "t3.large"
        server = aws.ec2.Instance(f"{name}-server",
            instance_type=instance_type,
            ami="ami-12345678",
            tags={"Environment": name, "Tier": tier},
        )
        pulumi.export("server_ip", server.public_ip)

    stack = auto.create_or_select_stack(
        stack_name=name,
        project_name="self-service",
        program=program,
    )
    stack.set_config("aws:region", auto.ConfigValue("us-east-1"))
    result = stack.up()

    return {
        "environment": name,
        "server_ip": result.outputs["server_ip"].value,
    }

@app.delete("/environments/{name}")
async def destroy_environment(name: str):
    stack = auto.select_stack(
        stack_name=name,
        project_name="self-service",
        program=lambda: None,
    )
    stack.destroy()
    stack.workspace.remove_stack(name)
    return {"status": "destroyed"}
```

### Database Migration Runner

```python
def ensure_database():
    """Ensure database exists before running migrations."""
    def program():
        db = aws.rds.Instance("app-db",
            engine="postgres",
            instance_class="db.t4g.micro",
            allocated_storage=20,
            opts=pulumi.ResourceOptions(protect=True),
        )
        pulumi.export("endpoint", db.endpoint)

    stack = auto.create_or_select_stack(
        stack_name="prod",
        project_name="database",
        program=program,
    )
    stack.set_config("aws:region", auto.ConfigValue("us-east-1"))
    result = stack.up()
    return result.outputs["endpoint"].value
```

## Best Practices

1. **Handle errors** — wrap stack operations in try/except for `auto.CommandError`
2. **Use `create_or_select_stack`** — idempotent, works whether stack exists or not
3. **Stream output** — always pass `on_output` for visibility into long operations
4. **Clean up** — destroy and remove stacks in test/ephemeral scenarios
5. **Separate concerns** — inline programs for simple cases, local programs for complex projects
6. **Manage concurrency** — don't run multiple operations on the same stack simultaneously
7. **Set timeouts** — long-running `up()` calls should have application-level timeouts
