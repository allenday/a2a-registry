# Agent Discovery Examples

This guide demonstrates various strategies and patterns for discovering agents in the A2A Registry.

## Basic Discovery

The A2A Registry supports both JSON-RPC 2.0 (primary) and REST (secondary) protocols. All examples show JSON-RPC first as it's the default transport per the **A2A Protocol v0.3.0** specification.

### Search by Name

Find agents by their name using JSON-RPC:

```bash
curl -X POST http://localhost:8000/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "search_agents",
    "params": {"query": "weather"},
    "id": 1
  }'
```

REST alternative:
```bash
curl -X POST http://localhost:8000/agents/search \
  -H "Content-Type: application/json" \
  -d '{"query": "weather"}'
```

### Search by Description

Find agents by keywords in their description using JSON-RPC:

```bash
curl -X POST http://localhost:8000/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "search_agents",
    "params": {"query": "natural language processing"},
    "id": 2
  }'
```

REST alternative:
```bash
curl -X POST http://localhost:8000/agents/search \
  -H "Content-Type: application/json" \
  -d '{"query": "natural language processing"}'
```

### Search by Skills

Find agents with specific capabilities using JSON-RPC:

```bash
curl -X POST http://localhost:8000/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "search_agents",
    "params": {"query": "translate"},
    "id": 3
  }'
```

REST alternative:
```bash
curl -X POST http://localhost:8000/agents/search \
  -H "Content-Type: application/json" \
  -d '{"query": "translate"}'
```

## Advanced Discovery Patterns

### Python Discovery Client with JSON-RPC

```python
import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class AgentSearchCriteria:
    required_skills: List[str] = None
    preferred_skills: List[str] = None
    min_version: str = None
    max_response_time_ms: int = None
    regions: List[str] = None
    exclude_agents: List[str] = None

class AgentDiscoveryClient:
    def __init__(self, registry_url="http://localhost:8000"):
        self.registry_url = registry_url
        self.request_id = 0
    
    def _next_id(self) -> int:
        """Generate next JSON-RPC request ID."""
        self.request_id += 1
        return self.request_id
    
    def _jsonrpc_request(self, method: str, params: dict = None) -> dict:
        """Make a JSON-RPC 2.0 request."""
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "id": self._next_id()
        }
        if params:
            payload["params"] = params
        
        response = requests.post(
            f"{self.registry_url}/jsonrpc",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        result = response.json()
        
        if "error" in result:
            raise Exception(f"JSON-RPC Error: {result['error']}")
        
        return result.get("result", {})
    
    def find_agents_by_skill(self, skill_id: str) -> List[Dict[str, Any]]:
        """Find all agents that have a specific skill using JSON-RPC."""
        result = self._jsonrpc_request("search_agents", {"query": skill_id})
        return result.get("agents", [])
    
    def find_agents_by_skill_rest(self, skill_id: str) -> List[Dict[str, Any]]:
        """Find all agents that have a specific skill using REST (fallback)."""
        response = requests.post(
            f"{self.registry_url}/agents/search",
            json={"query": skill_id}
        )
        response.raise_for_status()
        return response.json()["agents"]
    
    def find_best_agent_for_task(self, 
                                required_skills: List[str],
                                task_description: str = None) -> Optional[Dict[str, Any]]:
        """Find the best agent for a specific task."""
        all_agents = self.get_all_agents()
        
        # Filter agents that have all required skills
        compatible_agents = []
        for agent in all_agents:
            agent_skills = {skill["id"] for skill in agent.get("skills", [])}
            if all(skill in agent_skills for skill in required_skills):
                compatible_agents.append(agent)
        
        if not compatible_agents:
            return None
        
        # Rank agents by relevance
        ranked_agents = self._rank_agents_by_relevance(
            compatible_agents, required_skills, task_description
        )
        
        return ranked_agents[0] if ranked_agents else None
    
    def find_agents_by_criteria(self, criteria: AgentSearchCriteria) -> List[Dict[str, Any]]:
        """Find agents matching complex criteria."""
        all_agents = self.get_all_agents()
        matching_agents = []
        
        for agent in all_agents:
            if self._matches_criteria(agent, criteria):
                matching_agents.append(agent)
        
        return matching_agents
    
    def get_all_agents(self) -> List[Dict[str, Any]]:
        """Get all registered agents using JSON-RPC."""
        result = self._jsonrpc_request("list_agents")
        return result.get("agents", [])
    
    def get_all_agents_rest(self) -> List[Dict[str, Any]]:
        """Get all registered agents using REST (fallback)."""
        response = requests.get(f"{self.registry_url}/agents")
        response.raise_for_status()
        return response.json()["agents"]
    
    def find_similar_agents(self, reference_agent_id: str) -> List[Dict[str, Any]]:
        """Find agents similar to a reference agent using JSON-RPC."""
        # Get reference agent
        try:
            result = self._jsonrpc_request("get_agent", {"agent_name": reference_agent_id})
            reference_agent = result.get("agent_card")
        except Exception:
            return []
        
        if not reference_agent:
            return []
        reference_skills = {skill["id"] for skill in reference_agent.get("skills", [])}
        
        # Find agents with overlapping skills
        all_agents = self.get_all_agents()
        similar_agents = []
        
        for agent in all_agents:
            if agent["name"] == reference_agent_id:
                continue
            
            agent_skills = {skill["id"] for skill in agent.get("skills", [])}
            overlap = len(reference_skills.intersection(agent_skills))
            
            if overlap > 0:
                similarity_score = overlap / len(reference_skills.union(agent_skills))
                agent["similarity_score"] = similarity_score
                similar_agents.append(agent)
        
        # Sort by similarity
        similar_agents.sort(key=lambda x: x["similarity_score"], reverse=True)
        return similar_agents
    
    def _matches_criteria(self, agent: Dict[str, Any], criteria: AgentSearchCriteria) -> bool:
        """Check if an agent matches the given criteria."""
        # Check required skills
        if criteria.required_skills:
            agent_skills = {skill["id"] for skill in agent.get("skills", [])}
            if not all(skill in agent_skills for skill in criteria.required_skills):
                return False
        
        # Check version requirements
        if criteria.min_version:
            from packaging import version
            if version.parse(agent.get("version", "0.0.0")) < version.parse(criteria.min_version):
                return False
        
        # Check response time requirements
        if criteria.max_response_time_ms:
            agent_response_time = agent.get("metadata", {}).get("average_response_time_ms")
            if agent_response_time and agent_response_time > criteria.max_response_time_ms:
                return False
        
        # Check region preferences
        if criteria.regions:
            agent_regions = agent.get("metadata", {}).get("preferred_regions", [])
            if not any(region in agent_regions for region in criteria.regions):
                return False
        
        # Check exclusion list
        if criteria.exclude_agents and agent["name"] in criteria.exclude_agents:
            return False
        
        return True
    
    def _rank_agents_by_relevance(self, 
                                 agents: List[Dict[str, Any]], 
                                 required_skills: List[str],
                                 task_description: str = None) -> List[Dict[str, Any]]:
        """Rank agents by their relevance to the task."""
        scored_agents = []
        
        for agent in agents:
            score = 0
            agent_skills = {skill["id"] for skill in agent.get("skills", [])}
            
            # Base score: number of matching skills
            matching_skills = len(set(required_skills).intersection(agent_skills))
            score += matching_skills * 10
            
            # Bonus for additional relevant skills
            if task_description:
                for skill in agent.get("skills", []):
                    if any(word in skill["description"].lower() 
                          for word in task_description.lower().split()):
                        score += 5
            
            # Performance bonuses
            metadata = agent.get("metadata", {})
            if metadata.get("average_response_time_ms", 1000) < 500:
                score += 5  # Fast response time
            
            if metadata.get("uptime_percentage", 0) > 99:
                score += 3  # High uptime
            
            agent["relevance_score"] = score
            scored_agents.append(agent)
        
        scored_agents.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored_agents

# Usage examples
def main():
    discovery = AgentDiscoveryClient()
    
    # Find agents for natural language processing
    nlp_agents = discovery.find_agents_by_skill("natural_language_processing")
    print(f"Found {len(nlp_agents)} NLP agents")
    
    # Find best agent for translation task
    translation_agent = discovery.find_best_agent_for_task(
        required_skills=["translate_text", "detect_language"],
        task_description="Translate document from Spanish to English"
    )
    if translation_agent:
        print(f"Best translation agent: {translation_agent['name']}")
    
    # Find agents with specific criteria
    criteria = AgentSearchCriteria(
        required_skills=["image_analysis"],
        min_version="2.0.0",
        max_response_time_ms=1000,
        regions=["us-east-1", "us-west-2"]
    )
    matching_agents = discovery.find_agents_by_criteria(criteria)
    print(f"Found {len(matching_agents)} agents matching criteria")
    
    # Find similar agents
    if nlp_agents:
        similar = discovery.find_similar_agents(nlp_agents[0]["name"])
        print(f"Found {len(similar)} similar agents")

if __name__ == "__main__":
    main()
```

## Task-Specific Discovery

### Multi-Modal Task Discovery

```python
class TaskOrchestrator:
    def __init__(self, discovery_client: AgentDiscoveryClient):
        self.discovery = discovery_client
    
    def find_agents_for_complex_task(self, task_definition: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Find agents for a complex multi-step task."""
        required_capabilities = task_definition.get("required_capabilities", [])
        optional_capabilities = task_definition.get("optional_capabilities", [])
        constraints = task_definition.get("constraints", {})
        
        # Find agents for each capability
        capability_agents = {}
        
        for capability in required_capabilities:
            agents = self.discovery.find_agents_by_skill(capability)
            
            # Apply constraints
            if constraints:
                agents = self._apply_constraints(agents, constraints)
            
            capability_agents[capability] = agents
        
        # Find agents that can handle multiple capabilities
        multi_capability_agents = self._find_multi_capability_agents(
            required_capabilities, capability_agents
        )
        
        return {
            "single_capability": capability_agents,
            "multi_capability": multi_capability_agents,
            "orchestration_plan": self._create_orchestration_plan(
                required_capabilities, capability_agents, multi_capability_agents
            )
        }
    
    def _apply_constraints(self, agents: List[Dict[str, Any]], constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply constraints to filter agents."""
        filtered_agents = []
        
        for agent in agents:
            metadata = agent.get("metadata", {})
            
            # Performance constraints
            if "max_response_time" in constraints:
                if metadata.get("average_response_time_ms", 0) > constraints["max_response_time"]:
                    continue
            
            # Resource constraints
            if "max_memory_usage" in constraints:
                if metadata.get("memory_usage_mb", 0) > constraints["max_memory_usage"]:
                    continue
            
            # Compliance constraints
            if "required_compliance" in constraints:
                agent_compliance = metadata.get("compliance", [])
                if not all(req in agent_compliance for req in constraints["required_compliance"]):
                    continue
            
            filtered_agents.append(agent)
        
        return filtered_agents
    
    def _find_multi_capability_agents(self, 
                                    required_capabilities: List[str],
                                    capability_agents: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Find agents that can handle multiple capabilities."""
        all_agents = self.discovery.get_all_agents()
        multi_capability = []
        
        for agent in all_agents:
            agent_skills = {skill["id"] for skill in agent.get("skills", [])}
            
            # Count how many required capabilities this agent can handle
            covered_capabilities = [
                cap for cap in required_capabilities
                if cap in agent_skills
            ]
            
            if len(covered_capabilities) > 1:
                agent["covered_capabilities"] = covered_capabilities
                agent["capability_coverage"] = len(covered_capabilities) / len(required_capabilities)
                multi_capability.append(agent)
        
        # Sort by capability coverage
        multi_capability.sort(key=lambda x: x["capability_coverage"], reverse=True)
        return multi_capability
    
    def _create_orchestration_plan(self, 
                                 required_capabilities: List[str],
                                 capability_agents: Dict[str, List[Dict[str, Any]]],
                                 multi_capability_agents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create an orchestration plan for the task."""
        plan = {
            "strategy": "unknown",
            "agents": [],
            "workflow": []
        }
        
        # Strategy 1: Single agent handles everything
        if multi_capability_agents:
            best_agent = multi_capability_agents[0]
            if best_agent["capability_coverage"] == 1.0:
                plan["strategy"] = "single_agent"
                plan["agents"] = [best_agent]
                plan["workflow"] = [
                    {
                        "step": 1,
                        "agent": best_agent["name"],
                        "capabilities": best_agent["covered_capabilities"]
                    }
                ]
                return plan
        
        # Strategy 2: Multi-agent pipeline
        plan["strategy"] = "multi_agent_pipeline"
        step = 1
        
        for capability in required_capabilities:
            agents = capability_agents.get(capability, [])
            if agents:
                best_agent = agents[0]  # Assume first is best ranked
                plan["agents"].append(best_agent)
                plan["workflow"].append({
                    "step": step,
                    "agent": best_agent["name"],
                    "capability": capability
                })
                step += 1
        
        return plan

# Example usage
def document_processing_example():
    discovery = AgentDiscoveryClient()
    orchestrator = TaskOrchestrator(discovery)
    
    # Define a complex document processing task
    task = {
        "name": "legal_document_analysis",
        "description": "Analyze legal documents for compliance and extract key information",
        "required_capabilities": [
            "pdf_text_extraction",
            "legal_entity_recognition",
            "compliance_checking",
            "document_summarization"
        ],
        "optional_capabilities": [
            "language_detection",
            "sentiment_analysis"
        ],
        "constraints": {
            "max_response_time": 5000,  # 5 seconds
            "required_compliance": ["GDPR", "SOX"],
            "preferred_regions": ["us-east-1", "eu-west-1"]
        }
    }
    
    # Find suitable agents
    result = orchestrator.find_agents_for_complex_task(task)
    
    print("Orchestration Plan:")
    print(f"Strategy: {result['orchestration_plan']['strategy']}")
    print(f"Required agents: {len(result['orchestration_plan']['agents'])}")
    
    for step in result['orchestration_plan']['workflow']:
        print(f"Step {step['step']}: {step['agent']} - {step.get('capability', step.get('capabilities'))}")

def main():
    document_processing_example()

if __name__ == "__main__":
    main()
```

## Discovery with Load Balancing

```python
import random
from typing import Dict, List, Any

class LoadBalancedDiscovery:
    def __init__(self, discovery_client: AgentDiscoveryClient):
        self.discovery = discovery_client
        self.agent_metrics = {}  # Track agent performance metrics
    
    def find_agent_with_load_balancing(self, 
                                     required_skill: str,
                                     load_balancing_strategy: str = "round_robin") -> Dict[str, Any]:
        """Find an agent with load balancing considerations."""
        candidate_agents = self.discovery.find_agents_by_skill(required_skill)
        
        if not candidate_agents:
            return None
        
        if load_balancing_strategy == "round_robin":
            return self._round_robin_selection(candidate_agents, required_skill)
        elif load_balancing_strategy == "least_loaded":
            return self._least_loaded_selection(candidate_agents)
        elif load_balancing_strategy == "random":
            return random.choice(candidate_agents)
        elif load_balancing_strategy == "performance_weighted":
            return self._performance_weighted_selection(candidate_agents)
        else:
            return candidate_agents[0]  # Default to first
    
    def _round_robin_selection(self, agents: List[Dict[str, Any]], skill: str) -> Dict[str, Any]:
        """Select agent using round-robin strategy."""
        if skill not in self.agent_metrics:
            self.agent_metrics[skill] = {"round_robin_index": 0}
        
        index = self.agent_metrics[skill]["round_robin_index"]
        selected_agent = agents[index % len(agents)]
        
        # Update index for next selection
        self.agent_metrics[skill]["round_robin_index"] = (index + 1) % len(agents)
        
        return selected_agent
    
    def _least_loaded_selection(self, agents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select the least loaded agent."""
        # In a real implementation, this would query actual load metrics
        # For this example, we'll use simulated metrics
        
        least_loaded = None
        min_load = float('inf')
        
        for agent in agents:
            # Simulate getting current load (0-100%)
            current_load = self._get_agent_current_load(agent["name"])
            
            if current_load < min_load:
                min_load = current_load
                least_loaded = agent
        
        return least_loaded
    
    def _performance_weighted_selection(self, agents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select agent based on performance weights."""
        weights = []
        
        for agent in agents:
            # Calculate weight based on performance metrics
            metadata = agent.get("metadata", {})
            
            # Lower response time = higher weight
            response_time = metadata.get("average_response_time_ms", 1000)
            response_weight = max(0, 1000 - response_time) / 1000
            
            # Higher uptime = higher weight
            uptime = metadata.get("uptime_percentage", 95) / 100
            
            # Lower current load = higher weight
            current_load = self._get_agent_current_load(agent["name"])
            load_weight = max(0, 100 - current_load) / 100
            
            # Combined weight
            total_weight = (response_weight * 0.4 + uptime * 0.3 + load_weight * 0.3)
            weights.append(total_weight)
        
        # Weighted random selection
        return self._weighted_random_choice(agents, weights)
    
    def _get_agent_current_load(self, agent_name: str) -> float:
        """Get current load percentage for an agent."""
        # In a real implementation, this would query the agent's metrics endpoint
        # For this example, return a random load between 0-100
        return random.uniform(0, 100)
    
    def _weighted_random_choice(self, agents: List[Dict[str, Any]], weights: List[float]) -> Dict[str, Any]:
        """Select a random agent based on weights."""
        total_weight = sum(weights)
        if total_weight == 0:
            return random.choice(agents)
        
        r = random.uniform(0, total_weight)
        cumulative_weight = 0
        
        for agent, weight in zip(agents, weights):
            cumulative_weight += weight
            if r <= cumulative_weight:
                return agent
        
        return agents[-1]  # Fallback
    
    def record_agent_performance(self, agent_name: str, response_time_ms: int, success: bool):
        """Record performance metrics for an agent."""
        if agent_name not in self.agent_metrics:
            self.agent_metrics[agent_name] = {
                "response_times": [],
                "success_rate": []
            }
        
        metrics = self.agent_metrics[agent_name]
        metrics["response_times"].append(response_time_ms)
        metrics["success_rate"].append(success)
        
        # Keep only recent metrics (last 100 requests)
        metrics["response_times"] = metrics["response_times"][-100:]
        metrics["success_rate"] = metrics["success_rate"][-100:]

# Example usage
def load_balancing_example():
    discovery = AgentDiscoveryClient()
    lb_discovery = LoadBalancedDiscovery(discovery)
    
    # Simulate multiple requests for the same skill
    skill = "text_classification"
    
    print("Load-balanced agent selection:")
    for i in range(5):
        agent = lb_discovery.find_agent_with_load_balancing(
            skill, 
            "round_robin"
        )
        if agent:
            print(f"Request {i+1}: Selected {agent['name']}")
    
    print("\nPerformance-weighted selection:")
    for i in range(5):
        agent = lb_discovery.find_agent_with_load_balancing(
            skill,
            "performance_weighted"
        )
        if agent:
            print(f"Request {i+1}: Selected {agent['name']}")

if __name__ == "__main__":
    load_balancing_example()
```

## Geographic Discovery

```python
class GeographicDiscovery:
    def __init__(self, discovery_client: AgentDiscoveryClient):
        self.discovery = discovery_client
        
        # Region proximity mapping (simplified)
        self.region_proximity = {
            "us-east-1": ["us-east-2", "us-west-1", "us-west-2"],
            "us-west-1": ["us-west-2", "us-east-1", "us-east-2"],
            "eu-west-1": ["eu-central-1", "eu-north-1"],
            "ap-southeast-1": ["ap-southeast-2", "ap-northeast-1"]
        }
    
    def find_nearest_agents(self, 
                           required_skill: str,
                           user_region: str,
                           max_distance: int = 2) -> List[Dict[str, Any]]:
        """Find agents nearest to the user's region."""
        all_agents = self.discovery.find_agents_by_skill(required_skill)
        regional_agents = []
        
        for agent in all_agents:
            agent_regions = agent.get("metadata", {}).get("preferred_regions", [])
            
            for region in agent_regions:
                distance = self._calculate_region_distance(user_region, region)
                if distance <= max_distance:
                    agent["region_distance"] = distance
                    agent["matched_region"] = region
                    regional_agents.append(agent)
                    break  # Use the closest region for this agent
        
        # Sort by distance
        regional_agents.sort(key=lambda x: x["region_distance"])
        return regional_agents
    
    def _calculate_region_distance(self, region1: str, region2: str) -> int:
        """Calculate distance between regions (simplified)."""
        if region1 == region2:
            return 0
        
        if region2 in self.region_proximity.get(region1, []):
            return 1
        
        # Check if they're in the same continent
        continent1 = region1.split("-")[0]
        continent2 = region2.split("-")[0]
        
        if continent1 == continent2:
            return 2
        
        return 3  # Different continents
    
    def find_multi_region_deployment(self, 
                                   required_skill: str,
                                   target_regions: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Find agents for multi-region deployment."""
        deployment_plan = {}
        
        for region in target_regions:
            nearest_agents = self.find_nearest_agents(required_skill, region, max_distance=1)
            deployment_plan[region] = nearest_agents
        
        return deployment_plan

# Example usage
def geographic_discovery_example():
    discovery = AgentDiscoveryClient()
    geo_discovery = GeographicDiscovery(discovery)
    
    # Find nearest translation agents to EU region
    agents = geo_discovery.find_nearest_agents(
        "translate_text",
        "eu-west-1",
        max_distance=2
    )
    
    print("Nearest translation agents to EU:")
    for agent in agents:
        print(f"{agent['name']} - Distance: {agent['region_distance']} - Region: {agent['matched_region']}")
    
    # Plan multi-region deployment
    target_regions = ["us-east-1", "eu-west-1", "ap-southeast-1"]
    deployment = geo_discovery.find_multi_region_deployment("image_analysis", target_regions)
    
    print("\nMulti-region deployment plan:")
    for region, agents in deployment.items():
        print(f"{region}: {len(agents)} available agents")

if __name__ == "__main__":
    geographic_discovery_example()
```

This comprehensive guide covers various agent discovery patterns, from basic search to complex multi-criteria discovery with load balancing and geographic considerations.