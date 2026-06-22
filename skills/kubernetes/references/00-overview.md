# Kubernetes Overview & Architecture

> Source: [kubernetes.io/docs/concepts/overview](https://kubernetes.io/docs/concepts/overview/)

## Table of Contents

- [What Is Kubernetes](#what-is-kubernetes)
- [Architecture](#architecture)
- [Control Plane Components](#control-plane-components)
- [Node Components](#node-components)
- [Kubernetes Objects](#kubernetes-objects)
- [Namespaces](#namespaces)
- [Labels and Selectors](#labels-and-selectors)
- [Installation Options](#installation-options)
- [Cluster Setup](#cluster-setup)
- [Common Pitfalls](#common-pitfalls)

---

## What Is Kubernetes

Kubernetes (K8s) is an open-source container orchestration platform for automating deployment, scaling, and management of containerized applications. It originated from 15+ years of Google's production experience (Borg/Omega).

### Core Capabilities

| Capability | Description |
|-----------|-------------|
| **Service discovery** | DNS-based exposure and automatic load balancing |
| **Storage orchestration** | Automatic mounting of local, cloud, or network storage |
| **Automated rollouts** | Controlled state transitions with rollback support |
| **Bin packing** | Optimal resource utilization across nodes |
| **Self-healing** | Container restart, replacement, health checking |
| **Secret management** | Secure storage of passwords, tokens, keys |
| **Horizontal scaling** | Manual or automatic pod replication |
| **Batch execution** | Job and cron workload management |

### What Kubernetes Is Not

- Not a PaaS — operates at container level, default solutions are optional
- Not a build system — doesn't compile or deploy source code
- Not a middleware provider — no built-in databases or caches (they can run on K8s)
- Not monolithic — provides composable building blocks

---

## Architecture

A Kubernetes cluster consists of a **control plane** and one or more **worker nodes**.

```
┌─────────────────────────────────────────────────────┐
│                   Control Plane                      │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────┐ │
│  │ API      │  │ Controller   │  │  Scheduler    │ │
│  │ Server   │  │ Manager      │  │               │ │
│  └──────────┘  └──────────────┘  └───────────────┘ │
│  ┌──────────────────────────────────────────────┐   │
│  │                   etcd                        │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
         │                    │                │
   ┌─────┴─────┐       ┌─────┴─────┐    ┌─────┴─────┐
   │  Node 1   │       │  Node 2   │    │  Node 3   │
   │ ┌───────┐ │       │ ┌───────┐ │    │ ┌───────┐ │
   │ │kubelet│ │       │ │kubelet│ │    │ │kubelet│ │
   │ ├───────┤ │       │ ├───────┤ │    │ ├───────┤ │
   │ │kube-  │ │       │ │kube-  │ │    │ │kube-  │ │
   │ │proxy  │ │       │ │proxy  │ │    │ │proxy  │ │
   │ ├───────┤ │       │ ├───────┤ │    │ ├───────┤ │
   │ │ Pods  │ │       │ │ Pods  │ │    │ │ Pods  │ │
   │ └───────┘ │       │ └───────┘ │    │ └───────┘ │
   └───────────┘       └───────────┘    └───────────┘
```

---

## Control Plane Components

### kube-apiserver

The REST API frontend for the cluster. All `kubectl` commands and internal components communicate through it.

```bash
# Check API server health
kubectl get --raw /healthz

# List available API resources
kubectl api-resources

# List API versions
kubectl api-versions
```

### etcd

Distributed key-value store that holds all cluster state. Only the API server communicates directly with etcd.

```bash
# Check etcd health (on control plane node)
ETCDCTL_API=3 etcdctl endpoint health

# Backup etcd
ETCDCTL_API=3 etcdctl snapshot save /backup/etcd-snapshot.db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key
```

### kube-scheduler

Assigns newly created pods to nodes based on resource requirements, affinity rules, taints/tolerations, and topology constraints.

### kube-controller-manager

Runs controller processes including:
- **Node controller** — monitors node health
- **Deployment controller** — manages ReplicaSets
- **Job controller** — manages batch workloads
- **EndpointSlice controller** — populates service endpoints
- **ServiceAccount controller** — creates default service accounts

### cloud-controller-manager

Integrates with cloud provider APIs for load balancers, storage volumes, and node management (only in cloud environments).

---

## Node Components

### kubelet

Agent on each node that ensures containers described in PodSpecs are running and healthy. It does not manage containers not created by Kubernetes.

### kube-proxy

Network proxy on each node implementing Kubernetes Service abstraction. Maintains network rules using iptables, IPVS, or nftables.

### Container Runtime

Software responsible for running containers. Kubernetes supports any runtime implementing the Container Runtime Interface (CRI):
- **containerd** (most common)
- **CRI-O**
- **Docker Engine** (via cri-dockerd adapter)

---

## Kubernetes Objects

Every Kubernetes object has a spec (desired state) and status (current state). Objects are defined declaratively in YAML:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  namespace: default
  labels:
    app: nginx
  annotations:
    description: "Web server deployment"
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.26
```

### Required Fields

| Field | Description |
|-------|-------------|
| `apiVersion` | API version (e.g., `v1`, `apps/v1`, `batch/v1`) |
| `kind` | Object type (e.g., `Pod`, `Deployment`, `Service`) |
| `metadata` | Name, namespace, labels, annotations |
| `spec` | Desired state (structure varies by kind) |

### Common API Groups

| Group | Resources |
|-------|-----------|
| `v1` (core) | Pod, Service, ConfigMap, Secret, PersistentVolume, Namespace |
| `apps/v1` | Deployment, StatefulSet, DaemonSet, ReplicaSet |
| `batch/v1` | Job, CronJob |
| `networking.k8s.io/v1` | Ingress, NetworkPolicy, IngressClass |
| `rbac.authorization.k8s.io/v1` | Role, ClusterRole, RoleBinding, ClusterRoleBinding |
| `storage.k8s.io/v1` | StorageClass, CSIDriver, VolumeAttachment |
| `autoscaling/v2` | HorizontalPodAutoscaler |

---

## Namespaces

Namespaces provide logical isolation within a cluster. They scope names — two objects of the same kind can have the same name in different namespaces.

```bash
# List namespaces
kubectl get namespaces

# Create namespace
kubectl create namespace staging

# Set default namespace for context
kubectl config set-context --current --namespace=staging
```

### Default Namespaces

| Namespace | Purpose |
|-----------|---------|
| `default` | Objects with no other namespace |
| `kube-system` | System components (API server, scheduler, CoreDNS) |
| `kube-public` | Publicly readable data (e.g., cluster-info ConfigMap) |
| `kube-node-lease` | Node heartbeat leases |

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    env: production
```

---

## Labels and Selectors

Labels are key-value pairs attached to objects for identification and grouping.

```yaml
metadata:
  labels:
    app: web-server
    environment: production
    tier: frontend
    version: v2.1.0
```

### Selector Types

**Equality-based:**
```bash
kubectl get pods -l environment=production
kubectl get pods -l tier!=frontend
```

**Set-based:**
```bash
kubectl get pods -l 'environment in (production,staging)'
kubectl get pods -l 'tier notin (frontend)'
kubectl get pods -l 'partition'          # key exists
kubectl get pods -l '!partition'         # key does not exist
```

### Recommended Labels

```yaml
metadata:
  labels:
    app.kubernetes.io/name: mysql
    app.kubernetes.io/instance: mysql-prod
    app.kubernetes.io/version: "8.0"
    app.kubernetes.io/component: database
    app.kubernetes.io/part-of: ecommerce
    app.kubernetes.io/managed-by: helm
```

---

## Installation Options

### Local Development

| Tool | Description | Best For |
|------|-------------|----------|
| **minikube** | Single-node cluster in VM/container | Learning, local development |
| **kind** | Kubernetes in Docker containers | CI/CD pipelines, testing |
| **k3s** | Lightweight distribution | Edge, IoT, resource-constrained |
| **Docker Desktop** | Built-in K8s with Docker | macOS/Windows developers |

```bash
# minikube
brew install minikube
minikube start --cpus=4 --memory=8192 --driver=docker
minikube dashboard

# kind
brew install kind
kind create cluster --name dev
kind create cluster --config kind-config.yaml

# k3s (Linux)
curl -sfL https://get.k3s.io | sh -
```

### Production

| Tool | Description |
|------|-------------|
| **kubeadm** | Official cluster bootstrapping tool |
| **EKS** | Amazon Elastic Kubernetes Service |
| **GKE** | Google Kubernetes Engine |
| **AKS** | Azure Kubernetes Service |
| **kOps** | Production-grade cluster management on AWS/GCE |

```bash
# kubeadm init (control plane)
sudo kubeadm init --pod-network-cidr=10.244.0.0/16

# kubeadm join (worker node)
sudo kubeadm join <control-plane-ip>:6443 \
  --token <token> \
  --discovery-token-ca-cert-hash sha256:<hash>
```

---

## Cluster Setup

### kubeconfig

```bash
# View config
kubectl config view

# List contexts
kubectl config get-contexts

# Switch context
kubectl config use-context production-cluster

# Set namespace for context
kubectl config set-context --current --namespace=staging
```

### Verify Cluster

```bash
# Cluster info
kubectl cluster-info

# Node status
kubectl get nodes -o wide

# System pods
kubectl get pods -n kube-system

# Component statuses
kubectl get componentstatuses
```

---

## Common Pitfalls

1. **Creating pods directly** — Always use Deployments/StatefulSets for self-healing and scaling
2. **No resource requests/limits** — Pods without resource definitions get BestEffort QoS and are evicted first
3. **Using `latest` tag** — Always pin image versions for reproducibility
4. **Ignoring namespaces** — Use namespaces to isolate workloads and apply resource quotas
5. **Skipping health probes** — Without liveness/readiness probes, K8s can't detect unhealthy containers
6. **Running as root** — Set `runAsNonRoot: true` in security contexts
7. **No pod disruption budgets** — Without PDBs, cluster operations can take down all replicas
8. **Storing secrets in ConfigMaps** — Use Secrets with encryption at rest for sensitive data
