# HELM — app-python

## 1. Chart Overview

- Structure:
  - `Chart.yaml`: chart metadata
  - `values.yaml`: default configuration (image, replicas, resources, service, probes)
  - `templates/`:
    - `_helpers.tpl`: helpers for names/labels
    - `deployment.yaml`: Deployment for Flask app on port 5000
    - `service.yaml`: Service exposing the app
    - `NOTES.txt`: post-install access hints
    - `hooks/`: pre/post-install Job hooks
- Values organization:
  - Top-level keys: `replicaCount`, `image`, `service`, `resources`, `livenessProbe`, `readinessProbe`
  - Environment overrides in `values-dev.yaml` and `values-prod.yaml`

## 2. Configuration Guide

- Important values:
  - `image.repository` (string): Docker image repo (e.g., `yourusername/app_python`)
  - `image.tag` (string): image tag (dev uses `latest`, prod uses a fixed version)
  - `replicaCount` (int): number of Pods
  - `resources.*` (object): CPU/Memory requests/limits
  - `service.type` (NodePort/LoadBalancer), `service.port`, `service.targetPort`
  - `livenessProbe` / `readinessProbe` (httpGet to `/health` by default)
- Environment customization:
  - Dev: 1 replica, smaller resources, NodePort
  - Prod: 5 replicas, stronger resources, LoadBalancer
- Examples:
  - Dev: `helm install app-dev DevOps-Core-Course/k8s/app-python -f DevOps-Core-Course/k8s/app-python/values-dev.yaml`
  - Prod: `helm install app-prod DevOps-Core-Course/k8s/app-python -f DevOps-Core-Course/k8s/app-python/values-prod.yaml`
  - Override single value: `--set replicaCount=10`

## 3. Hook Implementation

- Hooks:
  - Pre-install Job (`templates/hooks/pre-install-job.yaml`)
    - Annotations: `helm.sh/hook: pre-install`, weight `-5`, delete policy `hook-succeeded`
  - Post-install Job (`templates/hooks/post-install-job.yaml`)
    - Annotations: `helm.sh/hook: post-install`, weight `5`, delete policy `hook-succeeded`
- Purpose:
  - Pre-install: placeholder for validation/migrations
  - Post-install: placeholder for smoke validation

## 4. Installation Evidence

### Helm setup and chart exploration

```bash
$ helm version
version.BuildInfo{Version:"v4.1.3", GitCommit:"c94d381b03be117e7e57908edbf642104e00eb8f", GitTreeState:"clean", GoVersion:"go1.26.1", KubeClientVersion:"v1.35"}
```

```bash
$ helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
"prometheus-community" has been added to your repositories

$ helm repo update
...Successfully got an update from the "prometheus-community" chart repository
Update Complete. ⎈Happy Helming!⎈
```

```bash
$ helm show chart prometheus-community/prometheus | head -n 12
apiVersion: v2
appVersion: v3.11.0
dependencies:
- condition: alertmanager.enabled
  name: alertmanager
  repository: https://prometheus-community.github.io/helm-charts
  version: 1.34.*
description: Prometheus is a monitoring system and time series database.
home: https://prometheus.io/
```

### Chart validation

```bash
$ helm dependency update k8s/app-python
Saving 1 charts
Deleting outdated charts
```

```bash
$ helm lint k8s/app-python
==> Linting k8s/app-python
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

```bash
$ helm template app k8s/app-python | head -n 25
---
# Source: app-python/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: app-app-python
spec:
  type: NodePort
...
---
# Source: app-python/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-app-python
...
```

```bash
$ helm install --dry-run --debug app-dry k8s/app-python
NAME: app-dry
STATUS: pending-install
DESCRIPTION: Dry run complete
...
HOOKS:
# Source: app-python/templates/hooks/post-install-job.yaml
# Source: app-python/templates/hooks/pre-install-job.yaml
```

### Kubernetes install evidence (real cluster)

```bash
$ kind create cluster --name lab10
Creating cluster "lab10" ...
Set kubectl context to "kind-lab10"
```

```bash
$ helm install app-dev k8s/app-python -f k8s/app-python/values-dev.yaml --set image.repository=nginx --set image.tag=stable
NAME: app-dev
STATUS: deployed
```

```bash
$ helm upgrade --install app-prod k8s/app-python -f k8s/app-python/values-prod.yaml --set image.repository=nginx --set image.tag=stable
Release "app-prod" does not exist. Installing it now.
NAME: app-prod
STATUS: deployed
```

```bash
$ helm list
NAME     NAMESPACE REVISION STATUS   CHART            APP VERSION
app-dev  default   1        deployed app-python-0.1.0 1.0.0
app-prod default   1        deployed app-python-0.1.0 1.0.0
```

```bash
$ kubectl get all
pod/app-dev-app-python-...     0/1 Running
pod/app-prod-app-python-...    0/1 Running
service/app-dev-app-python     NodePort
service/app-prod-app-python    LoadBalancer
deployment.apps/app-dev-app-python    0/1
deployment.apps/app-prod-app-python   0/5
```

```bash
$ kubectl get jobs
No resources found in default namespace.
```

Hook Jobs were created and executed during install, then removed automatically due to `helm.sh/hook-delete-policy: hook-succeeded`.

## 5. Operations

- Install:
  - Dev: `helm install app-dev DevOps-Core-Course/k8s/app-python -f DevOps-Core-Course/k8s/app-python/values-dev.yaml`
  - Prod: `helm install app-prod DevOps-Core-Course/k8s/app-python -f DevOps-Core-Course/k8s/app-python/values-prod.yaml`
- Upgrade:
  - `helm upgrade app-dev DevOps-Core-Course/k8s/app-python -f DevOps-Core-Course/k8s/app-python/values-dev.yaml`
- Rollback:
  - `helm rollback app-dev 1`
- Uninstall:
  - `helm uninstall app-dev`

## 6. Testing & Validation

- `helm lint DevOps-Core-Course/k8s/app-python`
- `helm template DevOps-Core-Course/k8s/app-python` and review resources
- `helm install --dry-run --debug app-dry DevOps-Core-Course/k8s/app-python`
- Access:
  - NodePort: `kubectl port-forward svc/<release>-app-python 8080:5000` then open `http://127.0.0.1:8080/health`
  - LoadBalancer (cloud): open external IP

---

## Bonus — Library Chart (Outline)

- Create `DevOps-Core-Course/k8s/common-lib` as type `library` and move shared helpers there.
- Add dependency to `app-python/Chart.yaml`:
  ```yaml
  dependencies:
    - name: common-lib
      version: 0.1.0
      repository: "file://../common-lib"
  ```
- Run: `helm dependency update DevOps-Core-Course/k8s/app-python`
