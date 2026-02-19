# Lab 4 — Infrastructure as Code (Terraform & Pulumi)

## 1. Cloud Provider & Infrastructure

### Cloud Provider: Yandex Cloud

**Provider choice:**
Yandex Cloud was chosen for the following reasons:
- Available in Russia without restrictions
- Provides a free tier suitable for learning
- Good documentation in Russian
- Simple setup and management

**Cloud ID:** `b1g*******`  
**Folder ID:** `b1g*******`  
**Zone:** `ru-central1-a`

### Instance Configuration

**Instance Type:** `standard-v2` (free tier)
- **CPU:** 2 cores with `core_fraction = 20%` (20% of full CPU = free tier)
- **Memory:** 1 GB RAM
- **Boot Disk:** 10 GB HDD (network-hdd)
- **Image:** Ubuntu 22.04 LTS (`ubuntu-2204-lts`)

**Rationale:**
- Used minimal instance size that fits the Yandex Cloud free tier
- Ubuntu 22.04 LTS is a stable and widely used server version
- 10 GB disk is sufficient for basic tasks and testing

### Total Cost

**$0.00** — all resources are within the Yandex Cloud free tier.

### Resources Created

1. **VPC Network** (existing `default` network was used)
   - Network ID: `enp6uso6sq07omlb3b2p`
   - Reason: quota limit for creating new networks was reached, so an existing network was used

2. **VPC Subnet**
   - Subnet ID: `e9bh0jeng28u34vpi50p`
   - Name: `lab04-subnet`
   - CIDR: `10.0.1.0/24`
   - Zone: `ru-central1-a`

3. **Security Group**
   - Security Group ID: `enp1p1d0mda36pcil266`
   - Name: `lab04-security-group`
   - Rules:
     - **SSH (port 22):** Access allowed only from IP `***.***.***.***/32`
     - **HTTP (port 80):** Access allowed from any network (`0.0.0.0/0`)
     - **Custom port 5000:** Access allowed from any network (for future application deployment)
     - **Egress:** All outbound traffic allowed

4. **Compute Instance (VM)**
   - VM ID: `fhm51jb3b2pjjr63g07f`
   - Name: `lab04-vm`
   - Public IP: `***.***.***.***`
   - Private IP: `***.***.***.***`
   - FQDN: `fhm51jb3b2pjjr63g07f.auto.internal`
   - Platform: `standard-v2`
   - Zone: `ru-central1-a`

---

## 2. Terraform Implementation

### Terraform Version

```bash
$ terraform version
Terraform v1.14.5
```

### Project Structure

```
terraform/
├── .gitignore              # Excludes secrets and state files
├── main.tf                 # Main configuration (provider, resources)
├── variables.tf            # Variable declarations
├── outputs.tf              # Outputs (IP addresses, commands)
├── terraform.tfvars        # Variable values (gitignored!)
├── terraform.tfvars.example # Variable template
├── authorized_key.json     # Service Account key (gitignored!)
├── README.md               # Usage instructions
└── SETUP_GUIDE.md          # Step-by-step setup guide
```

**Structure explanation:**
- **main.tf** — contains Yandex Cloud provider configuration, data sources (Ubuntu image, existing network), and all resources (subnet, security group, VM)
- **variables.tf** — declarations of all variables with descriptions and default values
- **outputs.tf** — outputs of important information (IP addresses, SSH command, resource IDs)
- **terraform.tfvars** — actual variable values (secrets, not committed to Git)
- **.gitignore** — excludes `*.tfstate`, `*.tfvars`, `*.json` (credentials), `.terraform/`

### Key Configuration Decisions

1. **Using existing VPC network:**
   - Problem: quota limit for creating new networks was reached (`Quota limit vpc.networks.count exceeded`)
   - Solution: used a data source to find the existing `default` network
   - Code: `data "yandex_vpc_network" "lab04_network" { name = "default" }`

2. **Security Group with SSH restriction:**
   - SSH access is allowed only from a specific IP address (`***.***.***.***/32`)
   - This improves security compared to `0.0.0.0/0`
   - HTTP and port 5000 are open for everyone (for future application deployment)

3. **Using variables:**
   - All configurable values are extracted into variables
   - This makes the code reusable and easily configurable
   - Secrets are stored in `terraform.tfvars` (gitignored)

4. **Outputs for convenience:**
   - Automatic SSH command generation
   - Output of all important IDs and IP addresses

### Challenges Encountered

1. **Quota limit for VPC networks:**
   - **Problem:** `Error: Quota limit vpc.networks.count exceeded`
   - **Solution:** Changed configuration from creating a new network to using an existing one via data source
   - **Lesson:** It's important to check provider quotas before creating resources

2. **CIDR format for Security Group:**
   - **Problem:** `Error: Illegal argument Prefix length is required: ***.***.***.***`
   - **Solution:** Added `/32` to the IP address in `terraform.tfvars` (`***.***.***.***/32`)
   - **Lesson:** Yandex Cloud requires CIDR notation for all IP addresses in security groups

3. **SSH key in metadata:**
   - Initially used the `ssh-keys` format in VM metadata
   - Format: `"${var.ssh_user}:${local.ssh_public_key}"`
   - Works correctly, SSH connection successful

### Terminal Output

#### terraform init

```bash
$ terraform init

Initializing the backend...

Initializing provider plugins...
- Finding yandex-cloud/yandex versions matching "~> 0.100"...
- Installing yandex-cloud/yandex v0.100.0...
- Installed yandex-cloud/yandex v0.100.0 (self-signed, key ID 7D8F...)

Terraform has been successfully initialized!
```

#### terraform plan (sanitized)

```bash
$ terraform plan

data.yandex_compute_image.ubuntu: Reading...
data.yandex_vpc_network.lab04_network: Reading...
data.yandex_compute_image.ubuntu: Read complete after 0s [id=fd8t9g30r3pc23et5krl]
data.yandex_vpc_network.lab04_network: Read complete after 1s [id=enp6uso6sq07omlb3b2p]

Terraform used the selected providers to generate the following execution plan.

Plan: 3 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + network_id             = "enp6uso6sq07omlb3b2p"
  + security_group_id      = (known after apply)
  + ssh_connection_command = (known after apply)
  + subnet_id              = (known after apply)
  + vm_fqdn                = (known after apply)
  + vm_id                  = (known after apply)
  + vm_name                = "lab04-vm"
  + vm_private_ip          = (known after apply)
  + vm_public_ip           = (known after apply)
```

#### terraform apply (successful)

```bash
$ terraform apply

data.yandex_compute_image.ubuntu: Reading...
data.yandex_vpc_network.lab04_network: Reading...
data.yandex_compute_image.ubuntu: Read complete after 0s [id=fd8t9g30r3pc23et5krl]
data.yandex_vpc_network.lab04_network: Read complete after 1s [id=enp6uso6sq07omlb3b2p]
yandex_vpc_subnet.lab04_subnet: Refreshing state... [id=e9bh0jeng28u34vpi50p]

Plan: 2 to add, 0 to change, 0 to destroy.

yandex_vpc_security_group.lab04_sg: Creating...
yandex_vpc_security_group.lab04_sg: Creation complete after 2s [id=enp1p1d0mda36pcil266]
yandex_compute_instance.lab04_vm: Creating...
yandex_compute_instance.lab04_vm: Still creating... [00m10s elapsed]
yandex_compute_instance.lab04_vm: Still creating... [00m20s elapsed]
yandex_compute_instance.lab04_vm: Still creating... [00m30s elapsed]
yandex_compute_instance.lab04_vm: Still creating... [00m40s elapsed]
yandex_compute_instance.lab04_vm: Creation complete after 44s [id=fhm51jb3b2pjjr63g07f]

Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

Outputs:

network_id = "enp6uso6sq07omlb3b2p"
security_group_id = "enp1p1d0mda36pcil266"
ssh_connection_command = "ssh ubuntu@***.***.***.***"
subnet_id = "e9bh0jeng28u34vpi50p"
vm_fqdn = "fhm51jb3b2pjjr63g07f.auto.internal"
vm_id = "fhm51jb3b2pjjr63g07f"
vm_name = "lab04-vm"
vm_private_ip = "***.***.***.***"
vm_public_ip = "***.***.***.***"
```

#### SSH Connection to VM

```bash
$ ssh ubuntu@***.***.***.***

The authenticity of host '***.***.***.*** (***.***.***.***)' can't be established.
ED25519 key fingerprint is SHA256:Qdh0OegJ91lCVu7Gr0vT3AHnOPIlbaSQQO1na9WUT3I.
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added '***.***.***.***' (ED25519) to the list of known hosts.

Welcome to Ubuntu 22.04.5 LTS (GNU/Linux 5.15.0-170-generic x86_64)

System information as of Thu Feb 19 12:38:47 UTC 2026

 System load:  0.1               Processes:             99
 Usage of /:   19.6% of 9.04GB   Users logged in:       0
 Memory usage: 16%               IPv4 address for eth0: ***.***.***.***
 Swap usage:   0%

ubuntu@fhm51jb3b2pjjr63g07f:~$ hostname
fhm51jb3b2pjjr63g07f

ubuntu@fhm51jb3b2pjjr63g07f:~$ uname -a
Linux fhm51jb3b2pjjr63g07f 5.15.0-170-generic #180-Ubuntu SMP Fri Jan 9 16:10:31 UTC 2026 x86_64 x86_64 x86_64 GNU/Linux

ubuntu@fhm51jb3b2pjjr63g07f:~$ exit
logout
Connection to ***.***.***.*** closed.
```

**✅ SSH connection successful!** VM is accessible and working correctly.

---

## 3. Pulumi Implementation

### Pulumi Version and Stack

- **Pulumi CLI:** `pulumi version` (current version at the time of execution)
- **Project:** `lab04-pulumi`
- **Stack:** `dev`
- **Runtime:** Python

### Project Structure

```
pulumi/
├── __main__.py           # Main infrastructure code in Python
├── requirements.txt      # Dependencies (pulumi, pulumi-yandex, setuptools)
├── Pulumi.yaml           # Project metadata
├── SETUP_INSTRUCTIONS.md # Step-by-step setup guide
├── README.md             # Project description
└── venv/                 # Python virtual environment (gitignored)
```

### Configuration

Pulumi configuration was set up via `pulumi config`:

- Namespace `yandex`:
  - `yandex:cloudId = b1g*******`
  - `yandex:folderId = b1g*******`
  - `yandex:zone = ru-central1-a`
  - `yandex:serviceAccountKeyFile` (secret) = `***/authorized_key.json`

- Project-level config:
  - `networkId = enp6uso6sq07omlb3b2p` (existing `default` network)
  - `imageId = fd8t9g30r3pc23et5krl` (Ubuntu 22.04 LTS)
  - `sshPublicKeyPath = ~/.ssh/id_rsa.pub`
  - `sshUser = ubuntu`
  - `allowedSshCidr = ***.***.***.***/32`

### Resources (Pulumi)

Infrastructure equivalent to Terraform was created:

1. **VPC Subnet**
   - Subnet ID: `e9b4b0ookvtbjtmaqi86`
   - Name: `lab04-subnet`
   - CIDR: `10.0.1.0/24`
   - Network ID: `enp6uso6sq07omlb3b2p` (same `default` network)

2. **Security Group**
   - Security Group ID: `enpq76o3rp4l9pidqonm`
   - Name: `lab04-security-group`
   - Rules:
     - **SSH (22):** `***.***.***.***/32`
     - **HTTP (80):** `0.0.0.0/0`
     - **Port 5000:** `0.0.0.0/0`
     - **Egress:** all outbound traffic

3. **Compute Instance (VM)**
   - VM ID: `fhmggcg49jpv5o80fc6l`
   - Name: `lab04-vm`
   - Public IP: `***.***.***.***`
   - Private IP: `***.***.***.***`
   - Image: Ubuntu 22.04 LTS
   - Platform: `standard-v2`
   - Zone: `ru-central1-a`

### Terminal Output (Pulumi)

#### pulumi preview / pulumi up

```bash
$ pulumi preview

Previewing update (dev)

     Type                              Name              Plan
 +   pulumi:pulumi:Stack               lab04-pulumi-dev  create
 +   ├─ yandex:index:VpcSubnet         lab04-subnet      create
 +   ├─ yandex:index:VpcSecurityGroup  lab04-sg          create
 +   └─ yandex:index:ComputeInstance   lab04-vm          create
```

```bash
$ pulumi up

Updating (dev)

     Type                              Name              Status
 +   pulumi:pulumi:Stack               lab04-pulumi-dev  creating failed     1 error
 +   ├─ yandex:index:VpcSecurityGroup  lab04-sg          created
 +   ├─ yandex:index:VpcSubnet         lab04-subnet      created
 +   └─ yandex:index:ComputeInstance   lab04-vm          creating failed     1 error

# After multiple retries and temporary Yandex Cloud API issues:
# VM was successfully created and is visible in Yandex Cloud Console.
```

#### SSH Connection to Pulumi VM

```bash
$ ssh ubuntu@***.***.***.***

Welcome to Ubuntu 22.04.5 LTS (GNU/Linux 5.15.0-170-generic x86_64)

System information as of Thu Feb 19 13:49:55 UTC 2026

 System load:  0.08              Processes:             94
 Usage of /:   19.6% of 9.04GB   Users logged in:       0
 Memory usage: 18%               IPv4 address for eth0: ***.***.***.***
 Swap usage:   0%

ubuntu@fhmggcg49jpv5o80fc6l:~$ hostname
fhmggcg49jpv5o80fc6l

ubuntu@fhmggcg49jpv5o80fc6l:~$ uname -a
Linux fhmggcg49jpv5o80fc6l 5.15.0-170-generic #180-Ubuntu SMP Fri Jan 9 16:10:31 UTC 2026 x86_64 x86_64 x86_64 GNU/Linux

ubuntu@fhmggcg49jpv5o80fc6l:~$ exit
logout
Connection to ***.***.***.*** closed.
```

### Challenges Encountered (Pulumi)

1. **Missing `pkg_resources`:**
   - **Problem:** `ModuleNotFoundError: No module named 'pkg_resources'`
   - **Solution:** added `setuptools` to `requirements.txt`, ran `pip install -r requirements.txt`

2. **Yandex Cloud API timeouts:**
   - **Problem:** `context deadline exceeded` when creating/reading resources (VM, subnet, SG)
   - **Solution:** repeated runs of `pulumi up` and `pulumi refresh`; verified state via Yandex Cloud Console
   - **Lesson:** when working with cloud APIs, temporary errors are possible; it's important to be able to verify state through the console

3. **Differences in Pulumi provider API:**
   - **Problem:** `VpcSecurityGroup` expected parameters `ingresses`/`egresses`, not `ingress`/`egress`
   - **Solution:** updated resource signature in `__main__.py`
   - **Lesson:** carefully read Pulumi provider documentation; field names may differ from Terraform

---

## 4. Terraform vs Pulumi Comparison

### Ease of Learning

- **Terraform:** easier to start with, declarative HCL, many examples and documentation; was able to describe basic infrastructure relatively quickly.
- **Pulumi:** requires knowledge of a programming language (Python), plus understanding of Pulumi concepts (stack, config), so the entry barrier is slightly higher.

### Code Readability

- **Terraform:** configuration is compact and easy to read as a declarative infrastructure description.
- **Pulumi (Python):** code is more verbose, but familiar to Python developers; convenient to use variables, functions, modules.

### Debugging & Tooling

- **Terraform:** good error messages, clear plans (`plan/apply`), but when there are quota/format errors, you need to read provider messages.
- **Pulumi:** errors are sometimes less obvious (especially with Yandex provider), but it helps that this is regular Python code, you can log and debug.

### Documentation & Ecosystem

- **Terraform:** huge ecosystem, many articles/examples, detailed documentation for providers (including Yandex Cloud).
- **Pulumi:** documentation is good, but fewer examples specifically for Yandex Cloud; sometimes you have to cross-reference with Terraform docs and map resources.

### Use Cases

- **Terraform:** excellent for standard infrastructure templates, when there are many typical resources and minimal logic.
- **Pulumi:** convenient when you need complex logic, loops, conditions, code reuse, integration with existing Python libraries.

**Personal conclusion:**  
For simple infrastructure tasks (one VM, basic networks) Terraform feels simpler and faster. Pulumi becomes more interesting when infrastructure is more complex and you need to use a full programming language.

---

## 5. Lab 5 Preparation & Cleanup

### VM for Lab 5

**Decision:** Keep one VM for Lab 5, destroy the rest.

**Current state:**
- Terraform VM: `lab04-vm` (***.***.***.***) — was created first.
- Pulumi VM: `lab04-vm` (***.***.***.***) — created second, with the same characteristics.

**Plan:**
1. Keep **Pulumi VM** (`***.***.***.***`) for Lab 5.
2. Destroy Terraform infrastructure:
   ```bash
   cd terraform
   terraform destroy
   ```

### Cleanup Status

**Current status:**
- ✅ Terraform VM created and tested
- ✅ Pulumi VM created and tested
- ⏳ Terraform resources will be destroyed (before final commit)

**Cleanup commands (when needed):**
```bash
cd terraform
terraform destroy
# Confirm deletion of all resources
```