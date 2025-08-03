"""Tests for JSON-RPC server functionality."""

import json
from fastapi.testclient import TestClient
from a2a_registry.server import create_app
from a2a_registry import A2A_PROTOCOL_VERSION


def test_jsonrpc_register_agent():
    """Test agent registration via JSON-RPC."""
    app = create_app()
    client = TestClient(app)
    
    # JSON-RPC request to register an agent
    jsonrpc_request = {
        "jsonrpc": "2.0",
        "method": "register_agent",
        "params": {
            "agent_card": {
                "name": "test-jsonrpc-agent",
                "description": "Test agent via JSON-RPC",
                "url": "http://localhost:3000",
                "version": "0.420.0",
                "protocol_version": A2A_PROTOCOL_VERSION,
                "capabilities": {
                    "streaming": False,
                    "push_notifications": False,
                    "state_transition_history": False
                },
                "default_input_modes": ["text"],
                "default_output_modes": ["text"],
                "skills": [
                    {"id": "test_skill", "description": "A test skill"}
                ]
            }
        },
        "id": 1
    }
    
    response = client.post("/jsonrpc", json=jsonrpc_request)
    assert response.status_code == 200
    
    result = response.json()
    assert "result" in result
    assert result["result"]["success"] is True
    assert result["result"]["agent_id"] == "test-jsonrpc-agent"
    assert result["result"]["transport"] == "JSONRPC"
    assert result["id"] == 1


def test_jsonrpc_get_agent():
    """Test getting an agent via JSON-RPC."""
    app = create_app()
    client = TestClient(app)
    
    # First register an agent
    register_request = {
        "jsonrpc": "2.0",
        "method": "register_agent",
        "params": {
            "agent_card": {
                "name": "get-test-agent",
                "description": "Agent for get test",
                "url": "http://localhost:3001",
                "version": "0.420.0",
                "protocol_version": A2A_PROTOCOL_VERSION,
                "skills": []
            }
        },
        "id": 1
    }
    client.post("/jsonrpc", json=register_request)
    
    # Now get the agent
    get_request = {
        "jsonrpc": "2.0",
        "method": "get_agent",
        "params": {
            "agent_id": "get-test-agent"
        },
        "id": 2
    }
    
    response = client.post("/jsonrpc", json=get_request)
    assert response.status_code == 200
    
    result = response.json()
    assert "result" in result
    assert result["result"]["found"] is True
    assert result["result"]["agent_card"]["name"] == "get-test-agent"
    assert result["result"]["agent_card"]["preferred_transport"] == "JSONRPC"


def test_jsonrpc_list_agents():
    """Test listing agents via JSON-RPC."""
    app = create_app()
    client = TestClient(app)
    
    # Register a few agents first
    for i in range(3):
        register_request = {
            "jsonrpc": "2.0",
            "method": "register_agent",
            "params": {
                "agent_card": {
                    "name": f"list-test-agent-{i}",
                    "description": f"Agent {i} for list test",
                    "url": f"http://localhost:300{i}",
                    "version": "0.420.0",
                    "protocol_version": A2A_PROTOCOL_VERSION,
                    "skills": []
                }
            },
            "id": i + 1
        }
        client.post("/jsonrpc", json=register_request)
    
    # List all agents
    list_request = {
        "jsonrpc": "2.0", 
        "method": "list_agents",
        "params": {},
        "id": 10
    }
    
    response = client.post("/jsonrpc", json=list_request)
    assert response.status_code == 200
    
    result = response.json()
    assert "result" in result
    assert result["result"]["count"] >= 3
    assert result["result"]["transport"] == "JSONRPC"
    
    # Check that all registered agents are in the list
    agent_names = [agent["name"] for agent in result["result"]["agents"]]
    for i in range(3):
        assert f"list-test-agent-{i}" in agent_names


def test_jsonrpc_search_agents():
    """Test searching agents via JSON-RPC."""
    app = create_app()
    client = TestClient(app)
    
    # Register agents with different skills
    test_agents = [
        {
            "name": "search-agent-1",
            "description": "Agent with translation skills",
            "skills": [{"id": "translate", "description": "Translation service"}]
        },
        {
            "name": "search-agent-2", 
            "description": "Agent with weather skills",
            "skills": [{"id": "weather", "description": "Weather information"}]
        }
    ]
    
    for i, agent_data in enumerate(test_agents):
        register_request = {
            "jsonrpc": "2.0",
            "method": "register_agent",
            "params": {
                "agent_card": {
                    **agent_data,
                    "url": f"http://localhost:400{i}",
                    "version": "0.420.0",
                    "protocol_version": A2A_PROTOCOL_VERSION
                }
            },
            "id": i + 1
        }
        client.post("/jsonrpc", json=register_request)
    
    # Search by query
    search_request = {
        "jsonrpc": "2.0",
        "method": "search_agents",
        "params": {
            "query": "translation"
        },
        "id": 10
    }
    
    response = client.post("/jsonrpc", json=search_request)
    assert response.status_code == 200
    
    result = response.json()
    assert "result" in result
    assert result["result"]["count"] == 1
    assert result["result"]["agents"][0]["name"] == "search-agent-1"
    assert result["result"]["transport"] == "JSONRPC"
    
    # Search by skills
    skills_search_request = {
        "jsonrpc": "2.0",
        "method": "search_agents", 
        "params": {
            "query": "",
            "skills": ["weather"]
        },
        "id": 11
    }
    
    response = client.post("/jsonrpc", json=skills_search_request)
    assert response.status_code == 200
    
    result = response.json()
    assert result["result"]["count"] == 1
    assert result["result"]["agents"][0]["name"] == "search-agent-2"


def test_jsonrpc_unregister_agent():
    """Test unregistering an agent via JSON-RPC."""
    app = create_app()
    client = TestClient(app)
    
    # First register an agent
    register_request = {
        "jsonrpc": "2.0",
        "method": "register_agent",
        "params": {
            "agent_card": {
                "name": "unregister-test-agent",
                "description": "Agent for unregister test",
                "url": "http://localhost:3005",
                "version": "0.420.0",
                "protocol_version": A2A_PROTOCOL_VERSION,
                "skills": []
            }
        },
        "id": 1
    }
    client.post("/jsonrpc", json=register_request)
    
    # Now unregister the agent
    unregister_request = {
        "jsonrpc": "2.0",
        "method": "unregister_agent",
        "params": {
            "agent_id": "unregister-test-agent"
        },
        "id": 2
    }
    
    response = client.post("/jsonrpc", json=unregister_request)
    assert response.status_code == 200
    
    result = response.json()
    assert "result" in result
    assert result["result"]["success"] is True
    assert result["result"]["agent_id"] == "unregister-test-agent"
    
    # Verify agent is no longer available
    get_request = {
        "jsonrpc": "2.0",
        "method": "get_agent",
        "params": {
            "agent_id": "unregister-test-agent"
        },
        "id": 3
    }
    
    response = client.post("/jsonrpc", json=get_request)
    result = response.json()
    assert "error" in result
    assert result["error"]["code"] == -32001  # Agent not found


def test_jsonrpc_get_agent_card():
    """Test getting the registry's agent card via JSON-RPC."""
    app = create_app()
    client = TestClient(app)
    
    request = {
        "jsonrpc": "2.0",
        "method": "get_agent_card", 
        "params": {},
        "id": 1
    }
    
    response = client.post("/jsonrpc", json=request)
    assert response.status_code == 200
    
    result = response.json()
    assert "result" in result
    assert "agent_card" in result["result"]
    
    agent_card = result["result"]["agent_card"]
    assert agent_card["name"] == "A2A Registry"
    assert agent_card["preferred_transport"] == "JSONRPC"
    assert agent_card["protocol_version"] == A2A_PROTOCOL_VERSION
    assert len(agent_card["skills"]) > 0
    
    # Check that registry skills are properly defined
    skill_ids = [skill["id"] for skill in agent_card["skills"]]
    expected_skills = ["register_agent", "get_agent", "list_agents", "search_agents", "unregister_agent"]
    for skill in expected_skills:
        assert skill in skill_ids


def test_jsonrpc_health_check():
    """Test health check via JSON-RPC."""
    app = create_app()
    client = TestClient(app)
    
    request = {
        "jsonrpc": "2.0",
        "method": "health_check",
        "params": {},
        "id": 1
    }
    
    response = client.post("/jsonrpc", json=request)
    assert response.status_code == 200
    
    result = response.json()
    assert "result" in result
    assert result["result"]["status"] == "healthy"
    assert result["result"]["service"] == "A2A Registry"
    assert result["result"]["transport"] == "JSONRPC"
    assert result["result"]["protocol_version"] == A2A_PROTOCOL_VERSION
    assert "agents_count" in result["result"]


def test_jsonrpc_error_handling():
    """Test JSON-RPC error handling."""
    app = create_app()
    client = TestClient(app)
    
    # Test missing required field
    invalid_request = {
        "jsonrpc": "2.0",
        "method": "register_agent",
        "params": {
            "agent_card": {
                "name": "incomplete-agent",
                # Missing required fields
            }
        },
        "id": 1
    }
    
    response = client.post("/jsonrpc", json=invalid_request)
    assert response.status_code == 200
    
    result = response.json()
    assert "error" in result
    assert result["error"]["code"] == -32602  # Invalid params
    assert "Missing required field" in result["error"]["message"]
    
    # Test getting non-existent agent
    get_request = {
        "jsonrpc": "2.0",
        "method": "get_agent",
        "params": {
            "agent_id": "non-existent-agent"
        },
        "id": 2
    }
    
    response = client.post("/jsonrpc", json=get_request)
    result = response.json()
    assert "error" in result
    assert result["error"]["code"] == -32001  # Agent not found


def test_dual_transport_consistency():
    """Test that both REST and JSON-RPC transports work consistently."""
    app = create_app()
    client = TestClient(app)
    
    # Register agent via JSON-RPC
    jsonrpc_request = {
        "jsonrpc": "2.0",
        "method": "register_agent",
        "params": {
            "agent_card": {
                "name": "dual-transport-agent",
                "description": "Test dual transport",
                "url": "http://localhost:3010",
                "version": "0.420.0",
                "protocol_version": A2A_PROTOCOL_VERSION,
                "skills": []
            }
        },
        "id": 1
    }
    
    response = client.post("/jsonrpc", json=jsonrpc_request)
    assert response.status_code == 200
    assert response.json()["result"]["success"] is True
    
    # Retrieve via REST API
    rest_response = client.get("/agents/dual-transport-agent")
    assert rest_response.status_code == 200
    
    rest_result = rest_response.json()
    assert rest_result["agent_card"]["name"] == "dual-transport-agent"
    assert rest_result["agent_card"]["preferred_transport"] == "JSONRPC"
    
    # List via both transports and verify consistency
    jsonrpc_list = {
        "jsonrpc": "2.0",
        "method": "list_agents",
        "params": {},
        "id": 2
    }
    
    jsonrpc_response = client.post("/jsonrpc", json=jsonrpc_list)
    rest_list_response = client.get("/agents")
    
    jsonrpc_count = jsonrpc_response.json()["result"]["count"]
    rest_count = rest_list_response.json()["count"]
    
    assert jsonrpc_count == rest_count  # Both should see the same agents


def test_root_endpoint_info():
    """Test that root endpoint provides correct transport information."""
    app = create_app()
    client = TestClient(app)
    
    response = client.get("/")
    assert response.status_code == 200
    
    result = response.json()
    assert result["service"] == "A2A Registry"
    assert "protocols" in result
    
    protocols = result["protocols"]
    assert protocols["primary"]["transport"] == "JSONRPC"
    assert protocols["primary"]["endpoint"] == "/jsonrpc"
    assert protocols["secondary"]["transport"] == "HTTP+JSON"