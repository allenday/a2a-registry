# A2A Registry

A FastA2A-compatible Agent-to-Agent Registry server that allows A2A agents to register and discover each other.

## Overview

The A2A Registry is a central service that enables agent discovery and registration in Agent-to-Agent (A2A) networks. It provides a RESTful API for agents to:

- **Register** themselves with their capabilities and metadata
- **Discover** other agents by searching through registered agents
- **Retrieve** detailed information about specific agents
- **Unregister** when they go offline

## Key Features

- **FastA2A Compatible**: Built using FastA2A schemas for seamless integration
- **RESTful API**: Clean, well-documented REST endpoints
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

```bash
curl -X POST http://localhost:8000/agents \
  -H "Content-Type: application/json" \
  -d '{
    "agent_card": {
      "name": "my-agent",
      "description": "A sample agent",
      "url": "http://localhost:3000",
      "version": "1.0.0",
      "protocol_version": "1.0.0",
      "skills": []
    }
  }'
```

### Discover Agents

```bash
curl http://localhost:8000/agents
```

## Documentation

- [**Getting Started**](getting-started/installation.md) - Installation and setup guide
- [**API Reference**](api/overview.md) - Complete API documentation
- [**Developer Guide**](developer/contributing.md) - Contributing and development
- [**Examples**](examples/basic-usage.md) - Usage examples and tutorials

## Support

- [GitHub Issues](https://github.com/allendy/a2a-registry/issues) - Bug reports and feature requests
- [GitHub Discussions](https://github.com/allendy/a2a-registry/discussions) - Questions and community support

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/allendy/a2a-registry/blob/master/LICENSE) file for details.