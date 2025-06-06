variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "Region for resources"
  type        = string
  default     = "us-central1"
}

variable "vm_machine_type" {
  description = "VM machine type"
  default     = "e2-medium"
}

variable "vm_image" {
  description = "VM boot image"
  default     = "ubuntu-os-cloud/ubuntu-2204-lts"
}

variable "mongo_uri" {
  description = "MongoDB Atlas URI"
  type        = string
  sensitive   = true
}

variable "frontend_api_url" {
  description = "Base URL for the FastAPI backend"
  type        = string
  default     = "{Add here your API domain name}}/api/explorer/search"
}

variable "redeploy_version" {
  description = "Change this to trigger rolling redeploy (e.g., v1, v2)"
  type        = string
  default     = "v1"
}
