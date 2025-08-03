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

## Kubernetes Deployment

The Kubernetes deployment is configured to use file-based storage with a PersistentVolumeClaim:

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

### 3. Database Storage (Planned)

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

### 4. Cloud Storage (Planned)

**Potential Options:**
- **Google Cloud Storage**: JSON files in buckets
- **AWS S3**: JSON files in buckets
- **Azure Blob Storage**: JSON files in containers

**Configuration:**
```bash
STORAGE_TYPE=cloud
CLOUD_STORAGE_BUCKET=my-registry-bucket
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

## Performance Considerations

### In-Memory Storage
- **Read/Write**: ~1-10 microseconds
- **Memory Usage**: ~1KB per agent
- **Scalability**: Limited by available RAM

### File Storage
- **Read/Write**: ~1-10 milliseconds
- **Disk Usage**: ~1KB per agent
- **Scalability**: Limited by disk I/O

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

### Storage Metrics (Future)

```python
# Example metrics to collect
storage_metrics = {
    "total_agents": len(await storage.list_agents()),
    "storage_size_bytes": os.path.getsize("/data/agents.json"),
    "storage_type": os.getenv("STORAGE_TYPE", "memory"),
    "last_backup": get_last_backup_time(),
}
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

## Troubleshooting

### Common Issues

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

### Logs

```bash
# Check storage-related logs
kubectl logs deployment/a2a-registry | grep -i storage
``` 