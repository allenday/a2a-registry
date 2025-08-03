# Client Libraries

A2A Registry provides client libraries and examples for easy integration with various programming languages and frameworks.

## Python Client

### Installation

The Python client is included with the main package:

```bash
pip install a2a-registry
```

### Basic Usage

```python
from a2a_registry import A2ARegistryClient
import asyncio

async def main():
    # Initialize client
    client = A2ARegistryClient("http://localhost:8000")
    
    # Register an agent
    agent_card = {
        "name": "my-agent",
        "description": "A sample agent",
        "url": "http://localhost:3000",
        "version": "0.420.0",
        "protocol_version": "0.3.0",
        "capabilities": {
            "streaming": False,
            "push_notifications": False,
            "state_transition_history": False
        },
        "default_input_modes": ["text"],
        "default_output_modes": ["text"],
        "skills": [
            {
                "id": "hello",
                "description": "Say hello"
            }
        ],
        "preferred_transport": "http"
    }
    
    result = await client.register_agent(agent_card)
    print(f"Registered agent: {result}")
    
    # Discover agents
    agents = await client.list_agents()
    print(f"Found {len(agents)} agents")
    
    # Search for specific agents
    search_results = await client.search_agents(skills=["hello"])
    print(f"Found {len(search_results)} agents with 'hello' skill")

if __name__ == "__main__":
    asyncio.run(main())
```

### Advanced Client Features

#### Error Handling

```python
from a2a_registry import A2ARegistryClient, RegistryError

async def safe_registration():
    client = A2ARegistryClient("http://localhost:8000")
    
    try:
        await client.register_agent(agent_card)
    except RegistryError as e:
        print(f"Registration failed: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
```

#### Configuration Options

```python
client = A2ARegistryClient(
    base_url="http://localhost:8000",
    timeout=30.0,  # Request timeout in seconds
    retries=3,     # Number of retry attempts
    headers={      # Custom headers
        "Authorization": "Bearer token",
        "User-Agent": "MyAgent/1.0"
    }
)
```

#### Health Monitoring

```python
async def monitor_agent_health():
    client = A2ARegistryClient("http://localhost:8000")
    
    while True:
        try:
            health = await client.health_check()
            print(f"Registry health: {health}")
            
            # Update agent status if needed
            await client.update_agent_health("my-agent-id")
            
        except Exception as e:
            print(f"Health check failed: {e}")
        
        await asyncio.sleep(30)  # Check every 30 seconds
```

### Client API Reference

#### Core Methods

```python
class A2ARegistryClient:
    async def register_agent(self, agent_card: dict) -> dict:
        """Register a new agent"""
    
    async def get_agent(self, agent_id: str) -> dict:
        """Get specific agent by ID"""
    
    async def list_agents(self) -> List[dict]:
        """List all registered agents"""
    
    async def search_agents(self, **criteria) -> List[dict]:
        """Search agents by criteria"""
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """Remove agent from registry"""
    
    async def health_check(self) -> dict:
        """Check registry health"""
```

#### Search Parameters

```python
# Search by skills
await client.search_agents(skills=["translate", "analyze"])

# Search by query string
await client.search_agents(query="weather service")

# Search by transport protocol
await client.search_agents(preferred_transport="grpc")

# Combined search
await client.search_agents(
    skills=["ml", "inference"],
    query="tensorflow",
    preferred_transport="grpc"
)
```

## HTTP/REST Client Examples

### cURL Examples

#### Register Agent

```bash
curl -X POST http://localhost:8000/agents \
  -H "Content-Type: application/json" \
  -d '{
    "agent_card": {
      "name": "curl-agent",
      "description": "Agent registered via cURL",
      "url": "http://localhost:3000",
      "version": "0.420.0",
      "protocol_version": "0.3.0",
      "capabilities": {
        "streaming": false,
        "push_notifications": false,
        "state_transition_history": false
      },
      "default_input_modes": ["text"],
      "default_output_modes": ["text"],
      "skills": [],
      "preferred_transport": "http"
    }
  }'
```

#### List Agents

```bash
curl http://localhost:8000/agents
```

#### Search Agents

```bash
curl -X POST http://localhost:8000/agents/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "weather",
    "skills": ["forecast"]
  }'
```

#### Get Specific Agent

```bash
curl http://localhost:8000/agents/my-agent-id
```

#### Delete Agent

```bash
curl -X DELETE http://localhost:8000/agents/my-agent-id
```

### JavaScript/Node.js Client

```javascript
class A2ARegistryClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }
    
    async registerAgent(agentCard) {
        const response = await fetch(`${this.baseUrl}/agents`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ agent_card: agentCard }),
        });
        
        if (!response.ok) {
            throw new Error(`Registration failed: ${response.statusText}`);
        }
        
        return await response.json();
    }
    
    async listAgents() {
        const response = await fetch(`${this.baseUrl}/agents`);
        if (!response.ok) {
            throw new Error(`Failed to list agents: ${response.statusText}`);
        }
        return await response.json();
    }
    
    async searchAgents(criteria) {
        const response = await fetch(`${this.baseUrl}/agents/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(criteria),
        });
        
        if (!response.ok) {
            throw new Error(`Search failed: ${response.statusText}`);
        }
        
        return await response.json();
    }
}

// Usage example
const client = new A2ARegistryClient();

async function example() {
    try {
        // Register an agent
        const agentCard = {
            name: "js-agent",
            description: "JavaScript-based agent",
            url: "http://localhost:3001",
            version: "0.420.0",
            protocol_version: "0.3.0",
            capabilities: {
                streaming: false,
                push_notifications: false,
                state_transition_history: false
            },
            default_input_modes: ["text"],
            default_output_modes: ["text"],
            skills: [
                { id: "greet", description: "Greeting service" }
            ],
            preferred_transport: "http"
        };
        
        await client.registerAgent(agentCard);
        console.log("Agent registered successfully");
        
        // List all agents
        const agents = await client.listAgents();
        console.log(`Found ${agents.length} agents`);
        
        // Search for greeting agents
        const greetingAgents = await client.searchAgents({
            skills: ["greet"]
        });
        console.log(`Found ${greetingAgents.length} greeting agents`);
        
    } catch (error) {
        console.error("Error:", error.message);
    }
}

example();
```

### Go Client

```go
package main

import (
    "bytes"
    "encoding/json"
    "fmt"
    "net/http"
    "time"
)

type A2ARegistryClient struct {
    BaseURL    string
    HTTPClient *http.Client
}

type AgentCard struct {
    Name              string                 `json:"name"`
    Description       string                 `json:"description"`
    URL               string                 `json:"url"`
    Version           string                 `json:"version"`
    ProtocolVersion   string                 `json:"protocol_version"`
    Capabilities      map[string]bool        `json:"capabilities"`
    DefaultInputModes []string               `json:"default_input_modes"`
    DefaultOutputModes []string              `json:"default_output_modes"`
    Skills            []map[string]string    `json:"skills"`
    PreferredTransport string                `json:"preferred_transport"`
}

type RegisterRequest struct {
    AgentCard AgentCard `json:"agent_card"`
}

func NewA2ARegistryClient(baseURL string) *A2ARegistryClient {
    return &A2ARegistryClient{
        BaseURL: baseURL,
        HTTPClient: &http.Client{
            Timeout: 30 * time.Second,
        },
    }
}

func (c *A2ARegistryClient) RegisterAgent(agentCard AgentCard) error {
    reqBody := RegisterRequest{AgentCard: agentCard}
    jsonBody, err := json.Marshal(reqBody)
    if err != nil {
        return err
    }
    
    resp, err := c.HTTPClient.Post(
        c.BaseURL+"/agents",
        "application/json",
        bytes.NewBuffer(jsonBody),
    )
    if err != nil {
        return err
    }
    defer resp.Body.Close()
    
    if resp.StatusCode != http.StatusCreated {
        return fmt.Errorf("registration failed with status: %d", resp.StatusCode)
    }
    
    return nil
}

func (c *A2ARegistryClient) ListAgents() ([]AgentCard, error) {
    resp, err := c.HTTPClient.Get(c.BaseURL + "/agents")
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    
    var agents []AgentCard
    if err := json.NewDecoder(resp.Body).Decode(&agents); err != nil {
        return nil, err
    }
    
    return agents, nil
}

func main() {
    client := NewA2ARegistryClient("http://localhost:8000")
    
    // Register an agent
    agentCard := AgentCard{
        Name:              "go-agent",
        Description:       "Go-based agent",
        URL:               "http://localhost:3002",
        Version:           "1.0.0",
        ProtocolVersion:   "0.3.0",
        Capabilities: map[string]bool{
            "streaming":                  false,
            "push_notifications":         false,
            "state_transition_history":   false,
        },
        DefaultInputModes:  []string{"text"},
        DefaultOutputModes: []string{"text"},
        Skills: []map[string]string{
            {"id": "calculate", "description": "Mathematical calculations"},
        },
        PreferredTransport: "http",
    }
    
    if err := client.RegisterAgent(agentCard); err != nil {
        fmt.Printf("Failed to register agent: %v\n", err)
        return
    }
    
    fmt.Println("Agent registered successfully")
    
    // List agents
    agents, err := client.ListAgents()
    if err != nil {
        fmt.Printf("Failed to list agents: %v\n", err)
        return
    }
    
    fmt.Printf("Found %d agents\n", len(agents))
}
```

## Framework Integration

### FastA2A Integration

```python
from fasta2a import FastA2A
from a2a_registry import A2ARegistryClient

app = FastA2A(name="integrated-agent")
registry = A2ARegistryClient("http://localhost:8000")

@app.on_startup
async def register_with_registry():
    """Register this FastA2A agent with the registry"""
    agent_card = app.agent_card  # FastA2A provides this
    await registry.register_agent(agent_card)
    print(f"Registered {agent_card['name']} with A2A Registry")

@app.on_shutdown
async def unregister_from_registry():
    """Clean deregistration on shutdown"""
    await registry.unregister_agent(app.agent_card["name"])
    print("Unregistered from A2A Registry")

@app.skill("discover_agents")
async def discover_agents(skill: str) -> list:
    """Skill to discover other agents"""
    agents = await registry.search_agents(skills=[skill])
    return [{"name": agent["name"], "url": agent["url"]} for agent in agents]
```

### LangChain Integration

```python
from langchain.tools import BaseTool
from a2a_registry import A2ARegistryClient

class A2ADiscoveryTool(BaseTool):
    name = "a2a_discovery"
    description = "Discover A2A agents with specific capabilities"
    
    def __init__(self):
        super().__init__()
        self.registry = A2ARegistryClient("http://localhost:8000")
    
    async def _arun(self, skill: str) -> str:
        agents = await self.registry.search_agents(skills=[skill])
        if agents:
            return f"Found {len(agents)} agents with '{skill}' capability"
        else:
            return f"No agents found with '{skill}' capability"
    
    def _run(self, skill: str) -> str:
        # Sync wrapper for async call
        import asyncio
        return asyncio.run(self._arun(skill))

# Usage in LangChain agent
from langchain.agents import initialize_agent
from langchain.llms import OpenAI

tools = [A2ADiscoveryTool()]
agent = initialize_agent(tools, OpenAI(), agent="zero-shot-react-description")
```

## Client Configuration

### Environment Variables

```bash
# .env file
A2A_REGISTRY_URL=http://localhost:8000
A2A_REGISTRY_TIMEOUT=30
A2A_REGISTRY_RETRIES=3
A2A_REGISTRY_API_KEY=your-api-key
```

```python
import os
from a2a_registry import A2ARegistryClient

client = A2ARegistryClient(
    base_url=os.getenv("A2A_REGISTRY_URL", "http://localhost:8000"),
    timeout=float(os.getenv("A2A_REGISTRY_TIMEOUT", "30")),
    retries=int(os.getenv("A2A_REGISTRY_RETRIES", "3")),
    headers={
        "Authorization": f"Bearer {os.getenv('A2A_REGISTRY_API_KEY')}"
    } if os.getenv("A2A_REGISTRY_API_KEY") else {}
)
```

### Connection Pooling

```python
import aiohttp
from a2a_registry import A2ARegistryClient

# Custom session with connection pooling
connector = aiohttp.TCPConnector(
    limit=100,           # Total connection pool size
    limit_per_host=30,   # Per-host connection limit
    keepalive_timeout=30 # Keep connections alive for 30s
)

session = aiohttp.ClientSession(connector=connector)
client = A2ARegistryClient(
    base_url="http://localhost:8000",
    session=session  # Use custom session
)
```

## Error Handling

### Common Error Scenarios

```python
from a2a_registry import (
    A2ARegistryClient,
    RegistryError,
    AgentNotFoundError,
    ValidationError,
    ConnectionError
)

async def robust_agent_lookup(agent_id: str):
    client = A2ARegistryClient("http://localhost:8000")
    
    try:
        agent = await client.get_agent(agent_id)
        return agent
    except AgentNotFoundError:
        print(f"Agent {agent_id} not found in registry")
        return None
    except ValidationError as e:
        print(f"Invalid agent ID format: {e}")
        return None
    except ConnectionError:
        print("Cannot connect to registry - using cached data")
        return get_cached_agent(agent_id)
    except RegistryError as e:
        print(f"Registry error: {e}")
        return None
```

### Retry Logic

```python
import asyncio
from typing import Optional

async def register_with_retry(
    client: A2ARegistryClient,
    agent_card: dict,
    max_retries: int = 3
) -> Optional[dict]:
    """Register agent with exponential backoff retry"""
    
    for attempt in range(max_retries):
        try:
            return await client.register_agent(agent_card)
        except ConnectionError:
            if attempt == max_retries - 1:
                raise
            
            wait_time = 2 ** attempt  # Exponential backoff
            print(f"Registration failed, retrying in {wait_time}s...")
            await asyncio.sleep(wait_time)
    
    return None
```

## Testing with Client Libraries

### Unit Testing

```python
import pytest
from unittest.mock import AsyncMock, patch
from a2a_registry import A2ARegistryClient

@pytest.mark.asyncio
async def test_register_agent():
    client = A2ARegistryClient("http://localhost:8000")
    
    # Mock the HTTP call
    with patch.object(client, '_make_request') as mock_request:
        mock_request.return_value = {"agent_id": "test-agent", "status": "registered"}
        
        result = await client.register_agent({
            "name": "test-agent",
            "url": "http://test.com"
        })
        
        assert result["agent_id"] == "test-agent"
        mock_request.assert_called_once()

@pytest.mark.asyncio
async def test_search_agents():
    client = A2ARegistryClient("http://localhost:8000")
    
    with patch.object(client, '_make_request') as mock_request:
        mock_request.return_value = [
            {"name": "agent1", "skills": ["skill1"]},
            {"name": "agent2", "skills": ["skill1", "skill2"]}
        ]
        
        results = await client.search_agents(skills=["skill1"])
        
        assert len(results) == 2
        assert all("skill1" in agent["skills"] for agent in results)
```

### Integration Testing

```python
import pytest
import asyncio
from a2a_registry import A2ARegistryClient

@pytest.mark.asyncio
async def test_full_agent_lifecycle():
    """Test complete agent registration, discovery, and cleanup"""
    client = A2ARegistryClient("http://localhost:8000")
    
    agent_card = {
        "name": "test-lifecycle-agent",
        "description": "Agent for testing lifecycle",
        "url": "http://localhost:9999",
        "version": "0.420.0",
        "protocol_version": "0.3.0",
        "skills": [{"id": "test", "description": "Test skill"}]
    }
    
    try:
        # Register
        register_result = await client.register_agent(agent_card)
        assert "agent_id" in register_result
        
        agent_id = register_result["agent_id"]
        
        # Verify registration
        agent = await client.get_agent(agent_id)
        assert agent["name"] == "test-lifecycle-agent"
        
        # Search
        search_results = await client.search_agents(skills=["test"])
        assert any(a["name"] == "test-lifecycle-agent" for a in search_results)
        
    finally:
        # Cleanup
        try:
            await client.unregister_agent(agent_id)
        except:
            pass  # Ignore cleanup errors
```

## Next Steps

- Review [API Examples](examples.md) for more usage patterns
- Check [API Reference](reference.md) for complete documentation
- Explore [Integration Examples](../examples/basic-usage.md)
- Learn about [Protocol Support](../concepts/protocols.md)