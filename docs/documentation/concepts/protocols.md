# Protocol Support

A2A Registry supports multiple communication protocols to accommodate diverse agent architectures and requirements. The registry implements **A2A Protocol v0.3.0** as its core specification.

## Overview

The registry supports agent discovery across different transport protocols while maintaining protocol-agnostic discovery capabilities.

## Supported Protocols

### 1. HTTP/REST (Primary)

**Status**: ✅ Fully Supported

The registry itself is built on REST principles using FastAPI:

```http
POST /agents HTTP/1.1
Content-Type: application/json

{
  "agent_card": {
    "name": "rest-agent",
    "url": "http://example.com:8080",
    "preferred_transport": "http",
    "protocol_version": "0.3.0"
  }
}
```

#### Features:
- JSON request/response
- OpenAPI documentation
- HTTP status codes
- Standard REST verbs

#### Agent Card Example:

```json
{
  "name": "weather-api",
  "description": "RESTful weather service",
  "url": "https://api.weather.com",
  "preferred_transport": "http",
  "capabilities": {
    "streaming": false,
    "push_notifications": false,
    "state_transition_history": false
  }
}
```

### 2. gRPC

**Status**: ✅ Supported via Agent Cards

Agents using gRPC can register with the registry:

```json
{
  "name": "grpc-ml-service",
  "description": "High-performance ML inference service",
  "url": "grpc://ml-service:50051",
  "preferred_transport": "grpc",
  "protocol_version": "0.3.0"
}
```

#### Discovery Example:

```python
# Discover gRPC services
grpc_agents = await registry.search_agents(
    preferred_transport="grpc"
)

# Connect to discovered gRPC service
for agent in grpc_agents:
    if "ml-inference" in agent["skills"]:
        channel = grpc.aio.insecure_channel(agent["url"])
        stub = MLServiceStub(channel)
        break
```

### 3. JSON-RPC

**Status**: 🚧 Planned

Future support for JSON-RPC protocol:

```json
{
  "name": "jsonrpc-calculator",
  "description": "Mathematical calculation service",
  "url": "http://calc.example.com/rpc",
  "preferred_transport": "jsonrpc",
  "protocol_version": "2.0"
}
```

### 4. WebSocket

**Status**: 🚧 Planned

Future support for WebSocket-based agents:

```json
{
  "name": "realtime-chat",
  "description": "Real-time chat agent",
  "url": "ws://chat.example.com/ws",
  "preferred_transport": "websocket",
  "capabilities": {
    "streaming": true,
    "push_notifications": true
  }
}
```

## Protocol-Specific Features

### HTTP/REST Capabilities

#### Content Types
- `application/json` (primary)
- `application/xml` (future)
- `text/plain` (simple responses)

#### Authentication Methods
- Bearer tokens
- API keys
- Basic authentication
- OAuth 2.0 (future)

#### Example Agent Card:

```json
{
  "name": "authenticated-api",
  "url": "https://secure-api.com",
  "preferred_transport": "http",
  "metadata": {
    "auth_type": "bearer_token",
    "content_types": ["application/json"],
    "rate_limit": "1000/hour"
  }
}
```

### gRPC Capabilities

#### Service Definition
- Protocol Buffer schemas
- Streaming support
- Bidirectional communication

#### Example Registration:

```python
from a2a_registry import A2ARegistryClient

# Register gRPC service
agent_card = {
    "name": "grpc-data-processor",
    "description": "High-throughput data processing",
    "url": "grpc://processor.example.com:50051",
    "preferred_transport": "grpc",
    "skills": [
        {
            "id": "process_batch",
            "description": "Process large data batches",
            "streaming": True
        }
    ],
    "metadata": {
        "proto_file": "data_processor.proto",
        "max_message_size": "100MB"
    }
}

registry = A2ARegistryClient("http://localhost:8000")
await registry.register_agent(agent_card)
```

## Protocol Detection

### Automatic Protocol Detection

The registry can infer protocol from URL schemes:

```python
def detect_transport(url: str) -> str:
    if url.startswith("http://") or url.startswith("https://"):
        return "http"
    elif url.startswith("grpc://"):
        return "grpc"
    elif url.startswith("ws://") or url.startswith("wss://"):
        return "websocket"
    else:
        return "unknown"
```

### Protocol Validation

```python
def validate_agent_card(agent_card: AgentCard) -> bool:
    transport = agent_card.get("preferred_transport")
    url = agent_card.get("url")
    
    if transport == "grpc" and not url.startswith("grpc://"):
        raise ValueError("gRPC agents must use grpc:// URL scheme")
    
    if transport == "http" and not (url.startswith("http://") or url.startswith("https://")):
        raise ValueError("HTTP agents must use http:// or https:// URL scheme")
    
    return True
```

## Cross-Protocol Communication

### Protocol Bridges

Future support for protocol adaptation:

```python
# Future: Protocol bridge
class ProtocolBridge:
    async def adapt_request(self, from_protocol: str, to_protocol: str, request):
        """Convert request between protocols"""
        if from_protocol == "http" and to_protocol == "grpc":
            return await self.http_to_grpc(request)
        elif from_protocol == "grpc" and to_protocol == "http":
            return await self.grpc_to_http(request)
        else:
            raise UnsupportedConversion(from_protocol, to_protocol)
```

### Universal Agent Interface

```python
# Future: Universal client
class UniversalAgent:
    def __init__(self, agent_card: AgentCard):
        self.card = agent_card
        self.client = self._create_client()
    
    def _create_client(self):
        transport = self.card["preferred_transport"]
        url = self.card["url"]
        
        if transport == "http":
            return HTTPClient(url)
        elif transport == "grpc":
            return GRPCClient(url)
        elif transport == "jsonrpc":
            return JSONRPCClient(url)
        else:
            raise UnsupportedProtocol(transport)
    
    async def invoke_skill(self, skill_id: str, **kwargs):
        return await self.client.call(skill_id, **kwargs)
```

## Protocol-Specific Search

### Search by Transport

```bash
# Find all gRPC services
curl -X POST http://localhost:8000/agents/search \
  -H "Content-Type: application/json" \
  -d '{
    "preferred_transport": "grpc"
  }'
```

### Search by Capabilities

```bash
# Find streaming-capable agents
curl -X POST http://localhost:8000/agents/search \
  -H "Content-Type: application/json" \
  -d '{
    "capabilities": {
      "streaming": true
    }
  }'
```

## Best Practices

### Protocol Selection Guidelines

#### Use HTTP/REST When:
- Building web-based agents
- Need wide compatibility
- Developing quick prototypes
- Integration with existing REST APIs

#### Use gRPC When:
- High-performance requirements
- Strong typing needed
- Streaming data
- Microservice architectures

#### Use JSON-RPC When:
- Simple RPC semantics
- Language-agnostic communication
- Lightweight protocols needed

### Agent Card Best Practices

#### Clear Protocol Declaration

```json
{
  "preferred_transport": "grpc",
  "url": "grpc://service.example.com:50051",
  "metadata": {
    "protocol_details": {
      "grpc_version": "1.50.0",
      "tls_enabled": true,
      "compression": "gzip"
    }
  }
}
```

#### Capability Documentation

```json
{
  "capabilities": {
    "streaming": true,
    "push_notifications": false,
    "state_transition_history": true
  },
  "streaming_info": {
    "max_stream_duration": "1h",
    "supported_stream_types": ["server", "client", "bidirectional"]
  }
}
```

## Integration Examples

### FastA2A HTTP Agent

```python
from fasta2a import FastA2A
from a2a_registry import A2ARegistryClient

app = FastA2A()
registry = A2ARegistryClient("http://localhost:8000")

@app.on_startup
async def register():
    await registry.register_agent({
        "name": "fasta2a-service",
        "url": "http://localhost:3000",
        "preferred_transport": "http",
        "description": "FastA2A HTTP service"
    })

@app.skill("greet")
async def greet(name: str) -> str:
    return f"Hello, {name}!"
```

### gRPC Agent Registration

```python
import grpc
from concurrent import futures
from a2a_registry import A2ARegistryClient

class MyGRPCService:
    async def register_with_a2a(self):
        registry = A2ARegistryClient("http://localhost:8000")
        await registry.register_agent({
            "name": "grpc-service",
            "url": "grpc://localhost:50051",
            "preferred_transport": "grpc",
            "skills": [
                {"id": "process_data", "description": "Process data via gRPC"}
            ]
        })

# Start gRPC server and register
server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
service = MyGRPCService()
await service.register_with_a2a()
```

## Future Protocol Support

### Planned Additions

1. **MQTT**: IoT and pub/sub patterns
2. **Apache Kafka**: Event streaming
3. **WebRTC**: Peer-to-peer communication
4. **GraphQL**: Query-based APIs

### Protocol Extensibility

The registry is designed to support new protocols:

```python
# Future: Plugin architecture
class ProtocolPlugin:
    def validate_url(self, url: str) -> bool:
        """Validate URL format for this protocol"""
        
    def create_client(self, url: str) -> Client:
        """Create client for this protocol"""
        
    def health_check(self, url: str) -> bool:
        """Check if agent is healthy"""

# Register new protocol
registry.register_protocol("mqtt", MQTTProtocolPlugin())
```

## Next Steps

- Explore [Agent Discovery](agent-discovery.md) patterns
- Review [Registry Architecture](architecture.md)
- Check out [API Examples](../api/examples.md)
- Learn about [Client Libraries](../api/clients.md)