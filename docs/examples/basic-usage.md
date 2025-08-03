# Basic Usage

This guide demonstrates the fundamental operations of the A2A Registry with practical examples. All examples follow **A2A Protocol v0.3.0** specifications.

## Starting the Registry

First, start the A2A Registry server:

```bash
a2a-registry serve
```

The server will start on `http://localhost:8000` by default.

## Health Check

Verify the server is running:

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

## Basic Agent Operations

### 1. Register Your First Agent

Create an agent card and register it:

```bash
curl -X POST http://localhost:8000/agents \
  -H "Content-Type: application/json" \
  -d '{
    "agent_card": {
      "name": "hello-world-agent",
      "description": "A simple greeting agent",
      "url": "http://localhost:3000",
      "version": "0.420.0",
      "protocol_version": "0.3.0",
      "skills": [
        {
          "id": "say_hello",
          "description": "Generate personalized greetings"
        },
        {
          "id": "get_time",
          "description": "Get current date and time"
        }
      ]
    }
  }'
```

Response:
```json
{
  "success": true,
  "agent_id": "hello-world-agent",
  "message": "Agent registered successfully"
}
```

### 2. List All Agents

See what agents are registered:

```bash
curl http://localhost:8000/agents
```

Response:
```json
{
  "agents": [
    {
      "name": "hello-world-agent",
      "description": "A simple greeting agent",
      "url": "http://localhost:3000",
      "version": "0.420.0",
      "protocol_version": "0.3.0",
      "skills": [
        {
          "id": "say_hello",
          "description": "Generate personalized greetings"
        },
        {
          "id": "get_time",
          "description": "Get current date and time"
        }
      ]
    }
  ],
  "count": 1
}
```

### 3. Get Specific Agent

Retrieve information about a specific agent:

```bash
curl http://localhost:8000/agents/hello-world-agent
```

Response:
```json
{
      "agent_card": {
      "name": "hello-world-agent",
      "description": "A simple greeting agent",
      "url": "http://localhost:3000",
      "version": "0.420.0",
      "protocol_version": "0.3.0",
      "skills": [...]
    }
}
```

### 4. Search for Agents

Find agents by name, description, or skills:

```bash
curl -X POST http://localhost:8000/agents/search \
  -H "Content-Type: application/json" \
  -d '{"query": "greeting"}'
```

Response:
```json
{
  "agents": [
    {
      "name": "hello-world-agent",
      "description": "A simple greeting agent",
      ...
    }
  ],
  "count": 1,
  "query": "greeting"
}
```

### 5. Update Agent Information

Update an existing agent (re-register with same name):

```bash
curl -X POST http://localhost:8000/agents \
  -H "Content-Type: application/json" \
  -d '{
    "agent_card": {
      "name": "hello-world-agent",
      "description": "An improved greeting agent with more features",
      "url": "http://localhost:3000",
      "version": "0.421.0",
      "protocol_version": "0.3.0",
      "skills": [
        {
          "id": "say_hello",
          "description": "Generate personalized greetings"
        },
        {
          "id": "get_time", 
          "description": "Get current date and time"
        },
        {
          "id": "translate_greeting",
          "description": "Translate greetings to different languages"
        }
      ]
    }
  }'
```

### 6. Unregister Agent

Remove an agent from the registry:

```bash
curl -X DELETE http://localhost:8000/agents/hello-world-agent
```

Response:
```json
{
  "success": true,
  "message": "Agent unregistered successfully"
}
```

## Python Client Example

Here's how to interact with the registry using Python:

```python
import requests
import json

class A2ARegistryClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def health_check(self):
        """Check if registry is healthy."""
        response = requests.get(f"{self.base_url}/health")
        return response.json()
    
    def register_agent(self, agent_card):
        """Register an agent."""
        response = requests.post(
            f"{self.base_url}/agents",
            json={"agent_card": agent_card}
        )
        response.raise_for_status()
        return response.json()
    
    def get_agent(self, agent_id):
        """Get a specific agent."""
        response = requests.get(f"{self.base_url}/agents/{agent_id}")
        response.raise_for_status()
        return response.json()
    
    def list_agents(self):
        """List all agents."""
        response = requests.get(f"{self.base_url}/agents")
        response.raise_for_status()
        return response.json()
    
    def search_agents(self, query):
        """Search for agents."""
        response = requests.post(
            f"{self.base_url}/agents/search",
            json={"query": query}
        )
        response.raise_for_status()
        return response.json()
    
    def unregister_agent(self, agent_id):
        """Unregister an agent."""
        response = requests.delete(f"{self.base_url}/agents/{agent_id}")
        response.raise_for_status()
        return response.json()

# Usage example
def main():
    client = A2ARegistryClient()
    
    # Check health
    health = client.health_check()
    print(f"Registry status: {health['status']}")
    
    # Define agent
    agent_card = {
        "name": "calculator-agent",
        "description": "Mathematical calculation agent",
        "url": "http://localhost:4000",
        "version": "2.0.0",
        "protocol_version": "0.3.0",
        "skills": [
            {
                "id": "add",
                "description": "Add two numbers"
            },
            {
                "id": "multiply",
                "description": "Multiply two numbers"
            },
            {
                "id": "solve_equation",
                "description": "Solve algebraic equations"
            }
        ]
    }
    
    # Register agent
    result = client.register_agent(agent_card)
    print(f"Registered: {result['agent_id']}")
    
    # List all agents
    agents = client.list_agents()
    print(f"Total agents: {agents['count']}")
    
    # Search for math-related agents
    search_results = client.search_agents("math")
    print(f"Math agents found: {search_results['count']}")
    
    # Get specific agent
    agent = client.get_agent("calculator-agent")
    print(f"Agent URL: {agent['agent_card']['url']}")
    
    # Update agent (register again with same name)
    updated_card = agent_card.copy()
    updated_card["version"] = "2.1.0"
    updated_card["skills"].append({
        "id": "calculate_derivative",
        "description": "Calculate derivatives of functions"
    })
    
    result = client.register_agent(updated_card)
    print(f"Updated: {result['agent_id']}")
    
    # Final cleanup
    result = client.unregister_agent("calculator-agent")
    print(f"Unregistered: {result['success']}")

if __name__ == "__main__":
    main()
```

## JavaScript/Node.js Example

```javascript
class A2ARegistryClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }

    async healthCheck() {
        const response = await fetch(`${this.baseUrl}/health`);
        return response.json();
    }

    async registerAgent(agentCard) {
        const response = await fetch(`${this.baseUrl}/agents`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ agent_card: agentCard })
        });
        
        if (!response.ok) {
            throw new Error(`Registration failed: ${response.statusText}`);
        }
        
        return response.json();
    }

    async listAgents() {
        const response = await fetch(`${this.baseUrl}/agents`);
        return response.json();
    }

    async searchAgents(query) {
        const response = await fetch(`${this.baseUrl}/agents/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });
        return response.json();
    }

    async getAgent(agentId) {
        const response = await fetch(`${this.baseUrl}/agents/${agentId}`);
        if (!response.ok) {
            throw new Error(`Agent not found: ${agentId}`);
        }
        return response.json();
    }

    async unregisterAgent(agentId) {
        const response = await fetch(`${this.baseUrl}/agents/${agentId}`, {
            method: 'DELETE'
        });
        return response.json();
    }
}

// Example usage
async function example() {
    const client = new A2ARegistryClient();
    
    // Register a web scraper agent
    const agentCard = {
        name: 'web-scraper-agent',
        description: 'Web scraping and data extraction agent',
        url: 'http://localhost:5000',
        version: '1.3.0',
        protocol_version: '0.3.0',
        skills: [
            {
                id: 'scrape_webpage',
                description: 'Extract content from web pages'
            },
            {
                id: 'extract_links',
                description: 'Find and extract all links from a page'
            },
            {
                id: 'monitor_changes',
                description: 'Monitor web pages for changes'
            }
        ]
    };
    
    try {
        // Register
        const registerResult = await client.registerAgent(agentCard);
        console.log('Agent registered:', registerResult.agent_id);
        
        // Search for web-related agents
        const searchResults = await client.searchAgents('web');
        console.log('Web agents found:', searchResults.count);
        
        // List all agents
        const allAgents = await client.listAgents();
        console.log('Total agents:', allAgents.count);
        
        // Get specific agent
        const agent = await client.getAgent('web-scraper-agent');
        console.log('Agent version:', agent.agent_card.version);
        
    } catch (error) {
        console.error('Error:', error.message);
    }
}

example();
```

## Common Patterns

### Agent Lifecycle Management

```python
import atexit
import time
import threading

class ManagedAgent:
    def __init__(self, registry_client, agent_card):
        self.client = registry_client
        self.agent_card = agent_card
        self.registered = False
        self.heartbeat_interval = 30  # seconds
        self.heartbeat_thread = None
        self.stop_heartbeat = threading.Event()
    
    def register(self):
        """Register agent with the registry."""
        result = self.client.register_agent(self.agent_card)
        self.registered = True
        print(f"Agent {self.agent_card['name']} registered")
        
        # Setup automatic unregister on exit
        atexit.register(self.unregister)
        
        return result
    
    def unregister(self):
        """Unregister agent from the registry."""
        if self.registered:
            try:
                self.client.unregister_agent(self.agent_card['name'])
                self.registered = False
                print(f"Agent {self.agent_card['name']} unregistered")
            except Exception as e:
                print(f"Failed to unregister: {e}")
    
    def start_heartbeat(self):
        """Start periodic re-registration to maintain presence."""
        def heartbeat():
            while not self.stop_heartbeat.is_set():
                if self.registered:
                    try:
                        self.client.register_agent(self.agent_card)
                        print(f"Heartbeat sent for {self.agent_card['name']}")
                    except Exception as e:
                        print(f"Heartbeat failed: {e}")
                
                self.stop_heartbeat.wait(self.heartbeat_interval)
        
        self.heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
        self.heartbeat_thread.start()
    
    def stop_heartbeat_thread(self):
        """Stop the heartbeat thread."""
        self.stop_heartbeat.set()
        if self.heartbeat_thread:
            self.heartbeat_thread.join()

# Usage
agent_card = {
    "name": "my-service-agent",
    "description": "My service agent",
    "url": "http://localhost:6000",
    "version": "0.420.0",
    "protocol_version": "0.3.0",
    "skills": []
}

client = A2ARegistryClient()
managed_agent = ManagedAgent(client, agent_card)

# Register and start heartbeat
managed_agent.register()
managed_agent.start_heartbeat()

# Your agent's main loop
try:
    while True:
        # Do agent work
        time.sleep(1)
except KeyboardInterrupt:
    managed_agent.stop_heartbeat_thread()
    managed_agent.unregister()
```

This basic usage guide covers the fundamental operations you'll need to work with the A2A Registry. For more advanced features and use cases, see the [Agent Registration](agent-registration.md) and [Agent Discovery](agent-discovery.md) examples.