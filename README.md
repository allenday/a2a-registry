# A2A Registry

[![CI](https://github.com/allenday/a2a-registry/workflows/CI/badge.svg)](https://github.com/allenday/a2a-registry/actions)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![PyPI Version](https://img.shields.io/pypi/v/a2a-registry.svg)](https://pypi.org/project/a2a-registry/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Production-Ready Agent Discovery Platform

A2A Registry is the definitive solution for agent discovery, registration, and management in distributed Agent-to-Agent (A2A) networks. Built on **A2A Protocol v0.3.0** and FastA2A standards, it provides a robust, scalable infrastructure for dynamic agent ecosystems.

### Version Information
- **Current Version**: 0.1.1
- **Protocol Version**: A2A Protocol v0.3.0
- **Status**: Production-Ready

### Key Highlights
- Universal Agent Coordination
- Multi-Protocol Support (JSON-RPC 2.0, REST, GraphQL)
- High-Performance Architecture
- Comprehensive Security Model
- Flexible Extension System

## Quick Start

### Prerequisites
- Python 3.9+
- pip package manager

### Installation

```bash
pip install a2a-registry
```

### Basic Usage

#### Start Registry Server
```bash
# Start with default configuration
a2a-registry serve

# Custom configuration
a2a-registry serve --host 0.0.0.0 --port 8080 --log-level DEBUG
```

#### Agent Registration
```python
from a2a_registry import A2ARegistryClient

# Initialize client
client = A2ARegistryClient('http://localhost:8000')

# Define and register agent
weather_agent = {
    "name": "weather-agent",
    "description": "Provides real-time weather information",
    "version": "0.420.0",
    "protocol_version": "0.3.0",
    "preferred_transport": "JSONRPC",
    "skills": [
        {"id": "get_current_weather", "description": "Current weather data"},
        {"id": "get_forecast", "description": "7-day weather forecast"}
    ]
}

# Register agent
client.register_agent(weather_agent)

# Discover agents
forecast_agents = client.search_agents(skills=['get_forecast'])
```

## Documentation

For comprehensive guides, API references, and tutorials:
- [Full Documentation](https://allenday.github.io/a2a-registry/)
- [Getting Started Guide](/docs/documentation/getting-started/quickstart.md)
- [API Reference](/docs/documentation/api/reference.md)

## Supported Protocols
- JSON-RPC 2.0 (Primary)
- REST API
- GraphQL

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on how to get started.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments
- [A2A Protocol Specification](https://a2a-protocol.org)
- [FastA2A](https://github.com/a2aproject/FastA2A)
- [FastAPI](https://fastapi.tiangolo.com/)
- [gRPC](https://grpc.io/)

---

**Built for the Future of Agent Ecosystems**