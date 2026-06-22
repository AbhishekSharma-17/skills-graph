# Storage

> Source: [kubernetes.io/docs/concepts/storage](https://kubernetes.io/docs/concepts/storage/)

## Table of Contents

- [Volume Types](#volume-types)
- [PersistentVolumes](#persistentvolumes)
- [PersistentVolumeClaims](#persistentvolumeclaims)
- [StorageClasses](#storageclasses)
- [Volume Lifecycle](#volume-lifecycle)
- [Volume Snapshots](#volume-snapshots)
- [Volume Cloning](#volume-cloning)
- [Common Pitfalls](#common-pitfalls)

---

## Volume Types

### emptyDir

Temporary directory that exists for the Pod's lifetime. Shared between containers.

```yaml
spec:
  containers:
  - name: app
    volumeMounts:
    - name: cache
      mountPath: /cache
  - name: sidecar
    volumeMounts:
    - name: cache
      mountPath: /cache
  volumes:
  - name: cache
    emptyDir:
      sizeLimit: 500Mi
      medium: Memory    # Use RAM-backed tmpfs (faster, counts against memory limit)
```

### hostPath

Mounts a file or directory from the host node's filesystem. Use with caution — ties Pod to a specific node.

```yaml
volumes:
- name: docker-sock
  hostPath:
    path: /var/run/docker.sock
    type: Socket        # File, Directory, DirectoryOrCreate, FileOrCreate, Socket, CharDevice, BlockDevice
```

### configMap and secret

Mount ConfigMap/Secret data as files:

```yaml
volumes:
- name: config
  configMap:
    name: app-config
    items:
    - key: nginx.conf
      path: nginx.conf
- name: certs
  secret:
    secretName: tls-secret
    defaultMode: 0400
```

### projected

Combine multiple volume sources into a single directory:

```yaml
volumes:
- name: all-in-one
  projected:
    sources:
    - configMap:
        name: app-config
    - secret:
        name: app-secret
    - downwardAPI:
        items:
        - path: labels
          fieldRef:
            fieldPath: metadata.labels
    - serviceAccountToken:
        path: token
        expirationSeconds: 3600
```

### downwardAPI

Exposes Pod and container metadata as files:

```yaml
volumes:
- name: podinfo
  downwardAPI:
    items:
    - path: labels
      fieldRef:
        fieldPath: metadata.labels
    - path: cpu-limit
      resourceFieldRef:
        containerName: app
        resource: limits.cpu
```

---

## PersistentVolumes

Cluster-level storage resource provisioned by an admin or dynamically via StorageClasses.

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: nfs-pv
  labels:
    type: nfs
spec:
  capacity:
    storage: 100Gi
  accessModes:
  - ReadWriteMany
  persistentVolumeReclaimPolicy: Retain
  storageClassName: nfs
  mountOptions:
  - hard
  - nfsvers=4.1
  nfs:
    server: nfs.example.com
    path: /exports/data
```

### Access Modes

| Mode | Abbreviation | Description |
|------|-------------|-------------|
| `ReadWriteOnce` | RWO | Read-write by a single node |
| `ReadOnlyMany` | ROX | Read-only by many nodes |
| `ReadWriteMany` | RWX | Read-write by many nodes |
| `ReadWriteOncePod` | RWOP | Read-write by a single pod |

### Reclaim Policies

| Policy | Behavior |
|--------|----------|
| `Retain` | PV preserved after PVC deletion; manual cleanup needed |
| `Delete` | PV and underlying storage deleted automatically |

### Volume Modes

| Mode | Description |
|------|-------------|
| `Filesystem` | Directory mount (default) |
| `Block` | Raw block device |

---

## PersistentVolumeClaims

User's request for storage. Binds to a matching PV.

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-data
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 20Gi
  selector:                    # Optional: bind to specific PV
    matchLabels:
      type: nfs
```

### Using PVCs in Pods

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: myapp:1.0
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: app-data
```

### Expanding PVCs

Requires `allowVolumeExpansion: true` in the StorageClass.

```bash
kubectl patch pvc app-data -p '{"spec":{"resources":{"requests":{"storage":"50Gi"}}}}'
```

---

## StorageClasses

Define different storage tiers for dynamic provisioning.

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
provisioner: pd.csi.storage.gke.io
parameters:
  type: pd-ssd
  replication-type: regional-pd
allowVolumeExpansion: true
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
mountOptions:
- debug
```

### Volume Binding Modes

| Mode | Description |
|------|-------------|
| `Immediate` | PV provisioned immediately when PVC is created |
| `WaitForFirstConsumer` | PV provisioned when Pod using PVC is scheduled (preferred for topology-aware storage) |

### Common Provisioners

| Provisioner | Cloud Provider |
|------------|----------------|
| `pd.csi.storage.gke.io` | Google Cloud |
| `ebs.csi.aws.com` | AWS |
| `disk.csi.azure.com` | Azure |
| `csi.vsphere.vmware.com` | vSphere |
| `rancher.io/local-path` | Local (k3s, kind) |

```bash
# List StorageClasses
kubectl get storageclass

# Set default StorageClass
kubectl patch storageclass fast-ssd -p \
  '{"metadata":{"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
```

---

## Volume Lifecycle

```
                 Provisioning
                      │
              ┌───────┴────────┐
              │ Static  │ Dynamic│
              └───────┬────────┘
                      │
                   Binding
                      │
                    Using
                      │
                  Reclaiming
                      │
              ┌───────┴────────┐
              │ Retain │ Delete │
              └────────────────┘
```

### Storage Object in Use Protection

Kubernetes prevents accidental deletion of PVCs in use by Pods and PVs bound to PVCs. Objects show `Terminating` status with a protection finalizer until safe to delete.

---

## Volume Snapshots

Create point-in-time copies of PVCs for backup/restore.

```yaml
# Create snapshot
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: db-snapshot
spec:
  volumeSnapshotClassName: csi-snapshotter
  source:
    persistentVolumeClaimName: db-data

---
# Restore from snapshot
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: db-restored
spec:
  dataSource:
    name: db-snapshot
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
  accessModes:
  - ReadWriteOnce
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 20Gi
```

---

## Volume Cloning

Clone data from an existing PVC:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: cloned-data
spec:
  dataSource:
    name: original-data
    kind: PersistentVolumeClaim
  accessModes:
  - ReadWriteOnce
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 20Gi
```

---

## Common Pitfalls

1. **Wrong access mode for multi-pod workloads** — Most cloud disks only support RWO; use a shared filesystem for RWX
2. **`Immediate` binding with topology constraints** — PV may be provisioned in wrong zone; use `WaitForFirstConsumer`
3. **Forgetting `allowVolumeExpansion`** — Can't resize PVCs without this on the StorageClass
4. **Using `hostPath` in production** — Ties pods to specific nodes; use PVs instead
5. **Not setting `reclaimPolicy`** — Default for dynamic provisioning is `Delete`; data is lost when PVC is deleted
6. **PVC stuck in Pending** — No matching PV exists; check StorageClass, access modes, and capacity
7. **StatefulSet PVC not cleaned up** — `volumeClaimTemplates` PVCs persist after StatefulSet deletion; delete manually
