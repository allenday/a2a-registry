# Storage Configuration

The A2A Registry supports multiple storage backends for agent data persistence.

## Storage Backends

### 1. In-Memory Storage (Default)

**Configuration:**
```bash
STORAGE_TYPE=memory
```

**Characteristics:**
- ✅ Fastest performance
- ❌ Data lost on restart
- ❌ No persistence between deployments
- ✅ No additional infrastructure required

**Use Cases:**
- Development and testing
- Temporary registries
- When persistence is not required

### 2. File-Based Storage

**Configuration:**
```bash
STORAGE_TYPE=file
STORAGE_DATA_DIR=/data
```

**Characteristics:**
- ✅ Persistent across restarts
- ✅ Simple to set up
- ✅ No external dependencies
- ⚠️ Single-node only (no clustering)
- ⚠️ Limited scalability

**Use Cases:**
- Single-node deployments
- Development environments
- Small-scale production deployments

### 3. S3 Storage

**Configuration:**
```bash
STORAGE_TYPE=s3
S3_BUCKET_NAME=my-registry-bucket
S3_PREFIX=a2a-registry/
AWS_REGION=us-east-1
```

**Characteristics:**
- ✅ Highly scalable and durable
- ✅ Multi-region support
- ✅ Built-in backup and versioning
- ✅ Supports clustering
- ⚠️ Requires AWS credentials
- ⚠️ Network latency considerations

**Use Cases:**
- Production deployments
- Multi-region setups
- High availability requirements
- Large-scale agent registries

**AWS Credentials:**
S3 storage uses standard AWS credential chain:
1. Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
2. IAM roles (recommended for EC2/EKS)
3. AWS credentials file (`~/.aws/credentials`)
4. Instance metadata service

**Required IAM Permissions:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::my-registry-bucket",
        "arn:aws:s3:::my-registry-bucket/*"
      ]
    }
  ]
}
```

## Kubernetes Deployment

### File Storage Deployment

The Kubernetes deployment can be configured to use file-based storage with a PersistentVolumeClaim:

```yaml
env:
- name: STORAGE_TYPE
  value: "file"
- name: STORAGE_DATA_DIR
  value: "/data"
volumeMounts:
- name: registry-data
  mountPath: /data
volumes:
- name: registry-data
  persistentVolumeClaim:
    claimName: registry-data-pvc
```

### S3 Storage Deployment

For production deployments, S3 storage is recommended:

```yaml
env:
- name: STORAGE_TYPE
  value: "s3"
- name: S3_BUCKET_NAME
  value: "my-registry-bucket"
- name: S3_PREFIX
  value: "a2a-registry/"
- name: AWS_REGION
  value: "us-east-1"
# AWS credentials via IAM roles (recommended)
serviceAccountName: a2a-registry-sa
```

**Service Account with IAM Role (EKS):**
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: a2a-registry-sa
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT:role/A2ARegistryRole
```

### PersistentVolumeClaim

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: registry-data-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

## Future Storage Backends

### 4. Database Storage (Planned)

**Potential Options:**
- **PostgreSQL**: Full ACID compliance, complex queries
- **SQLite**: Lightweight, embedded
- **Redis**: High performance, in-memory with persistence
- **Cloud Firestore**: Serverless, auto-scaling

**Configuration:**
```bash
STORAGE_TYPE=database
DATABASE_URL=postgresql://user:pass@host:port/db
```

### 5. Additional Cloud Storage (Planned)

**Potential Options:**
- **Google Cloud Storage**: JSON files in buckets
- **Azure Blob Storage**: JSON files in containers

**Configuration:**
```bash
STORAGE_TYPE=gcs
GCS_BUCKET_NAME=my-registry-bucket
```

## Migration Between Backends

### From In-Memory to File

1. **Export current data:**
```python
# Get all agents
agents = await storage.list_agents()

# Save to JSON file
import json
with open('agents_backup.json', 'w') as f:
    json.dump(agents, f, indent=2)
```

2. **Switch to file storage:**
```bash
STORAGE_TYPE=file
STORAGE_DATA_DIR=/data
```

3. **Import data (if needed):**
```python
# Load from JSON file
with open('agents_backup.json', 'r') as f:
    agents = json.load(f)

# Register each agent
for agent in agents:
    await storage.register_agent(agent)
```

### From File to S3

1. **Export current data:**
```python
# Get all agents and extensions
agents = await storage.list_agents()
extensions, _, _ = await storage.list_extensions()

# Save to backup files
import json
with open('agents_backup.json', 'w') as f:
    json.dump([dict(agent) for agent in agents], f, indent=2)

with open('extensions_backup.json', 'w') as f:
    json.dump([ext.to_dict() for ext in extensions], f, indent=2)
```

2. **Switch to S3 storage:**
```bash
STORAGE_TYPE=s3
S3_BUCKET_NAME=my-registry-bucket
S3_PREFIX=a2a-registry/
AWS_REGION=us-east-1
```

3. **Import data:**
```python
# Load and register agents
with open('agents_backup.json', 'r') as f:
    agents = json.load(f)

for agent in agents:
    await storage.register_agent(agent)

# Load and register extensions
with open('extensions_backup.json', 'r') as f:
    extensions_data = json.load(f)

from a2a_registry.storage import ExtensionInfo
for ext_data in extensions_data:
    ext_info = ExtensionInfo.from_dict(ext_data)
    await storage.store_extension(ext_info)
```

## Performance Considerations

### In-Memory Storage
- **Read/Write**: ~1-10 microseconds
- **Memory Usage**: ~1KB per agent
- **Scalability**: Limited by available RAM

### File Storage
- **Read/Write**: ~1-10 milliseconds
- **Disk Usage**: ~1KB per agent
- **Scalability**: Limited by disk I/O

### S3 Storage
- **Read/Write**: ~50-200 milliseconds
- **Storage**: ~1KB per agent + S3 metadata
- **Scalability**: Virtually unlimited
- **Throughput**: Up to 3,500 PUT/COPY/POST/DELETE and 5,500 GET/HEAD requests per second per prefix

### Database Storage (Future)
- **Read/Write**: ~1-100 milliseconds
- **Storage**: ~1KB per agent + indexes
- **Scalability**: High (depends on database)

## Backup and Recovery

### File Storage Backup

```bash
# Backup agents data
kubectl exec -it deployment/a2a-registry -- cat /data/agents.json > backup.json

# Restore agents data
kubectl cp backup.json deployment/a2a-registry:/data/agents.json
```

### S3 Storage Backup

S3 provides built-in durability and versioning:

```bash
# Enable versioning on S3 bucket
aws s3api put-bucket-versioning \
  --bucket my-registry-bucket \
  --versioning-configuration Status=Enabled

# Create cross-region replication for disaster recovery
aws s3api put-bucket-replication \
  --bucket my-registry-bucket \
  --replication-configuration file://replication-config.json

# Manual backup to another bucket
aws s3 sync s3://my-registry-bucket/a2a-registry/ s3://my-backup-bucket/a2a-registry/
```

**S3 Lifecycle Policy for Cost Optimization:**
```json
{
  "Rules": [
    {
      "ID": "A2ARegistryLifecycle",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "STANDARD_IA"
        },
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        }
      ]
    }
  ]
}
```

### Automated Backup (Future)

```yaml
# CronJob for automated backups
apiVersion: batch/v1
kind: CronJob
metadata:
  name: registry-backup
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: busybox
            command:
            - /bin/sh
            - -c
            - |
              kubectl exec deployment/a2a-registry -- cat /data/agents.json > /backup/agents-$(date +%Y%m%d).json
          volumes:
          - name: backup-volume
            persistentVolumeClaim:
              claimName: backup-pvc
```

## Monitoring and Metrics

### Storage Metrics

```python
# Example metrics to collect
async def get_storage_metrics():
    agents = await storage.list_agents()
    extensions, _, total_extensions = await storage.list_extensions()
    
    metrics = {
        "total_agents": len(agents),
        "total_extensions": total_extensions,
        "storage_type": os.getenv("STORAGE_TYPE", "memory"),
    }
    
    # Storage-specific metrics
    if metrics["storage_type"] == "file":
        metrics["storage_size_bytes"] = os.path.getsize("/data/agents.json")
    elif metrics["storage_type"] == "s3":
        metrics["s3_bucket"] = os.getenv("S3_BUCKET_NAME")
        metrics["s3_prefix"] = os.getenv("S3_PREFIX", "a2a-registry/")
    
    return metrics
```

### S3 CloudWatch Metrics

Monitor S3 storage performance:

```bash
# Enable S3 request metrics
aws s3api put-bucket-metrics-configuration \
  --bucket my-registry-bucket \
  --id A2ARegistryMetrics \
  --metrics-configuration Id=A2ARegistryMetrics,Status=Enabled

# CloudWatch alarms for S3 errors
aws cloudwatch put-metric-alarm \
  --alarm-name "A2A-Registry-S3-Errors" \
  --alarm-description "S3 4xx errors for A2A Registry" \
  --metric-name 4xxErrors \
  --namespace AWS/S3 \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold
```

## Security Considerations

### File Storage Security

1. **File Permissions:**
```bash
# Secure the data directory
chmod 600 /data/agents.json
chown 1000:1000 /data/agents.json
```

2. **Encryption at Rest:**
```yaml
# Use encrypted persistent volumes
spec:
  storageClassName: encrypted-storage
```

3. **Access Control:**
```yaml
# Use security contexts
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000
```

### S3 Storage Security

1. **Bucket Encryption:**
```bash
# Enable default encryption
aws s3api put-bucket-encryption \
  --bucket my-registry-bucket \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'
```

2. **Bucket Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyInsecureConnections",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::my-registry-bucket",
        "arn:aws:s3:::my-registry-bucket/*"
      ],
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "false"
        }
      }
    }
  ]
}
```

3. **Access Logging:**
```bash
# Enable access logging
aws s3api put-bucket-logging \
  --bucket my-registry-bucket \
  --bucket-logging-status '{
    "LoggingEnabled": {
      "TargetBucket": "my-access-logs-bucket",
      "TargetPrefix": "a2a-registry-access-logs/"
    }
  }'
```

4. **VPC Endpoint (Optional):**
```bash
# Create VPC endpoint for private S3 access
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-12345678 \
  --service-name com.amazonaws.us-east-1.s3 \
  --vpc-endpoint-type Gateway \
  --route-table-ids rtb-12345678
```

## Troubleshooting

### Common Issues

#### File Storage Issues

1. **Permission Denied:**
```bash
# Fix file permissions
kubectl exec -it deployment/a2a-registry -- chown -R 1000:1000 /data
```

2. **Storage Full:**
```bash
# Check storage usage
kubectl exec -it deployment/a2a-registry -- df -h /data
```

3. **Data Corruption:**
```bash
# Validate JSON file
kubectl exec -it deployment/a2a-registry -- python -m json.tool /data/agents.json
```

#### S3 Storage Issues

1. **Access Denied:**
```bash
# Check IAM permissions
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::ACCOUNT:role/A2ARegistryRole \
  --action-names s3:GetObject s3:PutObject s3:ListBucket \
  --resource-arns arn:aws:s3:::my-registry-bucket/*

# Test S3 access
aws s3 ls s3://my-registry-bucket/a2a-registry/ --profile your-profile
```

2. **Network Connectivity:**
```bash
# Test S3 endpoint connectivity
kubectl exec -it deployment/a2a-registry -- curl -I https://s3.amazonaws.com

# Check VPC endpoint (if used)
kubectl exec -it deployment/a2a-registry -- nslookup s3.amazonaws.com
```

3. **Bucket Not Found:**
```bash
# Verify bucket exists and region
aws s3api head-bucket --bucket my-registry-bucket --region us-east-1

# Check bucket region
aws s3api get-bucket-location --bucket my-registry-bucket
```

4. **High Latency:**
```bash
# Check S3 request metrics in CloudWatch
aws cloudwatch get-metric-statistics \
  --namespace AWS/S3 \
  --metric-name FirstByteLatency \
  --dimensions Name=BucketName,Value=my-registry-bucket \
  --start-time 2023-01-01T00:00:00Z \
  --end-time 2023-01-02T00:00:00Z \
  --period 3600 \
  --statistics Average
```

### Logs

```bash
# Check storage-related logs
kubectl logs deployment/a2a-registry | grep -i storage

# Check S3-specific logs
kubectl logs deployment/a2a-registry | grep -i "s3\|boto"

# Enable debug logging for boto3
kubectl set env deployment/a2a-registry BOTO_DEBUG=1
``` 