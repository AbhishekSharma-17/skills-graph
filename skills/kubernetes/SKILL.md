---
name: kubernetes
description: "Kubernetes container orchestration — pods, deployments, services, networking, storage, configuration, security, scaling, Helm, and kubectl. MANDATORY TRIGGERS: kubernetes, k8s, kubectl, kubelet, kube-apiserver, kube-proxy, kubeadm, pod, deployment, statefulset, daemonset, replicaset, service, ingress, configmap, secret, persistentvolume, PVC, HPA, RBAC, helm, taint, toleration, node affinity, namespace, kustomize, container orchestration. Also trigger when user wants to deploy containers, manage microservices, set up container networking, configure auto-scaling, implement rolling updates, manage cluster security, or orchestrate containerized workloads. When in doubt about whether to use this skill for container orchestration tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["kubernetes", "k8s", "containers", "orchestration", "devops", "docker", "pods", "deployments", "services", "helm", "kubectl"]
---

# Kubernetes — Skill Router

> The open-source container orchestration platform for automating deployment, scaling, and management of containerized applications.

**Source:** [kubernetes.io/docs](https://kubernetes.io/docs/home/) | **Version:** `1.36` | **GitHub:** 115K+ stars

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Architecture** | `references/00-overview.md` | Cluster components, control plane, nodes, installation, minikube |
| **Pods & Containers** | `references/01-pods-containers.md` | Pod lifecycle, init containers, sidecars, probes, multi-container patterns |
| **Workloads** | `references/02-workloads.md` | Deployments, ReplicaSets, StatefulSets, DaemonSets, Jobs, CronJobs |
| **Services & Networking** | `references/03-services-networking.md` | Service types, DNS, Ingress, Gateway API, Network Policies |
| **Storage** | `references/04-storage.md` | Volumes, PersistentVolumes, PVCs, StorageClasses, snapshots |
| **Configuration** | `references/05-configuration.md` | ConfigMaps, Secrets, resource limits, environment variables |
| **Scheduling** | `references/06-scheduling.md` | Node selectors, affinity, taints, tolerations, topology spread |
| **Security & RBAC** | `references/07-security-rbac.md` | Roles, RoleBindings, ServiceAccounts, Pod Security, security contexts |
| **Scaling & Autoscaling** | `references/08-scaling-autoscaling.md` | HPA, VPA, Cluster Autoscaler, scaling policies, metrics |
| **Helm** | `references/09-helm.md` | Charts, repositories, values, templates, releases, hooks |
| **Observability** | `references/10-observability.md` | Metrics Server, logging, monitoring, debugging, kubectl top |
| **kubectl Commands** | `references/11-kubectl.md` | CLI reference, contexts, output formats, common operations |
| **Production Best Practices** | `references/12-production.md` | HA clusters, resource quotas, namespaces, upgrades, disaster recovery |

## Installation

```bash
# kubectl (macOS)
brew install kubectl

# kubectl (Linux)
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# minikube (local dev cluster)
brew install minikube && minikube start

# kind (Kubernetes in Docker)
brew install kind && kind create cluster

# Helm
brew install helm
```

## Quick Reference

- [Kubernetes Documentation](https://kubernetes.io/docs/home/)
- [API Reference](https://kubernetes.io/docs/reference/kubernetes-api/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/quick-reference/)
- [GitHub](https://github.com/kubernetes/kubernetes)
- [Helm Documentation](https://helm.sh/docs/)
