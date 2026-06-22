# Configuration

> Source: [kubernetes.io/docs/concepts/configuration](https://kubernetes.io/docs/concepts/configuration/)

## Table of Contents

- [ConfigMaps](#configmaps)
- [Secrets](#secrets)
- [Environment Variables](#environment-variables)
- [Resource Management](#resource-management)
- [LimitRanges](#limitranges)
- [ResourceQuotas](#resourcequotas)
- [Common Pitfalls](#common-pitfalls)

---

## ConfigMaps

Store non-confidential configuration data as key-value pairs (max 1 MiB).

### Creating ConfigMaps

```bash
# From literals
kubectl create configmap app-config \
  --from-literal=DB_HOST=postgres \
  --from-literal=DB_PORT=5432

# From file
kubectl create configmap nginx-config \
  --from-file=nginx.conf

# From directory
kubectl create configmap configs \
  --from-file=./config-dir/
```

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  DB_HOST: "postgres.default.svc.cluster.local"
  DB_PORT: "5432"
  LOG_LEVEL: "info"
  app.properties: |
    server.port=8080
    server.timeout=30
    cache.ttl=300
```

### Using as Environment Variables

```yaml
spec:
  containers:
  - name: app
    image: myapp:1.0
    # Individual keys
    env:
    - name: DATABASE_HOST
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: DB_HOST
    # All keys at once
    envFrom:
    - configMapRef:
        name: app-config
        prefix: APP_       # Optional prefix: APP_DB_HOST, APP_DB_PORT
```

### Mounting as Volume

```yaml
spec:
  containers:
  - name: app
    image: myapp:1.0
    volumeMounts:
    - name: config
      mountPath: /etc/config
      readOnly: true
  volumes:
  - name: config
    configMap:
      name: app-config
      items:               # Mount specific keys
      - key: app.properties
        path: app.properties
      defaultMode: 0644
```

### Immutable ConfigMaps

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: static-config
data:
  feature-flags: |
    enable_v2: true
immutable: true
```

### Auto-Update Behavior

| Usage | Auto-Updated |
|-------|-------------|
| Volume mount | Yes (kubelet sync delay) |
| Volume mount with `subPath` | No |
| Environment variable | No (requires pod restart) |
| Immutable ConfigMap | Not applicable |

---

## Secrets

Store sensitive data (passwords, tokens, keys). Base64-encoded by default; enable encryption at rest for security.

### Creating Secrets

```bash
# Generic secret
kubectl create secret generic db-credentials \
  --from-literal=username=admin \
  --from-literal=password='s3cur3P@ss!'

# TLS secret
kubectl create secret tls app-tls \
  --cert=tls.crt --key=tls.key

# Docker registry
kubectl create secret docker-registry regcred \
  --docker-server=ghcr.io \
  --docker-username=user \
  --docker-password=token
```

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
type: Opaque
stringData:                # Plain text (auto-encoded to base64)
  username: admin
  password: "s3cur3P@ss!"
```

### Secret Types

| Type | Usage |
|------|-------|
| `Opaque` | Arbitrary user data (default) |
| `kubernetes.io/tls` | TLS certificate and key |
| `kubernetes.io/dockerconfigjson` | Private registry credentials |
| `kubernetes.io/basic-auth` | Username and password |
| `kubernetes.io/ssh-auth` | SSH private key |
| `kubernetes.io/service-account-token` | Service account token |

### Using as Environment Variables

```yaml
spec:
  containers:
  - name: app
    image: myapp:1.0
    env:
    - name: DB_USERNAME
      valueFrom:
        secretKeyRef:
          name: db-credentials
          key: username
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: db-credentials
          key: password
```

### Mounting as Volume

```yaml
spec:
  containers:
  - name: app
    image: myapp:1.0
    volumeMounts:
    - name: certs
      mountPath: /etc/certs
      readOnly: true
  volumes:
  - name: certs
    secret:
      secretName: app-tls
      defaultMode: 0400    # Read-only for owner
```

### Image Pull Secrets

```yaml
spec:
  imagePullSecrets:
  - name: regcred
  containers:
  - name: app
    image: ghcr.io/myorg/myapp:1.0
```

### Encryption at Rest

```yaml
# /etc/kubernetes/enc/enc.yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
- resources:
  - secrets
  providers:
  - aescbc:
      keys:
      - name: key1
        secret: <base64-encoded-32-byte-key>
  - identity: {}
```

---

## Environment Variables

### Downward API

Expose Pod and container metadata:

```yaml
env:
- name: POD_NAME
  valueFrom:
    fieldRef:
      fieldPath: metadata.name
- name: POD_NAMESPACE
  valueFrom:
    fieldRef:
      fieldPath: metadata.namespace
- name: POD_IP
  valueFrom:
    fieldRef:
      fieldPath: status.podIP
- name: NODE_NAME
  valueFrom:
    fieldRef:
      fieldPath: spec.nodeName
- name: CPU_LIMIT
  valueFrom:
    resourceFieldRef:
      containerName: app
      resource: limits.cpu
- name: MEMORY_REQUEST
  valueFrom:
    resourceFieldRef:
      containerName: app
      resource: requests.memory
```

### Available Downward API Fields

| Field | Source |
|-------|--------|
| `metadata.name` | Pod name |
| `metadata.namespace` | Pod namespace |
| `metadata.uid` | Pod UID |
| `metadata.labels` | Pod labels |
| `metadata.annotations` | Pod annotations |
| `spec.nodeName` | Node name |
| `spec.serviceAccountName` | Service account |
| `status.podIP` | Pod IP address |
| `status.hostIP` | Node IP address |

---

## Resource Management

### Requests and Limits

```yaml
containers:
- name: app
  resources:
    requests:
      cpu: "250m"
      memory: "256Mi"
      ephemeral-storage: "1Gi"
    limits:
      cpu: "1"
      memory: "512Mi"
      ephemeral-storage: "2Gi"
```

### Best Practices

- Always set **requests** — scheduler uses them for placement decisions
- Set **memory limits** equal to requests for Guaranteed QoS
- Be cautious with **CPU limits** — throttling can increase latency
- Monitor actual usage with `kubectl top pods` before setting values

---

## LimitRanges

Set default and max/min resource constraints per namespace.

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: default-limits
  namespace: production
spec:
  limits:
  - default:
      cpu: "500m"
      memory: "256Mi"
    defaultRequest:
      cpu: "100m"
      memory: "128Mi"
    max:
      cpu: "2"
      memory: "2Gi"
    min:
      cpu: "50m"
      memory: "64Mi"
    type: Container
  - max:
      storage: "50Gi"
    type: PersistentVolumeClaim
```

---

## ResourceQuotas

Limit total resource consumption per namespace.

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: staging
spec:
  hard:
    requests.cpu: "10"
    requests.memory: "20Gi"
    limits.cpu: "20"
    limits.memory: "40Gi"
    pods: "50"
    persistentvolumeclaims: "20"
    services: "10"
    services.loadbalancers: "2"
    secrets: "50"
    configmaps: "50"
```

```bash
kubectl get resourcequota -n staging
kubectl describe resourcequota compute-quota -n staging
```

---

## Common Pitfalls

1. **Secrets in environment variables logged** — Env vars may appear in crash dumps or debugging output
2. **ConfigMap used for secrets** — ConfigMaps are not encrypted; always use Secrets for sensitive data
3. **Forgetting `stringData` field** — Using `data` requires manual base64 encoding
4. **No resource requests** — Pods get BestEffort QoS and are first to be evicted under pressure
5. **CPU limits causing throttling** — Consider omitting CPU limits if latency matters
6. **subPath volume mounts not updating** — Changes to ConfigMap/Secret won't propagate with subPath
7. **ResourceQuota without LimitRange** — Pods without resource specs will be rejected when quota is enforced
