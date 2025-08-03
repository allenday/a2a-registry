# Debugging Guide

Comprehensive debugging techniques and tools for A2A Registry development and troubleshooting.

## Development Environment Setup

### Debug Mode Configuration

```bash
# Start server in debug mode
a2a-registry serve --log-level DEBUG --reload

# Enable debug in code
import logging
logging.basicConfig(level=logging.DEBUG)

# FastAPI debug mode
export FASTAPI_DEBUG=true
```

### IDE Debugging Setup

#### VS Code Configuration

Create `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug A2A Registry Server",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/.venv/bin/a2a-registry",
            "args": ["serve", "--host", "127.0.0.1", "--port", "8000", "--log-level", "DEBUG"],
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}",
            "env": {
                "PYTHONPATH": "${workspaceFolder}/src"
            }
        },
        {
            "name": "Debug Tests",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["tests/", "-v", "-s"],
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}"
        }
    ]
}
```

#### PyCharm Configuration

1. Go to `Run > Edit Configurations`
2. Add new Python configuration
3. Set script path to `src/a2a_registry/cli.py`
4. Set parameters to `serve --log-level DEBUG`
5. Set working directory to project root

### Environment Variables for Debugging

```bash
# .env file for development
DEBUG=true
LOG_LEVEL=DEBUG
PYTHONPATH=src
FASTAPI_DEBUG=true
UVICORN_LOG_LEVEL=debug
```

## Debugging Techniques

### 1. Logging-Based Debugging

#### Enhanced Logging

```python
import logging
import inspect
from functools import wraps

def debug_trace(func):
    """Decorator to trace function calls"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        
        # Log function entry
        logger.debug(f"Entering {func.__name__} with args={args[1:]} kwargs={kwargs}")
        
        try:
            result = await func(*args, **kwargs)
            logger.debug(f"Exiting {func.__name__} with result type: {type(result).__name__}")
            return result
        except Exception as e:
            logger.error(f"Exception in {func.__name__}: {e}", exc_info=True)
            raise
    
    return wrapper

# Usage
class InMemoryStorage:
    @debug_trace
    async def register_agent(self, agent_id: str, agent_card: dict):
        # Implementation
        pass
```

#### Request/Response Logging

```python
import json
from starlette.middleware.base import BaseHTTPMiddleware

class DebugMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Log request details
        logger.debug(f"Request: {request.method} {request.url}")
        logger.debug(f"Headers: {dict(request.headers)}")
        
        # Capture request body for POST/PUT
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
            if body:
                try:
                    json_body = json.loads(body)
                    logger.debug(f"Request body: {json.dumps(json_body, indent=2)}")
                except:
                    logger.debug(f"Request body (raw): {body}")
            
            # Recreate request with body
            request = Request(request.scope, receive=lambda: {"type": "http.request", "body": body})
        
        # Process request
        response = await call_next(request)
        
        # Log response
        logger.debug(f"Response: {response.status_code}")
        
        return response

# Add to app
app.add_middleware(DebugMiddleware)
```

### 2. Interactive Debugging

#### PDB Integration

```python
import pdb
from a2a_registry.storage import InMemoryStorage

async def debug_storage_issue():
    storage = InMemoryStorage()
    
    # Set breakpoint
    pdb.set_trace()
    
    # Debug agent registration
    agent_card = {...}
    await storage.register_agent("test-agent", agent_card)
    
    # Check storage state
    agents = await storage.list_agents()
    print(f"Agents in storage: {len(agents)}")

# Run in development
if __name__ == "__main__":
    import asyncio
    asyncio.run(debug_storage_issue())
```

#### IPython/Jupyter Integration

```python
# Install IPython for better debugging
# pip install ipython

# Use IPython debugger
from IPython import embed

async def debug_with_ipython():
    storage = InMemoryStorage()
    
    # Drop into IPython shell
    embed()
    
    # Continue execution
    return await storage.list_agents()
```

### 3. Test-Driven Debugging

#### Debug-Specific Tests

```python
import pytest
from fastapi.testclient import TestClient
from a2a_registry.server import create_app

@pytest.fixture
def debug_client():
    """Test client with debug logging enabled"""
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    app = create_app()
    return TestClient(app)

def test_debug_agent_registration(debug_client):
    """Debug agent registration issues"""
    
    # Test valid registration
    valid_card = {
        "agent_card": {
            "name": "debug-agent",
            "description": "Agent for debugging",
            "url": "http://localhost:3000",
            "version": "0.420.0",
            "protocol_version": "0.3.0",
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
    
    response = debug_client.post("/agents", json=valid_card)
    print(f"Registration response: {response.status_code}")
    print(f"Response body: {response.json()}")
    
    assert response.status_code == 201

def test_debug_search_functionality(debug_client):
    """Debug search issues"""
    
    # First register some test agents
    for i in range(3):
        agent_card = {
            "agent_card": {
                "name": f"search-test-{i}",
                "description": f"Test agent {i} for searching",
                "url": f"http://localhost:300{i}",
                "version": "0.420.0",
                "protocol_version": "0.3.0",
                "skills": [
                    {"id": f"skill_{i}", "description": f"Skill number {i}"}
                ]
            }
        }
        debug_client.post("/agents", json=agent_card)
    
    # Test search
    search_response = debug_client.post("/agents/search", json={
        "query": "search"
    })
    
    print(f"Search response: {search_response.status_code}")
    print(f"Search results: {search_response.json()}")
    
    assert search_response.status_code == 200
```

## Performance Debugging

### Memory Profiling

```python
import tracemalloc
import psutil
import gc
from functools import wraps

def memory_profile(func):
    """Decorator to profile memory usage"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Start tracing
        tracemalloc.start()
        
        # Get initial memory
        process = psutil.Process()
        mem_before = process.memory_info().rss
        
        try:
            result = await func(*args, **kwargs)
            
            # Get final memory
            mem_after = process.memory_info().rss
            mem_diff = mem_after - mem_before
            
            # Get top memory allocations
            current, peak = tracemalloc.get_traced_memory()
            top_stats = tracemalloc.take_snapshot().statistics('lineno')
            
            print(f"Memory profile for {func.__name__}:")
            print(f"  RSS memory change: {mem_diff / 1024 / 1024:.2f} MB")
            print(f"  Current traced: {current / 1024 / 1024:.2f} MB")
            print(f"  Peak traced: {peak / 1024 / 1024:.2f} MB")
            
            # Show top allocations
            print("  Top 5 allocations:")
            for stat in top_stats[:5]:
                print(f"    {stat}")
            
            return result
            
        finally:
            tracemalloc.stop()
    
    return wrapper

# Usage
@memory_profile
async def test_bulk_registration():
    """Test memory usage during bulk registration"""
    storage = InMemoryStorage()
    
    for i in range(1000):
        await storage.register_agent(f"agent-{i}", {...})
    
    return await storage.list_agents()
```

### Performance Profiling

```python
import cProfile
import pstats
import io
from functools import wraps

def profile_performance(func):
    """Decorator to profile function performance"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            pr.disable()
            
            # Generate stats
            s = io.StringIO()
            ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
            ps.print_stats(20)  # Top 20 functions
            
            print(f"Performance profile for {func.__name__}:")
            print(s.getvalue())
    
    return wrapper

# Usage
@profile_performance
async def benchmark_search():
    """Benchmark search performance"""
    storage = InMemoryStorage()
    
    # Add test data
    for i in range(100):
        await storage.register_agent(f"agent-{i}", {...})
    
    # Perform searches
    for i in range(10):
        await storage.search_agents(query=f"agent-{i}")
```

## Network Debugging

### HTTP Client Debugging

```python
import httpx
import logging

# Enable httpx debug logging
logging.getLogger("httpx").setLevel(logging.DEBUG)

class DebugRegistryClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def register_agent_debug(self, agent_card: dict):
        """Register agent with detailed debugging"""
        print(f"Registering agent: {agent_card['name']}")
        print(f"URL: {self.base_url}/agents")
        print(f"Payload: {json.dumps(agent_card, indent=2)}")
        
        try:
            response = await self.client.post(
                f"{self.base_url}/agents",
                json={"agent_card": agent_card}
            )
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print(f"Response body: {response.text}")
            
            return response
            
        except Exception as e:
            print(f"Request failed: {e}")
            raise

# Usage
async def debug_client_connection():
    client = DebugRegistryClient("http://localhost:8000")
    await client.register_agent_debug({...})
```

### Server-Side Request Debugging

```python
from starlette.middleware.base import BaseHTTPMiddleware
import time

class RequestDebugMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log detailed request info
        print(f"\n=== Request Debug ===")
        print(f"Method: {request.method}")
        print(f"URL: {request.url}")
        print(f"Path: {request.url.path}")
        print(f"Query: {request.url.query}")
        print(f"Headers: {dict(request.headers)}")
        print(f"Client: {request.client}")
        
        # Process request
        response = await call_next(request)
        
        # Log response info
        duration = time.time() - start_time
        print(f"Status: {response.status_code}")
        print(f"Duration: {duration:.3f}s")
        print(f"Response headers: {dict(response.headers)}")
        print("========================\n")
        
        return response
```

## Database Debugging (Future)

### SQL Query Debugging

```python
import asyncpg
import logging

class DebugConnection:
    def __init__(self, connection):
        self.connection = connection
    
    async def execute(self, query: str, *args):
        print(f"Executing SQL: {query}")
        print(f"Parameters: {args}")
        
        start_time = time.time()
        result = await self.connection.execute(query, *args)
        duration = time.time() - start_time
        
        print(f"Query completed in {duration:.3f}s")
        print(f"Result: {result}")
        
        return result
    
    async def fetch(self, query: str, *args):
        print(f"Fetching SQL: {query}")
        print(f"Parameters: {args}")
        
        start_time = time.time()
        result = await self.connection.fetch(query, *args)
        duration = time.time() - start_time
        
        print(f"Query completed in {duration:.3f}s")
        print(f"Rows returned: {len(result)}")
        
        return result

# Future database storage debugging
class DatabaseStorage:
    async def get_debug_connection(self):
        conn = await self.pool.acquire()
        return DebugConnection(conn)
```

## Error Analysis

### Exception Analysis

```python
import traceback
import sys
from typing import Any, Dict

class ErrorAnalyzer:
    @staticmethod
    def analyze_exception(exc: Exception) -> Dict[str, Any]:
        """Analyze exception for debugging insights"""
        
        exc_type = type(exc).__name__
        exc_message = str(exc)
        exc_traceback = traceback.format_exc()
        
        # Extract relevant information
        analysis = {
            "exception_type": exc_type,
            "message": exc_message,
            "traceback": exc_traceback,
            "locals": {},
            "suggestions": []
        }
        
        # Add type-specific analysis
        if isinstance(exc, ValidationError):
            analysis["suggestions"].append("Check agent card format against FastA2A schema")
            analysis["validation_errors"] = getattr(exc, 'errors', None)
        
        elif isinstance(exc, KeyError):
            analysis["suggestions"].append(f"Missing required field: {exc_message}")
            analysis["suggestions"].append("Verify all required fields are present")
        
        elif isinstance(exc, asyncio.TimeoutError):
            analysis["suggestions"].append("Request timed out - check network connectivity")
            analysis["suggestions"].append("Consider increasing timeout values")
        
        elif isinstance(exc, ConnectionError):
            analysis["suggestions"].append("Cannot connect to registry server")
            analysis["suggestions"].append("Verify server is running and accessible")
        
        # Capture local variables from traceback
        tb = sys.exc_info()[2]
        if tb:
            frame = tb.tb_frame
            while frame:
                analysis["locals"][frame.f_code.co_filename] = {
                    "function": frame.f_code.co_name,
                    "line": frame.f_lineno,
                    "locals": {k: str(v) for k, v in frame.f_locals.items() 
                             if not k.startswith('_')}
                }
                frame = frame.f_back
        
        return analysis

# Usage in exception handlers
async def safe_register_agent(agent_card: dict):
    try:
        return await storage.register_agent("test", agent_card)
    except Exception as e:
        analysis = ErrorAnalyzer.analyze_exception(e)
        print("Error Analysis:")
        print(json.dumps(analysis, indent=2, default=str))
        raise
```

### Custom Exception Classes

```python
class RegistryError(Exception):
    """Base exception for registry errors"""
    pass

class AgentValidationError(RegistryError):
    """Agent card validation failed"""
    def __init__(self, message: str, validation_errors: list = None):
        super().__init__(message)
        self.validation_errors = validation_errors or []

class AgentNotFoundError(RegistryError):
    """Agent not found in registry"""
    def __init__(self, agent_id: str):
        super().__init__(f"Agent not found: {agent_id}")
        self.agent_id = agent_id

class StorageError(RegistryError):
    """Storage operation failed"""
    pass

# Enhanced error handling with debugging info
class DebugRegistryError(RegistryError):
    def __init__(self, message: str, context: dict = None):
        super().__init__(message)
        self.context = context or {}
        self.timestamp = datetime.utcnow()
        
    def to_dict(self):
        return {
            "error": self.__class__.__name__,
            "message": str(self),
            "context": self.context,
            "timestamp": self.timestamp.isoformat()
        }
```

## Debug Utilities

### State Inspection

```python
class RegistryDebugger:
    def __init__(self, storage):
        self.storage = storage
    
    async def dump_state(self) -> dict:
        """Dump complete registry state for debugging"""
        agents = await self.storage.list_agents()
        
        state = {
            "agent_count": len(agents),
            "agents": agents,
            "memory_usage": psutil.Process().memory_info().rss,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add storage-specific debug info
        if hasattr(self.storage, '_agents'):
            state["internal_agent_count"] = len(self.storage._agents)
        
        if hasattr(self.storage, '_skills_index'):
            state["skills_index"] = dict(self.storage._skills_index)
        
        return state
    
    async def validate_consistency(self) -> dict:
        """Check for data consistency issues"""
        issues = []
        agents = await self.storage.list_agents()
        
        # Check for duplicate names
        names = [agent.get('name') for agent in agents]
        duplicates = [name for name in set(names) if names.count(name) > 1]
        if duplicates:
            issues.append(f"Duplicate agent names: {duplicates}")
        
        # Check for invalid URLs
        for agent in agents:
            url = agent.get('url', '')
            if not url.startswith(('http://', 'https://', 'grpc://')):
                issues.append(f"Invalid URL for agent {agent.get('name')}: {url}")
        
        # Check for missing required fields
        required_fields = ['name', 'description', 'url', 'version', 'protocol_version']
        for agent in agents:
            missing = [field for field in required_fields if not agent.get(field)]
            if missing:
                issues.append(f"Agent {agent.get('name')} missing fields: {missing}")
        
        return {
            "issues": issues,
            "is_consistent": len(issues) == 0
        }

# Debug endpoint
@app.get("/debug/state")
async def get_debug_state():
    """Debug endpoint to inspect registry state"""
    debugger = RegistryDebugger(storage)
    
    state = await debugger.dump_state()
    consistency = await debugger.validate_consistency()
    
    return {
        "state": state,
        "consistency": consistency
    }
```

### Test Data Generation

```python
import random
from faker import Faker

class TestDataGenerator:
    def __init__(self):
        self.fake = Faker()
    
    def generate_agent_card(self, agent_id: str = None) -> dict:
        """Generate realistic test agent card"""
        agent_id = agent_id or f"test-{random.randint(1000, 9999)}"
        
        return {
            "name": agent_id,
            "description": self.fake.text(max_nb_chars=200),
            "url": f"http://{self.fake.domain_name()}:{random.randint(3000, 9000)}",
            "version": f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
            "protocol_version": "0.3.0",
            "capabilities": {
                "streaming": random.choice([True, False]),
                "push_notifications": random.choice([True, False]),
                "state_transition_history": random.choice([True, False])
            },
            "default_input_modes": random.sample(["text", "audio", "image"], k=random.randint(1, 3)),
            "default_output_modes": random.sample(["text", "audio", "image"], k=random.randint(1, 3)),
            "skills": [
                {
                    "id": self.fake.word(),
                    "description": self.fake.sentence()
                }
                for _ in range(random.randint(1, 5))
            ],
            "preferred_transport": random.choice(["http", "grpc", "websocket"])
        }
    
    def generate_test_data(self, count: int = 10) -> list:
        """Generate multiple test agent cards"""
        return [self.generate_agent_card() for _ in range(count)]

# Usage in tests
def setup_test_data():
    generator = TestDataGenerator()
    return generator.generate_test_data(50)
```

## Debugging Best Practices

1. **Use structured logging** with correlation IDs
2. **Implement health checks** at multiple levels
3. **Add debug endpoints** for development environments
4. **Use type hints** to catch issues early
5. **Write comprehensive tests** with debug information
6. **Profile performance** regularly
7. **Monitor memory usage** and detect leaks
8. **Log request/response** details in debug mode
9. **Use proper exception handling** with context
10. **Document debugging procedures** for common issues

## Production Debugging

### Remote Debugging

```bash
# Enable remote debugging (development only)
python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m a2a_registry.cli serve
```

### Log Analysis Scripts

```bash
#!/bin/bash
# debug_logs.sh - Analyze production logs

LOG_FILE="/var/log/a2a-registry/app.log"

echo "=== Error Summary ==="
grep "ERROR" $LOG_FILE | tail -10

echo "=== Slow Requests ==="
grep "duration.*[1-9][0-9]\." $LOG_FILE | tail -5

echo "=== Memory Warnings ==="
grep -i "memory" $LOG_FILE | tail -5

echo "=== Recent Activity ==="
tail -20 $LOG_FILE
```

## Next Steps

- Review [Performance Tuning](../troubleshooting/performance.md) for optimization
- Check [Common Issues](../troubleshooting/common-issues.md) for solutions
- Explore [Testing Strategy](testing.md) for comprehensive testing
- Learn about [Development Setup](setup.md) for environment configuration