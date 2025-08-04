# Network resources after APIs are enabled
resource "google_compute_subnetwork" "private_staging" {
  name          = "private-staging-subnet"
  ip_cidr_range = "10.0.1.0/24" # Different range from main subnet
  region        = var.region
  network       = google_compute_network.a2a_registry.id

  depends_on = [data.google_project.project]
}

resource "google_compute_firewall" "tailscale" {
  name    = "allow-tailscale"
  network = google_compute_network.a2a_registry.name

  allow {
    protocol = "udp"
    ports    = ["41641"] # Default Tailscale port
  }

  source_ranges = ["0.0.0.0/0"] # Tailscale nodes can be anywhere
  target_tags   = ["tailscale"]

  depends_on = [data.google_project.project]
}