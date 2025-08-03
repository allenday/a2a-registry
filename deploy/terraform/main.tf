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

    metadata = {
      disable-legacy-endpoints = "true"
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

# Cloud Build Trigger
resource "google_cloudbuild_trigger" "a2a_registry" {
  name        = "a2a-registry-build"
  description = "Build and deploy A2A Registry"

  github {
    owner = "allenday"
    name  = "a2a-registry"
    push {
      branch = "main"
    }
  }

  # Use inline build configuration instead of filename
  build {
    step {
      name = "gcr.io/cloud-builders/docker"
      args = ["build", "-t", "gcr.io/${var.project_id}/a2a-registry:$COMMIT_SHA", "-f", "deploy/Dockerfile", "."]
    }
    step {
      name = "gcr.io/cloud-builders/docker"
      args = ["push", "gcr.io/${var.project_id}/a2a-registry:$COMMIT_SHA"]
    }
    step {
      name = "gcr.io/cloud-builders/gcloud"
      args = [
        "container", "clusters", "get-credentials", 
        google_container_cluster.a2a_registry.name, 
        "--zone", var.region, 
        "--project", var.project_id
      ]
    }
    step {
      name = "gcr.io/cloud-builders/kubectl"
      args = [
        "set", "image", "deployment/a2a-registry", 
        "a2a-registry=gcr.io/${var.project_id}/a2a-registry:$COMMIT_SHA"
      ]
    }
  }
} 