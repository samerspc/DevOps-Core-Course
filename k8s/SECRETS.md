# Secret management — Lab 11

This document describes Kubernetes native Secrets, Helm integration, resource limits, HashiCorp Vault Agent injection (including templating), and a short security comparison. It includes **live cluster evidence** (below) and rendered chart fragments.

---

## Evidence — live cluster (kind `lab11`, 2026-04-09)

Cluster: `kind create cluster --name lab11`. Context: `kind-lab11`.

### Task 1 — `kubectl` Secret

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=demo-user \
  --from-literal=password=demo-pass
# secret/app-credentials created
```

`kubectl get secret app-credentials -o yaml` (data is base64, not encrypted):

```yaml
apiVersion: v1
data:
  password: ZGVtby1wYXNz
  username: ZGVtby11c2Vy
kind: Secret
metadata:
  name: app-credentials
  namespace: default
type: Opaque
```

Decode:

```text
username b64 decode: demo-user
password b64 decode: demo-pass
```

### Helm chart check

```text
$ helm lint k8s/app-python
==> Linting k8s/app-python
[INFO] Chart.yaml: icon is recommended
1 chart(s) linted, 0 chart(s) failed
```

### Vault install note (Helm repo 403)

`helm repo add hashicorp https://helm.releases.hashicorp.com` returned **403 Forbidden** (CloudFront) in this environment. **Workaround:** install from the official Git chart:

```bash
git clone --depth 1 --branch v0.29.1 https://github.com/hashicorp/vault-helm.git /tmp/vault-helm
helm install vault /tmp/vault-helm \
  --set server.dev.enabled=true \
  --set injector.enabled=true \
  --wait --timeout 10m
```

Dev root token appears in `kubectl logs vault-0` (dev only; do not use in production).

### Task 3 — Pods and releases

```text
$ helm list
NAME  NAMESPACE REVISION STATUS   CHART            APP VERSION
lab11 default   1        deployed app-python-0.1.0 1.0.0
vault default   1        deployed vault-0.29.1  1.18.1

$ kubectl get pods | grep -E 'vault|injector|lab11'
vault-0                                 1/1   Running
vault-agent-injector-...                1/1   Running
lab11-app-python-...                    2/2   Running
```

Application install (nginx + Vault annotations + Helm Secret):

```bash
cd DevOps-Core-Course
helm dependency update k8s/app-python
helm upgrade --install lab11 k8s/app-python \
  -f k8s/app-python/values-dev.yaml \
  -f k8s/app-python/values-lab11.yaml \
  --set image.repository=nginx \
  --set image.tag=stable \
  --wait --timeout 8m
```

### `kubectl describe pod` — Secret by reference, not literal values

Fragment from the app Pod (Helm-managed Secret name; no decoded `username`/`password` in describe):

```text
    Environment Variables from:
      lab11-app-python-secret  Secret  Optional: false
```

Vault annotations appear on the Pod (template text is the Agent template, not the resolved secret).

### Vault file injection + templated file (bonus)

```bash
kubectl exec -n default deploy/lab11-app-python -c app-python -- ls -la /vault/secrets
```

```text
total 8
-rw-r--r-- 1 100 1000 64 ... config
```

Rendered `/vault/secrets/config` (values redacted for submission):

```text
USERNAME=<redacted>
PASSWORD=<redacted>
API_KEY=<redacted>
```

(Verified on cluster: three `KEY=value` lines matching Vault KV paths `secret/data/myapp/config`.)

### Env from Helm Secret (names + redacted values)

```text
APP_CHART_NAME=app-python
HELM_RELEASE=lab11
password=<redacted>
username=<redacted>
```

---

## 1. Kubernetes Secrets

### 1.1 Create a Secret with `kubectl` (Task 1)

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=demo-user \
  --from-literal=password=demo-pass
```

### 1.2 View and decode

```bash
kubectl get secret app-credentials -o yaml
```

Values under `data:` are **base64-encoded**, not encrypted. Decode (example):

```bash
kubectl get secret app-credentials -o jsonpath='{.data.username}' | base64 -d
echo
kubectl get secret app-credentials -o jsonpath='{.data.password}' | base64 -d
echo
```

### 1.3 Encoding vs encryption

- **Base64** in the API is an encoding for transport/storage of arbitrary bytes. Anyone who can `kubectl get secret` (or read etcd with sufficient access) can recover the plaintext after decoding.
- **Encryption at rest** for Secrets in etcd is a separate cluster feature: you configure an `EncryptionConfiguration` and a provider (e.g. KMS or aescbc) so etcd persists ciphertext. It is **not** enabled by default on a minimal cluster; enable it for production per [Encrypting Secret Data at Rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/).

**RBAC:** restrict who can `get/list/watch` Secrets; prefer namespace-scoped roles.

---

## 2. Helm secret integration (Task 2)

### 2.1 Chart structure

- `k8s/app-python/templates/secrets.yaml` — `Secret` with `stringData` from `values.yaml` (`secrets.stringData`).
- `k8s/app-python/templates/serviceaccount.yaml` — workload ServiceAccount (used by Vault Kubernetes auth in Task 3).
- `k8s/app-python/values.yaml` — `secrets.enabled`, `secrets.stringData` placeholders (`changeme`), `resources`, `serviceAccount`.

Secret name: `{{ release-fullname }}-secret` (helper `app-python.secretName` in `templates/_helpers.tpl`).

### 2.2 How the Deployment consumes the Secret

`k8s/app-python/templates/deployment.yaml` uses **`envFrom`** + **`secretRef`** so every key in the Secret becomes an environment variable:

```yaml
envFrom:
  - secretRef:
      name: <release>-app-python-secret
```

Non-sensitive variables are centralized in the named template **`app-python.standardEnv`** in `_helpers.tpl` and included under `env:` (DRY, bonus-friendly).

### 2.3 Verification (examples)

Deploy without committing real credentials (override at install time):

```bash
cd DevOps-Core-Course
helm dependency update k8s/app-python
helm upgrade --install app-dev k8s/app-python \
  -f k8s/app-python/values-dev.yaml \
  --set secrets.stringData.username=devuser \
  --set secrets.stringData.password=REPLACE_AT_CI
```

Check env names (avoid printing values in shared logs):

```bash
POD=$(kubectl get pods -l app.kubernetes.io/instance=app-dev -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it "$POD" -- env | egrep '^(username|password|APP_CHART_NAME|HELM_RELEASE)=' | sed 's/=.*/=<redacted>/'
```

`kubectl describe pod` shows that env vars **come from a Secret** (references), not the raw secret values in the describe output.

### 2.4 Rendered manifest excerpt (evidence)

From `helm template app-dev k8s/app-python -f k8s/app-python/values-dev.yaml` (abridged):

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-dev-app-python-secret
type: Opaque
stringData:
  password: "changeme"
  username: "changeme"
---
# Deployment fragment
          env:
            - name: APP_CHART_NAME
              value: "app-python"
            - name: HELM_RELEASE
              value: "app-dev"
          envFrom:
            - secretRef:
                name: app-dev-app-python-secret
          resources:
            limits:
              cpu: 100m
              memory: 128Mi
            requests:
              cpu: 50m
              memory: 64Mi
```

`helm lint k8s/app-python` — **0 failures** (icon recommendation only).

---

## 3. Resource management (Task 2)

### 3.1 Configuration

CPU/memory **requests** and **limits** live under `resources` in `values.yaml` and are overridden per environment in `values-dev.yaml` / `values-prod.yaml`.

### 3.2 Requests vs limits

- **Requests:** used by the scheduler (which node fits) and by `kubelet` for fair sharing; may affect **Quality of Service** class.
- **Limits:** hard cap; container may be throttled (CPU) or OOM-killed (memory) if exceeded.

### 3.3 Choosing values

Start from observed usage (`kubectl top pod` if metrics-server is installed), leave headroom for spikes, and set limits to avoid noisy neighbors. Prefer the same order of magnitude for dev/prod with prod higher; this chart uses smaller requests/limits in dev and larger in prod.

---

## 4. HashiCorp Vault integration (Task 3)

### 4.1 Install Vault (Helm, dev mode — learning only)

Preferred (when the repo is reachable):

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
helm install vault hashicorp/vault \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true"
kubectl get pods -l app.kubernetes.io/name=vault
```

If `helm repo add` returns **403**, use the Git clone path from **Evidence** (official `hashicorp/vault-helm` chart on disk).

Dev mode uses a known root token (see `kubectl logs vault-0`); **do not use in production**.

### 4.2 KV v2 and sample data

Exec into the Vault pod and use the CLI (dev token is often `root` — confirm with chart output):

```bash
kubectl exec -it vault-0 -- sh
export VAULT_TOKEN=root   # dev only; confirm from helm install notes

vault secrets enable -path=secret kv-v2 2>/dev/null || true
vault kv put secret/myapp/config username="appuser" password="vault-demo-pass" api_key="demo-api-key"
vault kv get secret/myapp/config
```

KV v2 read path for Agent/injector is typically `secret/data/myapp/config`.

### 4.3 Kubernetes auth

Configure the Kubernetes API for token review using the **Vault pod’s** service account CA/token, with `VAULT_TOKEN` and `VAULT_ADDR=http://127.0.0.1:8200` (see `kubectl exec` one-liners in **Evidence**):

```bash
vault auth enable kubernetes 2>/dev/null || true
vault write auth/kubernetes/config \
  kubernetes_host="https://${KUBERNETES_SERVICE_HOST}:443" \
  token_reviewer_jwt="$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)" \
  kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt \
  issuer="https://kubernetes.default.svc.cluster.local" \
  disable_iss_validation=true
```

(`disable_iss_validation=true` is often needed on **kind** / modern bound service account tokens.)

**Policy** (read-only on app path), name `app-python`:

```hcl
path "secret/data/myapp/*" {
  capabilities = ["read"]
}
path "secret/metadata/myapp/*" {
  capabilities = ["list", "read"]
}
```

```bash
printf '%s\n' 'path "secret/data/myapp/*" { capabilities = ["read"] }' \
  'path "secret/metadata/myapp/*" { capabilities = ["list", "read"] }' \
  | kubectl exec -i vault-0 -- env VAULT_TOKEN=root VAULT_ADDR=http://127.0.0.1:8200 vault policy write app-python -
```

**Role** bound to the workload ServiceAccount (replace names if your release/namespace differ):

- Release `lab11` → ServiceAccount **`lab11-app-python`** (from chart template).
- Namespace `default` example:

```bash
vault write auth/kubernetes/role/app-python \
  bound_service_account_names=lab11-app-python \
  bound_service_account_namespaces=default \
  policies=app-python \
  ttl=1h
```

### 4.4 Helm values for injection

File `k8s/app-python/values-lab11.yaml` sets `vault.inject.enabled: true`, `vault.role`, `secretPath`, and **bonus** `vault.inject.template` for a rendered file.

Install example (after Vault is configured):

```bash
helm upgrade --install lab11 k8s/app-python \
  -f k8s/app-python/values-dev.yaml \
  -f k8s/app-python/values-lab11.yaml \
  --set image.repository=nginx \
  --set image.tag=stable
```

### 4.5 Proof of secret injection

Vault Agent sidecar mounts files under `/vault/secrets` by default. With template suffix `config`, expect a file such as **`/vault/secrets/config`** (verify exact path in pod):

```bash
POD=$(kubectl get pods -l app.kubernetes.io/instance=lab11 -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it "$POD" -c app-python -- ls -la /vault/secrets 2>/dev/null || true
kubectl exec -it "$POD" -c vault-agent -- ls -la /vault/secrets 2>/dev/null || true
```

Use `kubectl describe pod "$POD"` to see injected containers and annotation-based configuration.

### 4.6 Sidecar injection pattern

The **Vault Agent Injector** is a mutating admission webhook. It patches the Pod spec to add an **init** and **sidecar** container that authenticate to Vault (here via Kubernetes auth), fetch secrets, and write them to a shared volume. The app container reads files or env sourced from that volume. Benefits: no long-lived cluster Secret objects for dynamic credentials, centralized rotation and policy in Vault.

---

## 5. Security analysis (Task 4)

| Topic | Kubernetes Secrets | Vault |
|--------|---------------------|--------|
| Storage | etcd (optionally encrypted at rest) | Dedicated Vault storage / HA backend |
| Access control | RBAC on Secret objects | Vault policies, namespaces, auth methods |
| Rotation | External process / manual | Dynamic secrets, leases, rotation workflows |
| Audit | API audit logs | Vault audit devices |
| Ops complexity | Low | Higher |

**When to use native Secrets:** simple apps, dev/test, static credentials with strict RBAC and etcd encryption.

**When to use Vault:** centralized policy, many teams, dynamic DB credentials, encryption-as-a-service, strict audit, multi-cloud.

**Production recommendations:** enable **etcd encryption at rest**, narrow RBAC, avoid committing secrets to Git (CI/CD injection, External Secrets Operator, or Vault Agent as used here), and run Vault in **non-dev** mode with TLS and proper seal configuration.

---

## 6. Bonus — Vault Agent templates & Helm DRY

### 6.1 Template annotation

With `vault.inject.template.enabled: true`, the chart emits:

- `vault.hashicorp.com/agent-inject-secret-config`
- `vault.hashicorp.com/agent-inject-template-config`

The template body uses **Vault Agent template** syntax (not Helm) to render e.g. a pseudo-`.env` with `USERNAME`, `PASSWORD`, and `API_KEY` from `secret/data/myapp/config`.

### 6.2 Dynamic refresh and `agent-inject-command`

Vault Agent can **renew** leases and **re-render** templates when secrets change (depending on engine and TTL). The annotation **`vault.hashicorp.com/agent-inject-command`** runs a command after render (e.g. signal the app to reload). Research current behavior for your Vault version in [Agent Injector annotations](https://developer.hashicorp.com/vault/docs/platform/k8s/injector/annotations).

### 6.3 Named template for environment variables

`_helpers.tpl` defines **`app-python.standardEnv`**; `deployment.yaml` uses:

```yaml
env:
  {{- include "app-python.standardEnv" . | nindent 12 }}
```

Add more non-sensitive `env` entries in one place to keep the Deployment DRY.

---

## 7. Checklist mapping

| Lab requirement | Where it is satisfied |
|-----------------|------------------------|
| kubectl `app-credentials` | Section 1 commands |
| Helm `secrets.yaml`, values, `envFrom` | Section 2 |
| Resource limits in values | Section 2–3 |
| Vault Helm, KV, K8s auth, policy/role | Section 4 |
| Injection + sidecar explanation | Section 4.6 |
| Bonus: template + `_helpers.tpl` env | Section 6 + chart files |

**Never commit real secrets.** Use placeholders in `values.yaml` and `--set` / CI secrets at deploy time.
