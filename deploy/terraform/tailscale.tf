# Tailscale subnet for private staging
resource "google_compute_subnetwork" "private_staging" {
  name          = "private-staging-subnet"
  ip_cidr_range = "10.0.1.0/24" # Different range from main subnet
  region        = var.region
  network       = google_compute_network.a2a_registry.id

  depends_on = [google_project_service.required_apis]

  lifecycle {
    create_before_destroy = true
  }
}

# Firewall rule for Tailscale
resource "google_compute_firewall" "tailscale" {
  name    = "allow-tailscale"
  network = google_compute_network.a2a_registry.name

  allow {
    protocol = "udp"
    ports    = ["41641"] # Default Tailscale port
  }

  source_ranges = ["0.0.0.0/0"] # Tailscale nodes can be anywhere
  target_tags   = ["tailscale"]

  depends_on = [google_project_service.required_apis]

  lifecycle {
    create_before_destroy = true
  }
}

# IAM role for Tailscale
resource "google_service_account" "tailscale" {
  account_id   = "tailscale-sa"
  display_name = "Tailscale Service Account"

  depends_on = [google_project_service.required_apis]

  lifecycle {
    create_before_destroy = true
  }
}

# Wait for service account to be fully created
resource "time_sleep" "wait_for_service_account" {
  depends_on = [google_service_account.tailscale]

  create_duration = "30s"
}

resource "google_project_iam_member" "tailscale_node" {
  project = var.project_id
  role    = "roles/container.nodeServiceAccount"
  member  = "serviceAccount:${google_service_account.tailscale.email}"

  depends_on = [
    google_project_service.required_apis,
    time_sleep.wait_for_service_account
  ]

  lifecycle {
    create_before_destroy = true
  }
}

# Wait for IAM to propagate
resource "time_sleep" "wait_for_iam" {
  depends_on = [google_project_iam_member.tailscale_node]

  create_duration = "30s"
}

# Add Tailscale node pool
resource "google_container_node_pool" "private_staging_nodes" {
  name       = "private-staging-node-pool"
  location   = var.region
  cluster    = google_container_cluster.a2a_registry.name
  node_count = 1

  depends_on = [
    google_project_service.required_apis,
    time_sleep.wait_for_iam
  ]

  management {
    auto_repair  = true
    auto_upgrade = true
  }

  node_config {
    oauth_scopes = [
      "https://www.googleapis.com/auth/logging.write",
      "https://www.googleapis.com/auth/monitoring",
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    labels = {
      env = "private-staging"
    }

    tags = ["tailscale"] # Apply Tailscale firewall rules

    machine_type = "e2-micro"
    disk_size_gb = 20
    disk_type    = "pd-balanced"
    image_type   = "COS_CONTAINERD"

    service_account = google_service_account.tailscale.email

    workload_metadata_config {
      mode = "GKE_METADATA"
    }
  }

  lifecycle {
    create_before_destroy = true
  }
}