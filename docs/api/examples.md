# API Examples

This page provides practical examples of using the A2A Registry API with different protocols and programming languages.

## REST API Examples

### Python with requests

```python
import requests
import json

# Base URL for the registry
BASE_URL = "http://localhost:8000"

# 1. Register an agent
agent_card = {
    "agent_card": {
        "name": "weather-service",
        "description": "Provides weather information and forecasts",
        "url": "http://weather-agent.example.com:3000",
        "version": "0.420.0",
        "protocol_version": "0.3.0",
        "skills": [
            {
                "id": "get_current_weather",
                "description": "Get current weather conditions for a location"
            },
            {
                "id": "get_forecast", 
                "description": "Get weather forecast for upcoming days"
            }
        ]
    }
}

response = requests.post(f"{BASE_URL}/agents", json=agent_card)
print(f"Registration: {response.json()}")

# 2. List all agents
response = requests.get(f"{BASE_URL}/agents")
agents = response.json()
print(f"Found {agents['count']} agents")

# 3. Search for weather-related agents
search_request = {"query": "weather"}
response = requests.post(f"{BASE_URL}/agents/search", json=search_request)
results = response.json()
print(f"Weather agents: {len(results['agents'])}")

# 4. Get specific agent
agent_id = "weather-service"
response = requests.get(f"{BASE_URL}/agents/{agent_id}")
if response.status_code == 200:
    agent = response.json()
    print(f"Agent URL: {agent['agent_card']['url']}")

# 5. Unregister agent
response = requests.delete(f"{BASE_URL}/agents/{agent_id}")
print(f"Unregistration: {response.json()}")
```

### JavaScript/Node.js with fetch

```javascript
// 1. Register an agent
const agentCard = {
  agent_card: {
    name: "translation-service",
    description: "Multi-language translation agent",
    url: "http://translator.example.com:4000",
    version: "0.420.0",
    protocol_version: "0.3.0",
    skills: [
      {
        id: "translate_text",
        description: "Translate text between languages"
      },
      {
        id: "detect_language",
        description: "Detect the language of input text"
      }
    ]
  }
};

const response = await fetch('http://localhost:8000/agents', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(agentCard)
});

const result = await response.json();
console.log('Registration result:', result);

// 2. Search for translation agents
const searchResponse = await fetch('http://localhost:8000/agents/search', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ query: 'translate' })
});

const searchResults = await searchResponse.json();
console.log(`Found ${searchResults.count} translation agents`);
```

### cURL Examples

```bash
# 1. Health check
curl http://localhost:8000/health

# 2. Register an agent
curl -X POST http://localhost:8000/agents \
  -H "Content-Type: application/json" \
  -d '{
    "agent_card": {
      "name": "math-solver",
      "description": "Mathematical problem solving agent",
      "url": "http://math.example.com:5000",
      "version": "3.0.1",
      "protocol_version": "0.3.0",
      "skills": [
        {
          "id": "solve_equation",
          "description": "Solve mathematical equations"
        },
        {
          "id": "plot_function",
          "description": "Generate plots for mathematical functions"
        }
      ]
    }
  }'

# 3. List all agents
curl http://localhost:8000/agents

# 4. Search for math agents
curl -X POST http://localhost:8000/agents/search \
  -H "Content-Type: application/json" \
  -d '{"query": "math"}'

# 5. Get specific agent
curl http://localhost:8000/agents/math-solver

# 6. Unregister agent
curl -X DELETE http://localhost:8000/agents/math-solver
```

## gRPC Examples

### Python with grpcio

```python
import grpc
from google.protobuf.timestamp_pb2 import Timestamp
from a2a_registry.proto.generated import (
    registry_pb2,
    registry_pb2_grpc,
    a2a_pb2
)

# Create gRPC channel
channel = grpc.insecure_channel('localhost:50051')
stub = registry_pb2_grpc.A2ARegistryServiceStub(channel)

# 1. Create an agent card
agent_card = a2a_pb2.AgentCard(
    name="data-analyzer",
    description="Advanced data analysis and visualization agent",
    url="http://analyzer.example.com:6000",
    version="1.2.0",
    protocol_version="0.3.0"
)

# Add skills
skill1 = agent_card.skills.add()
skill1.id = "analyze_dataset"
skill1.description = "Perform statistical analysis on datasets"

skill2 = agent_card.skills.add()
skill2.id = "create_visualization"
skill2.description = "Generate charts and graphs from data"

# Create registry agent card
registry_card = registry_pb2.RegistryAgentCard(
    agent_card=agent_card
)

# 2. Store the agent card
store_request = registry_pb2.StoreAgentCardRequest(
    registry_agent_card=registry_card,
    upsert=True
)

try:
    store_response = stub.StoreAgentCard(store_request)
    print(f"Stored agent: {store_response.success}")
    print(f"Message: {store_response.message}")
except grpc.RpcError as e:
    print(f"gRPC error: {e.code()} - {e.details()}")

# 3. Search for agents
search_criteria = registry_pb2.AgentSearchCriteria(
    required_skills=["analyze_dataset", "visualization"],
    min_health_score=80,
    page_size=10
)

search_request = registry_pb2.SearchAgentsRequest(criteria=search_criteria)
search_response = stub.SearchAgents(search_request)

print(f"Found {len(search_response.agents)} matching agents")
for agent in search_response.agents:
    print(f"- {agent.agent_card.name}: {agent.agent_card.description}")

# 4. Get specific agent
get_request = registry_pb2.GetAgentCardRequest(
    agent_id="data-analyzer",
    include_registry_metadata=True
)

get_response = stub.GetAgentCard(get_request)
if get_response.found:
    agent = get_response.registry_agent_card.agent_card
    print(f"Found agent: {agent.name} v{agent.version}")
    if get_response.registry_agent_card.registry_metadata:
        metadata = get_response.registry_agent_card.registry_metadata
        print(f"Health score: {metadata.health_score}")
        print(f"Status: {metadata.status}")

# 5. Ping agent for health check
ping_request = registry_pb2.PingAgentRequest(
    agent_id="data-analyzer",
    timestamp=Timestamp()
)

ping_response = stub.PingAgent(ping_request)
print(f"Agent responsive: {ping_response.responsive}")
print(f"Response time: {ping_response.response_time_ms}ms")

# 6. List all agents with pagination
list_request = registry_pb2.ListAllAgentsRequest(
    include_inactive=False,
    page_size=5
)

list_response = stub.ListAllAgents(list_request)
print(f"Total agents: {list_response.total_count}")
for agent in list_response.agents:
    print(f"- {agent.agent_card.name}")

# Close the channel
channel.close()
```

### Go with grpc

```go
package main

import (
    "context"
    "log"
    "time"

    "google.golang.org/grpc"
    "google.golang.org/grpc/credentials/insecure"
    pb "dev.allenday/a2a-registry/v1"
)

func main() {
    // Connect to the server
    conn, err := grpc.Dial("localhost:50051", grpc.WithTransportCredentials(insecure.NewCredentials()))
    if err != nil {
        log.Fatalf("Failed to connect: %v", err)
    }
    defer conn.Close()

    client := pb.NewA2ARegistryServiceClient(conn)
    ctx, cancel := context.WithTimeout(context.Background(), time.Second*10)
    defer cancel()

    // Create and store an agent card
    agentCard := &pb.AgentCard{
        Name:            "document-processor",
        Description:     "Document analysis and processing agent",
        Url:             "http://docs.example.com:7000",
        Version:         "2.3.1",
        ProtocolVersion: "0.3.0",
        Skills: []*pb.Skill{
            {
                Id:          "extract_text",
                Description: "Extract text from various document formats",
            },
            {
                Id:          "summarize_document", 
                Description: "Generate summaries of long documents",
            },
        },
    }

    registryCard := &pb.RegistryAgentCard{
        AgentCard: agentCard,
    }

    storeReq := &pb.StoreAgentCardRequest{
        RegistryAgentCard: registryCard,
        Upsert:            true,
    }

    storeResp, err := client.StoreAgentCard(ctx, storeReq)
    if err != nil {
        log.Fatalf("Failed to store agent: %v", err)
    }
    log.Printf("Agent stored: %v", storeResp.Success)

    // Search for document-related agents
    searchCriteria := &pb.AgentSearchCriteria{
        RequiredSkills: []string{"extract_text"},
        PageSize:       10,
    }

    searchReq := &pb.SearchAgentsRequest{
        Criteria: searchCriteria,
    }

    searchResp, err := client.SearchAgents(ctx, searchReq)
    if err != nil {
        log.Fatalf("Failed to search: %v", err)
    }

    log.Printf("Found %d agents", len(searchResp.Agents))
    for _, agent := range searchResp.Agents {
        log.Printf("- %s: %s", agent.AgentCard.Name, agent.AgentCard.Description)
    }
}
```

## Error Handling Examples

### Python REST Error Handling

```python
import requests
from requests.exceptions import RequestException

def register_agent_safely(agent_card):
    try:
        response = requests.post(
            "http://localhost:8000/agents",
            json={"agent_card": agent_card},
            timeout=10
        )
        response.raise_for_status()  # Raises HTTPError for bad responses
        return response.json()
    except requests.exceptions.ConnectionError:
        print("Failed to connect to registry service")
    except requests.exceptions.Timeout:
        print("Request timed out")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            print(f"Invalid agent card: {e.response.json().get('detail')}")
        elif e.response.status_code == 409:
            print("Agent already exists")
        else:
            print(f"HTTP error {e.response.status_code}: {e.response.text}")
    except RequestException as e:
        print(f"Request failed: {e}")
    return None
```

### Python gRPC Error Handling

```python
import grpc
from grpc import StatusCode

def search_agents_safely(stub, criteria):
    try:
        request = registry_pb2.SearchAgentsRequest(criteria=criteria)
        response = stub.SearchAgents(request)
        return response.agents
    except grpc.RpcError as e:
        if e.code() == StatusCode.INVALID_ARGUMENT:
            print(f"Invalid search criteria: {e.details()}")
        elif e.code() == StatusCode.NOT_FOUND:
            print("No agents found matching criteria")
        elif e.code() == StatusCode.UNAVAILABLE:
            print("Registry service unavailable")
        else:
            print(f"gRPC error {e.code()}: {e.details()}")
    return []
```

## Integration Patterns

### Agent Auto-Registration

```python
import time
import threading
from contextlib import contextmanager

class AgentRegistrar:
    def __init__(self, registry_url, agent_card):
        self.registry_url = registry_url
        self.agent_card = agent_card
        self.registered = False
        self._stop_event = threading.Event()
    
    def register(self):
        """Register agent with the registry."""
        try:
            response = requests.post(
                f"{self.registry_url}/agents",
                json={"agent_card": self.agent_card}
            )
            response.raise_for_status()
            self.registered = True
            print(f"Agent {self.agent_card['name']} registered successfully")
        except Exception as e:
            print(f"Registration failed: {e}")
    
    def unregister(self):
        """Unregister agent from the registry."""
        if self.registered:
            try:
                response = requests.delete(
                    f"{self.registry_url}/agents/{self.agent_card['name']}"
                )
                response.raise_for_status()
                print(f"Agent {self.agent_card['name']} unregistered")
            except Exception as e:
                print(f"Unregistration failed: {e}")
            finally:
                self.registered = False
    
    def start_heartbeat(self, interval=30):
        """Start sending periodic heartbeats to maintain registration."""
        def heartbeat():
            while not self._stop_event.is_set():
                if self.registered:
                    try:
                        # Re-register to update last_seen timestamp
                        self.register()
                    except Exception as e:
                        print(f"Heartbeat failed: {e}")
                time.sleep(interval)
        
        thread = threading.Thread(target=heartbeat, daemon=True)
        thread.start()
        return thread
    
    def stop_heartbeat(self):
        """Stop the heartbeat thread."""
        self._stop_event.set()
    
    @contextmanager
    def managed_registration(self):
        """Context manager for automatic registration/unregistration."""
        try:
            self.register()
            heartbeat_thread = self.start_heartbeat()
            yield self
        finally:
            self.stop_heartbeat()
            self.unregister()

# Usage example
agent_card = {
    "name": "my-agent",
    "description": "My autonomous agent",
    "url": "http://localhost:3000",
    "version": "0.420.0",
    "protocol_version": "0.3.0",
    "skills": []
}

registrar = AgentRegistrar("http://localhost:8000", agent_card)

# Use with context manager for automatic cleanup
with registrar.managed_registration():
    # Agent is now registered and sending heartbeats
    # Run your agent's main loop here
    time.sleep(60)  # Simulate agent work
# Agent automatically unregistered when exiting context
```

This comprehensive API documentation provides examples for both REST and gRPC interfaces, showing how to handle errors properly and implement common integration patterns.