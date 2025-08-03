# Quick Start

Get up and running with A2A Registry in just a few minutes.

## Start the Server

The simplest way to start the A2A Registry server:

```bash
a2a-registry serve
```

By default, the server will:
- Listen on `http://localhost:8000` (REST API)
- Support both REST/HTTP+JSON and gRPC transport protocols
- Use in-memory storage
- Enable debug logging

## Protocol Support

The A2A Registry supports multiple transport protocols as defined in the **A2A Protocol v0.3.0** specification:

- **REST/HTTP+JSON**: Traditional REST API endpoints for easy integration
- **gRPC**: High-performance binary protocol using Protocol Buffers
- **JSON-RPC 2.0**: (Coming soon) JSON-RPC over HTTP

## Basic Usage

### 1. Check Server Health

First, verify the server is running:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "A2A Registry"
}
```

### 2. Register an Agent

Register your first agent:

```bash
curl -X POST http://localhost:8000/agents \
  -H "Content-Type: application/json" \
  -d '{
    "agent_card": {
      "name": "weather-agent",
      "description": "An agent that provides weather information",
      "url": "http://localhost:3001",
      "version": "0.420.0",
      "protocol_version": "0.3.0",
      "skills": [
        {
          "id": "get_weather",
          "description": "Get current weather for a location"
        }
      ]
    }
  }'
```

Expected response:
```json
{
  "success": true,
  "agent_id": "weather-agent",
  "message": "Agent registered successfully"
}
```

### 3. List All Agents

See all registered agents:

```bash
curl http://localhost:8000/agents
```

Expected response:
```json
{
  "agents": [
    {
      "name": "weather-agent",
      "description": "An agent that provides weather information",
      "url": "http://localhost:3001",
      "version": "0.420.0",
      "protocol_version": "0.3.0",
      "skills": [
        {
          "id": "get_weather",
          "description": "Get current weather for a location"
        }
      ]
    }
  ],
  "count": 1
}
```

### 4. Get Specific Agent

Retrieve details for a specific agent:

```bash
curl http://localhost:8000/agents/weather-agent
```

### 5. Search Agents

Search for agents by name, description, or skills:

```bash
curl -X POST http://localhost:8000/agents/search \
  -H "Content-Type: application/json" \
  -d '{"query": "weather"}'
```

### 6. Unregister an Agent

Remove an agent from the registry:

```bash
curl -X DELETE http://localhost:8000/agents/weather-agent
```

## Command Line Options

The `a2a-registry serve` command supports several options:

```bash
# Custom host and port
a2a-registry serve --host 0.0.0.0 --port 8080

# Enable debug mode
a2a-registry serve --debug

# Custom log level
a2a-registry serve --log-level INFO
```

## What's Next?

- [Configuration Guide](configuration.md) - Customize server settings
- [API Reference](../api/overview.md) - Detailed API documentation
- [Examples](../examples/basic-usage.md) - More usage examples
- [Development Setup](../developer/setup.md) - Set up development environment