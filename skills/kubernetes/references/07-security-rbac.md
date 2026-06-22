# Security & RBAC

> Source: [kubernetes.io/docs/reference/access-authn-authz/rbac](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)

## Table of Contents

- [RBAC Overview](#rbac-overview)
- [Roles and ClusterRoles](#roles-and-clusterroles)
- [RoleBindings and ClusterRoleBindings](#rolebindings-and-clusterrolebindings)
- [ServiceAccounts](#serviceaccounts)
- [Security Contexts](#security-contexts)
- [Pod Security Standards](#pod-security-standards)
- [Network Security](#network-security)
- [Best Practices](#best-practices)

---

## RBAC Overview

Role-Based Access Control (RBAC) regulates access to Kubernetes resources based on roles assigned to users, groups, or service accounts.

```
Subject ──binds to──▸ Role ──grants──▸ Permissions on Resources
```

### API Groups

| Group | Resources |
|-------|-----------|
| `""` (core) | pods, services, configmaps, secrets, nodes |
| `apps` | deployments, statefulsets, daemonsets, replicasets |
| `batch` | jobs, cronjobs |
| `networking.k8s.io` | ingresses, networkpolicies |
| `rbac.authorization.k8s.io` | roles, clusterroles, rolebindings |

### Verbs

| Verb | HTTP Method | Description |
|------|------------|-------------|
| `get` | GET | Read a specific resource |
| `list` | GET | List resources |
| `watch` | GET (streaming) | Watch for changes |
| `create` | POST | Create a resource |
| `update` | PUT | Replace a resource |
| `patch` | PATCH | Partially modify a resource |
| `delete` | DELETE | Delete a resource |
| `deletecollection` | DELETE | Delete multiple resources |

---

## Roles and ClusterRoles

### Role (Namespace-Scoped)

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
  namespace: production
rules:
- apiGroups: [""]
  resources: ["pods", "pods/log"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["configmaps"]
  resourceNames: ["app-config"]     # Restrict to specific resources
  verbs: ["get"]
```

### ClusterRole (Cluster-Wide)

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: namespace-admin
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "secrets"]
  verbs: ["get", "list", "watch", "create", "update", "delete"]
- apiGroups: ["apps"]
  resources: ["deployments", "statefulsets"]
  verbs: ["get", "list", "watch", "create", "update", "delete"]
- apiGroups: [""]
  resources: ["pods/exec", "pods/portforward"]
  verbs: ["create"]
```

### Aggregated ClusterRoles

Combine multiple ClusterRoles:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: monitoring-view
  labels:
    rbac.authorization.k8s.io/aggregate-to-view: "true"
rules:
- apiGroups: ["monitoring.coreos.com"]
  resources: ["servicemonitors", "prometheusrules"]
  verbs: ["get", "list", "watch"]
```

---

## RoleBindings and ClusterRoleBindings

### RoleBinding

Grants a Role's permissions within a specific namespace:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: dev-pod-reader
  namespace: production
subjects:
- kind: User
  name: jane
  apiGroup: rbac.authorization.k8s.io
- kind: Group
  name: developers
  apiGroup: rbac.authorization.k8s.io
- kind: ServiceAccount
  name: ci-bot
  namespace: ci
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

### ClusterRoleBinding

Grants permissions across all namespaces:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: readonly-binding
subjects:
- kind: Group
  name: viewers
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: view               # Built-in read-only ClusterRole
  apiGroup: rbac.authorization.k8s.io
```

### Built-in ClusterRoles

| Role | Description |
|------|-------------|
| `cluster-admin` | Full access to everything |
| `admin` | Full access within a namespace |
| `edit` | Read/write most resources in a namespace |
| `view` | Read-only access in a namespace |

### Checking Permissions

```bash
# Can I do X?
kubectl auth can-i create deployments --namespace production
kubectl auth can-i delete pods --as jane
kubectl auth can-i list secrets --as system:serviceaccount:default:my-sa

# Who can do X?
kubectl auth who-can create pods -n production
```

---

## ServiceAccounts

Identities for Pods and processes running in the cluster.

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-sa
  namespace: production
automountServiceAccountToken: false
```

### Assigning to a Pod

```yaml
spec:
  serviceAccountName: app-sa
  automountServiceAccountToken: true    # Override SA default
  containers:
  - name: app
    image: myapp:1.0
```

### Token Projection

```yaml
spec:
  containers:
  - name: app
    image: myapp:1.0
    volumeMounts:
    - name: token
      mountPath: /var/run/secrets/tokens
  volumes:
  - name: token
    projected:
      sources:
      - serviceAccountToken:
          path: token
          expirationSeconds: 3600
          audience: api.example.com
```

---

## Security Contexts

Control privilege and access at Pod and container level.

### Pod-Level Security Context

```yaml
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 3000
    fsGroup: 2000
    seccompProfile:
      type: RuntimeDefault
```

### Container-Level Security Context

```yaml
spec:
  containers:
  - name: app
    image: myapp:1.0
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop: ["ALL"]
        add: ["NET_BIND_SERVICE"]
      privileged: false
```

### Hardened Pod Example

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 65534
    fsGroup: 65534
    seccompProfile:
      type: RuntimeDefault
  automountServiceAccountToken: false
  containers:
  - name: app
    image: myapp:1.0
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop: ["ALL"]
    resources:
      requests:
        cpu: "100m"
        memory: "128Mi"
      limits:
        cpu: "500m"
        memory: "256Mi"
    volumeMounts:
    - name: tmp
      mountPath: /tmp
  volumes:
  - name: tmp
    emptyDir: {}
```

---

## Pod Security Standards

Three levels of security enforced at namespace level:

| Level | Description |
|-------|-------------|
| `privileged` | Unrestricted (no enforcement) |
| `baseline` | Prevents known privilege escalations |
| `restricted` | Hardened security best practices |

### Enforcement via Labels

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: latest
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

### Enforcement Modes

| Mode | Behavior |
|------|----------|
| `enforce` | Reject Pods that violate the policy |
| `audit` | Log violations in audit log |
| `warn` | Show warnings to user but allow Pods |

---

## Network Security

### Restrict API Server Access

```yaml
# In kube-apiserver configuration
--anonymous-auth=false
--authorization-mode=Node,RBAC
--enable-admission-plugins=NodeRestriction
```

### Encrypt Secrets at Rest

```yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
- resources:
  - secrets
  providers:
  - aescbc:
      keys:
      - name: key1
        secret: <32-byte-base64-key>
  - identity: {}
```

---

## Best Practices

1. **Least privilege** — Grant minimum permissions needed; prefer Role over ClusterRole
2. **No wildcard permissions** — Avoid `"*"` in resources or verbs
3. **Disable auto-mount tokens** — Set `automountServiceAccountToken: false` unless needed
4. **Use Pod Security Standards** — Enforce `restricted` level in production namespaces
5. **Drop all capabilities** — `capabilities.drop: ["ALL"]` then add back only what's needed
6. **Read-only root filesystem** — Set `readOnlyRootFilesystem: true` and mount writable volumes explicitly
7. **Run as non-root** — Set `runAsNonRoot: true` with a specific `runAsUser`
8. **Audit RBAC regularly** — Review bindings for stale users and overly broad permissions
9. **Separate service accounts** — Each workload should have its own ServiceAccount
10. **Never use `system:masters`** — This group bypasses all RBAC authorization
