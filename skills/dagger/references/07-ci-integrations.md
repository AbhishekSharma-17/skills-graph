# Dagger CI Integrations

> Source: https://docs.dagger.io/getting-started/ci-integrations | Version: 0.20.x

## Table of Contents
- [Overview](#overview)
- [GitHub Actions](#github-actions)
- [GitLab CI](#gitlab-ci)
- [CircleCI](#circleci)
- [Jenkins](#jenkins)
- [Generic CI Runner](#generic-ci-runner)
- [Dagger Cloud Integration](#dagger-cloud-integration)
- [Common Pitfalls](#common-pitfalls)

## Overview

Dagger pipelines are portable — the same code runs on any CI platform. The CI configuration becomes a thin wrapper that:

1. Checks out code
2. Installs the Dagger CLI
3. Calls `dagger call <function>` with arguments
4. Passes secrets from the CI platform

All pipeline logic lives in your Dagger module, not in CI-specific YAML.

## GitHub Actions

### Using the Official Action

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run tests
        uses: dagger/dagger-for-github@v8
        with:
          version: "0.20.3"
          verb: call
          args: test --source=.
          cloud-token: ${{ secrets.DAGGER_CLOUD_TOKEN }}

  build:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4

      - name: Build and publish
        uses: dagger/dagger-for-github@v8
        with:
          version: "0.20.3"
          verb: call
          args: publish --source=. --registry-password=env:REGISTRY_PASSWORD
        env:
          REGISTRY_PASSWORD: ${{ secrets.REGISTRY_PASSWORD }}
```

### Action Parameters

| Parameter | Description |
|-----------|-------------|
| `version` | Dagger CLI version (e.g., "0.20.3" or "latest") |
| `verb` | Dagger command: `call`, `run`, `shell` |
| `module` | Module reference (default: current directory) |
| `args` | Function name and arguments |
| `cloud-token` | Dagger Cloud token for telemetry and caching |
| `engine-stop` | Stop engine after job (default: true) |

### Passing Secrets

```yaml
- name: Deploy
  uses: dagger/dagger-for-github@v8
  with:
    version: "0.20.3"
    verb: call
    args: >
      deploy
      --source=.
      --registry-password=env:REGISTRY_PASSWORD
      --deploy-token=env:DEPLOY_TOKEN
  env:
    REGISTRY_PASSWORD: ${{ secrets.REGISTRY_PASSWORD }}
    DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
```

### Dagger Shell Mode

```yaml
- name: Custom pipeline
  uses: dagger/dagger-for-github@v8
  with:
    version: "0.20.3"
    verb: shell
    args: |
      container | from alpine | with-exec echo "Hello CI" | stdout
```

### Depot Runners (Managed Infrastructure)

```yaml
jobs:
  build:
    runs-on: depot-ubuntu-24.04,dagger=0.20.3
    steps:
      - uses: actions/checkout@v4
      - run: dagger call build --source=.
```

Benefits: Pre-installed CLI, persistent caching, multi-architecture support.

## GitLab CI

### Basic Setup

```yaml
.dagger:
  image: docker:latest
  services:
    - docker:27.2.0-dind
  variables:
    DOCKER_HOST: tcp://docker:2376
    DOCKER_TLS_CERTDIR: /certs
    DOCKER_CERT_PATH: /certs/client
    DOCKER_TLS_VERIFY: "1"
  before_script:
    - apk add curl
    - curl -fsSL https://dl.dagger.io/dagger/install.sh | DAGGER_VERSION=0.20.3 BIN_DIR=/usr/local/bin sh

test:
  extends: .dagger
  script:
    - dagger call test --source=.

build:
  extends: .dagger
  script:
    - dagger call build --source=. publish --registry-password=env:CI_REGISTRY_PASSWORD
  variables:
    CI_REGISTRY_PASSWORD: $CI_REGISTRY_PASSWORD
  only:
    - main
```

### GitLab with Dagger Cloud

```yaml
variables:
  DAGGER_CLOUD_TOKEN: $DAGGER_CLOUD_TOKEN

test:
  extends: .dagger
  script:
    - dagger call test --source=.
```

## CircleCI

```yaml
version: 2.1

jobs:
  test:
    docker:
      - image: cimg/base:current
    steps:
      - checkout
      - setup_remote_docker:
          version: "24.0"
      - run:
          name: Install Dagger
          command: |
            curl -fsSL https://dl.dagger.io/dagger/install.sh | DAGGER_VERSION=0.20.3 BIN_DIR=$HOME/bin sh
            echo 'export PATH=$HOME/bin:$PATH' >> $BASH_ENV
      - run:
          name: Run tests
          command: dagger call test --source=.
          environment:
            DAGGER_CLOUD_TOKEN: << pipeline.parameters.dagger-cloud-token >>

workflows:
  ci:
    jobs:
      - test
```

## Jenkins

### Jenkinsfile (Declarative)

```groovy
pipeline {
    agent any

    environment {
        DAGGER_CLOUD_TOKEN = credentials('dagger-cloud-token')
    }

    stages {
        stage('Install Dagger') {
            steps {
                sh 'curl -fsSL https://dl.dagger.io/dagger/install.sh | DAGGER_VERSION=0.20.3 BIN_DIR=$HOME/bin sh'
            }
        }

        stage('Test') {
            steps {
                sh '$HOME/bin/dagger call test --source=.'
            }
        }

        stage('Build & Publish') {
            when { branch 'main' }
            steps {
                withCredentials([string(credentialsId: 'registry-password', variable: 'REGISTRY_PASSWORD')]) {
                    sh '$HOME/bin/dagger call publish --source=. --registry-password=env:REGISTRY_PASSWORD'
                }
            }
        }
    }
}
```

## Generic CI Runner

For any CI platform that supports Docker:

```bash
#!/bin/bash
set -euo pipefail

# Install Dagger CLI
curl -fsSL https://dl.dagger.io/dagger/install.sh | DAGGER_VERSION=0.20.3 BIN_DIR=/usr/local/bin sh

# Run pipeline
dagger call test --source=.
dagger call build --source=. publish --registry-password=env:REGISTRY_PASSWORD
```

Requirements:
- Container runtime (Docker, Podman)
- curl for CLI installation
- Environment variables for secrets

## Dagger Cloud Integration

Set `DAGGER_CLOUD_TOKEN` in any CI platform for:
- **Distributed caching**: Share cache across CI runners
- **Trace visualization**: Browser-based pipeline debugging
- **Telemetry**: Performance metrics and pipeline analytics
- **Module registry**: Track modules used across your organization

```bash
# Set in CI environment
export DAGGER_CLOUD_TOKEN=your-token-here
```

Every `dagger call` execution generates a trace URL printed in the output.

## Common Pitfalls

1. **Version mismatch**: Pin the same Dagger CLI version across all CI jobs
2. **Missing Docker**: Ensure Docker or a compatible runtime is available
3. **Secret exposure**: Use `env:` prefix for secrets, don't pass values directly in args
4. **DinD permissions**: GitLab CI requires Docker-in-Docker service configuration
5. **Timeout**: Long pipelines may need CI job timeout increases
6. **Cache cold start**: First run on new runners won't have cache — use Dagger Cloud for shared caching
