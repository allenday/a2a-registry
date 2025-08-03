"""Storage module for A2A Registry."""

import logging
from typing import Optional

from fasta2a.schema import AgentCard  # type: ignore

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


# Global storage instance
storage = RegistryStorage()
