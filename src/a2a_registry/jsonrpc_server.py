"""A2A Registry JSON-RPC server implementation."""

import logging
from typing import Any, Optional

from fasta2a.schema import AgentCard  # type: ignore
from jsonrpcserver import Error, Result, Success, method

from . import A2A_PROTOCOL_VERSION, __version__
from .storage import storage

logger = logging.getLogger(__name__)


@method
async def register_agent(agent_card: dict[str, Any]) -> Result:
    """Register an agent in the registry via JSON-RPC.

    Args:
        agent_card: Agent card data following FastA2A schema

    Returns:
        Success with registration details or Error
    """
    try:
        # Validate required fields for AgentCard
        required_fields = [
            "name",
            "description",
            "url",
            "version",
            "protocol_version",
        ]
        for field in required_fields:
            if field not in agent_card:
                return Error(code=-32602, message=f"Missing required field: {field}")

        # Set default transport to JSONRPC per A2A specification
        if "preferred_transport" not in agent_card:
            agent_card["preferred_transport"] = "JSONRPC"

        # Cast to AgentCard type for type safety
        typed_agent_card: AgentCard = agent_card  # type: ignore
        success = await storage.register_agent(typed_agent_card)

        if success:
            return Success(
                {
                    "success": True,
                    "agent_id": agent_card["name"],
                    "message": "Agent registered successfully",
                    "transport": "JSONRPC",
                }
            )
        else:
            return Error(code=-32603, message="Failed to register agent")

    except Exception as e:
        logger.error(f"Error registering agent via JSON-RPC: {e}")
        return Error(code=-32603, message=str(e))


@method
async def get_agent(agent_id: str) -> Result:
    """Get an agent by ID via JSON-RPC.

    Args:
        agent_id: Unique identifier for the agent

    Returns:
        Success with agent data or Error if not found
    """
    try:
        agent_card = await storage.get_agent(agent_id)
        if agent_card:
            return Success({"agent_card": dict(agent_card), "found": True})
        else:
            return Error(code=-32001, message="Agent not found")

    except Exception as e:
        logger.error(f"Error getting agent via JSON-RPC: {e}")
        return Error(code=-32603, message=str(e))


@method
async def list_agents() -> Result:
    """List all registered agents via JSON-RPC.

    Returns:
        Success with list of all agents
    """
    try:
        agents = await storage.list_agents()
        return Success(
            {
                "agents": [dict(agent) for agent in agents],
                "count": len(agents),
                "transport": "JSONRPC",
            }
        )

    except Exception as e:
        logger.error(f"Error listing agents via JSON-RPC: {e}")
        return Error(code=-32603, message=str(e))


@method
async def unregister_agent(agent_id: str) -> Result:
    """Unregister an agent via JSON-RPC.

    Args:
        agent_id: Unique identifier for the agent to remove

    Returns:
        Success with confirmation or Error if not found
    """
    try:
        success = await storage.unregister_agent(agent_id)
        if success:
            return Success(
                {
                    "success": True,
                    "message": "Agent unregistered successfully",
                    "agent_id": agent_id,
                }
            )
        else:
            return Error(code=-32001, message="Agent not found")

    except Exception as e:
        logger.error(f"Error unregistering agent via JSON-RPC: {e}")
        return Error(code=-32603, message=str(e))


@method
async def search_agents(query: str, skills: Optional[list[str]] = None) -> Result:
    """Search for agents via JSON-RPC.

    Args:
        query: Search query string
        skills: Optional list of skills to filter by

    Returns:
        Success with matching agents
    """
    try:
        # Enhanced search functionality
        results = []
        query_lower = query.lower() if query else ""

        agents = await storage.list_agents()
        for agent in agents:
            matches = False

            # Search by query in name, description
            if query_lower:
                if (
                    query_lower in agent.get("name", "").lower()
                    or query_lower in agent.get("description", "").lower()
                    or any(
                        query_lower in skill.get("id", "").lower()
                        or query_lower in skill.get("description", "").lower()
                        for skill in agent.get("skills", [])
                    )
                ):
                    matches = True
            else:
                matches = True  # No query means match all

            # Filter by skills if provided
            if skills and matches:
                agent_skills = [
                    skill.get("id", "") for skill in agent.get("skills", [])
                ]
                if not any(skill in agent_skills for skill in skills):
                    matches = False

            if matches:
                results.append(agent)

        return Success(
            {
                "agents": [dict(agent) for agent in results],
                "count": len(results),
                "query": query,
                "skills_filter": skills,
                "transport": "JSONRPC",
            }
        )

    except Exception as e:
        logger.error(f"Error searching agents via JSON-RPC: {e}")
        return Error(code=-32603, message=str(e))


@method
async def get_agent_card() -> Result:
    """Get the registry's own agent card via JSON-RPC.

    This implements the A2A protocol requirement for GetAgentCard.

    Returns:
        Success with registry's agent card
    """
    try:
        registry_card: AgentCard = {
            "name": "A2A Registry",
            "description": "A central registry for Agent-to-Agent (A2A) discovery and coordination",
            "url": "http://localhost:8000",  # Will be configurable
            "version": __version__,
            "protocol_version": A2A_PROTOCOL_VERSION,
            "preferred_transport": "JSONRPC",  # A2A default
            "capabilities": {
                "streaming": False,
                "push_notifications": False,
                "state_transition_history": False,
            },
            "default_input_modes": ["application/json"],
            "default_output_modes": ["application/json"],
            "skills": [
                {
                    "id": "register_agent",
                    "description": "Register a new agent in the registry",
                },
                {"id": "get_agent", "description": "Retrieve agent information by ID"},
                {"id": "list_agents", "description": "List all registered agents"},
                {
                    "id": "search_agents",
                    "description": "Search for agents by query and skills",
                },
                {
                    "id": "unregister_agent",
                    "description": "Remove an agent from the registry",
                },
            ],
        }

        return Success({"agent_card": dict(registry_card)})

    except Exception as e:
        logger.error(f"Error getting registry agent card: {e}")
        return Error(code=-32603, message=str(e))


@method
async def health_check() -> Result:
    """Health check endpoint via JSON-RPC.

    Returns:
        Success with health status
    """
    try:
        agents = await storage.list_agents()
        agents_count = len(agents)
        return Success(
            {
                "status": "healthy",
                "service": "A2A Registry",
                "transport": "JSONRPC",
                "agents_count": agents_count,
                "protocol_version": A2A_PROTOCOL_VERSION,
            }
        )

    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return Error(code=-32603, message=str(e))


def get_jsonrpc_methods() -> list[str]:
    """Get list of available JSON-RPC methods for introspection."""
    return [
        "register_agent",
        "get_agent",
        "list_agents",
        "unregister_agent",
        "search_agents",
        "get_agent_card",
        "health_check",
    ]
