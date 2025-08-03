# A2A Registry

A FastA2A-compatible Agent-to-Agent Registry server that allows A2A agents to register and discover each other. Built on **A2A Protocol v0.3.0**.

## Overview

The A2A Registry is a central service that enables agent discovery and registration in Agent-to-Agent (A2A) networks. It provides both JSON-RPC 2.0 (primary) and REST (secondary) APIs for agents to:

- **Register** themselves with their capabilities and metadata
- **Discover** other agents by searching through registered agents
- **Retrieve** detailed information about specific agents
- **Unregister** when they go offline

## Key Features

- **A2A Protocol Compliant**: Full support for A2A Protocol v0.3.0 with JSON-RPC 2.0 as default transport
- **Dual Protocol Support**: JSON-RPC 2.0 (primary) and REST (secondary) endpoints
- **In-Memory Storage**: Fast, lightweight storage for development and testing
- **Search Capabilities**: Find agents by name, description, or capabilities
- **Health Monitoring**: Built-in health check endpoints
- **Easy Setup**: Simple installation and configuration

## Quick Start

### Installation

```bash
pip install a2a-registry
```

### Start the Server

```bash
a2a-registry serve
```

The server will start on `http://localhost:8000` by default.

### Register an Agent

Using JSON-RPC 2.0 (recommended):

```bash
curl -X POST http://localhost:8000/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "register_agent",
    "params": {
      "agent_card": {
        "name": "my-agent",
        "description": "A sample agent",
        "url": "http://localhost:3000",
        "version": "0.420.0",
        "protocol_version": "0.3.0",
        "preferred_transport": "JSONRPC",
        "skills": []
      }
    },
    "id": 1
  }'
```

Using REST (alternative):

```bash
curl -X POST http://localhost:8000/agents \
  -H "Content-Type: application/json" \
  -d '{
          "agent_card": {
        "name": "my-agent",
        "description": "A sample agent",
        "url": "http://localhost:3000",
        "version": "0.420.0",
        "protocol_version": "0.3.0",
        "preferred_transport": "JSONRPC",
        "skills": []
      }
  }'
```

### Discover Agents

Using JSON-RPC 2.0:

```bash
curl -X POST http://localhost:8000/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "list_agents",
    "id": 2
  }'
```

Using REST:

```bash
curl http://localhost:8000/agents
```

## Documentation

- [**Getting Started**](getting-started/installation.md) - Installation and setup guide
- [**API Reference**](api/overview.md) - Complete API documentation
- [**Agent Extensions**](concepts/agent-extensions.md) - Modular agent capabilities and security framework
- [**Developer Guide**](developer/contributing.md) - Contributing and development
- [**Examples**](examples/basic-usage.md) - Usage examples and tutorials

## Support

- [GitHub Issues](https://github.com/allenday/a2a-registry/issues) - Bug reports and feature requests
- [GitHub Discussions](https://github.com/allenday/a2a-registry/discussions) - Questions and community support

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/allenday/a2a-registry/blob/master/LICENSE) file for details.