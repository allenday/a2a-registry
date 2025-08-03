variable "project_id" {
  description = "The GCP project ID"
  type        = string
  default     = "a2a-registry-dev"
}

variable "region" {
  description = "The GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "node_count" {
  description = "Number of nodes in the GKE cluster"
  type        = number
  default     = 1
}

variable "machine_type" {
  description = "Machine type for GKE nodes"
  type        = string
  default     = "e2-micro"
}

variable "domain" {
  description = "Base domain name for the application"
  type        = string
  default     = "a2a-registry.dev"
}

variable "api_subdomain" {
  description = "Subdomain for API endpoints"
  type        = string
  default     = "api"
}

variable "registry_subdomain" {
  description = "Subdomain for main registry application"
  type        = string
  default     = "registry"
}

variable "enable_direct_ssl" {
  description = "Enable direct SSL certificates (disable when using Cloudflare proxy)"
  type        = bool
  default     = false
}

variable "use_cloudflare" {
  description = "Whether to use Cloudflare proxy for subdomains"
  type        = bool
  default     = true
} 