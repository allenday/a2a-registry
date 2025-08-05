resource "google_container_node_pool" "private_staging_nodes" {
  depends_on = [
    time_sleep.wait_for_iam,
    google_compute_subnetwork.private_staging,
    google_compute_firewall.tailscale
  ]
  name       = "private-staging-node-pool"
  location   = var.region
  cluster    = google_container_cluster.a2a_registry.name
  node_count = 1

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

    service_account = data.google_service_account.tailscale_data.email

    workload_metadata_config {
      mode = "GKE_METADATA"
    }
  }

  lifecycle {
    prevent_destroy = true
    create_before_destroy = true
  }
}