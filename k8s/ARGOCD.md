# Lab 13 - ArgoCD GitOps Report

This document captures the completed Lab 13 implementation: ArgoCD setup, GitOps applications, multi-environment strategy, self-healing tests, and bonus ApplicationSet.

## 1) ArgoCD Setup

### Installation verification

ArgoCD was installed via Helm into the `argocd` namespace:

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
helm upgrade --install argocd argo/argo-cd --namespace argocd
kubectl wait --for=condition=available deployment/argocd-server -n argocd --timeout=300s
```

Result: release `argocd` deployed successfully and `argocd-server` became `Available`.

### UI access method

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Then open: `https://localhost:8080`.

Initial password retrieval:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d
```

### CLI configuration

CLI was installed and configured:

```bash
brew install argocd
argocd login localhost:8080 --insecure --username admin --password <password>
argocd app list
```

Result: login successful and ArgoCD context updated.

## 2) Application Configuration

Manifests created in `k8s/argocd/`:

- `application.yaml` (single app, manual sync)
- `application-dev.yaml` (dev app with auto-sync)
- `application-prod.yaml` (prod app, manual sync)
- `applicationset.yaml` (bonus)

### Source and destination

All apps use:

- `repoURL`: `https://github.com/samerspc/DevOps-Core-Course.git`
- `targetRevision`: `master`
- `path`: `k8s/app-python`
- `destination.server`: `https://kubernetes.default.svc`

### Values selection

- default app: `values.yaml`
- dev app: `values-dev.yaml`
- prod app: `values-prod.yaml`

## 3) Multi-Environment (dev/prod)

### Namespace separation

```bash
kubectl create namespace dev --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace prod --dry-run=client -o yaml | kubectl apply -f -
```

### Sync policy differences

- **Dev** (`python-app-dev`): automated sync with `prune: true` and `selfHeal: true`
- **Prod** (`python-app-prod`): manual sync only (no `automated` block)

### Why prod is manual

- Requires explicit release approval/timing
- Reduces risk of unintended immediate production change
- Supports controlled rollback/change-window processes

### Current deployment verification

```bash
argocd app list
kubectl get pods -n dev
kubectl get pods -n prod
```

State observed:

- `python-app` -> Synced / Healthy
- `python-app-dev` -> Synced / Healthy
- `python-app-prod` -> Synced / Progressing (service type is `LoadBalancer` in kind)

## 4) Self-Healing Evidence

> Note: local kind cluster was used, app image was built and loaded into cluster:
>
> ```bash
> docker build -t yourusername/app_python:latest app_python
> docker tag yourusername/app_python:latest yourusername/app_python:1.0.0
> kind load docker-image yourusername/app_python:latest --name lab13
> kind load docker-image yourusername/app_python:1.0.0 --name lab13
> ```

### A) Manual scale drift test (ArgoCD self-heal)

Command:

```bash
kubectl scale deployment python-app-dev-app-python -n dev --replicas=5
```

Observed:

- `2026-04-23 22:31:18 MSK` before scale: `replicas=1`
- `2026-04-23 22:31:19 MSK` manual drift: `replicas=5`
- `2026-04-23 22:31:35 MSK` after self-heal: `replicas=1`

Conclusion: ArgoCD auto-sync + selfHeal reverted live drift to Git state.

### B) Pod deletion test (Kubernetes self-healing)

Commands:

```bash
kubectl get pods -n dev -l app.kubernetes.io/instance=python-app-dev
kubectl delete pod <pod-name> -n dev
kubectl get pods -n dev -l app.kubernetes.io/instance=python-app-dev
```

Observed:

- Before: `python-app-dev-app-python-955ccf7f6-k28zv`
- After deletion: new pod `python-app-dev-app-python-955ccf7f6-ff8wp`

Conclusion: pod recreation is done by Kubernetes Deployment/ReplicaSet controllers.

### C) Configuration drift test (ArgoCD self-heal)

Command:

```bash
kubectl set image deployment/python-app-dev-app-python -n dev app-python=nginx:latest
```

Observed:

- Immediately after drift: image = `nginx:latest`
- After self-heal: image = `yourusername/app_python:latest`

Conclusion: ArgoCD detected spec drift and restored desired image from Git.

### D) Sync behavior explanation

- Kubernetes self-healing: keeps runtime replica/pod count and restarts failed pods.
- ArgoCD self-healing: keeps declared configuration aligned with Git (`Application` source).
- ArgoCD sync can be triggered by:
  - automated policy (`spec.syncPolicy.automated`)
  - manual UI/CLI sync
  - periodic repository poll (default ~3 minutes)
  - webhooks for near-immediate updates

## 5) Screenshots Checklist

Capture and attach these in your submission:

1. ArgoCD Applications page showing `python-app-dev` and `python-app-prod`
2. One app details page showing Sync/Health and resource tree
3. OutOfSync -> Synced transition (during any drift test)
4. Bonus: ApplicationSet-generated apps (`python-appset-dev`, `python-appset-prod`)

## Bonus - ApplicationSet

Bonus implementation file: `k8s/argocd/applicationset.yaml`

Implemented:

- `List` generator with environment parameters (`dev`, `prod`)
- Single template that renders multiple Applications
- Conditional auto-sync behavior using `templatePatch` for `dev`

Generated apps observed:

- `python-appset-dev` (auto-sync)
- `python-appset-prod` (manual sync)

### Why ApplicationSet

- Less duplication than separate per-env Application files
- Scales better when adding more environments/tenants/apps
- Centralizes template logic and env parameter management

