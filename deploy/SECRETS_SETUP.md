# Secrets and Environment Variables Setup

This guide explains how to configure environment variables and secrets for the A2A Registry deployment.

## Local Development Setup

### 1. Create Local Environment File

Copy the example file and customize it:

```bash
cp env.example .env
```

### 2. Edit `.env` File

```bash
# GCP Configuration
GCP_PROJECT_ID=a2a-registry-dev
GCP_REGION=us-central1
GCP_CLUSTER_NAME=a2a-registry-cluster

# Domain Configuration
DOMAIN=a2a-registry.dev
API_SUBDOMAIN=api
REGISTRY_SUBDOMAIN=registry

# Deployment Configuration
USE_CLOUDFLARE=true
ENABLE_DIRECT_SSL=false

# Docker Configuration
DOCKER_REGISTRY=gcr.io
DOCKER_IMAGE_NAME=a2a-registry
```

### 3. Load Environment Variables

Add this to your shell profile (`.bashrc`, `.zshrc`, etc.):

```bash
# Load A2A Registry environment variables
if [ -f /path/to/a2a-registry/.env ]; then
    export $(cat /path/to/a2a-registry/.env | grep -v '^#' | xargs)
fi
```

## GitHub Secrets Setup

### Required Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

#### 1. GCP Service Account Key
```
Name: GCP_SA_KEY
Value: [Base64 encoded service account JSON]
```

#### 2. PyPI Tokens
```
Name: PYPI_API_TOKEN
Value: [Your PyPI API token]

Name: TEST_PYPI_API_TOKEN  
Value: [Your TestPyPI API token]
```

#### 3. Cloudflare API Token (Optional)
```
Name: CLOUDFLARE_API_TOKEN
Value: [Your Cloudflare API token]
```

### How to Create GCP Service Account

1. **Create Service Account**
```bash
gcloud iam service-accounts create a2a-registry-sa \
    --display-name="A2A Registry Service Account"
```

2. **Grant Permissions**
```bash
# Get the service account email
SA_EMAIL=$(gcloud iam service-accounts list --filter="displayName:A2A Registry Service Account" --format="value(email)")

# Grant necessary roles
gcloud projects add-iam-policy-binding a2a-registry-dev \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/container.admin"

gcloud projects add-iam-policy-binding a2a-registry-dev \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding a2a-registry-dev \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/cloudbuild.builds.builder"

gcloud projects add-iam-policy-binding a2a-registry-dev \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/compute.admin"
```

3. **Create and Download Key**
```bash
gcloud iam service-accounts keys create ~/a2a-registry-sa-key.json \
    --iam-account=$SA_EMAIL
```

4. **Encode for GitHub**
```bash
base64 -i ~/a2a-registry-sa-key.json | tr -d '\n'
```

5. **Add to GitHub Secrets**
- Copy the base64 output
- Add as `GCP_SA_KEY` secret in GitHub

## Environment Variables in GitHub Actions

### Repository Variables (Non-sensitive)

Go to Settings → Secrets and variables → Actions → Variables tab

```
Name: GCP_PROJECT_ID
Value: a2a-registry-dev

Name: GCP_REGION  
Value: us-central1

Name: GCP_CLUSTER_NAME
Value: a2a-registry-cluster

Name: DOMAIN
Value: a2a-registry.dev

Name: API_SUBDOMAIN
Value: api

Name: REGISTRY_SUBDOMAIN
Value: registry

Name: USE_CLOUDFLARE
Value: true

Name: ENABLE_DIRECT_SSL
Value: false
```

## Terraform Configuration

### Using Environment Variables

Update `deploy/terraform/main.tf` to use environment variables:

```hcl
variable "project_id" {
  description = "The GCP project ID"
  type        = string
  default     = "a2a-registry-dev"
}

variable "region" {
  description = "The GCP region for resources"
  type        = string
  default     = "us-central1"
}
```

### Local Development with Terraform

```bash
# Set environment variables
export TF_VAR_project_id=a2a-registry-dev
export TF_VAR_region=us-central1
export TF_VAR_use_cloudflare=true
export TF_VAR_enable_direct_ssl=false

# Run Terraform
cd deploy/terraform
terraform init
terraform plan
terraform apply
```

## Security Best Practices

### 1. Never Commit Secrets
- Add `.env` to `.gitignore`
- Use GitHub Secrets for sensitive data
- Use environment variables for non-sensitive config

### 2. Rotate Keys Regularly
- Rotate GCP service account keys quarterly
- Rotate PyPI tokens annually
- Monitor for unauthorized access

### 3. Principle of Least Privilege
- Grant minimum required permissions
- Use specific IAM roles
- Review permissions regularly

### 4. Environment Separation
- Use different projects for dev/staging/prod
- Use different service accounts per environment
- Use different domains per environment

## Troubleshooting

### Common Issues

1. **Permission Denied**
   - Check service account permissions
   - Verify project ID is correct
   - Ensure API is enabled

2. **Authentication Failed**
   - Verify service account key is valid
   - Check if key is base64 encoded correctly
   - Ensure key hasn't expired

3. **Environment Variables Not Found**
   - Check variable names match exactly
   - Verify variables are set in correct environment
   - Check for typos in variable names

### Verification Commands

```bash
# Check GCP authentication
gcloud auth list

# Check current project
gcloud config get-value project

# Test service account
gcloud auth activate-service-account --key-file=~/a2a-registry-sa-key.json

# Verify permissions
gcloud projects get-iam-policy a2a-registry-dev
``` 