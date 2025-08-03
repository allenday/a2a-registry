# DNS Configuration Guide

This guide explains how to set up DNS for the A2A Registry with separate domains for documentation and API.

## Domain Structure

```
a2a-registry.dev          → GitHub Pages (documentation)
api.a2a-registry.dev      → Kubernetes cluster (API endpoints)
registry.a2a-registry.dev → Kubernetes cluster (main application)
```

## Step 1: Register Domain

1. Register `a2a-registry.dev` through your preferred domain registrar
2. Ensure you have access to manage DNS records

## Step 2: GitHub Pages Setup

### Configure GitHub Pages for Documentation

1. Go to your repository settings
2. Navigate to **Pages** section
3. Set source to **GitHub Actions** (recommended) or **Deploy from a branch**
4. Add custom domain: `a2a-registry.dev`
5. Check **Enforce HTTPS**

### DNS Records for GitHub Pages

Add these records to your domain registrar's DNS:

```
Type: A
Name: @ (or a2a-registry.dev)
Value: 185.199.108.153
TTL: 3600

Type: A
Name: @ (or a2a-registry.dev)
Value: 185.199.109.153
TTL: 3600

Type: A
Name: @ (or a2a-registry.dev)
Value: 185.199.110.153
TTL: 3600

Type: A
Name: @ (or a2a-registry.dev)
Value: 185.199.111.153
TTL: 3600

Type: CNAME
Name: www
Value: a2a-registry.dev
TTL: 3600
```

## Step 3: Deploy Infrastructure

### Get Static IP from Terraform

```bash
cd deploy/terraform
terraform init
terraform apply

# Note the static IP from outputs
terraform output static_ip
```

### DNS Records for Kubernetes Cluster

Add these records pointing to the static IP from Terraform:

```
Type: A
Name: api
Value: [STATIC_IP_FROM_TERRAFORM]
TTL: 3600

Type: A
Name: registry
Value: [STATIC_IP_FROM_TERRAFORM]
TTL: 3600
```

## Step 4: Verify Setup

### Test Documentation
```bash
curl -I https://a2a-registry.dev
# Should return 200 OK from GitHub Pages
```

### Test API
```bash
curl -I https://api.a2a-registry.dev/health
# Should return 200 OK from Kubernetes cluster

curl -I https://registry.a2a-registry.dev/health
# Should return 200 OK from Kubernetes cluster
```

## Alternative: Cloud DNS (GCP)

If using Google Cloud DNS:

1. Create a managed zone for `a2a-registry.dev`
2. Update your domain's nameservers to point to Google Cloud DNS
3. Add the records through the GCP Console or Terraform

### Terraform Cloud DNS Configuration

```hcl
# Add to deploy/terraform/main.tf
resource "google_dns_managed_zone" "a2a_registry" {
  name        = "a2a-registry-zone"
  dns_name    = "a2a-registry.dev."
  description = "DNS zone for A2A Registry"
}

resource "google_dns_record_set" "api" {
  name         = "api.a2a-registry.dev."
  managed_zone = google_dns_managed_zone.a2a_registry.name
  type         = "A"
  ttl          = 300
  rrdatas      = [google_compute_global_address.a2a_registry.address]
}

resource "google_dns_record_set" "registry" {
  name         = "registry.a2a-registry.dev."
  managed_zone = google_dns_managed_zone.a2a_registry.name
  type         = "A"
  ttl          = 300
  rrdatas      = [google_compute_global_address.a2a_registry.address]
}
```

## SSL Certificate Management

### GitHub Pages
- Automatically managed by GitHub
- Enforce HTTPS in repository settings

### Kubernetes Cluster
- Managed by Google Cloud Load Balancer
- Automatically provisions certificates for configured domains
- Certificates are automatically renewed

## Troubleshooting

### Common Issues

1. **DNS Propagation**: Changes can take up to 48 hours to propagate globally
2. **SSL Certificate Issues**: Ensure DNS is properly configured before certificates are provisioned
3. **CNAME Conflicts**: Don't use CNAME for root domain (@) - use A records instead

### Verification Commands

```bash
# Check DNS resolution
nslookup a2a-registry.dev
nslookup api.a2a-registry.dev
nslookup registry.a2a-registry.dev

# Check SSL certificates
openssl s_client -connect a2a-registry.dev:443 -servername a2a-registry.dev
openssl s_client -connect api.a2a-registry.dev:443 -servername api.a2a-registry.dev
```

## Security Considerations

1. **HTTPS Only**: All domains should enforce HTTPS
2. **Security Headers**: Configure appropriate security headers in your application
3. **CORS**: Configure CORS policies if needed for API access
4. **Rate Limiting**: Consider implementing rate limiting for API endpoints

## Monitoring

- Set up monitoring for all domains
- Monitor SSL certificate expiration
- Track DNS resolution and response times
- Set up alerts for downtime 