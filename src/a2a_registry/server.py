"""A2A Registry server using FastAPI and FastA2A schemas with dual transport support."""

import logging
from typing import Any, Optional

from fasta2a.schema import AgentCard  # type: ignore
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from jsonrpcserver import async_dispatch
from pydantic import BaseModel

from . import __version__

logger = logging.getLogger(__name__)


class RegistryStorage:
    """In-memory storage for agent registry."""

    def __init__(self) -> None:
        self._agents: dict[str, AgentCard] = {}

    async def register_agent(self, agent_card: AgentCard) -> bool:
        """Register an agent in the registry."""
        # AgentCard is a TypedDict, we need to get the identifier from it
        # Looking at the structure, we might need to use 'name' as identifier
        agent_id = agent_card.get("name")
        if not agent_id:
            return False
        self._agents[agent_id] = agent_card
        logger.info(f"Registered agent: {agent_id}")
        return True

    async def get_agent(self, agent_id: str) -> Optional[AgentCard]:
        """Get an agent by ID."""
        return self._agents.get(agent_id)

    async def list_agents(self) -> list[AgentCard]:
        """List all registered agents."""
        return list(self._agents.values())

    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent."""
        if agent_id in self._agents:
            del self._agents[agent_id]
            logger.info(f"Unregistered agent: {agent_id}")
            return True
        return False

    async def search_agents(self, query: str) -> list[AgentCard]:
        """Search agents by name, description, or capabilities."""
        results = []
        query_lower = query.lower()

        for agent in self._agents.values():
            # Search in name, description, and skills
            if (
                query_lower in agent.get("name", "").lower()
                or query_lower in agent.get("description", "").lower()
                or any(
                    query_lower in skill.get("id", "").lower()
                    for skill in agent.get("skills", [])
                )
            ):
                results.append(agent)

        return results


class RegisterAgentRequest(BaseModel):
    """Request to register an agent."""

    agent_card: dict[str, Any]


class AgentSearchRequest(BaseModel):
    """Request to search for agents."""

    query: str


# Global storage instance
storage = RegistryStorage()


def create_app() -> FastAPI:
    """Create FastAPI application for A2A Registry."""
    app = FastAPI(
        title="A2A Registry",
        description="Agent-to-Agent Registry Service",
        version=__version__,
    )

    @app.post("/agents", response_model=dict[str, Any])
    async def register_agent(request: RegisterAgentRequest) -> dict[str, Any]:
        """Register an agent in the registry."""
        try:
            # AgentCard is a TypedDict, so we can use the dict directly
            # but we should validate required fields
            agent_card_dict = request.agent_card

            # Validate required fields for AgentCard
            required_fields = [
                "name",
                "description",
                "url",
                "version",
                "protocol_version",
            ]
            for field in required_fields:
                if field not in agent_card_dict:
                    raise ValueError(f"Missing required field: {field}")

            # Set default transport to JSONRPC per A2A specification
            if "preferred_transport" not in agent_card_dict:
                agent_card_dict["preferred_transport"] = "JSONRPC"

            # Cast to AgentCard type for type safety
            agent_card: AgentCard = agent_card_dict  # type: ignore
            success = await storage.register_agent(agent_card)

            if success:
                return {
                    "success": True,
                    "agent_id": agent_card["name"],
                    "message": "Agent registered successfully",
                }
            else:
                raise HTTPException(status_code=400, detail="Failed to register agent")

        except Exception as e:
            logger.error(f"Error registering agent: {e}")
            raise HTTPException(status_code=400, detail=str(e)) from e

    @app.get("/agents/{agent_id}", response_model=dict[str, Any])
    async def get_agent(agent_id: str) -> dict[str, Any]:
        """Get an agent by ID."""
        agent_card = await storage.get_agent(agent_id)
        if agent_card:
            return {"agent_card": dict(agent_card)}
        else:
            raise HTTPException(status_code=404, detail="Agent not found")

    @app.get("/agents", response_model=dict[str, Any])
    async def list_agents() -> dict[str, Any]:
        """List all registered agents."""
        agents = await storage.list_agents()
        return {"agents": [dict(agent) for agent in agents], "count": len(agents)}

    @app.delete("/agents/{agent_id}", response_model=dict[str, Any])
    async def unregister_agent(agent_id: str) -> dict[str, Any]:
        """Unregister an agent."""
        success = await storage.unregister_agent(agent_id)
        if success:
            return {"success": True, "message": "Agent unregistered successfully"}
        else:
            raise HTTPException(status_code=404, detail="Agent not found")

    @app.post("/agents/search", response_model=dict[str, Any])
    async def search_agents(request: AgentSearchRequest) -> dict[str, Any]:
        """Search for agents."""
        agents = await storage.search_agents(request.query)
        return {
            "agents": [dict(agent) for agent in agents],
            "count": len(agents),
            "query": request.query,
        }

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy", "service": "A2A Registry"}

    @app.post("/jsonrpc")
    async def jsonrpc_endpoint(request: Request) -> JSONResponse:
        """JSON-RPC endpoint - primary A2A protocol transport."""
        # Import here to avoid circular imports

        # Get request body
        data = await request.body()

        # Dispatch to JSON-RPC handlers
        response = await async_dispatch(data.decode())

        # The response from jsonrpcserver is a string, parse it to return proper JSON
        import json

        response_data = json.loads(response) if isinstance(response, str) else response

        return JSONResponse(content=response_data, media_type="application/json")

    @app.get("/")
    async def root() -> dict[str, Any]:
        """Root endpoint with service information."""
        return {
            "service": "A2A Registry",
            "version": __version__,
            "description": "Agent-to-Agent Registry Service with dual transport support",
            "protocols": {
                "primary": {
                    "transport": "JSONRPC",
                    "endpoint": "/jsonrpc",
                    "description": "JSON-RPC 2.0 endpoint (A2A default)",
                },
                "secondary": {
                    "transport": "HTTP+JSON",
                    "endpoints": {
                        "register": "POST /agents",
                        "get": "GET /agents/{id}",
                        "list": "GET /agents",
                        "search": "POST /agents/search",
                        "unregister": "DELETE /agents/{id}",
                    },
                    "description": "REST API endpoints (convenience)",
                },
            },
            "health_check": "/health",
            "documentation": "/docs",
        }

    return app
