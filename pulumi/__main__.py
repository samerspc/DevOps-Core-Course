"""
Lab 4 - Pulumi Infrastructure for Yandex Cloud
Recreates the same infrastructure as Terraform Task 1
"""
import pulumi
import pulumi_yandex as yandex
import os

# Get configuration from Pulumi config
config = pulumi.Config()

# Yandex Cloud configuration
# Using project-specific config namespace
yandex_config = pulumi.Config("yandex")
cloud_id = yandex_config.require("cloudId")
folder_id = yandex_config.require("folderId")
zone = yandex_config.get("zone") or "ru-central1-a"
service_account_key_file = yandex_config.get_secret("serviceAccountKeyFile")

# VM configuration
project_name = config.get("projectName") or "lab04"
vm_name = config.get("vmName") or "lab04-vm"
vm_platform_id = config.get("vmPlatformId") or "standard-v2"
vm_cores = config.get_int("vmCores") or 2
vm_core_fraction = config.get_int("vmCoreFraction") or 20
vm_memory = config.get_int("vmMemory") or 1
vm_boot_disk_size = config.get_int("vmBootDiskSize") or 10
vm_image_family = config.get("vmImageFamily") or "ubuntu-2204-lts"

# SSH configuration
ssh_public_key_path = config.get("sshPublicKeyPath") or os.path.expanduser("~/.ssh/id_rsa.pub")
ssh_user = config.get("sshUser") or "ubuntu"
allowed_ssh_cidr = config.get("allowedSshCidr") or "0.0.0.0/0"

# Read SSH public key
with open(ssh_public_key_path, "r") as f:
    ssh_public_key = f.read().strip()

# Get existing VPC network ID from config
# We use existing "default" network to avoid quota limits
# Network ID from previous Terraform run or from config
network_id = config.get("networkId") or "enp6uso6sq07omlb3b2p"

# Create subnet
subnet = yandex.VpcSubnet(
    "lab04-subnet",
    name=f"{project_name}-subnet",
    zone=zone,
    network_id=network_id,
    v4_cidr_blocks=["10.0.1.0/24"],
    labels={
        "project": project_name,
        "lab": "lab04"
    }
)

# Create security group
security_group = yandex.VpcSecurityGroup(
    "lab04-sg",
    name=f"{project_name}-security-group",
    description="Security group for Lab 4 VM",
    network_id=network_id,
    ingresses=[
        yandex.VpcSecurityGroupIngressArgs(
            description="SSH",
            protocol="TCP",
            port=22,
            v4_cidr_blocks=[allowed_ssh_cidr]
        ),
        yandex.VpcSecurityGroupIngressArgs(
            description="HTTP",
            protocol="TCP",
            port=80,
            v4_cidr_blocks=["0.0.0.0/0"]
        ),
        yandex.VpcSecurityGroupIngressArgs(
            description="Custom app port",
            protocol="TCP",
            port=5000,
            v4_cidr_blocks=["0.0.0.0/0"]
        )
    ],
    egresses=[
        yandex.VpcSecurityGroupEgressArgs(
            description="All outbound",
            protocol="ANY",
            v4_cidr_blocks=["0.0.0.0/0"]
        )
    ],
    labels={
        "project": project_name,
        "lab": "lab04"
    }
)

# Get latest Ubuntu image ID
# Using the same image ID as Terraform (Ubuntu 22.04 LTS)
image_id = config.get("imageId") or "fd8t9g30r3pc23et5krl"

# Create compute instance
vm = yandex.ComputeInstance(
    "lab04-vm",
    name=vm_name,
    platform_id=vm_platform_id,
    zone=zone,
    resources=yandex.ComputeInstanceResourcesArgs(
        cores=vm_cores,
        core_fraction=vm_core_fraction,
        memory=vm_memory
    ),
    boot_disk=yandex.ComputeInstanceBootDiskArgs(
        initialize_params=yandex.ComputeInstanceBootDiskInitializeParamsArgs(
            image_id=image_id,
            size=vm_boot_disk_size,
            type="network-hdd"
        )
    ),
    network_interfaces=[
        yandex.ComputeInstanceNetworkInterfaceArgs(
            subnet_id=subnet.id,
            security_group_ids=[security_group.id],
            nat=True  # Enable public IP
        )
    ],
    metadata={
        "ssh-keys": f"{ssh_user}:{ssh_public_key}"
    },
    labels={
        "project": project_name,
        "lab": "lab04",
        "env": "dev"
    }
)

# Export outputs
pulumi.export("vm_id", vm.id)
pulumi.export("vm_name", vm.name)
pulumi.export("vm_public_ip", vm.network_interfaces[0].nat_ip_address)
pulumi.export("vm_private_ip", vm.network_interfaces[0].ip_address)
pulumi.export("vm_fqdn", vm.fqdn)
pulumi.export("ssh_connection_command", pulumi.Output.concat("ssh ", ssh_user, "@", vm.network_interfaces[0].nat_ip_address))
pulumi.export("network_id", network_id)
pulumi.export("subnet_id", subnet.id)
pulumi.export("security_group_id", security_group.id)
