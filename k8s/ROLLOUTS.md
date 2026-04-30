# Argo Rollouts — Progressive Delivery (Lab 14)

## 1) Argo Rollouts Setup

### Installation and verification

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
kubectl -n argo-rollouts rollout status deploy/argo-rollouts
kubectl -n argo-rollouts rollout status deploy/argo-rollouts-dashboard
kubectl argo rollouts version
```

Verified in cluster:
- `argo-rollouts` controller is deployed and healthy.
- `argo-rollouts-dashboard` is deployed and healthy.
- `kubectl-argo-rollouts` plugin is installed and responding.

### Dashboard access

```bash
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

Open: `http://localhost:3100`

### Rollout vs Deployment (key differences)

- `Rollout` is a CRD (`argoproj.io/v1alpha1`) with the same pod template model as `Deployment`.
- `Rollout` adds progressive delivery strategies via `spec.strategy.canary` and `spec.strategy.blueGreen`.
- `Rollout` supports manual/automatic promotion steps, traffic shifting, and analysis-driven decisions.
- `Rollout` supports fast abort/undo behavior during release progression.

---

## 2) Canary Deployment

### Chart implementation

Updated chart files:
- `k8s/app-python/templates/rollout.yaml` (replaces Deployment with Rollout)
- `k8s/app-python/templates/analysis-template.yaml` (bonus analysis)
- `k8s/app-python/values.yaml` (canary steps and analysis values)

Canary steps configured:
- `20%` then manual pause
- `40%` then pause `30s`
- `60%` then pause `30s`
- `80%` then pause `30s`
- `100%`

### Deploy and progression test

```bash
helm upgrade --install app-canary k8s/app-python \
  --set persistence.enabled=false \
  --set image.repository=nginx \
  --set image.tag=1.27-alpine \
  --set service.targetPort=80 \
  --set livenessProbe.httpGet.path=/ \
  --set livenessProbe.httpGet.port=80 \
  --set readinessProbe.httpGet.path=/ \
  --set readinessProbe.httpGet.port=80

helm upgrade app-canary k8s/app-python \
  --set persistence.enabled=false \
  --set image.repository=nginx \
  --set image.tag=1.27.5-alpine \
  --set service.targetPort=80 \
  --set livenessProbe.httpGet.path=/ \
  --set livenessProbe.httpGet.port=80 \
  --set readinessProbe.httpGet.path=/ \
  --set readinessProbe.httpGet.port=80

kubectl argo rollouts get rollout app-canary-app-python
kubectl argo rollouts promote app-canary-app-python
```

Observed behavior:
- Rollout pauses at first manual pause step (`CanaryPauseStep`).
- Manual `promote` continues rollout to next steps.
- AnalysisRun is executed after `20%` step.

### Abort and rollback test

```bash
kubectl argo rollouts abort app-canary-app-python
kubectl argo rollouts get rollout app-canary-app-python
kubectl argo rollouts retry rollout app-canary-app-python
```

Observed behavior:
- `abort` immediately shifts traffic back to stable ReplicaSet.
- Rollout status becomes degraded (expected after manual abort).
- `retry` restarts rollout from canary progression.

---

## 3) Blue-Green Deployment

### Chart implementation

Updated chart files:
- `k8s/app-python/templates/rollout.yaml` (`strategy.blueGreen`)
- `k8s/app-python/templates/service-preview.yaml` (preview service)
- `k8s/app-python/values-bluegreen.yaml` (blue-green profile)

Blue-green config:
- `activeService`: main service (`<release>-app-python`)
- `previewService`: `<release>-app-python-preview`
- `autoPromotionEnabled: false` for manual promotion

### Blue-green flow test

```bash
helm upgrade --install app-bluegreen k8s/app-python \
  -f k8s/app-python/values-bluegreen.yaml \
  --set persistence.enabled=false \
  --set image.repository=nginx \
  --set image.tag=1.27-alpine \
  --set service.type=ClusterIP \
  --set service.targetPort=80 \
  --set livenessProbe.httpGet.path=/ \
  --set livenessProbe.httpGet.port=80 \
  --set readinessProbe.httpGet.path=/ \
  --set readinessProbe.httpGet.port=80

helm upgrade app-bluegreen k8s/app-python \
  -f k8s/app-python/values-bluegreen.yaml \
  --force-conflicts \
  --set persistence.enabled=false \
  --set image.repository=nginx \
  --set image.tag=1.27.5-alpine \
  --set service.type=ClusterIP \
  --set service.targetPort=80 \
  --set livenessProbe.httpGet.path=/ \
  --set livenessProbe.httpGet.port=80 \
  --set readinessProbe.httpGet.path=/ \
  --set readinessProbe.httpGet.port=80

kubectl argo rollouts promote app-bluegreen-app-python
kubectl argo rollouts get rollout app-bluegreen-app-python
```

Observed behavior:
- New version appears as non-active ReplicaSet first.
- After `promote`, active service switches to new ReplicaSet.
- Switch is instantaneous from user perspective.

### Instant rollback test

```bash
kubectl argo rollouts undo app-bluegreen-app-python --to-revision=1
kubectl argo rollouts get rollout app-bluegreen-app-python
```

Observed behavior:
- Rollback returns stable/active role to previous revision immediately.
- Blue-green rollback is faster than canary rollback because no gradual weighted steps are needed.

---

## 4) Strategy Comparison

### When to choose canary

- High-risk changes requiring gradual exposure.
- Need to observe behavior at small percentages before full traffic.
- Useful for metric-driven progressive gating.

### When to choose blue-green

- Need near-instant cutover and fast revert.
- Clear separation between current (active) and new (preview) versions.
- Good for pre-production verification against preview endpoint.

### Pros and cons

- Canary:
  - Pros: granular control, safer gradual release, analysis at each phase.
  - Cons: slower rollout, more operational steps.
- Blue-green:
  - Pros: instant switch, very fast rollback.
  - Cons: requires parallel environments during transition.

Recommendation:
- Use canary for risky backend/business-logic changes.
- Use blue-green for release windows where fast switch and rollback are top priority.

---

## 5) Bonus — Automated Analysis

Bonus implemented with `AnalysisTemplate` + canary `analysis` step.

Files:
- `k8s/app-python/templates/analysis-template.yaml`
- `k8s/app-python/values.yaml` (`analysis.*`, canary step with analysis)

Behavior:
- Metric `webcheck` calls app health endpoint (`/health`).
- Success condition: `result == "ok"`.
- Failure threshold is controlled via `failureLimit`.
- During canary rollout, analysis run executes after first weighted step.
- Failed analysis can be used to halt/rollback rollout automatically.

---

## 6) Useful CLI Commands

```bash
# Rollout status
kubectl argo rollouts get rollout <name> -w

# Manual promotion
kubectl argo rollouts promote <name>

# Abort/Retry
kubectl argo rollouts abort <name>
kubectl argo rollouts retry rollout <name>

# Undo to previous revision
kubectl argo rollouts undo <name> --to-revision=<n>

# History
kubectl argo rollouts history <name>

# Dashboard
kubectl argo rollouts dashboard
```

---

## 7) Screenshots checklist

Add dashboard screenshots in your report/repo for:
- Canary paused at manual step (20%).
- Canary analysis run state.
- Canary aborted rollback to stable.
- Blue-green preview/new ReplicaSet before promote.
- Blue-green active switch after promote.
- Blue-green rollback (`undo`) result.
