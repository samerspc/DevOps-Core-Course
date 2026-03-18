variable "yandex_cloud_id" {
  description = "Yandex Cloud ID"
  type        = string
  sensitive   = true
}

variable "yandex_folder_id" {
  description = "Yandex Cloud Folder ID"
  type        = string
  sensitive   = true
}

variable "yandex_zone" {
  description = "Yandex Cloud zone (e.g., ru-central1-a)"
  type        = string
  default     = "ru-central1-a"
}

variable "yandex_token" {
  description = "Yandex Cloud OAuth token or service account key file path"
  type        = string
  sensitive   = true
  default     = ""
}

variable "yandex_service_account_key_file" {
  description = "Path to Yandex Cloud service account key file (JSON)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "vm_name" {
  description = "Name of the virtual machine"
  type        = string
  default     = "lab04-vm"
}

variable "vm_platform_id" {
  description = "Platform ID for VM (standard-v2 for free tier)"
  type        = string
  default     = "standard-v2"
}

variable "vm_cores" {
  description = "Number of CPU cores"
  type        = number
  default     = 2
}

variable "vm_core_fraction" {
  description = "CPU core fraction (20 for free tier)"
  type        = number
  default     = 20
}

variable "vm_memory" {
  description = "Amount of memory in GB"
  type        = number
  default     = 1
}

variable "vm_boot_disk_size" {
  description = "Boot disk size in GB"
  type        = number
  default     = 10
}

variable "vm_image_family" {
  description = "Image family (e.g., ubuntu-2204-lts)"
  type        = string
  default     = "ubuntu-2204-lts"
}

variable "ssh_public_key_path" {
  description = "Path to SSH public key file"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

variable "ssh_user" {
  description = "SSH username for VM"
  type        = string
  default     = "ubuntu"
}

variable "allowed_ssh_cidr" {
  description = "CIDR block allowed for SSH access (your IP)"
  type        = string
  default     = "0.0.0.0/0"  # Change to your IP for better security!
}

variable "project_name" {
  description = "Project name for resource tagging"
  type        = string
  default     = "lab04"
}
