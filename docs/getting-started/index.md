# Getting Started with A2A Registry

Welcome to the A2A Registry! This guide will help you get up and running quickly with our Agent-to-Agent discovery platform.

## What is A2A Registry?

A2A Registry is a central discovery service for Agent-to-Agent (A2A) networks. It allows autonomous agents to:

- **Register** their capabilities and metadata
- **Discover** other agents in the network
- **Retrieve** detailed information about available agents
- **Search** for agents with specific skills or characteristics

## Prerequisites

Before getting started, ensure you have:

- Python 3.9 or higher
- pip package manager
- Basic familiarity with REST APIs (optional but helpful)

## Installation Options

### Option 1: From PyPI (Recommended)

```bash
pip install a2a-registry
```

### Option 2: From Source

```bash
git clone https://github.com/allenday/a2a-registry.git
cd a2a-registry
pip install -e .
```

## Quick Start

### 1. Start the Registry Server

```bash
# Start with default settings
a2a-registry serve

# Or with custom configuration
a2a-registry serve --host 0.0.0.0 --port 8080
```

The server will start and listen for agent registrations and discovery requests.

### 2. Verify Installation

Open your browser and navigate to `http://localhost:8000/health` to confirm the server is running.

### 3. Register Your First Agent

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
      "capabilities": {
        "streaming": false,
        "push_notifications": false,
        "state_transition_history": false
      },
      "default_input_modes": ["text"],
      "default_output_modes": ["text"],
      "skills": [
        {
          "id": "greet",
          "description": "Generates personalized greetings"
        }
      ],
      "preferred_transport": "http"
    }
  }'
```

### 4. Discover Registered Agents

```bash
# List all agents
curl http://localhost:8000/agents

# Search for specific agents
curl -X POST http://localhost:8000/agents/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "greeting"
  }'
```

## Next Steps

Now that you have A2A Registry running, explore these topics:

- [**Installation Guide**](installation.md) - Detailed installation instructions
- [**Quick Start**](quickstart.md) - More comprehensive examples
- [**Configuration**](configuration.md) - Server configuration options
- [**API Reference**](../api/overview.md) - Complete API documentation

## Common Use Cases

- **Development Environment**: Quick agent discovery during development
- **Testing**: Validate agent interactions in isolated environments
- **Production**: Central registry for distributed agent systems
- **Microservices**: Service discovery for agent-based architectures

## Need Help?

- Check our [Troubleshooting Guide](../troubleshooting/common-issues.md)
- Browse [Examples](../examples/basic-usage.md)
- Visit [GitHub Issues](https://github.com/allenday/a2a-registry/issues) for support