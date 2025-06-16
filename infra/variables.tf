variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "project_id_number" {
  description = "GCP Project ID Number"
  type        = string
}

variable "project_name" {
  description = "Project Name"
  type        = string
}

variable "region" {
  description = "Region for resources"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "Zone for resources"
  type        = string
}

variable "cidr_range" {
  description = "Region for resources"
  type        = string
  default     = "10.10.0.0/24"
}

variable "vm_machine_type" {
  description = "VM machine type"
  default     = "e2-small"
}

variable "vm_image" {
  description = "VM boot image"
  default     = "ubuntu-os-cloud/ubuntu-2204-lts"
}

variable "secret_name_cert_fullchain" {
  description = "Secret name for SSL certificates fullchain.pem"
  type        = string
}

variable "secret_name_cert_privatekey" {
  description = "Secret name for SSL certificates private key"
  type        = string
}

variable "domain" {
  description = "Domain on which app needs to run"
  type        = string
}

variable "redeploy_version" {
  description = "Change this to trigger rolling redeploy (e.g., v1, v2)"
  type        = string
  default     = "v1"
}
