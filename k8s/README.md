# Lab 09 - Kubernetes Fundamentals Report

## 1) Architecture Overview

This lab deploys the Python application (`devops-info-service`) into a local Kubernetes cluster (`kind`, single control-plane node) using declarative manifests.

- Namespace: `lab09`
- App 1 deployment: `devops-info-python` (main app, 3 replicas in manifest)
- App 1 service: `devops-info-python-svc` (`NodePort`, `80 -> 5000`, node port `30080`)
- App 2 deployment (bonus): `devops-info-python-app2` (separate config)
- App 2 service (bonus): `devops-info-python-app2-svc` (`ClusterIP`)
- Ingress (bonus): `devops-info-ingress` with host `local.example.com`
  - `/app1` -> app1 service
  - `/app2` -> app2 service
- TLS secret (bonus): `lab09-tls` (self-signed cert)

Traffic flow:

1. Client -> NodePort (`devops-info-python-svc`) for base task validation.
2. Client -> Ingress controller -> path-based routing -> app1/app2 services for bonus.

Resource strategy:

- Requests/limits are set to avoid noisy-neighbor issues and to ensure scheduler predictability.
- Main app resources: request `100m/128Mi`, limit `250m/256Mi`.

## 2) Manifest Files

- `k8s/namespace.yml` - Dedicated namespace for lab isolation.
- `k8s/deployment.yml` - Main production-style deployment:
  - 3 replicas
  - rolling update strategy (`maxSurge: 1`, `maxUnavailable: 0`)
  - liveness/readiness probes on `/health`
  - resource requests and limits
  - non-root runtime inherited from Docker image
- `k8s/service.yml` - Main `NodePort` service for local external access.
- `k8s/deployment-app2.yml` - Bonus second deployment (Go application image).
- `k8s/service-app2.yml` - Bonus internal service for app2.
- `k8s/ingress.yml` - Bonus ingress with TLS and path routing.

Why these values:

- `replicas: 3` gives baseline high availability.
- `maxUnavailable: 0` demonstrates safer updates (no intentional capacity drop).
- Probe timings are short enough for quick local feedback without excessive flapping.

## 3) Deployment Evidence

All raw command output is stored in `k8s/evidence.txt`.

### Cluster up

```bash
kubectl cluster-info
kubectl get nodes
```

Result excerpt:

```text
Kubernetes control plane is running at https://127.0.0.1:52348
NAME                  STATUS   ROLES           AGE   VERSION
lab09-control-plane   Ready    control-plane   86s   v1.35.0
```

### Core resources deployed

```bash
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
kubectl get deployments,pods,svc -n lab09 -o wide
```

Result excerpt:

```text
deployment.apps/devops-info-python   3/3 ... IMAGES devops-info-python:lab09-v1
service/devops-info-python-svc       NodePort ... 80:30080/TCP
```

### App reachable

```bash
kubectl port-forward -n lab09 service/devops-info-python-svc 8080:80
curl http://127.0.0.1:8080/health
```

Result excerpt:

```json
{"status":"healthy","timestamp":"2026-03-26T12:41:40.323354+00:00","uptime_seconds":9}
```

## 4) Operations Performed

### Scaling

```bash
kubectl scale deployment/devops-info-python -n lab09 --replicas=5
kubectl rollout status deployment/devops-info-python -n lab09
```

Result excerpt:

```text
deployment.apps/devops-info-python scaled
deployment "devops-info-python" successfully rolled out
```

### Rolling update

```bash
kubectl set image deployment/devops-info-python -n lab09 app=devops-info-python:lab09-v2
kubectl rollout status deployment/devops-info-python -n lab09
kubectl rollout history deployment/devops-info-python -n lab09
```

Result excerpt:

```text
deployment.apps/devops-info-python image updated
deployment "devops-info-python" successfully rolled out
REVISION  CHANGE-CAUSE
1         <none>
2         <none>
```

### Rollback

```bash
kubectl rollout undo deployment/devops-info-python -n lab09
kubectl rollout status deployment/devops-info-python -n lab09
kubectl rollout history deployment/devops-info-python -n lab09
```

Result excerpt:

```text
deployment.apps/devops-info-python rolled back
deployment "devops-info-python" successfully rolled out
REVISION  CHANGE-CAUSE
2         <none>
3         <none>
```

Zero-downtime verification:

- Rollout used `maxUnavailable: 0`.
- During update/rollback, Kubernetes kept serving traffic through ready pods.

## 5) Production Considerations

- Health checks:
  - `livenessProbe` restarts unhealthy containers.
  - `readinessProbe` blocks traffic to non-ready pods.
  - Both use `/health`, which exists in the Flask app.
- Resource controls:
  - Protect node stability and improve scheduling decisions.
  - Limits prevent runaway memory/CPU usage.
- Security:
  - Container runs as non-root user (from app image Dockerfile).
- Monitoring/observability strategy:
  - Keep app metrics endpoint (`/metrics`) for Prometheus scraping.
  - Use `kubectl logs`, `kubectl describe`, and events for incident triage.
  - Add centralized logs and alerts in production.
- Future improvements:
  - HPA + metrics-server
  - PodDisruptionBudget
  - dedicated ConfigMap/Secret management
  - network policies and CI validation of manifests

## 6) Challenges and Solutions

- Challenge: no local cluster available initially.
  - Solution: installed `kind`, launched Docker Desktop, created `kind` cluster.
- Challenge: `app_go` image initially failed to build because package install happened after switching to non-root user.
  - Solution: moved `apk add --no-cache wget` before `USER appuser` in `app_go/Dockerfile`, rebuilt image, redeployed app2.
- Challenge: ingress HTTP requests returned 308 redirects.
  - Solution: validated final routing over HTTPS with TLS (`curl -k --resolve ...`).

## Bonus - Ingress with TLS

Completed:

- Ingress controller installed (`ingress-nginx` for kind)
- App2 deployment and service created
- Self-signed certificate generated
- TLS secret `lab09-tls` created
- Ingress configured with `/app1` and `/app2` routes
- HTTPS verified

Commands used:

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /tmp/lab09-tls.key -out /tmp/lab09-tls.crt \
  -subj "/CN=local.example.com/O=local.example.com"
kubectl create secret tls lab09-tls -n lab09 --key /tmp/lab09-tls.key --cert /tmp/lab09-tls.crt
kubectl apply -f k8s/ingress.yml
```

Ingress verification excerpt:

```text
deployment "devops-info-python-app2" successfully rolled out
kubectl get ingress -n lab09
devops-info-ingress   nginx   local.example.com   ...   80,443
APP1_FRAMEWORK:
"framework":"Flask"
APP2_FRAMEWORK:
"framework":"Go"
```
