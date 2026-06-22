# Production Best Practices

> Source: [kubernetes.io/docs/setup/best-practices](https://kubernetes.io/docs/setup/best-practices/)

## Table of Contents

- [High Availability](#high-availability)
- [Resource Management](#resource-management)
- [Pod Disruption Budgets](#pod-disruption-budgets)
- [Namespace Strategy](#namespace-strategy)
- [Image Management](#image-management)
- [Upgrade Strategy](#upgrade-strategy)
- [Disaster Recovery](#disaster-recovery)
- [Cost Optimization](#cost-optimization)
- [Production Checklist](#production-checklist)

---

## High Availability

### Control Plane HA

- Run 3+ control plane nodes across availability zones
- Use odd number of etcd members (3 or 5) for quorum
- Place API server behind a load balancer

### Application HA

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0     # Zero-downtime updates
  template:
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchLabels:
                app: web-app
            topologyKey: topology.kubernetes.io/zone
      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: DoNotSchedule
        labelSelector:
          matchLabels:
            app: web-app
      containers:
      - name: web
        image: myapp:2.0.0
        resources:
          requests:
            cpu: "250m"
            memory: "256Mi"
          limits:
            memory: "512Mi"
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8080
          initialDelaySeconds: 15
          periodSeconds: 20
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 10"]
      terminationGracePeriodSeconds: 60
```

### Graceful Shutdown

```yaml
spec:
  terminationGracePeriodSeconds: 60
  containers:
  - name: app
    lifecycle:
      preStop:
        exec:
          command: ["/bin/sh", "-c", "sleep 10"]
```

The `preStop` hook ensures the Pod continues serving requests while being removed from Service endpoints.

---

## Resource Management

### Always Set Resource Requests

```yaml
resources:
  requests:
    cpu: "250m"
    memory: "256Mi"
  limits:
    memory: "512Mi"     # Set memory limits to prevent OOM
    # CPU limits optional — throttling can increase latency
```

### LimitRange for Defaults

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: defaults
  namespace: production
spec:
  limits:
  - default:
      cpu: "500m"
      memory: "512Mi"
    defaultRequest:
      cpu: "100m"
      memory: "128Mi"
    type: Container
```

### ResourceQuota per Namespace

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: production-quota
  namespace: production
spec:
  hard:
    requests.cpu: "100"
    requests.memory: "200Gi"
    limits.cpu: "200"
    limits.memory: "400Gi"
    pods: "500"
    services.loadbalancers: "5"
    persistentvolumeclaims: "100"
```

---

## Pod Disruption Budgets

Protect application availability during voluntary disruptions (node drains, upgrades, autoscaling).

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: web-app-pdb
spec:
  minAvailable: 2              # At least 2 pods must stay running
  # OR
  # maxUnavailable: 1          # At most 1 pod can be down at a time
  selector:
    matchLabels:
      app: web-app
```

### Guidelines

| Replicas | PDB Setting |
|----------|-------------|
| 1 | Don't use PDB (blocks all disruptions) |
| 2-3 | `maxUnavailable: 1` |
| 4+ | `minAvailable: 50%` or `maxUnavailable: 25%` |

---

## Namespace Strategy

### Environment-Based

```yaml
# Namespaces: dev, staging, production
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    env: production
    pod-security.kubernetes.io/enforce: restricted
```

### Team-Based

```yaml
# Namespaces: team-backend, team-frontend, team-data
apiVersion: v1
kind: Namespace
metadata:
  name: team-backend
  labels:
    team: backend
```

### RBAC per Namespace

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: team-edit
  namespace: team-backend
subjects:
- kind: Group
  name: backend-engineers
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: edit
  apiGroup: rbac.authorization.k8s.io
```

---

## Image Management

### Pin Image Versions

```yaml
# GOOD
image: myapp:2.0.0
image: nginx:1.26.1

# BAD
image: myapp:latest
image: nginx
```

### Image Pull Policy

| Policy | Behavior |
|--------|----------|
| `Always` | Pull image every time |
| `IfNotPresent` | Pull only if not cached locally (default for tagged images) |
| `Never` | Never pull; image must exist locally |

### Private Registries

```yaml
spec:
  imagePullSecrets:
  - name: registry-credentials
  containers:
  - name: app
    image: ghcr.io/myorg/myapp:2.0.0
```

### Image Scanning

Integrate vulnerability scanning in CI/CD before deployment:

```bash
# Trivy
trivy image myapp:2.0.0

# Grype
grype myapp:2.0.0
```

---

## Upgrade Strategy

### Cluster Upgrades

1. **Read release notes** for breaking changes
2. **Upgrade control plane first**, then worker nodes
3. **Upgrade one minor version at a time** (1.35 → 1.36, not 1.34 → 1.36)
4. **Test in staging** before production

```bash
# kubeadm upgrade
sudo kubeadm upgrade plan
sudo kubeadm upgrade apply v1.36.1

# Drain and upgrade each worker
kubectl drain worker-1 --ignore-daemonsets --delete-emptydir-data
# ... upgrade kubelet and kubectl on the node ...
kubectl uncordon worker-1
```

### Application Upgrades

```yaml
# Blue-Green with Service selector switch
apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  selector:
    app: web-app
    version: v2       # Switch from v1 to v2
```

```yaml
# Canary with traffic splitting (Gateway API)
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
spec:
  rules:
  - backendRefs:
    - name: web-v1
      port: 80
      weight: 90
    - name: web-v2
      port: 80
      weight: 10
```

---

## Disaster Recovery

### etcd Backup

```bash
# Backup
ETCDCTL_API=3 etcdctl snapshot save /backup/etcd-$(date +%Y%m%d).db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Verify backup
ETCDCTL_API=3 etcdctl snapshot status /backup/etcd-20260623.db --write-table

# Restore
ETCDCTL_API=3 etcdctl snapshot restore /backup/etcd-20260623.db \
  --data-dir=/var/lib/etcd-restore
```

### Velero (Cluster Backup)

```bash
# Install Velero
velero install --provider aws --bucket my-backup-bucket \
  --secret-file ./cloud-credentials

# Backup namespace
velero backup create prod-backup --include-namespaces production

# Schedule regular backups
velero schedule create daily --schedule="0 2 * * *" --include-namespaces production

# Restore
velero restore create --from-backup prod-backup
```

### GitOps (Configuration as Code)

Store all manifests in Git and use GitOps tools for reconciliation:

| Tool | Description |
|------|-------------|
| **ArgoCD** | Declarative GitOps CD for Kubernetes |
| **Flux** | GitOps toolkit for Kubernetes |

---

## Cost Optimization

1. **Right-size resources** — Monitor actual usage with `kubectl top` and VPA recommendations
2. **Use Cluster Autoscaler** — Scale nodes down when underutilized
3. **Spot/preemptible instances** — For fault-tolerant workloads
4. **KEDA scale-to-zero** — Scale non-critical workloads to zero when idle
5. **ResourceQuotas** — Prevent teams from over-provisioning
6. **Namespace-level budgets** — Track cost per team/service

---

## Production Checklist

### Pod Configuration
- [ ] Resource requests and limits defined
- [ ] Liveness and readiness probes configured
- [ ] Security context set (non-root, read-only FS, drop capabilities)
- [ ] Image tag pinned (not `latest`)
- [ ] terminationGracePeriodSeconds and preStop hook set
- [ ] Pod Disruption Budget created

### Deployment
- [ ] Multiple replicas (3+ for production)
- [ ] Anti-affinity across zones
- [ ] Rolling update strategy with `maxUnavailable: 0`
- [ ] HPA configured with appropriate metrics

### Security
- [ ] RBAC with least privilege
- [ ] Pod Security Standards enforced (`restricted`)
- [ ] Secrets encrypted at rest
- [ ] Network Policies applied
- [ ] Image vulnerability scanning in CI/CD
- [ ] ServiceAccount per workload

### Operations
- [ ] Monitoring stack deployed (Prometheus + Grafana)
- [ ] Log aggregation configured
- [ ] Alerting rules defined
- [ ] etcd backup scheduled
- [ ] Disaster recovery plan tested
- [ ] Cluster upgrade runbook documented

### Networking
- [ ] Ingress with TLS termination
- [ ] Network Policies for isolation
- [ ] DNS configuration verified
- [ ] Load balancer health checks configured
