terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# GKE Cluster
resource "google_container_cluster" "a2a_registry" {
  name     = "a2a-registry-cluster"
  location = var.region

  # We can't create a cluster with no node pool defined, but we want to only use
  # separately managed node pools. So we create the smallest possible default
  # node pool and immediately delete it.
  remove_default_node_pool = true
  initial_node_count       = 1

  network    = google_compute_network.a2a_registry.name
  subnetwork = google_compute_subnetwork.a2a_registry.name

  # Enable Workload Identity
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }
}

# Node Pool
resource "google_container_node_pool" "a2a_registry_nodes" {
  name       = "a2a-registry-node-pool"
  location   = var.region
  cluster    = google_container_cluster.a2a_registry.name
  node_count = var.node_count

  management {
    auto_repair  = true
    auto_upgrade = true
  }

  upgrade_settings {
    max_surge       = 1
    max_unavailable = 0
    strategy        = "SURGE"
  }

  node_config {
    oauth_scopes = [
      "https://www.googleapis.com/auth/logging.write",
      "https://www.googleapis.com/auth/monitoring",
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    labels = {
      env = var.project_id
    }

    machine_type = var.machine_type
    disk_size_gb = 20
    disk_type    = "pd-balanced"
    image_type   = "COS_CONTAINERD"

    metadata = {
      disable-legacy-endpoints = "true"
    }

    resource_labels = {
      "goog-gke-node-pool-provisioning-model" = "on-demand"
    }

    kubelet_config {
      cpu_cfs_quota      = false
      pod_pids_limit     = 0
      cpu_manager_policy = "static"
    }

    shielded_instance_config {
      enable_integrity_monitoring = true
      enable_secure_boot          = false
    }

    workload_metadata_config {
      mode = "GKE_METADATA"
    }
  }
}

# VPC Network
resource "google_compute_network" "a2a_registry" {
  name                    = "a2a-registry-vpc"
  auto_create_subnetworks = false
}

# Subnet
resource "google_compute_subnetwork" "a2a_registry" {
  name          = "a2a-registry-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.a2a_registry.id
}

# Static IP for Ingress
resource "google_compute_global_address" "a2a_registry" {
  name = "a2a-registry-ip"
}

# Note: SSL certificates will be managed by Cloudflare when using proxy
# This certificate is for direct access (bypassing Cloudflare) if needed
resource "google_compute_managed_ssl_certificate" "a2a_registry" {
  name = "a2a-registry-cert"
  managed {
    domains = ["${var.api_subdomain}.${var.domain}", "${var.registry_subdomain}.${var.domain}"]
  }
  count = var.enable_direct_ssl ? 1 : 0
}

# Note: Frontend config and HTTPS proxy removed - will use GKE ingress controller instead
# This simplifies the setup and avoids the complex load balancer configuration

# Note: URL Map removed - will use GKE ingress controller instead
# This simplifies the setup and avoids the complex load balancer configuration

# Note: For GKE, we'll use the native ingress controller instead of manual load balancer setup
# This simplifies the configuration and avoids the instance group issues
# The application will be accessible via the GKE ingress controller

# Health Check (kept for potential future use)
resource "google_compute_health_check" "a2a_registry" {
  name = "a2a-registry-health-check"

  http_health_check {
    port = 8000
  }
}

# Cloud Build Trigger - Commented out due to GitHub connection issues
# Will use GitHub Actions for deployment instead
# resource "google_cloudbuild_trigger" "a2a_registry" {
#   name        = "a2a-registry-build"
#   description = "Build and deploy A2A Registry"
#   location    = "global"
# 
#   github {
#     owner = "allenday"
#     name  = "a2a-registry"
#     push {
#       branch = "main"
#     }
#   }
# 
#   filename = "deploy/cloudbuild/cloudbuild.yaml"
# } 