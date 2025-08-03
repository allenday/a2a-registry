# A2A Registry API Reference

## Overview

The A2A Registry provides a multi-protocol API for agent registration, discovery, and management. This reference covers the primary interaction methods across JSON-RPC 2.0, REST, and GraphQL protocols.

## Authentication & Security

### Trust Levels
- **Development Mode**: Open access, for local development
- **Production Mode**: Strict authentication and authorization
  - JWT-based authentication
  - Role-based access control (RBAC)
  - Configurable trust levels for agent registration

### Authentication Methods
1. **JWT Token**
2. **API Key**
3. **OAuth 2.0**

## Core API Methods

### Agent Registration

#### JSON-RPC 2.0
```json
{
  "jsonrpc": "2.0",
  "method": "register_agent",
  "params": {
    "agent_card": {
      "name": "example-agent",
      "description": "Agent description",
      "version": "1.0.0",
      "protocol_version": "0.3.0",
      "preferred_transport": "JSONRPC",
      "skills": [
        {
          "id": "skill_id",
          "description": "Skill description"
        }
      ]
    }
  },
  "id": 1
}
```

#### REST Endpoint
```
POST /api/v1/agents
Content-Type: application/json

{
  "name": "example-agent",
  ...
}
```

#### GraphQL Mutation
```graphql
mutation {
  registerAgent(
    agentCard: {
      name: "example-agent"
      # ... other fields
    }
  ) {
    id
    name
    registrationTimestamp
  }
}
```

### Agent Discovery

#### Search Methods
- By skill
- By name/description
- By trust level
- By protocol version

#### JSON-RPC 2.0 Search
```json
{
  "jsonrpc": "2.0",
  "method": "search_agents",
  "params": {
    "skills": ["weather_forecast"],
    "protocol_version": "0.3.0"
  },
  "id": 2
}
```

#### GraphQL Query
```graphql
query {
  searchAgents(
    skills: ["weather_forecast"]
    protocolVersion: "0.3.0"
  ) {
    agents {
      name
      skills {
        id
        description
      }
    }
  }
}
```

## Auto-Generated Module Documentation

### Server Module
::: a2a_registry.server

### Storage Module  
::: a2a_registry.storage

### CLI Module
::: a2a_registry.cli

## Extension System

### URI Allowlist
- Configurable whitelist for agent extension URIs
- Trust level assignment for extensions
- Granular access control

### Extension Registration
```python
# Example extension registration
extension = {
    "uri": "https://example.com/agent-extension",
    "trust_level": "high",
    "allowed_skills": ["weather", "forecast"]
}
registry.register_extension(extension)
```

## Error Handling

### Common Error Codes
- `AGENT_REGISTRATION_FAILED` (1001)
- `AGENT_NOT_FOUND` (1002)
- `UNAUTHORIZED_ACCESS` (1003)
- `INVALID_PROTOCOL_VERSION` (1004)

### Error Response Example
```json
{
  "error": {
    "code": 1001,
    "message": "Agent registration failed",
    "details": {
      "reason": "Invalid agent card format"
    }
  }
}
```

## Performance & Rate Limiting

- Default rate limit: 100 requests/minute
- Configurable per API key
- Supports exponential backoff

## Monitoring & Health Checks

### Agent Health Endpoints
- `/health`: Overall system health
- `/agents/health`: Aggregate agent health
- `/metrics`: Prometheus-compatible metrics

## Configuration Options

```python
# Example configuration
registry_config = {
    "host": "0.0.0.0",
    "port": 8000,
    "log_level": "INFO",
    "auth_mode": "production",
    "trust_levels": {
        "development": {"max_agents": 10},
        "production": {"max_agents": 1000}
    }
}
```

## Compatibility

- **A2A Protocol**: v0.3.0
- **Python**: 3.9+
- **Supported Transports**: 
  - JSON-RPC 2.0 (Primary)
  - REST
  - GraphQL
  - gRPC (Experimental)

## Best Practices

1. Use JWT for authentication in production
2. Implement agent health checks
3. Validate agent cards before registration
4. Use GraphQL for complex querying
5. Implement proper error handling

## SDK & Client Libraries

- Official Python SDK
- Community-supported libraries for other languages

## Troubleshooting

### Common Issues
- Incorrect agent card format
- Authentication failures
- Protocol version mismatches

Refer to our [Troubleshooting Guide](/docs/documentation/troubleshooting/common-issues.md) for detailed resolution steps.