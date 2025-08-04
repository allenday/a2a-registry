# Create service account first
resource "google_service_account" "tailscale" {
  account_id   = "tailscale-sa"
  display_name = "Tailscale Service Account"
}

# Verify service account exists
data "google_service_account" "tailscale" {
  account_id = google_service_account.tailscale.account_id
  depends_on = [google_service_account.tailscale]
}