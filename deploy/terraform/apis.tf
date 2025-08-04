# Enable required Google Cloud APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "cloudresourcemanager.googleapis.com", # For IAM and project-level operations
    "iam.googleapis.com",                  # For service account management
    "container.googleapis.com",            # For GKE
    "compute.googleapis.com",              # For networking and compute resources
    "serviceusage.googleapis.com",         # For enabling other APIs
  ])

  project = var.project_id
  service = each.value

  disable_dependent_services = false
  disable_on_destroy         = false

  # Handle the case where APIs are already enabled
  lifecycle {
    ignore_changes = [disable_dependent_services, disable_on_destroy]
  }
}