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

# Frontend Config for HTTPS
resource "google_compute_global_forwarding_rule" "a2a_registry" {
  name       = "a2a-registry-frontend-config"
  target     = google_compute_target_https_proxy.a2a_registry.id
  port_range = "443"
  ip_address = google_compute_global_address.a2a_registry.address
}

# HTTPS Proxy
resource "google_compute_target_https_proxy" "a2a_registry" {
  name             = "a2a-registry-https-proxy"
  url_map          = google_compute_url_map.a2a_registry.id
  ssl_certificates = var.enable_direct_ssl ? [google_compute_managed_ssl_certificate.a2a_registry[0].id] : []
}

# URL Map with host-based routing
resource "google_compute_url_map" "a2a_registry" {
  name = "a2a-registry-url-map"

  default_service = google_compute_backend_service.a2a_registry.id

  host_rule {
    hosts        = ["${var.api_subdomain}.${var.domain}", "${var.registry_subdomain}.${var.domain}"]
    path_matcher = "api"
  }

  path_matcher {
    name            = "api"
    default_service = google_compute_backend_service.a2a_registry.id
  }
}

# Backend Service
resource "google_compute_backend_service" "a2a_registry" {
  name        = "a2a-registry-backend"
  protocol    = "HTTP"
  port_name   = "http"
  timeout_sec = 10

  backend {
    group = google_container_node_pool.a2a_registry_nodes.instance_group_urls[0]
  }

  health_checks = [google_compute_health_check.a2a_registry.id]
}

# Health Check
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

  filename = "deploy/cloudbuild/cloudbuild.yaml"
} 