"""A2A Registry JSON-RPC server implementation."""

import logging
from datetime import UTC
from typing import Any

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
async def search_agents(
    query: str = "",
    skills: list[str] | None = None,
    search_mode: str = "SEARCH_MODE_VECTOR",
    similarity_threshold: float = 0.7,
    max_results: int = 10,
) -> Result:
    """Search for agents via JSON-RPC with vector search support.

    Args:
        query: Search query string (for keyword) or semantic query (for vector search)
        skills: Optional list of skill IDs to filter by
        search_mode: "SEARCH_MODE_KEYWORD" or "SEARCH_MODE_VECTOR"
        similarity_threshold: Minimum similarity score for vector search (0.0-1.0)
        max_results: Maximum number of results to return

    Returns:
        Success with matching agents and similarity scores
    """
    try:
        # Use vector-enhanced storage if available
        if hasattr(storage, "search_agents_hybrid"):
            results = await storage.search_agents_hybrid(
                query=query,
                skills=skills,
                search_mode=search_mode,
                similarity_threshold=similarity_threshold,
                max_results=max_results,
            )

            # Format response with similarity scores
            response = {
                "agents": [dict(agent) for agent, _ in results],
                "count": len(results),
                "query": query,
                "skills_filter": skills,
                "search_mode": search_mode,
                "transport": "JSONRPC",
            }

            # Include similarity scores for vector search
            if search_mode == "SEARCH_MODE_VECTOR":
                response["similarity_scores"] = [
                    score for _, score in results if score is not None
                ]
                response["similarity_threshold"] = similarity_threshold

            return Success(response)

        else:
            # Fallback to basic keyword search for backward compatibility
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
                    "agents": [dict(agent) for agent in results[:max_results]],
                    "count": len(results[:max_results]),
                    "query": query,
                    "skills_filter": skills,
                    "search_mode": "SEARCH_MODE_KEYWORD",
                    "transport": "JSONRPC",
                }
            )

    except Exception as e:
        logger.error(f"Error searching agents via JSON-RPC: {e}")
        return Error(code=-32603, message=str(e))


@method
async def list_extensions(
    uri_pattern: str | None = None,
    declaring_agents: list[str] | None = None,
    trust_levels: list[str] | None = None,
    page_size: int = 100,
    page_token: str | None = None,
) -> Result:
    """List extensions via JSON-RPC.

    Args:
        uri_pattern: Optional URI pattern to filter by
        declaring_agents: Optional list of agent IDs to filter by
        trust_levels: Optional list of trust levels to filter by
        page_size: Number of extensions per page (default: 100)
        page_token: Page token for pagination

    Returns:
        Success with list of extensions
    """
    try:
        extensions, next_page_token, total_count = await storage.list_extensions(
            uri_pattern=uri_pattern,
            declaring_agents=declaring_agents,
            trust_levels=trust_levels,
            page_size=page_size,
            page_token=page_token,
        )

        return Success(
            {
                "extensions": [ext.to_dict() for ext in extensions],
                "count": len(extensions),
                "total_count": total_count,
                "next_page_token": next_page_token,
                "transport": "JSONRPC",
            }
        )

    except Exception as e:
        logger.error(f"Error listing extensions via JSON-RPC: {e}")
        return Error(code=-32603, message=str(e))


@method
async def ping_agent(agent_id: str) -> Result:
    """Ping an agent to check its health/responsiveness via JSON-RPC.

    Args:
        agent_id: Unique identifier for the agent to ping

    Returns:
        Success with ping response or Error if agent not found
    """
    try:
        # First check if agent exists in registry
        agent_card = await storage.get_agent(agent_id)
        if not agent_card:
            return Error(code=-32001, message="Agent not found")

        # For now, we'll return a basic ping response
        # In a full implementation, this would actually attempt to contact the agent
        from datetime import datetime

        timestamp = datetime.now(UTC)

        return Success(
            {
                "responsive": True,  # Assuming agent is responsive if it's registered
                "response_time_ms": 0,  # No actual network call for now
                "status": "registered",
                "timestamp": timestamp.isoformat(),
                "agent_id": agent_id,
                "transport": "JSONRPC",
            }
        )

    except Exception as e:
        logger.error(f"Error pinging agent via JSON-RPC: {e}")
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
                {
                    "id": "list_extensions",
                    "description": "List available extensions",
                },
                {
                    "id": "ping_agent",
                    "description": "Ping an agent to check health",
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


@method
async def system_listMethods() -> Result:
    """JSON-RPC system method for listing available methods.

    This implements the standard JSON-RPC system.listMethods method.

    Returns:
        Success with list of available methods
    """
    try:
        methods = get_jsonrpc_methods()
        return Success(methods)

    except Exception as e:
        logger.error(f"Error listing methods: {e}")
        return Error(code=-32603, message=str(e))


@method
async def list_methods() -> Result:
    """Alternative method name for listing available methods.

    This provides the same functionality as system.listMethods but with a different name.

    Returns:
        Success with list of available methods
    """
    try:
        methods = get_jsonrpc_methods()
        return Success(methods)

    except Exception as e:
        logger.error(f"Error listing methods: {e}")
        return Error(code=-32603, message=str(e))


@method
async def update_agent_vectors(agent_id: str, vectors: list[dict]) -> Result:
    """Update vectors for an agent via JSON-RPC.

    Args:
        agent_id: Unique agent identifier
        vectors: List of vector dictionaries with 'values', 'field_path', etc.

    Returns:
        Success with update status
    """
    try:
        # Convert dict vectors to proto vectors
        from datetime import datetime

        from google.protobuf import struct_pb2, timestamp_pb2

        from .proto.generated.registry_pb2 import Vector  # type: ignore

        proto_vectors = []
        for vec_dict in vectors:
            # Create timestamp
            now = datetime.now(UTC)
            timestamp = timestamp_pb2.Timestamp()
            timestamp.FromDatetime(now)

            # Create metadata
            metadata = struct_pb2.Struct()
            if "metadata" in vec_dict:
                metadata.update(vec_dict["metadata"])

            # Create proto vector
            vector = Vector(
                values=vec_dict.get("values", []),
                agent_id=vec_dict.get("agent_id", agent_id),
                field_path=vec_dict.get("field_path", ""),
                field_content=vec_dict.get("field_content", ""),
                created_at=timestamp,
                metadata=metadata,
            )
            proto_vectors.append(vector)

        # Update vectors in storage
        if hasattr(storage, "update_agent_vectors"):
            success = await storage.update_agent_vectors(agent_id, proto_vectors)

            return Success(
                {
                    "success": success,
                    "message": f"Updated {len(proto_vectors)} vectors for agent {agent_id}",
                    "agent_id": agent_id,
                    "vector_count": len(proto_vectors),
                    "transport": "JSONRPC",
                }
            )
        else:
            return Error(
                code=-32601,
                message="Vector operations not supported by storage backend",
            )

    except Exception as e:
        logger.error(f"Error updating agent vectors via JSON-RPC: {e}")
        return Error(code=-32603, message=str(e))


@method
async def get_agent_vectors(agent_id: str) -> Result:
    """Get all vectors for an agent via JSON-RPC.

    Args:
        agent_id: Unique agent identifier

    Returns:
        Success with agent vectors
    """
    try:
        if hasattr(storage, "get_agent_vectors"):
            vectors = await storage.get_agent_vectors(agent_id)

            # Convert proto vectors to dict format
            vector_dicts = []
            for vector in vectors:
                vec_dict = {
                    "values": list(vector.values),
                    "agent_id": vector.agent_id,
                    "field_path": vector.field_path,
                    "field_content": vector.field_content,
                    "created_at": vector.created_at.ToDatetime().isoformat(),
                }

                # Add metadata if present
                if vector.metadata:
                    vec_dict["metadata"] = dict(vector.metadata)

                vector_dicts.append(vec_dict)

            return Success(
                {
                    "agent_id": agent_id,
                    "vectors": vector_dicts,
                    "count": len(vector_dicts),
                    "transport": "JSONRPC",
                }
            )
        else:
            return Error(
                code=-32601,
                message="Vector operations not supported by storage backend",
            )

    except Exception as e:
        logger.error(f"Error getting agent vectors via JSON-RPC: {e}")
        return Error(code=-32603, message=str(e))


@method
async def get_vector_stats() -> Result:
    """Get vector store statistics via JSON-RPC.

    Returns:
        Success with vector store statistics
    """
    try:
        if hasattr(storage, "get_vector_stats"):
            stats = storage.get_vector_stats()

            return Success({"vector_stats": stats, "transport": "JSONRPC"})
        else:
            return Error(
                code=-32601,
                message="Vector operations not supported by storage backend",
            )

    except Exception as e:
        logger.error(f"Error getting vector stats via JSON-RPC: {e}")
        return Error(code=-32603, message=str(e))


def get_jsonrpc_methods() -> list[str]:
    """Get list of available JSON-RPC methods for introspection."""
    return [
        "register_agent",
        "get_agent",
        "list_agents",
        "unregister_agent",
        "search_agents",
        "list_extensions",
        "ping_agent",
        "get_agent_card",
        "health_check",
        "update_agent_vectors",
        "get_agent_vectors",
        "get_vector_stats",
        "system.listMethods",
        "list_methods",
    ]
