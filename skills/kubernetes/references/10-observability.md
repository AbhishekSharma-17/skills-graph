# Observability

> Source: [kubernetes.io/docs/tasks/debug](https://kubernetes.io/docs/tasks/debug/)

## Table of Contents

- [Metrics Server](#metrics-server)
- [Logging](#logging)
- [Debugging Pods](#debugging-pods)
- [Debugging Services](#debugging-services)
- [Debugging Nodes](#debugging-nodes)
- [Events](#events)
- [Prometheus and Grafana](#prometheus-and-grafana)
- [Common Pitfalls](#common-pitfalls)

---

## Metrics Server

Provides CPU and memory metrics for HPA and `kubectl top`.

### Installation

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# For local clusters (minikube/kind) — disable TLS verification
kubectl patch deployment metrics-server -n kube-system \
  --type='json' \
  -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'
```

### Usage

```bash
# Node resource usage
kubectl top nodes

# Pod resource usage
kubectl top pods
kubectl top pods -n production --sort-by=cpu
kubectl top pods --containers     # Per-container breakdown

# Specific pod
kubectl top pod web-app-abc123
```

---

## Logging

### Pod Logs

```bash
# Current logs
kubectl logs pod/web-app-abc123

# Previous container instance (after crash)
kubectl logs pod/web-app-abc123 --previous

# Specific container in multi-container pod
kubectl logs pod/web-app-abc123 -c sidecar

# Stream logs
kubectl logs -f pod/web-app-abc123

# Last N lines
kubectl logs pod/web-app-abc123 --tail=100

# Logs since a time
kubectl logs pod/web-app-abc123 --since=1h
kubectl logs pod/web-app-abc123 --since-time="2026-06-23T10:00:00Z"

# All pods with a label
kubectl logs -l app=web-app --all-containers

# All pods in a deployment
kubectl logs deployment/web-app
```

### Cluster-Level Logging

Kubernetes does not provide a built-in log aggregation solution. Common stacks:

| Stack | Components |
|-------|-----------|
| **EFK** | Elasticsearch + Fluentd + Kibana |
| **ELK** | Elasticsearch + Logstash + Kibana |
| **PLG** | Promtail + Loki + Grafana |

### Fluentd DaemonSet (Example)

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd
  namespace: logging
spec:
  selector:
    matchLabels:
      app: fluentd
  template:
    metadata:
      labels:
        app: fluentd
    spec:
      tolerations:
      - key: node-role.kubernetes.io/control-plane
        effect: NoSchedule
      containers:
      - name: fluentd
        image: fluent/fluentd-kubernetes-daemonset:v1.16-debian-elasticsearch8
        env:
        - name: FLUENT_ELASTICSEARCH_HOST
          value: "elasticsearch.logging.svc.cluster.local"
        volumeMounts:
        - name: varlog
          mountPath: /var/log
        - name: containers
          mountPath: /var/lib/docker/containers
          readOnly: true
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
      - name: containers
        hostPath:
          path: /var/lib/docker/containers
```

---

## Debugging Pods

### Troubleshooting Flow

```
Pod not starting?
  │
  ├── Pending → Check scheduling: kubectl describe pod <name>
  │              - Insufficient resources
  │              - No matching nodes (affinity/taints)
  │              - PVC not bound
  │
  ├── CrashLoopBackOff → Check logs: kubectl logs <name> --previous
  │                       - Application error
  │                       - Missing config/secrets
  │                       - Wrong command/args
  │
  ├── ImagePullBackOff → Check image: kubectl describe pod <name>
  │                       - Wrong image name/tag
  │                       - Missing imagePullSecret
  │                       - Registry authentication
  │
  └── Running but not working → Check app:
                                 - kubectl exec -it <name> -- sh
                                 - kubectl port-forward <name> 8080:8080
                                 - kubectl debug <name> -it --image=busybox
```

### Common Commands

```bash
# Describe pod (shows events, conditions, status)
kubectl describe pod web-app-abc123

# Get pod YAML
kubectl get pod web-app-abc123 -o yaml

# Exec into pod
kubectl exec -it web-app-abc123 -- /bin/sh

# Port forward
kubectl port-forward pod/web-app-abc123 8080:8080

# Copy files from/to pod
kubectl cp web-app-abc123:/var/log/app.log ./app.log
kubectl cp ./config.yaml web-app-abc123:/etc/config/

# Debug with ephemeral container
kubectl debug -it web-app-abc123 --image=nicolaka/netshoot --target=app

# Debug by copying pod (shares process namespace)
kubectl debug web-app-abc123 -it --copy-to=debug-pod --image=busybox --share-processes
```

---

## Debugging Services

```bash
# Check service endpoints
kubectl get endpoints web-service
kubectl get endpointslices -l kubernetes.io/service-name=web-service

# Verify service selector matches pods
kubectl get pods -l app=web-app
kubectl get svc web-service -o yaml

# Test connectivity from within cluster
kubectl run test-pod --image=busybox --rm -it -- wget -qO- http://web-service:80

# DNS resolution test
kubectl run test-dns --image=busybox --rm -it -- nslookup web-service.default.svc.cluster.local

# Check kube-proxy
kubectl get pods -n kube-system -l k8s-app=kube-proxy
kubectl logs -n kube-system -l k8s-app=kube-proxy
```

### Service Troubleshooting Checklist

1. Does the Service exist? `kubectl get svc`
2. Does the Service have endpoints? `kubectl get endpoints`
3. Do the Pod labels match the Service selector?
4. Is the target port correct?
5. Can you reach the Pod directly? `kubectl port-forward`
6. Is DNS working? `nslookup` from a test pod
7. Are NetworkPolicies blocking traffic?

---

## Debugging Nodes

```bash
# Node status
kubectl get nodes -o wide
kubectl describe node worker-1

# Node conditions
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.conditions[?(@.type=="Ready")].status}{"\n"}{end}'

# Debug a node
kubectl debug node/worker-1 -it --image=ubuntu

# Cordon/drain for maintenance
kubectl cordon worker-1                    # Prevent new pods
kubectl drain worker-1 --ignore-daemonsets --delete-emptydir-data  # Evict pods
kubectl uncordon worker-1                  # Allow pods again

# Node resource pressure
kubectl describe node worker-1 | grep -A5 Conditions
# MemoryPressure, DiskPressure, PIDPressure
```

---

## Events

```bash
# All events in namespace
kubectl get events --sort-by='.lastTimestamp'

# Warning events only
kubectl events --types=Warning

# Events for specific object
kubectl events --for pod/web-app-abc123

# Watch events
kubectl get events -w
```

### Event Fields

| Field | Description |
|-------|-------------|
| `Type` | Normal or Warning |
| `Reason` | Short machine-readable reason |
| `Object` | Resource the event is about |
| `Message` | Human-readable description |
| `Count` | Number of times this event occurred |
| `FirstTimestamp` | When event was first seen |
| `LastTimestamp` | When event was last seen |

---

## Prometheus and Grafana

### kube-prometheus-stack (Recommended)

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.adminPassword=admin
```

### ServiceMonitor (Custom Metrics)

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: app-monitor
  labels:
    release: monitoring
spec:
  selector:
    matchLabels:
      app: web-app
  endpoints:
  - port: metrics
    interval: 15s
    path: /metrics
```

### PrometheusRule (Alerts)

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: app-alerts
  labels:
    release: monitoring
spec:
  groups:
  - name: app.rules
    rules:
    - alert: HighErrorRate
      expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "High error rate on {{ $labels.instance }}"
```

### Access Dashboards

```bash
# Grafana
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80

# Prometheus
kubectl port-forward svc/monitoring-kube-prometheus-prometheus -n monitoring 9090:9090
```

---

## Common Pitfalls

1. **No Metrics Server** — `kubectl top` and HPA won't work without it
2. **Missing `--previous` flag** — Can't see logs from crashed containers without it
3. **Logging to stdout** — Kubernetes expects container logs on stdout/stderr, not files
4. **Events expire** — Default retention is 1 hour; use external event collection for history
5. **Debug container limitations** — Ephemeral containers can't be restarted or have probes
6. **Not setting up alerting** — Monitoring without alerts means nobody notices problems
