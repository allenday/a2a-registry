# Configuration

Learn how to customize the A2A Registry server configuration.

## Command Line Options

The A2A Registry server can be configured using command line arguments:

### Basic Options

```bash
a2a-registry serve [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--host` | `127.0.0.1` | Host address to bind the server |
| `--port` | `8000` | Port number to listen on |
| `--debug` | `False` | Enable debug mode |
| `--log-level` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

### Examples

#### Development Setup

For development, you might want to enable debug mode and bind to all interfaces:

```bash
a2a-registry serve --host 0.0.0.0 --port 8000 --debug --log-level DEBUG
```

#### Production Setup

For production, use more conservative settings:

```bash
a2a-registry serve --host 127.0.0.1 --port 8000 --log-level WARNING
```

## Environment Variables

You can also configure the server using environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `A2A_REGISTRY_HOST` | Server host address | `0.0.0.0` |
| `A2A_REGISTRY_PORT` | Server port | `8080` |
| `A2A_REGISTRY_LOG_LEVEL` | Logging level | `INFO` |
| `A2A_REGISTRY_DEBUG` | Debug mode | `true` |

Example:
```bash
export A2A_REGISTRY_HOST=0.0.0.0
export A2A_REGISTRY_PORT=8080
export A2A_REGISTRY_LOG_LEVEL=INFO
a2a-registry serve
```

## Storage Configuration

Currently, the A2A Registry uses in-memory storage by default. This means:

- All data is lost when the server restarts
- No persistent storage is required
- Fast performance for development and testing

### Future Storage Options

Future versions will support additional storage backends:

- **File-based storage** - JSON or SQLite files
- **Database storage** - PostgreSQL, MySQL, etc.
- **Redis storage** - For distributed setups

## Logging Configuration

### Log Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General information about server operation
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for serious problems

### Log Format

The server uses structured logging with the following information:

- Timestamp
- Log level
- Logger name
- Message
- Additional context (for requests, errors, etc.)

Example log output:
```
2025-01-15 10:30:00,123 - INFO - a2a_registry.server - Registered agent: weather-agent
2025-01-15 10:30:05,456 - INFO - uvicorn.access - 127.0.0.1:54321 - "GET /agents HTTP/1.1" 200
```

## Security Considerations

### Development vs Production

**Development:**
- Debug mode enabled
- Detailed error messages
- Verbose logging

**Production:**
- Debug mode disabled
- Generic error messages
- Minimal logging

### Network Security

- Bind to `127.0.0.1` for local-only access
- Bind to `0.0.0.0` only when needed for external access
- Consider using a reverse proxy (nginx, Apache) in production
- Implement proper firewall rules

## Performance Tuning

### Server Settings

For high-traffic scenarios, consider:

- Using a production ASGI server like `gunicorn` with `uvicorn` workers
- Implementing connection pooling
- Adding caching layers
- Using external storage backends

### Example Production Setup

```bash
# Using gunicorn with uvicorn workers
gunicorn a2a_registry.server:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers 4 \
  --bind 127.0.0.1:8000
```

## Monitoring and Health Checks

### Health Check Endpoint

The registry provides a health check endpoint at `/health`:

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "service": "A2A Registry"
}
```

### Metrics and Monitoring

For production deployments, consider adding:

- Application metrics (Prometheus, etc.)
- Request/response logging
- Error tracking (Sentry, etc.)
- Performance monitoring (APM tools)

## Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Use a different port
a2a-registry serve --port 8001
```

**Permission denied on port 80/443:**
```bash
# Use a higher port number (> 1024) or run with sudo
a2a-registry serve --port 8080
```

**Can't access from other machines:**
```bash
# Bind to all interfaces
a2a-registry serve --host 0.0.0.0
```

### Debug Mode

Enable debug mode for troubleshooting:

```bash
a2a-registry serve --debug --log-level DEBUG
```

This will provide detailed logging and better error messages.