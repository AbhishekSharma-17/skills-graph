# Helm

> Source: [helm.sh/docs](https://helm.sh/docs/)

## Table of Contents

- [What Is Helm](#what-is-helm)
- [Core Concepts](#core-concepts)
- [Installing Charts](#installing-charts)
- [Managing Releases](#managing-releases)
- [Creating Charts](#creating-charts)
- [Chart Structure](#chart-structure)
- [Values and Templates](#values-and-templates)
- [Hooks](#hooks)
- [Chart Repositories](#chart-repositories)
- [Common Pitfalls](#common-pitfalls)

---

## What Is Helm

Helm is the package manager for Kubernetes. It packages Kubernetes manifests into reusable units called **charts** and manages their lifecycle as **releases**.

```bash
# Install Helm
brew install helm                  # macOS
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash  # Linux
```

---

## Core Concepts

| Concept | Description |
|---------|-------------|
| **Chart** | Package of pre-configured Kubernetes resources |
| **Release** | Running instance of a chart in a cluster |
| **Repository** | Collection of charts (HTTP server or OCI registry) |
| **Values** | Configuration parameters passed to a chart |

---

## Installing Charts

### From OCI Registry

```bash
# Install directly from OCI registry
helm install my-nginx oci://registry-1.docker.io/bitnamicharts/nginx

# With custom values
helm install my-app oci://ghcr.io/myorg/charts/myapp \
  --version 2.1.0 \
  --values custom-values.yaml \
  --namespace production \
  --create-namespace
```

### From Repository

```bash
# Add repository
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Search for charts
helm search repo bitnami/nginx
helm search hub wordpress     # Search Artifact Hub

# Install
helm install my-release bitnami/nginx \
  --set service.type=LoadBalancer \
  --set replicaCount=3
```

### Common Install Options

```bash
helm install my-release chart-name \
  --namespace production \
  --create-namespace \
  --values values-prod.yaml \
  --set image.tag=2.0.0 \
  --set-string annotations."key"="value" \
  --wait \                     # Wait for all resources to be ready
  --timeout 10m \
  --dry-run \                  # Render templates without installing
  --debug                      # Show debug output
```

---

## Managing Releases

```bash
# List releases
helm list
helm list --all-namespaces
helm list --filter 'web-.*'

# Check release status
helm status my-release

# Get release values
helm get values my-release
helm get values my-release --all     # Including defaults

# Get rendered manifests
helm get manifest my-release

# Upgrade release
helm upgrade my-release bitnami/nginx \
  --set replicaCount=5 \
  --values new-values.yaml

# Upgrade or install if not exists
helm upgrade --install my-release bitnami/nginx

# Rollback
helm rollback my-release 1          # Rollback to revision 1
helm rollback my-release            # Rollback to previous

# View history
helm history my-release

# Uninstall
helm uninstall my-release
helm uninstall my-release --keep-history    # Preserve history for rollback
```

---

## Creating Charts

```bash
# Scaffold a new chart
helm create myapp

# Lint chart
helm lint myapp/

# Template render (debug)
helm template myapp myapp/ --values values.yaml

# Package chart
helm package myapp/

# Install local chart
helm install my-release ./myapp
```

---

## Chart Structure

```
myapp/
├── Chart.yaml          # Chart metadata
├── Chart.lock          # Dependency lock file
├── values.yaml         # Default configuration values
├── values.schema.json  # JSON Schema for values validation
├── .helmignore         # Files to exclude from packaging
├── templates/          # Kubernetes manifest templates
│   ├── _helpers.tpl    # Template helpers and partials
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── hpa.yaml
│   ├── serviceaccount.yaml
│   ├── configmap.yaml
│   ├── NOTES.txt       # Post-install instructions
│   └── tests/
│       └── test-connection.yaml
├── charts/             # Dependency charts
└── crds/               # Custom Resource Definitions
```

### Chart.yaml

```yaml
apiVersion: v2
name: myapp
description: A Helm chart for MyApp
type: application              # application or library
version: 1.2.0                 # Chart version (SemVer)
appVersion: "2.0.0"            # Application version
keywords:
- web
- api
home: https://github.com/myorg/myapp
maintainers:
- name: Team
  email: team@example.com
dependencies:
- name: postgresql
  version: "~15.0"
  repository: oci://registry-1.docker.io/bitnamicharts
  condition: postgresql.enabled
- name: redis
  version: "~19.0"
  repository: oci://registry-1.docker.io/bitnamicharts
  condition: redis.enabled
```

---

## Values and Templates

### values.yaml

```yaml
replicaCount: 3

image:
  repository: myapp
  tag: "2.0.0"
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 80

ingress:
  enabled: true
  className: nginx
  hosts:
  - host: app.example.com
    paths:
    - path: /
      pathType: Prefix
  tls:
  - secretName: app-tls
    hosts:
    - app.example.com

resources:
  requests:
    cpu: 250m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
  targetCPUUtilizationPercentage: 60

postgresql:
  enabled: true
  auth:
    database: myapp
```

### Template Syntax

```yaml
# templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "myapp.fullname" . }}
  labels:
    {{- include "myapp.labels" . | nindent 4 }}
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
  selector:
    matchLabels:
      {{- include "myapp.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "myapp.selectorLabels" . | nindent 8 }}
    spec:
      containers:
      - name: {{ .Chart.Name }}
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
        imagePullPolicy: {{ .Values.image.pullPolicy }}
        ports:
        - containerPort: {{ .Values.service.port }}
        {{- with .Values.resources }}
        resources:
          {{- toYaml . | nindent 10 }}
        {{- end }}
```

### Template Functions

| Function | Description | Example |
|----------|-------------|---------|
| `default` | Default value | `{{ .Values.port \| default 8080 }}` |
| `quote` | Wrap in quotes | `{{ .Values.name \| quote }}` |
| `upper` / `lower` | Case conversion | `{{ .Values.env \| upper }}` |
| `b64enc` | Base64 encode | `{{ .Values.secret \| b64enc }}` |
| `toYaml` | Convert to YAML | `{{ toYaml .Values.labels }}` |
| `nindent` | Indent with newline | `{{ toYaml .Values.x \| nindent 4 }}` |
| `include` | Include template | `{{ include "myapp.name" . }}` |
| `required` | Fail if missing | `{{ required "name required" .Values.name }}` |
| `tpl` | Render string as template | `{{ tpl .Values.template . }}` |

### _helpers.tpl

```yaml
{{- define "myapp.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "myapp.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name (include "myapp.name" .) | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{- define "myapp.labels" -}}
helm.sh/chart: {{ include "myapp.chart" . }}
{{ include "myapp.selectorLabels" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "myapp.selectorLabels" -}}
app.kubernetes.io/name: {{ include "myapp.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
```

---

## Hooks

Execute resources at specific lifecycle points:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: {{ include "myapp.fullname" . }}-migrate
  annotations:
    "helm.sh/hook": pre-upgrade,pre-install
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  template:
    spec:
      containers:
      - name: migrate
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
        command: ["python", "manage.py", "migrate"]
      restartPolicy: Never
```

### Hook Types

| Hook | When |
|------|------|
| `pre-install` | Before any resources are installed |
| `post-install` | After all resources are installed |
| `pre-upgrade` | Before upgrade begins |
| `post-upgrade` | After upgrade completes |
| `pre-delete` | Before deletion begins |
| `post-delete` | After deletion completes |
| `pre-rollback` | Before rollback begins |
| `post-rollback` | After rollback completes |

---

## Chart Repositories

### OCI Registries (Preferred)

```bash
# Login to registry
helm registry login ghcr.io -u username

# Push chart
helm push myapp-1.2.0.tgz oci://ghcr.io/myorg/charts

# Pull chart
helm pull oci://ghcr.io/myorg/charts/myapp --version 1.2.0
```

### Managing Dependencies

```bash
# Download dependencies
helm dependency update myapp/

# List dependencies
helm dependency list myapp/
```

---

## Common Pitfalls

1. **Not using `--dry-run`** — Always preview changes before applying
2. **Hardcoded values in templates** — Use `values.yaml` for all configurable parameters
3. **Missing `required` validation** — Critical values should fail early with descriptive errors
4. **Not setting resource limits** — Charts should include default resource requests/limits
5. **Helm release name conflicts** — Release names must be unique within a namespace
6. **Forgetting `helm dependency update`** — Subchart changes require re-downloading dependencies
7. **Using `helm install` instead of `upgrade --install`** — The latter is idempotent
