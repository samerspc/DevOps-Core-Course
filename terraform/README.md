# Lab 4 - Terraform Infrastructure

This directory contains Terraform configuration for creating a virtual machine in Yandex Cloud for Lab 4.

## Prerequisites

1. **Terraform installed** (version >= 1.9)
   ```bash
   # macOS
   brew install terraform
   
   # Or download from: https://developer.hashicorp.com/terraform/downloads
   ```

2. **Yandex Cloud account** with:
   - Cloud ID
   - Folder ID
   - Service account with `compute.admin` and `vpc.admin` roles, OR OAuth token

3. **SSH key pair** generated:
   ```bash
   ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
   ```

## Setup

1. **Copy the example variables file:**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

2. **Edit `terraform.tfvars`** with your values:
   - Yandex Cloud ID and Folder ID (from Yandex Cloud Console)
   - Authentication method (token or service account key file)
   - SSH public key path
   - Your IP address for SSH access (for security)

3. **Get your IP address** (for better security):
   ```bash
   curl ifconfig.me
   ```
   Then set `allowed_ssh_cidr = "YOUR_IP/32"` in `terraform.tfvars`

## Authentication Methods

### Option 1: OAuth Token (Quick Start)
1. Get token from: https://oauth.yandex.com/authorize?response_type=token&client_id=1a6990aa636648e9b2ef855e7c2f0e7b
2. Set `yandex_token` in `terraform.tfvars`

### Option 2: Service Account (Recommended)
1. Create service account in Yandex Cloud Console
2. Assign roles: `compute.admin`, `vpc.admin`
3. Create authorized key (JSON)
4. Download key file
5. Set `yandex_service_account_key_file` in `terraform.tfvars`

## Usage

1. **Initialize Terraform:**
   ```bash
   terraform init
   ```

2. **Format and validate:**
   ```bash
   terraform fmt
   terraform validate
   ```

3. **Preview changes:**
   ```bash
   terraform plan
   ```

4. **Apply infrastructure:**
   ```bash
   terraform apply
   ```
   Type `yes` when prompted.

5. **Get VM information:**
   ```bash
   terraform output
   ```

6. **Connect to VM:**
   ```bash
   ssh ubuntu@$(terraform output -raw vm_public_ip)
   ```
   Or use the output command:
   ```bash
   terraform output -raw ssh_connection_command
   ```

7. **Destroy infrastructure:**
   ```bash
   terraform destroy
   ```

## Resources Created

- **VPC Network**: Virtual private cloud network
- **Subnet**: Subnet in the specified zone
- **Security Group**: Firewall rules for:
  - SSH (port 22) - from your IP
  - HTTP (port 80) - from anywhere
  - Custom port 5000 - from anywhere (for future app deployment)
- **Compute Instance**: Ubuntu 22.04 VM with:
  - 2 cores (20% fraction = free tier)
  - 1 GB RAM
  - 10 GB HDD
  - Public IP address

## Important Notes

⚠️ **Security:**
- Never commit `terraform.tfvars` to Git (it's in `.gitignore`)
- Change `allowed_ssh_cidr` to your IP address for better security
- Keep your service account key file secure

💰 **Cost:**
- This configuration uses free tier resources
- Should cost $0 if within free tier limits
- Remember to run `terraform destroy` when done!

📝 **For Lab 5:**
- You can keep this VM for Lab 5 (Ansible)
- Or destroy it and recreate later using this code
- Document your decision in `docs/LAB04.md`

## Troubleshooting

**Error: "authentication failed"**
- Check your token or service account key file path
- Verify service account has required roles

**Error: "insufficient permissions"**
- Ensure service account has `compute.admin` and `vpc.admin` roles

**Error: "image not found"**
- Check `vm_image_family` variable
- Available families: `ubuntu-2204-lts`, `ubuntu-2004-lts`, `centos-7`, etc.

**SSH connection fails:**
- Wait a few minutes after VM creation
- Check security group rules
- Verify your IP in `allowed_ssh_cidr`
- Check VM is running in Yandex Cloud Console

## Files

- `main.tf` - Main infrastructure configuration
- `variables.tf` - Variable declarations
- `outputs.tf` - Output values
- `terraform.tfvars.example` - Example variables (copy to `terraform.tfvars`)
- `.gitignore` - Files to exclude from Git

## Next Steps

After completing Task 1:
1. Document your setup in `docs/LAB04.md`
2. Move to Task 2: Destroy this infrastructure and recreate with Pulumi
