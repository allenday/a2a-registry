# API Overview

The A2A Registry provides APIs for agent registration and discovery, supporting multiple transport protocols as defined in the [A2A Protocol Specification](https://a2a-protocol.org). This implementation follows **A2A Protocol v0.3.0**.

## Supported Protocols

The A2A Registry implements multiple transport protocols to ensure maximum compatibility:

### 1. REST/HTTP+JSON
- **Endpoint**: `http://localhost:8000` (default)
- **Content-Type**: `application/json`
- **Use Case**: Web integrations, simple HTTP clients, testing

### 2. gRPC
- **Endpoint**: `localhost:50051` (default gRPC port)
- **Protocol**: Protocol Buffers over HTTP/2
- **Use Case**: High-performance applications, typed clients, streaming

### 3. JSON-RPC 2.0 (Planned)
- **Endpoint**: `http://localhost:8000/rpc`
- **Content-Type**: `application/json`
- **Use Case**: RPC-style integrations, batch operations

## Core Concepts

### Agent Card
An Agent Card is a JSON metadata document that describes an agent's:
- Identity (name, description, version)
- Capabilities and skills
- Service endpoints
- Authentication requirements

### Registry Metadata
Additional metadata maintained by the registry:
- Registration timestamps
- Health status and monitoring
- Discovery preferences
- Performance metrics

## Common Operations

### Registration Flow
1. **Register Agent**: Submit agent card to registry
2. **Health Check**: Registry periodically checks agent availability
3. **Discovery**: Other agents can find this agent through search
4. **Update**: Agent can update its card as needed
5. **Unregister**: Remove agent when going offline

### Discovery Flow
1. **Search**: Query registry with search criteria
2. **Filter**: Apply filters (region, capabilities, health)
3. **Select**: Choose appropriate agent for task
4. **Connect**: Use agent's endpoint to establish communication

## Authentication & Security

### Current Implementation
- No authentication required (development/testing)
- HTTP transport (can be upgraded to HTTPS)

### Production Considerations
- Implement API key authentication
- Use HTTPS/TLS for all communication
- Add rate limiting and request validation
- Consider mutual TLS for gRPC

## Error Handling

### HTTP Status Codes (REST)
- `200 OK`: Successful operation
- `201 Created`: Agent registered successfully
- `400 Bad Request`: Invalid request data
- `404 Not Found`: Agent not found
- `500 Internal Server Error`: Server error

### gRPC Status Codes
- `OK`: Successful operation
- `INVALID_ARGUMENT`: Invalid request parameters
- `NOT_FOUND`: Agent not found
- `ALREADY_EXISTS`: Agent already registered
- `INTERNAL`: Server error

## Rate Limits

Current implementation has no rate limiting. For production use, consider:
- Per-IP rate limiting
- Per-agent rate limiting
- Burst allowances for batch operations

## Next Steps

- [Endpoints](endpoints.md) - Detailed API reference
- [Examples](examples.md) - Code examples and tutorials
- [Configuration](../getting-started/configuration.md) - Server configuration options