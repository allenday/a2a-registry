resource "time_sleep" "wait_for_service_account" {
  depends_on = [google_service_account.tailscale]
  create_duration = "30s"
}

resource "google_project_iam_member" "tailscale_node" {
  project = var.project_id
  role    = "roles/container.nodeServiceAccount"
  member  = "serviceAccount:${data.google_service_account.tailscale.email}"
  depends_on = [
    time_sleep.wait_for_apis,
    time_sleep.wait_for_service_account
  ]
  lifecycle {
    create_before_destroy = true
  }
}

resource "time_sleep" "wait_for_iam" {
  depends_on = [google_project_iam_member.tailscale_node]
  create_duration = "30s"
}