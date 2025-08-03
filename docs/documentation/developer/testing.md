# Testing Guide

This guide covers testing practices and strategies for the A2A Registry project.

## Test Structure

The project uses pytest for testing with the following structure:

```
tests/
├── __init__.py
├── test_basic.py           # Basic functionality tests
├── test_server.py          # FastAPI server tests
├── conftest.py            # Shared fixtures (if needed)
├── unit/                  # Unit tests
├── integration/           # Integration tests
└── fixtures/              # Test data files
```

## Running Tests

### Basic Test Commands

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
pytest tests/test_server.py

# Run specific test
pytest tests/test_server.py::test_register_agent

# Run with verbose output
pytest -v

# Run tests in parallel
pytest -n auto
```

### Test Categories

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only  
pytest tests/integration/

# Fast tests (skip slow ones)
pytest -m "not slow"

# Run only failed tests from last run
pytest --lf
```

## Writing Tests

### Test Structure

Follow the Arrange-Act-Assert pattern:

```python
def test_register_agent_success():
    # Arrange
    agent_card = create_test_agent_card()
    client = TestClient(app)
    
    # Act
    response = client.post("/agents", json={"agent_card": agent_card})
    
    # Assert
    assert response.status_code == 200
    assert response.json()["success"] is True
```

### Fixtures

Use pytest fixtures for common test setup:

```python
import pytest
from fastapi.testclient import TestClient
from a2a_registry.server import create_app

@pytest.fixture
def app():
    """Create test application instance."""
    return create_app()

@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)

@pytest.fixture
def sample_agent_card():
    """Sample agent card for testing."""
    return {
        "name": "test-agent",
        "description": "A test agent",
        "url": "http://localhost:3000",
        "version": "0.420.0",
        "protocol_version": "0.3.0",
        "skills": [
            {
                "id": "test_skill",
                "description": "A test skill"
            }
        ]
    }

def test_register_agent(client, sample_agent_card):
    response = client.post("/agents", json={"agent_card": sample_agent_card})
    assert response.status_code == 200
```

### Parameterized Tests

Test multiple scenarios with parameterized tests:

```python
import pytest

@pytest.mark.parametrize("agent_name,expected_status", [
    ("valid-agent", 200),
    ("", 400),  # Empty name should fail
    ("a" * 256, 400),  # Too long name should fail
])
def test_register_agent_names(client, agent_name, expected_status):
    agent_card = {
        "name": agent_name,
        "description": "Test agent",
        "url": "http://localhost:3000",
        "version": "0.420.0",
        "protocol_version": "0.3.0",
        "skills": []
    }
    response = client.post("/agents", json={"agent_card": agent_card})
    assert response.status_code == expected_status
```

## Unit Tests

Unit tests focus on individual components in isolation.

### Testing Storage Layer

```python
import pytest
from a2a_registry.storage import RegistryStorage

@pytest.fixture
def storage():
    return RegistryStorage()

@pytest.mark.asyncio
async def test_register_agent(storage, sample_agent_card):
    # Test successful registration
    result = await storage.register_agent(sample_agent_card)
    assert result is True
    
    # Test agent can be retrieved
    retrieved = await storage.get_agent(sample_agent_card["name"])
    assert retrieved == sample_agent_card

@pytest.mark.asyncio
async def test_search_agents(storage, sample_agent_card):
    await storage.register_agent(sample_agent_card)
    
    # Search by name
    results = await storage.search_agents("test")
    assert len(results) == 1
    assert results[0]["name"] == sample_agent_card["name"]
    
    # Search by skill
    results = await storage.search_agents("test_skill")
    assert len(results) == 1
```

### Testing Business Logic

```python
def test_agent_card_validation():
    """Test agent card validation logic."""
    from a2a_registry.server import validate_agent_card
    
    # Valid card
    valid_card = {...}
    assert validate_agent_card(valid_card) is True
    
    # Missing required field
    invalid_card = valid_card.copy()
    del invalid_card["name"]
    assert validate_agent_card(invalid_card) is False
```

## Integration Tests

Integration tests verify that components work together correctly.

### API Integration Tests

```python
@pytest.mark.asyncio
async def test_full_agent_lifecycle(client):
    """Test complete agent registration/discovery/deletion cycle."""
    agent_card = create_test_agent_card()
    
    # 1. Register agent
    response = client.post("/agents", json={"agent_card": agent_card})
    assert response.status_code == 200
    agent_id = response.json()["agent_id"]
    
    # 2. Verify agent appears in listings
    response = client.get("/agents")
    assert response.status_code == 200
    agents = response.json()["agents"]
    assert any(agent["name"] == agent_id for agent in agents)
    
    # 3. Search for agent
    response = client.post("/agents/search", json={"query": "test"})
    assert response.status_code == 200
    assert len(response.json()["agents"]) > 0
    
    # 4. Get specific agent
    response = client.get(f"/agents/{agent_id}")
    assert response.status_code == 200
    assert response.json()["agent_card"]["name"] == agent_id
    
    # 5. Delete agent
    response = client.delete(f"/agents/{agent_id}")
    assert response.status_code == 200
    
    # 6. Verify agent is gone
    response = client.get(f"/agents/{agent_id}")
    assert response.status_code == 404
```

### gRPC Integration Tests

```python
import grpc
import pytest
from a2a_registry.proto.generated import registry_pb2, registry_pb2_grpc

@pytest.fixture
def grpc_channel():
    """Create gRPC channel for testing."""
    # This would need a running gRPC server
    channel = grpc.insecure_channel('localhost:50051')
    yield channel
    channel.close()

@pytest.fixture
def grpc_stub(grpc_channel):
    """Create gRPC stub."""
    return registry_pb2_grpc.A2ARegistryServiceStub(grpc_channel)

@pytest.mark.integration
def test_grpc_agent_registration(grpc_stub):
    """Test agent registration via gRPC."""
    # Create agent card
    agent_card = registry_pb2.AgentCard(
        name="grpc-test-agent",
        description="gRPC test agent",
        url="http://localhost:3000",
        version="0.420.0",
        protocol_version="0.3.0"
    )
    
    registry_card = registry_pb2.RegistryAgentCard(agent_card=agent_card)
    request = registry_pb2.StoreAgentCardRequest(
        registry_agent_card=registry_card,
        upsert=True
    )
    
    # Store agent
    response = grpc_stub.StoreAgentCard(request)
    assert response.success is True
    
    # Retrieve agent
    get_request = registry_pb2.GetAgentCardRequest(agent_id="grpc-test-agent")
    get_response = grpc_stub.GetAgentCard(get_request)
    assert get_response.found is True
    assert get_response.registry_agent_card.agent_card.name == "grpc-test-agent"
```

## Error Testing

Test error conditions and edge cases:

```python
def test_register_agent_invalid_data(client):
    """Test error handling for invalid agent data."""
    # Missing required fields
    invalid_data = {"agent_card": {"name": "test"}}  # Missing required fields
    response = client.post("/agents", json=invalid_data)
    assert response.status_code == 400
    
    # Invalid JSON
    response = client.post("/agents", data="invalid json", 
                          headers={"Content-Type": "application/json"})
    assert response.status_code == 422

def test_get_nonexistent_agent(client):
    """Test retrieving non-existent agent."""
    response = client.get("/agents/nonexistent")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_delete_nonexistent_agent(client):
    """Test deleting non-existent agent."""
    response = client.delete("/agents/nonexistent")
    assert response.status_code == 404
```

## Performance Tests

Test performance characteristics:

```python
import time
import pytest

@pytest.mark.slow
def test_concurrent_registrations(client):
    """Test handling of concurrent agent registrations."""
    import concurrent.futures
    
    def register_agent(agent_id):
        agent_card = create_test_agent_card(name=f"agent-{agent_id}")
        response = client.post("/agents", json={"agent_card": agent_card})
        return response.status_code == 200
    
    # Register 100 agents concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(register_agent, i) for i in range(100)]
        results = [future.result() for future in futures]
    
    # All registrations should succeed
    assert all(results)
    
    # Verify all agents are registered
    response = client.get("/agents")
    assert response.json()["count"] == 100

@pytest.mark.slow
def test_large_search_performance(client):
    """Test search performance with many agents."""
    # Register 1000 agents
    for i in range(1000):
        agent_card = create_test_agent_card(name=f"perf-agent-{i}")
        client.post("/agents", json={"agent_card": agent_card})
    
    # Time search operation
    start_time = time.time()
    response = client.post("/agents/search", json={"query": "perf"})
    end_time = time.time()
    
    assert response.status_code == 200
    assert response.json()["count"] == 1000
    assert end_time - start_time < 1.0  # Should complete within 1 second
```

## Test Data Management

### Using Test Fixtures

Create reusable test data:

```python
# tests/fixtures/agent_cards.py
def minimal_agent_card():
    return {
        "name": "minimal-agent",
        "description": "Minimal test agent",
        "url": "http://localhost:3000",
        "version": "0.420.0",
        "protocol_version": "0.3.0",
        "skills": []
    }

def weather_agent_card():
    return {
        "name": "weather-agent",
        "description": "Weather information agent",
        "url": "http://weather.example.com",
        "version": "0.420.0",
        "protocol_version": "0.3.0",
        "skills": [
            {"id": "get_weather", "description": "Get current weather"},
            {"id": "get_forecast", "description": "Get weather forecast"}
        ]
    }
```

### Database Test Helpers

For future database implementations:

```python
@pytest.fixture
def clean_database():
    """Ensure clean database state for each test."""
    # Setup: Clear database
    clear_test_database()
    yield
    # Teardown: Clear database
    clear_test_database()

def clear_test_database():
    """Clear all test data from database."""
    # Implementation depends on storage backend
    pass
```

## Continuous Integration

Tests run automatically in CI. See `.github/workflows/ci.yml`:

```yaml
- name: Run tests
  run: |
    pytest --cov=src/a2a_registry --cov-report=xml --cov-report=term
    
- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## Test Configuration

Configure pytest in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short --strict-markers"
asyncio_mode = "auto"
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
]
```

## Coverage Goals

Maintain high test coverage:

- **Minimum**: 80% overall coverage
- **Target**: 90%+ coverage for core modules
- **Critical paths**: 100% coverage for registration/discovery logic

## Best Practices

1. **Test Naming**: Use descriptive test names that explain what is being tested
2. **Independence**: Tests should not depend on each other
3. **Fast Feedback**: Unit tests should run quickly (< 100ms each)
4. **Clear Assertions**: Use specific assertions with meaningful error messages
5. **Test Data**: Use factories or fixtures for test data creation
6. **Error Cases**: Test both success and failure scenarios
7. **Documentation**: Document complex test scenarios

## Debugging Tests

### Debug Failed Tests

```bash
# Run with debugging info
pytest -vvv --tb=long

# Drop into debugger on failure
pytest --pdb

# Run only failed tests
pytest --lf -vvv
```

### Test Isolation

```bash
# Run single test in isolation
pytest tests/test_server.py::test_specific_function -s -vvv

# Run with fresh imports
pytest --forked
```

This comprehensive testing guide ensures reliable, maintainable code with good test coverage.