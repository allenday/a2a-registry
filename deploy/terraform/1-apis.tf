# Enable Cloud Resource Manager API first
resource "google_project_service" "cloudresourcemanager" {
  project = var.project_id
  service = "cloudresourcemanager.googleapis.com"

  disable_dependent_services = false
  disable_on_destroy         = false

  timeouts {
    create = "30m"
    update = "40m"
  }
}

# Then enable other APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "iam.googleapis.com",          # For service account management
    "container.googleapis.com",    # For GKE
    "compute.googleapis.com",      # For networking and compute resources
    "serviceusage.googleapis.com", # For enabling other APIs
  ])

  project = var.project_id
  service = each.value

  disable_dependent_services = false
  disable_on_destroy         = false

  depends_on = [google_project_service.cloudresourcemanager]

  timeouts {
    create = "30m"
    update = "40m"
  }
}

# Verify Cloud Resource Manager API is enabled
data "google_project" "project" {
  project_id = var.project_id
  depends_on = [
    google_project_service.cloudresourcemanager,
    google_project_service.required_apis
  ]
}