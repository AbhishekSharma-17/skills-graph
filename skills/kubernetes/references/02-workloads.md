# Workloads

> Source: [kubernetes.io/docs/concepts/workloads/controllers](https://kubernetes.io/docs/concepts/workloads/controllers/)

## Table of Contents

- [Deployments](#deployments)
- [ReplicaSets](#replicasets)
- [StatefulSets](#statefulsets)
- [DaemonSets](#daemonsets)
- [Jobs](#jobs)
- [CronJobs](#cronjobs)
- [Choosing the Right Workload](#choosing-the-right-workload)
- [Common Pitfalls](#common-pitfalls)

---

## Deployments

The most common workload resource for stateless applications. Manages ReplicaSets and provides declarative updates.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-app
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: web-app
    spec:
      containers:
      - name: web
        image: myapp:2.0
        ports:
        - containerPort: 8080
        resources:
          requests:
            cpu: "250m"
            memory: "128Mi"
          limits:
            cpu: "500m"
            memory: "256Mi"
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8080
          initialDelaySeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
```

### Update Strategies

| Strategy | Behavior | Downtime |
|----------|----------|----------|
| `RollingUpdate` | Gradually replace old pods with new (default) | None |
| `Recreate` | Kill all old pods before creating new ones | Yes |

### Rolling Update Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `maxSurge` | 25% | Max pods above desired count during update |
| `maxUnavailable` | 25% | Max pods unavailable during update |

### Rollout Management

```bash
# Check rollout status
kubectl rollout status deployment/web-app

# View rollout history
kubectl rollout history deployment/web-app

# Rollback to previous revision
kubectl rollout undo deployment/web-app

# Rollback to specific revision
kubectl rollout undo deployment/web-app --to-revision=2

# Pause rollout (for batching changes)
kubectl rollout pause deployment/web-app

# Resume rollout
kubectl rollout resume deployment/web-app

# Restart deployment (triggers rolling update)
kubectl rollout restart deployment/web-app
```

### Scaling

```bash
kubectl scale deployment/web-app --replicas=5
```

### Key Spec Fields

| Field | Default | Description |
|-------|---------|-------------|
| `replicas` | 1 | Desired pod count |
| `revisionHistoryLimit` | 10 | Old ReplicaSets to retain |
| `progressDeadlineSeconds` | 600 | Max time for rollout progress |
| `minReadySeconds` | 0 | Time pod must be ready before available |
| `paused` | false | Whether rollout is paused |

---

## ReplicaSets

Ensures a specified number of pod replicas are running. Deployments manage ReplicaSets — rarely created directly.

```yaml
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: frontend
spec:
  replicas: 3
  selector:
    matchLabels:
      tier: frontend
  template:
    metadata:
      labels:
        tier: frontend
    spec:
      containers:
      - name: php-redis
        image: gcr.io/google_samples/gb-frontend:v4
```

---

## StatefulSets

For applications requiring stable network identities, ordered deployment/scaling, and persistent storage.

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres
  replicas: 3
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:16
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: pg-secret
              key: password
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 10Gi
```

### StatefulSet Guarantees

| Feature | Description |
|---------|-------------|
| **Stable network identity** | Pods get predictable names: `<statefulset>-0`, `-1`, `-2` |
| **Stable DNS** | Each pod gets `<pod-name>.<service-name>.<namespace>.svc.cluster.local` |
| **Ordered deployment** | Pods created sequentially (0, then 1, then 2) |
| **Ordered termination** | Pods deleted in reverse order (2, then 1, then 0) |
| **Persistent storage** | Each pod gets its own PVC that persists across restarts |

### Headless Service (Required)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres
spec:
  clusterIP: None
  selector:
    app: postgres
  ports:
  - port: 5432
```

### Update Strategies

```yaml
spec:
  updateStrategy:
    type: RollingUpdate       # or OnDelete
    rollingUpdate:
      partition: 2            # Only update pods with ordinal >= 2 (canary)
      maxUnavailable: 1
```

---

## DaemonSets

Ensures a copy of a pod runs on every (or selected) node. Pods are automatically added to new nodes and removed from deleted nodes.

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-exporter
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: node-exporter
  template:
    metadata:
      labels:
        app: node-exporter
    spec:
      tolerations:
      - key: node-role.kubernetes.io/control-plane
        effect: NoSchedule
      containers:
      - name: node-exporter
        image: prom/node-exporter:v1.8.0
        ports:
        - containerPort: 9100
        resources:
          requests:
            cpu: "100m"
            memory: "64Mi"
          limits:
            cpu: "200m"
            memory: "128Mi"
      hostNetwork: true
      hostPID: true
```

### Use Cases

- Node monitoring agents (Prometheus Node Exporter, Datadog)
- Log collectors (Fluentd, Fluent Bit)
- Network plugins (Calico, Cilium)
- Storage daemons (GlusterFS, Ceph)

### Run on Specific Nodes

```yaml
spec:
  template:
    spec:
      nodeSelector:
        disk: ssd
```

---

## Jobs

Runs pods to completion. Pods are not restarted after successful termination.

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: data-migration
spec:
  backoffLimit: 4
  activeDeadlineSeconds: 600
  template:
    spec:
      containers:
      - name: migrate
        image: myapp:1.0
        command: ["python", "migrate.py"]
      restartPolicy: Never
```

### Parallel Jobs

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: parallel-job
spec:
  completions: 10        # Total tasks to complete
  parallelism: 3         # Max concurrent pods
  completionMode: Indexed # Each pod gets a unique index (0-9)
  template:
    spec:
      containers:
      - name: worker
        image: worker:1.0
        env:
        - name: JOB_INDEX
          valueFrom:
            fieldRef:
              fieldPath: metadata.annotations['batch.kubernetes.io/job-completion-index']
      restartPolicy: Never
```

### Job Parameters

| Parameter | Description |
|-----------|-------------|
| `completions` | Total successful completions needed |
| `parallelism` | Max concurrent pods |
| `backoffLimit` | Max retries before marking failed (default: 6) |
| `activeDeadlineSeconds` | Max runtime before job is terminated |
| `ttlSecondsAfterFinished` | Auto-cleanup after completion |

---

## CronJobs

Runs Jobs on a time-based schedule.

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: nightly-backup
spec:
  schedule: "0 2 * * *"           # Every day at 2:00 AM
  timeZone: "America/New_York"
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  startingDeadlineSeconds: 200
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: backup-tool:1.0
            command: ["/bin/sh", "-c", "backup.sh"]
          restartPolicy: OnFailure
```

### Schedule Syntax

```
┌───────────── minute (0-59)
│ ┌───────────── hour (0-23)
│ │ ┌───────────── day of month (1-31)
│ │ │ ┌───────────── month (1-12)
│ │ │ │ ┌───────────── day of week (0-6, Sun=0)
│ │ │ │ │
* * * * *
```

| Expression | Meaning |
|------------|---------|
| `*/15 * * * *` | Every 15 minutes |
| `0 */6 * * *` | Every 6 hours |
| `0 9 * * 1-5` | Weekdays at 9:00 AM |
| `0 0 1 * *` | First day of each month |

### Concurrency Policies

| Policy | Behavior |
|--------|----------|
| `Allow` | Allow concurrent job runs (default) |
| `Forbid` | Skip new run if previous is still running |
| `Replace` | Cancel running job and start new one |

---

## Choosing the Right Workload

| Workload | Use Case |
|----------|----------|
| **Deployment** | Stateless web servers, APIs, microservices |
| **StatefulSet** | Databases, message queues, anything needing stable identity |
| **DaemonSet** | Node-level agents, log collectors, monitoring |
| **Job** | One-off tasks, data migrations, batch processing |
| **CronJob** | Scheduled tasks, periodic backups, report generation |

---

## Common Pitfalls

1. **Using StatefulSet for stateless apps** — Deployments are simpler and more flexible
2. **No PodDisruptionBudget** — Cluster operations can take down all replicas simultaneously
3. **CronJob with `Allow` concurrency** — Long-running jobs pile up; use `Forbid` or `Replace`
4. **Job without `backoffLimit`** — Default is 6; infinite retries on misconfigured jobs waste resources
5. **StatefulSet without headless Service** — Required for stable DNS names
6. **Forgetting `volumeClaimTemplates`** — StatefulSet pods lose data on restart without persistent storage
7. **DaemonSet without tolerations** — Won't run on control plane nodes with taints
