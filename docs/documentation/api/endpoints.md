# API Endpoints

This page documents all available endpoints for both REST and gRPC interfaces.

## REST API Endpoints

### Health Check

**GET** `/health`

Check if the registry service is running.

**Response:**
```json
{
  "status": "healthy",
  "service": "A2A Registry"
}
```

### Register Agent

**POST** `/agents`

Register a new agent or update an existing one.

**Request Body:**
```json
{
  "agent_card": {
    "name": "string",
    "description": "string", 
    "url": "string",
    "version": "string",
    "protocol_version": "string",
    "skills": [
      {
        "id": "string",
        "description": "string"
      }
    ]
  }
}
```

**Response:**
```json
{
  "success": true,
  "agent_id": "string",
  "message": "Agent registered successfully"
}
```

### Get Agent

**GET** `/agents/{agent_id}`

Retrieve a specific agent's information.

**Path Parameters:**
- `agent_id` (string): The unique identifier of the agent

**Response:**
```json
{
  "agent_card": {
    "name": "string",
    "description": "string",
    "url": "string", 
    "version": "string",
    "protocol_version": "string",
    "skills": [...]
  }
}
```

### List All Agents

**GET** `/agents`

Retrieve all registered agents.

**Response:**
```json
{
  "agents": [
    {
      "name": "string",
      "description": "string",
      "url": "string",
      "version": "string", 
      "protocol_version": "string",
      "skills": [...]
    }
  ],
  "count": 0
}
```

### Search Agents

**POST** `/agents/search`

Search for agents based on criteria.

**Request Body:**
```json
{
  "query": "string"
}
```

**Response:**
```json
{
  "agents": [...],
  "count": 0,
  "query": "string"
}
```

### Unregister Agent

**DELETE** `/agents/{agent_id}`

Remove an agent from the registry.

**Path Parameters:**
- `agent_id` (string): The unique identifier of the agent

**Response:**
```json
{
  "success": true,
  "message": "Agent unregistered successfully"
}
```

## gRPC Service Methods

The gRPC interface is defined in `proto/registry.proto` and provides the following methods:

### GetAgentCard

Retrieve a specific agent card by ID.

**Request:** `GetAgentCardRequest`
```protobuf
message GetAgentCardRequest {
  string agent_id = 1;
  bool include_registry_metadata = 2;
}
```

**Response:** `GetAgentCardResponse`
```protobuf
message GetAgentCardResponse {
  RegistryAgentCard registry_agent_card = 1;
  bool found = 2;
}
```

### StoreAgentCard

Register or update an agent card.

**Request:** `StoreAgentCardRequest`
```protobuf
message StoreAgentCardRequest {
  RegistryAgentCard registry_agent_card = 1;
  bool upsert = 2;
}
```

**Response:** `StoreAgentCardResponse`
```protobuf
message StoreAgentCardResponse {
  bool success = 1;
  string message = 2;
  RegistryAgentCard stored_card = 3;
}
```

### SearchAgents

Search for agents based on criteria.

**Request:** `SearchAgentsRequest`
```protobuf
message SearchAgentsRequest {
  AgentSearchCriteria criteria = 1;
}
```

**Response:** `SearchAgentsResponse`
```protobuf
message SearchAgentsResponse {
  repeated RegistryAgentCard agents = 1;
  string next_page_token = 2;
  int32 total_count = 3;
}
```

### DeleteAgentCard

Remove an agent from the registry.

**Request:** `DeleteAgentCardRequest`
```protobuf
message DeleteAgentCardRequest {
  string agent_id = 1;
  string requester_id = 2;
}
```

**Response:** `google.protobuf.Empty`

### PingAgent

Health check and status update for an agent.

**Request:** `PingAgentRequest`
```protobuf
message PingAgentRequest {
  string agent_id = 1;
  google.protobuf.Timestamp timestamp = 2;
}
```

**Response:** `PingAgentResponse`
```protobuf
message PingAgentResponse {
  bool responsive = 1;
  int32 response_time_ms = 2;
  string status = 3;
  google.protobuf.Timestamp timestamp = 4;
}
```

### ListAllAgents

Get all registered agents with pagination.

**Request:** `ListAllAgentsRequest`
```protobuf
message ListAllAgentsRequest {
  bool include_inactive = 1;
  int32 page_size = 2;
  string page_token = 3;
}
```

**Response:** `ListAllAgentsResponse`
```protobuf
message ListAllAgentsResponse {
  repeated RegistryAgentCard agents = 1;
  string next_page_token = 2;
  int32 total_count = 3;
}
```

### UpdateAgentStatus

Update agent status and health information.

**Request:** `UpdateAgentStatusRequest`
```protobuf
message UpdateAgentStatusRequest {
  string agent_id = 1;
  string status = 2;
  int32 health_score = 3;
  google.protobuf.Timestamp timestamp = 4;
}
```

**Response:** `UpdateAgentStatusResponse`
```protobuf
message UpdateAgentStatusResponse {
  bool success = 1;
  string message = 2;
  RegistryAgentCard updated_card = 3;
}
```

## Protocol Buffer Definitions

The complete Protocol Buffer definitions are available in:
- [`proto/registry.proto`](https://github.com/allenday/a2a-registry/blob/master/proto/registry.proto) - Registry service definitions
- [`third_party/a2a/specification/grpc/a2a.proto`](https://github.com/a2aproject/A2A/blob/main/specification/grpc/a2a.proto) - Core A2A types

## Error Responses

### REST API Errors

```json
{
  "detail": "Error message"
}
```

### gRPC Errors

gRPC errors follow standard gRPC status codes with descriptive messages in the status details.

## Client Libraries

### Python gRPC Client Example

```python
import grpc
from a2a_registry.proto.generated import registry_pb2_grpc, registry_pb2

# Create channel
channel = grpc.insecure_channel('localhost:50051')
stub = registry_pb2_grpc.A2ARegistryServiceStub(channel)

# Search for agents
request = registry_pb2.SearchAgentsRequest(
    criteria=registry_pb2.AgentSearchCriteria(
        required_skills=['weather', 'forecast']
    )
)
response = stub.SearchAgents(request)
```

### Python REST Client Example

```python
import requests

# Search for agents
response = requests.post(
    'http://localhost:8000/agents/search',
    json={'query': 'weather'}
)
agents = response.json()
```