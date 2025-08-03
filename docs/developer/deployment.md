# Deployment Guide

This guide explains how to deploy the A2A Registry to Google Cloud Platform using GitHub Actions.

## 🏗️ **Infrastructure Management**

### Terraform Workflow

The infrastructure is managed through a dedicated Terraform workflow:

**File:** `.github/workflows/terraform.yml`

**Triggers:**
- ✅ **Automatic**: On push/PR to `deploy/terraform/**`
- ✅ **Manual**: Via GitHub Actions UI with options

**Actions Available:**
- `plan`: Show what changes will be made
- `apply`: Apply infrastructure changes
- `destroy`: Destroy all infrastructure (⚠️ dangerous)

### Manual Terraform Commands

For local development or CI/CD:

```bash
# Initialize Terraform
make terraform-init

# Plan changes
make terraform-plan

# Apply changes
make terraform-apply

# Destroy infrastructure
make terraform-destroy
```

### GitHub Actions Terraform Triggers

For manual runs via GitHub Actions:

```bash
# Plan via GitHub Actions
make terraform-plan-gh

# Apply via GitHub Actions
make terraform-apply-gh

# Destroy via GitHub Actions
make terraform-destroy-gh

# Check workflow status
make terraform-status
```

## 🚀 **Application Deployment**

### Deployment Workflow

**File:** `.github/workflows/deploy.yml`

**Triggers:**
- ✅ **Automatic**: On push to `main` (excluding Terraform changes)
- ✅ **Manual**: Via GitHub Actions UI

**What it does:**
1. Builds Docker image
2. Pushes to Google Container Registry
3. Deploys to GKE cluster
4. Verifies deployment

### Manual Deployment Commands

```bash
# Build Docker image
make deploy-build

# Build and push to GCR
make deploy-push

# Full GCP deployment (build, push, deploy)
make deploy-gcp

# Deploy to local Kubernetes
make deploy-local
```

## 🔄 **Complete Deployment Process**

### First-Time Setup

1. **Set up GitHub Secrets:**
   ```
   GCP_PROJECT_ID=a2a-registry-dev
   GCP_REGION=us-central1
   GCP_CLUSTER_NAME=a2a-registry-cluster
   GCP_SA_KEY=[base64-encoded-service-account-key]
   ```

2. **Create Infrastructure:**
   ```bash
   # Option A: Via GitHub Actions (recommended)
   make terraform-apply-gh
   
   # Option B: Locally
   make terraform-apply
   ```

3. **Deploy Application:**
   ```bash
   # Option A: Via GitHub Actions (recommended)
   # Go to Actions → Deploy to GCP → Run workflow
   
   # Option B: Locally
   make deploy-gcp
   ```

### Regular Deployments

**For code changes:**
- Push to `main` branch
- GitHub Actions automatically deploys

**For infrastructure changes:**
- Push to `main` branch with changes in `deploy/terraform/**`
- Terraform workflow runs automatically
- Deployment workflow skips (no app changes)

**For manual deployments:**
- Use GitHub Actions UI
- Or run locally: `make deploy-gcp`

## 🏗️ **Infrastructure Components**

### GKE Cluster
- **Nodes**: 1 e2-micro instance
- **Region**: us-central1
- **Network**: Custom VPC with subnet

### Load Balancer
- **Type**: Global HTTPS load balancer
- **Static IP**: Reserved for the application
- **Domains**: 
  - `api.a2a-registry.dev`
  - `registry.a2a-registry.dev`

### Storage
- **Type**: File-based persistent storage
- **Volume**: 1Gi PersistentVolumeClaim
- **Path**: `/data/agents.json`

### Cloud Build
- **Trigger**: Automatic on push to `main`
- **Build**: Docker image from `deploy/Dockerfile`
- **Push**: To Google Container Registry

## 🔧 **Configuration**

### Environment Variables

**Local Development:**
```bash
# Copy example
cp env.example .env

# Edit with your values
nano .env
```

**Kubernetes Deployment:**
```yaml
env:
- name: STORAGE_TYPE
  value: "file"
- name: STORAGE_DATA_DIR
  value: "/data"
- name: LOG_LEVEL
  value: "INFO"
```

### Secrets Management

**GitHub Secrets:**
- `GCP_SA_KEY`: Base64-encoded service account JSON
- `GCP_PROJECT_ID`: Your GCP project ID
- `GCP_REGION`: GCP region (e.g., us-central1)
- `GCP_CLUSTER_NAME`: GKE cluster name

**Service Account Permissions:**
- `roles/container.admin`
- `roles/storage.admin`
- `roles/cloudbuild.builds.builder`
- `roles/compute.admin`

## 📊 **Monitoring and Logs**

### View Logs

```bash
# Application logs
kubectl logs -f deployment/a2a-registry

# Storage-related logs
kubectl logs deployment/a2a-registry | grep -i storage

# All pods
kubectl get pods -l app=a2a-registry
```

### Check Status

```bash
# Deployment status
kubectl rollout status deployment/a2a-registry

# Service status
kubectl get service a2a-registry-service

# Ingress status
kubectl get ingress a2a-registry-ingress
```

### Health Checks

```bash
# Application health
curl https://api.a2a-registry.dev/health

# Registry health
curl https://registry.a2a-registry.dev/health
```

## 🔄 **Workflow Integration**

### Automatic Triggers

**Infrastructure Changes:**
```
Push to main with terraform changes
↓
Terraform workflow runs
↓
Plan → Apply (if approved)
```

**Application Changes:**
```
Push to main (no terraform changes)
↓
Deploy workflow runs
↓
Build → Push → Deploy
```

### Manual Triggers

**Infrastructure:**
- GitHub Actions → Terraform Infrastructure → Run workflow
- Choose action: plan/apply/destroy

**Application:**
- GitHub Actions → Deploy to GCP → Run workflow
- Force deployment if needed

## 🛠️ **Troubleshooting**

### Common Issues

1. **Terraform Plan Fails:**
   ```bash
   # Check Terraform syntax
   cd deploy/terraform && terraform validate
   
   # Check formatting
   cd deploy/terraform && terraform fmt -check
   ```

2. **Deployment Fails:**
   ```bash
   # Check pod status
   kubectl describe pod -l app=a2a-registry
   
   # Check logs
   kubectl logs deployment/a2a-registry
   ```

3. **Storage Issues:**
   ```bash
   # Check PVC status
   kubectl get pvc registry-data-pvc
   
   # Check volume mount
   kubectl exec -it deployment/a2a-registry -- ls -la /data
   ```

4. **Network Issues:**
   ```bash
   # Check ingress status
   kubectl describe ingress a2a-registry-ingress
   
   # Check DNS resolution
   nslookup api.a2a-registry.dev
   ```

### Rollback

```bash
# Rollback deployment
kubectl rollout undo deployment/a2a-registry

# Check rollback status
kubectl rollout status deployment/a2a-registry
```

## 🔒 **Security**

### Best Practices

1. **Service Account:**
   - Use least privilege principle
   - Rotate keys regularly
   - Monitor usage

2. **Network:**
   - Use private GKE cluster
   - Configure firewall rules
   - Enable Cloud Armor

3. **Storage:**
   - Encrypt persistent volumes
   - Use secure file permissions
   - Regular backups

4. **Secrets:**
   - Store in GitHub Secrets
   - Never commit to repository
   - Use environment-specific values

## 📈 **Scaling**

### Horizontal Scaling

```bash
# Scale deployment
kubectl scale deployment a2a-registry --replicas=3

# Auto-scaling (future)
kubectl autoscale deployment a2a-registry --min=1 --max=5 --cpu-percent=80
```

### Vertical Scaling

```yaml
# Update resource limits in deploy/k8s/deployment.yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### Infrastructure Scaling

```bash
# Scale GKE node pool
gcloud container clusters resize a2a-registry-cluster \
  --node-pool=a2a-registry-node-pool \
  --num-nodes=3 \
  --region=us-central1
``` 