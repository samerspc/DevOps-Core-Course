# Lab 03 — Continuous Integration (CI/CD)

## 1. Overview

### Testing Framework: pytest

**Choice:** pytest with Flask test client.

**Why pytest:**
- Simple, concise test syntax — no boilerplate classes required
- Powerful fixture system for test setup and reuse
- Rich plugin ecosystem (coverage, etc.)
- De facto standard for modern Python projects
- Excellent assertion introspection (detailed failure messages)
- Works seamlessly with Flask's built-in test client

### Test Coverage

**23 unit tests** covering all application endpoints and error handling:

| Endpoint | Tests | What's tested |
|----------|-------|---------------|
| `GET /` | 17 | HTTP 200, JSON structure, all 5 top-level sections (service, system, runtime, request, endpoints), field types, specific values |
| `GET /health` | 6 | HTTP 200, JSON structure, status value, timestamp ISO format, uptime type |
| Error handling | 3 | 404 custom response, 404 JSON structure, 404 message content |

### CI Workflow Triggers

The workflow runs on:
- **Push** to `lab03` and `master` branches — full pipeline (test + Docker push)
- **Pull requests** to `master` — test only (no Docker push)

This ensures code quality on every change while only publishing images from trusted branches.

### Versioning Strategy: Semantic Versioning (SemVer)

**Choice:** SemVer (`MAJOR.MINOR.PATCH`, e.g., `1.2.3`)

**Rationale:**
- Already established in Lab 02 with version `1.0.0`
- Clear communication of breaking vs non-breaking changes
- Industry standard for API services
- Easy to integrate with git tags and Docker metadata action

## 2. Workflow Evidence

- **Successful workflow run:** [GitHub Actions](https://github.com/samerspc/DevOps-Core-Course/actions/workflows/python-ci.yml)
- **Docker Hub image:** [samerdockerhup/devops-info-service](https://hub.docker.com/r/samerdockerhup/devops-info-service)
- **Status badge:** visible in `app_python/README.md`

### Tests passing locally

```bash
$ python -m pytest tests/ -v
============================= test session starts ==============================
collected 23 items

tests/test_app.py::TestRootEndpoint::test_returns_200 PASSED             [  4%]
tests/test_app.py::TestRootEndpoint::test_returns_json PASSED            [  8%]
tests/test_app.py::TestRootEndpoint::test_top_level_keys PASSED          [ 13%]
tests/test_app.py::TestRootEndpoint::test_service_fields PASSED          [ 17%]
tests/test_app.py::TestRootEndpoint::test_service_name PASSED            [ 21%]
tests/test_app.py::TestRootEndpoint::test_service_framework PASSED       [ 26%]
tests/test_app.py::TestRootEndpoint::test_system_fields PASSED           [ 30%]
tests/test_app.py::TestRootEndpoint::test_system_hostname_is_string PASSED [ 34%]
tests/test_app.py::TestRootEndpoint::test_system_cpu_count_is_positive_int PASSED [ 38%]
tests/test_app.py::TestRootEndpoint::test_runtime_fields PASSED          [ 43%]
tests/test_app.py::TestRootEndpoint::test_runtime_uptime_is_non_negative PASSED [ 47%]
tests/test_app.py::TestRootEndpoint::test_runtime_current_time_is_iso_format PASSED [ 52%]
tests/test_app.py::TestRootEndpoint::test_request_fields PASSED          [ 56%]
tests/test_app.py::TestRootEndpoint::test_request_method_is_get PASSED   [ 60%]
tests/test_app.py::TestRootEndpoint::test_request_path_is_root PASSED    [ 65%]
tests/test_app.py::TestRootEndpoint::test_endpoints_is_list PASSED       [ 69%]
tests/test_app.py::TestRootEndpoint::test_endpoints_contain_root_and_health PASSED [ 73%]
tests/test_app.py::TestHealthEndpoint::test_returns_200 PASSED           [ 78%]
tests/test_app.py::TestHealthEndpoint::test_returns_json PASSED          [ 82%]
tests/test_app.py::TestHealthEndpoint::test_required_fields PASSED       [ 86%]
tests/test_app.py::TestHealthEndpoint::test_status_is_healthy PASSED     [ 91%]
tests/test_app.py::TestHealthEndpoint::test_uptime_is_non_negative_int PASSED [ 95%]
tests/test_app.py::TestHealthEndpoint::test_timestamp_is_utc_iso PASSED  [100%]

======================== 23 passed in 0.15s ================================
```

### Linter passing

```bash
$ python -m ruff check .
All checks passed!
```

## 3. Best Practices Implemented

| Practice | Implementation | Why it helps |
|----------|---------------|-------------|
| **Dependency Caching** | `actions/setup-python` with `cache: pip` keyed on `requirements-dev.txt` | Avoids re-downloading packages on every run; saves ~15-30s per workflow |
| **Workflow Concurrency** | `concurrency` group with `cancel-in-progress: true` | Cancels outdated runs when new commits are pushed, saving CI minutes |
| **Job Dependencies** | Docker & Snyk jobs use `needs: test` | Docker image is never built/pushed if tests fail — fail fast |
| **Conditional Docker Push** | `if: github.event_name == 'push'` on Docker job | Prevents Docker pushes on pull requests (PRs only run tests) |
| **Environment Variables** | `env:` block for `DOCKER_IMAGE` and `PYTHON_VERSION` | DRY principle — single place to update image name or Python version |
| **Docker Layer Caching** | Registry-based cache (`cache-from`/`cache-to`) | Reuses Docker build layers across CI runs, significantly faster rebuilds |
| **Snyk Security Scanning** | Separate job with `continue-on-error: true` | Checks dependencies for known CVEs without blocking deployments; severity threshold set to `high` |
| **Status Badge** | Markdown badge in `README.md` linking to Actions tab | Immediate visibility of CI health for contributors and reviewers |

### Snyk Integration

- **Severity threshold:** `high` — only high/critical vulnerabilities are flagged
- **Behavior:** `continue-on-error: true` — scan results are reported but don't block the pipeline
- **Rationale:** For a course project, blocking on every advisory would be impractical; high-severity threshold catches genuinely dangerous issues while allowing development to proceed

## 4. Key Decisions

### Versioning Strategy

**SemVer** was chosen because it was already established in Lab 02 (`1.0.0`) and clearly communicates the nature of changes. For an API service, knowing when breaking changes occur (major bump) is more useful than date-based versioning. Docker metadata action generates version tags automatically from git tags.

### Docker Tags

Every push produces multiple tags:
- `latest` — always points to the most recent build from CI
- `sha-<commit>` — unique per commit for traceability
- Branch name tags (e.g., `lab03`) for branch-specific builds

When a git tag like `v1.2.3` is pushed:
- `1.2.3` — full SemVer
- `1.2` — minor version (rolling)
- `sha-<commit>` + `latest`

### Workflow Triggers

- **Push to lab03/master:** Full pipeline including Docker push, because these are trusted branches
- **Pull requests to master:** Tests only (no Docker push), to validate code quality before merge without polluting Docker Hub with untested images

### Test Coverage

**Tested:** All endpoints (`/`, `/health`), response structures, field types, specific values, error handling (404).

**Not tested:** Server startup (`if __name__ == "__main__"`), logging output, environment variable configuration. These are infrastructure concerns better verified through integration/deployment testing.

## 5. Challenges

- **Flask test client differences:** Flask's test client uses `.get_json()` instead of `.json()` compared to FastAPI's TestClient — adapted tests accordingly
- **Content-Type header:** Flask returns `application/json` in `content_type` attribute, not `headers["content-type"]` — updated assertions
- **Linter configuration:** Initially ruff had some warnings, resolved by ensuring proper code formatting and removing unused imports
