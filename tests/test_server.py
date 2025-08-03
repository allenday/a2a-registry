"""Tests for A2A Registry server functionality."""

import pytest
from fastapi.testclient import TestClient

from a2a_registry.server import create_app
from a2a_registry import A2A_PROTOCOL_VERSION


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


def create_agent_card(name: str, description: str = "", url: str = "http://localhost:8000"):
    """Helper to create a valid AgentCard payload."""
    return {
        "agent_card": {
            "name": name,
            "description": description or f"Description for {name}",
            "url": url,
            "version": "0.420.0",
            "protocol_version": A2A_PROTOCOL_VERSION,
            "capabilities": {
                "streaming": False,
                "push_notifications": False,
                "state_transition_history": False
            },
            "default_input_modes": ["text"],
            "default_output_modes": ["text"],
            "skills": [],
            "preferred_transport": "http"
        }
    }


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "A2A Registry"}


def test_register_agent(client):
    """Test agent registration."""
    payload = create_agent_card("test-agent-001", "A test agent for unit tests", "http://localhost:8001")
    
    response = client.post("/agents", json=payload)
    assert response.status_code == 200
    
    result = response.json()
    assert result["success"] is True
    assert result["agent_id"] == "test-agent-001"
    assert result["message"] == "Agent registered successfully"


def test_get_agent(client):
    """Test getting an agent."""
    # First register an agent
    register_payload = create_agent_card("test-agent-002", "Another test agent", "http://localhost:8002")
    
    client.post("/agents", json=register_payload)
    
    # Now get the agent
    response = client.get("/agents/test-agent-002")
    assert response.status_code == 200
    
    result = response.json()
    assert result["agent_card"]["name"] == "test-agent-002"
    assert result["agent_card"]["description"] == "Another test agent"
    assert result["agent_card"]["url"] == "http://localhost:8002"


def test_get_nonexistent_agent(client):
    """Test getting a non-existent agent."""
    response = client.get("/agents/nonexistent-agent")
    assert response.status_code == 404
    assert response.json()["detail"] == "Agent not found"


def test_list_agents(client):
    """Test listing agents."""
    # Register a couple of agents first
    for i in range(2):
        register_payload = create_agent_card(f"list-test-agent-{i}", f"Test agent {i} for list test", f"http://localhost:800{i+3}")
        client.post("/agents", json=register_payload)
    
    # Now list agents
    response = client.get("/agents")
    assert response.status_code == 200
    
    result = response.json()
    assert result["count"] >= 2
    assert len(result["agents"]) >= 2
    
    # Check that our test agents are in the list
    agent_names = [agent["name"] for agent in result["agents"]]
    assert "list-test-agent-0" in agent_names
    assert "list-test-agent-1" in agent_names


def test_search_agents(client):
    """Test searching agents."""
    # Register an agent with specific capabilities
    register_payload = create_agent_card("search-test-agent", "An agent designed for search testing", "http://localhost:8010")
    
    client.post("/agents", json=register_payload)
    
    # Search for the agent by capability
    search_payload = {"query": "search"}
    response = client.post("/agents/search", json=search_payload)
    assert response.status_code == 200
    
    result = response.json()
    assert result["count"] >= 1
    assert result["query"] == "search"
    
    # Check that our test agent is in the results
    agent_names = [agent["name"] for agent in result["agents"]]
    assert "search-test-agent" in agent_names


def test_unregister_agent(client):
    """Test unregistering an agent."""
    # First register an agent
    register_payload = create_agent_card("delete-test-agent", "An agent to be deleted", "http://localhost:8020")
    
    response = client.post("/agents", json=register_payload)
    assert response.status_code == 200
    
    # Verify it exists
    response = client.get("/agents/delete-test-agent")
    assert response.status_code == 200
    
    # Delete the agent
    response = client.delete("/agents/delete-test-agent")
    assert response.status_code == 200
    
    result = response.json()
    assert result["success"] is True
    assert result["message"] == "Agent unregistered successfully"
    
    # Verify it's gone
    response = client.get("/agents/delete-test-agent")
    assert response.status_code == 404


def test_unregister_nonexistent_agent(client):
    """Test unregistering a non-existent agent."""
    response = client.delete("/agents/nonexistent-agent")
    assert response.status_code == 404
    assert response.json()["detail"] == "Agent not found"


def test_invalid_agent_registration(client):
    """Test registering an invalid agent."""
    # Missing required fields
    payload = {
        "agent_card": {
            "name": "Invalid Agent"
            # Missing required fields like url, version, etc.
        }
    }
    
    response = client.post("/agents", json=payload)
    assert response.status_code == 400