# State and Backends

> Source: https://www.pulumi.com/docs/iac/concepts/state-and-backends/ | Version: 3.242.0

## Table of Contents

- [State Overview](#state-overview)
- [Pulumi Cloud Backend](#pulumi-cloud-backend)
- [Self-Managed Backends](#self-managed-backends)
- [State Operations](#state-operations)
- [State Import and Export](#state-import-and-export)
- [State Locking](#state-locking)
- [Drift Detection](#drift-detection)
- [Best Practices](#best-practices)

## State Overview

Pulumi state is a JSON checkpoint file that records every resource managed by a stack — its type, inputs, outputs, dependencies, and provider information. The engine uses state to compute diffs and determine the correct create/update/delete operations during `pulumi up`.

State is stored in a **backend** — either Pulumi Cloud (managed) or a self-managed storage location.

```bash
# Check current backend
pulumi whoami -v

# Show stack state summary
pulumi stack

# Show resources in state
pulumi stack --show-urns
```

## Pulumi Cloud Backend

The default and recommended backend. Provides:

- **Managed state storage** with encryption at rest
- **Concurrent access** with automatic locking
- **Deployment history** and audit logs
- **Stack tags** and organization features
- **RBAC** for team access control
- **Webhooks** and API access

```bash
# Login to Pulumi Cloud (default)
pulumi login

# Login with access token
export PULUMI_ACCESS_TOKEN=pul-abc123...
pulumi login

# Login to self-hosted Pulumi Cloud
pulumi login https://pulumi.mycompany.com
```

## Self-Managed Backends

Store state in your own infrastructure. No Pulumi Cloud account needed.

### Local Filesystem

```bash
pulumi login --local
# Or specify a directory
pulumi login file://~/.pulumi-state

# State files stored at:
# ~/.pulumi-state/.pulumi/stacks/<project>/<stack>.json
```

### AWS S3

```bash
pulumi login s3://my-pulumi-state-bucket

# With specific region and profile
pulumi login 's3://my-bucket?region=us-east-1&profile=prod&awssdk=v2'
```

### Azure Blob Storage

```bash
pulumi login azblob://my-container

# Set storage account via env var
export AZURE_STORAGE_ACCOUNT=mystorageaccount
```

### Google Cloud Storage

```bash
pulumi login gs://my-pulumi-state-bucket
```

### Per-Project Backend (Pulumi.yaml)

```yaml
# Pulumi.yaml
name: my-project
runtime: python
backend:
  url: s3://my-state-bucket/my-project
```

### Self-Managed Backend Comparison

| Feature | Pulumi Cloud | S3/GCS/Azure | Local |
|---------|-------------|--------------|-------|
| State encryption | Yes | Depends on bucket config | No |
| Locking | Yes | Via DynamoDB/none | File lock |
| History | Full UI | Manual | None |
| RBAC | Yes | IAM policies | None |
| Webhooks | Yes | No | No |
| Cost | Free tier + paid | Storage costs | Free |

## State Operations

### Refresh

Sync state with actual cloud resources (detect drift):

```bash
pulumi refresh
pulumi refresh --yes           # Skip confirmation
pulumi refresh --skip-preview  # Skip preview
```

### State Delete

Remove a resource from state without deleting the cloud resource:

```bash
# Remove resource from state (keeps cloud resource)
pulumi state delete <urn>

# Example
pulumi state delete 'urn:pulumi:prod::myapp::aws:s3/bucketV2:BucketV2::my-bucket'
```

### State Unprotect

Remove protection flag:

```bash
pulumi state unprotect <urn>
# Then you can destroy the resource
```

### State Rename

```bash
pulumi state rename <old-urn> <new-name>
```

## State Import and Export

### Export State

```bash
# Export current state as JSON
pulumi stack export > state.json

# Export specific stack
pulumi stack export --stack prod > prod-state.json
```

### Import State

```bash
# Import state from JSON
pulumi stack import --file state.json
```

### State Migration Between Backends

```bash
# Export from source backend
pulumi login --local
pulumi stack select prod
pulumi stack export --file state-backup.json

# Import to target backend
pulumi login s3://new-state-bucket
pulumi stack init prod
pulumi stack import --file state-backup.json
```

### Import from Terraform State

```bash
# Convert Terraform state to Pulumi state
pulumi import --from terraform ./terraform.tfstate

# If conversion fails, use generated import file
pulumi import --file generated-imports.json
```

## State Locking

Prevents concurrent modifications to the same stack.

### Pulumi Cloud

Automatic locking — no configuration needed. If a stack is locked (update in progress), other operations wait or fail with a clear message.

### Self-Managed Backends

**S3 with DynamoDB** — Pulumi does not natively use DynamoDB for locking (unlike Terraform). Concurrent access protection depends on S3's consistency model.

**Best practice**: use Pulumi Cloud or implement CI/CD-level locking (only one pipeline runs per stack at a time).

### Cancel a Stuck Update

```bash
# Cancel an in-progress update
pulumi cancel

# Force unlock if state is stuck (use with caution)
pulumi stack export > backup.json
# Manually remove the lock from the backend
pulumi stack import --file backup.json
```

## Drift Detection

Detect when cloud resources have been modified outside of Pulumi:

```bash
# Refresh state from cloud reality
pulumi refresh

# Preview shows drift as updates
pulumi preview
```

Automated drift detection:

```python
# In CI/CD, run refresh and check for drift
# pulumi refresh --expect-no-changes
# Returns non-zero exit code if drift detected
```

## Best Practices

1. **Use Pulumi Cloud for teams** — built-in locking, history, RBAC, and secrets management
2. **Never edit state manually** — always use `pulumi state` commands
3. **Refresh before major operations** — catch drift early with `pulumi refresh`
4. **Back up state** — export state before destructive operations
5. **Separate state per environment** — isolate blast radius between dev/staging/prod
6. **Enable encryption** — use KMS-backed encryption for self-managed backends
7. **Version control config** — commit `Pulumi.<stack>.yaml` files (secrets are encrypted)
8. **Don't version control state** — state files contain sensitive data and should be in a secure backend
