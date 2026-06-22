# Scheduling

> Source: [kubernetes.io/docs/concepts/scheduling-eviction](https://kubernetes.io/docs/concepts/scheduling-eviction/)

## Table of Contents

- [How Scheduling Works](#how-scheduling-works)
- [nodeSelector](#nodeselector)
- [Node Affinity](#node-affinity)
- [Pod Affinity and Anti-Affinity](#pod-affinity-and-anti-affinity)
- [Taints and Tolerations](#taints-and-tolerations)
- [Topology Spread Constraints](#topology-spread-constraints)
- [Pod Priority and Preemption](#pod-priority-and-preemption)
- [Common Pitfalls](#common-pitfalls)

---

## How Scheduling Works

The kube-scheduler selects a node for each unscheduled Pod using a two-phase process:

1. **Filtering**: Eliminates nodes that don't meet requirements (resources, taints, affinity)
2. **Scoring**: Ranks remaining nodes by preferences (resource balance, affinity weights)

If no node satisfies constraints, the Pod stays `Pending` until a suitable node becomes available.

---

## nodeSelector

The simplest scheduling constraint — match node labels.

```bash
# Label a node
kubectl label nodes worker-1 disktype=ssd
kubectl label nodes worker-2 gpu=nvidia-a100
```

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: gpu-pod
spec:
  nodeSelector:
    gpu: nvidia-a100
  containers:
  - name: ml-training
    image: training:1.0
    resources:
      limits:
        nvidia.com/gpu: 1
```

### Built-in Node Labels

| Label | Description |
|-------|-------------|
| `kubernetes.io/hostname` | Node hostname |
| `kubernetes.io/os` | Operating system (linux, windows) |
| `kubernetes.io/arch` | CPU architecture (amd64, arm64) |
| `topology.kubernetes.io/zone` | Cloud availability zone |
| `topology.kubernetes.io/region` | Cloud region |
| `node.kubernetes.io/instance-type` | Instance type (e.g., m5.xlarge) |

---

## Node Affinity

More expressive than nodeSelector — supports soft preferences and set-based operators.

### Required (Hard Constraint)

Pod will not schedule if the constraint isn't met:

```yaml
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: topology.kubernetes.io/zone
            operator: In
            values:
            - us-east-1a
            - us-east-1b
          - key: kubernetes.io/os
            operator: In
            values:
            - linux
```

### Preferred (Soft Constraint)

Scheduler tries to satisfy but won't prevent scheduling:

```yaml
spec:
  affinity:
    nodeAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 80
        preference:
          matchExpressions:
          - key: disktype
            operator: In
            values:
            - ssd
      - weight: 20
        preference:
          matchExpressions:
          - key: node.kubernetes.io/instance-type
            operator: In
            values:
            - m5.xlarge
            - m5.2xlarge
```

### Operators

| Operator | Description |
|----------|-------------|
| `In` | Value is in the list |
| `NotIn` | Value is not in the list |
| `Exists` | Key exists (any value) |
| `DoesNotExist` | Key does not exist |
| `Gt` | Value is greater than |
| `Lt` | Value is less than |

---

## Pod Affinity and Anti-Affinity

Schedule Pods relative to other Pods based on their labels.

### Pod Affinity (Co-locate)

Place the Pod near other Pods with matching labels:

```yaml
spec:
  affinity:
    podAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchExpressions:
          - key: app
            operator: In
            values:
            - cache
        topologyKey: kubernetes.io/hostname
```

### Pod Anti-Affinity (Spread)

Keep the Pod away from other Pods with matching labels:

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
  template:
    metadata:
      labels:
        app: web-app
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchLabels:
                app: web-app
            topologyKey: kubernetes.io/hostname
      containers:
      - name: web
        image: nginx:1.26
```

### Topology Keys

| Key | Spreads across |
|-----|---------------|
| `kubernetes.io/hostname` | Individual nodes |
| `topology.kubernetes.io/zone` | Availability zones |
| `topology.kubernetes.io/region` | Regions |

---

## Taints and Tolerations

Taints repel Pods from nodes. Tolerations allow Pods to schedule on tainted nodes.

### Adding Taints

```bash
# Add taint
kubectl taint nodes worker-1 dedicated=ml:NoSchedule

# Remove taint
kubectl taint nodes worker-1 dedicated=ml:NoSchedule-
```

### Taint Effects

| Effect | Behavior |
|--------|----------|
| `NoSchedule` | New Pods without toleration won't schedule |
| `PreferNoSchedule` | Scheduler tries to avoid but may place Pods |
| `NoExecute` | Existing Pods without toleration are evicted |

### Tolerations

```yaml
spec:
  tolerations:
  - key: "dedicated"
    operator: "Equal"
    value: "ml"
    effect: "NoSchedule"
  - key: "node.kubernetes.io/not-ready"
    operator: "Exists"
    effect: "NoExecute"
    tolerationSeconds: 300     # Evict after 5 minutes
```

### Common Use Cases

```yaml
# Tolerate control plane nodes
tolerations:
- key: node-role.kubernetes.io/control-plane
  effect: NoSchedule

# Tolerate any taint (run anywhere)
tolerations:
- operator: "Exists"

# GPU-dedicated nodes
# Taint: kubectl taint nodes gpu-node nvidia.com/gpu=present:NoSchedule
tolerations:
- key: "nvidia.com/gpu"
  operator: "Exists"
  effect: "NoSchedule"
```

---

## Topology Spread Constraints

Distribute Pods evenly across topology domains (zones, nodes).

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 6
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: DoNotSchedule
        labelSelector:
          matchLabels:
            app: web-app
      - maxSkew: 1
        topologyKey: kubernetes.io/hostname
        whenUnsatisfiable: ScheduleAnyway
        labelSelector:
          matchLabels:
            app: web-app
      containers:
      - name: web
        image: nginx:1.26
```

### Parameters

| Parameter | Description |
|-----------|-------------|
| `maxSkew` | Max difference in Pod count between topology domains |
| `topologyKey` | Node label defining topology domains |
| `whenUnsatisfiable` | `DoNotSchedule` (hard) or `ScheduleAnyway` (soft) |
| `labelSelector` | Which Pods to consider for spread calculation |
| `minDomains` | Minimum number of domains to consider |

---

## Pod Priority and Preemption

Higher-priority Pods can evict lower-priority Pods when resources are scarce.

```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority
value: 1000000
globalDefault: false
preemptionPolicy: PreemptLowerPriority
description: "Critical production workloads"
---
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: low-priority
value: 100
preemptionPolicy: Never         # Never preempt other pods
---
apiVersion: v1
kind: Pod
metadata:
  name: critical-pod
spec:
  priorityClassName: high-priority
  containers:
  - name: app
    image: myapp:1.0
```

### Built-in Priority Classes

| Class | Value | Description |
|-------|-------|-------------|
| `system-cluster-critical` | 2000000000 | Cluster-critical components |
| `system-node-critical` | 2000001000 | Node-critical components |

---

## Common Pitfalls

1. **Pod stuck Pending with affinity** — No nodes satisfy the constraint; verify labels with `kubectl get nodes --show-labels`
2. **Anti-affinity with too many replicas** — Can't spread 10 replicas across 3 nodes with hard anti-affinity
3. **Missing tolerations for system taints** — `node.kubernetes.io/not-ready` and `unreachable` need tolerations
4. **`topologyKey` mismatch** — Key must exist on nodes; typos cause silent scheduling failures
5. **PriorityClass without preemptionPolicy** — Default is `PreemptLowerPriority`; production pods may evict dev pods
6. **nodeName bypassing scheduler** — Directly assigned pods skip all scheduling checks
