# Common Issues and Troubleshooting

This guide covers the most common issues encountered when using A2A Registry and their solutions.

## Installation Issues

### Issue: `pip install a2a-registry` fails

**Symptoms:**
```
ERROR: Could not find a version that satisfies the requirement a2a-registry
```

**Solutions:**

1. **Check Python version**:
   ```bash
   python --version  # Should be 3.9+
   ```

2. **Upgrade pip**:
   ```bash
   pip install --upgrade pip
   ```

3. **Install from source**:
   ```bash
   git clone https://github.com/allenday/a2a-registry.git
   cd a2a-registry
   pip install -e .
   ```

### Issue: Import errors after installation

**Symptoms:**
```python
ImportError: No module named 'a2a_registry'
```

**Solutions:**

1. **Verify installation**:
   ```bash
   pip list | grep a2a-registry
   ```

2. **Check virtual environment**:
   ```bash
   which python
   which pip
   ```

3. **Reinstall in clean environment**:
   ```bash
   python -m venv fresh_env
   source fresh_env/bin/activate  # On Windows: fresh_env\Scripts\activate
   pip install a2a-registry
   ```

## Server Startup Issues

### Issue: Server won't start

**Symptoms:**
```
Error: Could not start server on port 8000
```

**Common Causes & Solutions:**

1. **Port already in use**:
   ```bash
   # Check what's using port 8000
   lsof -i :8000  # On macOS/Linux
   netstat -ano | findstr :8000  # On Windows
   
   # Use different port
   a2a-registry serve --port 8001
   ```

2. **Permission denied**:
   ```bash
   # Use unprivileged port (>1024)
   a2a-registry serve --port 8080
   
   # Or run with sudo (not recommended)
   sudo a2a-registry serve --port 80
   ```

3. **Missing dependencies**:
   ```bash
   pip install fastapi uvicorn
   ```

### Issue: Server starts but can't connect

**Symptoms:**
```
Connection refused when accessing http://localhost:8000
```

**Solutions:**

1. **Check bind address**:
   ```bash
   # Server only listening on localhost
   a2a-registry serve --host 0.0.0.0  # Listen on all interfaces
   ```

2. **Verify server is running**:
   ```bash
   curl http://localhost:8000/health
   ```

3. **Check firewall settings**:
   ```bash
   # On Linux
   sudo ufw status
   sudo ufw allow 8000
   
   # On macOS
   # Check System Preferences > Security & Privacy > Firewall
   ```

## Registration Issues

### Issue: Agent registration fails

**Symptoms:**
```json
{
  "error": "Validation error",
  "details": "Invalid agent card format"
}
```

**Common Validation Errors:**

1. **Missing required fields**:
   ```python
   # ❌ Incomplete agent card
   agent_card = {
       "name": "my-agent"
       # Missing required fields
   }
   
   # ✅ Complete agent card
   agent_card = {
       "name": "my-agent",
       "description": "My test agent",
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
   ```

2. **Invalid URL format**:
   ```python
   # ❌ Invalid URLs
   "url": "localhost:3000"        # Missing protocol
   "url": "http:/localhost:3000"  # Typo in protocol
   
   # ✅ Valid URLs
   "url": "http://localhost:3000"
   "url": "https://api.example.com"
   "url": "grpc://service.example.com:50051"
   ```

3. **Invalid skill format**:
   ```python
   # ❌ Invalid skill format
   "skills": ["skill1", "skill2"]  # Should be objects
   
   # ✅ Valid skill format
   "skills": [
       {"id": "skill1", "description": "First skill"},
       {"id": "skill2", "description": "Second skill"}
   ]
   ```

### Issue: Duplicate agent registration

**Symptoms:**
```json
{
  "error": "Agent already exists",
  "agent_id": "existing-agent"
}
```

**Solutions:**

1. **Check existing registrations**:
   ```bash
   curl http://localhost:8000/agents
   ```

2. **Unregister old agent**:
   ```bash
   curl -X DELETE http://localhost:8000/agents/my-agent
   ```

3. **Use unique agent names**:
   ```python
   import uuid
   
   agent_card = {
       "name": f"my-agent-{uuid.uuid4().hex[:8]}",
       # ... rest of card
   }
   ```

## Discovery Issues

### Issue: Can't find registered agents

**Symptoms:**
- Agents register successfully but don't appear in search results
- Empty responses from list/search endpoints

**Solutions:**

1. **Verify agent is registered**:
   ```bash
   # List all agents
   curl http://localhost:8000/agents
   
   # Get specific agent
   curl http://localhost:8000/agents/my-agent-id
   ```

2. **Check search criteria**:
   ```python
   # ❌ Too restrictive search
   agents = await client.search_agents(
       skills=["exact_skill_name"],
       query="very specific query"
   )
   
   # ✅ Broader search
   agents = await client.search_agents(query="general")
   ```

3. **Case sensitivity issues**:
   ```python
   # Search is case-insensitive for descriptions but case-sensitive for skill IDs
   
   # ❌ Wrong case for skill ID
   agents = await client.search_agents(skills=["Translate"])
   
   # ✅ Correct case
   agents = await client.search_agents(skills=["translate"])
   ```

### Issue: Search returns unexpected results

**Solutions:**

1. **Understand search behavior**:
   - Query searches in name and description (case-insensitive)
   - Skills must match exactly (case-sensitive)
   - Multiple criteria are AND-ed together

2. **Debug search criteria**:
   ```python
   # Test each criterion separately
   by_query = await client.search_agents(query="weather")
   by_skills = await client.search_agents(skills=["forecast"])
   combined = await client.search_agents(query="weather", skills=["forecast"])
   
   print(f"By query: {len(by_query)}")
   print(f"By skills: {len(by_skills)}")
   print(f"Combined: {len(combined)}")
   ```

## Network and Connectivity Issues

### Issue: Connection timeouts

**Symptoms:**
```
TimeoutError: Request timed out after 30 seconds
```

**Solutions:**

1. **Increase timeout**:
   ```python
   client = A2ARegistryClient(
       "http://localhost:8000",
       timeout=60.0  # Increase to 60 seconds
   )
   ```

2. **Check network connectivity**:
   ```bash
   ping localhost
   telnet localhost 8000
   ```

3. **Use retry logic**:
   ```python
   import asyncio
   
   async def register_with_retry(client, agent_card, max_retries=3):
       for attempt in range(max_retries):
           try:
               return await client.register_agent(agent_card)
           except TimeoutError:
               if attempt == max_retries - 1:
                   raise
               await asyncio.sleep(2 ** attempt)  # Exponential backoff
   ```

### Issue: DNS resolution problems

**Symptoms:**
```
DNSError: Could not resolve hostname
```

**Solutions:**

1. **Use IP addresses**:
   ```python
   # Instead of hostname
   client = A2ARegistryClient("http://127.0.0.1:8000")
   ```

2. **Check DNS configuration**:
   ```bash
   nslookup localhost
   dig localhost
   ```

3. **Add to hosts file** (if using custom hostnames):
   ```bash
   # /etc/hosts (Linux/macOS) or C:\Windows\System32\drivers\etc\hosts (Windows)
   127.0.0.1 my-registry.local
   ```

## Performance Issues

### Issue: Slow response times

**Symptoms:**
- Registration takes several seconds
- Search requests are slow
- High memory usage

**Solutions:**

1. **Monitor server resources**:
   ```bash
   # Check CPU and memory usage
   top
   htop
   
   # Check specific process
   ps aux | grep a2a-registry
   ```

2. **Optimize agent card size**:
   ```python
   # ❌ Excessive data
   agent_card = {
       "description": "Very long description..." * 1000,
       "skills": [{"id": f"skill{i}", "description": "..."} for i in range(1000)]
   }
   
   # ✅ Reasonable size
   agent_card = {
       "description": "Concise description",
       "skills": [
           {"id": "main_skill", "description": "Primary functionality"}
       ]
   }
   ```

3. **Limit search results**:
   ```python
   # Future: Add pagination
   # For now, use specific search criteria
   agents = await client.search_agents(
       query="specific term",
       skills=["exact_skill"]
   )
   ```

### Issue: Memory leaks

**Symptoms:**
- Server memory usage keeps growing
- Eventually crashes with OutOfMemory

**Solutions:**

1. **Restart server periodically**:
   ```bash
   # Simple cron job (production should use proper process management)
   0 2 * * * pkill -f a2a-registry && sleep 5 && a2a-registry serve &
   ```

2. **Monitor registrations**:
   ```python
   # Check registry size
   response = await client.health_check()
   print(f"Registered agents: {response.get('agents_count', 'unknown')}")
   ```

3. **Clean up old agents**:
   ```python
   # Periodic cleanup of inactive agents
   async def cleanup_inactive_agents():
       agents = await client.list_agents()
       for agent in agents:
           if not await ping_agent(agent['url']):
               await client.unregister_agent(agent['name'])
   ```

## Development and Testing Issues

### Issue: Tests fail with "connection refused"

**Solutions:**

1. **Start test registry**:
   ```python
   import pytest
   import asyncio
   from a2a_registry.server import create_app
   
   @pytest.fixture
   async def test_registry():
       app = create_app()
       # Start test server on different port
       # Use TestClient for testing
   ```

2. **Use test client**:
   ```python
   from fastapi.testclient import TestClient
   from a2a_registry.server import create_app
   
   app = create_app()
   client = TestClient(app)
   
   # Test without running actual server
   response = client.post("/agents", json={"agent_card": {...}})
   assert response.status_code == 201
   ```

### Issue: Import errors in development

**Solutions:**

1. **Install in development mode**:
   ```bash
   pip install -e .
   ```

2. **Add to Python path**:
   ```python
   import sys
   import os
   sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
   
   from a2a_registry import A2ARegistryClient
   ```

## Configuration Issues

### Issue: Environment variables not loaded

**Solutions:**

1. **Check environment variable names**:
   ```bash
   export A2A_REGISTRY_URL=http://localhost:8000
   export A2A_REGISTRY_TIMEOUT=30
   ```

2. **Use .env file**:
   ```bash
   # .env
   A2A_REGISTRY_URL=http://localhost:8000
   A2A_REGISTRY_TIMEOUT=30
   ```

3. **Verify loading**:
   ```python
   import os
   print(f"Registry URL: {os.getenv('A2A_REGISTRY_URL')}")
   ```

## Logging and Debugging

### Enable Debug Logging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Or for specific logger
logger = logging.getLogger("a2a_registry")
logger.setLevel(logging.DEBUG)
```

### Server Debug Mode

```bash
# Start server with debug logging
a2a-registry serve --log-level DEBUG

# Or with reload for development
a2a-registry serve --reload --log-level DEBUG
```

### Client Debug Information

```python
import aiohttp
import logging

# Enable aiohttp debug logging
logging.getLogger("aiohttp").setLevel(logging.DEBUG)

# Custom debug wrapper
class DebugRegistryClient(A2ARegistryClient):
    async def _make_request(self, method, url, **kwargs):
        print(f"Making {method} request to {url}")
        print(f"Data: {kwargs.get('json')}")
        
        response = await super()._make_request(method, url, **kwargs)
        
        print(f"Response status: {response.status}")
        print(f"Response data: {await response.text()}")
        
        return response
```

## Getting Help

### Check Server Health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "agents_count": 5
}
```

### Collect Debug Information

```bash
# System info
python --version
pip list | grep -E "(a2a|fastapi|uvicorn)"

# Network info
netstat -an | grep 8000
curl -v http://localhost:8000/health

# Logs
journalctl -u a2a-registry  # If running as service
```

### Community Support

- [GitHub Issues](https://github.com/allenday/a2a-registry/issues) - Bug reports and feature requests
- [GitHub Discussions](https://github.com/allenday/a2a-registry/discussions) - Questions and community support
- [Documentation](https://allenday.github.io/a2a-registry/) - Complete documentation

### Reporting Bugs

When reporting issues, please include:

1. **Environment information**:
   - Python version
   - Operating system
   - Package versions

2. **Steps to reproduce**:
   - Minimal code example
   - Configuration used
   - Expected vs actual behavior

3. **Logs and error messages**:
   - Full error tracebacks
   - Server logs
   - Network request/response details

Example bug report template:

```markdown
**Environment:**
- Python: 3.9.7
- OS: Ubuntu 20.04
- a2a-registry: 0.1.0

**Issue:**
Agent registration fails with validation error

**Steps to reproduce:**
1. Start registry: `a2a-registry serve`
2. Register agent with code:
   ```python
   # Code here
   ```
3. See error: `Validation error: ...`

**Expected behavior:**
Agent should register successfully

**Actual behavior:**
Gets validation error

**Logs:**
```
Full error traceback here
```
```

## Next Steps

- Review [Performance Tuning](performance.md) for optimization tips
- Check [Logging and Monitoring](logging.md) for observability setup
- Explore [Developer Guide](../developer/setup.md) for contribution guidelines