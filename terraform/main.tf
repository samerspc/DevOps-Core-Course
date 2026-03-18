terraform {
  required_version = ">= 1.9"
  
  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = "~> 0.100"
    }
  }
}

# Configure Yandex Cloud provider
provider "yandex" {
  cloud_id                 = var.yandex_cloud_id
  folder_id                = var.yandex_folder_id
  zone                     = var.yandex_zone
  token                    = var.yandex_token != "" ? var.yandex_token : null
  service_account_key_file = var.yandex_service_account_key_file != "" ? var.yandex_service_account_key_file : null
}

# Get latest Ubuntu image
data "yandex_compute_image" "ubuntu" {
  family = var.vm_image_family
}

# Use existing VPC network to avoid hitting vpc.networks.count quota
# Tries to find network with name \"default\" in this folder
data "yandex_vpc_network" "lab04_network" {
  name = "default"
}

# Create subnet
resource "yandex_vpc_subnet" "lab04_subnet" {
  name           = "${var.project_name}-subnet"
  zone           = var.yandex_zone
  network_id     = data.yandex_vpc_network.lab04_network.id
  v4_cidr_blocks = ["10.0.1.0/24"]
  
  labels = {
    project = var.project_name
    lab     = "lab04"
  }
}

# Create security group
resource "yandex_vpc_security_group" "lab04_sg" {
  name        = "${var.project_name}-security-group"
  description = "Security group for Lab 4 VM"
  network_id  = data.yandex_vpc_network.lab04_network.id

  # Allow SSH from specified IP
  ingress {
    description    = "SSH"
    protocol       = "TCP"
    port           = 22
    v4_cidr_blocks = [var.allowed_ssh_cidr]
  }

  # Allow HTTP
  ingress {
    description    = "HTTP"
    protocol       = "TCP"
    port           = 80
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow custom port 5000 (for future app deployment)
  ingress {
    description    = "Custom app port"
    protocol       = "TCP"
    port           = 5000
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow all outbound traffic
  egress {
    description    = "All outbound"
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  labels = {
    project = var.project_name
    lab     = "lab04"
  }
}

# Read SSH public key
locals {
  ssh_public_key = file(var.ssh_public_key_path)
}

# Create compute instance
resource "yandex_compute_instance" "lab04_vm" {
  name        = var.vm_name
  platform_id = var.vm_platform_id
  zone        = var.yandex_zone

  resources {
    cores         = var.vm_cores
    core_fraction = var.vm_core_fraction
    memory        = var.vm_memory
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.id
      size     = var.vm_boot_disk_size
      type     = "network-hdd"  # HDD for free tier
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.lab04_subnet.id
    security_group_ids = [yandex_vpc_security_group.lab04_sg.id]
    nat                = true  # Enable public IP
  }

  metadata = {
    ssh-keys = "${var.ssh_user}:${local.ssh_public_key}"
  }

  labels = {
    project = var.project_name
    lab     = "lab04"
    env     = "dev"
  }

  scheduling_policy {
    preemptible = false
  }
}
