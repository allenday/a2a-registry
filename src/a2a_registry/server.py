"""A2A Registry server using FastAPI and FastA2A schemas."""

import logging
from typing import Any, Optional

from fasta2a.schema import AgentCard
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

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
        version="1.0.0",
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

    return app

