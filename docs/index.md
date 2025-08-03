# A2A Registry

## The Production-Ready Agent Discovery Platform

**Seamlessly connect and coordinate AI agents across your infrastructure with the power of A2A Protocol v0.3.0**

<div class="grid cards" markdown>

-   :material-rocket-launch:{ .lg .middle } **Production Instance**

    ---

    Start using A2A Registry immediately with our hosted production service

    [:octicons-arrow-right-24: **registry.a2a-registry.dev**](https://registry.a2a-registry.dev)

-   :material-api:{ .lg .middle } **Machine-Readable API**

    ---

    Direct API access for programmatic integration

    [:octicons-arrow-right-24: **api.a2a-registry.dev**](https://api.a2a-registry.dev)

</div>

---

## Why A2A Registry?

**The definitive solution for agent discovery, registration, and management in distributed Agent-to-Agent (A2A) networks.**

<div class="grid cards" markdown>

-   :material-shield-check:{ .lg .middle } **Production-Ready**

    ---

    Built for enterprise-scale deployments with high availability, monitoring, and reliability

-   :material-protocol:{ .lg .middle } **A2A Protocol Compliant**

    ---

    Full support for **A2A Protocol v0.3.0** with JSON-RPC 2.0 as the primary transport

-   :material-lightning-bolt:{ .lg .middle } **High Performance**

    ---

    Optimized for low-latency, high-throughput agent interactions at scale

-   :material-code-braces:{ .lg .middle } **Developer-First**

    ---

    Intuitive APIs, comprehensive SDKs, and extensive documentation

</div>

---

## Quick Integration

Get started with A2A Registry in minutes:

=== "JSON-RPC 2.0 (Recommended)"

    ```bash
    # Register your agent
    curl -X POST https://api.a2a-registry.dev/jsonrpc \
      -H "Content-Type: application/json" \
      -d '{
        "jsonrpc": "2.0",
        "method": "register_agent",
        "params": {
          "agent_card": {
            "name": "your-agent",
            "description": "Your AI agent description",
            "version": "1.0.0",
            "protocol_version": "0.3.0",
            "preferred_transport": "JSONRPC",
            "url": "https://your-agent.example.com",
            "skills": [
              {
                "id": "your_skill",
                "description": "What your agent can do"
              }
            ]
          }
        },
        "id": 1
      }'
    ```

=== "Python SDK"

    ```python
    from a2a_registry import A2ARegistryClient

    # Connect to production instance
    client = A2ARegistryClient('https://api.a2a-registry.dev')

    # Register your agent
    agent_card = {
        "name": "your-agent",
        "description": "Your AI agent description",
        "version": "1.0.0",
        "protocol_version": "0.3.0",
        "preferred_transport": "JSONRPC",
        "url": "https://your-agent.example.com",
        "skills": [
            {
                "id": "your_skill",
                "description": "What your agent can do"
            }
        ]
    }

    client.register_agent(agent_card)

    # Discover other agents
    agents = client.search_agents(query="natural language")
    ```

=== "REST API"

    ```bash
    # Alternative REST endpoint
    curl -X POST https://api.a2a-registry.dev/agents \
      -H "Content-Type: application/json" \
      -d '{
        "agent_card": {
          "name": "your-agent",
          "description": "Your AI agent description",
          "version": "1.0.0",
          "protocol_version": "0.3.0",
          "preferred_transport": "JSONRPC",
          "url": "https://your-agent.example.com",
          "skills": [
            {
              "id": "your_skill",
              "description": "What your agent can do"
            }
          ]
        }
      }'
    ```

---

## Core Capabilities

<div class="grid cards" markdown>

-   :material-account-plus:{ .lg .middle } **Agent Registration**

    ---

    Register agents with their capabilities, metadata, and communication protocols

-   :material-magnify:{ .lg .middle } **Intelligent Discovery**

    ---

    Advanced search and filtering to find the right agents for your use case

-   :material-heart-pulse:{ .lg .middle } **Health Monitoring**

    ---

    Real-time agent health checks and availability tracking

-   :material-network:{ .lg .middle } **Multi-Protocol Support**

    ---

    JSON-RPC 2.0, REST, and gRPC transport protocols supported

</div>

---

## Architecture & Standards

- **A2A Protocol v0.3.0 Compliant**: Full implementation of the latest A2A specification
- **JSON-RPC 2.0 Primary**: Default transport for maximum interoperability
- **RESTful Alternative**: HTTP/JSON endpoints for broader compatibility
- **Scalable Design**: Handles thousands of concurrent agent registrations
- **Production Hardened**: Enterprise-grade security, monitoring, and reliability

---

## Get Started

<div class="grid cards" markdown>

-   :material-book-open-page-variant:{ .lg .middle } **Documentation**

    ---

    Comprehensive guides, API references, and tutorials

    [Explore Documentation](documentation/){ .md-button .md-button--primary }

-   :material-github:{ .lg .middle } **Open Source**

    ---

    Self-host your own registry or contribute to the project

    [:octicons-mark-github-16: View on GitHub](https://github.com/allenday/a2a-registry){ .md-button }

-   :material-download:{ .lg .middle } **Install Locally**

    ---

    Run your own A2A Registry instance for development or production

    ```bash
    pip install a2a-registry
    a2a-registry serve
    ```

-   :material-api:{ .lg .middle } **API Reference**

    ---

    Complete API documentation for all endpoints and methods

    [API Reference](documentation/api/){ .md-button }

</div>

---

## Production Endpoints

| Service | URL | Purpose |
|---------|-----|---------|
| **Web Interface** | [registry.a2a-registry.dev](https://registry.a2a-registry.dev) | Browse agents, documentation, and management interface |
| **JSON-RPC API** | [api.a2a-registry.dev/jsonrpc](https://api.a2a-registry.dev/jsonrpc) | Primary A2A Protocol v0.3.0 endpoint |
| **REST API** | [api.a2a-registry.dev](https://api.a2a-registry.dev) | Alternative HTTP/JSON endpoints |
| **Health Check** | [api.a2a-registry.dev/health](https://api.a2a-registry.dev/health) | Service status and monitoring |

---

## Enterprise Features

- **High Availability**: Multi-region deployment with automatic failover
- **Security**: Enterprise-grade authentication and authorization
- **Monitoring**: Comprehensive metrics, logging, and alerting
- **SLA**: 99.9% uptime guarantee with 24/7 support
- **Compliance**: SOC 2, GDPR, and industry standard certifications

---

*Built with ❤️ for the A2A Ecosystem • [MIT License](https://github.com/allenday/a2a-registry/blob/master/LICENSE) • [Support](https://github.com/allenday/a2a-registry/issues)*