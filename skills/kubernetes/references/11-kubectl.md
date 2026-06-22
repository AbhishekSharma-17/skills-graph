# kubectl Commands

> Source: [kubernetes.io/docs/reference/kubectl/quick-reference](https://kubernetes.io/docs/reference/kubectl/quick-reference/)

## Table of Contents

- [Setup and Configuration](#setup-and-configuration)
- [Creating Resources](#creating-resources)
- [Viewing Resources](#viewing-resources)
- [Updating Resources](#updating-resources)
- [Deleting Resources](#deleting-resources)
- [Debugging](#debugging)
- [Cluster Operations](#cluster-operations)
- [Output Formatting](#output-formatting)
- [JSONPath](#jsonpath)
- [Common Pitfalls](#common-pitfalls)

---

## Setup and Configuration

### Autocomplete

```bash
# Bash
source <(kubectl completion bash)
echo 'source <(kubectl completion bash)' >> ~/.bashrc

# Zsh
source <(kubectl completion zsh)
echo '[[ $commands[kubectl] ]] && source <(kubectl completion zsh)' >> ~/.zshrc

# Alias
alias k=kubectl
complete -o default -F __start_kubectl k
```

### Context and Namespace

```bash
# View kubeconfig
kubectl config view
kubectl config view --minify    # Current context only

# List contexts
kubectl config get-contexts

# Switch context
kubectl config use-context production

# Set default namespace
kubectl config set-context --current --namespace=staging

# View current context
kubectl config current-context
```

### Multiple Kubeconfigs

```bash
# Merge kubeconfigs
export KUBECONFIG=~/.kube/config:~/.kube/config-production

# Use specific kubeconfig
kubectl --kubeconfig=/path/to/config get pods

# Per-command context
kubectl get pods --context=production
```

---

## Creating Resources

```bash
# From file
kubectl apply -f manifest.yaml
kubectl apply -f dir/                    # All files in directory
kubectl apply -f https://example.com/manifest.yaml

# Imperative creation
kubectl create deployment nginx --image=nginx:1.26 --replicas=3
kubectl create service clusterip nginx --tcp=80:8080
kubectl create configmap app-config --from-literal=key=value
kubectl create secret generic db-pass --from-literal=password=secret
kubectl create namespace staging
kubectl create job test --image=busybox -- echo "Hello"
kubectl create cronjob backup --image=backup:1.0 --schedule="0 2 * * *" -- /backup.sh

# Dry run (preview without applying)
kubectl apply -f manifest.yaml --dry-run=client
kubectl apply -f manifest.yaml --dry-run=server    # Server-side validation

# Diff (show changes before applying)
kubectl diff -f manifest.yaml

# Generate YAML without creating
kubectl create deployment nginx --image=nginx --dry-run=client -o yaml > deployment.yaml

# Explain resource fields
kubectl explain deployment.spec.strategy
kubectl explain pod.spec.containers.resources
```

---

## Viewing Resources

```bash
# List resources
kubectl get pods
kubectl get pods -o wide                 # Extra details (node, IP)
kubectl get pods -A                      # All namespaces
kubectl get pods --show-labels
kubectl get all                          # Pods, services, deployments, etc.

# Filter by label
kubectl get pods -l app=web
kubectl get pods -l 'env in (production,staging)'
kubectl get pods -l '!canary'

# Filter by field
kubectl get pods --field-selector=status.phase=Running
kubectl get pods --field-selector=spec.nodeName=worker-1

# Sort
kubectl get pods --sort-by=.metadata.creationTimestamp
kubectl get pods --sort-by=.status.containerStatuses[0].restartCount

# Describe (detailed info including events)
kubectl describe pod web-abc123
kubectl describe node worker-1
kubectl describe svc web-service

# YAML/JSON output
kubectl get pod web-abc123 -o yaml
kubectl get pod web-abc123 -o json

# Watch for changes
kubectl get pods -w
```

### Resource Shorthands

| Short | Full |
|-------|------|
| `po` | pods |
| `svc` | services |
| `deploy` | deployments |
| `ds` | daemonsets |
| `sts` | statefulsets |
| `rs` | replicasets |
| `cm` | configmaps |
| `ns` | namespaces |
| `no` | nodes |
| `pv` | persistentvolumes |
| `pvc` | persistentvolumeclaims |
| `ing` | ingresses |
| `sa` | serviceaccounts |
| `hpa` | horizontalpodautoscalers |
| `netpol` | networkpolicies |
| `sc` | storageclasses |
| `ep` | endpoints |
| `cj` | cronjobs |

---

## Updating Resources

```bash
# Edit in editor
kubectl edit deployment/web-app

# Set image
kubectl set image deployment/web-app web=myapp:2.0

# Set environment variable
kubectl set env deployment/web-app LOG_LEVEL=debug

# Set resources
kubectl set resources deployment/web-app -c=web \
  --requests=cpu=200m,memory=256Mi \
  --limits=cpu=500m,memory=512Mi

# Patch (strategic merge)
kubectl patch deployment web-app -p '{"spec":{"replicas":5}}'

# Patch (JSON patch)
kubectl patch deployment web-app --type='json' \
  -p='[{"op":"replace","path":"/spec/replicas","value":5}]'

# Scale
kubectl scale deployment/web-app --replicas=10

# Rollout management
kubectl rollout status deployment/web-app
kubectl rollout history deployment/web-app
kubectl rollout undo deployment/web-app
kubectl rollout undo deployment/web-app --to-revision=3
kubectl rollout restart deployment/web-app
kubectl rollout pause deployment/web-app
kubectl rollout resume deployment/web-app

# Label
kubectl label pod web-abc123 env=production
kubectl label pod web-abc123 env-                # Remove label

# Annotate
kubectl annotate pod web-abc123 description="Web server"
kubectl annotate pod web-abc123 description-     # Remove annotation

# Taint node
kubectl taint nodes worker-1 dedicated=ml:NoSchedule
kubectl taint nodes worker-1 dedicated:NoSchedule-    # Remove taint
```

---

## Deleting Resources

```bash
# Delete by name
kubectl delete pod web-abc123
kubectl delete deployment web-app
kubectl delete svc,deploy -l app=web    # By label

# Delete from file
kubectl delete -f manifest.yaml

# Delete all pods in namespace
kubectl delete pods --all -n staging

# Force delete (stuck pods)
kubectl delete pod web-abc123 --grace-period=0 --force

# Delete namespace (deletes everything inside)
kubectl delete namespace staging
```

---

## Debugging

```bash
# Logs
kubectl logs pod/web-abc123
kubectl logs pod/web-abc123 -c sidecar   # Specific container
kubectl logs pod/web-abc123 --previous   # Previous crash
kubectl logs -f pod/web-abc123           # Stream
kubectl logs -l app=web --all-containers # All pods with label

# Exec
kubectl exec -it pod/web-abc123 -- /bin/sh
kubectl exec pod/web-abc123 -- env       # Run command
kubectl exec pod/web-abc123 -c db -- psql -U postgres

# Port forward
kubectl port-forward pod/web-abc123 8080:8080
kubectl port-forward svc/web-service 8080:80
kubectl port-forward deploy/web-app 8080:8080

# Debug
kubectl debug pod/web-abc123 -it --image=nicolaka/netshoot
kubectl debug node/worker-1 -it --image=ubuntu

# Copy files
kubectl cp web-abc123:/var/log/app.log ./app.log
kubectl cp ./data.json web-abc123:/tmp/data.json

# Run temporary pod
kubectl run test --image=busybox --rm -it -- sh
kubectl run curl --image=curlimages/curl --rm -it -- curl http://web-service
```

---

## Cluster Operations

```bash
# Cluster info
kubectl cluster-info
kubectl version

# Node management
kubectl get nodes -o wide
kubectl cordon worker-1                    # Mark unschedulable
kubectl uncordon worker-1                  # Mark schedulable
kubectl drain worker-1 --ignore-daemonsets --delete-emptydir-data

# API resources
kubectl api-resources
kubectl api-resources --namespaced=true
kubectl api-versions

# Check permissions
kubectl auth can-i create deployments
kubectl auth can-i delete pods --as jane
kubectl auth who-can create pods
```

---

## Output Formatting

```bash
# Wide output
kubectl get pods -o wide

# YAML
kubectl get pod web-abc123 -o yaml

# JSON
kubectl get pod web-abc123 -o json

# Name only
kubectl get pods -o name

# Custom columns
kubectl get pods -o custom-columns=NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName

# Go template
kubectl get pods -o go-template='{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}'
```

---

## JSONPath

```bash
# Pod IPs
kubectl get pods -o jsonpath='{.items[*].status.podIP}'

# Node names
kubectl get nodes -o jsonpath='{.items[*].metadata.name}'

# Container images
kubectl get pods -o jsonpath='{.items[*].spec.containers[*].image}'

# Range with formatting
kubectl get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.phase}{"\n"}{end}'

# Conditional
kubectl get nodes -o jsonpath='{.items[?(@.status.conditions[?(@.type=="Ready")].status=="True")].metadata.name}'

# Sort
kubectl get pods --sort-by='.status.containerStatuses[0].restartCount' \
  -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.containerStatuses[0].restartCount}{"\n"}{end}'
```

---

## Common Pitfalls

1. **Wrong namespace** — Always check `--namespace` or set default with `config set-context`
2. **Editing managed resources** — `kubectl edit` on Helm-managed resources causes drift; use `helm upgrade`
3. **Force delete without investigation** — Diagnose why the pod is stuck before force-deleting
4. **`kubectl apply` vs `create`** — `apply` is declarative and idempotent; `create` fails if resource exists
5. **Missing `-w` flag** — Use `kubectl get pods -w` to watch status changes instead of polling
6. **Not using `--dry-run=server`** — Server-side dry run catches validation errors that client-side misses
