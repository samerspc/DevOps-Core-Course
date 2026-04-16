# Lab 12 — ConfigMaps & Persistent Volumes

This document describes the visit counter, Kubernetes ConfigMaps, PVC wiring, and the bonus ConfigMap rollout pattern for the `app-python` Helm chart.

## 1. Application changes

### Visits counter

- **File:** `app_python/app.py`
- On each **GET /** the service increments a counter stored in **`VISITS_FILE`** (default `/data/visits`).
- The file is read/written under a **threading lock**; writes use a temp file + **`os.replace`** for atomicity on POSIX systems.
- **GET /visits** returns JSON: `{"visits": <int>, "config": {...}}` (config reflects mounted JSON + env from the env ConfigMap).

### Optional mounted configuration

- **`APP_CONFIG_PATH`** (default `/config/config.json`) points at JSON merged with defaults (`appName`, `environment`, `features`).
- **Hot reload (bonus):** on each request the app checks the file **mtime**; when the kubelet refreshes the mounted ConfigMap (see below), the next request loads new values without a process restart.

### Local Docker

- **`app_python/docker-compose.yml`** builds the image, maps **`./data:/data`**, and **`./sample-config:/config:ro`** so the counter survives container restarts and config is readable at `/config/config.json`.
- **Evidence (run locally):**

```bash
cd app_python
docker compose up --build -d
curl -s http://localhost:5000/ | jq .visits
curl -s http://localhost:5000/ | jq .visits
docker compose restart
curl -s http://localhost:5000/visits | jq .
cat data/visits
```

---

## 2. ConfigMap implementation

### Chart layout

| Path | Role |
|------|------|
| `k8s/app-python/files/config.json` | Source file embedded into the file ConfigMap via Helm `.Files.Get` |
| `k8s/app-python/templates/configmap.yaml` | Two `ConfigMap` objects: file payload + env key/values |

### File ConfigMap (`*-config`)

Rendered with:

```yaml
data:
  config.json: |-
{{ .Files.Get "files/config.json" | indent 4 }}
```

The Deployment mounts the ConfigMap as a **directory** at **`/config`** (not `subPath` on a single key), so the kubelet can refresh file contents when the ConfigMap changes.

### Env ConfigMap (`*-env`)

Keys **`APP_ENV`** and **`LOG_LEVEL`** come from **`values.yaml`** (`environment`, `logLevel`). The pod uses **`envFrom` → `configMapRef`** so all keys appear as environment variables.

### Verification (cluster)

```bash
kubectl get configmap -l app.kubernetes.io/instance=<release>
kubectl exec deploy/<release>-app-python -- cat /config/config.json
kubectl exec deploy/<release>-app-python -- printenv | grep -E '^(APP_ENV|LOG_LEVEL)='
```

---

## 3. Persistent volume

### PVC template

- **`templates/pvc.yaml`**: `ReadWriteOnce`, size from **`persistence.size`**, optional **`storageClassName`** when **`persistence.storageClass`** is non-empty.
- **Note:** a single **RWO** volume can only attach to **one** node; the chart default **`replicaCount: 1`** matches that. To scale replicas, disable persistence or use a **ReadWriteMany** storage class.

### Mount

- Volume name **`app-data`** → **`mountPath: /data`**; the app writes **`/data/visits`**.

### Persistence test (evidence template)

1. Note counter: `kubectl exec <pod> -- cat /data/visits`
2. Hit the app root several times via the Service / NodePort.
3. Delete only the pod: `kubectl delete pod <pod-name> -n <ns>`
4. Wait for the new pod; **`cat /data/visits`** should match the previous value.

```bash
kubectl get pvc
kubectl describe pvc <release>-app-python-data
```

---

## 4. ConfigMap vs Secret

| Use **ConfigMap** | Use **Secret** |
|-------------------|----------------|
| App name, feature flags, log level, non-sensitive JSON | Passwords, API keys, tokens, TLS material |
| Plaintext in etcd (base64 is not encryption) | Opaque/tls types; still protect etcd at rest |
| Lab 12 env + JSON config | Lab 11 `templates/secrets.yaml` / Vault |

---

## 5. Bonus — ConfigMap updates & rollout

### Default kubelet behaviour

- Mounted ConfigMaps are **re-synced** periodically (often on the order of **~60s** plus cache effects). After **`kubectl edit configmap`** you may observe a delay before **`cat /config/config.json`** inside the pod changes.
- This app also **reloads config by mtime** so, once the file updates on disk, the next HTTP request sees new settings without restarting Python.

### `subPath` limitation

- If a volume mount uses **`subPath`** for a single file, that file is treated like a **one-off bind** and **does not** receive in-place updates when the ConfigMap changes. Prefer mounting the **whole directory** (e.g. `/config`) for hot refresh semantics.

### Helm: checksum annotation (pod restart on template change)

Pod template annotation **`checksum/config`** is set to a **SHA-256** of `files/config.json` plus `environment` and `logLevel`. Changing those values changes the checksum → Deployment rollout → new pods. Implemented in **`templates/_helpers.tpl`** (`configReload.checksumAnnotation`).

Disable without removing Lab 12 resources:

```yaml
configReload:
  checksumAnnotation: false
```

### Optional: Stakater Reloader

For automatic rollouts on live cluster edits to ConfigMaps, projects such as **[Stakater Reloader](https://github.com/stakater/Reloader)** watch resources and restart workloads; this chart does not install Reloader by default.

---

## 6. Example outputs (captured on kind cluster `lab11`, namespace `lab12`)

```text
$ kubectl get configmap,pvc -n lab12
NAME                                DATA   AGE
configmap/lab12-app-python-config   1      76s
configmap/lab12-app-python-env      2      76s

NAME                                          STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/lab12-app-python-data   Bound    pvc-5046053d-55f7-4a6d-97f6-9286b7ce2f8a   100Mi      RWO            standard   76s
```

```json
// kubectl exec -n lab12 deploy/lab12-app-python -- cat /config/config.json
{
  "appName": "devops-info-service",
  "environment": "dev",
  "features": {
    "metrics": true,
    "visits": true
  }
}
```

```text
$ kubectl exec -n lab12 deploy/lab12-app-python -- sh -c 'printenv | grep -E "^(APP_ENV|LOG_LEVEL)="'
APP_ENV=dev
LOG_LEVEL=info
```

**Persistence test:** after two GET `/` requests, `/data/visits` contained `2`. Pod was deleted (`kubectl delete pod -n lab12 <pod>`); the new pod still had `2` in `/data/visits`, and `GET /visits` returned `{"visits":2,...}` before any new root visit.

---

## 7. Install command (reference)

```bash
cd k8s/app-python
helm dependency update .
docker build -t local/app_python:lab12 ../../app_python
kind load docker-image local/app_python:lab12 --name lab11   # if using kind
helm upgrade --install lab12 . -f values-dev.yaml --namespace lab12 --create-namespace \
  --set image.repository=local/app_python \
  --set image.tag=lab12 \
  --set image.pullPolicy=Never
kubectl port-forward -n lab12 svc/lab12-app-python 15000:80
```

Use **`-f values-lab11.yaml`** for the Vault + nginx demo; that file turns off ConfigMap and PVC so the chart matches the non-Flask image.
