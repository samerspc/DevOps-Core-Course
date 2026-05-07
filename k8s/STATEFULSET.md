# Lab 15 — StatefulSet & Persistent Storage

This chart can run **`app_python` as a StatefulSet** instead of an Argo Rollout: stable pod names (`…-0`, `…-1`, …), a **headless Service** for DNS, and **one RWO PersistentVolumeClaim per pod** via `volumeClaimTemplates`.

## StatefulSet overview (vs Deployment / Rollout)

| Aspect | Deployment / Rollout | StatefulSet |
|--------|---------------------|-------------|
| Pod naming | Random suffix | Stable ordinal (`*-0`, `*-1`, …) |
| Storage | Typically one PVC or ephemeral | PVC per replica from `volumeClaimTemplates` |
| Scale order | Any | Ordered by default (`OrderedReady`) |
| Stable network DNS | Via Service only | Via headless Service: `<pod>.<headless>.<ns>.svc.cluster.local` |

**When to choose StatefulSet:** workloads that require stable identity and/or dedicated disks per instance (many databases, Kafka, etc.). Progressive delivery for **stateless** apps stays on Rollouts.

## What was added to the Helm chart

- `templates/statefulset.yaml` — StatefulSet (+ `volumeClaimTemplates` when `persistence.enabled`)
- `templates/service-headless.yaml` — Service with `clusterIP: None`, same selectors as workloads
- `templates/pvc.yaml` — renders the shared Lab 12 PVC **only when** `statefulset.enabled` is **false** (StatefulSet PVCs come from templates)
- `values.yaml` — `statefulset.*` toggle and default `RollingUpdate` / `partition: 0`
- `values-lab15.yaml` — turns off Rollout, enables StatefulSet, `replicaCount: 3`, ClusterIP Service, local-ish image defaults
- `values-lab15-bonus-update.yaml` — layered override for partitioned rolling (`partition: 2`)

Rollout manifests stay in the repo for reference; do **not** enable Rollout and StatefulSet together—they share selectors.

### Deploy (example with Kind)

```bash
docker build -t devops-course/app_python:lab15 ../../app_python
kind load docker-image devops-course/app_python:lab15 --name lab14

cd app-python
helm dependency update
helm upgrade --install lab15-app . -f values-lab15.yaml --namespace default --wait
```

## Resource verification (`kubectl get po,sts,svc,pvc`)

Example from cluster `kind-lab14`, release `lab15-app`:

```
NAME                         READY   STATUS    RESTARTS   AGE
pod/lab15-app-app-python-0   1/1     Running   0          ...
pod/lab15-app-app-python-1   1/1     Running   0          ...
pod/lab15-app-app-python-2   1/1     Running   0          ...

NAME                                    READY   AGE
statefulset.apps/lab15-app-app-python   3/3     ...

NAME                                    TYPE        CLUSTER-IP      PORT(S)
service/lab15-app-app-python            ClusterIP   10.96.233.236   80/TCP
service/lab15-app-app-python-headless   ClusterIP   None            80/TCP

NAME                                                     STATUS   CAPACITY   ACCESS MODES
persistentvolumeclaim/app-data-lab15-app-app-python-0   Bound    100Mi      RWO
persistentvolumeclaim/app-data-lab15-app-app-python-1   Bound    100Mi      RWO
persistentvolumeclaim/app-data-lab15-app-app-python-2   Bound    100Mi      RWO
```

PVC names follow `<volumeClaimTemplate>-<statefulsetName>-<ordinal>`.

## Network identity — DNS resolution

Pattern:

`<stateful-pod-name>.<headless-service>.<namespace>.svc.cluster.local`

The app image does not ship `nslookup`; use Python (already in the container):

```bash
kubectl exec pod/lab15-app-app-python-0 -- python3 -c \
  "import socket; h='lab15-app-app-python-1.lab15-app-app-python-headless.default.svc.cluster.local'; print(socket.gethostbyname(h))"
```

Example output:

```
lab15-app-app-python-1.lab15-app-app-python-headless.default.svc.cluster.local -> 10.244.0.9
```

(Optional) From your shell:

```bash
kubectl port-forward pod/lab15-app-app-python-0 8080:5000
kubectl port-forward pod/lab15-app-app-python-1 8081:5000
curl -s http://127.0.0.1:8080/visits
curl -s http://127.0.0.1:8081/visits
```

## Per-pod storage — different `/visits` per pod

After sending a different number of `GET /` hits to **each pod’s own** `127.0.0.1:5000` (so traffic is not balanced), `/visits` differs per ordinal:

```
=== pod-0 /visits ===
{"visits":2,...}
=== pod-1 /visits ===
{"visits":3,...}
=== pod-2 /visits ===
{"visits":1,...}
```

The Service load-balances; to prove isolation you must hit **individual pods** (port-forward to `pod/<name>` or exec + `urllib` as above).

## Persistence — counter survives pod delete

`/data/visits` lives on the pod’s PVC. After `kubectl delete pod <statefulset>-0`, the StatefulSet recreates `…-0` and re-attaches the same claim.

Example:

```bash
kubectl exec pod/lab15-app-app-python-0 -- cat /data/visits
# 2
kubectl delete pod lab15-app-app-python-0 --wait=false
kubectl wait --for=condition=ready pod/lab15-app-app-python-0 --timeout=120s
kubectl exec pod/lab15-app-app-python-0 -- cat /data/visits
# 2
```

## Bonus — update strategies

**Partitioned rolling update** — only replicas with ordinal `≥ partition` receive the new revision first; lowering the partition rolls the rest:

```bash
helm upgrade lab15-app . -f values-lab15.yaml -f values-lab15-bonus-update.yaml
```

`values-lab15-bonus-update.yaml` sets `partition: 2` with three replicas (`0`,`1` stay on older revision until you change strategy).

**`OnDelete`** — image/spec updates apply only after you manually delete pods (useful for strict operational control):

```yaml
statefulset:
  updateStrategy:
    type: OnDelete
```

Reference: [StatefulSet update strategies](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/#update-strategies).

## Checklist (Lab 15)

- StatefulSet guarantees and comparisons documented above
- `statefulset.yaml` + headless Service + `volumeClaimTemplates`
- Per-pod PVCs verified
- DNS + isolation + persistence exercises recorded
