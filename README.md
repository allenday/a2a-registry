# A2A Registry

[![CI](https://github.com/allenday/a2a-registry/workflows/CI/badge.svg)](https://github.com/allenday/a2a-registry/actions)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![PyPI Version](https://img.shields.io/pypi/v/a2a-registry.svg)](https://pypi.org/project/a2a-registry/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## 🚀 Production-Ready Agent Discovery Platform

A2A Registry is the definitive solution for agent discovery, registration, and management in distributed Agent-to-Agent (A2A) networks. Built on FastA2A standards, it provides a robust, scalable infrastructure for dynamic agent ecosystems.

## 🌟 Why A2A Registry?

- **Universal Agent Coordination**: Seamlessly register, discover, and interact with agents across diverse platforms
- **Multi-Protocol Support**: Native support for REST, gRPC, with planned JSON-RPC
- **High Performance**: Designed for low-latency, high-throughput agent interactions
- **Developer-Friendly**: Simple, intuitive APIs with comprehensive documentation

## 🔧 Key Features

- **Fast Agent Registration**: Quick and easy agent onboarding
- **Advanced Discovery**: Powerful search and filtering capabilities
- **Real-time Health Monitoring**: Ensure agent reliability
- **Flexible Deployment**: From development to production environments
- **Extensible Architecture**: Easy to customize and integrate

## 🚀 Quick Start

### Installation

```bash
pip install a2a-registry
```

### Running the Registry

```bash
# Start the registry server
a2a-registry serve

# With custom configuration
a2a-registry serve --host 0.0.0.0 --port 8080 --log-level DEBUG
```

### Agent Registration Workflow

```python
from a2a_registry import A2ARegistryClient

# Initialize client
client = A2ARegistryClient('http://localhost:8000')

# Define agent capabilities
weather_agent = {
    "name": "weather-agent",
    "description": "Provides real-time weather information",
    "version": "1.0.0",
    "skills": [
        {
            "id": "get_current_weather",
            "description": "Retrieve current weather for a location"
        },
        {
            "id": "get_forecast",
            "description": "Get 7-day weather forecast"
        }
    ]
}

# Register agent
client.register_agent(weather_agent)

# Discover agents with specific skills
forecast_agents = client.search_agents(skills=['get_forecast'])
```

## 📚 Documentation

For comprehensive guides, API references, and tutorials, visit our [Full Documentation](https://allenday.github.io/a2a-registry/).

## 🤝 Contributing

We welcome contributions! See our [Contributing Guide](https://allenday.github.io/a2a-registry/developer/contributing/) for details.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- [A2A Protocol Specification](https://a2a-protocol.org)
- [FastA2A](https://github.com/a2aproject/FastA2A)
- [FastAPI](https://fastapi.tiangolo.com/)
- [gRPC](https://grpc.io/)

---

**Built with ❤️ for the A2A Ecosystem**