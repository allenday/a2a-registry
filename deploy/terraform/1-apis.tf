resource "google_project_service" "cloudresourcemanager" {
  project                    = var.project_id
  service                    = "cloudresourcemanager.googleapis.com"
  disable_dependent_services = false
  disable_on_destroy         = false
  lifecycle {
    ignore_changes        = [disable_dependent_services, disable_on_destroy]
    create_before_destroy = true
  }
}

resource "time_sleep" "wait_for_cloudresourcemanager_api" {
  depends_on      = [google_project_service.cloudresourcemanager]
  create_duration = "30s"
}

resource "google_project_service" "required_apis" {
  for_each = toset([
    "iam.googleapis.com",
    "container.googleapis.com",
    "compute.googleapis.com",
    "serviceusage.googleapis.com",
  ])
  project                    = var.project_id
  service                    = each.key
  disable_dependent_services = false
  disable_on_destroy         = false
  depends_on                 = [time_sleep.wait_for_cloudresourcemanager_api]
  lifecycle {
    ignore_changes        = [disable_dependent_services, disable_on_destroy]
    create_before_destroy = true
  }
}

resource "time_sleep" "wait_for_apis" {
  depends_on      = [google_project_service.required_apis]
  create_duration = "60s"
}