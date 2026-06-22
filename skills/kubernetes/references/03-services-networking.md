# Services & Networking

> Source: [kubernetes.io/docs/concepts/services-networking](https://kubernetes.io/docs/concepts/services-networking/)

## Table of Contents

- [Services](#services)
- [Service Types](#service-types)
- [Service Discovery](#service-discovery)
- [Ingress](#ingress)
- [Gateway API](#gateway-api)
- [Network Policies](#network-policies)
- [DNS](#dns)
- [Common Pitfalls](#common-pitfalls)

---

## Services

A Service provides a stable endpoint for a set of Pods, decoupling clients from individual Pod IPs.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  selector:
    app: web-app
  ports:
  - name: http
    protocol: TCP
    port: 80
    targetPort: 8080
  type: ClusterIP
```

### Multi-Port Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: app-service
spec:
  selector:
    app: myapp
  ports:
  - name: http
    port: 80
    targetPort: 8080
  - name: https
    port: 443
    targetPort: 8443
  - name: metrics
    port: 9090
    targetPort: 9090
```

### Named Ports

Reference container port names instead of numbers:

```yaml
# In the Pod
ports:
- containerPort: 8080
  name: http-web

# In the Service
ports:
- port: 80
  targetPort: http-web    # References pod port name
```

---

## Service Types

### ClusterIP (Default)

Internal-only access within the cluster.

```yaml
spec:
  type: ClusterIP
  selector:
    app: backend
  ports:
  - port: 80
    targetPort: 8080
```

### NodePort

Exposes the Service on each node's IP at a static port (30000–32767).

```yaml
spec:
  type: NodePort
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 8080
    nodePort: 30080       # Optional; auto-assigned if omitted
```

Access: `http://<any-node-ip>:30080`

### LoadBalancer

Provisions an external load balancer (cloud providers only).

```yaml
spec:
  type: LoadBalancer
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 8080
  loadBalancerSourceRanges:    # Restrict access by IP range
  - "203.0.113.0/24"
```

### ExternalName

Maps a Service to an external DNS name (no proxy, returns CNAME).

```yaml
spec:
  type: ExternalName
  externalName: db.external-provider.com
```

### Headless Service

No cluster IP — DNS returns individual Pod IPs. Required for StatefulSets.

```yaml
spec:
  clusterIP: None
  selector:
    app: database
  ports:
  - port: 5432
```

### Service Without Selector

For external services outside the cluster:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: external-db
spec:
  ports:
  - port: 5432
---
apiVersion: discovery.k8s.io/v1
kind: EndpointSlice
metadata:
  name: external-db-1
  labels:
    kubernetes.io/service-name: external-db
addressType: IPv4
ports:
- name: ""
  port: 5432
  protocol: TCP
endpoints:
- addresses:
  - "10.240.0.50"
```

---

## Service Discovery

### DNS (Preferred)

Services are accessible via DNS: `<service>.<namespace>.svc.cluster.local`

```bash
# Within same namespace
curl http://web-service

# Cross-namespace
curl http://web-service.production.svc.cluster.local

# Headless service (returns individual pod IPs)
nslookup postgres.default.svc.cluster.local
# Returns: postgres-0, postgres-1, postgres-2 IPs
```

### Environment Variables

Kubernetes injects env vars for each Service:

```bash
WEB_SERVICE_SERVICE_HOST=10.0.0.11
WEB_SERVICE_SERVICE_PORT=80
```

### Session Affinity

```yaml
spec:
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800
```

### Traffic Policies

```yaml
spec:
  internalTrafficPolicy: Local   # Only route to local node pods
  externalTrafficPolicy: Local   # Preserve source IP (LoadBalancer/NodePort)
```

---

## Ingress

Manages external HTTP/HTTPS access with routing rules, TLS termination, and virtual hosting.

> The Ingress API is stable but frozen. For new features, use Gateway API.

### Prerequisites

An **Ingress Controller** must be installed (e.g., NGINX, Traefik, HAProxy).

```bash
# Install NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.12.0/deploy/static/provider/cloud/deploy.yaml
```

### Basic Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
```

### TLS Termination

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: tls-ingress
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - app.example.com
    secretName: app-tls-secret
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
```

```bash
# Create TLS secret
kubectl create secret tls app-tls-secret \
  --cert=tls.crt --key=tls.key
```

### Virtual Hosting

```yaml
spec:
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
  - host: web.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
```

### Path Types

| Type | Behavior |
|------|----------|
| `Exact` | Exact string match (`/foo` matches `/foo`, not `/foo/bar`) |
| `Prefix` | URL prefix match (`/foo` matches `/foo` and `/foo/bar`) |
| `ImplementationSpecific` | Controller-dependent matching |

---

## Gateway API

The successor to Ingress, supporting TCP/UDP, traffic splitting, and more.

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: main-gateway
spec:
  gatewayClassName: nginx
  listeners:
  - name: http
    port: 80
    protocol: HTTP
---
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: app-route
spec:
  parentRefs:
  - name: main-gateway
  hostnames:
  - "app.example.com"
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /api
    backendRefs:
    - name: api-service
      port: 80
      weight: 90
    - name: api-service-canary
      port: 80
      weight: 10
```

---

## Network Policies

Control traffic flow between Pods at the network level. Requires a CNI plugin that supports NetworkPolicy (Calico, Cilium, Weave Net).

### Deny All Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-ingress
spec:
  podSelector: {}
  policyTypes:
  - Ingress
```

### Allow Specific Traffic

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-policy
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: web
    - namespaceSelector:
        matchLabels:
          env: production
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - protocol: TCP
      port: 5432
  - to:                         # Allow DNS
    - namespaceSelector: {}
    ports:
    - protocol: UDP
      port: 53
```

---

## DNS

CoreDNS runs as a Deployment in `kube-system` and provides DNS for Services and Pods.

### DNS Records

| Record Type | Format | Example |
|------------|--------|---------|
| **Service** | `<svc>.<ns>.svc.cluster.local` | `web.default.svc.cluster.local` |
| **Pod** | `<pod-ip-dashed>.<ns>.pod.cluster.local` | `10-244-0-5.default.pod.cluster.local` |
| **StatefulSet Pod** | `<pod-name>.<svc>.<ns>.svc.cluster.local` | `postgres-0.postgres.default.svc.cluster.local` |

### Custom DNS Config

```yaml
spec:
  dnsPolicy: "None"
  dnsConfig:
    nameservers:
    - 8.8.8.8
    searches:
    - my-namespace.svc.cluster.local
    options:
    - name: ndots
      value: "5"
```

---

## Common Pitfalls

1. **No Ingress Controller installed** — Creating an Ingress resource without a controller has no effect
2. **NodePort conflicts** — Two services can't use the same NodePort
3. **Missing DNS egress in NetworkPolicy** — Pods can't resolve DNS without UDP/53 egress rule
4. **ExternalName with TLS** — CNAME redirect may break TLS certificate validation
5. **LoadBalancer without source ranges** — Exposes service to the entire internet
6. **Wrong targetPort** — Service port != container port; verify with `kubectl describe svc`
7. **Session affinity with multiple replicas** — `ClientIP` affinity may cause uneven load distribution
