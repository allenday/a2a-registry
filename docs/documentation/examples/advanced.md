# Advanced Examples

Complex scenarios and advanced usage patterns for A2A Registry.

## Multi-Protocol Agent Discovery

The A2A Registry supports both JSON-RPC 2.0 (primary) and REST (secondary) protocols per the **A2A Protocol v0.3.0** specification. Advanced clients should prefer JSON-RPC for full A2A compliance.

### Scenario: Protocol-Agnostic Service Discovery

Build a client that can discover and connect to agents regardless of their transport protocol:

```python
from a2a_registry import A2ARegistryClient
import asyncio
import httpx
import grpc

class UniversalAgentClient:
    def __init__(self, registry_url: str):
        self.registry = A2ARegistryClient(registry_url)
        self.protocol_handlers = {
            'JSONRPC': self._handle_jsonrpc_agent,  # Primary A2A transport
            'HTTP': self._handle_http_agent,
            'GRPC': self._handle_grpc_agent,
            'WEBSOCKET': self._handle_websocket_agent,
            # Legacy aliases
            'http': self._handle_http_agent,
            'grpc': self._handle_grpc_agent,
            'websocket': self._handle_websocket_agent
        }
    
    async def discover_and_invoke(self, skill: str, **kwargs):
        """Discover agents with a skill and invoke the first available"""
        
        # Find agents with the required skill
        agents = await self.registry.search_agents(skills=[skill])
        
        if not agents:
            raise ValueError(f"No agents found with skill: {skill}")
        
        # Try each agent until one succeeds
        for agent in agents:
            try:
                return await self.invoke_agent(agent, skill, **kwargs)
            except Exception as e:
                print(f"Failed to invoke {agent['name']}: {e}")
                continue
        
        raise RuntimeError(f"All agents failed for skill: {skill}")
    
    async def invoke_agent(self, agent: dict, skill: str, **kwargs):
        """Invoke a specific agent using appropriate protocol"""
        transport = agent.get('preferred_transport', 'JSONRPC')  # Default per A2A spec
        handler = self.protocol_handlers.get(transport)
        
        if not handler:
            raise ValueError(f"Unsupported transport: {transport}")
        
        return await handler(agent, skill, **kwargs)
    
    async def _handle_jsonrpc_agent(self, agent: dict, skill: str, **kwargs):
        """Handle JSON-RPC agent invocation per A2A protocol"""
        url = agent['url']
        
        async with httpx.AsyncClient() as client:
            # Standard A2A JSON-RPC 2.0 request
            payload = {
                "jsonrpc": "2.0",
                "method": skill,
                "params": kwargs,
                "id": 1
            }
            response = await client.post(
                f"{url}/jsonrpc",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            if "error" in result:
                raise Exception(f"Agent error: {result['error']}")
            
            return result.get("result", {})
    
    async def _handle_http_agent(self, agent: dict, skill: str, **kwargs):
        """Handle HTTP/REST agent invocation"""
        url = agent['url']
        
        async with httpx.AsyncClient() as client:
            # Assuming REST API follows convention
            response = await client.post(
                f"{url}/skills/{skill}",
                json=kwargs
            )
            response.raise_for_status()
            return response.json()
    
    async def _handle_grpc_agent(self, agent: dict, skill: str, **kwargs):
        """Handle gRPC agent invocation"""
        # Extract host and port from gRPC URL
        url = agent['url'].replace('grpc://', '')
        
        channel = grpc.aio.insecure_channel(url)
        
        # This would require the actual gRPC stub
        # stub = AgentServiceStub(channel)
        # request = SkillRequest(skill_id=skill, parameters=kwargs)
        # return await stub.InvokeSkill(request)
        
        # Placeholder implementation
        await channel.close()
        return {"result": f"gRPC invocation of {skill} on {agent['name']}"}
    
    async def _handle_websocket_agent(self, agent: dict, skill: str, **kwargs):
        """Handle WebSocket agent invocation"""
        # Implementation would depend on WebSocket protocol
        return {"result": f"WebSocket invocation of {skill} on {agent['name']}"}

# Usage
async def universal_example():
    client = UniversalAgentClient("http://localhost:8000")
    
    # Invoke translation service regardless of protocol
    result = await client.discover_and_invoke(
        skill="translate",
        text="Hello, world!",
        target_language="es"
    )
    
    print(f"Translation result: {result}")

asyncio.run(universal_example())
```

## Load Balancing and Failover

### Scenario: Intelligent Agent Selection

Implement sophisticated agent selection with load balancing and health monitoring:

```python
import time
import random
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from collections import defaultdict

@dataclass
class AgentStats:
    """Track agent performance statistics"""
    success_count: int = 0
    failure_count: int = 0
    total_response_time: float = 0.0
    last_success: Optional[float] = None
    last_failure: Optional[float] = None
    consecutive_failures: int = 0
    
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0
    
    @property
    def average_response_time(self) -> float:
        return self.total_response_time / self.success_count if self.success_count > 0 else 0.0

class SmartAgentSelector:
    def __init__(self, registry_client: A2ARegistryClient):
        self.registry = registry_client
        self.agent_stats: Dict[str, AgentStats] = defaultdict(AgentStats)
        self.circuit_breaker_threshold = 5  # Consecutive failures
        self.circuit_breaker_timeout = 300  # 5 minutes
    
    async def select_best_agent(self, skill: str, strategy: str = "balanced") -> Optional[dict]:
        """Select the best agent for a skill using specified strategy"""
        
        # Get available agents
        agents = await self.registry.search_agents(skills=[skill])
        
        if not agents:
            return None
        
        # Filter out circuit-broken agents
        healthy_agents = [
            agent for agent in agents 
            if not self._is_circuit_broken(agent['name'])
        ]
        
        if not healthy_agents:
            # All agents are circuit-broken, try one anyway
            healthy_agents = agents
        
        # Apply selection strategy
        if strategy == "round_robin":
            return self._round_robin_selection(healthy_agents, skill)
        elif strategy == "least_loaded":
            return self._least_loaded_selection(healthy_agents)
        elif strategy == "fastest":
            return self._fastest_selection(healthy_agents)
        elif strategy == "balanced":
            return self._balanced_selection(healthy_agents)
        else:
            return random.choice(healthy_agents)
    
    def _is_circuit_broken(self, agent_name: str) -> bool:
        """Check if agent's circuit breaker is open"""
        stats = self.agent_stats[agent_name]
        
        if stats.consecutive_failures < self.circuit_breaker_threshold:
            return False
        
        # Check if timeout period has passed
        if stats.last_failure:
            time_since_failure = time.time() - stats.last_failure
            if time_since_failure > self.circuit_breaker_timeout:
                # Reset circuit breaker
                stats.consecutive_failures = 0
                return False
        
        return True
    
    def _balanced_selection(self, agents: List[dict]) -> dict:
        """Select agent using balanced scoring"""
        scored_agents = []
        
        for agent in agents:
            stats = self.agent_stats[agent['name']]
            
            # Calculate composite score
            success_weight = 0.4
            speed_weight = 0.3
            availability_weight = 0.3
            
            success_score = stats.success_rate
            speed_score = 1.0 / (1.0 + stats.average_response_time)  # Inverse of response time
            availability_score = 1.0 if stats.consecutive_failures == 0 else 0.5
            
            total_score = (
                success_score * success_weight +
                speed_score * speed_weight +
                availability_score * availability_weight
            )
            
            scored_agents.append((agent, total_score))
        
        # Sort by score (highest first)
        scored_agents.sort(key=lambda x: x[1], reverse=True)
        
        # Add some randomness to top choices
        top_agents = scored_agents[:min(3, len(scored_agents))]
        weights = [score for _, score in top_agents]
        
        return random.choices([agent for agent, _ in top_agents], weights=weights)[0]
    
    def _round_robin_selection(self, agents: List[dict], skill: str) -> dict:
        """Round-robin selection"""
        if not hasattr(self, '_round_robin_counters'):
            self._round_robin_counters = defaultdict(int)
        
        counter = self._round_robin_counters[skill]
        selected = agents[counter % len(agents)]
        self._round_robin_counters[skill] = counter + 1
        
        return selected
    
    def _least_loaded_selection(self, agents: List[dict]) -> dict:
        """Select agent with lowest current load"""
        # In this simplified version, use success rate as proxy for load
        return min(agents, key=lambda a: self.agent_stats[a['name']].success_rate)
    
    def _fastest_selection(self, agents: List[dict]) -> dict:
        """Select agent with best response time"""
        return min(agents, key=lambda a: self.agent_stats[a['name']].average_response_time or float('inf'))
    
    async def invoke_with_fallback(self, skill: str, max_retries: int = 3, **kwargs):
        """Invoke skill with automatic fallback to other agents"""
        
        for attempt in range(max_retries):
            agent = await self.select_best_agent(skill)
            
            if not agent:
                raise ValueError(f"No agents available for skill: {skill}")
            
            agent_name = agent['name']
            start_time = time.time()
            
            try:
                # Invoke agent (implementation depends on agent type)
                result = await self._invoke_agent(agent, skill, **kwargs)
                
                # Record success
                duration = time.time() - start_time
                self._record_success(agent_name, duration)
                
                return result
                
            except Exception as e:
                # Record failure
                self._record_failure(agent_name)
                
                if attempt == max_retries - 1:
                    raise RuntimeError(f"All retry attempts failed. Last error: {e}")
                
                # Wait before retry with exponential backoff
                await asyncio.sleep(2 ** attempt)
    
    def _record_success(self, agent_name: str, duration: float):
        """Record successful agent invocation"""
        stats = self.agent_stats[agent_name]
        stats.success_count += 1
        stats.total_response_time += duration
        stats.last_success = time.time()
        stats.consecutive_failures = 0  # Reset failure counter
    
    def _record_failure(self, agent_name: str):
        """Record failed agent invocation"""
        stats = self.agent_stats[agent_name]
        stats.failure_count += 1
        stats.last_failure = time.time()
        stats.consecutive_failures += 1
    
    async def _invoke_agent(self, agent: dict, skill: str, **kwargs):
        """Invoke agent (simplified implementation)"""
        # This would contain actual agent invocation logic
        # For demo purposes, simulate random success/failure
        await asyncio.sleep(random.uniform(0.1, 2.0))  # Simulate work
        
        if random.random() < 0.1:  # 10% failure rate
            raise Exception("Simulated agent failure")
        
        return {"result": f"Success from {agent['name']}"}

# Usage example
async def load_balanced_example():
    registry = A2ARegistryClient("http://localhost:8000")
    selector = SmartAgentSelector(registry)
    
    # Make multiple requests with intelligent agent selection
    for i in range(10):
        try:
            result = await selector.invoke_with_fallback(
                skill="translate",
                text=f"Message {i}",
                target_language="es"
            )
            print(f"Request {i}: {result}")
        except Exception as e:
            print(f"Request {i} failed: {e}")

asyncio.run(load_balanced_example())
```

## Dynamic Agent Composition

### Scenario: Multi-Agent Workflow

Create workflows that compose multiple agents for complex tasks:

```python
from typing import Any, Callable, List
from dataclasses import dataclass

@dataclass
class WorkflowStep:
    skill: str
    input_transform: Callable[[dict], dict] = lambda x: x
    output_transform: Callable[[dict], dict] = lambda x: x
    required: bool = True
    parallel_group: Optional[str] = None

class AgentWorkflow:
    def __init__(self, registry_client: A2ARegistryClient):
        self.registry = registry_client
        self.steps: List[WorkflowStep] = []
    
    def add_step(self, step: WorkflowStep):
        """Add a step to the workflow"""
        self.steps.append(step)
        return self
    
    def add_skill(self, skill: str, **kwargs):
        """Add a simple skill step"""
        step = WorkflowStep(skill=skill, **kwargs)
        self.steps.append(step)
        return self
    
    async def execute(self, initial_data: dict) -> dict:
        """Execute the workflow"""
        context = {"input": initial_data, "results": {}, "errors": {}}
        
        # Group steps by parallel groups
        step_groups = self._group_steps()
        
        for group_steps in step_groups:
            if len(group_steps) == 1:
                # Sequential step
                await self._execute_step(group_steps[0], context)
            else:
                # Parallel steps
                await self._execute_parallel_steps(group_steps, context)
        
        return context
    
    def _group_steps(self) -> List[List[WorkflowStep]]:
        """Group steps for parallel execution"""
        groups = []
        current_group = []
        current_parallel_group = None
        
        for step in self.steps:
            if step.parallel_group is None:
                # Sequential step
                if current_group:
                    groups.append(current_group)
                    current_group = []
                groups.append([step])
                current_parallel_group = None
            else:
                # Parallel step
                if step.parallel_group != current_parallel_group:
                    if current_group:
                        groups.append(current_group)
                    current_group = [step]
                    current_parallel_group = step.parallel_group
                else:
                    current_group.append(step)
        
        if current_group:
            groups.append(current_group)
        
        return groups
    
    async def _execute_parallel_steps(self, steps: List[WorkflowStep], context: dict):
        """Execute steps in parallel"""
        tasks = [self._execute_step(step, context) for step in steps]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _execute_step(self, step: WorkflowStep, context: dict):
        """Execute a single workflow step"""
        try:
            # Find suitable agent
            agents = await self.registry.search_agents(skills=[step.skill])
            
            if not agents:
                error_msg = f"No agents found for skill: {step.skill}"
                if step.required:
                    raise ValueError(error_msg)
                else:
                    context["errors"][step.skill] = error_msg
                    return
            
            # Prepare input
            step_input = step.input_transform(context)
            
            # Invoke agent (simplified)
            agent = agents[0]  # Use first available agent
            result = await self._invoke_agent(agent, step.skill, **step_input)
            
            # Transform and store output
            transformed_result = step.output_transform(result)
            context["results"][step.skill] = transformed_result
            
        except Exception as e:
            context["errors"][step.skill] = str(e)
            if step.required:
                raise
    
    async def _invoke_agent(self, agent: dict, skill: str, **kwargs):
        """Invoke agent skill (simplified implementation)"""
        # Simulate agent invocation
        await asyncio.sleep(0.1)
        return {
            "agent": agent['name'],
            "skill": skill,
            "result": f"Processed by {agent['name']}"
        }

# Complex workflow example
async def document_processing_workflow():
    """Process a document through multiple AI agents"""
    
    registry = A2ARegistryClient("http://localhost:8000")
    workflow = AgentWorkflow(registry)
    
    # Define workflow steps
    workflow.add_step(WorkflowStep(
        skill="extract_text",
        input_transform=lambda ctx: {"document": ctx["input"]["document"]},
        output_transform=lambda result: {"text": result.get("text", "")}
    ))
    
    # Parallel analysis steps
    workflow.add_step(WorkflowStep(
        skill="sentiment_analysis",
        input_transform=lambda ctx: {"text": ctx["results"]["extract_text"]["text"]},
        parallel_group="analysis"
    ))
    
    workflow.add_step(WorkflowStep(
        skill="entity_extraction",
        input_transform=lambda ctx: {"text": ctx["results"]["extract_text"]["text"]},
        parallel_group="analysis"
    ))
    
    workflow.add_step(WorkflowStep(
        skill="topic_modeling",
        input_transform=lambda ctx: {"text": ctx["results"]["extract_text"]["text"]},
        parallel_group="analysis"
    ))
    
    # Final summary step
    workflow.add_step(WorkflowStep(
        skill="generate_summary",
        input_transform=lambda ctx: {
            "text": ctx["results"]["extract_text"]["text"],
            "sentiment": ctx["results"].get("sentiment_analysis", {}),
            "entities": ctx["results"].get("entity_extraction", {}),
            "topics": ctx["results"].get("topic_modeling", {})
        }
    ))
    
    # Execute workflow
    result = await workflow.execute({
        "document": "path/to/document.pdf"
    })
    
    print("Workflow completed:")
    print(f"Results: {result['results']}")
    print(f"Errors: {result['errors']}")

asyncio.run(document_processing_workflow())
```

## Event-Driven Agent Coordination

### Scenario: Reactive Agent System

Build a system where agents react to events and coordinate automatically:

```python
import asyncio
from typing import Dict, List, Callable
from dataclasses import dataclass
from enum import Enum

class EventType(Enum):
    AGENT_REGISTERED = "agent_registered"
    AGENT_UNREGISTERED = "agent_unregistered"
    SKILL_REQUESTED = "skill_requested"
    TASK_COMPLETED = "task_completed"
    SYSTEM_ERROR = "system_error"

@dataclass
class Event:
    type: EventType
    data: dict
    timestamp: float
    source: str

class EventBus:
    def __init__(self):
        self.subscribers: Dict[EventType, List[Callable]] = {}
        self.event_history: List[Event] = []
    
    def subscribe(self, event_type: EventType, handler: Callable):
        """Subscribe to an event type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)
    
    async def publish(self, event: Event):
        """Publish an event to all subscribers"""
        self.event_history.append(event)
        
        handlers = self.subscribers.get(event.type, [])
        
        # Execute all handlers concurrently
        if handlers:
            await asyncio.gather(
                *[handler(event) for handler in handlers],
                return_exceptions=True
            )
    
    def get_events(self, event_type: EventType = None, since: float = None) -> List[Event]:
        """Get events matching criteria"""
        events = self.event_history
        
        if event_type:
            events = [e for e in events if e.type == event_type]
        
        if since:
            events = [e for e in events if e.timestamp >= since]
        
        return events

class ReactiveAgentCoordinator:
    def __init__(self, registry_client: A2ARegistryClient):
        self.registry = registry_client
        self.event_bus = EventBus()
        self.task_queue = asyncio.Queue()
        self.setup_event_handlers()
    
    def setup_event_handlers(self):
        """Set up event handlers for coordination"""
        
        # Auto-scale handlers
        self.event_bus.subscribe(
            EventType.SKILL_REQUESTED,
            self.handle_skill_demand
        )
        
        # Load balancing
        self.event_bus.subscribe(
            EventType.TASK_COMPLETED,
            self.handle_task_completion
        )
        
        # Health monitoring
        self.event_bus.subscribe(
            EventType.SYSTEM_ERROR,
            self.handle_system_error
        )
    
    async def handle_skill_demand(self, event: Event):
        """Handle requests for skills that might need scaling"""
        skill = event.data.get('skill')
        
        # Check if we have enough agents for this skill
        agents = await self.registry.search_agents(skills=[skill])
        
        if len(agents) < 2:  # Threshold for scaling
            await self.event_bus.publish(Event(
                type=EventType.SYSTEM_ERROR,
                data={
                    "message": f"Low availability for skill: {skill}",
                    "skill": skill,
                    "available_agents": len(agents)
                },
                timestamp=time.time(),
                source="coordinator"
            ))
    
    async def handle_task_completion(self, event: Event):
        """Handle task completion for load balancing"""
        agent_name = event.data.get('agent')
        duration = event.data.get('duration', 0)
        
        # Log performance metrics
        print(f"Task completed by {agent_name} in {duration:.2f}s")
        
        # Could implement dynamic load balancing here
    
    async def handle_system_error(self, event: Event):
        """Handle system errors"""
        error_msg = event.data.get('message')
        print(f"System Alert: {error_msg}")
        
        # Could implement alerting, logging, or recovery actions
    
    async def monitor_agents(self):
        """Background task to monitor agent health"""
        while True:
            try:
                agents = await self.registry.list_agents()
                
                for agent in agents:
                    # Simulate health check
                    if random.random() < 0.05:  # 5% chance of detecting issue
                        await self.event_bus.publish(Event(
                            type=EventType.SYSTEM_ERROR,
                            data={
                                "message": f"Health check failed for {agent['name']}",
                                "agent": agent['name']
                            },
                            timestamp=time.time(),
                            source="health_monitor"
                        ))
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"Health monitoring error: {e}")
                await asyncio.sleep(10)

# Auto-discovering agent client
class SmartAgentClient:
    def __init__(self, coordinator: ReactiveAgentCoordinator):
        self.coordinator = coordinator
        self.registry = coordinator.registry
        self.event_bus = coordinator.event_bus
    
    async def request_skill(self, skill: str, **kwargs):
        """Request a skill with automatic discovery and coordination"""
        
        # Publish skill request event
        await self.event_bus.publish(Event(
            type=EventType.SKILL_REQUESTED,
            data={"skill": skill, "parameters": kwargs},
            timestamp=time.time(),
            source="client"
        ))
        
        # Find and invoke agent
        agents = await self.registry.search_agents(skills=[skill])
        
        if not agents:
            raise ValueError(f"No agents available for skill: {skill}")
        
        # Select best agent (simplified)
        agent = agents[0]
        
        start_time = time.time()
        try:
            # Simulate agent invocation
            await asyncio.sleep(random.uniform(0.1, 1.0))
            result = {"result": f"Task completed by {agent['name']}"}
            
            # Publish completion event
            await self.event_bus.publish(Event(
                type=EventType.TASK_COMPLETED,
                data={
                    "skill": skill,
                    "agent": agent['name'],
                    "duration": time.time() - start_time,
                    "success": True
                },
                timestamp=time.time(),
                source="client"
            ))
            
            return result
            
        except Exception as e:
            # Publish error event
            await self.event_bus.publish(Event(
                type=EventType.SYSTEM_ERROR,
                data={
                    "skill": skill,
                    "agent": agent['name'],
                    "error": str(e)
                },
                timestamp=time.time(),
                source="client"
            ))
            raise

# Usage example
async def reactive_system_example():
    """Demonstrate reactive agent coordination"""
    
    registry = A2ARegistryClient("http://localhost:8000")
    coordinator = ReactiveAgentCoordinator(registry)
    client = SmartAgentClient(coordinator)
    
    # Start background monitoring
    monitor_task = asyncio.create_task(coordinator.monitor_agents())
    
    try:
        # Make several requests to trigger events
        for i in range(5):
            try:
                result = await client.request_skill(
                    skill="translate",
                    text=f"Hello {i}",
                    target_language="es"
                )
                print(f"Request {i}: {result}")
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Request {i} failed: {e}")
        
        # Show event history
        events = coordinator.event_bus.get_events()
        print(f"\nEvent History ({len(events)} events):")
        for event in events[-10:]:  # Last 10 events
            print(f"  {event.type.value}: {event.data}")
    
    finally:
        monitor_task.cancel()

asyncio.run(reactive_system_example())
```

## Agent Mesh with Service Discovery

### Scenario: Distributed Agent Network

Create a mesh of agents that can discover and coordinate with each other:

```python
class AgentMesh:
    def __init__(self, local_agent_id: str, registry_url: str):
        self.local_agent_id = local_agent_id
        self.registry = A2ARegistryClient(registry_url)
        self.peer_connections: Dict[str, Any] = {}
        self.routing_table: Dict[str, List[str]] = {}  # skill -> agent_ids
        self.update_interval = 30  # seconds
    
    async def join_mesh(self, agent_card: dict):
        """Join the agent mesh"""
        # Register with central registry
        await self.registry.register_agent(agent_card)
        
        # Start background tasks
        self.update_task = asyncio.create_task(self._update_routing_table())
        self.heartbeat_task = asyncio.create_task(self._send_heartbeats())
        
        print(f"Agent {self.local_agent_id} joined the mesh")
    
    async def leave_mesh(self):
        """Leave the agent mesh"""
        # Cancel background tasks
        if hasattr(self, 'update_task'):
            self.update_task.cancel()
        if hasattr(self, 'heartbeat_task'):
            self.heartbeat_task.cancel()
        
        # Deregister from central registry
        await self.registry.unregister_agent(self.local_agent_id)
        
        # Close peer connections
        for connection in self.peer_connections.values():
            await connection.close()
        
        print(f"Agent {self.local_agent_id} left the mesh")
    
    async def discover_skill_providers(self, skill: str) -> List[str]:
        """Discover agents that provide a specific skill"""
        # Check local routing table first
        if skill in self.routing_table:
            return self.routing_table[skill]
        
        # Fallback to registry
        agents = await self.registry.search_agents(skills=[skill])
        agent_ids = [agent['name'] for agent in agents]
        
        # Update local routing table
        self.routing_table[skill] = agent_ids
        
        return agent_ids
    
    async def invoke_skill_on_mesh(self, skill: str, **kwargs):
        """Invoke a skill on the best available agent in the mesh"""
        providers = await self.discover_skill_providers(skill)
        
        if not providers:
            raise ValueError(f"No providers found for skill: {skill}")
        
        # Try providers in order of preference
        for provider_id in providers:
            try:
                if provider_id == self.local_agent_id:
                    # Invoke locally
                    return await self._invoke_local_skill(skill, **kwargs)
                else:
                    # Invoke on remote agent
                    return await self._invoke_remote_skill(provider_id, skill, **kwargs)
            except Exception as e:
                print(f"Failed to invoke {skill} on {provider_id}: {e}")
                continue
        
        raise RuntimeError(f"All providers failed for skill: {skill}")
    
    async def _update_routing_table(self):
        """Periodically update routing table from registry"""
        while True:
            try:
                agents = await self.registry.list_agents()
                
                # Rebuild routing table
                new_routing_table = {}
                for agent in agents:
                    agent_id = agent['name']
                    skills = [skill['id'] for skill in agent.get('skills', [])]
                    
                    for skill in skills:
                        if skill not in new_routing_table:
                            new_routing_table[skill] = []
                        new_routing_table[skill].append(agent_id)
                
                self.routing_table = new_routing_table
                print(f"Updated routing table: {len(new_routing_table)} skills")
                
            except Exception as e:
                print(f"Failed to update routing table: {e}")
            
            await asyncio.sleep(self.update_interval)
    
    async def _send_heartbeats(self):
        """Send periodic heartbeats to maintain presence"""
        while True:
            try:
                # This would typically update agent status or send keep-alive
                # For now, just log
                print(f"Agent {self.local_agent_id} heartbeat")
                await asyncio.sleep(30)
            except Exception as e:
                print(f"Heartbeat failed: {e}")
                await asyncio.sleep(5)
    
    async def _invoke_local_skill(self, skill: str, **kwargs):
        """Invoke skill locally"""
        # This would call the local agent's skill implementation
        return {"result": f"Local execution of {skill}", "agent": self.local_agent_id}
    
    async def _invoke_remote_skill(self, agent_id: str, skill: str, **kwargs):
        """Invoke skill on remote agent"""
        # This would make HTTP/gRPC call to remote agent
        # For demo, simulate network call
        await asyncio.sleep(0.1)
        return {"result": f"Remote execution of {skill}", "agent": agent_id}

# Mesh usage example
async def agent_mesh_example():
    """Demonstrate agent mesh coordination"""
    
    # Create multiple agents in the mesh
    agents = []
    for i in range(3):
        agent_id = f"mesh-agent-{i}"
        mesh = AgentMesh(agent_id, "http://localhost:8000")
        
        # Define agent capabilities
        agent_card = {
            "name": agent_id,
            "description": f"Mesh agent {i}",
            "url": f"http://localhost:300{i}",
            "version": "0.420.0",
            "protocol_version": "0.3.0",
            "skills": [
                {"id": f"skill_{i}", "description": f"Specialized skill {i}"},
                {"id": "common_skill", "description": "Common skill all agents have"}
            ]
        }
        
        await mesh.join_mesh(agent_card)
        agents.append(mesh)
    
    # Wait for routing tables to update
    await asyncio.sleep(2)
    
    try:
        # Test cross-mesh skill invocation
        primary_agent = agents[0]
        
        # Invoke specialized skill from another agent
        result1 = await primary_agent.invoke_skill_on_mesh("skill_1")
        print(f"Specialized skill result: {result1}")
        
        # Invoke common skill (could be handled by any agent)
        result2 = await primary_agent.invoke_skill_on_mesh("common_skill")
        print(f"Common skill result: {result2}")
        
    finally:
        # Clean up
        for agent in agents:
            await agent.leave_mesh()

asyncio.run(agent_mesh_example())
```

## Best Practices for Advanced Scenarios

1. **Circuit Breakers**: Implement circuit breakers to handle failing agents gracefully
2. **Health Checks**: Regular health monitoring and automatic failover
3. **Load Balancing**: Intelligent agent selection based on performance metrics
4. **Caching**: Cache agent discovery results for better performance
5. **Event-Driven Architecture**: Use events for loose coupling between components
6. **Graceful Degradation**: Handle partial failures without complete system breakdown
7. **Monitoring**: Comprehensive logging and metrics collection
8. **Security**: Implement authentication and authorization for agent communication
9. **Versioning**: Handle agent API versioning and compatibility
10. **Documentation**: Clear documentation of agent interfaces and workflows

## Next Steps

- Review [Basic Usage](basic-usage.md) for foundational concepts
- Check [Agent Registration](agent-registration.md) for registration patterns
- Explore [Agent Discovery](agent-discovery.md) for discovery strategies
- Learn about [API Reference](../api/overview.md) for detailed API documentation