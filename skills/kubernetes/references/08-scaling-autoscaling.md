# Scaling & Autoscaling

> Source: [kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)

## Table of Contents

- [Manual Scaling](#manual-scaling)
- [Horizontal Pod Autoscaler](#horizontal-pod-autoscaler)
- [HPA Metric Types](#hpa-metric-types)
- [Scaling Behavior](#scaling-behavior)
- [Vertical Pod Autoscaler](#vertical-pod-autoscaler)
- [Cluster Autoscaler](#cluster-autoscaler)
- [KEDA](#keda)
- [Common Pitfalls](#common-pitfalls)

---

## Manual Scaling

```bash
# Scale deployment
kubectl scale deployment/web-app --replicas=5

# Scale statefulset
kubectl scale statefulset/postgres --replicas=3

# Conditional scaling (only if current replicas match)
kubectl scale deployment/web-app --current-replicas=3 --replicas=5
```

---

## Horizontal Pod Autoscaler

HPA automatically adjusts replica count based on observed metrics. The controller checks metrics every 15 seconds by default.

### Core Algorithm

```
desiredReplicas = ceil(currentReplicas × (currentMetricValue / desiredMetricValue))
```

Scaling is skipped if the ratio is within ±10% tolerance.

### Basic CPU-Based HPA

```bash
kubectl autoscale deployment web-app \
  --cpu-percent=50 \
  --min=2 \
  --max=20
```

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: web-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-app
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50
```

### CPU and Memory HPA

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-app
  minReplicas: 3
  maxReplicas: 50
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 60
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Monitoring HPA

```bash
# View HPA status
kubectl get hpa
kubectl describe hpa web-app-hpa

# Current resource usage
kubectl top pods
kubectl top nodes
```

---

## HPA Metric Types

### Resource Metrics (Per-Pod)

CPU and memory from the Metrics Server:

```yaml
metrics:
- type: Resource
  resource:
    name: cpu
    target:
      type: Utilization           # Percentage of request
      averageUtilization: 50
- type: Resource
  resource:
    name: memory
    target:
      type: AverageValue          # Absolute value
      averageValue: 500Mi
```

### Custom Metrics (Per-Pod)

Application-specific metrics from a custom metrics adapter:

```yaml
metrics:
- type: Pods
  pods:
    metric:
      name: http_requests_per_second
    target:
      type: AverageValue
      averageValue: "1000"
```

### Object Metrics

Metrics from another Kubernetes object:

```yaml
metrics:
- type: Object
  object:
    metric:
      name: requests-per-second
    describedObject:
      apiVersion: networking.k8s.io/v1
      kind: Ingress
      name: main-route
    target:
      type: Value
      value: "10k"
```

### External Metrics

Metrics from external monitoring systems:

```yaml
metrics:
- type: External
  external:
    metric:
      name: pubsub_subscription_num_undelivered_messages
      selector:
        matchLabels:
          subscription: worker-tasks
    target:
      type: AverageValue
      averageValue: "30"
```

---

## Scaling Behavior

Fine-tune how fast scaling occurs:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: web-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-app
  minReplicas: 5
  maxReplicas: 100
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 0       # Scale up immediately
      policies:
      - type: Percent
        value: 100                        # Double pods
        periodSeconds: 15
      - type: Pods
        value: 5                          # Or add 5 pods
        periodSeconds: 15
      selectPolicy: Max                   # Use whichever adds more
    scaleDown:
      stabilizationWindowSeconds: 300     # Wait 5 min before scaling down
      policies:
      - type: Percent
        value: 10                         # Remove 10% at a time
        periodSeconds: 60
      selectPolicy: Min                   # Use whichever removes fewer
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50
```

### Disable Scale-Down

```yaml
behavior:
  scaleDown:
    selectPolicy: Disabled
```

### Scale-Down Only

```yaml
behavior:
  scaleUp:
    selectPolicy: Disabled
```

### Stabilization Window

Prevents rapid oscillation ("flapping"):

| Direction | Default | Purpose |
|-----------|---------|---------|
| Scale Up | 0s | React quickly to load increases |
| Scale Down | 300s | Avoid premature scale-down after brief drops |

---

## Vertical Pod Autoscaler

VPA adjusts CPU and memory requests/limits for individual Pods. Requires separate installation.

```bash
# Install VPA
git clone https://github.com/kubernetes/autoscaler.git
cd autoscaler/vertical-pod-autoscaler && ./hack/vpa-up.sh
```

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: app-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-app
  updatePolicy:
    updateMode: Auto          # Off, Initial, Recreate, Auto
  resourcePolicy:
    containerPolicies:
    - containerName: app
      minAllowed:
        cpu: "100m"
        memory: "128Mi"
      maxAllowed:
        cpu: "4"
        memory: "8Gi"
      controlledResources: ["cpu", "memory"]
```

### VPA Modes

| Mode | Behavior |
|------|----------|
| `Off` | Only provides recommendations |
| `Initial` | Sets resources only at Pod creation |
| `Recreate` | Evicts Pods to apply new resources |
| `Auto` | Updates in-place if possible, otherwise recreates |

---

## Cluster Autoscaler

Automatically adjusts the number of nodes in the cluster based on pending Pods and node utilization.

### Cloud Provider Configuration

```yaml
# AWS EKS managed node group
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig
metadata:
  name: my-cluster
  region: us-east-1
managedNodeGroups:
- name: workers
  instanceType: m5.xlarge
  minSize: 2
  maxSize: 20
  desiredCapacity: 5
  labels:
    role: worker
```

### Key Parameters

| Parameter | Description |
|-----------|-------------|
| `--scale-down-delay-after-add` | Wait time after scale-up before scale-down (default: 10m) |
| `--scale-down-unneeded-time` | Time node must be underutilized before removal (default: 10m) |
| `--scale-down-utilization-threshold` | Utilization below which node is unneeded (default: 0.5) |
| `--max-node-provision-time` | Max time to wait for node to become ready (default: 15m) |

---

## KEDA

Kubernetes Event-Driven Autoscaling — scales workloads based on event sources (queues, streams, databases).

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: queue-worker
spec:
  scaleTargetRef:
    name: worker-deployment
  minReplicaCount: 0           # Scale to zero when idle
  maxReplicaCount: 50
  triggers:
  - type: rabbitmq
    metadata:
      queueName: tasks
      host: amqp://rabbitmq.default.svc.cluster.local
      queueLength: "5"         # Scale when queue > 5 per replica
```

---

## Common Pitfalls

1. **No resource requests** — HPA requires requests defined for utilization-based scaling
2. **Metrics Server not installed** — HPA won't work without a metrics source
3. **HPA and manual scaling conflict** — Don't set replicas in Deployment when using HPA
4. **Scale-down too aggressive** — Default 5-minute stabilization may not be enough; increase for bursty workloads
5. **VPA and HPA on same metric** — Don't use both for CPU; VPA adjusts requests, HPA adjusts replicas
6. **Cluster Autoscaler with PDB** — Pod Disruption Budgets can prevent scale-down if too restrictive
7. **Ignoring `maxReplicas`** — Set a reasonable ceiling to prevent cost explosions
