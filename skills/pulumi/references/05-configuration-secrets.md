# Configuration and Secrets

> Source: https://www.pulumi.com/docs/iac/concepts/secrets/ | Version: 3.242.0

## Table of Contents

- [Configuration Basics](#configuration-basics)
- [Reading Configuration in Code](#reading-configuration-in-code)
- [Secrets Management](#secrets-management)
- [Encryption Providers](#encryption-providers)
- [Pulumi ESC](#pulumi-esc)
- [Environment Variables](#environment-variables)
- [Structured Configuration](#structured-configuration)
- [Best Practices](#best-practices)

## Configuration Basics

Pulumi configuration is stack-specific. Each stack has its own `Pulumi.<stack>.yaml` file containing key-value pairs.

```bash
# Set config values
pulumi config set aws:region us-east-1
pulumi config set instanceType t3.micro
pulumi config set replicas 3

# List all config
pulumi config

# Get a specific value
pulumi config get instanceType

# Remove a value
pulumi config rm replicas
```

### Namespaced Keys

Config keys are namespaced by project name:

```bash
# These are equivalent for project "my-infra"
pulumi config set instanceType t3.micro
pulumi config set my-infra:instanceType t3.micro

# Provider config uses provider namespace
pulumi config set aws:region us-east-1
pulumi config set gcp:project my-gcp-project
```

## Reading Configuration in Code

### Python

```python
import pulumi

config = pulumi.Config()

# Required values (raises ConfigMissingError if absent)
instance_type = config.require("instanceType")
db_name = config.require("dbName")

# Optional values (returns None if absent)
region = config.get("region")
replicas = config.get_int("replicas") or 3
debug = config.get_bool("debug") or False

# Secrets (returns Output[str] — automatically decrypted)
db_password = config.require_secret("dbPassword")
api_key = config.get_secret("apiKey")

# Provider-namespaced config
aws_config = pulumi.Config("aws")
region = aws_config.require("region")
```

### TypeScript

```typescript
import * as pulumi from "@pulumi/pulumi";

const config = new pulumi.Config();

const instanceType = config.require("instanceType");
const replicas = config.getNumber("replicas") ?? 3;
const dbPassword = config.requireSecret("dbPassword");

// Provider config
const awsConfig = new pulumi.Config("aws");
const region = awsConfig.require("region");
```

## Secrets Management

Secrets are encrypted values stored in stack config files.

```bash
# Set a secret (encrypted in Pulumi.<stack>.yaml)
pulumi config set --secret dbPassword "s3cr3t!"
pulumi config set --secret apiKey "sk-live-abc123"

# Read a secret (decrypted for display)
pulumi config get dbPassword
```

### How Secrets Work

1. Value is encrypted using the stack's encryption provider
2. Ciphertext is stored in `Pulumi.<stack>.yaml`
3. At runtime, Pulumi decrypts and injects the value
4. Outputs derived from secrets are automatically marked as secrets

```yaml
# Pulumi.prod.yaml
config:
  aws:region: us-east-1
  my-infra:instanceType: t3.micro
  my-infra:dbPassword:
    secure: AAABADfKzMp0...  # Encrypted ciphertext
```

### Secret Outputs

```python
# Values derived from secrets stay secret
db_password = config.require_secret("dbPassword")
connection_string = pulumi.Output.concat(
    "postgresql://admin:", db_password, "@db.example.com/mydb"
)
# connection_string is automatically a secret Output

# Manually mark a value as secret
token = pulumi.Output.secret("my-plain-token")

# Unsecret (remove secret marking — use with caution)
plain = pulumi.Output.unsecret(some_secret_output)
```

## Encryption Providers

### Default (Passphrase)

Uses a passphrase to derive an encryption key. Set via environment variable or prompted:

```bash
export PULUMI_CONFIG_PASSPHRASE="my-passphrase"
pulumi stack init dev --secrets-provider passphrase
```

### Pulumi Cloud (Default for Managed State)

Encryption keys managed by Pulumi Cloud. No setup required when using Pulumi Cloud as backend.

### AWS KMS

```bash
pulumi stack init prod --secrets-provider "awskms://alias/pulumi-secrets?region=us-east-1"
# Or by key ID:
pulumi stack init prod --secrets-provider "awskms://1234abcd-12ab-34cd-56ef-1234567890ab?region=us-east-1"
```

### Azure Key Vault

```bash
pulumi stack init prod --secrets-provider "azurekeyvault://my-vault.vault.azure.net/keys/pulumi-key"
```

### GCP KMS

```bash
pulumi stack init prod --secrets-provider "gcpkms://projects/my-project/locations/global/keyRings/my-ring/cryptoKeys/pulumi-key"
```

### HashiCorp Vault

```bash
pulumi stack init prod --secrets-provider "hashivault://transit/keys/pulumi-key"
```

### Changing Secrets Provider

```bash
# Migrate existing stack to a new secrets provider
pulumi stack change-secrets-provider "awskms://alias/my-key?region=us-east-1"
```

## Pulumi ESC

Pulumi ESC (Environments, Secrets, and Configuration) provides centralized secrets management across stacks and applications.

### Core Concepts

- **Environments** — named collections of configuration and secrets
- **Composition** — environments can import other environments
- **Dynamic credentials** — OIDC integration for short-lived cloud credentials
- **Versioning** — every environment change is versioned and auditable

### Creating Environments

```bash
# Create an environment
pulumi env init myorg/aws-dev

# Edit environment definition (opens editor)
pulumi env edit myorg/aws-dev
```

```yaml
# Environment definition
imports:
  - aws-base              # Import shared base config

values:
  aws:
    login:
      fn::open::aws-login:
        oidc:
          roleArn: arn:aws:iam::123456789:role/pulumi-oidc
          sessionName: pulumi-esc
    region: us-east-1

  app:
    database:
      host: db.example.com
      port: 5432
      password:
        fn::secret: "encrypted-password"

  environmentVariables:
    AWS_REGION: ${aws.region}
    DB_HOST: ${app.database.host}
```

### Using ESC with Stacks

```yaml
# Pulumi.prod.yaml
environment:
  - aws-prod              # Pull config from ESC environment
  - monitoring-base
```

### Using ESC from CLI

```bash
# Run any command with ESC environment injected
pulumi env run myorg/aws-dev -- aws s3 ls
pulumi env run myorg/aws-dev -- terraform plan

# Open environment values
pulumi env open myorg/aws-dev
```

## Environment Variables

Pulumi reads several environment variables:

```bash
# Authentication
PULUMI_ACCESS_TOKEN=pul-abc123...  # API token for Pulumi Cloud

# Backend
PULUMI_BACKEND_URL=s3://my-bucket  # Override default backend

# Secrets
PULUMI_CONFIG_PASSPHRASE=secret    # Passphrase for local encryption

# Behavior
PULUMI_SKIP_UPDATE_CHECK=true      # Disable CLI update check
PULUMI_SKIP_CONFIRMATIONS=true     # Auto-approve (like --yes)
```

## Structured Configuration

Store complex values (objects, lists) in config:

```bash
# Set a JSON object
pulumi config set --path 'database.host' db.example.com
pulumi config set --path 'database.port' 5432
pulumi config set --path --secret 'database.password' 's3cr3t'

# Set a list
pulumi config set --path 'allowedCidrs[0]' 10.0.0.0/8
pulumi config set --path 'allowedCidrs[1]' 172.16.0.0/12
```

```yaml
# Result in Pulumi.dev.yaml
config:
  my-infra:database:
    host: db.example.com
    port: "5432"
    password:
      secure: AAABADfKz...
  my-infra:allowedCidrs:
    - 10.0.0.0/8
    - 172.16.0.0/12
```

```python
# Read structured config in code
config = pulumi.Config()
db = config.require_object("database")
# db = {"host": "db.example.com", "port": "5432", "password": "s3cr3t"}

cidrs = config.require_object("allowedCidrs")
# cidrs = ["10.0.0.0/8", "172.16.0.0/12"]
```

## Best Practices

1. **Never hardcode secrets** — always use `config set --secret` or Pulumi ESC
2. **Use cloud KMS for production** — avoid passphrase encryption in production stacks
3. **Commit config files** — `Pulumi.<stack>.yaml` files with encrypted secrets are safe for version control
4. **Namespace config properly** — use `<project>:key` for project-specific values, `<provider>:key` for provider settings
5. **Use ESC for shared config** — centralize secrets used across multiple stacks
6. **Rotate secrets regularly** — update secrets and re-deploy stacks
7. **Separate environments** — never share secret values between dev and prod stacks
