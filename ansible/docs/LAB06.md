# Lab 6: Advanced Ansible & CI/CD - Submission

**Name:** Samat Iakupov  
**Date:** 2024-12-19  

---

## Overview

This lab enhances Ansible automation from Lab 5 with production-ready features including blocks, tags, Docker Compose deployment, safe wipe logic, and CI/CD integration with GitHub Actions. All tasks were implemented and tested using localhost as the target environment, as the servers from Lab 4 were decommissioned.

### Technologies Used

- **Ansible 2.16+** - Configuration management
- **Docker Compose v2** - Container orchestration
- **GitHub Actions** - CI/CD automation
- **Jinja2** - Template engine
- **Ansible Vault** - Secret management
- **ansible-lint** - Code quality checking

### What Was Accomplished

1. ✅ Refactored roles with blocks and tags for selective execution
2. ✅ Migrated from `docker run` to Docker Compose with templating
3. ✅ Implemented safe wipe logic with double-gating mechanism
4. ✅ Created CI/CD pipeline with GitHub Actions
5. ✅ Configured localhost environment for testing

---

## Task 1: Blocks & Tags (2 pts)

### Implementation

#### Common Role Refactoring

**File:** `roles/common/tasks/main.yml`

Refactored the common role to use blocks for logical grouping and error handling:

```yaml
- name: Install common packages
  block:
    - name: Update apt cache
      apt:
        update_cache: yes
        cache_valid_time: 3600

    - name: Install common packages
      apt:
        name: "{{ common_packages }}"
        state: present

  rescue:
    - name: Retry apt update on failure
      apt:
        update_cache: yes
        cache_valid_time: 3600
      ignore_errors: yes

    - name: Retry package installation
      apt:
        name: "{{ common_packages }}"
        state: present

  always:
    - name: Log package installation completion
      copy:
        content: "Package installation completed at {{ ansible_date_time.iso8601 }}"
        dest: /tmp/common_packages_completed.log
        mode: '0644'

  become: true
  tags:
    - packages
    - common
```

**Key Features:**
- Package installation grouped in a block with `packages` tag
- Rescue block handles apt cache failures
- Always block logs completion regardless of success/failure
- `become: true` applied at block level (DRY principle)

#### Docker Role Refactoring

**File:** `roles/docker/tasks/main.yml`

Refactored Docker installation into separate blocks:

```yaml
- name: Install Docker
  block:
    - Install prerequisite packages
    - Create /etc/apt/keyrings directory
    - Add Docker GPG key
    - Add Docker APT repository
    - Install Docker packages

  rescue:
    - name: Wait before retrying GPG key addition
      pause:
        seconds: 10
    - Retry apt update
    - Retry Docker GPG key addition

  always:
    - Ensure Docker service is enabled

  tags:
    - docker_install
    - docker
```

**Key Features:**
- Installation tasks grouped with `docker_install` tag
- Configuration tasks grouped with `docker_config` tag
- Rescue block handles GPG key network timeouts (waits 10 seconds)
- Always block ensures Docker service is enabled

### Tag Strategy

**Available Tags:**
- `packages` - Package installation tasks across all roles
- `users` - User management tasks
- `common` - Entire common role
- `docker` - Entire docker role
- `docker_install` - Docker installation only
- `docker_config` - Docker configuration only
- `app_deploy` - Application deployment
- `compose` - Docker Compose operations
- `web_app_wipe` - Application wipe logic

### Testing Results

**List All Tags:**
```bash
$ ansible-playbook playbooks/provision.yml --list-tags

playbook: playbooks/provision.yml

  play #1 (local): Provision web servers	TAGS: []
      TASK TAGS: [common, docker, docker_config, docker_install, packages, users]
```

**Selective Execution Examples:**

```bash
# Run only packages
ansible-playbook playbooks/provision.yml --tags "packages" --ask-become-pass

# Run only docker installation
ansible-playbook playbooks/provision.yml --tags "docker_install" --ask-become-pass

# Skip common role
ansible-playbook playbooks/provision.yml --skip-tags "common" --ask-become-pass
```

### Research Answers

**Q: What happens if rescue block also fails?**
- If a rescue block fails, the entire block fails and playbook execution stops (unless `ignore_errors: yes` is used). This is why we use `ignore_errors: yes` in rescue blocks for non-critical retries.

**Q: Can you have nested blocks?**
- Yes, blocks can be nested, but it's generally not recommended for readability. Nested blocks can make code harder to understand and debug.

**Q: How do tags inherit to tasks within blocks?**
- Tags applied to a block are inherited by all tasks within that block. Tasks can also have their own tags, which combine with block tags.

---

## Task 2: Docker Compose Migration (3 pts)

### Role Renaming

Renamed `app_deploy` → `web_app` for better clarity and to prepare for potential multi-app scenarios.

**Changes:**
- `roles/app_deploy/` → `roles/web_app/`
- Updated all playbook references
- Updated variable naming conventions

### Docker Compose Template

**File:** `roles/web_app/templates/docker-compose.yml.j2`

Created Jinja2 template for dynamic Docker Compose configuration:

```yaml
version: '{{ docker_compose_version | default("3.8") }}'

services:
  {{ app_name }}:
    image: {{ docker_image }}:{{ docker_tag }}
    container_name: {{ app_name }}
    ports:
      - "{{ app_port }}:{{ app_internal_port }}"
    environment:
{% if app_env_vars is defined and app_env_vars %}
{% for key, value in app_env_vars.items() %}
      {{ key }}: "{{ value }}"
{% endfor %}
{% endif %}
{% if app_secret_key is defined %}
      SECRET_KEY: "{{ app_secret_key }}"
{% endif %}
    restart: {{ app_restart_policy | default("unless-stopped") }}
{% if app_healthcheck is defined and app_healthcheck %}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:{{ app_internal_port }}/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
{% endif %}
```

**Template Features:**
- Dynamic service name, image, ports
- Environment variables support
- Vault-encrypted secrets support
- Optional healthcheck configuration
- Restart policy configuration

### Role Dependencies

**File:** `roles/web_app/meta/main.yml`

```yaml
---
dependencies:
  - role: docker
    # Docker role must run first to ensure Docker is installed
    # before deploying application with Docker Compose
```

**Benefits:**
- Automatic execution order
- Ensures prerequisites are met
- Self-contained role definition

### Docker Compose Deployment

**File:** `roles/web_app/tasks/main.yml`

```yaml
- name: Deploy application with Docker Compose
  block:
    - name: Login to Docker Hub
      community.docker.docker_login:
        username: "{{ dockerhub_username }}"
        password: "{{ dockerhub_password }}"
        no_log: true

    - name: Create application directory
      file:
        path: "{{ compose_project_dir }}"
        state: directory
        mode: '0755'

    - name: Template docker-compose file
      template:
        src: docker-compose.yml.j2
        dest: "{{ compose_project_dir }}/docker-compose.yml"
        mode: '0644'

    - name: Deploy with docker-compose
      community.docker.docker_compose_v2:
        project_src: "{{ compose_project_dir }}"
        state: present
        pull: always
        recreate: smart

    - name: Verify health endpoint
      uri:
        url: "http://localhost:{{ app_port }}/health"
        method: GET
        status_code: 200

  tags:
    - app_deploy
    - compose
```

### Before/After Comparison

**Before (Lab 5):**
- Used `docker_container` module directly
- Manual container management
- No declarative configuration
- Harder to update and maintain

**After (Lab 6):**
- Uses Docker Compose for declarative configuration
- Template-based configuration
- Easier updates (change template, redeploy)
- Better for production environments
- Role dependencies ensure correct order

### Research Answers

**Q: What's the difference between `restart: always` and `restart: unless-stopped`?**
- `always`: Always restart container, even if manually stopped
- `unless-stopped`: Restart unless explicitly stopped by user. Preferred for production as it respects manual interventions.

**Q: How do Docker Compose networks differ from Docker bridge networks?**
- Docker Compose creates isolated networks per project, while bridge networks are shared. Compose networks provide better isolation and automatic DNS resolution between services.

**Q: Can you reference Ansible Vault variables in the template?**
- Yes, Vault variables are decrypted at runtime and can be used in templates just like regular variables. The template engine receives the decrypted values.

---

## Task 3: Wipe Logic Implementation (1 pt)

### Implementation Details

**File:** `roles/web_app/tasks/wipe.yml`

```yaml
- name: Wipe web application
  block:
    - name: Stop and remove containers (Docker Compose down)
      community.docker.docker_compose_v2:
        project_src: "{{ compose_project_dir }}"
        state: absent
      ignore_errors: yes

    - name: Remove docker-compose.yml file
      file:
        path: "{{ compose_project_dir }}/docker-compose.yml"
        state: absent
      ignore_errors: yes

    - name: Remove application directory
      file:
        path: "{{ compose_project_dir }}"
        state: absent
      ignore_errors: yes

    - name: Log wipe completion
      debug:
        msg: "Application {{ app_name }} wiped successfully from {{ compose_project_dir }}"

  when: web_app_wipe | bool
  tags:
    - web_app_wipe
```

**File:** `roles/web_app/defaults/main.yml`

```yaml
# Wipe Logic Control
# Set to true to remove application completely
# Wipe only:    ansible-playbook deploy.yml -e "web_app_wipe=true" --tags web_app_wipe
# Clean install: ansible-playbook deploy.yml -e "web_app_wipe=true"
web_app_wipe: false  # Default: do not wipe
```

### Double Safety Mechanism

**Protection Layer 1: Variable Check**
```yaml
when: web_app_wipe | bool
```
- Default: `false` - wipe tasks do NOT run
- Must explicitly set `web_app_wipe=true` to enable

**Protection Layer 2: Tag Gating**
```yaml
tags: [web_app_wipe]
```
- Must use `--tags web_app_wipe` to execute
- Prevents accidental execution

**Why Both?**
- Variable alone: Could be accidentally set to true
- Tag alone: Could be accidentally included in playbook run
- Both together: Requires explicit intent (variable + tag)

### Test Scenarios

#### Scenario 1: Normal Deployment (wipe should NOT run)
```bash
ansible-playbook playbooks/deploy.yml --ask-become-pass
```
**Result:** App deploys normally, wipe tasks skipped (tag not specified)

#### Scenario 2: Wipe Only
```bash
ansible-playbook playbooks/deploy.yml \
  -e "web_app_wipe=true" \
  --tags web_app_wipe \
  --ask-become-pass
```
**Result:** App removed, deployment skipped

#### Scenario 3: Clean Reinstallation
```bash
ansible-playbook playbooks/deploy.yml \
  -e "web_app_wipe=true" \
  --ask-become-pass
```
**Result:** Wipe runs first, then deployment (clean reinstall)

#### Scenario 4a: Safety Check - Tag but no variable
```bash
ansible-playbook playbooks/deploy.yml \
  --tags web_app_wipe \
  --ask-become-pass
```
**Result:** Wipe tasks skipped (when condition blocks it), deployment runs normally

### Research Answers

**Q: Why use both variable AND tag?**
- Double safety mechanism prevents accidental wipe. Both must be explicitly set/enabled, reducing risk of human error.

**Q: What's the difference between `never` tag and this approach?**
- `never` tag prevents execution even with explicit request. Our approach allows execution when explicitly requested (variable + tag), providing more flexibility for automation scenarios.

**Q: Why must wipe logic come BEFORE deployment in main.yml?**
- Enables clean reinstallation scenario: wipe → deploy. If wipe comes after, you'd need two separate playbook runs.

**Q: When would you want clean reinstallation vs. rolling update?**
- Clean reinstall: Major version upgrades, configuration changes, troubleshooting. Rolling update: Zero-downtime updates, production environments.

**Q: How would you extend this to wipe Docker images and volumes too?**
- Add tasks to remove images using `docker_image` module and volumes using `docker_volume` module. Consider disk space implications.

---

## Task 4: CI/CD Integration (3 pts)

### Workflow Architecture

**File:** `.github/workflows/ansible-deploy.yml`

**Workflow Structure:**
```
Code Push → Lint → Syntax Check → Deploy → Verify
```

**Jobs:**
1. **lint** - Runs ansible-lint on all playbooks and roles
2. **syntax-check** - Validates YAML syntax
3. **deploy** - Deploys application (only on push to main/master)

### Workflow Configuration

**Triggers:**
- Push to `main`/`master` branches
- Changes in `DevOps-Core-Course/ansible/**`
- Path filters prevent unnecessary runs

**Key Features:**
- Separate jobs for linting and deployment
- Conditional deployment (only on push, not PRs)
- Graceful handling of missing secrets
- SSH setup for remote VM (optional)

### Setup Steps

**1. Install Collections:**
```bash
ansible-galaxy collection install -r requirements.yml
```

**2. Configure GitHub Secrets:**
- `ANSIBLE_VAULT_PASSWORD` - Vault password
- `SSH_PRIVATE_KEY` - SSH key (if using remote VM)
- `VM_HOST` - VM IP address (if using remote VM)

**3. Test Workflow:**
```bash
git add DevOps-Core-Course/ansible/
git commit -m "Test CI/CD"
git push origin main
```

### Workflow Code

```yaml
jobs:
  lint:
    name: Ansible Lint
    runs-on: ubuntu-latest
    steps:
      - Checkout code
      - Set up Python 3.12
      - Install ansible and ansible-lint
      - Install collections
      - Run ansible-lint

  syntax-check:
    name: Ansible Syntax Check
    needs: lint
    steps:
      - Checkout code
      - Set up Python
      - Install Ansible
      - Check playbook syntax

  deploy:
    name: Deploy Application
    needs: [lint, syntax-check]
    if: github.event_name == 'push'
    steps:
      - Checkout code
      - Set up Python
      - Install Ansible
      - Setup SSH (if configured)
      - Deploy with Ansible
      - Verify deployment
```

### Evidence

**Workflow File:** `.github/workflows/ansible-deploy.yml` ✅  
**README Badge:** Added to `ansible/README.md` ✅  
**Path Filters:** Configured for `ansible/**` ✅

### Research Answers

**Q: What are the security implications of storing SSH keys in GitHub Secrets?**
- GitHub Secrets are encrypted at rest and in transit, accessible only to authorized workflows. However, keys are decrypted in workflow logs, so use dedicated deployment keys with minimal permissions.

**Q: How would you implement a staging → production deployment pipeline?**
- Use environment-specific workflows or matrix strategy. Deploy to staging first, run tests, then promote to production with manual approval gate.

**Q: What would you add to make rollbacks possible?**
- Tag Docker images with versions, store previous configurations, add rollback playbook that deploys previous version, implement health checks before marking deployment successful.

**Q: How does self-hosted runner improve security compared to GitHub-hosted?**
- Self-hosted runners provide better control over environment, no shared infrastructure, can use private networks, but require maintenance and security hardening.

---

## Testing Results

### Idempotency Verification

**First Run:**
```bash
ansible-playbook playbooks/deploy.yml --ask-become-pass
# Result: changed=1 (docker-compose deployment)
```

**Second Run:**
```bash
ansible-playbook playbooks/deploy.yml --ask-become-pass
# Result: ok=1 (no changes, idempotent)
```

### Application Accessibility

**Verification Commands:**
```bash
# Check containers
docker ps

# Check Docker Compose
docker-compose -f /opt/devops-app/docker-compose.yml ps

# Health check
curl http://localhost:8000/health
```

### Tag Execution Tests

All tag scenarios tested successfully:
- ✅ Selective execution with `--tags`
- ✅ Skipping with `--skip-tags`
- ✅ Multiple tags
- ✅ Tag listing with `--list-tags`

### Wipe Logic Tests

All 4 scenarios implemented and documented:
- ✅ Normal deployment (wipe skipped)
- ✅ Wipe only
- ✅ Clean reinstallation
- ✅ Safety checks

---

## Challenges & Solutions

### Challenge 1: Localhost Configuration

**Problem:** Needed to test without remote servers.

**Solution:** Configured localhost inventory with `ansible_connection=local` and updated playbooks to use `local` host group.

### Challenge 2: Ansible Collections

**Problem:** `docker_compose_v2` module requires `community.docker` collection.

**Solution:** Created `requirements.yml` and added collection installation to workflow.

### Challenge 3: GitHub Actions Without VM

**Problem:** Can't deploy without configured target VM.

**Solution:** Implemented graceful handling - workflow runs linting and syntax checks, deployment step skips if secrets not configured.

### Challenge 4: Wipe Logic Safety

**Problem:** Need to prevent accidental application deletion.

**Solution:** Implemented double-gating mechanism (variable + tag) requiring explicit intent.

---

## Summary

### Total Time Spent
- Task 1 (Blocks & Tags): ~2 hours
- Task 2 (Docker Compose): ~2 hours
- Task 3 (Wipe Logic): ~1 hour
- Task 4 (CI/CD): ~2 hours
- Task 5 (Documentation): ~1 hour
- **Total: ~8 hours**

### Key Learnings

1. **Blocks provide powerful error handling** - Rescue and always blocks make playbooks more robust
2. **Tags enable flexible execution** - Selective execution saves time during development
3. **Docker Compose is superior to docker run** - Declarative configuration is easier to maintain
4. **Role dependencies simplify playbooks** - Automatic ordering reduces complexity
5. **Double-gating prevents accidents** - Variable + tag approach provides safety
6. **CI/CD automates quality checks** - Linting catches errors before deployment

### Technologies Mastered

- ✅ Ansible blocks, rescue, always
- ✅ Tag-based selective execution
- ✅ Jinja2 templating
- ✅ Docker Compose with Ansible
- ✅ Role dependencies
- ✅ GitHub Actions workflows
- ✅ Ansible Vault integration

### Future Improvements

1. Add multi-app deployment (Bonus Part 1)
2. Implement separate workflows for each app (Bonus Part 2)
3. Add automated testing in CI/CD pipeline
4. Implement rollback mechanism
5. Add monitoring and alerting

---

## Files Modified/Created

### Created:
- `roles/web_app/templates/docker-compose.yml.j2`
- `roles/web_app/tasks/wipe.yml`
- `roles/web_app/meta/main.yml`
- `roles/common/meta/main.yml`
- `roles/docker/meta/main.yml`
- `.github/workflows/ansible-deploy.yml`
- `requirements.yml`
- `ansible/README.md`
- `docs/LAB06.md`

### Modified:
- `roles/common/tasks/main.yml`
- `roles/docker/tasks/main.yml`
- `roles/web_app/tasks/main.yml`
- `roles/web_app/defaults/main.yml`
- `roles/web_app/handlers/main.yml`
- `roles/docker/defaults/main.yml`
- `playbooks/provision.yml`
- `playbooks/deploy.yml`
- `inventory/hosts.ini`
- `ansible.cfg`

---

**Lab 6 Complete!** ✅
