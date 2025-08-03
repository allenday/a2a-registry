"""Storage backend for A2A registry."""

from typing import Optional

from .proto.generated import registry_pb2  # type: ignore


class InMemoryStorage:
    """In-memory storage for agent cards."""

    def __init__(self) -> None:
        self._agents: dict[str, registry_pb2.RegistryAgentCard] = {}  # type: ignore

    async def register_agent(self, agent_card: registry_pb2.RegistryAgentCard) -> bool:  # type: ignore
        """Register an agent in the registry."""
        agent_id = agent_card.agent_card.id
        if not agent_id:
            return False

        self._agents[agent_id] = agent_card
        return True

    async def get_agent(
        self, agent_id: str
    ) -> Optional[registry_pb2.RegistryAgentCard]:  # type: ignore
        """Get an agent by ID."""
        return self._agents.get(agent_id)

    async def list_agents(self) -> list[registry_pb2.RegistryAgentCard]:  # type: ignore
        """List all registered agents."""
        return list(self._agents.values())

    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent."""
        if agent_id in self._agents:
            del self._agents[agent_id]
            return True
        return False

    async def search_agents(self, query: str) -> list[registry_pb2.RegistryAgentCard]:  # type: ignore
        """Search agents by name or description."""
        results = []
        query_lower = query.lower()

        for agent_card in self._agents.values():
            agent = agent_card.agent_card
            if (
                query_lower in agent.name.lower()
                or query_lower in agent.description.lower()
                or any(query_lower in tag.lower() for tag in agent.tags)
            ):
                results.append(agent_card)

        return results
