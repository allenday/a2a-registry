output "cluster_name" {
  description = "The name of the GKE cluster"
  value       = google_container_cluster.a2a_registry.name
}

output "cluster_endpoint" {
  description = "The IP address of the GKE cluster endpoint"
  value       = google_container_cluster.a2a_registry.endpoint
}

output "static_ip" {
  description = "The static IP address for the load balancer (if using direct SSL)"
  value       = var.enable_direct_ssl ? google_compute_global_address.a2a_registry.address : "Not configured - using GKE ingress"
}

output "domain" {
  description = "The domain name for the application"
  value       = var.domain
}

output "project_id" {
  description = "The GCP project ID"
  value       = var.project_id
}

output "region" {
  description = "The GCP region"
  value       = var.region
} 