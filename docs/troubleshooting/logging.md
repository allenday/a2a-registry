# Logging and Monitoring

Comprehensive logging and monitoring setup for A2A Registry deployments.

## Logging Configuration

### Server Logging

A2A Registry uses Python's standard logging module with configurable levels:

```bash
# Start server with different log levels
a2a-registry serve --log-level DEBUG    # Detailed debug information
a2a-registry serve --log-level INFO     # Standard information (default)
a2a-registry serve --log-level WARNING  # Warnings and errors only
a2a-registry serve --log-level ERROR    # Errors only
```

### Structured Logging

Configure structured JSON logging for production:

```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'agent_id'):
            log_entry['agent_id'] = record.agent_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'duration'):
            log_entry['duration'] = record.duration
            
        return json.dumps(log_entry)

# Configure logging
def setup_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    
    logger = logging.getLogger("a2a_registry")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    
    return logger

logger = setup_logging()
```

### Application Logging

Add detailed logging to registry operations:

```python
import logging
import time
from functools import wraps

logger = logging.getLogger("a2a_registry.storage")

def log_operation(operation_name: str):
    """Decorator to log storage operations"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            agent_id = kwargs.get('agent_id', args[1] if len(args) > 1 else 'unknown')
            
            logger.info(f"Starting {operation_name}", extra={
                'operation': operation_name,
                'agent_id': agent_id
            })
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.info(f"Completed {operation_name}", extra={
                    'operation': operation_name,
                    'agent_id': agent_id,
                    'duration': duration,
                    'success': True
                })
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                logger.error(f"Failed {operation_name}: {str(e)}", extra={
                    'operation': operation_name,
                    'agent_id': agent_id,
                    'duration': duration,
                    'success': False,
                    'error': str(e)
                })
                
                raise
                
        return wrapper
    return decorator

class InMemoryStorage:
    @log_operation("register_agent")
    async def register_agent(self, agent_id: str, agent_card: dict):
        # Implementation with automatic logging
        pass
    
    @log_operation("get_agent")
    async def get_agent(self, agent_id: str):
        # Implementation with automatic logging
        pass
```

### Request Logging Middleware

Track all API requests:

```python
import uuid
from starlette.middleware.base import BaseHTTPMiddleware

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        start_time = time.time()
        
        logger.info("Request started", extra={
            'request_id': request_id,
            'method': request.method,
            'url': str(request.url),
            'client_ip': request.client.host,
            'user_agent': request.headers.get('user-agent', 'unknown')
        })
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            logger.info("Request completed", extra={
                'request_id': request_id,
                'method': request.method,
                'url': str(request.url),
                'status_code': response.status_code,
                'duration': duration
            })
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            logger.error("Request failed", extra={
                'request_id': request_id,
                'method': request.method,
                'url': str(request.url),
                'duration': duration,
                'error': str(e)
            })
            
            raise

# Add middleware to app
app.add_middleware(RequestLoggingMiddleware)
```

## Log Aggregation

### ELK Stack Integration

#### Logstash Configuration

```ruby
# logstash.conf
input {
  file {
    path => "/var/log/a2a-registry/*.log"
    start_position => "beginning"
    codec => "json"
  }
}

filter {
  if [logger] == "a2a_registry" {
    mutate {
      add_tag => ["a2a_registry"]
    }
  }
  
  # Parse duration as number
  if [duration] {
    mutate {
      convert => { "duration" => "float" }
    }
  }
  
  # Add timestamp parsing
  date {
    match => [ "timestamp", "ISO8601" ]
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "a2a-registry-%{+YYYY.MM.dd}"
  }
  
  stdout {
    codec => rubydebug
  }
}
```

#### Elasticsearch Index Template

```json
{
  "index_patterns": ["a2a-registry-*"],
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0
  },
  "mappings": {
    "properties": {
      "timestamp": {
        "type": "date"
      },
      "level": {
        "type": "keyword"
      },
      "operation": {
        "type": "keyword"
      },
      "agent_id": {
        "type": "keyword"
      },
      "duration": {
        "type": "float"
      },
      "status_code": {
        "type": "integer"
      },
      "method": {
        "type": "keyword"
      },
      "url": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword"
          }
        }
      }
    }
  }
}
```

#### Kibana Dashboards

Key visualizations to create:

1. **Request Rate**: Requests per minute over time
2. **Response Times**: Average and percentile response times
3. **Error Rates**: HTTP error status codes
4. **Agent Operations**: Registration, discovery, search operations
5. **Top Agents**: Most frequently accessed agents

### Fluentd Integration

```yaml
# fluent.conf
<source>
  @type tail
  path /var/log/a2a-registry/*.log
  pos_file /var/log/fluentd/a2a-registry.log.pos
  tag a2a.registry
  format json
</source>

<filter a2a.registry>
  @type record_transformer
  <record>
    service "a2a-registry"
    environment "#{ENV['ENVIRONMENT']}"
  </record>
</filter>

<match a2a.registry>
  @type elasticsearch
  host elasticsearch
  port 9200
  index_name a2a-registry
  type_name _doc
</match>
```

## Metrics and Monitoring

### Prometheus Integration

```python
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest
import time

# Define metrics
REQUEST_COUNT = Counter(
    'registry_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'registry_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_AGENTS = Gauge(
    'registry_active_agents',
    'Number of active agents'
)

AGENT_OPERATIONS = Counter(
    'registry_agent_operations_total',
    'Total agent operations',
    ['operation', 'status']
)

REGISTRY_INFO = Info(
    'registry_info',
    'Registry information'
)

# Set static info
REGISTRY_INFO.info({
    'version': '0.420.0',
    'python_version': platform.python_version(),
    'platform': platform.platform()
})

# Middleware to collect metrics
class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        method = request.method
        endpoint = request.url.path
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            status = str(response.status_code)
            
            # Record metrics
            REQUEST_COUNT.labels(method, endpoint, status).inc()
            REQUEST_DURATION.labels(method, endpoint).observe(duration)
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            REQUEST_COUNT.labels(method, endpoint, "500").inc()
            REQUEST_DURATION.labels(method, endpoint).observe(duration)
            raise

# Add metrics endpoint
@app.get("/metrics")
async def get_metrics():
    # Update active agents count
    agent_count = await storage.count_agents()
    ACTIVE_AGENTS.set(agent_count)
    
    return Response(generate_latest(), media_type="text/plain")

# Add middleware
app.add_middleware(MetricsMiddleware)
```

### Custom Metrics Collection

```python
class MetricsCollector:
    def __init__(self, storage):
        self.storage = storage
        self.start_time = time.time()
        
    async def collect_metrics(self):
        """Collect custom application metrics"""
        metrics = {
            'uptime': time.time() - self.start_time,
            'agent_count': await self.storage.count_agents(),
            'memory_usage': psutil.Process().memory_info().rss,
            'cpu_percent': psutil.Process().cpu_percent(),
        }
        
        # Collect agent statistics
        agents = await self.storage.list_agents()
        
        # Count by transport protocol
        transport_counts = {}
        for agent in agents:
            transport = agent.get('preferred_transport', 'unknown')
            transport_counts[transport] = transport_counts.get(transport, 0) + 1
        
        metrics['transports'] = transport_counts
        
        # Count by capabilities
        capability_counts = {
            'streaming': 0,
            'push_notifications': 0,
            'state_transition_history': 0
        }
        
        for agent in agents:
            capabilities = agent.get('capabilities', {})
            for cap, value in capabilities.items():
                if value and cap in capability_counts:
                    capability_counts[cap] += 1
        
        metrics['capabilities'] = capability_counts
        
        return metrics

# Periodic metrics collection
async def metrics_background_task():
    collector = MetricsCollector(storage)
    
    while True:
        try:
            metrics = await collector.collect_metrics()
            
            # Update Prometheus gauges
            ACTIVE_AGENTS.set(metrics['agent_count'])
            
            # Log metrics for external collection
            logger.info("Metrics collected", extra={
                'metrics': metrics,
                'metric_type': 'application'
            })
            
        except Exception as e:
            logger.error(f"Metrics collection failed: {e}")
        
        await asyncio.sleep(60)  # Collect every minute

# Start background task
@app.on_event("startup")
async def start_metrics_collection():
    asyncio.create_task(metrics_background_task())
```

## Health Checks

### Basic Health Check

```python
@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    try:
        # Test storage connectivity
        await storage.list_agents()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "0.420.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )
```

### Detailed Health Check

```python
@app.get("/health/detailed")
async def detailed_health_check():
    """Comprehensive health check with metrics"""
    checks = {}
    overall_status = "healthy"
    
    # Storage check
    try:
        start = time.time()
        await storage.list_agents()
        checks["storage"] = {
            "status": "healthy",
            "response_time": time.time() - start
        }
    except Exception as e:
        checks["storage"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_status = "unhealthy"
    
    # Memory check
    process = psutil.Process()
    memory_usage = process.memory_info().rss
    memory_percent = process.memory_percent()
    
    if memory_percent > 90:
        checks["memory"] = {
            "status": "warning",
            "usage": memory_usage,
            "percent": memory_percent
        }
        if overall_status == "healthy":
            overall_status = "warning"
    else:
        checks["memory"] = {
            "status": "healthy",
            "usage": memory_usage,
            "percent": memory_percent
        }
    
    # Disk space check (if using file logging)
    disk_usage = psutil.disk_usage('/')
    disk_percent = (disk_usage.used / disk_usage.total) * 100
    
    if disk_percent > 90:
        checks["disk"] = {
            "status": "warning",
            "percent": disk_percent
        }
        if overall_status == "healthy":
            overall_status = "warning"
    else:
        checks["disk"] = {
            "status": "healthy",
            "percent": disk_percent
        }
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks,
        "uptime": time.time() - start_time,
        "version": "0.420.0"
    }
```

### Kubernetes Health Checks

```yaml
# kubernetes deployment with health checks
apiVersion: apps/v1
kind: Deployment
metadata:
  name: a2a-registry
spec:
  template:
    spec:
      containers:
      - name: a2a-registry
        image: a2a-registry:v0.1.0
        ports:
        - containerPort: 8000
        
        # Liveness probe
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        # Readiness probe
        readinessProbe:
          httpGet:
            path: /health/detailed
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        
        # Startup probe
        startupProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 10
```

## Alerting

### Prometheus Alerting Rules

```yaml
# prometheus-alerts.yml
groups:
- name: a2a-registry
  rules:
  - alert: RegistryDown
    expr: up{job="a2a-registry"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "A2A Registry is down"
      description: "A2A Registry has been down for more than 1 minute"
  
  - alert: HighErrorRate
    expr: rate(registry_requests_total{status=~"5.."}[5m]) > 0.1
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High error rate in A2A Registry"
      description: "Error rate is {{ $value }} errors per second"
  
  - alert: HighResponseTime
    expr: histogram_quantile(0.95, rate(registry_request_duration_seconds_bucket[5m])) > 1.0
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High response time in A2A Registry"
      description: "95th percentile response time is {{ $value }} seconds"
  
  - alert: HighMemoryUsage
    expr: process_resident_memory_bytes{job="a2a-registry"} > 1000000000
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage in A2A Registry"
      description: "Memory usage is {{ $value | humanize }}B"
```

### Slack Alerting Integration

```python
import aiohttp
import json

class SlackAlerter:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    async def send_alert(self, level: str, message: str, details: dict = None):
        color_map = {
            "info": "#36a64f",
            "warning": "#ffcc00", 
            "error": "#ff0000",
            "critical": "#8B0000"
        }
        
        payload = {
            "attachments": [{
                "color": color_map.get(level, "#cccccc"),
                "title": f"A2A Registry Alert ({level.upper()})",
                "text": message,
                "timestamp": int(time.time())
            }]
        }
        
        if details:
            payload["attachments"][0]["fields"] = [
                {"title": key, "value": str(value), "short": True}
                for key, value in details.items()
            ]
        
        async with aiohttp.ClientSession() as session:
            await session.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'}
            )

# Usage in error handling
alerter = SlackAlerter(os.getenv("SLACK_WEBHOOK_URL"))

async def handle_critical_error(error: Exception, context: dict):
    await alerter.send_alert(
        level="critical",
        message=f"Critical error in A2A Registry: {str(error)}",
        details=context
    )
```

## Log Analysis

### Common Log Queries

#### Elasticsearch/Kibana Queries

```json
// High error rates
{
  "query": {
    "bool": {
      "must": [
        {"range": {"timestamp": {"gte": "now-1h"}}},
        {"term": {"level": "ERROR"}}
      ]
    }
  },
  "aggs": {
    "errors_over_time": {
      "date_histogram": {
        "field": "timestamp",
        "interval": "5m"
      }
    }
  }
}

// Slow requests
{
  "query": {
    "bool": {
      "must": [
        {"range": {"timestamp": {"gte": "now-1h"}}},
        {"range": {"duration": {"gte": 1.0}}}
      ]
    }
  },
  "sort": [{"duration": {"order": "desc"}}]
}

// Agent operation statistics
{
  "query": {
    "bool": {
      "must": [
        {"range": {"timestamp": {"gte": "now-24h"}}},
        {"exists": {"field": "operation"}}
      ]
    }
  },
  "aggs": {
    "operations": {
      "terms": {"field": "operation"},
      "aggs": {
        "avg_duration": {
          "avg": {"field": "duration"}
        }
      }
    }
  }
}
```

### Log Analysis Scripts

```python
import json
from collections import defaultdict
from datetime import datetime, timedelta

def analyze_logs(log_file_path: str):
    """Analyze A2A Registry logs for insights"""
    
    operations = defaultdict(list)
    errors = []
    slow_requests = []
    
    with open(log_file_path, 'r') as f:
        for line in f:
            try:
                log_entry = json.loads(line)
                
                # Collect operation statistics
                if 'operation' in log_entry:
                    operations[log_entry['operation']].append(log_entry)
                
                # Collect errors
                if log_entry.get('level') == 'ERROR':
                    errors.append(log_entry)
                
                # Collect slow requests
                if log_entry.get('duration', 0) > 1.0:
                    slow_requests.append(log_entry)
                    
            except json.JSONDecodeError:
                continue
    
    # Generate report
    print("=== A2A Registry Log Analysis ===\n")
    
    # Operation statistics
    print("Operation Statistics:")
    for op, entries in operations.items():
        durations = [e.get('duration', 0) for e in entries if 'duration' in e]
        if durations:
            avg_duration = sum(durations) / len(durations)
            print(f"  {op}: {len(entries)} operations, avg {avg_duration:.3f}s")
    
    print(f"\nErrors: {len(errors)}")
    print(f"Slow requests (>1s): {len(slow_requests)}")
    
    # Top errors
    if errors:
        error_types = defaultdict(int)
        for error in errors:
            error_msg = error.get('message', 'Unknown error')
            error_types[error_msg] += 1
        
        print("\nTop Errors:")
        for error, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {count}x: {error}")

if __name__ == "__main__":
    analyze_logs("/var/log/a2a-registry/app.log")
```

## Monitoring Dashboard

### Grafana Dashboard Configuration

```json
{
  "dashboard": {
    "title": "A2A Registry Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(registry_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(registry_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(registry_request_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          }
        ]
      },
      {
        "title": "Active Agents",
        "type": "singlestat",
        "targets": [
          {
            "expr": "registry_active_agents",
            "legendFormat": "Agents"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(registry_requests_total{status=~\"4..|5..\"}[5m])",
            "legendFormat": "{{status}}"
          }
        ]
      }
    ]
  }
}
```

## Best Practices

1. **Use structured logging** for easy parsing and analysis
2. **Include correlation IDs** to track requests across services
3. **Log at appropriate levels** to avoid noise
4. **Monitor key metrics** like response time, error rate, and throughput
5. **Set up alerting** for critical conditions
6. **Regular log rotation** to manage disk space
7. **Centralized logging** for distributed deployments
8. **Health checks** for all critical components

## Next Steps

- Set up [Performance Tuning](performance.md) for optimization
- Review [Common Issues](common-issues.md) for troubleshooting
- Check [Architecture Guide](../concepts/architecture.md) for system design