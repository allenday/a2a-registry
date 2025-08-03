# A2A Registry Deployment

This directory contains all deployment-related files for the A2A Registry.

## Directory Structure

```
deploy/
├── README.md                 # This file
├── Dockerfile                # Container image definition
├── cloudbuild/
│   └── cloudbuild.yaml       # Google Cloud Build configuration
├── k8s/
│   └── deployment.yaml       # Kubernetes manifests
└── terraform/
    ├── main.tf               # Main Terraform configuration
    ├── variables.tf          # Variable definitions
    └── outputs.tf            # Output definitions
```

## Quick Start

### 1. Build and Deploy to GCP

```bash
# Set up GCP project
gcloud config set project YOUR_PROJECT_ID

# Deploy infrastructure with Terraform
cd deploy/terraform
terraform init
terraform plan
terraform apply

# Build and deploy application
cd ../..
gcloud builds submit --config deploy/cloudbuild/cloudbuild.yaml .
```

### 2. Local Development

```bash
# Build container locally
docker build -f deploy/Dockerfile -t a2a-registry:latest .

# Run locally
docker run -p 8000:8000 a2a-registry:latest
```

### 3. Kubernetes Deployment

```bash
# Apply Kubernetes manifests
kubectl apply -f deploy/k8s/
```

## Configuration

### Environment Variables

- `LOG_LEVEL`: Logging level (default: INFO)
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)

### GCP Resources

The Terraform configuration creates:
- GKE cluster with node pool
- VPC network and subnet
- Load balancer with SSL certificate
- Cloud Build trigger for CI/CD

### Domain Configuration

To use a custom domain (e.g., `a2a-registry.dev`):
1. Update the domain in `deploy/terraform/main.tf`
2. Point your domain's DNS to the static IP created by Terraform
3. The SSL certificate will be automatically provisioned

## Security

- Container runs as non-root user
- HTTPS enabled with managed SSL certificates
- Network policies can be added to restrict traffic
- Secrets should be stored in GCP Secret Manager

## Monitoring

- Health checks configured for both liveness and readiness
- GCP Cloud Monitoring integration
- Logs available in Cloud Logging

## Troubleshooting

### Common Issues

1. **Container won't start**: Check logs with `kubectl logs`
2. **Health check failures**: Verify the `/health` endpoint is working
3. **SSL certificate issues**: Ensure DNS is properly configured
4. **Build failures**: Check Cloud Build logs in GCP Console

### Useful Commands

```bash
# Check pod status
kubectl get pods -l app=a2a-registry

# View logs
kubectl logs -l app=a2a-registry

# Port forward for local testing
kubectl port-forward svc/a2a-registry-service 8000:80

# Check ingress status
kubectl get ingress a2a-registry-ingress
``` 