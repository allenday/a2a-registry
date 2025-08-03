# Cloudflare Setup Guide

This guide explains how to configure Cloudflare for the A2A Registry with optimal performance and security.

## Architecture Overview

```
a2a-registry.dev          → GitHub Pages (direct, no Cloudflare)
api.a2a-registry.dev      → Cloudflare → GCP Load Balancer → Kubernetes
registry.a2a-registry.dev → Cloudflare → GCP Load Balancer → Kubernetes
```

## Step 1: Add Domain to Cloudflare

1. Sign up/login to Cloudflare
2. Click "Add a Site"
3. Enter `a2a-registry.dev`
4. Choose the Free plan (sufficient for most use cases)
5. Cloudflare will scan existing DNS records

## Step 2: Update Nameservers

1. Go to your domain registrar (where you bought a2a-registry.dev)
2. Update nameservers to Cloudflare's nameservers:
   ```
   Nameserver 1: [Cloudflare will provide]
   Nameserver 2: [Cloudflare will provide]
   ```
3. Wait for DNS propagation (can take up to 48 hours)

## Step 3: Configure DNS Records

In Cloudflare DNS settings, configure these records:

### GitHub Pages (Documentation)
```
Type: A
Name: @
Value: 185.199.108.153
Proxy: ❌ (DNS only)
TTL: Auto

Type: A
Name: @
Value: 185.199.109.153
Proxy: ❌ (DNS only)
TTL: Auto

Type: A
Name: @
Value: 185.199.110.153
Proxy: ❌ (DNS only)
TTL: Auto

Type: A
Name: @
Value: 185.199.111.153
Proxy: ❌ (DNS only)
TTL: Auto

Type: CNAME
Name: www
Value: a2a-registry.dev
Proxy: ❌ (DNS only)
TTL: Auto
```

### API and Registry (Kubernetes)
```
Type: A
Name: api
Value: [GCP_STATIC_IP_FROM_TERRAFORM]
Proxy: ✅ (Proxied)
TTL: Auto

Type: A
Name: registry
Value: [GCP_STATIC_IP_FROM_TERRAFORM]
Proxy: ✅ (Proxied)
TTL: Auto
```

## Step 4: SSL/TLS Configuration

1. Go to **SSL/TLS** settings in Cloudflare
2. Set **Encryption mode** to "Full (strict)"
3. Enable **Always Use HTTPS**
4. Enable **Minimum TLS Version** to 1.2

## Step 5: Security Settings

### Web Application Firewall (WAF)
1. Go to **Security** → **WAF**
2. Enable **Managed Rules** (Cloudflare Managed)
3. Consider enabling **Bot Fight Mode** for API endpoints

### Rate Limiting
1. Go to **Security** → **Rate Limiting**
2. Create rules for API endpoints:
   ```
   Rule: Rate limit API requests
   When incoming requests match: Hostname equals api.a2a-registry.dev
   Rate: 100 requests per 10 minutes
   Action: Block
   ```

### Security Headers
1. Go to **Security** → **Transform Rules** → **HTTP Response Headers**
2. Add security headers:
   ```
   Name: X-Frame-Options
   Value: DENY

   Name: X-Content-Type-Options
   Value: nosniff

   Name: Referrer-Policy
   Value: strict-origin-when-cross-origin

   Name: Permissions-Policy
   Value: camera=(), microphone=(), geolocation=()
   ```

## Step 6: Performance Optimization

### Caching Rules
1. Go to **Caching** → **Configuration**
2. Set **Browser Cache TTL** to 4 hours
3. Create custom cache rules:
   ```
   Rule: Cache API responses
   When incoming requests match: Hostname equals api.a2a-registry.dev AND Path contains /health
   Cache Level: Cache Everything
   Edge Cache TTL: 1 minute
   ```

### Page Rules (Optional)
Create page rules for specific optimizations:
```
URL: api.a2a-registry.dev/*
Settings:
- Cache Level: Cache Everything
- Edge Cache TTL: 2 minutes
- Browser Cache TTL: 1 hour
```

## Step 7: Deploy Infrastructure

```bash
cd deploy/terraform
terraform init
terraform apply -var="enable_direct_ssl=false" -var="use_cloudflare=true"
```

## Step 8: Verify Setup

### Test Documentation
```bash
curl -I https://a2a-registry.dev
# Should return 200 OK from GitHub Pages
```

### Test API (through Cloudflare)
```bash
curl -I https://api.a2a-registry.dev/health
# Should return 200 OK with Cloudflare headers

curl -I https://registry.a2a-registry.dev/health
# Should return 200 OK with Cloudflare headers
```

### Check Cloudflare Headers
```bash
curl -I https://api.a2a-registry.dev/health | grep -i cloudflare
# Should show Cloudflare headers like CF-RAY, Server: cloudflare
```

## Advanced Configuration

### Workers (Optional)
For advanced functionality, consider Cloudflare Workers:

```javascript
// Example: Add custom headers or modify responses
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  const response = await fetch(request)
  const newResponse = new Response(response.body, response)
  newResponse.headers.set('X-Custom-Header', 'A2A-Registry')
  return newResponse
}
```

### Analytics
1. Enable **Web Analytics** in Cloudflare
2. Monitor traffic patterns and performance
3. Set up alerts for unusual activity

## Troubleshooting

### Common Issues

1. **SSL Errors**: Ensure "Full (strict)" mode is enabled
2. **Caching Issues**: Check cache rules and purge if needed
3. **DNS Propagation**: Use `dig` or `nslookup` to verify
4. **Rate Limiting**: Check if legitimate traffic is being blocked

### Useful Commands

```bash
# Check DNS resolution
dig api.a2a-registry.dev
dig registry.a2a-registry.dev

# Check SSL certificate
openssl s_client -connect api.a2a-registry.dev:443 -servername api.a2a-registry.dev

# Test Cloudflare proxy
curl -I https://api.a2a-registry.dev/health
```

## Cost Considerations

### Free Plan Includes:
- Unlimited bandwidth
- DDoS protection
- Global CDN
- SSL certificates
- Basic WAF
- Rate limiting

### Pro Plan ($20/month) Adds:
- Advanced WAF
- Bot management
- Image optimization
- Priority support

## Security Best Practices

1. **Enable HSTS**: Force HTTPS connections
2. **Use WAF**: Block malicious requests
3. **Rate Limiting**: Prevent abuse
4. **Security Headers**: Protect against common attacks
5. **Regular Monitoring**: Check analytics and logs

## Performance Monitoring

1. **Analytics**: Monitor traffic and performance
2. **Real User Monitoring**: Track actual user experience
3. **Alerts**: Set up notifications for issues
4. **Logs**: Review request logs for anomalies 