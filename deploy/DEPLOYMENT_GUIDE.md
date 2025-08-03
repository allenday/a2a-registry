# A2A Registry Deployment Guide

This guide covers the deployment process for the A2A Registry service to Google Cloud Platform (GCP) using Google Kubernetes Engine (GKE).

## Overview

The A2A Registry is deployed using a multi-environment approach with:
- **Production**: Main deployment for live traffic
- **Staging**: Pre-production environment for testing

## Prerequisites

### GCP Setup
1. **GCP Project**: Ensure you have a GCP project with billing enabled
2. **GKE Cluster**: A running GKE cluster in your desired region
3. **Service Account**: A service account with the following roles:
   - `roles/container.developer`
   - `roles/storage.admin`
   - `roles/iam.serviceAccountUser`

### GitHub Secrets
Configure the following secrets in your GitHub repository:
- `GCP_PROJECT_ID`: Your GCP project ID
- `GCP_REGION`: GKE cluster region (e.g., `us-central1`)
- `GCP_CLUSTER_NAME`: Name of your GKE cluster
- `GCP_SA_KEY`: JSON key for the service account

## Deployment Workflows

### Automatic Deployment
The main deployment workflow (`.github/workflows/deploy.yml`) automatically triggers on:
- Push to `main` branch (excluding Terraform changes)
- Manual workflow dispatch

### Manual Deployment
You can manually trigger deployments with:
1. Go to GitHub Actions → Deploy to GCP
2. Click "Run workflow"
3. Select environment (staging/production)
4. Optionally force deployment

### Rollback
Use the rollback workflow (`.github/workflows/rollback.yml`) to:
1. Go to GitHub Actions → Rollback Deployment
2. Select environment
3. Provide rollback reason
4. Optionally specify image tag

## Environment Configuration

### Production Environment
- **Deployment**: `a2a-registry`
- **Service**: `a2a-registry-service`
- **Ingress**: `a2a-registry-ingress`
- **Resources**: 128Mi-256Mi memory, 100m-200m CPU
- **Storage**: 1Gi persistent volume
- **Domains**: `api.a2a-registry.dev`, `registry.a2a-registry.dev`

### Staging Environment
- **Deployment**: `a2a-registry-staging`
- **Service**: `a2a-registry-staging-service`
- **Ingress**: `a2a-registry-staging-ingress`
- **Resources**: 64Mi-128Mi memory, 50m-100m CPU
- **Storage**: 500Mi persistent volume
- **Domains**: `staging.api.a2a-registry.dev`, `staging.registry.a2a-registry.dev`

## Deployment Process

### 1. Build and Test
- Checkout code with full history
- Set up Python 3.11 environment
- Install dependencies
- Run tests with coverage
- Upload coverage to Codecov

### 2. Container Build
- Authenticate to Google Cloud
- Build Docker image with commit SHA tag
- Tag as `latest`
- Push both tags to Google Container Registry

### 3. Kubernetes Deployment
- Get GKE cluster credentials
- Apply environment-specific manifests
- Update deployment with new image
- Wait for rollout completion
- Verify pod readiness

### 4. Health Verification
- Test health endpoint
- Verify service accessibility
- Check ingress configuration
- Monitor application logs

## Monitoring and Alerting

### Prometheus Integration
The deployment includes Prometheus monitoring with:
- **Service Monitors**: Automatic metrics collection
- **Alert Rules**: Predefined alerts for common issues

### Key Metrics
- Application uptime
- Error rates (5xx responses)
- Response latency (95th percentile)
- Resource usage (CPU, memory)

### Alerts
- **Critical**: Service down
- **Warning**: High error rate, high latency, high resource usage

## Troubleshooting

### Common Issues

#### Deployment Fails
1. Check GKE cluster status: `gcloud container clusters list`
2. Verify service account permissions
3. Check container registry access
4. Review deployment logs: `kubectl logs -l app=a2a-registry`

#### Pods Not Ready
1. Check pod status: `kubectl get pods -l app=a2a-registry`
2. Describe pod for details: `kubectl describe pod <pod-name>`
3. Check container logs: `kubectl logs <pod-name>`
4. Verify resource limits and requests

#### Health Check Fails
1. Verify health endpoint: `curl http://<service-ip>/health`
2. Check application logs for errors
3. Verify environment variables
4. Check storage mount permissions

#### Service Not Accessible
1. Check service status: `kubectl get service a2a-registry-service`
2. Verify ingress configuration: `kubectl get ingress a2a-registry-ingress`
3. Check DNS resolution
4. Verify SSL certificate status

### Debugging Commands

```bash
# Get cluster info
kubectl cluster-info

# List all resources
kubectl get all -l app=a2a-registry

# Check events
kubectl get events --sort-by='.lastTimestamp'

# Port forward for local debugging
kubectl port-forward service/a2a-registry-service 8000:80

# Check resource usage
kubectl top pods -l app=a2a-registry
```

## Security Considerations

### Container Security
- Non-root user in container
- Minimal base image (Python slim)
- Regular security updates
- Resource limits enforced

### Network Security
- Cluster IP service type
- Ingress with managed SSL certificates
- Network policies (if configured)

### Access Control
- Service account with minimal permissions
- RBAC for Kubernetes resources
- Secrets management via GitHub Actions

## Performance Optimization

### Resource Tuning
- Monitor actual usage vs. requests
- Adjust limits based on metrics
- Consider horizontal pod autoscaling

### Caching
- Implement application-level caching
- Use CDN for static assets
- Consider Redis for session storage

### Database Optimization
- Monitor query performance
- Implement connection pooling
- Consider read replicas for scaling

## Backup and Recovery

### Data Backup
- Persistent volume snapshots
- Application-level backups
- Configuration backups

### Disaster Recovery
- Multi-region deployment option
- Automated rollback procedures
- Documentation of recovery steps

## Maintenance

### Regular Tasks
- Monitor resource usage
- Review security updates
- Update dependencies
- Clean up old images

### Scaling
- Horizontal pod autoscaling
- Vertical pod autoscaling
- Cluster node scaling

## Support

For deployment issues:
1. Check this documentation
2. Review GitHub Actions logs
3. Check Kubernetes events
4. Contact the development team

## Changelog

### v1.0.0
- Initial deployment configuration
- Multi-environment support
- Monitoring and alerting
- Rollback capabilities 