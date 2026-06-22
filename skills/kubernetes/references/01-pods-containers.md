# Pods & Containers

> Source: [kubernetes.io/docs/concepts/workloads/pods](https://kubernetes.io/docs/concepts/workloads/pods/)

## Table of Contents

- [What Is a Pod](#what-is-a-pod)
- [Pod Lifecycle](#pod-lifecycle)
- [Pod Spec](#pod-spec)
- [Init Containers](#init-containers)
- [Sidecar Containers](#sidecar-containers)
- [Container Probes](#container-probes)
- [Resource Requests and Limits](#resource-requests-and-limits)
- [Multi-Container Patterns](#multi-container-patterns)
- [Ephemeral Containers](#ephemeral-containers)
- [Pod Quality of Service](#pod-quality-of-service)
- [Common Pitfalls](#common-pitfalls)

---

## What Is a Pod

A Pod is the smallest deployable unit in Kubernetes — a group of one or more containers with shared storage and network resources. All containers in a Pod share the same IP address and port space, and can communicate via `localhost`.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
  labels:
    app: nginx
spec:
  containers:
  - name: nginx
    image: nginx:1.26
    ports:
    - containerPort: 80
```

```bash
kubectl apply -f pod.yaml
kubectl get pod nginx
kubectl describe pod nginx
kubectl delete pod nginx
```

---

## Pod Lifecycle

### Phases

| Phase | Description |
|-------|-------------|
| `Pending` | Accepted but containers not yet running (scheduling, image pull) |
| `Running` | At least one container is running |
| `Succeeded` | All containers terminated successfully (exit code 0) |
| `Failed` | At least one container terminated with failure |
| `Unknown` | Pod state cannot be determined (node communication failure) |

### Conditions

```yaml
status:
  conditions:
  - type: PodScheduled
    status: "True"
  - type: Initialized
    status: "True"
  - type: ContainersReady
    status: "True"
  - type: Ready
    status: "True"
```

### Restart Policies

| Policy | Behavior |
|--------|----------|
| `Always` | Restart containers regardless of exit code (default) |
| `OnFailure` | Restart only on non-zero exit code |
| `Never` | Never restart containers |

```yaml
spec:
  restartPolicy: OnFailure
```

---

## Pod Spec

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-pod
  labels:
    app: myapp
    version: v1
spec:
  serviceAccountName: app-sa
  terminationGracePeriodSeconds: 30
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 2000
  containers:
  - name: app
    image: myapp:1.0
    ports:
    - containerPort: 8080
      name: http
      protocol: TCP
    env:
    - name: DATABASE_URL
      valueFrom:
        secretKeyRef:
          name: db-secret
          key: url
    volumeMounts:
    - name: data
      mountPath: /data
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop: ["ALL"]
  volumes:
  - name: data
    emptyDir: {}
```

---

## Init Containers

Containers that run to completion before app containers start. They run sequentially — each must succeed before the next begins.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-init
spec:
  initContainers:
  - name: wait-for-db
    image: busybox:1.36
    command:
    - sh
    - -c
    - |
      until nslookup postgres.default.svc.cluster.local; do
        echo "Waiting for database..."
        sleep 2
      done
  - name: run-migrations
    image: myapp:1.0
    command: ["python", "manage.py", "migrate"]
    env:
    - name: DATABASE_URL
      valueFrom:
        secretKeyRef:
          name: db-secret
          key: url
  containers:
  - name: app
    image: myapp:1.0
    ports:
    - containerPort: 8080
```

### Use Cases

- Wait for a dependent service to be available
- Run database migrations
- Download configuration from a remote source
- Register with a service discovery system
- Set permissions on shared volumes

---

## Sidecar Containers

Containers that run alongside the main application container for the entire Pod lifecycle.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-sidecar
spec:
  initContainers:
  - name: log-agent
    image: fluentd:v1.16
    restartPolicy: Always    # Makes it a sidecar (runs for Pod lifetime)
    volumeMounts:
    - name: logs
      mountPath: /var/log/app
  containers:
  - name: app
    image: myapp:1.0
    volumeMounts:
    - name: logs
      mountPath: /var/log/app
  volumes:
  - name: logs
    emptyDir: {}
```

### Common Sidecar Patterns

| Pattern | Example |
|---------|---------|
| **Log collection** | Fluentd/Fluent Bit shipping logs to Elasticsearch |
| **Service mesh proxy** | Envoy/Istio sidecar for traffic management |
| **Configuration sync** | git-sync pulling config from a repository |
| **TLS termination** | Sidecar handling mTLS for the app container |

---

## Container Probes

### Liveness Probe

Detects when a container is stuck. Failure triggers a container restart.

```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 15
  periodSeconds: 20
  timeoutSeconds: 3
  failureThreshold: 3
  successThreshold: 1
```

### Readiness Probe

Determines if a container can receive traffic. Failure removes the Pod from Service endpoints.

```yaml
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 10
  failureThreshold: 3
```

### Startup Probe

Indicates when an application has started. Disables liveness/readiness checks until it succeeds. Designed for slow-starting containers.

```yaml
startupProbe:
  httpGet:
    path: /healthz
    port: 8080
  failureThreshold: 30
  periodSeconds: 10
  # Gives the app up to 5 minutes to start (30 × 10s)
```

### Probe Methods

| Method | Description |
|--------|-------------|
| `httpGet` | HTTP GET request; success = 200-399 status |
| `tcpSocket` | TCP connection; success = port is open |
| `exec` | Run command; success = exit code 0 |
| `grpc` | gRPC health check (requires gRPC health protocol) |

```yaml
# TCP probe
livenessProbe:
  tcpSocket:
    port: 3306
  periodSeconds: 10

# Exec probe
livenessProbe:
  exec:
    command:
    - cat
    - /tmp/healthy
  periodSeconds: 5

# gRPC probe
livenessProbe:
  grpc:
    port: 50051
  periodSeconds: 10
```

---

## Resource Requests and Limits

```yaml
containers:
- name: app
  image: myapp:1.0
  resources:
    requests:          # Scheduling guarantee
      cpu: "250m"      # 0.25 CPU cores
      memory: "128Mi"  # 128 mebibytes
    limits:            # Hard ceiling
      cpu: "500m"
      memory: "256Mi"
```

### CPU Units

| Value | Meaning |
|-------|---------|
| `1` | 1 vCPU/core |
| `500m` | 0.5 CPU (500 millicores) |
| `100m` | 0.1 CPU |

### Memory Units

| Value | Meaning |
|-------|---------|
| `128Mi` | 128 mebibytes (power of 2) |
| `1Gi` | 1 gibibyte |
| `256M` | 256 megabytes (power of 10) |

### Behavior When Limits Are Exceeded

- **CPU**: Container is throttled (not killed)
- **Memory**: Container is OOMKilled and restarted

---

## Multi-Container Patterns

### Sidecar Pattern

```yaml
spec:
  containers:
  - name: app
    image: myapp:1.0
    volumeMounts:
    - name: shared-logs
      mountPath: /var/log
  - name: log-shipper
    image: fluentd:latest
    volumeMounts:
    - name: shared-logs
      mountPath: /var/log
  volumes:
  - name: shared-logs
    emptyDir: {}
```

### Ambassador Pattern

A proxy container that handles external communication.

```yaml
spec:
  containers:
  - name: app
    image: myapp:1.0
    env:
    - name: DB_HOST
      value: "localhost"    # Connects to ambassador on localhost
    - name: DB_PORT
      value: "5432"
  - name: ambassador
    image: cloud-sql-proxy:latest
    command: ["/cloud_sql_proxy", "-instances=project:region:db=tcp:5432"]
```

### Adapter Pattern

A container that transforms output from the app container.

```yaml
spec:
  containers:
  - name: app
    image: myapp:1.0
    volumeMounts:
    - name: logs
      mountPath: /var/log
  - name: log-adapter
    image: log-transformer:1.0
    volumeMounts:
    - name: logs
      mountPath: /var/log
```

---

## Ephemeral Containers

Temporary containers added to running Pods for debugging. They cannot be restarted and have no ports or probes.

```bash
# Debug a running pod
kubectl debug pod/myapp -it --image=busybox:1.36 -- sh

# Debug by copying the pod
kubectl debug pod/myapp -it --image=busybox:1.36 --copy-to=debug-pod

# Debug a node
kubectl debug node/mynode -it --image=ubuntu
```

---

## Pod Quality of Service

Kubernetes assigns QoS classes based on resource specifications:

| QoS Class | Condition | Eviction Priority |
|-----------|-----------|-------------------|
| **Guaranteed** | All containers have equal requests and limits for CPU and memory | Last (highest priority) |
| **Burstable** | At least one container has a request or limit | Middle |
| **BestEffort** | No requests or limits defined | First (lowest priority) |

```yaml
# Guaranteed QoS
resources:
  requests:
    cpu: "500m"
    memory: "256Mi"
  limits:
    cpu: "500m"       # Same as request
    memory: "256Mi"   # Same as request
```

---

## Common Pitfalls

1. **No health probes** — Kubernetes can't detect stuck containers without probes
2. **Liveness probe too aggressive** — A tight `failureThreshold` with slow apps causes restart loops
3. **Missing resource requests** — Scheduler can't make good placement decisions
4. **Using `latest` image tag** — No way to track which version is actually running
5. **Sharing PID namespace unintentionally** — Containers can see each other's processes
6. **Ignoring termination grace period** — App doesn't handle SIGTERM gracefully, data loss on shutdown
7. **Readiness probe pointing to liveness endpoint** — Different concerns; readiness should check dependencies
