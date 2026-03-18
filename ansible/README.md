# Ansible Automation

[![Ansible Deployment](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ansible-deploy.yml)

Ansible automation for infrastructure provisioning and application deployment.

## Structure

```
ansible/
├── inventory/
│   └── hosts.ini              # Static inventory
├── roles/
│   ├── common/                # Common system tasks
│   ├── docker/                # Docker installation
│   └── web_app/               # Application deployment
├── playbooks/
│   ├── provision.yml          # System provisioning
│   ├── deploy.yml             # App deployment
│   └── site.yml               # Main playbook
├── group_vars/
│   └── all.yml                # Vault-encrypted variables
├── requirements.yml           # Ansible collections
└── docs/
    └── LAB06.md               # Lab 6 documentation
```

## Quick Start

### Install Dependencies

```bash
# Install Ansible collections
ansible-galaxy collection install -r requirements.yml
```

### Run Playbooks

```bash
# Provision infrastructure
ansible-playbook playbooks/provision.yml --ask-become-pass

# Deploy application
ansible-playbook playbooks/deploy.yml --ask-become-pass --ask-vault-pass

# Full deployment (provision + deploy)
ansible-playbook playbooks/site.yml --ask-become-pass --ask-vault-pass
```

## Features

- ✅ **Blocks & Tags** - Selective execution with tags
- ✅ **Docker Compose** - Declarative application deployment
- ✅ **Wipe Logic** - Safe application removal
- ✅ **CI/CD** - Automated deployment with GitHub Actions

## Tags

```bash
# List all tags
ansible-playbook playbooks/provision.yml --list-tags

# Run only packages
ansible-playbook playbooks/provision.yml --tags "packages" --ask-become-pass

# Run only docker installation
ansible-playbook playbooks/provision.yml --tags "docker_install" --ask-become-pass

# Deploy application
ansible-playbook playbooks/deploy.yml --tags "app_deploy" --ask-become-pass
```

## Wipe Logic

```bash
# Wipe application (requires variable + tag)
ansible-playbook playbooks/deploy.yml \
  -e "web_app_wipe=true" \
  --tags web_app_wipe \
  --ask-become-pass

# Clean reinstallation (wipe → deploy)
ansible-playbook playbooks/deploy.yml \
  -e "web_app_wipe=true" \
  --ask-become-pass
```

## CI/CD

GitHub Actions workflow automatically:
1. Lints Ansible code
2. Checks syntax
3. Deploys application (on push to main/master)

**Configure Secrets:**
- `ANSIBLE_VAULT_PASSWORD` - Vault password
- `SSH_PRIVATE_KEY` - SSH key (if using remote VM)
- `VM_HOST` - VM IP address (if using remote VM)

## Documentation

- [Task 1: Blocks & Tags](docs/TASK1_SUMMARY.md)
- [Task 2: Docker Compose](docs/TASK2_SUMMARY.md)
- [Task 3: Wipe Logic](docs/TASK3_SUMMARY.md)
- [Task 4: CI/CD](docs/TASK4_SUMMARY.md)
- [Lab 6 Complete](docs/LAB06.md)

## Requirements

- Ansible 2.16+
- Python 3.12+
- community.docker collection
- Target VM with SSH access (or use localhost)
