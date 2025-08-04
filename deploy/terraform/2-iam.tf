# Set IAM roles after verifying API and service account
resource "google_project_iam_member" "tailscale_node" {
  project = var.project_id
  role    = "roles/container.nodeServiceAccount"
  member  = "serviceAccount:${data.google_service_account.tailscale.email}"

  depends_on = [
    data.google_project.project,
    data.google_service_account.tailscale
  ]
}